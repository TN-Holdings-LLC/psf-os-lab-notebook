#!/usr/bin/env python3
# Independent re-count of results/ohm-ruler-night-2026-11-24 (home VS, 2026-11-24).
# Uses only qiskit, qiskit-aer, numpy and the night's JSON / QPY files: no psf-os, no notebook scoring tool.
# Formulas are written from prereg/ohm_ruler_night_2026-11-24.md. The qubit-to-clbit map is read from the measure
# instructions of the circuits as sent.
# Author: The Architect <love.os.architect@proton.me>
import gzip
import hashlib
import io
import json
import math
import sys

import numpy as np
from qiskit import qpy, QuantumCircuit
from qiskit.quantum_info import Statevector, SparsePauliOp
from qiskit_aer import AerSimulator

R, OUT = sys.argv[1], sys.argv[2]
ARMS, TS, K = ("A0", "A1", "A2"), (1, 3, 4), 7
NAMES = [f"{p}{k:02d}" for k in range(K) for p in "sc"]
SHOTS = 1000
out = {}


def window(t):
    return list(range(20, 20 + 2 * t - 1))


def cone(t):
    # backward light cone of the window, as declared: 4, 16 and 22 qubits at t = 1, 3, 4
    return {1: list(range(18, 22)), 3: list(range(14, 30)), 4: list(range(12, 34))}[t]


# ---- strings by the declared bits-only rule, written here from the declaration ---------------------------------
def make_strings():
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


strs, tried = make_strings()
A = json.load(open(f"{R}/answers/ohm_ruler_answers.json"))
AL = json.load(open(f"{R}/answers/ohm_ruler_answers_by_label.json"))
B = json.load(open(f"{R}/or/build.json"))
out["strings_rule_draws"] = tried
out["strings_equal_answers_meta"] = strs == A["meta"]["strings"]
out["strings_equal_build"] = strs == B["strings"]
out["answers_sha256"] = hashlib.sha256(open(f"{R}/answers/ohm_ruler_answers.json", "rb").read()).hexdigest()

# ---- the job ------------------------------------------------------------------------------------------------------
man = json.load(open(f"{R}/or/job/manifest.json"))
raw = json.load(open(f"{R}/or/job/raw_counts.json"))
blob = gzip.open(f"{R}/or/job/circuits.qpy.gz").read()
out["qpy_sha256_matches_manifest"] = hashlib.sha256(blob).hexdigest() == man["circuits_sha256"]
circs = qpy.load(io.BytesIO(blob))
out["n_circuits"] = len(circs)
cell_name = {c["cell"]: c["name"] for c in man["cells"]}
pub_name = [cell_name[p["cell"]] + (f"#{p['point']}" if cell_name[p["cell"]].startswith("ksent") else "")
            for p in man["pubs"]]
rows = {r["pub"]: r["counts"] for r in raw["rows"]}
out["shots_manifest"] = man["shots"]
out["shots_per_pub"] = sorted({sum(rows[i].values()) for i in range(len(circs))})
pi = {n: i for i, n in enumerate(pub_name)}
coup = {tuple(sorted(c)) for c in man["device"]["couplers"]}


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


def z_counts(counts, clbits):
    """per-qubit <Z>, and the SE of the per-shot mean over these qubits."""
    tot = sum(counts.values())
    z = np.zeros(len(clbits))
    per = []
    for key, c in counts.items():
        s = key.replace(" ", "")
        v = np.array([1 - 2 * int(s[-1 - k]) for k in clbits])
        z += c * v
        per.append((v.mean(), c))
    z /= tot
    mu = sum(m * c for m, c in per) / tot
    var = sum(c * (m - mu) ** 2 for m, c in per) / (tot - 1)
    return z, math.sqrt(var / tot)


# ---- what was sent ------------------------------------------------------------------------------------------------
users = [f"p2d_{a}_t{t}_L_{n}" for a in ARMS for t in TS for n in NAMES]
mirrors = [f"p2d_{a}_t{t}_L_s00_mirror" for a in ARMS for t in TS]
sent = [n for n in pub_name if n.startswith("ksent")]
others = sorted(set(pub_name) - set(users) - set(mirrors) - set(sent))
out["pubs"] = dict(users_as_declared=sorted(n for n in pub_name if n.startswith("p2d") and not n.endswith("_mirror"))
                   == sorted(users), mirrors_as_declared=sorted(n for n in pub_name if n.endswith("_mirror"))
                   == sorted(mirrors), floors=[n for n in pub_name if n.endswith("_floor")], sentinel=len(sent),
                   others=others)
