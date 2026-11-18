"""psf-os v0.2 prototype (branch v0.2-proto-2026-11-18): with every new option at its default, the jobs of 2026-11-18
rebuild byte for byte (home VS Claude, 2026-11-18 evening; desk only). Each job is rebuilt from its recorded device
record with its declared tool (unchanged), psf-os from PSF_OS on the path, and every runs/*.qpy and job/circuits.qpy is
compared with the record. The manifest is not compared byte for byte (it carries its write time, and from v0.2 the
build environment); its circuits_sha256 is.
usage: PYTHONPATH=PSF_OS:NB:NB/gpu python notes/v02_2026-11-18/rebuild_check.py NB"""
import json
import os
import subprocess
import sys

NB = os.path.abspath(sys.argv[1])
R = "results"
JOBS = [
    ("balanced-repeat", f"{R}/balanced-repeat-2026-11-18", ".", ["gpu/balanced_night.py", "build", "{dev}", "{dst}"]),
    ("timing A", f"{R}/timing-night-2026-11-18", "tmA",
     ["gpu/timing_night.py", "build", "{dev}", "{dst}", "--part", "A", "--dt-file", f"{R}/timing-night-2026-11-18/dt.json"]),
    ("timing B", f"{R}/timing-night-2026-11-18", "tmB",
     ["gpu/timing_night.py", "build", "{dev}", "{dst}", "--part", "B", "--dt-file", f"{R}/timing-night-2026-11-18/dt.json"]),
    ("os2 Dw", f"{R}/os2-night-2026-11-18", "dw", ["gpu/wait_night.py", "build", "{dev}", "{dst}"]),
    ("os2 Dc", f"{R}/os2-night-2026-11-18", "dc", ["gpu/ctrl_night.py", "build", "{dev}", "{dst}"]),
    ("os2 round 1", f"{R}/os2-night-2026-11-18", "r1",
     ["gpu/os2_night.py", "build", "{dev}", "{dst}", f"{R}/os2-night-2026-11-18/RULE1.json"]),
    ("parallel P-A + P-B", f"{R}/parallel-night-2026-11-18", ".", ["gpu/parallel_night.py", "build", "{dev}", "{dst}"]),
]
lines = []


def say(s):
    print(s, flush=True)
    lines.append(s)


def compare(src, dst):
    out = {}
    for sub in sorted({os.path.dirname(os.path.relpath(os.path.join(dp, f), src))
                       for dp, _, fs in os.walk(src) for f in fs if f.endswith(".qpy") or f == "circuits.qpy"}):
        a, b = os.path.join(src, sub), os.path.join(dst, sub)
        for f in sorted(x for x in os.listdir(a) if x.endswith(".qpy")):
            fa, fb = os.path.join(a, f), os.path.join(b, f)
            out[os.path.join(sub, f)] = os.path.exists(fb) and open(fa, "rb").read() == open(fb, "rb").read()
    return out


def main():
    res = {}
    for name, rd, sub, cmd in JOBS:
        dev = os.path.join(rd, "fetch_in", "ibm_marrakesh", "dev")
        dst = f"/tmp/v02_rebuild_{name.replace(' ', '_').replace('+', '')}"
        subprocess.run(["rm", "-rf", dst])
        args = [sys.executable, "-W", "ignore"] + [c.replace("{dev}", dev).replace("{dst}", dst) for c in cmd]
        r = subprocess.run(args, cwd=NB, capture_output=True, text=True)
        if r.returncode != 0:
            last = (r.stdout + r.stderr).strip().splitlines()[-1:] or [str(r.returncode)]
            say(f"{name}: BUILD REFUSED / FAILED: {last[0][:400]}")
            res[name] = dict(built=False, why=last[0])
            continue
        src = os.path.join(NB, rd, sub)
        cmp_ = compare(src, os.path.join(dst) if sub == "." else dst)
        same = all(cmp_.values())
        bad = [k for k, v in cmp_.items() if not v]
        say(f"{name}: {len(cmp_)} qpy files compared, {'all byte-identical' if same else 'DIFFERENT: ' + str(bad)}")
        res[name] = dict(built=True, files=len(cmp_), same=same, different=bad)
    json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild_check.json"), "w"), indent=1)
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild_check.txt"), "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
