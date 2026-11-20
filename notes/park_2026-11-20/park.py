"""Parking the waiting qubits in |0>: a desk prototype on IPE (workplace Claude, 2026-11-20; after the workplace VS's
finding that the compiler merges the target's rotations across the wait, and psf-os after-2026-11-20's fence).
Not declared, no device; ILLUSTRATIVE noise only (notes/qpe_repro_2026-11-19/noise, never fitted).

Three ways to send the same IPE:
  plain   as 2026-11-19 (compiled: the target waits in a superposition: a carrier, half excited)
  fence   a barrier on every qubit around each wait (psf_os.footprint.fence_waits): the target waits in |1>
          (no carrier, fully excited: exposed to decay)
  park    fence + X on the target before the wait and after it: the target waits in |0> (no carrier, not excited)
The action is the same (X X = I across a wait the target does not take part in). Read: the share of shots with all n
bits right, every phase pooled, by density matrix with damping gamma on the other qubits at each read and dephasing
after each conditional (gpu's branch_noise / cond_noise, as notes/ipe_long_2026-11-20/project.py).

  python notes/park_2026-11-20/park.py OUT.txt [--ns 3,4,5] [--noises a,c]
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, "..", ".."))
for d in ("gpu", "notes/ffapps_2026-11-17", "notes/rus_coherent_2026-11-17", "notes/os2_2026-11-18",
          "notes/ipe_long_2026-11-20"):
    sys.path.insert(0, os.path.join(NB, d))
import apps as AP  # noqa: E402
import branch_noise as BN  # noqa: E402
import cond_noise as CN  # noqa: E402
import project as PJ  # noqa: E402  (its noise model and shot count)
from psf_os.footprint import fence_waits, wait_footprint  # noqa: E402

TARGET = 1          # apps.ipe: qubit 0 the ancilla, qubit 1 the target (prepared |1>)


def park(qc, target=TARGET, conditionals=False):
    """fence_waits(qc) with X on `target` just before each fence before a read and just after each fence after a
    run of conditionals. conditionals=True (after the workplace VS's その6): also fence each run of phase-feedback
    conditionals and park the target there too."""
    f = fence_waits(qc, conditionals=conditionals)
    out = f.copy_empty_like()
    data = list(f.data)
    parked = False
    for i, ins in enumerate(data):
        nxt = data[i + 1].operation.name if i + 1 < len(data) else None
        prv = data[i - 1].operation.name if i > 0 else None
        is_fence = ins.operation.name == "barrier" and len(ins.qubits) == f.num_qubits
        if is_fence and (nxt == "measure" or (conditionals and nxt == "if_else")) and not parked:
            out.x(target)
            parked = True
        out.append(ins.operation, ins.qubits, ins.clbits)
        if is_fence and prv == "if_else" and parked:
            out.x(target)       # only after the conditionals of the wait it parked for (not a later feedback run)
            parked = False
    return out


def share(n, form, noise, seed):
    from qiskit import transpile
    from qiskit_aer import AerSimulator
    sim = AerSimulator(method="density_matrix", noise_model=PJ._model(noise))
    ok = tot = 0
    for j in range(2 ** n):
        qc, succ = AP.ipe(n, j, True)
        qc = {"plain": qc, "fence": fence_waits(qc), "park": park(qc),
              "fence2": fence_waits(qc, conditionals=True), "park2": park(qc, conditionals=True)}[form]
        cc = transpile(qc, basis_gates=["cz", "rz", "sx", "x"], optimization_level=1, seed_transpiler=0)
        nc = CN.dephase_conditionals(BN.noisy_circuit(cc, float(noise.get("gamma", 0.0))),
                                     float(noise.get("dephase_cond", 0.0)))
        cnt = sim.run(nc, shots=PJ.SHOTS, seed_simulator=seed + 10 ** 5 * j).result().get_counts()
        for k, v in cnt.items():
            k = k.replace(" ", "")
            if all(k[n - 1 - m] == str(b) for m, b in succ.items()):
                ok += v
            tot += v
    return ok / tot, cc


def main():
    import json
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--ns", default="3,4,5")
    ap.add_argument("--noises", default="a,c")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--forms", default="plain,fence,park")
    a = ap.parse_args()
    lines = []
    for nz in a.noises.split(","):
        noise = json.load(open(os.path.join(NB, "notes", "qpe_repro_2026-11-19", "noise", f"illus_{nz}.json")))
        for n in [int(x) for x in a.ns.split(",")]:
            row = []
            for form in a.forms.split(","):
                p, cc = share(n, form, noise, a.seed)
                f = wait_footprint(cc, span=True, conditionals=True)
                row.append(f"{form} {p:.4f} (carriers {f['max']}, excited {f['excited_waits']:.2f})")
            lines.append(f"noise {nz} n {n}: " + "; ".join(row))
            print(lines[-1], flush=True)
            open(a.out, "w").write("ILLUSTRATIVE noise, never fitted; no device\n" + "\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
