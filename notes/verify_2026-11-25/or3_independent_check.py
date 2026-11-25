#!/usr/bin/env python3
# Independent re-count of results/ohm-ruler3-night-2026-11-25 (home VS, 2026-11-25).
# qiskit, qiskit-aer, numpy and the night's JSON / QPY files only: no psf-os, no notebook scoring tool.
# Formulas from prereg/ohm_ruler3_night_2026-11-25.md; the qubit-to-clbit map from the measure instructions of the
# circuits as sent. The declared tool's scores3.json is read only at the end, to compare.
# Author: The Architect <love.os.architect@proton.me>
import gzip
import hashlib
import io
import json
import math
import os
import sys

import numpy as np
from qiskit import qpy, QuantumCircuit
from qiskit.quantum_info import Statevector, SparsePauliOp
from qiskit_aer import AerSimulator

R, OUT = sys.argv[1], sys.argv[2]
ARMS, TS = ("A0", "A1", "A2"), (1, 3, 4)
KT = {1: 7, 3: 7, 4: 9}
T975 = {6: 2.447, 8: 2.306}
TAU, SHOTS = 0.3, 1000
out = {}


def window(t):
    return list(range(20, 20 + 2 * t - 1))


def cone(t):
    return {1: list(range(18, 22)), 3: list(range(14, 30)), 4: list(range(12, 34))}[t]


def names(t):
    return [f"{p}{k:02d}" for k in range(KT[t]) for p in "sc"]


# ---- strings by the declared rule ----------------------------------------------------------------------------------
def make_strings(K):
    rng = np.random.default_rng(20261124)
    kept, tried = [], 0
    while len(kept) < K:
        tried += 1
        b = [int(rng.random() < (0.75 if q < 20 else 0.25)) for q in range(40)]
        if all(abs(sum(1 - 2 * b[q] for q in cone(t))) >= 6 for t in (3, 4)):
            kept.append(b)
    s = {}
    for i, b in enumerate(kept):
        s[f"s{i:02d}"] = "".join(map(str, b))
        s[f"c{i:02d}"] = "".join(str(1 - x) for x in b)
    return s, tried


strs, tried = make_strings(9)
A = json.load(open(f"{R}/answers/ohm_ruler_answers_L9.json"))
AL = json.load(open(f"{R}/answers/ohm_ruler3_answers_by_label.json"))
B = json.load(open(f"{R}/or3/build.json"))
out["strings_draws_for_9"] = tried
out["strings_equal_answers"] = strs == A["meta"]["strings"]
out["strings_equal_build"] = {k: strs[k] for k in B["strings"]} == B["strings"]
out["first7_equal_11_24"] = None
p24 = "results/ohm-ruler-night-2026-11-24/answers/ohm_ruler_answers.json"
if os.path.exists(p24):
    s24 = json.load(open(p24))["meta"]["strings"]
    out["first7_equal_11_24"] = all(strs[k] == s24[k] for k in s24)
out["answers_sha256"] = hashlib.sha256(open(f"{R}/answers/ohm_ruler_answers_L9.json", "rb").read()).hexdigest()

# ---- the job ------------------------------------------------------------------------------------------------------
man = json.load(open(f"{R}/or3/job/manifest.json"))
raw = json.load(open(f"{R}/or3/job/raw_counts.json"))
qp = f"{R}/or3/job/circuits.qpy"
blob = open(qp, "rb").read() if os.path.exists(qp) else gzip.open(qp + ".gz").read()
out["qpy_sha256_matches_manifest"] = hashlib.sha256(blob).hexdigest() == man["circuits_sha256"]
circs = qpy.load(io.BytesIO(blob))
out["n_circuits"] = len(circs)
cell_name = {c["cell"]: c["name"] for c in man["cells"]}
pub_name = [cell_name[p["cell"]] + (f"#{p['point']}" if cell_name[p["cell"]].startswith("ksent") else "")
            for p in man["pubs"]]
pi = {n: i for i, n in enumerate(pub_name)}
rows = {r["pub"]: r["counts"] for r in raw["rows"]}
out["shots"] = (man["shots"], sorted({sum(rows[i].values()) for i in range(len(circs))}))


