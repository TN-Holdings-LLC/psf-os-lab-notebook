"""Rebuild results/parallel-night-2026-11-18 with psf-os v0.2, build_bundle given allow_conditional_neighbours=True
(the flag a test of the loss itself is built with; the declared gpu/parallel_night.py runs unchanged, this wrapper
passes the flag), and compare every qpy byte for byte. usage: PYTHONPATH=PSF_OS:NB:NB/gpu python THIS NB"""
import os
import runpy
import subprocess
import sys

NB = os.path.abspath(sys.argv[1])
from psf_os import feedforward as FF  # noqa: E402

_orig = FF.build_bundle
FF.build_bundle = lambda *a, **k: _orig(*a, **dict(k, allow_conditional_neighbours=True))
dst = "/tmp/v02_rebuild_parallel_flag"
subprocess.run(["rm", "-rf", dst])
src = os.path.join(NB, "results/parallel-night-2026-11-18")
sys.argv = ["gpu/parallel_night.py", "build", os.path.join(src, "fetch_in/ibm_marrakesh/dev"), dst]
os.chdir(NB)
try:
    runpy.run_path(os.path.join(NB, "gpu/parallel_night.py"), run_name="__main__")
except SystemExit:
    pass
bad, n = [], 0
for sub in ("pa/runs", "pb/runs", "pa/job", "pb/job"):
    for f in sorted(x for x in os.listdir(os.path.join(src, sub)) if x.endswith(".qpy")):
        n += 1
        if open(os.path.join(src, sub, f), "rb").read() != open(os.path.join(dst, sub, f), "rb").read():
            bad.append(f"{sub}/{f}")
line = (f"parallel P-A + P-B (allow_conditional_neighbours=True by the wrapper): {n} qpy files compared, "
        + ("all byte-identical" if not bad else f"DIFFERENT: {bad}"))
print(line)
open(os.path.join(NB, "notes/v02_2026-11-18/rebuild_parallel_with_flag.txt"), "w").write(line + "\n")
