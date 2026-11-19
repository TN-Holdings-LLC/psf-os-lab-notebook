"""Twin rescale against mirror rescale in the same job: is their gap g = k_mirror - k_twin a marker of coherent
(phase) error?  A rough look on the desk (workplace VS, 2026-11-19, "その6"; not declared; author The Architect).

Every noise here is ILLUSTRATIVE, written by hand, never fitted to a device. No device, no device record, no
calibration number.

Circuit: the kicked brickwork chain of scripts/inverse_desk.py (same angles, same seeds), rebuilt in the sx / rz / cz
basis: rx(t) = rz(pi/2) sx rz(t + pi) sx rz(pi/2) (exact up to a global phase), consecutive rz on one qubit merged
(as a compiled circuit would have them; never across another gate on that qubit).

  user    U, all n qubits measured
  twin    psf_os.twin.twin(U): every rz rounded to a multiple of pi/2, sx / cz / order kept (check_same_schedule)
  mirror  U then U^-1, rebuilt in the same basis (sxdg = rz(pi) sx rz(pi)), all n qubits measured

  k_twin    = kept_share(z_twin, twin.z_exact(twin))        (r = sum z e / sum e^2 over the n qubits)
  k_mirror  = sqrt(kept_share(z_mirror, 1...1))              (the mirror's exact pattern is all +1)
  estimate  = z_user[mid] / k ;  g = k_mirror - k_twin ;  k_true = z_user[mid] / exact[mid]

Noises (illustrative): A depolarizing p after every cz + symmetric readout flip q; C = A + ZZ(eps) after every cz;
D = A + one-qubit depolarizing p1 after every sx; Cx (C') = A + ZZ(eps) for eps in --eps-scan.

  python twin_mirror.py OUT.json --mode inf  [--n 8] [--layers 2,4,8,12,20]
  python twin_mirror.py OUT.json --mode shots [--shots 40000] [--reps 1] [--seed 11]
"""
import argparse
import json
import math
import sys
import time

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import RZZGate
from qiskit.quantum_info import Statevector, SparsePauliOp
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError, coherent_unitary_error, depolarizing_error

import inverse_desk as I            # angles() only: the same chain and seeds as the workplace desk test
from psf_os import twin as T

HP = math.pi / 2


def basis_ops(n, L, phis):
    """The chain as a list of (name, qubits, angle) in the sx / rz / cz basis, rz not yet merged."""
    ops = []
    for l in range(L):
        for q in range(n):
            t, p = phis[0, l, q], phis[1, l, q]
            ops += [("rz", (q,), HP), ("sx", (q,), None), ("rz", (q,), t + math.pi), ("sx", (q,), None),
                    ("rz", (q,), HP), ("rz", (q,), p)]
        for a in list(range(0, n - 1, 2)) + list(range(1, n - 1, 2)):
            ops.append(("cz", (a, a + 1), None))
    return ops


def inverse_ops(ops):
    out = []
    for name, qs, t in reversed(ops):
        if name == "rz":
            out.append(("rz", qs, -t))
        elif name == "sx":                      # sxdg = Z sx Z (up to a global phase)
            out += [("rz", qs, math.pi), ("sx", qs, None), ("rz", qs, math.pi)]
        else:
            out.append((name, qs, t))
    return out


def merge_rz(ops):
    """Merge consecutive rz on a qubit (no other gate on that qubit in between); angle wrapped to (-pi, pi]."""
    out, pend = [], {}

    def flush(q):
        if q in pend:
            a = (pend.pop(q) + math.pi) % (2 * math.pi) - math.pi
            if a == -math.pi:
                a = math.pi
            out.append(("rz", (q,), a))

    for name, qs, t in ops:
        if name == "rz":
            pend[qs[0]] = pend.get(qs[0], 0.0) + t
        else:
            for q in qs:
                flush(q)
            out.append((name, qs, t))
    for q in sorted(pend):
        flush(q)
    return out