def measured(qc):
    m, after, delays, ops, done = {}, 0, 0, set(), set()
    for ins in qc.data:
        name = ins.operation.name
        qs = [qc.find_bit(q).index for q in ins.qubits]
        if name == "measure":
            m[qs[0]] = qc.find_bit(ins.clbits[0]).index
            done.add(qs[0])
            continue
        if name == "barrier":
            continue
        if name == "delay":
            delays += 1
        if any(q in done for q in qs):
            after += 1
        ops.add(name)
    return m, after, delays, ops


def reduce_unitary(qc, phys):
    idx = {p: i for i, p in enumerate(phys)}
    r = QuantumCircuit(len(phys))
    for ins in qc.data:
        if ins.operation.name in ("measure", "barrier"):
            continue
        qs = [qc.find_bit(q).index for q in ins.qubits]
        if not all(q in idx for q in qs):
            if any(q in idx for q in qs):
                raise RuntimeError("gate crosses the measured set")
            continue
        r.append(ins.operation, [idx[q] for q in qs])
    return r


aer = AerSimulator(method="matrix_product_state")


def z_noise_free(r):
    n = r.num_qubits
    if n <= 16:
        p = Statevector(r).probabilities()
        bits = (np.arange(len(p))[:, None] >> np.arange(n)[None, :]) & 1
        return 1 - 2 * (p @ bits)
    c = r.copy()
    for q in range(n):
        lab = ["I"] * n
        lab[n - 1 - q] = "Z"
        c.save_expectation_value(SparsePauliOp("".join(lab)), list(range(n)), label=f"z{q}")
    d = aer.run(c, shots=1).result().data()
    return np.array([d[f"z{q}"] for q in range(n)])


def z_counts(counts, clbits, weights=None):
    """per-qubit <Z>, and the SE of the per-shot (weighted) mean over these qubits."""
    w = np.ones(len(clbits)) if weights is None else np.asarray(weights, float)
    tot = sum(counts.values())
    z = np.zeros(len(clbits))
    per = []
    for key, c in counts.items():
        s = key.replace(" ", "")
        v = np.array([1 - 2 * int(s[-1 - k]) for k in clbits])
        z += c * v
        per.append(((w * v).mean(), c))
    z /= tot
    mu = sum(m * c for m, c in per) / tot
    var = sum(c * (m - mu) ** 2 for m, c in per) / (tot - 1)
    return z, math.sqrt(var / tot)


coup = {tuple(sorted(c)) for c in man["device"]["couplers"]}
chain = B["chain"]["labels"]
F = [q + 80 for q in chain]          # copy drow 4 (as 11-24): the chain labels + 80, confirmed below
out["F_copy"] = B["copy_of_F"]
out["F_is_device_path"] = all(tuple(sorted((F[i], F[i + 1]))) in coup for i in range(39))

# ---- items ---------------------------------------------------------------------------------------------------------
users = [f"p2d_{a}_t{t}_L_{n}" for a in ARMS for t in TS for n in names(t)]
zmir = [f"p2d_{a}_t{t}_L_s00_mirror" for a in ARMS for t in TS]
smir = [f"p2d_{a}_t{t}_L_{n}_smirror" for a in ARMS for t in TS for n in ("s00", "c00")]
sent = [n for n in pub_name if n.startswith("ksent")]
out["pubs"] = dict(users=sorted(n for n in pub_name if n.startswith("p2d") and not n.endswith(("mirror", "_floor")))
                   == sorted(users), zero_mirrors=sorted(n for n in pub_name if n.endswith("_s00_mirror")) == sorted(zmir),
                   string_mirrors=sorted(n for n in pub_name if n.endswith("_smirror")) == sorted(smir),
                   floors=[n for n in pub_name if n.endswith("_floor")], sentinel=len(sent),
                   others=sorted(set(pub_name) - set(users) - set(zmir) - set(smir) - set(sent)))

Z, EX, struct, cz, ws, wl, on_F = {}, {}, [], {}, 0.0, 0.0, True
for nm in users:
    t = int(nm.split("_")[2][1:])
    qc = circs[pi[nm]]
    m, after, delays, ops = measured(qc)
    struct.append((after, delays, tuple(sorted(ops))))
    pos = cone(t)
    phys = [F[p] for p in pos]
    it = B["items"][nm[4:]]
    on_F &= sorted(m) == sorted(phys) and dict(zip(it["positions"], it["physical"])) == dict(zip(pos, phys))
    cz[nm] = (qc.count_ops().get("cz", 0), qc.depth(filter_function=lambda x: x.operation.name == "cz"))
    apos = A["meta"]["positions"][f"t{t}_L"]
    exa = np.array([A["z"][nm[4:]][apos.index(p)] for p in pos])
    wl = max(wl, float(np.abs(exa - np.array([AL["z"][nm[4:]][str(q)] for q in phys])).max()))
    ws = max(ws, float(np.abs(z_noise_free(reduce_unitary(qc, phys)) - exa).max()))
    EX[nm] = exa
    Z[nm] = z_counts(rows[pi[nm]], [m[q] for q in phys])[0]
