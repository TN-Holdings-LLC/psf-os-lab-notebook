"""Run a declaration's device procedure word for word, without the device (workplace VS, 2026-11-25; home instruction
"道具の直し、その 3", 3). Author The Architect.

The first code block under the declaration's "Device procedure" heading is read line by line (comments after "#" are
dropped) and run in one bash session from the notebook's root, so a wrong argument stops here, before the night:
  - a line holding daily_fetch (it reads IBM) is not run: a recorded device folder (--fetch-in) is copied in its place;
  - a line holding "psf_os submit" or "psf_os collect" (they reach IBM) is not run;
  - a line holding " score " is not run (it needs the device's counts);
  - every other line (pick, build, check, ...) is run as written, with OUT -> a fresh folder, ANSWERS_SEALED -> the
    given answers file and "python" -> this interpreter. Nothing else in the line is changed.
It stops at the first line that fails and prints that line's last output lines. Nothing is sent and nothing in the
notebook is written (OUT is a temporary folder unless --out is given).

  python tools/procedure_dry.py PREREG.md --fetch-in RECORD/fetch_in --answers SEALED.json [--out DIR] [--keep]
Exit code: 0 when every line run passed; 1 at the first failure.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

SKIP = [(re.compile(r"daily_fetch"), "reads IBM: the recorded device folder is copied instead"),
        (re.compile(r"psf_os\s+(submit|collect)"), "reaches IBM: not run"),
        (re.compile(r"\sscore\s"), "needs the device's counts: not run")]


def procedure_lines(prereg):
    """The lines of the first code block under the "Device procedure" heading (comments dropped, blanks skipped)."""
    m = re.search(r"^#+\s*Device procedure.*?^```[^\n]*\n(.*?)^```", prereg, re.S | re.M)
    if not m:
        return []
    out = []
    for ln in m.group(1).splitlines():
        ln = re.sub(r"\s+#.*$", "", ln).strip()
        if ln and not ln.startswith("#"):
            out.append(ln)
    return out


def plan(lines, out_dir, answers, python):
    """[(line as declared, line as run or None, why not run)]."""
    steps = []
    for ln in lines:
        why = next((w for p, w in SKIP if p.search(" " + ln + " ")), None)
        run = None
        if why is None:
            run = re.sub(r"\bANSWERS_SEALED\b", answers.replace("\\", "/"), ln)
            run = re.sub(r"\bOUT\b", out_dir.replace("\\", "/"), run)
            run = re.sub(r"(^|[\s(;|&])python(?=\s)", lambda m: m.group(1) + '"' + python.replace("\\", "/") + '"', run)
        steps.append((ln, run, why))
    return steps


def run(prereg_path, fetch_in, answers, out_dir=None, keep=False, cwd=None, python=sys.executable):
    """[dict(line, run, status, tail)]; status one of PASS, FAIL, SKIPPED, NOT REACHED."""
    prereg = open(prereg_path, encoding="utf-8").read()
    tmp = out_dir or tempfile.mkdtemp(prefix="procedure_dry_")
    os.makedirs(tmp, exist_ok=True)
    steps = plan(procedure_lines(prereg), tmp, answers, python)
    script, res = ["cd " + repr((cwd or os.getcwd()).replace("\\", "/"))], []
    for i, (ln, cmd, why) in enumerate(steps):
        if cmd is None:
            if "daily_fetch" in ln:
                shutil.copytree(fetch_in, os.path.join(tmp, "fetch_in"), dirs_exist_ok=True)
            continue
        script += [f'echo "@@STEP {i}"', cmd, f'rc=$?; echo "@@RC {i} $rc"', '[ $rc = 0 ] || exit $rc']
    p = subprocess.run(["bash", "-c", "\n".join(script)], capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    text = p.stdout + "\n" + p.stderr
    rcs = {int(a): int(b) for a, b in re.findall(r"@@RC (\d+) (\d+)", p.stdout)}
    chunks = re.split(r"@@STEP (\d+)\n", p.stdout)
    outs = {int(chunks[j]): chunks[j + 1] for j in range(1, len(chunks) - 1, 2)}
    failed = False
    for i, (ln, cmd, why) in enumerate(steps):
        if cmd is None:
            res.append(dict(line=ln, run=None, status="SKIPPED", why=why, tail=""))
        elif failed:
            res.append(dict(line=ln, run=cmd, status="NOT REACHED", why="", tail=""))
        elif i in rcs and rcs[i] == 0:
            res.append(dict(line=ln, run=cmd, status="PASS", why="", tail=outs.get(i, "").strip()[-300:]))
        else:
            failed = True
            res.append(dict(line=ln, run=cmd, status="FAIL", why=f"exit {rcs.get(i, p.returncode)}",
                            tail=re.sub(r"@@RC.*\n?", "", outs.get(i, "") + "\n" + p.stderr).strip()[-600:]))
    if not keep and out_dir is None:
        shutil.rmtree(tmp, ignore_errors=True)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prereg")
    ap.add_argument("--fetch-in", required=True, help="a recorded device folder (results/NIGHT/fetch_in)")
    ap.add_argument("--answers", required=True, help="the sealed answers file the build reads")
    ap.add_argument("--out")
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    res = run(a.prereg, a.fetch_in, a.answers, a.out, a.keep)
    for r in res:
        print(f"{r['status']:11s} {r['line']}" + (f"   ({r['why']})" if r["why"] else ""))
        if r["status"] == "FAIL":
            print("   " + r["tail"].replace("\n", "\n   "))
    fail = any(r["status"] == "FAIL" for r in res)
    print(f"procedure_dry: {len(res)} lines, " + ", ".join(
        f"{s} {sum(r['status'] == s for r in res)}" for s in ("PASS", "FAIL", "SKIPPED", "NOT REACHED")))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