chain = B["chain"]["labels"]
copy = B["copy_of_F"]
# F's physical qubits by chain position (the L items sit on them); confirmed on the couplers
out["chain_is_device_path"] = all(tuple(sorted((chain[i], chain[i + 1]))) in coup for i in range(39))

Z, EX, struct, cz, worst_sim, worst_lab, on_chain = {}, {}, [], {}, 0.0, 0.0, True
for nm in users:
    _, a, tt, f, s = nm.split("_")
    t = int(tt[1:])
    qc = circs[pi[nm]]
    m, after, delays, ops = measured(qc)
    struct.append((after, delays, tuple(sorted(ops))))
    pos = cone(t)
    phys = [B["items"][nm[4:]]["physical"][B["items"][nm[4:]]["positions"].index(p)] for p in pos]
    if sorted(m) != sorted(phys):
        on_chain = False
    cz[nm] = (qc.count_ops().get("cz", 0), qc.depth(filter_function=lambda x: x.operation.name == "cz"))
    apos = A["meta"]["positions"][f"t{t}_L"]
    exa = np.array([A["z"][nm[4:]][apos.index(p)] for p in pos])
    lab = np.array([AL["z"][nm[4:]][str(q)] for q in phys])
    worst_lab = max(worst_lab, float(np.abs(exa - lab).max()))
    zs = z_noise_free(reduce_unitary(qc, phys))
    worst_sim = max(worst_sim, float(np.abs(zs - exa).max()))
    EX[nm] = exa
    Z[nm] = z_counts(rows[pi[nm]], [m[q] for q in phys])[0]
    out.setdefault("phys_sets", {}).setdefault(f"t{t}", sorted(phys))
out["L_measured_qubits_are_build_physical"] = on_chain
out["L_physical_is_F_chain_segment"] = {f"t{t}": out["phys_sets"][f"t{t}"] == sorted(chain[p] for p in cone(t))
                                        for t in TS}
out["noise_free_vs_answers_worst"] = worst_sim
out["answers_vs_by_label_worst"] = worst_lab
out["structure"] = dict(gates_after_measure=sum(x[0] for x in struct), delays=sum(x[1] for x in struct),
                        ops=sorted({o for x in struct for o in x[2]}))
out["cz"] = {f"{a}_t{t}": sorted({cz[f"p2d_{a}_t{t}_L_{n}"] for n in NAMES}) for a in ARMS for t in TS}

MIR = {}
for nm in mirrors:
    qc = circs[pi[nm]]
    m, after, delays, ops = measured(qc)
    phys = sorted(m)
    zs = z_noise_free(reduce_unitary(qc, phys))
    z, se = z_counts(rows[pi[nm]], [m[q] for q in phys])
    MIR[nm] = dict(n=len(phys), noise_free_min=round(float(zs.min()), 9), mean=float(z.mean()), se=se,
                   cz=qc.count_ops().get("cz", 0), delays=delays, after=after)
out["mirrors"] = {k[4:]: {kk: (round(v, 5) if isinstance(v, float) else v) for kk, v in d.items()} for k, d in MIR.items()}

# ---- the scores, from the declaration's formulas -------------------------------------------------------------------
def chi2_sf(x, k):
    # chi-square survival function by the regularized upper incomplete gamma (series / continued fraction)
    a, x2 = k / 2.0, x / 2.0
    if x2 <= 0:
        return 1.0
    if x2 < a + 1:
        s, term, n = 1.0 / a, 1.0 / a, 0
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


