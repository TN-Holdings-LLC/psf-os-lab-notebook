"""A feed-forward test that no after-the-fact processing can reach (desk, 2026-11-16; owner "進めて").

k one-bit teleports along a line: qubit i+1 starts in |+>, CZ(i, i+1), qubit i is measured in the X basis (H, measure),
and if the result is 1 an X is applied to qubit i+1 at once (feed-forward). Each hop applies H to the carried state, so
the input psi = H^k T^dag |+> arrives as T^dag |+>; then T and H turn it into |0>: with working feed-forward every
shot ends in 0. Without the real-time X the carried state picks up X byproducts before the non-Clifford T, and the last
bit becomes random for those shots: no relabelling of the recorded bits can repair them (only discarding shots,
post-selection, which the verdict forbids by counting every shot).
Arms: "ff" (the test), "off" (the same circuit with the conditional X removed: the control, same pulses but the
conditionals), "frame" (off, then the best classical fix of the last bit from the recorded mid-circuit bits: flip
by the parity a Clifford Pauli frame would predict). Noiseless Aer, 20000 shots each.
usage: python notes/feedforward_2026-11-16/ff_desk.py"""
import itertools
import math

from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit_aer import AerSimulator


def circuit(k, feed_forward=True):
    q = QuantumRegister(k + 1, "q")
    mid = ClassicalRegister(k, "mid")
    fin = ClassicalRegister(1, "fin")
    qc = QuantumCircuit(q, mid, fin)
    qc.h(q[0]); qc.tdg(q[0])                                    # T^dag |+>
    for _ in range(k):
        qc.h(q[0])                                              # psi = H^k T^dag |+>  (H applied k times)
    for i in range(k):
        qc.h(q[i + 1])
        qc.cz(q[i], q[i + 1])
        qc.h(q[i])
        qc.measure(q[i], mid[i])
        if feed_forward:
            with qc.if_test((mid[i], 1)):
                qc.x(q[i + 1])
    qc.t(q[k]); qc.h(q[k])
    qc.measure(q[k], fin[0])
    return qc


def run(qc, shots=20000):
    res = AerSimulator().run(qc, shots=shots, seed_simulator=7).result().get_counts()
    return res


def best_frame_fix(counts, k):
    """The best success any fixed classical rule f(mid bits) -> flip of the final bit can reach on the 'off' data."""
    by_mid = {}
    for key, c in counts.items():
        fin, mid = key.split(" ")
        by_mid.setdefault(mid, [0, 0])[int(fin)] += c
    tot = sum(counts.values())
    return sum(max(v) for v in by_mid.values()) / tot


for k in (1, 2, 3, 4):
    ff = run(circuit(k, True))
    off = run(circuit(k, False))
    tot = sum(ff.values())
    p_ff = sum(c for key, c in ff.items() if key.split(" ")[0] == "0") / tot
    p_off = sum(c for key, c in off.items() if key.split(" ")[0] == "0") / tot
    print(f"k = {k}: success with feed-forward {p_ff:.3f}; without {p_off:.3f}; "
          f"without + the best classical fix from the recorded bits {best_frame_fix(off, k):.3f}")
