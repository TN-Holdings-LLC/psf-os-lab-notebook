"""Dry runs of gpu/ohm_ruler_night3.py's job (workplace Claude, 2026-11-25; desk, never a device).

As notes/ohm_ruler_2026-11-24/dry.py (every circuit sampled noise-free on its active qubits, Aer statevector; the ring
sentinel not sampled), with ILLUSTRATIVE readout-like noises written by hand, never fitted to a device:
  --flip Q            every measured bit flipped with probability Q (symmetric, as dry.py)
  --broken-pos P,...  chain positions whose measured bit is flipped asymmetrically: 1 -> 0 with probability --q10,
                      0 -> 1 with --q01 (a decay-like fault that a |1> suffers and a |0> does not). The positions are
                      chosen by hand, not where any device's qubits failed.

  python notes/ohm_ruler3_2026-11-25/dry3.py OUT [--flip 0.02] [--broken-pos 15,18,22 --q10 0.4] [--seed 1]
"""
import argparse
import json
import os

import numpy as np
from qiskit import qpy


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--flip", type=float, default=0.0)
    ap.add_argument("--broken-pos", default="")
    ap.add_argument("--q10", type=float, default=0.0)
    ap.add_argument("--q01", type=float, default=0.0)
    ap.add_argument("--seed", type=int, default=20261125)
    a = ap.parse_args()
    from psf_os import feedforward as FF
    from qiskit.transpiler.passes import RemoveBarriers
    from qiskit_aer import AerSimulator
    job = os.path.join(a.out, "job")
    b = json.load(open(os.path.join(a.out, "build.json")))
    phys_of = {}
    for w in b["items"].values():
        phys_of.update(dict(zip(w["positions"], w["physical"])))
    broken = {phys_of[int(p)] for p in a.broken_pos.split(",") if p} if a.broken_pos else set()
    man = json.load(open(os.path.join(job, "manifest.json")))
    circs = qpy.load(open(os.path.join(job, "circuits.qpy"), "rb"))
    rng = np.random.default_rng(a.seed)
    sim = AerSimulator(method="statevector")
    rows, skipped = [], []
    for k, c in enumerate(circs):
        nb = c.num_clbits
        q_of_clbit = {}
        for ins in c.data:
            if ins.operation.name == "measure":
                q_of_clbit[c.find_bit(ins.clbits[0]).index] = c.find_bit(ins.qubits[0]).index
        cc = FF.compact(RemoveBarriers()(c))
        if cc.num_qubits > 28:
            rows.append(dict(pub=k, counts={"0" * nb: man["shots"]}))
            skipped.append(k)
            continue
        mem = sim.run(cc, shots=man["shots"], memory=True, seed_simulator=a.seed + 10007 * k).result().get_memory(0)
        bits = np.array([[int(ch) for ch in m.replace(" ", "")] for m in mem], dtype=np.int8)
        if a.flip:
            bits ^= (rng.random(bits.shape) < a.flip).astype(np.int8)
        for j in range(nb):                       # column j holds clbit nb - 1 - j
            if q_of_clbit.get(nb - 1 - j) in broken:
                col = bits[:, j]
                u = rng.random(col.shape)
                bits[:, j] = np.where(col == 1, (u >= a.q10).astype(np.int8), (u < a.q01).astype(np.int8))
        counts = {}
        for row in bits:
            key = "".join(map(str, row))
            counts[key] = counts.get(key, 0) + 1
        rows.append(dict(pub=k, counts=counts))
    tag = f"flip{a.flip}-broken{a.broken_pos or 'none'}-q10{a.q10}-q01{a.q01}-{a.seed}"
    json.dump(dict(job_id=f"local-dry-{tag}", submitted="dry", local=True, backend=man["fetch"]["backend"],
                   simulator=f"aer statevector; {tag} (ILLUSTRATIVE)", broken_physical=sorted(broken),
                   sentinel_not_sampled=skipped), open(os.path.join(job, "submission.json"), "w"), indent=1)
    json.dump(dict(fetched="dry", job_id=f"local-dry-{tag}", status="DONE (dry)", rows=rows),
              open(os.path.join(job, "raw_counts.json"), "w"))
    print(f"{len(circs)} circuits; sentinel pubs not sampled: {skipped}; {tag}; broken physical {sorted(broken)}")


if __name__ == "__main__":
    main()