out["L_on_F_physical"] = on_F
out["noise_free_vs_answers_worst"] = ws
out["answers_vs_by_label_worst"] = wl
out["structure"] = dict(after=sum(x[0] for x in struct), delays=sum(x[1] for x in struct),
                        ops=sorted({o for x in struct for o in x[2]}))
out["cz"] = {f"{a}_t{t}": sorted({cz[f"p2d_{a}_t{t}_L_{n}"] for n in names(t)}) for a in ARMS for t in TS}

# mirrors: per-qubit <Z>, noise-free ideal checked
MZ, MS = {}, {}
worst_mirror = 0.0
for a in ARMS:
    for t in TS:
        pos = cone(t)
        phys = [F[p] for p in pos]
        nm = f"p2d_{a}_t{t}_L_s00_mirror"
        qc = circs[pi[nm]]
        m, after, delays, _ = measured(qc)
        assert sorted(m) == sorted(phys) and after == 0 and delays == 0
        worst_mirror = max(worst_mirror, float(np.abs(z_noise_free(reduce_unitary(qc, phys)) - 1).max()))
        MZ[(a, t)] = (qc, m, phys)
        for n in ("s00", "c00"):
            nm = f"p2d_{a}_t{t}_L_{n}_smirror"
            qc = circs[pi[nm]]
            m, after, delays, _ = measured(qc)
            assert sorted(m) == sorted(phys) and after == 0 and delays == 0
            ideal = np.array([1 - 2 * int(strs[n][p]) for p in pos])
            worst_mirror = max(worst_mirror, float(np.abs(z_noise_free(reduce_unitary(qc, phys)) - ideal).max()))
            MS[(a, t, n)] = (qc, m, phys)
out["mirrors_noise_free_worst"] = worst_mirror
out["mirror_cz"] = {f"{a}_t{t}": [MZ[(a, t)][0].count_ops().get("cz", 0),
                                  MS[(a, t, "s00")][0].count_ops().get("cz", 0)] for a in ARMS for t in TS}


# ---- scoring ---------------------------------------------------------------------------------------------------------
def chi2_sf(x, k):
    a, x2 = k / 2.0, x / 2.0
    if x2 <= 0:
        return 1.0
    if x2 < a + 1:
        s = term = 1.0 / a
        n = 0
        while abs(term) > 1e-16 * abs(s):
            n += 1
            term *= x2 / (a + n)
            s += term
        return 1.0 - s * math.exp(-x2 + a * math.log(x2) - math.lgamma(a))
    b, c, d = x2 + 1 - a, 1e300, 1 / (x2 + 1 - a)
    h = d
    for i in range(1, 500):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = 1 / d if d != 0 else 1e300
        c = b + an / c
        h *= d * c
    return math.exp(-x2 + a * math.log(x2) - math.lgamma(a)) * h


def words(d, se, K):
    if se == 0:
        return dict(t="NOT READ", **{"2se": "NOT READ"})
    return dict(t="AGREES" if abs(d) < T975[K - 1] * se else "DIFFERS", **{"2se": "AGREES" if abs(d) < 2 * se else "DIFFERS"})


