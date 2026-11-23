"""Test forms with few seconds (home VS, 2026-11-23; desk, no device; NOT a declaration draft, no prediction).

Counts per plan: items (arm x cycles x strings x twin), circuits as psf-os's user entrance builds them (each item with
its floor and mirror: 3 circuits, plus one ring sentinel per job), seconds by the project's time model
(psf_os.job.qpu_seconds: 0.036 s per circuit + 0.00027 s per shot + 3 s per job), the qubits and CZ of the circuits
from cone.json, and the shot error of W over the light-cone window read from the 11-12 records' per-pair shot errors
(notes/ohm_idle_2026-11-23/reciprocity.json), scaled to the plan's pairs and shots (beside, a rough guide).

usage: PYTHONPATH=<psf-os 0.3.3> python notes/ohm_readable_2026-11-23/design.py OUT.json
"""
import json
import os
import sys

import numpy as np

NB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HERE = os.path.dirname(os.path.abspath(__file__))

PLANS = {
    "A_shallow_cone": dict(what="light-cone circuits only, t = 1, 2, 3, 4, arms A0 / A1 / A2, 7 pairs (14 strings)",
                           arms=3, ts=(1, 2, 3, 4), strings=14, twin=False, shots=1000),
    "B_twin_cone_full": dict(what="t = 1 and 3, arms A0 / A1 / A2, 7 pairs; each circuit twice in the job: the "
                                  "light-cone circuit and the 40-qubit circuit (same window)",
                             arms=3, ts=(1, 3), strings=14, twin=True, shots=1000),
}


def main(out):
    from psf_os import job as J
    cone = json.load(open(os.path.join(HERE, "cone.json")))["rows"]
    rec = json.load(open(os.path.join(NB, "notes/ohm_idle_2026-11-23/reciprocity.json")))["cells"]
    # per-pair shot SE of S on the light-cone window at t = 3 in the records (1000 shots); W = (M_s - M_c)/2 has the
    # same per-pair shot SE / 2; over P pairs: / sqrt(P)
    se_pair = float(np.mean([p["se_shots"] for k, c in rec.items() if k.endswith("_t3")
                             for p in c["light_cone"]["pairs"]]))
    res = dict(note="not a declaration draft; no prediction; seconds by psf_os.job.qpu_seconds", plans={},
               se_pair_S_light_cone_t3_records=se_pair)
    for name, p in PLANS.items():
        items = p["arms"] * len(p["ts"]) * p["strings"] * (2 if p["twin"] else 1)
        circuits = 3 * items + 1
        sec = J.qpu_seconds(circuits, p["shots"])
        per_t = {}
        for t in p["ts"]:
            r = cone[f"A1_t{t}"]
            per_t[t] = dict(cone_qubits=r["cone_qubits"], cz_cone_A1=r["cz_cone"], cz_full_A1=r["cz_full"],
                            cz_layers=r["cz_layers_cone"])
        se_W = se_pair / 2 / np.sqrt(p["strings"] // 2) * np.sqrt(1000 / p["shots"])
        res["plans"][name] = dict(p, ts=list(p["ts"]), items=items, circuits=circuits, qpu_seconds_model=round(sec, 1),
                                  per_t=per_t, se_W_light_cone_rough=float(se_W))
        print(f"{name}: {items} items, {circuits} circuits, {p['shots']} shots -> {sec:.1f} s (model); "
              f"shot SE of W on the window about {se_W:.3f} (rough, from the records)")
    json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
