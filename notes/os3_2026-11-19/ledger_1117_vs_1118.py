"""The ledger between the real records of 2026-11-17 and 2026-11-18 (same device, other calibration times): not used.
usage (notebook root): PYTHONPATH=gpu python notes/os3_2026-11-19/ledger_1117_vs_1118.py"""
import json
import sys

sys.path.insert(0, "gpu")
import os3_run as R  # noqa: E402

D17 = "results/os-night-2026-11-17/fetch_in/ibm_marrakesh/dev"
D18 = "results/os2-night-2026-11-18/fetch_in/ibm_marrakesh/dev"
lines = []
n17, c17 = R.calibration_time(D17)
n18, c18 = R.calibration_time(D18)
led17 = [dict(night="2026-11-17 (its last stacks as recorded: P2 at L = 1, 2, 3)", device=n17, calibration_time=c17,
              last_stacks={"1": ["P2"], "2": ["P2"], "3": ["P2"]})]
st, dec = R.ledger_start(led17, n18, c18, {"1": "P1", "2": "P1", "3": "P1"})
lines.append(f"ledger 2026-11-17 ({n17}, calibration {c17}) -> night on the 2026-11-18 record ({n18}, calibration {c18}): "
             f"used {dec['used']} ({dec['why']}); round 1 stacks {st}")
sim = json.load(open("notes/os3_2026-11-19/ledger_sim_ledger.json"))
n1 = [e for e in sim if e["night"] == "night1_same_record"]
st, dec = R.ledger_start(n1, n17, c17, {"1": "P2", "2": "P1", "3": "P1"})
lines.append(f"ledger = simulated night 1 on the 2026-11-18 record -> a night on the 2026-11-17 record: used {dec['used']} "
             f"({dec['why']})")
print("\n".join(lines))
open("notes/os3_2026-11-19/ledger_1117_vs_1118.txt", "w").write("\n".join(lines) + "\n")
