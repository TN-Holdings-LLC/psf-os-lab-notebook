"""The branch-cost night's job (plan d, L = 4500 dt) rebuilt with psf-os 0.3.2 (candidate) on the night's device record
with its dt (results/ipe-branch-cost-night-2026-11-22/dt.txt): the limit refuses it, allow_long_delay builds it, and
the time model with the delays is set beside the 112 s charged (home VS, 2026-11-23; desk).

  PYTHONPATH=<psf-os 0.3.2> python notes/units_charge_2026-11-23/branch_night_priced.py OUT
"""
import dataclasses
import json
import os
import sys

NB = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(NB, "gpu"))
import ipe_branch_cost_night as B  # noqa: E402  (declared 2026-11-22; read only: its items)
import psf_os  # noqa: E402
from psf_os import feedforward as FF  # noqa: E402
from psf_os import job as J  # noqa: E402
from psf_os.device import Device  # noqa: E402

out = sys.argv[1]
R = os.path.join(NB, "results", "ipe-branch-cost-night-2026-11-22")
dt = float(open(os.path.join(R, "dt.txt")).read().split()[0])
dev = dataclasses.replace(Device.load(os.path.join(R, "fetch_in", "ibm_fez", "dev")), dt=dt)
items = []
for tag, n, j, form, dl, sp in B.plan_items("d", 4500):
    qc, succ = B.ipe_form(n, j, form, True, dl, sp)
    off, _ = B.ipe_form(n, j, "OFF", False, 0, sp)
    items.append((tag, qc, dict(success=succ, off_circuit=off, form="blocks")))
kw = dict(shots=2950, max_seconds=200, sentinel_spec=None, ff_only=[t for t, _, _ in items], park=True,
          park_likely=True, footprint=True, declared="0.3.1")
lines = [f"psf-os {psf_os.__version__}; dt {dt:g} s; limit {J.DELAY_LIMIT_US:g} us"]
try:
    FF.build(dev, items, os.path.join(out, "refused"), **kw)
    lines.append("without allow_long_delay: BUILT (not expected)")
except RuntimeError as e:
    lines.append(f"without allow_long_delay: refused: {e}")
rep = FF.build(dev, items, os.path.join(out, "allowed"), allow_long_delay=True, **kw)
man = json.load(open(os.path.join(out, "allowed", "job", "manifest.json")))
d = man["delays"]
us = sorted({c["us"] for c in d["per_circuit"]})
base = J.qpu_seconds(rep["circuits"], 2950)
rel = 2.6 + 0.000269 * rep["circuits"] * 2950
lines += [f"with allow_long_delay: {rep['circuits']} circuits; delays per circuit (us) {us}",
          f"model without delays {base:.1f} s; delays {d['qpu_seconds_delays']} s; qpu_seconds_model {rep['qpu_seconds_model']} s",
          f"charged 112 s: model {rep['qpu_seconds_model'] - 112:+.1f} s ({(rep['qpu_seconds_model'] - 112) / 112:+.1%}); "
          f"the 105-job relation with the delays {rel + d['qpu_seconds_delays']:.1f} s"]
print("\n".join(lines))
open(os.path.join(out, "priced.txt"), "w").write("\n".join(lines) + "\n")
