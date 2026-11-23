#!/usr/bin/env python3
# Independent re-count of results/ohm-window-night-2026-11-23 (home VS, 2026-11-23).
# Uses only qiskit, qiskit-aer, numpy and the records' JSON / QPY files: no psf-os, no notebook scoring tool.
# Author: The Architect <love.os.architect@proton.me>
import gzip
import hashlib
import io
import json
import sys

import numpy as np
from qiskit import qpy, QuantumCircuit
from qiskit.quantum_info import Statevector, SparsePauliOp
from qiskit_aer import AerSimulator

R = sys.argv[1]                      # results/ohm-window-night-2026-11-23
ARMS, TS, FORMS = ("A0", "A1", "A2"), (1, 3), ("L", "F")
NAMES = [f"{p}{k:02d}" for k in range(7) for p in "sc"]
out = {}


def window(t):
    return list(range(20, 20 + 2 * t - 1))


def cone(t):
    # backward light cone of the window, as declared: chain positions 18-21 at t = 1, 14-29 at t = 3
    return list(range(18, 22)) if t == 1 else list(range(14, 30))


# ---- job files -------------------------------------------------------------------------------------------------
man = json.load(open(f"{R}/ow/job/manifest.json"))
raw = json.load(open(f"{R}/ow/job/raw_counts.json"))
blob = gzip.open(f"{R}/ow/job/circuits.qpy.gz").read()
out["qpy_sha256_matches_manifest"] = hashlib.sha256(blob).hexdigest() == man["circuits_sha256"]
circs = qpy.load(io.BytesIO(blob))
out["n_circuits"] = len(circs)
out["shots_manifest"] = man["shots"]
cell_name = {c["cell"]: c["name"] for c in man["cells"]}
pub_name = [cell_name[p["cell"]] + (f"#{p['point']}" if cell_name[p["cell"]].startswith("ksent") else "")
            for p in man["pubs"]]
rows = {r["pub"]: r["counts"] for r in raw["rows"]}
out["shots_per_pub"] = sorted({sum(rows[i].values()) for i in range(len(circs))})

# device couplers (to confirm the chain is a path on the device)
coup = {tuple(sorted(c)) for c in man["device"]["couplers"]}
bad_c = {tuple(sorted(c)) for c in man["device"]["failed_couplers"]}


def measured(qc):
    """physical qubit -> clbit, and structural checks."""
    m, after, delays, other_ops = {}, 0, 0, set()
    done = set()
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
        other_ops.add(name)
    return m, after, delays, other_ops


def cz_count_depth(qc):
    n = qc.count_ops().get("cz", 0)
    d = qc.depth(filter_function=lambda x: x.operation.name == "cz")
    return n, d


def reduce_unitary(qc, phys):
    """keep only the operations on qubits in `phys`, drop measurements; return circuit on len(phys) qubits."""
    idx = {p: i for i, p in enumerate(phys)}
    r = QuantumCircuit(len(phys))
    for ins in qc.data:
        name = ins.operation.name
        if name in ("measure", "barrier"):
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
        sv = Statevector(r)
        p = sv.probabilities()
        bits = (np.arange(len(p))[:, None] >> np.arange(n)[None, :]) & 1
        return 1 - 2 * (p @ bits)
    c = r.copy()
    for q in range(n):
        lab = ["I"] * n
        lab[n - 1 - q] = "Z"
        c.save_expectation_value(SparsePauliOp("".join(lab)), [*range(n)], label=f"z{q}")
    res = aer.run(c, shots=1).result().data()
    return np.array([res[f"z{q}"] for q in range(n)])


def z_from_counts(counts, clbits):
    tot = sum(counts.values())
    z = np.zeros(len(clbits))
    for key, c in counts.items():
        s = key.replace(" ", "")
        z += c * np.array([1 - 2 * int(s[-1 - k]) for k in clbits])
    return z / tot


# ---- sealed answers -----------------------------------------------------------------------------------------------
A = json.load(open(f"{R}/answers/ohm_window_answers.json"))
AL = json.load(open(f"{R}/answers/ohm_window_answers_by_label.json"))
out["answers_sha256"] = hashlib.sha256(open(f"{R}/answers/ohm_window_answers.json", "rb").read()).hexdigest()
strs = A["meta"]["strings"]
out["strings_complements"] = all(
    "".join("1" if ch == "0" else "0" for ch in strs["s" + n[1:]]) == strs["c" + n[1:]] for n in strs if n[0] == "c")
out["string_names"] = sorted(strs)
pos_of = A["meta"]["positions"]          # key t{t}_{form} -> chain positions in answer order

