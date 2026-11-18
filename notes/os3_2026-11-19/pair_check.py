"""Part C, two direct checks of gpu/os3_run.ledger_start (home VS Claude, 2026-11-18 night; desk only):
  1. the 2026-11-17 and 2026-11-18 marrakesh records (same device, other calibration times) in both directions: the
     ledger must not be used;
  2. same device and calibration time, but tonight's diagnostics disagree with the ledger on one L (ledger P0, tonight
     P2): the diagnostics win for that L, the ledger is used for the others.
usage: PYTHONPATH=PSF_OS:NB:NB/gpu python notes/os3_2026-11-19/pair_check.py   (writes pair_check.txt beside)"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(NB, "gpu"))
import os3_run as R  # noqa: E402

d17 = os.path.join(NB, "results/os-night-2026-11-17/fetch_in/ibm_marrakesh/dev")
d18 = os.path.join(NB, "results/os2-night-2026-11-18/fetch_in/ibm_marrakesh/dev")
c17, c18 = R.calibration_time(d17), R.calibration_time(d18)
pick = {"1": "P2", "2": "P1", "3": "P1"}
last = {"1": ["P2", "B"], "2": ["P1", "M"], "3": ["P2", "B"]}
out, ok = [], True
for (na, ca), (nb, cb), tag in [(c17, c18, "11-17 -> 11-18"), (c18, c17, "11-18 -> 11-17")]:
    led = [dict(device=na, calibration_time=ca, ladder="B", last_stacks=last)]
    st, dec = R.ledger_start(led, nb, cb, pick)
    good = (not dec["used"]) and st == {L: [p] for L, p in pick.items()}
    ok &= good
    out.append(f"{tag}: used {dec['used']} ({dec['why']}); round 1 {st}; {'OK' if good else 'FAIL'}")
led = [dict(device=c18[0], calibration_time=c18[1], ladder="B", last_stacks=dict(last, **{"1": ["P0"]}))]
st, dec = R.ledger_start(led, c18[0], c18[1], pick)
good = st["1"] == ["P2"] and st["2"] == ["P1", "M"] and st["3"] == ["P2", "B"]
ok &= good
out.append(f"disagreement on L1 (ledger P0, tonight P2): round 1 {st}; per L {dec['per_L']}; {'OK' if good else 'FAIL'}")
out.append("PASS" if ok else "FAIL")
print("\n".join(out))
open(os.path.join(HERE, "pair_check.txt"), "w").write("\n".join(out) + "\n")
