"""Fractional gates for the Ohm fSim (home VS, 2026-11-23; desk, no device).

1. Does the fake backends' Target (qiskit-ibm-runtime 0.49.0, FakeFez, FakeKingston) list a fractional RZZ (rzz) or
   RX? Only the names of the instructions are read.
2. fSim(pi/4, phi) in an RZZ form against the CZ form: fSim(theta, phi) = exp(-i theta/2 (XX + YY)) CPhase(-phi), three
   commuting two-qubit rotations (XX, YY, ZZ) and one-qubit gates. Both forms are made by qiskit's transpile (basis
   rzz, rz, sx, x or cz, rz, sx, x; a line; level 2; seed 1): the two-qubit gate count, two-qubit layers and the RZZ
   angles, per arm, for the fSim alone, for the 40-qubit circuit and for the light-cone circuit (cone.py) at t = 3;
   noise-free equality: the fSim's operator (up to a global phase) and, on a 12-qubit chain at t = 3 with one 11-12
   string, the statevector of both compiled forms against the logical circuit.
Whether the devices accept these gates and angles is not in this notebook's device records; it has to be checked there.

usage: python notes/ohm_readable_2026-11-23/frac.py OUT.json
"""
import json
import os
import sys

import numpy as np

NB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(NB, "gpu"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ohm_answers as OA  # noqa: E402
import cone as C  # noqa: E402

BASES = {"cz": ["cz", "rz", "sx", "x"], "rzz": ["rzz", "rz", "sx", "x"]}


def compile_(qc, form):
    from qiskit import transpile
    from qiskit.transpiler import CouplingMap
    n = qc.num_qubits
    return transpile(qc, basis_gates=BASES[form], coupling_map=CouplingMap.from_line(n) if n > 1 else None,
                     initial_layout=list(range(n)), optimization_level=2, seed_transpiler=1)


def counts(tq, form):
    two = form
    angles = sorted({round(abs(float(i.operation.params[0])), 6) for i in tq.data if i.operation.name == "rzz"})
    signs = sorted({int(np.sign(float(i.operation.params[0]))) for i in tq.data if i.operation.name == "rzz"})
    return dict(two_qubit=int(tq.count_ops().get(two, 0)),
                two_qubit_layers=int(tq.depth(filter_function=lambda i: i.operation.name == two)),
                one_qubit=int(sum(v for k, v in tq.count_ops().items() if k in ("rz", "sx", "x"))),
                rzz_abs_angles=angles, rzz_signs=signs)


def main(out):
    if os.path.exists(out):
        raise SystemExit(f"STOP: {out} exists")
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import UnitaryGate
    from qiskit.quantum_info import Operator, Statevector
    from qiskit_ibm_runtime import fake_provider as FP
    res = dict(targets={}, fsim={}, circuits={})
    for name in ("FakeFez", "FakeKingston"):
        ops = sorted(getattr(FP, name)().target.operation_names)
        res["targets"][name] = dict(operations=ops, rzz="rzz" in ops, rx="rx" in ops)
    strs = OA.strings(40, 14, 0.5, 20261112)
    for arm in ("A0", "A1", "A2"):
        phi, _ = OA.ARMS[arm]
        g = QuantumCircuit(2)
        g.append(UnitaryGate(OA.fsim(OA.THETA, phi)), [0, 1])
        row = {}
        for form in BASES:
            tq = compile_(g, form)
            row[form] = dict(counts(tq, form), equal_to_fsim=bool(Operator(tq).equiv(Operator(g))))
        res["fsim"][arm] = row
        # 12-qubit chain, t = 3, the first string's first 12 bits: statevectors
        n, t, bits = 12, 3, strs[0][1][:12]
        qc = QuantumCircuit(n)
        for k, b in enumerate(bits):
            if b:
                qc.x(k)
        G = UnitaryGate(OA.fsim(OA.THETA, phi))
        for _ in range(t):
            for par in (0, 1):
                for q in range(par, n - 1, 2):
                    qc.append(G, [q, q + 1])
            if OA.ARMS[arm][1]:
                for k in range(n):
                    if OA.PATTERN[k % 3]:
                        qc.rz(OA.ARMS[arm][1] * OA.PATTERN[k % 3], k)
        sv = Statevector(qc)
        fid = {form: float(abs(np.vdot(sv.data, Statevector(compile_(qc, form)).data)) ** 2) for form in BASES}
        # the 40-qubit circuit and the light-cone circuit at t = 3
        win = list(range(20, 25))
        qs, kept = C.cone(3, win)
        full = [(c, p, q) for c, p, gs in C.layers(3) for q, _ in gs]
        cc = {}
        for which, (qq, kk) in (("full_40", (list(range(40)), full)), ("light_cone", (qs, kept))):
            circ = C.circuit(arm, 3, strs[0][1], qq, kk)
            cc[which] = {form: counts(compile_(circ, form), form) for form in BASES}
        res["circuits"][arm] = dict(chain12_t3_fidelity_to_logical=fid, t3=cc)
        print(f"{arm}: fSim CZ form {row['cz']['two_qubit']} CZ, RZZ form {row['rzz']['two_qubit']} RZZ "
              f"(|angles| {row['rzz']['rzz_abs_angles']}, signs {row['rzz']['rzz_signs']}), equal "
              f"{row['cz']['equal_to_fsim']}/{row['rzz']['equal_to_fsim']}; 12-qubit fidelity {fid}; t3 full "
              f"{cc['full_40']['cz']['two_qubit']}/{cc['full_40']['rzz']['two_qubit']} (layers "
              f"{cc['full_40']['cz']['two_qubit_layers']}/{cc['full_40']['rzz']['two_qubit_layers']}), cone "
              f"{cc['light_cone']['cz']['two_qubit']}/{cc['light_cone']['rzz']['two_qubit']} (layers "
              f"{cc['light_cone']['cz']['two_qubit_layers']}/{cc['light_cone']['rzz']['two_qubit_layers']})", flush=True)
    print("targets:", {k: (v["rzz"], v["rx"]) for k, v in res["targets"].items()})
    json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
