"""Dry runs of gpu/ohm_ruler_night.py's job (workplace Claude, 2026-11-24; desk, never a device).

Every circuit is sampled noise-free on its active qubits (Aer statevector). The ring sentinel (40 qubits, not Clifford)
cannot be sampled here: it gets all-zero counts, marked in submission.json. Optionally, every measured bit is flipped
with probability FLIP, independently (an ILLUSTRATIVE readout-like noise, written by hand, never fitted): it shrinks
every <Z> by the same factor 1 - 2 FLIP, once, in the circuits and in the mirrors alike.

  python notes/ohm_ruler_2026-11-24/dry.py OUT/job [--flip 0.065] [--seed 20261124]
"""
import argparse
import json
import os

import numpy as np
from qiskit import qpy


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("job")
    ap.add_argument("--flip", type=float, default=0.0)
    ap.add_argument("--seed", type=int, default=20261124)
    a = ap.parse_args()
    from psf_os import feedforward as FF
    from qiskit_aer import AerSimulator
    man = json.load(open(os.path.join(a.job, "manifest.json")))
    circs = qpy.load(open(os.path.join(a.job, "circuits.qpy"), "rb"))
    rng = np.random.default_rng(a.seed)
    sim = AerSimulator(method="statevector")
    rows, skipped = [], []
    from qiskit.transpiler.passes import RemoveBarriers
    for k, c in enumerate(circs):
        cc = FF.compact(RemoveBarriers()(c))          # the mirror's barrier spans the device: not an active qubit
        nb = c.num_clbits
        if cc.num_qubits > 28:
            rows.append(dict(pub=k, counts={"0" * nb: man["shots"]}))
            skipped.append(k)
            continue
        mem = sim.run(cc, shots=man["shots"], memory=True, seed_simulator=a.seed + 10007 * k).result().get_memory(0)
        bits = np.array([[int(ch) for ch in m.replace(" ", "")] for m in mem], dtype=np.int8)
        if a.flip:
            bits ^= (rng.random(bits.shape) < a.flip).astype(np.int8)
        counts = {}
        for row in bits:
            key = "".join(map(str, row))
            counts[key] = counts.get(key, 0) + 1
        rows.append(dict(pub=k, counts=counts))
    json.dump(dict(job_id=f"local-dry-flip{a.flip}-{a.seed}", submitted="dry", local=True,
                   backend=man["fetch"]["backend"], simulator=f"aer statevector, bit flips {a.flip} (ILLUSTRATIVE)",
                   sentinel_not_sampled=skipped), open(os.path.join(a.job, "submission.json"), "w"), indent=1)
    json.dump(dict(fetched="dry", job_id=f"local-dry-flip{a.flip}-{a.seed}", status="DONE (dry)", rows=rows),
              open(os.path.join(a.job, "raw_counts.json"), "w"))
    print(f"{len(circs)} circuits; sentinel pubs given all-zero counts: {skipped}; flip {a.flip}")


if __name__ == "__main__":
    main()
