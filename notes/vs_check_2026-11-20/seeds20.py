"""The decoy tool's noiseless dry run with 20 seeds (workplace VS, 2026-11-20; author The Architect). No device.

Reads the score.txt of each seed; per conditional sub-item: d, its 2 SE, the word. Compares the rate of LESS / MORE
with the 4.6 % the 2 SE threshold gives a normal statistic, and with a Monte Carlo of the folded statistic
d = |s - v| - |p - v| when s and p are both centred on v (the noiseless case), where d is not normal and its spread
is below the SE the score uses.

  python seeds20.py SEEDS_DIR
"""
import glob
import math
import os
import re
import sys

import numpy as np

R = re.compile(r"^\s+(d\d[ab]) against (s[ab]): alone ([0-9.]+)\s+packed ([0-9.]+)\s+d ([+-][0-9.]+) \(2 SE ([0-9.]+)\) -> (.+)$")
V = re.compile(r"noiseless ff of rd2 \(exact, read flipped\): ([0-9.]+)")


def main():
    rows, v = [], None
    files = sorted(glob.glob(os.path.join(sys.argv[1], "s*.score.txt")), key=lambda p: int(re.findall(r"s(\d+)\.", p)[0]))
    for f in files:
        for line in open(f):
            m = V.search(line)
            if m:
                v = float(m.group(1))
            m = R.match(line)
            if m:
                rows.append(dict(seed=os.path.basename(f).split(".")[0], sub=m.group(1), s=float(m.group(3)),
                                 p=float(m.group(4)), d=float(m.group(5)), two_se=float(m.group(6)), word=m.group(7)))
    n = len(rows)
    words = {}
    for r in rows:
        words[r["word"]] = words.get(r["word"], 0) + 1
    z = np.array([r["d"] / (r["two_se"] / 2) for r in rows])
    zl = np.array([(r["p"] - r["s"]) / (r["two_se"] / 2) for r in rows])
    print(f"seeds {len(files)}, conditional sub-items {n}; words: {words}")
    print(f"d / SE:            mean {z.mean():+.3f}, SD {z.std(ddof=1):.3f}, |d| >= 2 SE: {int((abs(z) >= 2).sum())}")
    print(f"(p - s) / SE:      mean {zl.mean():+.3f}, SD {zl.std(ddof=1):.3f}, |.| >= 2 SE: {int((abs(zl) >= 2).sum())}")
    # Monte Carlo of the folded statistic at the noiseless point, with this test's shots
    rng = np.random.default_rng(20261120)
    N, shots = 2_000_000, 4000
    sig = math.sqrt(v * (1 - v) / shots)
    s = rng.normal(v, sig, N)
    p = rng.normal(v, sig, N)
    d = np.abs(s - v) - np.abs(p - v)
    se = math.sqrt(2) * sig
    rate = float((np.abs(d) >= 2 * se).mean())
    print(f"Monte Carlo, s and p ~ N(v, v(1-v)/4000), v = {v}: SD(d)/SE {d.std() / se:.3f} "
          f"(theory sqrt(1 - 2/pi) = {math.sqrt(1 - 2 / math.pi):.3f}); P(|d| >= 2 SE) = {rate:.5f} "
          f"(a normal statistic: {math.erfc(2 / math.sqrt(2)):.4f})")
    expect = rate * n
    print(f"expected LESS or MORE in {n} sub-items: {expect:.2f} (folded) against {n * 0.0455:.1f} (normal)")
    # away from v (a device night: s 0.06 below v), the fold vanishes and d ~ p - s
    s2 = rng.normal(v - 0.06, sig, N)
    p2 = rng.normal(v - 0.06, sig, N)
    d2 = np.abs(s2 - v) - np.abs(p2 - v)
    print(f"same, s and p centred 0.06 below v: SD(d)/SE {d2.std() / se:.3f}; P(|d| >= 2 SE) "
          f"{float((np.abs(d2) >= 2 * se).mean()):.4f}")
    for t in (0.0, 0.005, 0.01, 0.02):
        s3 = rng.normal(v - t, sig, N)
        p3 = rng.normal(v - t, sig, N)
        d3 = np.abs(s3 - v) - np.abs(p3 - v)
        print(f"  centred {t:.3f} below v: P(|d| >= 2 SE) {float((np.abs(d3) >= 2 * se).mean()):.4f}")


if __name__ == "__main__":
    main()
