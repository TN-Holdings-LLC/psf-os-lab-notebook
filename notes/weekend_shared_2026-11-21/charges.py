"""The charged seconds of every recorded device job against its circuits and shots (home VS, 2026-11-21): is the
cost per job a fixed part plus a part in proportion to circuits x shots, as the project's time model says? Reads
results/**/job/raw_counts.json (metrics.usage) and manifest.json; numpy least squares."""
import glob
import json
import os
import sys

import numpy as np

root = sys.argv[1] if len(sys.argv) > 1 else "results"
rows = []
for p in sorted(glob.glob(os.path.join(root, "**", "job", "raw_counts.json"), recursive=True)):
    try:
        r = json.load(open(p))
        m = json.load(open(os.path.join(os.path.dirname(p), "manifest.json")))
    except (OSError, ValueError):
        continue
    u = (r.get("metrics") or {}).get("usage") or {}
    if "qpu_charge_time_seconds" not in u:
        continue
    n, s = len(m["pubs"]), m["shots"]
    rows.append((n * s, n, s, u["qpu_charge_time_seconds"], m.get("qpu_seconds_model"), p.split(os.sep)[1]))
rows.sort()
for x in rows:
    print("%8d circuit-shots  %4d circuits x %5d shots  charged %3d s  model %s  %s" % x)
A = np.array([[1, x[1], x[0]] for x in rows], float)
y = np.array([x[3] for x in rows], float)
c = np.linalg.lstsq(A, y, rcond=None)[0]
print(f"{len(rows)} jobs; fit: charged = {c[0]:.2f} s + {c[1]:.4f} s per circuit + {c[2]:.6f} s per circuit-shot; "
      f"largest residual {np.max(np.abs(A @ c - y)):.1f} s")
A2 = A[:, [0, 2]]
c2 = np.linalg.lstsq(A2, y, rcond=None)[0]
print(f"fit without the per-circuit term: charged = {c2[0]:.2f} s + {c2[1]:.6f} s per circuit-shot; largest residual "
      f"{np.max(np.abs(A2 @ c2 - y)):.1f} s")
mod = [(x[3], x[4]) for x in rows if x[4]]
print(f"charged / model over {len(mod)} jobs with a model value: {sum(a for a, _ in mod) / sum(b for _, b in mod):.3f}")
