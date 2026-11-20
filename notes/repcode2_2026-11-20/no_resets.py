"""Desk only: repcode2's arrangement without the two ancilla-reset conditionals (the ancillas are not used after
their measurement in this arrangement). Illustrative noise only."""
import sys, types
sys.argv = sys.argv
import repcode_night as RN
import repcode2_night as R2

def circuit(error, table, lookup=True):
    qc, succ = R2.circuit(error, table, lookup)
    from qiskit import QuantumCircuit
    out = qc.copy_empty_like()
    for ins in qc.data:
        op = ins.operation
        if op.name == "if_else" and type(op.condition[0]).__name__ != "ClassicalRegister":
            continue                                    # the single-bit reset tests
        out.append(op, ins.qubits, ins.clbits)
    return out, succ

R2.install()
RN.circuit = circuit
RN.NCOND = {"lut3": 3, "lut1": 1, "lut5": 5}
import argparse
cmd = sys.argv[1]
a = argparse.Namespace()
if cmd == "ideal":
    I = RN.ideal(); print({e: (round(r["ff"]["lut3"], 4), round(r["ceiling"], 4)) for e, r in I["rows"].items()}, I["ceiling"])
elif cmd == "build":
    a.devdir, a.out, a.shots, a.dry_clifford_sentinel = sys.argv[2], sys.argv[3], 4000, True
    RN.build(a)
elif cmd == "dry":
    a.out, a.noise, a.seed = sys.argv[2], sys.argv[3], 20261119
    RN.dry(a)
elif cmd == "score":
    a.out = sys.argv[2]
    RN.score(a)
