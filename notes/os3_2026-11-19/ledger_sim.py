"""Part C, the ledger, simulated (home VS Claude, 2026-11-18 night; desk only; the noise is ILLUSTRATIVE, never fitted
to a device). Four nights through gpu/os3_run.py with one ledger file:
  1. night 1 on the 2026-11-18 marrakesh record (results/os2-night-2026-11-18/fetch_in): empty ledger, from scratch;
  2. night 2 on the same record (same device, same calibration time), other seeds: round 1 starts from night 1's last
     stacks where the night's diagnostics agree; fewer rounds to the stop;
  3. night 3 on a copy of the same record with only source.calibration_time changed: the ledger is not used;
  4. night 4 on the 2026-11-17 marrakesh record (results/os-night-2026-11-17/fetch_in, calibration 2026-11-13 18:22):
     same device, another calibration time: the ledger is not used.
usage: PYTHONPATH=PSF_OS:NB:NB/gpu python notes/os3_2026-11-19/ledger_sim.py LADDER NOISE.json WORK
writes notes/os3_2026-11-19/ledger_sim.json / .txt and WORK/ledger.json"""
import contextlib
import io
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(NB, "gpu"))
import os3_run as R  # noqa: E402

lad, noise_f, work = sys.argv[1], sys.argv[2], sys.argv[3]
noise = json.load(open(noise_f))
shutil.rmtree(work, ignore_errors=True)
os.makedirs(work)
led = os.path.join(work, "ledger.json")
d18 = os.path.join(NB, "results/os2-night-2026-11-18/fetch_in/ibm_marrakesh/dev")
d17 = os.path.join(NB, "results/os-night-2026-11-17/fetch_in/ibm_marrakesh/dev")
dch = os.path.join(work, "dev_changed_calibration")
shutil.copytree(d18, dch)
dj = json.load(open(os.path.join(dch, "device.json")))
dj["source"]["calibration_time"] = "2026-11-19 10:40:00+01:00"        # only the time stamp is changed
json.dump(dj, open(os.path.join(dch, "device.json"), "w"), indent=1)
plan = [("night1_same_record", d18, 20261119), ("night2_same_record", d18, 20261119 + 70_000_000),
        ("night3_changed_calibration", dch, 20261119 + 140_000_000), ("night4_2026-11-17_record", d17, 20261119 + 210_000_000)]
lines, recs = [], {}
for name, dev, seed in plan:
    buf = io.StringIO()
    rec = R.night(dev, os.path.join(work, name), lad, noise, led, seed_base=seed, label=name)
    with contextlib.redirect_stdout(buf):
        R.show(rec)
    lines.append(buf.getvalue())
    print(buf.getvalue(), flush=True)
    recs[name] = dict(device=rec["device"], calibration_time=rec["calibration_time"], ledger=rec["ledger"],
                      diagnostics_pick=rec["diagnostics_pick"], round1_stacks=rec["round1_stacks"],
                      rounds_run=rec["rounds_run"], stop=rec.get("stop"), last_stacks=rec.get("last_stacks"),
                      last_g=rec.get("last_g"), model_seconds=rec["model_seconds"],
                      G=[x["G"] for x in rec.get("compound", {}).get("per_round", [])])
summary = (f"rounds: night 1 {recs['night1_same_record']['rounds_run']}, night 2 {recs['night2_same_record']['rounds_run']} "
           f"(ledger used {recs['night2_same_record']['ledger']['used']}), night 3 "
           f"{recs['night3_changed_calibration']['rounds_run']} (ledger used "
           f"{recs['night3_changed_calibration']['ledger']['used']}), night 4 {recs['night4_2026-11-17_record']['rounds_run']}"
           f" (ledger used {recs['night4_2026-11-17_record']['ledger']['used']})")
print(summary)
lines.append(summary)
json.dump(dict(ladder=lad, noise=noise, illustrative=True, nights=recs, ledger=json.load(open(led))),
          open(os.path.join(HERE, "ledger_sim.json"), "w"), indent=1, default=str)
open(os.path.join(HERE, "ledger_sim.txt"), "w").write("\n".join(lines) + "\n")