# ---- per user circuit -------------------------------------------------------------------------------------------
names_user = [f"p2d_{a}_t{t}_{f}_{n}" for a in ARMS for t in TS for f in FORMS for n in NAMES]
expect_extra = [f"p2d_A1_t{t}_{f}_s00_{k}" for t in TS for f in FORMS for k in ("floor", "mirror")]
sent = [n for n in pub_name if n.startswith("ksent")]
out["pub_sets"] = dict(
    user_as_declared=sorted(n for n in pub_name if n.startswith("p2d") and not n.endswith(("_floor", "_mirror")))
    == sorted(names_user),
    floor_mirror=sorted(n for n in pub_name if n.endswith(("_floor", "_mirror"))),
    floor_mirror_as_declared=sorted(n for n in pub_name if n.endswith(("_floor", "_mirror"))) == sorted(expect_extra),
    sentinel_pubs=len(sent), sentinel_names=sorted(set(n.split("#")[0] for n in sent)))

# the F chain: the order of F's physical qubits by chain position, read from the build record, then confirmed on the
# device's couplers and by the noise-free simulation against the answers (a wrong order would not match).
chain = json.load(open(f"{R}/ow/build.json"))["chain"]["labels"]
out["chain_is_device_path"] = all(tuple(sorted((chain[i], chain[i + 1]))) in coup and
                                  tuple(sorted((chain[i], chain[i + 1]))) not in bad_c for i in range(39))

pi = {n: i for i, n in enumerate(pub_name)}
dev_z, ex_z, struct, worst_sim, worst_lab = {}, {}, {}, 0.0, 0.0
L_on_F, cz = True, {}
for nm in names_user:
    _, a, tt, f, s = nm.split("_")
    t = int(tt[1:])
    qc = circs[pi[nm]]
    m, after, delays, ops = measured(qc)
    struct[nm] = (after, delays, sorted(ops))
    pos = list(range(40)) if f == "F" else cone(t)
    phys = [chain[p] for p in pos]
    if sorted(m) != sorted(phys):
        L_on_F = False
        raise SystemExit(f"{nm}: measured qubits are not the declared chain positions")
    cz[nm] = cz_count_depth(qc)
    # answers by chain position
    apos = pos_of[f"t{t}_{f}"]
    exa = np.array([A["z"][nm[4:]][apos.index(p)] for p in pos])
    lab = np.array([AL["z"][nm[4:]][str(chain[p])] for p in pos])
    worst_lab = max(worst_lab, float(np.abs(exa - lab).max()))
    zs = z_noise_free(reduce_unitary(qc, phys))
    worst_sim = max(worst_sim, float(np.abs(zs - exa).max()))
    ex_z[nm] = dict(zip(pos, exa))
    dev_z[nm] = dict(zip(pos, z_from_counts(rows[pi[nm]], [m[q] for q in phys])))
out["L_measured_on_F_physical_at_same_positions"] = L_on_F
out["noise_free_vs_answers_worst"] = worst_sim
out["answers_vs_by_label_worst"] = worst_lab
out["structure"] = dict(gates_after_measure=sum(v[0] for v in struct.values()),
                        delays=sum(v[1] for v in struct.values()),
                        ops=sorted({o for v in struct.values() for o in v[2]}))
out["cz"] = {f"{a}_t{t}_{f}": sorted({cz[f"p2d_{a}_t{t}_{f}_{n}"] for n in NAMES}) for a in ARMS for t in TS
             for f in FORMS}

# fSim count by construction: brickwork on the cone/chain, per cycle two layers of even/odd bonds
def fsim_count(t, f):
    pos = list(range(40)) if f == "F" else cone(t)
    lo, hi = pos[0], pos[-1]
    n = 0
    for c in range(t):
        for par in (0, 1):
            for b in range(lo, hi):
                if b % 2 != par:
                    continue
                if f == "F":
                    n += 1
                else:
                    # keep the gate if it lies in the backward cone of the window at this layer
                    layer = 2 * c + par            # 0 .. 2t-1
                    rem = 2 * t - 1 - layer       # layers after this one
                    if b + 1 >= 20 - rem and b <= 20 + 2 * t - 2 + rem:
                        n += 1
    return n


out["fsim_count"] = {f"t{t}_{f}": fsim_count(t, f) for t in TS for f in FORMS}

# ---- verdicts ---------------------------------------------------------------------------------------------------
def mw(nm, which):
    t = int(nm.split("_")[2][1:])
    s = nm.split("_")[4]
    z = dev_z[nm] if which == "d" else ex_z[nm]
    return sum((1 - z[p]) / 2 for p in window(t)) - sum(int(strs[s][p]) for p in window(t))