cells, unif, direc, mirq = {}, {}, {}, {}
for a in ARMS:
    for t in TS:
        K, pos = KT[t], cone(t)
        wi = [pos.index(p) for p in window(t)]
        Od, Oe, T0, const, Vd, Ms, Me = [], [], [], [], [], [], []
        for k in range(K):
            s, c = f"p2d_{a}_t{t}_L_s{k:02d}", f"p2d_{a}_t{t}_L_c{k:02d}"
            Od.append((Z[s] - Z[c]) / 2)
            Oe.append((EX[s] - EX[c]) / 2)
            Vd.append(((1 - Z[s] ** 2) + (1 - Z[c] ** 2)) / SHOTS / 4)
            T0.append(sum(1 - 2 * int(strs[f"s{k:02d}"][p]) for p in pos))
            ms = sum(int(strs[f"s{k:02d}"][p]) for p in window(t))
            mc = sum(int(strs[f"c{k:02d}"][p]) for p in window(t))
            const.append(-(ms - mc) / 2)
            for nm, m0 in ((s, ms), (c, mc)):
                Ms.append(float(((1 - Z[nm][wi]) / 2).sum() - m0))
                Me.append(float(((1 - EX[nm][wi]) / 2).sum() - m0))
        Od, Oe, T0, const, Vd, Ms, Me = map(np.array, (Od, Oe, T0, const, Vd, Ms, Me))
        se_k = lambda x: float(np.std(x, ddof=1) / math.sqrt(K))
        sumOw = Od[:, wi].sum(axis=1)
        w_raw, w_ex = -sumOw / 2 + const, -Oe[:, wi].sum(axis=1) / 2 + const
        c = dict(K=K, M_ratio=float(np.mean((Ms - Me) ** 2) / np.mean(Me ** 2)),
                 W_ratio=float(np.mean((w_raw - w_ex) ** 2) / np.mean(w_ex ** 2)), W_dev=float(w_raw.mean()),
                 W_ex=float(w_ex.mean()), excess=float((w_raw - w_ex).mean()), excess_se=se_k(w_raw - w_ex), rulers={})
        c["M"] = "READS" if c["M_ratio"] <= 0.5 else "DOES NOT READ"
        c["W"] = "READS" if c["W_ratio"] <= 0.5 else "DOES NOT READ"

        def mirror_ruler(mean, se_mean, extra=None):
            rho = math.sqrt(mean)
            wx = -(sumOw / rho) / 2 + const
            dx = wx - w_ex
            slope = float(np.mean(sumOw)) / (4 * mean ** 1.5)
            se = math.sqrt(se_k(dx) ** 2 + (slope * se_mean) ** 2)
            r = dict(rho=rho, mean=mean, W=float(wx.mean()), d=float(dx.mean()), se=se, t_se=T975[K - 1] * se,
                     words=words(float(dx.mean()), se, K))
            if extra:
                r.update(extra)
            return r

        if t >= 3:
            rho_a = Od.sum(axis=1) / T0
            wa = -(sumOw / rho_a) / 2 + const
            da = wa - w_ex
            c["rulers"]["a"] = dict(W=float(wa.mean()), d=float(da.mean()), se=se_k(da), t_se=T975[K - 1] * se_k(da),
                                    words=words(float(da.mean()), se_k(da), K))
        # |0> mirror
        qc, m, phys = MZ[(a, t)]
        cnt = rows[pi[f"p2d_{a}_t{t}_L_s00_mirror"]]
        zm, sem = z_counts(cnt, [m[q] for q in phys])
        mirq[f"{a}_t{t}"] = {str(p): round(float(zm[i]), 4) for i, p in enumerate(pos)}
        c["rulers"]["b"] = mirror_ruler(float(zm.mean()), sem)
        keep = [i for i, p in enumerate(pos) if p in window(t) or zm[i] >= TAU]
        left = [pos[i] for i in range(len(pos)) if i not in keep]
        if len(keep) < len(pos) / 2:
            c["rulers"]["b_out"] = dict(words=dict(t="NOT READ", **{"2se": "NOT READ"}), left_out=left)
        else:
            zk, sek = z_counts(cnt, [m[phys[i]] for i in keep])
            c["rulers"]["b_out"] = mirror_ruler(float(zk.mean()), sek, dict(kept=len(keep), of=len(pos), left_out=left,
                                                                              left_out_phys=[F[p] for p in left]))
        zw, sew = z_counts(cnt, [m[phys[i]] for i in wi])
        c["rulers"]["c"] = mirror_ruler(float(zw.mean()), sew)
        # string mirrors' odd part over the window
        sign = np.array([1 - 2 * int(strs["s00"][pos[i]]) for i in wi])
        qs_, ms_, _ = MS[(a, t, "s00")]
        qc_, mc_, _ = MS[(a, t, "c00")]
        zs_, ses_ = z_counts(rows[pi[f"p2d_{a}_t{t}_L_s00_smirror"]], [ms_[phys[i]] for i in wi], sign)
        zc_, sec_ = z_counts(rows[pi[f"p2d_{a}_t{t}_L_c00_smirror"]], [mc_[phys[i]] for i in wi], sign)
        mq = (zs_ - zc_) / 2 * sign
        c["rulers"]["d"] = mirror_ruler(float(mq.mean()), math.hypot(ses_, sec_) / 2)
        cells[f"{a}_t{t}"] = c
        if t >= 3:
            use = [i for i in wi if np.sum(Oe[:, i] ** 2) >= 0.05 * K]
            # direction: per pair r_k over the used window positions, minus rho_a,k
            rk = np.array([float(np.sum(Od[k, use] * Oe[k, use]) / np.sum(Oe[k, use] ** 2)) for k in range(K)])
            dk = rk - rho_a
            sd = se_k(dk)
            mu = float(dk.mean())
            word = ("NOT READ" if sd == 0 else "WINDOW SHRINKS LESS" if mu > T975[K - 1] * sd
                    else "WINDOW SHRINKS MORE" if mu < -T975[K - 1] * sd else "NOT SEEN")
            direc[f"{a}_t{t}"] = dict(r_minus_rho_a=mu, se=sd, t_se=T975[K - 1] * sd, word=word,
                                      ruler_a=c["rulers"]["a"]["words"]["t"])
            rq, sq = [], []
            for i in use:
                den = float(np.sum(Oe[:, i] ** 2))
                rq.append(float(np.sum(Od[:, i] * Oe[:, i]) / den))
                sq.append(math.sqrt(float(np.sum(Oe[:, i] ** 2 * Vd[:, i]))) / den)
            rq, sq = np.array(rq), np.array(sq)
            wts = 1 / sq ** 2
            rp = float(np.sum(wts * rq) / np.sum(wts))
            chi2 = float(np.sum(((rq - rp) / sq) ** 2))
            p = chi2_sf(chi2, len(use) - 1)
            unif[f"{a}_t{t}"] = dict(r=[round(x, 4) for x in rq], r_pool=rp, chi2=chi2, p=p,
                                     word="UNIFORM" if p >= 0.05 else "NOT UNIFORM",
                                     outlying=[pos[use[j]] for j in range(len(use)) if abs(rq[j] - rp) > 2 * sq[j]])