def to_circuit(n, ops, measure):
    qc = QuantumCircuit(n, n if measure else 0)
    for name, qs, t in ops:
        if name == "rz":
            qc.rz(t, qs[0])
        elif name == "sx":
            qc.sx(qs[0])
        else:
            qc.cz(*qs)
    if measure:
        qc.measure(range(n), range(n))
    return qc


def build(n, L, seed):
    phis = I.angles(n, L, seed + L)
    ops = merge_rz(basis_ops(n, L, phis))
    U = to_circuit(n, ops, True)
    M = to_circuit(n, merge_rz(ops + inverse_ops(ops)), True)
    tw = T.twin(U)
    assert T.check_same_schedule(U, tw)
    # the basis rebuild is the same unitary as the rx / rz chain
    ref = I.brick(n, L, phis)
    ref.remove_final_measurements()
    u0 = U.remove_final_measurements(inplace=False)
    assert abs(abs(Statevector(ref).inner(Statevector(u0))) - 1) < 1e-9
    exact = np.array([float(np.real(Statevector(u0).expectation_value(SparsePauliOp(lab(n, q))))) for q in range(n)])
    e_twin = T.z_exact(tw, list(range(n)))
    return U, tw, M, exact, e_twin


def lab(n, q):
    s = ["I"] * n
    s[n - 1 - q] = "Z"
    return "".join(s)


def noise(kind, p, q, eps, p1):
    nm = NoiseModel(basis_gates=["sx", "rz", "cz"])
    err = depolarizing_error(p, 2)
    if kind == "C":
        err = err.compose(coherent_unitary_error(RZZGate(eps).to_matrix()))
    nm.add_all_qubit_quantum_error(err, ["cz"])
    if kind == "D":
        nm.add_all_qubit_quantum_error(depolarizing_error(p1, 1), ["sx"])
    nm.add_all_qubit_readout_error(ReadoutError([[1 - q, q], [q, 1 - q]]))
    return nm


def z_inf(sim, qc, n, q):
    """Per-qubit <Z> at infinite shots: density matrix, readout flip applied as (1 - 2 q)."""
    c = qc.remove_final_measurements(inplace=False)
    c.save_probabilities()
    pr = np.asarray(sim.run(c).result().data(0)["probabilities"])
    idx = np.arange(len(pr))
    return np.array([(1 - 2 * q) * float(pr @ (1 - 2 * ((idx >> k) & 1))) for k in range(n)])


def shots_stats(counts, n, e):
    """Per-shot statistic s = sum_q e_q z_q / sum e^2 (z_q = +-1): its mean and the SE of the mean (correlations between
    qubits included). Also the per-qubit means."""
    tot, s1, s2 = 0, 0.0, 0.0
    zq = np.zeros(n)
    d = float(e @ e)
    for b, c in counts.items():
        bits = np.array([1 - 2 * int(b[n - 1 - k]) for k in range(n)], float)
        s = float(bits @ e) / d
        tot += c
        s1 += c * s
        s2 += c * s * s
        zq += c * bits
    m = s1 / tot
    var = max(s2 / tot - m * m, 0.0)
    return m, math.sqrt(var / tot), zq / tot


