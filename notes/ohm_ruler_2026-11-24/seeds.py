"""How often the declared words fire on dry runs, over seeds (workplace Claude, 2026-11-24; desk, no device).

Reads the scores.json of dry runs named seed_<flip>_<seed>.scores.json in a folder (gpu/ohm_ruler_night.py score on
jobs sampled by dry.py) and counts, per noise: ruler (a) DIFFERS, ruler (b) DIFFERS and NOT UNIFORM, over the cells
where each is read.

  python notes/ohm_ruler_2026-11-24/seeds.py FOLDER > notes/ohm_ruler_2026-11-24/seeds.txt
"""
import glob
import json
import os
import sys
from collections import defaultdict

c = defaultdict(lambda: defaultdict(lambda: [0, 0]))
seeds = defaultdict(set)
for p in sorted(glob.glob(os.path.join(sys.argv[1], "seed_*_*.scores.json"))):
    _, flip, sd = os.path.basename(p).split(".scores")[0].split("_")
    seeds[flip].add(sd)
    r = json.load(open(p))
    for k, cell in r["cells"].items():
        for w in ("ruler_a", "ruler_b"):
            if cell.get(w) in ("AGREES", "DIFFERS"):
                c[flip][w][0] += cell[w] == "DIFFERS"
                c[flip][w][1] += 1
        c[flip]["raw W"][0] += cell["W"] != "READS"
        c[flip]["raw W"][1] += 1
    for k, u in r["uniform"].items():
        if u["word"] != "NOT READ":
            c[flip]["one factor"][0] += u["word"] == "NOT UNIFORM"
            c[flip]["one factor"][1] += 1
print("| bit flips q | seeds | ruler (a) DIFFERS | ruler (b) DIFFERS | NOT UNIFORM | raw W DOES NOT READ |")
print("|---|---|---|---|---|---|")
for flip in sorted(c, key=float):
    f = lambda w: f"{c[flip][w][0]} of {c[flip][w][1]} ({100 * c[flip][w][0] / max(1, c[flip][w][1]):.0f} %)"
    print(f"| {flip} | {len(seeds[flip])} | {f('ruler_a')} | {f('ruler_b')} | {f('one factor')} | {f('raw W')} |")