TAB_B = {("WINDOW SHRINKS LESS", "DIFFERS"): "the total overstates the window's shrink",
         ("WINDOW SHRINKS LESS", "AGREES"): "the window keeps more than the total, within ruler (a)'s word",
         ("WINDOW SHRINKS MORE", "DIFFERS"): "the total understates the window's shrink",
         ("WINDOW SHRINKS MORE", "AGREES"): "the window loses more than the total, within ruler (a)'s word",
         ("NOT SEEN", "DIFFERS"): "no lean seen, yet the total does not carry it: read with the one-factor word",
         ("NOT SEEN", "AGREES"): "the window and the total shrink alike"}
tableB = {k: TAB_B[(v["word"], v["ruler_a"])] for k, v in direc.items()}
order = {}
for t in (3, 4):
    for q, get in (("W_dev", lambda c: c["W_dev"]), ("W_ex", lambda c: c["W_ex"])):
        v = [get(cells[f"{a}_t{t}"]) for a in ARMS]
        order[f"{q}_t{t}"] = "yes" if v[0] > v[1] > v[2] else "no"
    for r_ in ("a", "b", "b_out", "c", "d"):
        v = [cells[f"{a}_t{t}"]["rulers"][r_]["W"] for a in ARMS]
        order[f"W_{r_}_t{t}"] = "yes" if v[0] > v[1] > v[2] else "no"
growth = {f"{a}_W{t}/W1": dict(raw=cells[f"{a}_t{t}"]["W_dev"] / cells[f"{a}_t1"]["W_dev"],
                               exact=cells[f"{a}_t{t}"]["W_ex"] / cells[f"{a}_t1"]["W_ex"]) for a in ARMS for t in (3, 4)}

# the sentinel's overlap with the user's qubits, from the circuits as sent
user_q = {F[p] for t in TS for p in cone(t)}
sq_ = set()
for n in sent:
    sq_ |= set(measured(circs[pi[n]])[0])
out["sentinel_overlap"] = dict(sentinel_qubits=len(sq_), user_qubits=len(user_q), overlap=sorted(sq_ & user_q))

q = json.load(open(f"{R}/fetch_in/queue.json"))
p = {d: n for d, n in q["pending"].items() if d in ("ibm_fez", "ibm_kingston")}
out["queue"] = dict(read=q["read"], pending=q["pending"],
                    pick=[d for d in q["chosen"] if d in p and p[d] == min(p.values())][0])