def point(n, L, kind, eps, args, rng):
    U, tw, M, exact, e_twin = build(n, L, args.seed)
    mid = n // 2
    nm = noise(kind, args.p, args.q, eps, args.p1)
    r = dict(n=n, L=L, cz=sum(1 for i in U.data if i.operation.name == "cz"), noise=kind, eps=eps if kind == "C" else 0.0,
             exact_mid=exact[mid], twin_exact=e_twin.tolist())
    if args.mode == "inf":
        sim = AerSimulator(method="density_matrix", noise_model=nm)
        zu, zt, zm = (z_inf(sim, c, n, args.q) for c in (U, tw, M))
        kt = T.kept_share(zt, e_twin)
        rm = T.kept_share(zm, np.ones(n))
        km = math.sqrt(rm) if rm > 0 else float("nan")
        raw = zu[mid]
        r.update(raw=raw, k_true=raw / exact[mid], k_twin=kt, k_mirror=km, g=km - kt,
                 twin_est=raw / kt, mirror_est=raw / km, twin_err=raw / kt - exact[mid], mirror_err=raw / km - exact[mid],
                 raw_err=raw - exact[mid])
        return r
    sim = AerSimulator(method="density_matrix", noise_model=nm)
    reps = []
    for _ in range(args.reps):
        res = sim.run([U, tw, M], shots=args.shots, seed_simulator=int(rng.integers(1 << 30))).result()
        cu, ct, cm = (res.get_counts(i) for i in range(3))
        _, _, zu = shots_stats(cu, n, np.ones(n))
        kt, se_t, _ = shots_stats(ct, n, e_twin)
        rm, se_m, _ = shots_stats(cm, n, np.ones(n))
        km = math.sqrt(rm)
        se_km = se_m / (2 * km)
        raw = zu[mid]
        se_raw = math.sqrt(max(1 - raw * raw, 0) / args.shots)
        reps.append(dict(raw=raw, two_se_raw=2 * se_raw, k_twin=kt, two_se_k_twin=2 * se_t, k_mirror=km,
                         two_se_k_mirror=2 * se_km, g=km - kt, two_se_g=2 * math.hypot(se_t, se_km),
                         twin_err=raw / kt - exact[mid], mirror_err=raw / km - exact[mid]))
    r["shots"] = args.shots
    r["reps"] = reps
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--mode", choices=["inf", "shots"], required=True)
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--layers", default="2,4,8,12,20")
    ap.add_argument("--noises", default="A,C,D")
    ap.add_argument("--eps-scan", default="0.02,0.05,0.1")
    ap.add_argument("--p", type=float, default=0.01)
    ap.add_argument("--q", type=float, default=0.02)
    ap.add_argument("--eps", type=float, default=0.05)
    ap.add_argument("--p1", type=float, default=0.002)
    ap.add_argument("--shots", type=int, default=40000)
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--seed", type=int, default=7)          # the chain's angles: the same as inverse_desk.py
    ap.add_argument("--shot-seed", type=int, default=11)
    args = ap.parse_args()
    rng = np.random.default_rng(args.shot_seed)
    jobs = [(k, args.eps) for k in args.noises.split(",") if k]
    jobs += [("C", float(e)) for e in args.eps_scan.split(",") if e and float(e) != args.eps]
    rows, t0 = [], time.time()
    for L in [int(x) for x in args.layers.split(",")]:
        for kind, eps in jobs:
            r = point(args.n, L, kind, eps, args, rng)
            rows.append(r)
            tag = kind if kind != "C" else f"C{eps:g}"
            if args.mode == "inf":
                print(f"n {args.n} L {L:2d} {tag:6s} exact {r['exact_mid']:+.4f} raw {r['raw']:+.4f} k_true "
                      f"{r['k_true']:.4f} k_twin {r['k_twin']:.4f} k_mirror {r['k_mirror']:.4f} g {r['g']:+.4f} | err "
                      f"twin {r['twin_err']:+.4f} mirror {r['mirror_err']:+.4f}  [{time.time() - t0:.0f}s]", flush=True)
            else:
                for x in r["reps"]:
                    print(f"n {args.n} L {L:2d} {tag:6s} k_twin {x['k_twin']:.4f}+-{x['two_se_k_twin']:.4f} k_mirror "
                          f"{x['k_mirror']:.4f}+-{x['two_se_k_mirror']:.4f} g {x['g']:+.4f}+-{x['two_se_g']:.4f} | err "
                          f"twin {x['twin_err']:+.4f} mirror {x['mirror_err']:+.4f}  [{time.time() - t0:.0f}s]",
                          flush=True)
    json.dump(dict(config=vars(args), note="ILLUSTRATIVE noise, written by hand, never fitted; no device", rows=rows),
              open(args.out, "w"), indent=1)


if __name__ == "__main__":
    sys.exit(main())
