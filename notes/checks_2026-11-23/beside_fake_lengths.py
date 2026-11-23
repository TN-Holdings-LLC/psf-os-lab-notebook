"""Beside, never judged: the 2026-11-22 branch-cost night's circuits, as rebuilt by recheck_nights.py, timed with the
lengths of qiskit-ibm-runtime's FakeFez snapshot (conf_fez.json / props_fez.json shipped with the package): THE FAKE
BACKEND'S VALUES, NOT THE DEVICE'S RECORD (the night's device record holds no durations). psf_os.compiled.lengths:
as soon as possible per qubit; a conditional's wait is its measurement plus its longest block, a lower bound (the
decision latency is in no record).

usage: PYTHONPATH=<psf-os 0.3.3rc1> python notes/checks_2026-11-23/beside_fake_lengths.py REBUILT_JOB_DIR
"""
import json
import os
import statistics
import sys

from qiskit import qpy

from psf_os import compiled as CP
from psf_os import device as Dv


def main(job):
    fake = Dv.fetch_fake("FakeFez")
    man = json.load(open(os.path.join(job, "manifest.json")))
    names = [c["name"] for c in man["cells"] for _ in range(c["points"])]
    cs = qpy.load(open(os.path.join(job, "circuits.qpy"), "rb"))
    rows = {}
    for name, c in zip(names, cs):
        if not name.startswith("ff_") or name.endswith(("_off", "_floor")):
            continue
        form = name[3:].rsplit("_", 1)[0]          # the tag without its phase: form and n
        ln = CP.lengths(c, fake.timing, fake.dt)
        if not ln or "length_dt" not in ln:
            continue
        r = rows.setdefault(form, dict(length_us=[], cond_waits_dt=[]))
        r["length_us"].append(ln["length_us"])
        if "conditionals" in ln:
            r["cond_waits_dt"] += [m + b for m, b in ln["conditionals"]["wait_dt_lower"]]
    out = {}
    for form, r in sorted(rows.items()):
        w = r["cond_waits_dt"]
        out[form] = dict(circuits=len(r["length_us"]), length_us_median=round(statistics.median(r["length_us"]), 3),
                         conditionals=len(w),
                         cond_wait_dt_lower_median=statistics.median(w) if w else None,
                         cond_wait_us_lower_median=round(statistics.median(w) * fake.dt * 1e6, 3) if w else None)
    doc = dict(note="FakeFez snapshot values (qiskit-ibm-runtime fake_provider), not the device's record; beside, "
                    "never judged; conditional waits are lower bounds (no decision latency)",
               fake=dict(dt=fake.dt, constraints=fake.timing["constraints"],
                         x=sorted(set(fake.timing["durations"]["x"].values())),
                         measure=sorted(set(fake.timing["durations"]["measure"].values())),
                         cz=sorted(set(fake.timing["durations"]["cz"].values()))),
               L_dt=4500, L_us=round(4500 * fake.dt * 1e6, 3), forms=out)
    print(json.dumps(doc, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