cells, unif, tables, order, beside = {}, {}, {}, {}, {}
for a in ARMS:
    for t in TS:
        pos = cone(t)
        wi = [pos.index(p) for p in window(t)]
        Od, Oe, T0, const, Ms, Me = [], [], [], [], [], []
        Vd = []
        for k in range(K):
            s, c = f"p2d_{a}_t{t}_L_s{k:02d}", f"p2d_{a}_t{t}_L_c{k:02d}"
            Od.append((Z[s] - Z[c]) / 2)
            Oe.append((EX[s] - EX[c]) / 2)
            Vd.append(((1 - Z[s] ** 2) / SHOTS + (1 - Z[c] ** 2) / SHOTS) / 4)
            T0.append(sum(1 - 2 * int(strs[f"s{k:02d}"][p]) for p in pos))
            ms = sum(int(strs[f"s{k:02d}"][p]) for p in window(t))
            mc = sum(int(strs[f"c{k:02d}"][p]) for p in window(t))
            const.append(-(ms - mc) / 2)
            for nm, m0 in ((s, ms), (c, mc)):
                Ms.append(float(((1 - Z[nm][wi]) / 2).sum() - m0))
                Me.append(float(((1 - EX[nm][wi]) / 2).sum() - m0))
        Od, Oe, T0, const, Vd = map(np.array, (Od, Oe, T0, const, Vd))
        Ms, Me = np.array(Ms), np.array(Me)
        # T_exact equals T0 (the conservation) -- checked against the answers
        out.setdefault("T_exact_minus_T0_worst", 0.0)
        out["T_exact_minus_T0_worst"] = max(out["T_exact_minus_T0_worst"], float(np.abs(Oe.sum(axis=1) - T0).max()))
        se = lambda x: float(np.std(x, ddof=1) / math.sqrt(K))
        w_raw = -Od[:, wi].sum(axis=1) / 2 + const
        w_ex = -Oe[:, wi].sum(axis=1) / 2 + const
        S = Ms.reshape(K, 2).sum(axis=1)
        c = dict(M_ratio=float(np.mean((Ms - Me) ** 2) / np.mean(Me ** 2)),
                 W_ratio=float(np.mean((w_raw - w_ex) ** 2) / np.mean(w_ex ** 2)),
                 W_dev=float(w_raw.mean()), W_ex=float(w_ex.mean()), excess=float((w_raw - w_ex).mean()),
                 excess_2se=2 * se(w_raw - w_ex), S=float(S.mean()), T0=T0.tolist())
        c["M"] = "READS" if c["M_ratio"] <= 0.5 else "DOES NOT READ"
        c["W"] = "READS" if c["W_ratio"] <= 0.5 else "DOES NOT READ"
        if t >= 3:
            rho_a = Od.sum(axis=1) / T0
            w_a = -(Od[:, wi].sum(axis=1) / rho_a) / 2 + const
            da = w_a - w_ex
            c.update(rho_a=rho_a.tolist(), W_a=float(w_a.mean()), d_a=float(da.mean()), d_a_2se=2 * se(da))
            c["ruler_a"] = "AGREES" if abs(c["d_a"]) < c["d_a_2se"] else "DIFFERS"
        else:
            c["ruler_a"] = "NOT READ"
        mr = MIR[f"p2d_{a}_t{t}_L_s00_mirror"]
        rb = math.sqrt(mr["mean"])
        w_b = -(Od[:, wi].sum(axis=1) / rb) / 2 + const
        db = w_b - w_ex
        # the mirror's shot noise through the square root: dW_b / dm = sum_window O / (4 m^1.5), mean over pairs
        slope = float(np.mean(Od[:, wi].sum(axis=1))) / (4 * mr["mean"] ** 1.5)
        se_b = math.sqrt(se(db) ** 2 + (slope * mr["se"]) ** 2)
        c.update(rho_b=rb, W_b=float(w_b.mean()), d_b=float(db.mean()), d_b_2se=2 * se_b,
                 d_b_2se_pairs_only=2 * se(db))
        c["ruler_b"] = "AGREES" if abs(c["d_b"]) < 2 * se_b else "DIFFERS"
        cells[f"{a}_t{t}"] = c
        if t >= 3:
            use = [i for i in wi if np.sum(Oe[:, i] ** 2) >= 0.05 * K]
            rq, sq = [], []
            for i in use:
                den = float(np.sum(Oe[:, i] ** 2))
                rq.append(float(np.sum(Od[:, i] * Oe[:, i]) / den))
                sq.append(math.sqrt(float(np.sum(Oe[:, i] ** 2 * Vd[:, i]))) / den)
            rq, sq = np.array(rq), np.array(sq)
            w = 1 / sq ** 2
            rbar = float(np.sum(w * rq) / np.sum(w))
            chi2 = float(np.sum(((rq - rbar) / sq) ** 2))
            p = chi2_sf(chi2, len(use) - 1) if len(use) >= 2 else float("nan")
            word = "NOT READ" if len(use) < 2 else ("UNIFORM" if p >= 0.05 else "NOT UNIFORM")
            unif[f"{a}_t{t}"] = dict(positions=[pos[i] for i in use], r=[round(x, 4) for x in rq], r_pool=rbar,
                                     chi2=chi2, dof=len(use) - 1, p=p, word=word)
            tables[f"{a}_t{t}"] = dict(table1=(word, c["ruler_a"]), table2=(c["ruler_a"], c["ruler_b"]))
