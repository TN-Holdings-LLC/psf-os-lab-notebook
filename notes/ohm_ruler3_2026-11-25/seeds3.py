"""Tally of score3 words over dry-run seeds (workplace Claude, 2026-11-25; desk, no device). Reads
<case>_<seed>.scores3.json (gpu/ohm_ruler_night3.py score3 on jobs sampled by dry3.py) and counts, per case and
ruler, AGREES at the t quantile and at 2 SE, NOT READ, and candidate 1's left-out qubits; the direction words; the
one-factor words.

  python notes/ohm_ruler3_2026-11-25/seeds3.py FOLDER > notes/ohm_ruler3_2026-11-25/seeds3.txt
"""
import glob
import json
import os
import sys
from collections import Counter, defaultdict

RULERS = ("a", "b", "c", "d", "d1", "b_tau", "c_tau", "d_tau", "d1_tau")
agree = defaultdict(lambda: [0, 0, 0, 0])      # t AGREES, 2se AGREES, NOT READ, cells
left = defaultdict(Counter)
dirw = defaultdict(Counter)
uni = defaultdict(Counter)
rho = defaultdict(list)
seeds = defaultdict(set)
for p in sorted(glob.glob(os.path.join(sys.argv[1], "*_*.scores3.json"))):
    case, sd = os.path.basename(p).split(".scores3")[0].rsplit("_", 1)
    seeds[case].add(sd)
    r = json.load(open(p))
    for k, c in r["cells"].items():
        tt = "t1" if "_t1_" in k else "t>=3"
        for rr, v in c["rulers"].items():
            a = agree[(case, rr, tt)]
            a[0] += v["words"]["t"] == "AGREES"
            a[1] += v["words"]["2se"] == "AGREES"
            a[2] += v["words"]["t"] == "NOT READ"
            a[3] += 1
            for q in v.get("left_out", []):
                left[(case, rr)][q] += 1
            if v.get("rho") is not None and tt != "t1":
                rho[(case, rr)].append(v["rho"])
    for k, v in r["direction"].items():
        dirw[case][v["word"]] += 1
    for k, u in r["uniform"].items():
        uni[case][u["word"]] += 1
print("| case | seeds | ruler | t | cells | AGREES (t quantile) | AGREES (2 SE) | NOT READ |")
print("|---|---|---|---|---|---|---|---|")
for key in sorted(agree, key=lambda x: (x[0], RULERS.index(x[1]) if x[1] in RULERS else 99, x[2])):
    a = agree[key]
    print(f"| {key[0]} | {len(seeds[key[0]])} | ({key[1]}) | {key[2]} | {a[3]} | {a[0]} ({100 * a[0] / a[3]:.0f} %) | "
          f"{a[1]} ({100 * a[1] / a[3]:.0f} %) | {a[2]} |")
print()
for case in sorted(dirw):
    print(f"{case}: direction {dict(dirw[case])}; one factor {dict(uni[case])}")
print()
for key in sorted(left):
    print(f"{key[0]} ({key[1]}): left out by chain position {dict(sorted(left[key].items()))}")
for key in sorted(rho):
    v = rho[key]
    print(f"{key[0]} ({key[1]}): mean rho at t >= 3 {sum(v) / len(v):.3f} over {len(v)} cells")
