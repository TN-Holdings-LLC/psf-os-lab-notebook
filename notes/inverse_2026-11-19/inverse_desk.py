"""Desk test: can noise be removed by running its inverse backwards ("inversion"), and at what cost?

Workplace Claude, 2026-11-19, on the owner's question. Desk only: no device, no device record, no calibration number.
Every noise here is ILLUSTRATIVE, written by hand, and never fitted to a device.

Circuit: a kicked brickwork chain of n qubits (rx, rz, cz), L layers, |0...0> in, observable <Z> on the
middle qubit. Exact value by statevector.

The "device" (truth) is Aer with a hand-written noise; four truths:
  A  two-qubit depolarizing p after every cz, symmetric readout flip q           (the model is right)
  B  as A, but the model assumes 0.8 p                                            (the model's strength is wrong)
  C  as A plus a coherent ZZ over-rotation eps after every cz, not in the model   (an error the model does not know)
  D  as A plus one-qubit depolarizing p1 on every rx, not in the model            (an error the model does not know)

Methods, each with the same total number of shots S:
  raw     the noisy <Z> as read
  mirror  model-free rescale: run U then U^-1 (S/2 shots) and divide raw (S/2 shots) by sqrt(<Z> of the mirror)
  inverse probabilistic error cancellation with the model: after every cz insert a Pauli pair drawn from the
          quasi-probabilities of the inverse of the model's channel, weight each shot by the sign and gamma_total,
          and divide by (1 - 2 q) for the readout (the inverse of the model's readout)

Read per depth: the estimate, its 2 SE, the error against the exact value, gamma_total^2 (the shot overhead of the
inverse), and the shots the inverse would need for 2 SE = 0.02.

  python inverse_desk.py OUT.json [--n 8] [--layers 2,4,8,12,16,20] [--shots 100000] [--per 50] [--seed 7]
"""
import argparse
import itertools
import json
import math
import time

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, SparsePauliOp
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error, coherent_unitary_error
from qiskit.circuit.library import RZZGate

PAULI = ["I", "X", "Y", "Z"]
PAIRS = [a + b for a, b in itertools.product(PAULI, PAULI)]          # 16 two-qubit Paulis, "II" first


def angles(n, L, seed):
    """Per layer and qubit: an x kick in [0.2, 0.6] and a z angle in [-pi, pi] (a kicked chain that keeps a readable
    <Z> to depth 20; uniform x kicks scramble <Z> to ~0 within a few layers)."""
    rng = np.random.default_rng(seed)
    return np.stack([rng.uniform(0.2, 0.6, size=(L, n)), rng.uniform(-np.pi, np.pi, size=(L, n))])


