"""What the smallest change to verify would give (workplace VS Claude, 2026-11-19): psf_os.loop.same_job is wrapped
in memory, never in the file, so that when circuits.qpy's bytes differ the per-cell byte hashes of the manifest
(cells[*].qpy_sha256, cells[*].run_sha256) are left out as the top-level ones already are. Then verify is run on a
night recorded on another machine.

  python vs_patched_verify.py NIGHT
"""
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "gpu"))
from psf_os import loop as LP  # noqa: E402
import os_loop as O  # noqa: E402

CELL_KEYS = ("qpy_sha256", "run_sha256")
_orig = LP.same_job


def same_job(rec_job, new_job):
    a = open(os.path.join(rec_job, "circuits.qpy"), "rb").read()
    b = open(os.path.join(new_job, "circuits.qpy"), "rb").read()
    if a == b:
        return _orig(rec_job, new_job)
    tmp = tempfile.mkdtemp()
    try:
        jobs = []
        for src, tag in ((rec_job, "a"), (new_job, "b")):
            d = os.path.join(tmp, tag)
            shutil.copytree(src, d)
            m = json.load(open(os.path.join(d, "manifest.json")))
            for c in m.get("cells", []):
                for k in CELL_KEYS:
                    c.pop(k, None)
            json.dump(m, open(os.path.join(d, "manifest.json"), "w"))
            jobs.append(d)
        return _orig(*jobs)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


LP.same_job = same_job
ok = LP.verify(sys.argv[1], O.RusLoop(), False)
print("verify with the per-cell byte hashes left out:", "SAME" if ok else "DIFFERENT")
