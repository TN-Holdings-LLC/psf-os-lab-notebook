"""The same desk test at infinite shots: every estimator's expectation computed exactly on the density matrix, so a
bias of the inverse cannot hide behind its spread. ILLUSTRATIVE noise, never fitted; no device.

For the inverse, each cz is followed by the truth's channel and then the model's inverse channel (a linear map that is
not completely positive: sum_Q c_Q Q . Q with negative c_Q), contracted on the density matrix; this is the tensor
that probabilistic error cancellation samples. Readout: symmetric flip q, divided out by the model's (1 - 2 q).

  python infinite_shots.py OUT.json [--n 8] [--layers 2,4,8,12,20,30]
"""
import argparse
import json
import math

import numpy as np
from qiskit.quantum_info import DensityMatrix, Operator, Pauli, SparsePauliOp, SuperOp
from qiskit_aer.noise import coherent_unitary_error, depolarizing_error
from qiskit.circuit.library import RZZGate, CZGate, RXGate, RZGate

import inverse_desk as I


def inverse_superop(p):
    c = I.inverse_quasi(p)
    S = None
    for k, lab in enumerate(I.PAIRS):
        term = SuperOp(Operator(Pauli(lab))) * float(c[k])
        S = term if S is None else S + term
    return S


def truth_cz_channel(truth, p, eps):
    ch = SuperOp(depolarizing_error(p, 2).to_quantumchannel())
    if truth == "C":
        ch = ch.compose(SuperOp(coherent_unitary_error(RZZGate(eps).to_matrix()).to_quantumchannel()))
    return ch


def evolve(n, L, phis, truth, args, inverse=None, mirror=False, noisy=True):
    """<Z> on the middle qubit before readout."""
    rho = DensityMatrix.from_label("0" * n)
    p_ch = truth_cz_channel(truth, args.p, args.eps) if noisy else None
    d1 = SuperOp(depolarizing_error(args.p1, 1).to_quantumchannel()) if (noisy and truth == "D") else None
    ops = []
    for l in range(L):
        for q in range(n):
            ops.append(("rx", q, phis[0, l, q]))
            ops.append(("rz", q, phis[1, l, q]))
        for a in range(0, n - 1, 2):
            ops.append(("cz", a, None))
        for a in range(1, n - 1, 2):
            ops.append(("cz", a, None))
    seq = ops + ([(o, q, -t if t is not None else None) for o, q, t in reversed(ops)] if mirror else [])
    for o, q, t in seq:
        if o == "rx":
            rho = rho.evolve(Operator(RXGate(t)), [q])
            if d1 is not None:
                rho = rho.evolve(d1, [q])
        elif o == "rz":
            rho = rho.evolve(Operator(RZGate(t)), [q])
        else:
            rho = rho.evolve(Operator(CZGate()), [q, q + 1])
            if p_ch is not None:
                rho = rho.evolve(p_ch, [q, q + 1])
            if inverse is not None:
                rho = rho.evolve(inverse, [q, q + 1])
    lab = ["I"] * n
    lab[n - 1 - n // 2] = "Z"
    return float(np.real(rho.expectation_value(SparsePauliOp("".join(lab)))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--layers", default="2,4,8,12,20,30")
    ap.add_argument("--truths", default="A,B,C,D")
    ap.add_argument("--p", type=float, default=0.01)
    ap.add_argument("--q", type=float, default=0.02)
    ap.add_argument("--eps", type=float, default=0.05)
    ap.add_argument("--p1", type=float, default=0.002)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    rows = []
    for L in [int(x) for x in a.layers.split(",")]:
        phis = I.angles(a.n, L, a.seed + L)
        exact = I.exact_z(a.n, L, phis)
        for truth in a.truths.split(","):
            pm = 0.8 * a.p if truth == "B" else a.p
            r = (1 - 2 * a.q)
            raw = r * evolve(a.n, L, phis, truth, a)
            mir = r * evolve(a.n, L, phis, truth, a, mirror=True)
            mres = raw / math.sqrt(mir) if mir > 0 else None
            inv = evolve(a.n, L, phis, truth, a, inverse=inverse_superop(pm)) * r / (1 - 2 * a.q)
            row = dict(L=L, cz=I.n_cz(a.n, L), truth=truth, exact=exact, raw=raw, mirror=mres, inverse=inv,
                       raw_bias=raw - exact, mirror_bias=None if mres is None else mres - exact, inverse_bias=inv - exact)
            rows.append(row)
            ms = "n/a" if mres is None else f"{mres:+.4f} ({mres - exact:+.4f})"
            print(f"L {L:2d} cz {row['cz']:3d} {truth}: exact {exact:+.4f} | raw {raw:+.4f} ({raw - exact:+.4f}) | "
                  f"mirror {ms} | inverse {inv:+.4f} ({inv - exact:+.4f})", flush=True)
    json.dump(dict(config=vars(a), note="ILLUSTRATIVE noise, written by hand, never fitted; no device; infinite shots",
                   rows=rows), open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
