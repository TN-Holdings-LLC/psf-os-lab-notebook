"""psf-os after-2026-11-20 run_local seed slots: do the noiseless dry runs of the declared tools read the same words
with the new default seeds as with v0.2.0's (stride=1)? (workplace Claude, 2026-11-20; no device)

Per tool: one build (the dry Clifford sentinel), copied twice; run_local(stride=1) on one copy, run_local() on the
other (the tool's documented seed); the tool's score on each; the words (verdict lines) compared. Writes
seed_stride_check.txt beside this file.

  python notes/receivers_2026-11-20/seed_stride_check.py DEVDIR WORK      (psf-os after-2026-11-20 on the path)
"""
import os
import re
import shutil
import subprocess
import sys

NB = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
TOOLS = [   # name, build args (after DEVDIR OUT), score args (after OUT), run_local seed
    ("ff_night", ["--k", "1", "2", "4"], [], 20261116),
    ("rus_night", [], [], 20261116),
    ("qpe_repro_night A", ["--part", "A"], [], 20261119),
    ("qpe_repro_night B", ["--part", "B"], [], 20261119),
]
WORDS = re.compile(r"BEYOND|NOT BEYOND|KEEPS|SAME|HELPS|SHOWN|PASS|FAIL|->")


def sh(args, log):
    r = subprocess.run([sys.executable] + args, cwd=NB, capture_output=True, text=True)
    open(log, "w").write(r.stdout + r.stderr)
    if r.returncode not in (0,):
        raise SystemExit(f"{' '.join(args)} failed: {(r.stdout + r.stderr)[-800:]}")
    return r.stdout


def main():
    devdir, work = sys.argv[1], sys.argv[2]
    os.makedirs(work, exist_ok=True)
    from psf_os import feedforward as FF
    lines = []
    for name, bargs, sargs, seed in TOOLS:
        n0 = len(lines)
        tool = "gpu/" + name.split()[0] + ".py"
        tag = name.replace(" ", "_")
        base = os.path.join(work, tag)
        if not os.path.exists(base):
            sh([tool, "build", devdir, base] + bargs + ["--dry-clifford-sentinel"], base + "_build.txt")
        outs = {}
        for which, st in (("old", 1), ("new", None)):
            d = f"{base}_{which}"
            if not os.path.exists(d):
                shutil.copytree(base, d)
                FF.run_local(d, seed=seed, stride=st)
            outs[which] = sh([tool, "score", d] + sargs, d + "_score.txt")
        w = {k: [ln for ln in v.splitlines() if WORDS.search(ln)] for k, v in outs.items()}
        strip = lambda ln: re.sub(r"[-+]?\d+(\.\d+)?", "#", ln)
        same = [strip(x) for x in w["old"]] == [strip(x) for x in w["new"]]
        lines.append(f"{name}: {'SAME WORDS' if same else 'WORDS DIFFER'} ({len(w['old'])} verdict lines)")
        if not same:
            for a, b in zip(w["old"], w["new"]):
                if strip(a) != strip(b):
                    lines.append(f"  old: {a}\n  new: {b}")
        print("\n".join(lines[n0:]), flush=True)
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed_stride_check.txt"), "w").write(
        "\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
