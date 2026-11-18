"""V2b: which clbit holds which bit of j, read from the compiled device circuits (job/circuits.qpy) without the
workplace code (workplace VS Claude, 2026-11-18). Only qiskit and qiskit_aer are imported.

Expected readout, from the algorithms themselves (not from the tool's success maps):
  - textbook phase estimation of phi = j / 2^n: the counting register reads the integer j, clbit k = bit k of j
    (k = 0 least significant);
  - IPE: round m uses 2 pi phi 2^m and, with the feedback, reads the binary digit phi_{m+1} of phi = 0.phi_1 phi_2 ..,
    so clbit m = bit (n - 1 - m) of j.
Checks, per compiled arm (the item's j and n from the cell name):
  - tqpe ff and its replicate (off) arm: statevector of the circuit without its final reads; P(read == j) must be 1;
  - ipe ff: noiseless Aer sampling (it has conditionals); every shot must read the expected bits;
  - ipe off: sampled against the product formula of vs_ceiling.py (total variation <= 0.03);
  - every floor: every shot all zero.
The circuit is cut down to the qubits it touches by a helper written here.

  python vs_bits.py OUT [OUT ...] [--shots S]
"""
import json
import math
import os
import re
import sys

import vs_ceiling as VC


def compact(c):
    from qiskit import QuantumCircuit, QuantumRegister
    used = sorted({c.find_bit(q).index for ins in c.data for q in ins.qubits})
    pos = {q: i for i, q in enumerate(used)}
    out = QuantumCircuit(QuantumRegister(len(used), "q"), *c.cregs)
    for ins in c.data:
        out.append(ins.operation, [out.qubits[pos[c.find_bit(q).index]] for q in ins.qubits],
                   [out.clbits[c.find_bit(b).index] for b in ins.clbits])
    return out, used


def expected_key(fam, n, j):
    bits = {k: (j >> k) & 1 for k in range(n)} if fam == "tqpe" else {m: (j >> (n - 1 - m)) & 1 for m in range(n)}
    return "".join(str(bits[k]) for k in reversed(range(n)))      # clbit 0 rightmost


def textbook_prob(cc, n, want):
    from qiskit.quantum_info import Statevector
    meas = {cc.find_bit(ins.clbits[0]).index: cc.find_bit(ins.qubits[0]).index
            for ins in cc.data if ins.operation.name == "measure"}
    assert sorted(meas) == list(range(n)), meas
    sv = Statevector(cc.remove_final_measurements(inplace=False))
    return sv.probabilities_dict(qargs=[meas[k] for k in range(n)]).get(want, 0.0)


def run(out, shots):
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    m = json.load(open(os.path.join(out, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(out, "job", "circuits.qpy"), "rb"))
    sim = AerSimulator()
    names = [cell["name"] + (f"#{p}" if cell["points"] > 1 else "") for cell in m["cells"] for p in range(cell["points"])]
    assert len(names) == len(cs)
    bad, rows, worst_tv = [], 0, 0.0
    for i, (name, c) in enumerate(zip(names, cs)):
        mt = re.fullmatch(r"ff_(ipe|tqpe)(\d)_(\d+)(_off|_floor)?", name)
        if not mt:
            continue
        fam, n, j, arm = mt.group(1), int(mt.group(2)), int(mt.group(3)), (mt.group(4) or "_ff")[1:]
        cc, used = compact(c)
        want = expected_key(fam, n, j)
        rows += 1
        if fam == "tqpe" and arm in ("ff", "off"):
            p = textbook_prob(cc, n, want)
            ok = abs(p - 1) < 1e-9
            note = f"P(read {want}) {p:.9f}"
        else:
            cnt = sim.run(cc, shots=shots, seed_simulator=7 + i).result().get_counts()
            cnt = {k.replace(" ", "")[-n:]: v for k, v in cnt.items()}
            tot = sum(cnt.values())
            if arm == "floor":
                ok = cnt.get("0" * n, 0) == tot
                note = f"all zero {cnt.get('0' * n, 0)}/{tot}"
            elif arm == "ff":
                ok = cnt.get(want, 0) == tot
                note = f"read {want} {cnt.get(want, 0)}/{tot}"
            else:
                P = VC.analytic(n)[j]
                exact = {"".join(str(k[b]) for b in reversed(range(n))): v for k, v in P.items()}
                tv = 0.5 * sum(abs(cnt.get(k, 0) / tot - exact.get(k, 0.0)) for k in set(cnt) | set(exact))
                worst_tv = max(worst_tv, tv)
                ok = tv <= 0.03
                note = f"total variation to the product formula {tv:.3f}"
        if not ok:
            bad.append(name)
            print(f"  {name:18s} {note}  FAIL")
    print(f"{out}: {rows} arms checked (ipe off worst total variation {worst_tv:.3f}); "
          + ("ALL AS EXPECTED" if not bad else f"NOT AS EXPECTED {bad}"))
    return not bad


if __name__ == "__main__":
    args = sys.argv[1:]
    shots = 2000
    if "--shots" in args:
        k = args.index("--shots")
        shots = int(args[k + 1])
        del args[k:k + 2]
    oks = [run(o, shots) for o in args]
    sys.exit(0 if all(oks) else 1)
