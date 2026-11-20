"""List the instructions of a few sent circuits (active qubits only)."""
import json
import sys

from qiskit import qpy

out, names = sys.argv[1], sys.argv[2].split(",")
man = json.load(open(f"{out}/job/manifest.json"))
circs = qpy.load(open(f"{out}/job/circuits.qpy", "rb"))
cells = {c["cell"]: c["name"] for c in man["cells"]}
idx = {cells[p["cell"]]: i for i, p in enumerate(man["pubs"]) if p["point"] == 0}
print(sorted(idx))


def show(qc, outer, ind=""):
    for ins in qc.data:
        op = ins.operation
        qs = [outer[qc.find_bit(q).index] for q in ins.qubits]
        cs = [qc.find_bit(c).index for c in ins.clbits]
        if op.name == "if_else":
            print(f"{ind}if_else cond={op.condition} qubits={qs} clbits={cs}")
            for k, b in enumerate(op.blocks):
                print(f"{ind}  block {k}:")
                show(b, qs, ind + "    ")
        else:
            print(f"{ind}{op.name} {[round(float(p), 4) for p in op.params] if op.params else ''} q={qs} c={cs}")


for n in names:
    qc = circs[idx[n]]
    print("=====", n, "clbits", qc.num_clbits, [(r.name, r.size) for r in qc.cregs])
    show(qc, list(range(qc.num_qubits)))
