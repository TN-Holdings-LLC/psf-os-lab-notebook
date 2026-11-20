"""Where does iterative phase estimation (IPE) meet its ceiling, and how fast does the textbook circuit fall, for n = 2 to
6? A desk projection with ILLUSTRATIVE noise (written by hand, never fitted; workplace Claude, 2026-11-20; home's
improvement candidate 6; not declared, no device).

Circuits as the 2026-11-19 test (gpu/qpe_repro_night.py): IPE = notes/ffapps_2026-11-17 apps.ipe (one ancilla, one
target, bits read least significant first, phase feedback and a conditional-X reset), compiled to cz / rz / sx / x;
textbook = qpe_repro_night.textbook_logical (n counting qubits and the target routed on a line by the fixed rule).
Noises = notes/qpe_repro_2026-11-19/noise/illus_*.json: depolarizing p2 on every cz, amplitude damping gamma on the
other qubits at each mid-circuit read (branch_noise.noisy_circuit), dephasing dephase_cond after every conditional
(cond_noise). Read: the share of shots with all n bits right, every phase pooled (IPE: 2000 shots per phase,
density matrix; textbook: exact probabilities from the density matrix), against C(n) = apps.ipe_ideal(n)["ceiling"].

  python notes/ipe_long_2026-11-20/project.py OUT.json [--ns 2,3,4,5,6] [--noises a,b,c]
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, "..", ".."))
for d in ("gpu", "notes/ffapps_2026-11-17", "notes/rus_coherent_2026-11-17", "notes/os2_2026-11-18"):
    sys.path.insert(0, os.path.join(NB, d))
import apps as AP  # noqa: E402
import branch_noise as BN  # noqa: E402
import cond_noise as CN  # noqa: E402
import qpe_repro_night as Q  # noqa: E402  (read only)

SHOTS = 2000


def _model(noise):
    from qiskit_aer.noise import NoiseModel, depolarizing_error
    nm = NoiseModel(basis_gates=["cz", "rz", "sx", "x"])
    if noise.get("p2"):
        nm.add_all_qubit_quantum_error(depolarizing_error(float(noise["p2"]), 2), ["cz"])
    return nm


def ipe_share(n, noise, seed):
    from qiskit import transpile
    from qiskit_aer import AerSimulator
    sim = AerSimulator(method="density_matrix", noise_model=_model(noise))
    ok = tot = 0
    for j in range(2 ** n):
        qc, succ = AP.ipe(n, j, True)
        cc = transpile(qc, basis_gates=["cz", "rz", "sx", "x"], optimization_level=1, seed_transpiler=0)
        nc = CN.dephase_conditionals(BN.noisy_circuit(cc, float(noise.get("gamma", 0.0))),
                                     float(noise.get("dephase_cond", 0.0)))
        cnt = sim.run(nc, shots=SHOTS, seed_simulator=seed + 10 ** 5 * j).result().get_counts()
        for k, v in cnt.items():
            k = k.replace(" ", "")
            if all(k[n - 1 - m] == str(b) for m, b in succ.items()):
                ok += v
            tot += v
    return ok / tot


def textbook_share(n, noise):
    from qiskit_aer import AerSimulator
    sim = AerSimulator(method="density_matrix", noise_model=_model(noise))
    acc = 0.0
    for j in range(2 ** n):
        qc, succ, _ = Q.textbook_logical(n, j)
        meas = {qc.find_bit(i.clbits[0]).index: qc.find_bit(i.qubits[0]).index for i in qc.data
                if i.operation.name == "measure"}
        body = qc.remove_final_measurements(inplace=False)
        body.save_probabilities_dict(qubits=[meas[k] for k in range(n)])
        p = sim.run(body).result().data(0)["probabilities"]
        want = sum(succ[k] << k for k in range(n))
        acc += p.get(want, p.get(hex(want), 0.0))
    return acc / 2 ** n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--ns", default="2,3,4,5,6")
    ap.add_argument("--noises", default="a,b,c")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    rows = []
    t0 = time.time()
    for nz in a.noises.split(","):
        noise = json.load(open(os.path.join(NB, "notes", "qpe_repro_2026-11-19", "noise", f"illus_{nz}.json")))
        for n in [int(x) for x in a.ns.split(",")]:
            C = float(AP.ipe_ideal(n)["ceiling"])
            p = ipe_share(n, noise, a.seed)
            q = textbook_share(n, noise)
            rows.append(dict(noise=nz, n=n, ceiling=C, ipe=p, textbook=q, margin=p - C, ipe_minus_textbook=p - q))
            print(f"noise {nz} n {n}: IPE {p:.4f} (ceiling {C:.4f}, margin {p - C:+.4f}); textbook {q:.4f}; "
                  f"IPE - textbook {p - q:+.4f}  [{time.time() - t0:.0f}s]", flush=True)
            json.dump(dict(note="ILLUSTRATIVE noise, written by hand, never fitted; no device", rows=rows),
                      open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
