"""Daily record, step 1 at home (VPN OFF): read the queue (pending jobs only) of ibm_marrakesh, ibm_fez, ibm_kingston,
choose the night's devices by the standing rule (every device with at most 10 pending jobs; if none, the one with
the fewest; ties in that order), then `psf-os fetch` each into OUT_BASE/<device>/dev.

Uses the saved IBM account only; reads no key and no quality number. Run from ~/toqb_push_2026-10-15.
2026-11-23: also writes OUT_BASE/<device>/dt.txt, the clock step of the backend configuration (a unit of time).
2026-11-23 (psf-os 0.3.3rc1): also writes OUT_BASE/<device>/timing.json, the lengths of time of the backend's Target
(x, sx, cz, measure, reset per qubit or coupler, in dt) and its timing constraints, read with psf_os.device.timing_of
(only an instruction's duration, never an error number). With a psf-os before 0.3.3rc1 it writes "timing": null.
usage: python daily_fetch_2026-11-05.py OUT_BASE
"""
import datetime as dt
import json
import os
import subprocess
import sys

from qiskit_ibm_runtime import QiskitRuntimeService

ORDER = ["ibm_marrakesh", "ibm_fez", "ibm_kingston"]
LIMIT = 10
base = sys.argv[1]
if os.path.exists(base):
    raise SystemExit(f"STOP: {base} exists")
svc = QiskitRuntimeService()
q = {n: svc.backend(n).status().pending_jobs for n in ORDER}
chosen = [n for n in ORDER if q[n] <= LIMIT] or [min(ORDER, key=lambda n: (q[n], ORDER.index(n)))]
os.makedirs(base)
json.dump(dict(pending=q, read=dt.datetime.now(dt.timezone.utc).isoformat(), limit=LIMIT, chosen=chosen),
          open(os.path.join(base, "queue.json"), "w"), indent=1)
print("queue", q, "-> chosen", chosen)
for n in chosen:
    subprocess.run([sys.executable, "-m", "psf_os", "fetch", "--backend", n, "--out", os.path.join(base, n, "dev")],
                   check=True)
    # 2026-11-23: the device's clock step dt (seconds), from the backend configuration (Target.dt). A unit of time,
    # the same for every qubit, not a calibration or quality number: it converts delays between dt and seconds.
    # psf-os 0.3.2 also writes it into device.json; dt.txt keeps it beside the record for every psf-os.
    step = svc.backend(n).target.dt
    open(os.path.join(base, n, "dt.txt"), "w").write(f"{step!r}\n" if step else "none\n")
    # 2026-11-23 (psf-os 0.3.3rc1): lengths of time and the timing constraints, beside the record for every psf-os
    try:
        from psf_os.device import timing_of
    except ImportError:
        timing_of = None
    tm = timing_of(svc.backend(n).target, step) if timing_of else None
    json.dump(dict(timing=tm, dt=step), open(os.path.join(base, n, "timing.json"), "w"), indent=1)
print("fetched:", ", ".join(chosen))
