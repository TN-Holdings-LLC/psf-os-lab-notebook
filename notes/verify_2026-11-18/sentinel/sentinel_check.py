"""Sentinel byte check of 2026-11-18 (home VS Claude): the night's jobs rebuilt in this environment from the recorded
device records (gpu/balanced_night.py build; gpu/timing_night.py build --part A / B with dt.json), compared file by
file with the recorded runs/*.qpy and job/circuits.qpy; for the ring-sentinel circuits, per circuit: a hash of the
qpy bytes, the operation counts and whether every gate is Clifford, so that another environment's rebuild can be
compared circuit by circuit. Versions recorded. usage: python sentinel_check.py NB OUTDIR (rebuilds in /tmp/sent_*)"""
import hashlib
import io
import json
import os
import platform
import subprocess
import sys

from qiskit import qpy

NB, OUT = sys.argv[1], sys.argv[2]
env = dict(os.environ, PYTHONPATH=":".join([os.path.expanduser("~/psf-os-ff"), NB, os.path.join(NB, "gpu")]))
jobs = {"balanced-repeat": ("results/balanced-repeat-2026-11-18", ".", ["gpu/balanced_night.py", "build"], []),
        "timing A": ("results/timing-night-2026-11-18", "tmA", ["gpu/timing_night.py", "build"], ["--part", "A"]),
        "timing B": ("results/timing-night-2026-11-18", "tmB", ["gpu/timing_night.py", "build"], ["--part", "B"])}
lines, res = [], {}


def say(s):
    print(s, flush=True)
    lines.append(s)


import importlib.metadata as md
vers = {p: md.version(p) for p in ("qiskit", "qiskit-aer", "qiskit-ibm-runtime", "numpy", "scipy", "rustworkx")}
vers["python"] = platform.python_version()
say(f"environment: {vers}")
say(f"owner PC (results/balanced-repeat-2026-11-18/versions.txt): "
    f"{open(os.path.join(NB, 'results/balanced-repeat-2026-11-18/versions.txt')).read().strip()} "
    "(python qiskit aer runtime numpy)")
for name, (rd, sub, cmd, extra) in jobs.items():
    src = os.path.join(NB, rd, sub)
    dst = f"/tmp/sent_check_{name.replace(' ', '_')}"
    subprocess.run(["rm", "-rf", dst])
    dev = os.path.join(NB, rd, "fetch_in", "ibm_marrakesh", "dev")
    args = [sys.executable, "-W", "ignore", os.path.join(NB, cmd[0]), cmd[1], dev, dst] + extra
    if "timing" in name:
        args += ["--dt-file", os.path.join(NB, rd, "dt.json")]
    subprocess.run(args, env=env, check=True, capture_output=True, cwd=NB)
    files = sorted(f for f in os.listdir(os.path.join(src, "runs")) if f.endswith(".qpy"))
    diff = [f for f in files if open(os.path.join(src, "runs", f), "rb").read() != open(os.path.join(dst, "runs", f), "rb").read()]
    jobsame = open(os.path.join(src, "job", "circuits.qpy"), "rb").read() == open(os.path.join(dst, "job", "circuits.qpy"), "rb").read()
    sent = [f for f in files if not f.startswith("ff_")]
    per = []
    for f in sent:
        circs = qpy.load(open(os.path.join(src, "runs", f), "rb"))
        for c in circs:
            b = io.BytesIO()
            qpy.dump([c], b)
            ops = dict(c.count_ops())
            cliff = all(op in ("cz", "x", "sx", "measure", "barrier", "delay", "id") or
                        (op == "rz") for op in ops)
            rz = [float(i.operation.params[0]) for i in c.data if i.operation.name == "rz"]
            import math
            cl_rz = all(abs((p / (math.pi / 2)) - round(p / (math.pi / 2))) < 1e-9 for p in rz)
            per.append(dict(file=f, circuit=c.name, sha256=hashlib.sha256(b.getvalue()).hexdigest(), ops=ops,
                            clifford=bool(cliff and cl_rz)))
    res[name] = dict(run_files=len(files), differ=diff, job_circuits_same=jobsame, sentinel=per)
    say(f"{name}: {len(files)} run files rebuilt, {len(diff)} differ {diff}; job/circuits.qpy "
        f"{'byte-identical' if jobsame else 'DIFFERS'}")
    for p in per:
        say(f"  sentinel {p['circuit']}: sha256 {p['sha256'][:16]}..., ops {p['ops']}, Clifford {p['clifford']}")
json.dump(dict(environment=vers, jobs=res), open(os.path.join(OUT, "sentinel_check.json"), "w"), indent=1)
open(os.path.join(OUT, "sentinel_check.txt"), "w").write("\n".join(lines) + "\n")