def brick(n, L, phis, pec=None, mirror=False):
    """rx(theta), rz(phi) on every qubit, then cz on even pairs, then on odd pairs; pec: list of Pauli pairs, one per cz in
    order (inserted after that cz); mirror: append the inverse circuit."""
    qc = QuantumCircuit(n, 1)
    k = 0

    def cz(a, b):
        nonlocal k
        qc.cz(a, b)
        if pec is not None:
            p = pec[k]
            for q, s in ((a, p[1]), (b, p[0])):            # p is "PaPb" read big-endian: p[1] on a, p[0] on b
                if s != "I":
                    getattr(qc, s.lower())(q)
        k += 1

    for l in range(L):
        for q in range(n):
            qc.rx(phis[0, l, q], q)
            qc.rz(phis[1, l, q], q)
        for a in range(0, n - 1, 2):
            cz(a, a + 1)
        for a in range(1, n - 1, 2):
            cz(a, a + 1)
    if mirror:
        qc = qc.compose(qc.inverse())
    qc.measure(n // 2, 0)
    return qc


def n_cz(n, L):
    return L * ((n // 2) + ((n - 1) // 2))


def exact_z(n, L, phis):
    qc = brick(n, L, phis)
    qc.remove_final_measurements()
    sv = Statevector(qc)
    lab = ["I"] * n
    lab[n - 1 - n // 2] = "Z"
    return float(np.real(sv.expectation_value(SparsePauliOp("".join(lab)))))


def noise_model(truth, p, q, eps, p1):
    nm = NoiseModel(basis_gates=["rx", "rz", "cz", "x", "y", "z"])
    err = depolarizing_error(p, 2)
    if truth == "C":
        zz = RZZGate(eps).to_matrix()
        err = err.compose(coherent_unitary_error(zz))
    nm.add_all_qubit_quantum_error(err, ["cz"])
    if truth == "D":
        nm.add_all_qubit_quantum_error(depolarizing_error(p1, 1), ["rx"])
    nm.add_all_qubit_readout_error(ReadoutError([[1 - q, q], [q, 1 - q]]))
    return nm


def inverse_quasi(p):
    """Quasi-probabilities of the inverse of qiskit-aer's two-qubit depolarizing_error(p), over the 16 Paulis.
    Aer's convention: E(rho) = (1 - p) rho + p Tr(rho) I / 4, so every non-identity Pauli keeps f = 1 - p; inverse
    coefficients by the Walsh-Hadamard relation: c_I = (1 + 15 / f) / 16, c_Q = (1 - 1 / f) / 16 (Q != I).
    (A first version used f = 1 - 16 p / 15, the other convention; the infinite-shot check showed a bias of +0.002 at
    L = 2 with the right model, which this removes.)"""
    f = 1 - p
    c = np.full(16, (1 - 1 / f) / 16)
    c[0] = (1 + 15 / f) / 16
    return c


def z_from_counts(counts):
    n0 = counts.get("0", 0)
    n1 = counts.get("1", 0)
    return n0, n1


def run(sim, circs, shots, seed):
    res = sim.run(circs, shots=shots, seed_simulator=seed).result()
    return [res.get_counts(i) for i in range(len(circs))]


def point(n, L, phis, truth, args, rng):
    p, q, eps, p1 = args.p, args.q, args.eps, args.p1
    p_model = 0.8 * p if truth == "B" else p
    q_model = q
    sim = AerSimulator(method="statevector", noise_model=noise_model(truth, p, q, eps, p1))
    S = args.shots
    exact = exact_z(n, L, phis)
    out = dict(L=L, cz=n_cz(n, L), exact=exact)
    # raw
    c = run(sim, [brick(n, L, phis)], S, int(rng.integers(1 << 30)))[0]
    n0, n1 = z_from_counts(c)
    z = (n0 - n1) / S
    out["raw"] = dict(est=z, two_se=2 * math.sqrt(max(1 - z * z, 0) / S), err=z - exact)
    # mirror rescale (model-free): raw on S/2, mirror on S/2
    h = S // 2
    cr, cm = run(sim, [brick(n, L, phis), brick(n, L, phis, mirror=True)], h, int(rng.integers(1 << 30)))
    zr = (cr.get("0", 0) - cr.get("1", 0)) / h
    zm = (cm.get("0", 0) - cm.get("1", 0)) / h
    if zm > 0:
        k = math.sqrt(zm)
        est = zr / k
        # delta method: var(zr)/k^2 + (zr/(2 k^3))^2 var(zm)
        var = (1 - zr * zr) / h / k ** 2 + (zr / (2 * k ** 3)) ** 2 * (1 - zm * zm) / h
        out["mirror"] = dict(est=est, two_se=2 * math.sqrt(var), err=est - exact, kept_share=k)
    else:
        out["mirror"] = dict(est=None, two_se=None, err=None, kept_share=None, note="mirror read <= 0")
    # inverse (PEC with the model)
    cq = inverse_quasi(p_model)
    g = float(np.abs(cq).sum())
    prob = np.abs(cq) / g
    sign = np.sign(cq)
    ncz = n_cz(n, L)
    G = g ** ncz
    M = S // args.per
    draws = rng.choice(16, size=(M, ncz), p=prob)
    circs, sg = [], []
    for row in draws:
        circs.append(brick(n, L, phis, pec=[PAIRS[i] for i in row]))
        sg.append(float(np.prod(sign[row])))
    vals = []
    t = 0
    B = 500
    for i in range(0, M, B):
        cs = run(sim, circs[i:i + B], args.per, int(rng.integers(1 << 30)))
        for cnt, s in zip(cs, sg[i:i + B]):
            m = (cnt.get("0", 0) - cnt.get("1", 0)) / args.per
            vals.append(s * G * m / (1 - 2 * q_model))
            t += 1
    vals = np.array(vals)
    est = float(vals.mean())
    se = float(vals.std(ddof=1) / math.sqrt(len(vals)))
    # shots for 2 SE = 0.02 with this per-circuit split: se scales as 1/sqrt(M)
    need = int(S * (2 * se / 0.02) ** 2)
    out["inverse"] = dict(est=est, two_se=2 * se, err=est - exact, gamma=g, gamma_total=G, overhead=G * G,
                          circuits=M, shots_per_circuit=args.per, shots_for_two_se_0_02=need, p_model=p_model)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--layers", default="2,4,8,12,16,20")
    ap.add_argument("--truths", default="A,B,C,D")
    ap.add_argument("--shots", type=int, default=100000)
    ap.add_argument("--per", type=int, default=50)
    ap.add_argument("--p", type=float, default=0.01)
    ap.add_argument("--q", type=float, default=0.02)
    ap.add_argument("--eps", type=float, default=0.05)
    ap.add_argument("--p1", type=float, default=0.002)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    n = args.n
    Ls = [int(x) for x in args.layers.split(",")]
    rng = np.random.default_rng(args.seed)
    rows = []
    t0 = time.time()
    for L in Ls:
        phis = angles(n, L, args.seed + L)
        for truth in args.truths.split(","):
            r = point(n, L, phis, truth, args, rng)
            r["truth"] = truth
            rows.append(r)
            i, m, w = r["inverse"], r["mirror"], r["raw"]
            ms = "n/a" if m["est"] is None else f"{m['est']:+.3f}+-{m['two_se']:.3f}"
            print(f"L {L:2d} cz {r['cz']:3d} {truth}: exact {r['exact']:+.3f} | raw {w['est']:+.3f}+-{w['two_se']:.3f}"
                  f" | mirror {ms} | inverse {i['est']:+.3f}+-{i['two_se']:.3f} (gamma^2 {i['overhead']:.1f}, "
                  f"shots for 2SE 0.02 ~{i['shots_for_two_se_0_02']:.2e})  [{time.time() - t0:.0f}s]", flush=True)
            json.dump(dict(config=vars(args), note="ILLUSTRATIVE noise, written by hand, never fitted; no device",
                           rows=rows), open(args.out, "w"), indent=1)


if __name__ == "__main__":
    main()