out["charge_formula_s"] = round(2.6 + 0.000269 * len(circs) * man["shots"], 2)
out["usage"] = (raw["metrics"]["usage"]["qpu_charge_time_seconds"], raw["metrics"]["usage"]["value"], raw["job_id"])
out.update(cells=cells, uniform=unif, direction=direc, tableB=tableB, order=order, growth=growth, mirror_per_qubit=mirq)

# ---- compare with the declared tool's scores3.json --------------------------------------------------------------------
D = json.load(open(f"{R}/or3/scores3.json"))
worst, wq, diffs = 0.0, True, []
for a in ARMS:
    for t in TS:
        mc, dc = cells[f"{a}_t{t}"], D["cells"][f"{a}_t{t}_L"]
        for km, kd in (("M_ratio", "M_ratio"), ("W_ratio", "W_ratio"), ("W_dev", "W_device"), ("W_ex", "W_exact"),
                       ("excess", "W_excess"), ("excess_se", "W_excess_se")):
            worst = max(worst, abs(mc[km] - dc[kd]))
        for r_ in ("a", "b", "b_out", "c", "d"):
            if r_ not in mc["rulers"]:
                continue
            mr, dr = mc["rulers"][r_], dc["rulers"].get(r_)
            if dr is None:
                diffs.append(f"{a}_t{t} {r_} missing in scores3")
                continue
            for kk in ("d", "se", "t_se", "rho"):
                if kk in mr and kk in dr:
                    e = abs(mr[kk] - dr[kk])
                    worst = max(worst, e)
                    if e > 1e-9:
                        diffs.append(f"{a}_t{t} {r_}.{kk} mine {mr[kk]:.6f} declared {dr[kk]:.6f}")
            if mr["words"] != dr["words"]:
                wq = False
                diffs.append(f"{a}_t{t} {r_} words {mr['words']} vs {dr['words']}")
            if "left_out" in mr and mr["left_out"] != dr.get("left_out"):
                diffs.append(f"{a}_t{t} b_out left_out {mr['left_out']} vs {dr.get('left_out')}")
        if t >= 3:
            md, dd = direc[f"{a}_t{t}"], D["direction"][f"{a}_t{t}_L"]
            worst = max(worst, abs(md["r_minus_rho_a"] - dd["r_minus_rho_a"]), abs(md["t_se"] - dd["t_se"]))
            wq &= md["word"] == dd["word"]
            mu_, du = unif[f"{a}_t{t}"], D["uniform"][f"{a}_t{t}_L"]
            worst = max(worst, abs(mu_["chi2"] - du["chi2"]), abs(mu_["r_pool"] - du["r_pool"]))
            wq &= mu_["word"] == du["word"]
            if mu_["outlying"] != [x["position"] for x in du.get("outlying_positions", [])]:
                diffs.append(f"{a}_t{t} outlying {mu_['outlying']} vs {du.get('outlying_positions')}")
for k, v in order.items():
    kd = k.replace("W_dev", "W_device").replace("W_ex", "W_exact").rsplit("_t", 1)
    dv = D["beside"].get(f"order_t{kd[1]}", {}).get(kd[0])
    if dv is not None and dv != v:
        diffs.append(f"order {k} {v} vs {dv}")
out["vs_declared"] = dict(worst_abs_difference=worst, words_equal=wq, differences=diffs)
json.dump(out, open(OUT, "w"), indent=1, default=str)
print(json.dumps({k: v for k, v in out.items() if k not in ("cells", "uniform", "mirror_per_qubit")}, indent=1,
                 default=str))
for k, c in cells.items():
    print(k, f"M {c['M_ratio']:.3f} W {c['W_ratio']:.3f} Wdev {c['W_dev']:.3f} Wex {c['W_ex']:.3f} exc {c['excess']:+.3f}"
          f" (2SE {2 * c['excess_se']:.3f})")
    for r_, v in c["rulers"].items():
        if "d" in v:
            print(f"   {r_:5s} rho {v.get('rho', float('nan')):.3f} d {v['d']:+.4f} tSE {v['t_se']:.4f} 2SE {2 * v['se']:.4f}"
                  f" {v['words']}" + (f" left {v.get('left_out')}" if r_ == "b_out" else ""))
for k, u in unif.items():
    print("uniform", k, u["word"], f"p {u['p']:.4g}", "outlying", u["outlying"], f"r_pool {u['r_pool']:.3f}")
