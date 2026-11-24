"""How often rulers (a), (b) and (c) read DIFFERS at 2 SE and at the t quantile, on dry runs scored by
gpu/ohm_ruler_night2.py score2 (workplace Claude, 2026-11-24; desk, no device). Reads seed_<flip>_<seed>.scores2.json.

  python notes/ohm_ruler_next_2026-11-24/seeds_c.py FOLDER > notes/ohm_ruler_next_2026-11-24/seeds_c.txt
"""
import glob
import json
import os
import sys
from collections import defaultdict

c = defaultdict(lambda: [0, 0, 0])
gap = defaultdict(list)
seeds = defaultdict(set)
for p in sorted(glob.glob(os.path.join(sys.argv[1], "seed_*_*.scores2.json"))):
    _, flip, sd = os.path.basename(p).split(".scores2")[0].split("_")
    seeds[flip].add(sd)
    for k, cell in json.load(open(p))["cells"].items():
        tt = "t1" if "_t1_" in k else "t>=3"
        for r, v in cell.items():
            key = (flip, r, tt)
            c[key][0] += v["words"]["2se"] == "DIFFERS"
            c[key][1] += v["words"]["t"] == "DIFFERS"
            c[key][2] += 1
        if "b" in cell and "c" in cell:
            gap[(flip, tt)].append(cell["c"]["rho"] - cell["b"]["rho"])
print("| bit flips q | seeds | ruler | t | cells | DIFFERS at 2 SE | DIFFERS at the t quantile |")
print("|---|---|---|---|---|---|---|")
for key in sorted(c, key=lambda x: (float(x[0]), x[1], x[2])):
    n2, nt, n = c[key]
    print(f"| {key[0]} | {len(seeds[key[0]])} | ({key[1]}) | {key[2]} | {n} | {n2} ({100 * n2 / n:.0f} %) | "
          f"{nt} ({100 * nt / n:.0f} %) |")
print()
for key in sorted(gap, key=lambda x: (float(x[0]), x[1])):
    g = gap[key]
    print(f"q {key[0]}, {key[1]}: sqrt(window mirror) - sqrt(mirror), mean {sum(g) / len(g):+.4f} over {len(g)} cells")
