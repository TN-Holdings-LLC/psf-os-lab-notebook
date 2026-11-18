"""Conditionals and broadcasts per job and per circuit, from circuits.qpy only (workplace VS Claude, 2026-11-18; home
instruction 18h, item 3). qiskit only; no counts are read.

IBM's text (Execute dynamic circuits, "Quantum Compute limitations"): the limit on `if` statements "is a function of
the number of broadcasts and the number of broadcasted bits in a job (not a circuit)"; "A broadcast is a transfer of
unique classical data"; two if_test on an unchanged register are one broadcast. Read here as: an if_test is a new
broadcast when a bit it reads was written by a measurement after that bit's last broadcast; its broadcasted bits are
the bits it reads. Conditions inside blocks are walked too.

  python broadcasts.py JOBDIR [JOBDIR ...]
"""
import json
import os
import sys

from qiskit.circuit import Clbit


def per_circuit(c):
    stamp, sent = {}, {}          # clbit -> index of its last write / of its last broadcast
    conds = bcast = bits = 0
    t = 0
    for ins in c.data:
        t += 1
        op = ins.operation
        if op.name == "measure":
            stamp[c.find_bit(ins.clbits[0]).index] = t
        elif op.name == "if_else":
            conds += 1
            tgt = op.condition[0]
            cb = [c.find_bit(b).index for b in ([tgt] if isinstance(tgt, Clbit) else list(tgt))]
            if any(stamp.get(b, 0) > sent.get(b, -1) for b in cb):
                bcast += 1
                bits += len(cb)
                for b in cb:
                    sent[b] = t
    return conds, bcast, bits


def job(d):
    from qiskit import qpy
    cs = qpy.load(open(os.path.join(d, "circuits.qpy"), "rb"))
    rows = [per_circuit(c) for c in cs]
    return dict(circuits=len(cs), conditionals=sum(r[0] for r in rows), broadcasts=sum(r[1] for r in rows),
                broadcasted_bits=sum(r[2] for r in rows), max_conditionals_per_circuit=max(r[0] for r in rows),
                max_broadcasts_per_circuit=max(r[1] for r in rows))


if __name__ == "__main__":
    out = {}
    for d in sys.argv[1:]:
        r = job(d)
        out[d] = r
        print(d, json.dumps(r))
