"""A quantum neuron by repeat-until-success (desk, 2026-11-16; owner "進めて" on the next step after the teleport test).

The repeat-until-success (RUS) circuit of Cao, Guerreschi and Aspuru-Guzik (arXiv:1711.11240) applies a non-linear
rotation to an output qubit: ancilla RY(2 theta), controlled (-iY) from ancilla to output, ancilla RY(-2 theta), measure
the ancilla. Outcome 0: the output is turned by RY(2 q(theta)) with tan q = tan^2 theta (a sigmoid-like step). Outcome
1: the output is turned by a known RY(-pi/2) (checked numerically in this sign convention); undo it with RY(pi/2),
reset the ancilla, try again.

Three ways to run L neurons in a row (neuron j+1's angle is set by neuron j's output through a controlled rotation, so
the chain carries its state forward: the "compound" case):
  ff       real time: after each failed attempt the undo and the retry are applied at once (attempts unrolled to m);
  post     no real-time control: one attempt per neuron, keep only the shots where every attempt succeeded
           (post-selection); the kept share falls as p^L;
  off      no real-time control and no discarding: failed attempts stay in.
Reported per (L, theta): the output's P(1) against the exact non-linear value, and the share of shots kept or still
failed. Noiseless Aer, 20000 shots.
usage: python notes/feedforward_2026-11-16/rus_neuron_desk.py"""
import math

from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit_aer import AerSimulator


def q_of(theta):
    return math.atan(math.tan(theta) ** 2)


def attempt(qc, a, o, theta, ctrl=None):
    """One RUS attempt on ancilla a and output o; with ctrl, the ancilla rotation is controlled by ctrl."""
    if ctrl is None:
        qc.ry(2 * theta, a)
    else:
        qc.cry(2 * theta, ctrl, a)
    qc.cy(a, o)
    qc.sdg(a)                                                   # controlled (-iY) = CY with phase -i on |1>_a
    if ctrl is None:
        qc.ry(-2 * theta, a)
    else:
        qc.cry(-2 * theta, ctrl, a)


def neuron_chain(L, theta, mode, m=3):
    """L neurons: neuron 0 on a fixed angle theta, neuron j > 0 with angle theta controlled by neuron j-1's output."""
    anc = QuantumRegister(L, "a")
    out = QuantumRegister(L, "o")
    tries = ClassicalRegister(L * (m if mode == "ff" else 1), "t")
    fin = ClassicalRegister(1, "f")
    qc = QuantumCircuit(anc, out, tries, fin)
    for j in range(L):
        ctrl = None if j == 0 else out[j - 1]
        base = j * (m if mode == "ff" else 1)
        attempt(qc, anc[j], out[j], theta, ctrl)
        qc.measure(anc[j], tries[base])
        if mode == "ff":
            for r in range(1, m):
                with qc.if_test((tries[base + r - 1], 1)):      # failed: undo, reset the ancilla, try again
                    qc.ry(math.pi / 2, out[j])
                    qc.x(anc[j])
                    attempt(qc, anc[j], out[j], theta, ctrl)
                    qc.measure(anc[j], tries[base + r])
    qc.measure(out[L - 1], fin[0])
    return qc


def exact_chain(L, theta):
    """P(final output = 1) when every neuron succeeds: neuron 0 gives P1 = sin^2 q(theta); neuron j's ancilla turns only
    when the previous output is 1, so its output is RY(2 q(theta)) on that branch and untouched otherwise."""
    p = math.sin(q_of(theta)) ** 2
    for _ in range(1, L):
        p = p * math.sin(q_of(theta)) ** 2
    return p


def run(qc, shots=20000):
    return AerSimulator().run(qc, shots=shots, seed_simulator=11).result().get_counts()


for L in (1, 2, 3):
    for theta in (0.5, 0.8, 1.1):
        target = exact_chain(L, theta)
        row = [f"L {L} theta {theta:.1f}: exact P1 {target:.3f}"]
        for mode in ("ff", "post", "off"):
            m = 3 if mode == "ff" else 1
            cnt = run(neuron_chain(L, theta, mode, m))
            tot = sum(cnt.values())
            kept, ones = 0, 0
            failed = 0
            for key, c in cnt.items():
                f, t = key.split(" ")
                bits = t[::-1]                                  # bits[i] = tries[i]
                if mode == "ff":
                    ok = all(bits[j * m:(j + 1) * m].find("0") >= 0 for j in range(L))
                    failed += c * (not ok)
                    kept += c
                    ones += c * (f == "1")
                elif mode == "post":
                    if set(bits) == {"0"}:
                        kept += c
                        ones += c * (f == "1")
                else:
                    kept += c
                    ones += c * (f == "1")
            p1 = ones / kept if kept else float("nan")
            extra = (f", still failed after {m} tries {failed / tot:.3f}" if mode == "ff" else
                     f", kept {kept / tot:.3f}" if mode == "post" else "")
            row.append(f"{mode} P1 {p1:.3f} (error {p1 - target:+.3f}{extra})")
        print("; ".join(row))
