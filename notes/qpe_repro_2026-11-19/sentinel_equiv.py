# Workplace Claude, 2026-11-18. Usage: python sentinel_equiv.py OUT VS_DUMP.json "ksent_n40_D24-fold_rule#0"
"""Are the workplace's and the VS's sentinel point the same operation? The 80 RZ that differ come in pairs on one
qubit; between a pair there are CZs (diagonal: an RZ passes through them) and single-qubit gates M. With offsets d1, d2
(VS minus workplace), the two agree iff RZ(d2) M RZ(d1) is M up to a global phase."""
import json, os, sys
import numpy as np
from qiskit import qpy
from qiskit.circuit.library import RZGate, SXGate, XGate
out, vj, which = sys.argv[1:4]
m = json.load(open(os.path.join(out, "job", "manifest.json")))
names = [c["name"] + (f"#{p}" if c["points"] > 1 else "") for c in m["cells"] for p in range(c["points"])]
c = qpy.load(open(os.path.join(out, "job", "circuits.qpy"), "rb"))[names.index(which)]
vs = [float.fromhex(r[1]) for r in json.load(open(vj))["rz"]]
k, per = 0, {}
for ins in c.data:
    nm, qs = ins.operation.name, [c.find_bit(x).index for x in ins.qubits]
    for q in qs:
        per.setdefault(q, [])
    if nm == "rz":
        th = float(ins.operation.params[0]); per[qs[0]].append(("rz", th, vs[k])); k += 1
    elif len(qs) == 1 and nm in ("sx", "x"):
        per[qs[0]].append((nm, None, None))
    elif nm == "cz":
        for q in qs:
            per[q].append(("cz", None, None))
    elif nm not in ("barrier", "measure", "delay"):
        raise SystemExit(f"unexpected {nm}")
mat = {"sx": SXGate().to_matrix(), "x": XGate().to_matrix()}
worst, pairs, other = 0.0, 0, 0
for q, seq in per.items():
    idx = [i for i, g in enumerate(seq) if g[0] == "rz" and abs(g[1] - g[2]) > 1e-12]
    if not idx:
        continue
    if len(idx) % 2:
        other += 1
        continue
    for i1, i2 in zip(idx[::2], idx[1::2]):
        d1, d2 = seq[i1][2] - seq[i1][1], seq[i2][2] - seq[i2][1]
        M = np.eye(2)
        for g in seq[i1 + 1:i2]:
            if g[0] == "rz":
                M = RZGate(g[1]).to_matrix() @ M
            elif g[0] in mat:
                M = mat[g[0]] @ M
        A = RZGate(d2).to_matrix() @ M @ RZGate(d1).to_matrix()
        worst = max(worst, 1 - abs(np.trace(M.conj().T @ A)) / 2)
        pairs += 1
print(f"{which}: {k} rz, {pairs} pairs checked, unpaired qubits {other}, worst 1 - |overlap| {worst:.2e}")
