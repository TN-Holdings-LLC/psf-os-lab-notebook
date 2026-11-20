"""The loopvar tool's noiseless dry run with 20 seeds (workplace VS, 2026-11-20; author The Architect). No device.

Reads loopvar_scores.json of each seed. Under shot noise alone: z = d / SE of the within and between pairs should be
about N(0, 1) (between pairs are correlated), and the three-job p about uniform; counts of MOVES / DRIFTS against what
2 SE and the level 0.05 give.

  python lvseeds20.py SEEDS_DIR
"""
import glob
import json
import os
import sys

import numpy as np


def main():
    files = sorted(glob.glob(os.path.join(sys.argv[1], "s*", "loopvar_scores.json")))
    zw, zb, ps, pooled, sb = [], [], [], [], []
    for f in files:
        r = json.load(open(f))
        for L, row in r["rows"].items():
            zw += [w["d"] / (w["two_se"] / 2) for w in row["within"].values()]
            zb += [b["d"] / (b["two_se"] / 2) for b in row["between"].values()]
            ps.append(row["p"])
            sb.append(row["excess_var"])
        pooled.append(r["pooled"]["p"])
    zw, zb, ps = np.array(zw), np.array(zb), np.array(ps)
    print(f"seeds {len(files)}")
    print(f"within (a - b) / SE: n {len(zw)}, mean {zw.mean():+.3f}, SD {zw.std(ddof=1):.3f}, MOVES {int((abs(zw) >= 2).sum())} "
          f"(expected {0.0455 * len(zw):.1f})")
    print(f"between / SE:        n {len(zb)}, mean {zb.mean():+.3f}, SD {zb.std(ddof=1):.3f}, MOVES {int((abs(zb) >= 2).sum())} "
          f"(expected {0.0455 * len(zb):.1f}; pairs correlated)")
    print(f"three-job p per L:   n {len(ps)}, mean {ps.mean():.3f} (uniform 0.5), below 0.05: {int((ps < 0.05).sum())} "
          f"(expected {0.05 * len(ps):.1f}); deciles {np.histogram(ps, bins=5, range=(0, 1))[0].tolist()}")
    print(f"pooled p (6 df):     mean {np.mean(pooled):.3f}, below 0.05: {int((np.array(pooled) < 0.05).sum())}")
    print(f"excess variance:     mean {np.mean(sb):+.2e} (0 under shot noise alone), share negative {np.mean(np.array(sb) < 0):.2f}")
    lv1 = sum(1 for f in files if all(abs(w["d"]) < w["two_se"] for row in json.load(open(f))["rows"].values()
                                      for w in row["within"].values()))
    print(f"seeds where every within pair is SAME (LV-1 as written holds): {lv1} of {len(files)} (expected about 66 %)")


if __name__ == "__main__":
    main()
