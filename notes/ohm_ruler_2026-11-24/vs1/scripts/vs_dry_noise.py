"""Dry runs of gpu/ohm_ruler_night.py's job under an ILLUSTRATIVE gate noise (workplace VS, 2026-11-24, sono1; author
The Architect). Desk or pod only, never a device; the noise is written by hand and never fitted to any device.

Every circuit is compacted to its active qubits and sampled by Aer's matrix-product-state method (one noise trajectory
per shot), with a two-qubit depolarizing error p2 after every CZ. From the same shots, one raw_counts.json per readout
flip q in FLIPS is written (each measured bit flipped with probability q, independently: the readout-like noise of the
workplace's dry.py), so the gate-noise samples are shared between the flip settings. The ring sentinel (40 qubits) is
given all-zero counts, as in the workplace's dry.py.

  python vs_dry_noise.py BUILT_OUT WORK_DIR --p2 0.01 --flips 0 0.02 --seed S
writes WORK_DIR/p2{p2}_q{q}_s{S}/ (a copy of BUILT_OUT with job/raw_counts.json and job/submission.json)
"""
import argparse
import json
import os
import shutil
import time

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("built")
    ap.add_argument("work")
    ap.add_argument("--p2", type=float, required=True)
    ap.add_argument("--flips", type=float, nargs="+", default=[0.0])
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--skip", nargs="*", default=[], help="cell-name parts not simulated (given all-zero counts and "
                    "listed in submission.json; their cells are left out of every table), e.g. _t4_")
    a = ap.parse_args()
    from qiskit import qpy
    from qiskit.transpiler.passes import RemoveBarriers
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, depolarizing_error
    from psf_os import feedforward as FF
    job = os.path.join(a.built, "job")
    man = json.load(open(os.path.join(job, "manifest.json")))
    circs = qpy.load(open(os.path.join(job, "circuits.qpy"), "rb"))
    nm = NoiseModel()
    if a.p2:
        nm.add_all_qubit_quantum_error(depolarizing_error(a.p2, 2), ["cz"])
    sim = AerSimulator(method="matrix_product_state", noise_model=nm if a.p2 else None)
    t0 = time.time()
    mems, skipped = [], []
    cname = {cl["cell"]: cl["name"] for cl in man["cells"]}
    for k, c in enumerate(circs):
        if any(s in cname[man["pubs"][k]["cell"]] for s in a.skip):
            mems.append(None)
            skipped.append(k)
            continue
        cc = FF.compact(RemoveBarriers()(c))
        nb = c.num_clbits
        if cc.num_qubits > 28:
            mems.append(None)
            skipped.append(k)
            continue
        mem = sim.run(cc, shots=man["shots"], memory=True, seed_simulator=a.seed + 10007 * k).result().get_memory(0)
        mems.append(np.array([[int(ch) for ch in m.replace(" ", "")] for m in mem], dtype=np.int8))
    for q in a.flips:
        rng = np.random.default_rng(a.seed * 7 + int(round(q * 1e6)))
        rows = []
        for k, (c, bits) in enumerate(zip(circs, mems)):
            if bits is None:
                rows.append(dict(pub=k, counts={"0" * c.num_clbits: man["shots"]}))
                continue
            b = bits.copy()
            if q:
                b ^= (rng.random(b.shape) < q).astype(np.int8)
            counts = {}
            for row in b:
                key = "".join(map(str, row))
                counts[key] = counts.get(key, 0) + 1
            rows.append(dict(pub=k, counts=counts))
        out = os.path.join(a.work, f"p2{a.p2}_q{q}_s{a.seed}")
        if os.path.exists(out):
            raise SystemExit(f"{out} exists")
        shutil.copytree(a.built, out)
        jid = f"local-vsdry-p2{a.p2}-q{q}-{a.seed}"
        json.dump(dict(job_id=jid, submitted="dry", local=True, backend=man["fetch"]["backend"],
                       simulator=f"aer matrix_product_state, depolarizing p2 {a.p2} after every cz, readout flip {q} "
                                 "(ILLUSTRATIVE, never fitted)", not_sampled=skipped, skip=a.skip),
                  open(os.path.join(out, "job", "submission.json"), "w"), indent=1)
        json.dump(dict(fetched="dry", job_id=jid, status="DONE (dry)", rows=rows),
                  open(os.path.join(out, "job", "raw_counts.json"), "w"))
    print(f"{len(circs)} circuits, p2 {a.p2}, flips {a.flips}, seed {a.seed}: {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
