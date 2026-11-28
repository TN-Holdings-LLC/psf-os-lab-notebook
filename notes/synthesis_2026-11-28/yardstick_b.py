"""Analysis B: paper 9's line (r >= 1 - 1/sqrt 2 = 0.293) tested on the results recorded after 2026-11-16 that are
judged by the same reading (MSE <= half the mean square of the exact answer): the Ohm window and ruler nights,
2026-11-23 to 2026-11-27, raw M and raw W per cell. Reads only; the committed records are copied and scored by their
own declared scorers, unchanged except one added line after each scorer's ratio line that writes the vectors it
already holds (device and exact values) to a JSON-lines file. r = sum z e / sum e^2, as paper 9.

usage: python notes/synthesis_2026-11-28/yardstick_b.py --psf-os PATH [--json OUT]
"""
import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LINE = 1 - 1 / math.sqrt(2)
CAP = "__import__('json').dump({k: [float(x) for x in v] for k, v in %s.items()} | {'cell': %s}, " \
      "open(__import__('os').environ['YB_CAPTURE'], 'a')); open(__import__('os').environ['YB_CAPTURE'], 'a').write('\\n')"
INJECT = {
    "ohm_window_night.py": ("rM, rW = float(", "dict(z_M=d + ex, e_M=ex, z_W=wd, e_W=we)", 'f"{arm}_t{t}_{form}"'),
    "ohm_ruler_night.py": ("rM = float(", "dict(z_M=m_dev, e_M=m_ex, z_W=w_raw, e_W=w_ex)", 'f"{arm}_t{t}_{form}"'),
    "ohm_ruler_night3.py": ("rM = float(", "dict(z_M=m_dev, e_M=m_ex, z_W=w_raw, e_W=w_ex)", 'f"{arm}_t{t}_L"'),
}
NIGHTS = ["ohm-window-night-2026-11-23", "ohm-ruler-night-2026-11-24", "ohm-ruler3-night-2026-11-25",
          "ohm-ruler4-night-2026-11-26", "ohm-ruler5-night-2026-11-27"]


def patched_gpu(dst):
    shutil.copytree(os.path.join(ROOT, "gpu"), dst)
    for name, (anchor, vec, cell) in INJECT.items():
        p = os.path.join(dst, name)
        lines = open(p).read().split("\n")
        hits = [i for i, ln in enumerate(lines) if ln.strip().startswith(anchor)]
        assert len(hits) == 1, (name, hits)
        i = hits[0]
        ind = re.match(r"\s*", lines[i]).group(0)
        lines.insert(i + 1, ind + CAP % (vec, cell))
        open(p, "w").write("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--psf-os", required=True)
    ap.add_argument("--json")
    a = ap.parse_args()
    sys.path.insert(0, ROOT)
    import reproduce
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        gpu = os.path.join(tmp, "gpu")
        patched_gpu(gpu)
        for night in NIGHTS:
            folder, copies, cmd, _ = reproduce.RESULTS[night][:4]
            T = os.path.join(tmp, night)
            for c in copies:
                s = os.path.join(ROOT, folder, c)
                (shutil.copytree if os.path.isdir(s) else shutil.copy)(s, os.path.join(T, c)) if os.path.isdir(s) \
                    else (os.makedirs(T, exist_ok=True), shutil.copy(s, os.path.join(T, c)))
            cap = os.path.join(tmp, night + ".jsonl")
            env = dict(os.environ, YB_CAPTURE=cap, PYTHONPATH=os.pathsep.join([a.psf_os, gpu, ROOT]))
            argv = [sys.executable, os.path.join(tmp, cmd[0])] + [x.replace("{T}", T) for x in cmd[1:]]
            r = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True)
            if r.returncode:
                print(night, "FAILED", r.stderr[-800:])
                continue
            seen = set()
            for ln in open(cap):
                if not ln.strip():
                    continue
                c = json.loads(ln)
                if c["cell"] in seen:          # score4 / score5 call score3 once; keep the first
                    continue
                seen.add(c["cell"])
                for obs in ("M", "W"):
                    z, e = np.array(c["z_" + obs]), np.array(c["e_" + obs])
                    msq = float(np.mean(e ** 2))
                    if msq == 0:
                        continue
                    rr = float(np.dot(z, e) / np.dot(e, e))
                    ratio = float(np.mean((z - e) ** 2)) / msq
                    rows.append(dict(night=night, cell=c["cell"], obs=obs, n=len(e), r=rr, ratio=ratio,
                                     rest=ratio - (1 - rr) ** 2, reads=ratio <= 0.5, line=rr >= LINE))
    above = [x for x in rows if x["line"]]
    below = [x for x in rows if not x["line"]]
    p9 = 160 / 166
    thr = p9 - 2 * math.sqrt(p9 * (1 - p9) / 166)
    for obs in ("M", "W", "both"):
        ab = [x for x in above if obs == "both" or x["obs"] == obs]
        be = [x for x in below if obs == "both" or x["obs"] == obs]
        k = sum(x["reads"] for x in ab)
        print(f"{obs}: r >= 0.293: {k} of {len(ab)} read; r < 0.293: {sum(x['reads'] for x in be)} of {len(be)} read")
    k, n = sum(x["reads"] for x in above), len(above)
    print(f"declared reading: share read above the line {k}/{n} = {k / n:.3f} against {thr:.3f} "
          f"(paper 9's 160/166 = {p9:.3f} minus 2 SE): {'HOLDS' if k / n >= thr else 'DOES NOT HOLD'}")
    for x in rows:
        if x["line"] != x["reads"]:
            print("miss:", x["night"], x["cell"], x["obs"], f"r {x['r']:.3f} ratio {x['ratio']:.3f} rest {x['rest']:+.3f}")
    print(f"r range above the line {min(x['r'] for x in above):.3f} to {max(x['r'] for x in above):.3f}; "
          f"cells {len({(x['night'], x['cell']) for x in rows})}, units {len(rows)}")
    if a.json:
        json.dump(rows, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
