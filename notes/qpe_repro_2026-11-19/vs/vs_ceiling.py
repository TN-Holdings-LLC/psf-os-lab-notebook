"""V2a: the IPE ceiling C(n), recomputed without the workplace code (workplace VS Claude, 2026-11-18).

The off arm is the IPE without the phase feedback but with the conditional-X reset after each read. The target is an
eigenstate (|1> of P(theta)), so it never changes, and the reset returns the ancilla to |0>: the n rounds are
independent. Round m (m = 0 .. n-1) is H, controlled-P(2 pi phi 2^m), H on a fresh ancilla, so
    P(bit m = 1 | j) = sin^2(pi j 2^m / 2^n),  phi = j / 2^n.
C(n) is the best fixed decoder of these n bits with every j equally likely:
    C(n) = 2^-n * sum over bit strings k of max_j P(k | j).
Two methods, which do not share code:
  (1) analytic: the product formula above;
  (2) statevector: the deferred-measurement circuit (one fresh ancilla per round in place of the measurement and
      reset), built here from qiskit gates, its ancilla marginal from the statevector.
The decoder is free, so C(n) does not depend on which clbit holds which bit of j.

  python vs_ceiling.py [--json OUT.json]
"""
import itertools
import json
import math
import sys


def analytic(n):
    P = {}
    for j in range(2 ** n):
        p1 = [math.sin(math.pi * j * 2 ** m / 2 ** n) ** 2 for m in range(n)]
        P[j] = {k: math.prod(p1[m] if k[m] else 1 - p1[m] for m in range(n))
                for k in itertools.product((0, 1), repeat=n)}
    return P


def statevector(n):
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    P = {}
    for j in range(2 ** n):
        qc = QuantumCircuit(n + 1)          # qubits 0 .. n-1: one ancilla per round; qubit n: the target
        qc.x(n)
        for m in range(n):
            qc.h(m)
            qc.cp(2 * math.pi * j * 2 ** m / 2 ** n, m, n)
            qc.h(m)
        probs = Statevector(qc).probabilities_dict(qargs=list(range(n)))   # key: qubit 0 rightmost
        P[j] = {tuple(int(key[-1 - m]) for m in range(n)): v for key, v in probs.items()}
    return P


def ceiling(P, n):
    keys = set().union(*P.values())
    return sum(max(P[j].get(k, 0.0) for j in P) for k in keys) / 2 ** n


def main():
    rows = {}
    for n in (2, 3, 4):
        Pa, Ps = analytic(n), statevector(n)
        ca, cs = ceiling(Pa, n), ceiling(Ps, n)
        dmax = max(abs(Pa[j].get(k, 0.0) - Ps[j].get(k, 0.0)) for j in Pa for k in Pa[j])
        rows[n] = dict(analytic=ca, statevector=cs, max_abs_diff_of_distributions=dmax)
        print(f"n {n}: C analytic {ca:.4f}, statevector {cs:.4f}, distributions differ by at most {dmax:.1e}")
    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
        json.dump({n: {k: f"{v:.3e}" for k, v in r.items()} for n, r in rows.items()}, open(out, "w"), indent=1)
    return rows


if __name__ == "__main__":
    main()