for t in (3, 4):
    for q in ("W_dev", "W_a", "W_b"):
        v = [cells[f"{a}_t{t}"][q] for a in ARMS]
        order[f"{q}_t{t}"] = "yes" if v[0] > v[1] > v[2] else "no"
for a in ARMS:
    for t in (3, 4):
        c1, ct = cells[f"{a}_t1"], cells[f"{a}_t{t}"]
        beside[f"{a}_W{t}/W1"] = dict(raw=ct["W_dev"] / c1["W_dev"], exact=ct["W_ex"] / c1["W_ex"],
                                      W_b=ct["W_b"] / c1["W_b"])

q = json.load(open(f"{R}/fetch_in/queue.json"))
p = {d: n for d, n in q["pending"].items() if d in ("ibm_fez", "ibm_kingston")}
out["queue"] = dict(read=q["read"], pending=q["pending"],
                    pick=[d for d in q["chosen"] if d in p and p[d] == min(p.values())][0])
out["charge_formula_s"] = round(2.6 + 0.000269 * len(circs) * man["shots"], 2)
out["usage"] = raw["metrics"]["usage"]["qpu_charge_time_seconds"], raw["metrics"]["usage"]["value"]
out["job_id"] = raw["job_id"]
out["timestamps"] = raw["metrics"]["timestamps"]
out["calibration"] = man["device"]["source"]["calibration_time"]
out.update(cells=cells, uniform=unif, tables=tables, order=order, beside=beside)

# ---- compare with the declared tool's scores.json (set beside; it is not used above) -------------------------------
D = json.load(open(f"{R}/or/scores.json"))
worst, words_equal = 0.0, True
for a in ARMS:
    for t in TS:
        mine, dec = cells[f"{a}_t{t}"], D["cells"][f"{a}_t{t}_L"]
        for km, kd in (("M_ratio", "M_ratio"), ("W_ratio", "W_ratio"), ("W_dev", "W_device"), ("W_ex", "W_exact"),
                       ("excess", "W_excess"), ("excess_2se", "W_excess_2se"), ("S", "S_device"), ("W_a", "W_a"),
                       ("d_a", "d_a"), ("d_a_2se", "d_a_2se"), ("rho_b", "rho_b"), ("W_b", "W_b"), ("d_b", "d_b"),
                       ("d_b_2se", "d_b_2se")):
            if km in mine:
                worst = max(worst, abs(mine[km] - dec[kd]))
        for kw in ("M", "W", "ruler_a", "ruler_b"):
            words_equal &= mine[kw] == dec[kw]
        if t >= 3:
            u, du = unif[f"{a}_t{t}"], D["uniform"][f"{a}_t{t}_L"]
            worst = max(worst, abs(u["chi2"] - du["chi2"]), abs(u["p"] - du["p"]), abs(u["r_pool"] - du["r_pool"]))
            words_equal &= u["word"] == du["word"]
words_equal &= all(order[k.replace("W_device", "W_dev").replace("_L", "")] == v for k, v in D["order"].items())
out["vs_declared_scores"] = dict(worst_abs_difference=worst, words_equal=words_equal)
json.dump(out, open(OUT, "w"), indent=1, default=str)
print(json.dumps({k: v for k, v in out.items() if k not in ("cells", "uniform", "phys_sets")}, indent=1,
                 default=str))
for k, c in cells.items():
    print(k, {kk: (round(v, 4) if isinstance(v, float) else v) for kk, v in c.items() if kk not in ("T0", "rho_a")})
for k, u in unif.items():
    print("uniform", k, u)