cells, twins, order, beside = {}, {}, {}, {}
for a in ARMS:
    for t in TS:
        for f in FORMS:
            tg = [f"p2d_{a}_t{t}_{f}_{n}" for n in NAMES]
            d = np.array([mw(x, "d") for x in tg])
            e = np.array([mw(x, "e") for x in tg])
            ds = {x: mw(x, "d") for x in tg}
            es = {x: mw(x, "e") for x in tg}
            wd = np.array([(ds[f"p2d_{a}_t{t}_{f}_s{k:02d}"] - ds[f"p2d_{a}_t{t}_{f}_c{k:02d}"]) / 2 for k in range(7)])
            we = np.array([(es[f"p2d_{a}_t{t}_{f}_s{k:02d}"] - es[f"p2d_{a}_t{t}_{f}_c{k:02d}"]) / 2 for k in range(7)])
            rM = float(np.mean((d - e) ** 2) / np.mean(e ** 2))
            rW = float(np.mean((wd - we) ** 2) / np.mean(we ** 2))
            S = float(np.mean([ds[f"p2d_{a}_t{t}_{f}_s{k:02d}"] + ds[f"p2d_{a}_t{t}_{f}_c{k:02d}"] for k in range(7)]))
            Se = float(np.mean([es[f"p2d_{a}_t{t}_{f}_s{k:02d}"] + es[f"p2d_{a}_t{t}_{f}_c{k:02d}"] for k in range(7)]))
            exc = wd - we
            cells[f"{a}_t{t}_{f}"] = dict(
                M_ratio=round(rM, 4), M="READS" if rM <= 0.5 else "DOES NOT READ",
                W_ratio=round(rW, 4), W="READS" if rW <= 0.5 else "DOES NOT READ",
                W_dev=round(float(wd.mean()), 4), W_exact=round(float(we.mean()), 4),
                W_excess=round(float(exc.mean()), 4), W_excess_2SE=round(float(2 * exc.std(ddof=1) / np.sqrt(7)), 4),
                W_excess_rel=round(float(wd.mean() / we.mean() - 1), 4),
                S_dev=round(S, 4), S_exact=round(Se, 4), err=(d - e).tolist())
        eL = np.array(cells[f"{a}_t{t}_L"]["err"])
        eF = np.array(cells[f"{a}_t{t}_F"]["err"])
        dl = eF ** 2 - eL ** 2
        mu, se = float(dl.mean()), float(dl.std(ddof=1) / np.sqrt(14))
        twins[f"{a}_t{t}"] = dict(F_minus_L=round(mu, 5), SE=round(se, 5),
                                  verdict="KEEPS MORE" if mu > 2 * se else "KEEPS LESS" if mu < -2 * se else "SAME")
for f in FORMS:
    w3 = [cells[f"{a}_t3_{f}"]["W_dev"] for a in ARMS]
    order[f] = "yes" if w3[0] > w3[1] > w3[2] else "no"
    for a in ARMS:
        beside[f"{a}_{f}_W3/W1"] = dict(dev=round(cells[f"{a}_t3_{f}"]["W_dev"] / cells[f"{a}_t1_{f}"]["W_dev"], 3),
                                        exact=round(cells[f"{a}_t3_{f}"]["W_exact"] / cells[f"{a}_t1_{f}"]["W_exact"], 3))
for c in cells.values():
    del c["err"]

# floor and mirror: noise-free all-zero expected (checked), raw mean <Z> over the item's measured qubits
fm = {}
for nm in expect_extra:
    qc = circs[pi[nm]]
    m, after, delays, ops = measured(qc)
    phys = sorted(m)
    zs = z_noise_free(reduce_unitary(qc, phys))
    zd = z_from_counts(rows[pi[nm]], [m[q] for q in phys])
    fm[nm[4:]] = dict(n=len(phys), noise_free_min=round(float(zs.min()), 9), raw_mean=round(float(zd.mean()), 4),
                      cz=cz_count_depth(qc)[0])
# sentinel: noise-free distribution vs raw (total variation distance), no verdict of its own
sn = {}
for nm in sent:
    qc = circs[pi[nm]]
    m, after, delays, ops = measured(qc)
    sn[nm] = dict(qubits=len(m), cz=cz_count_depth(qc)[0], shots=sum(rows[pi[nm]].values()),
                  top=sorted(rows[pi[nm]].items(), key=lambda kv: -kv[1])[:2])

out.update(cells=cells, twins=twins, order=order, beside=beside, floor_mirror=fm, sentinel=sn)
# the queue and the pick
q = json.load(open(f"{R}/fetch_in/queue.json"))
p = {k: v for k, v in q["pending"].items() if k in ("ibm_fez", "ibm_kingston")}
best = min(p.values())
cand = [d for d in q["chosen"] if d in p and p[d] == best]
out["queue"] = dict(read=q["read"], pending=q["pending"], pick=cand[0])
out["charge_formula_s"] = round(2.6 + 0.000269 * len(circs) * man["shots"], 2)
out["usage"] = raw["metrics"]["usage"]["qpu_charge_time_seconds"], raw["metrics"]["usage"]["value"]
out["timestamps"] = raw["metrics"]["timestamps"]
out["calibration"] = man["device"]["source"]["calibration_time"]
json.dump(out, open(sys.argv[2], "w"), indent=1, default=str)
print(json.dumps({k: v for k, v in out.items() if k not in ("cells",)}, indent=1, default=str)[:6000])
for k, c in cells.items():
    print(k, c)
