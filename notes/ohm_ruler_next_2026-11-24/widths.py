"""How often the rulers' words fire at two widths, 2 SE (declared) and Student's t (K - 1 degrees of freedom), on the
dry runs' declared scores (workplace Claude, 2026-11-24; desk, no device). Reads seed_<flip>_<seed>.scores.json
(gpu/ohm_ruler_night.py score on jobs sampled by notes/ohm_ruler_2026-11-24/dry.py); SE = (2 SE) / 2 as written there.

  python notes/ohm_ruler_next_2026-11-24/widths.py FOLDER K > notes/ohm_ruler_next_2026-11-24/widths.txt
"""
import glob
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "gpu"))
from ohm_ruler_night2 import t975  # noqa: E402

folder, K = sys.argv[1], int(sys.argv[2])
tq = t975(K - 1)
c = defaultdict(lambda: [0, 0, 0])        # DIFFERS at 2 SE, DIFFERS at t, cells
seeds = defaultdict(set)
for p in sorted(glob.glob(os.path.join(folder, "seed_*_*.scores.json"))):
    _, flip, sd = os.path.basename(p).split(".scores")[0].split("_")
    seeds[flip].add(sd)
    for k, cell in json.load(open(p))["cells"].items():
        for r in ("a", "b"):
            if f"d_{r}" not in cell:
                continue
            d, se = cell[f"d_{r}"], cell[f"d_{r}_2se"] / 2
            key = (flip, r, "t1" if "_t1_" in k else "t>=3")
            c[key][0] += abs(d) >= 2 * se
            c[key][1] += abs(d) >= tq * se
            c[key][2] += 1
NOMINAL_2SE = {6: 9.2, 7: 8.6, 8: 8.1, 9: 7.7, 10: 7.3}  # 100 x P(|t_dof| >= 2), two-sided
print(f"K = {K}; 2 SE against t quantile {tq:.3f}; nominal false rate: {NOMINAL_2SE.get(K - 1, float('nan'))} % at 2 SE "
      f"({K - 1} dof), 5 % at the t quantile")
print()
print("| bit flips q | seeds | ruler | t | cells | DIFFERS at 2 SE | DIFFERS at the t quantile |")
print("|---|---|---|---|---|---|---|")
for key in sorted(c, key=lambda x: (float(x[0]), x[1], x[2])):
    n2, nt, n = c[key]
    print(f"| {key[0]} | {len(seeds[key[0]])} | ({key[1]}) | {key[2]} | {n} | {n2} ({100 * n2 / n:.0f} %) | "
          f"{nt} ({100 * nt / n:.0f} %) |")
