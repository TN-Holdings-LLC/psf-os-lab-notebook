"""Dry runs of parking under ILLUSTRATIVE noise written by hand (never fitted; no device): IPE n = 2-6, every phase,
built as before (psf-os park=False: the plain circuit) and parked (psf_os.footprint.park_waits). Only IPE is listed:
in every other tool of impact.py nothing is parked, so the parked circuit is the circuit itself.

Noises (the two types of the weekend's test C's dry runs, and one for the price of the X pairs):
  wait   amplitude damping 6 % on every other qubit at each mid-circuit read (gpu's branch_noise)
  cond   dephasing 5 % on every qubit after each conditional (cond_noise)
  gate1  depolarizing 0.5 % on every one-qubit gate (x, sx): parking's cost, two X per parked wait
These are expectations, not evidence: the rule rests on the device's test C only (2026-11-21, IPE n = 4).

  python notes/park_default_2026-11-21/dry.py OUT.txt [--ns 2,3,4,5,6]
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, "..", ".."))
for d in ("gpu", "notes/ffapps_2026-11-17", "notes/rus_coherent_2026-11-17", "notes/os2_2026-11-18"):
    sys.path.insert(0, os.path.join(NB, d))
import apps as AP  # noqa: E402
import branch_noise as BN  # noqa: E402
import cond_noise as CN  # noqa: E402
from psf_os.footprint import park_waits  # noqa: E402

SHOTS = 2000
NOISES = {"wait": dict(gamma=0.06), "cond": dict(dephase_cond=0.05), "gate1": dict(p1=0.005)}


def model(noise):
    from qiskit_aer.noise import NoiseModel, depolarizing_error
    nm = NoiseModel(basis_gates=["cz", "rz", "sx", "x"])
    if noise.get("p1"):
        nm.add_all_qubit_quantum_error(depolarizing_error(float(noise["p1"]), 1), ["x", "sx"])
    return nm


def share(n, parked, noise, seed):
    from qiskit import transpile
    from qiskit_aer import AerSimulator
    sim = AerSimulator(method="density_matrix", noise_model=model(noise))
    ok = tot = 0
    for j in range(2 ** n):
        qc, succ = AP.ipe(n, j, True)
        if parked:
            qc = park_waits(qc)[0]
        cc = transpile(qc, basis_gates=["cz", "rz", "sx", "x"], optimization_level=1, seed_transpiler=0)
        nc = CN.dephase_conditionals(BN.noisy_circuit(cc, float(noise.get("gamma", 0.0))),
                                     float(noise.get("dephase_cond", 0.0)))
        cnt = sim.run(nc, shots=SHOTS, seed_simulator=seed + 10 ** 5 * j).result().get_counts()
        for k, v in cnt.items():
            k = k.replace(" ", "")
            if all(k[n - 1 - m] == str(b) for m, b in succ.items()):
                ok += v
            tot += v
    return ok / tot, tot


def main():
    import math
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--ns", default="2,3,4,5,6")
    ap.add_argument("--seed", type=int, default=20261121)
    a = ap.parse_args()
    lines = ["ILLUSTRATIVE noise, never fitted; no device. IPE, every phase, 2000 shots per phase; d = parked - as before"]
    for nz, noise in NOISES.items():
        for n in [int(x) for x in a.ns.split(",")]:
            p0, N = share(n, False, noise, a.seed)
            p1, _ = share(n, True, noise, a.seed)
            se = math.sqrt(p0 * (1 - p0) / N + p1 * (1 - p1) / N)
            lines.append(f"{nz:5s} n {n}: as before {p0:.4f}, parked {p1:.4f}, d {p1 - p0:+.4f} (2 SE {2 * se:.4f})")
            print(lines[-1], flush=True)
            open(a.out, "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
