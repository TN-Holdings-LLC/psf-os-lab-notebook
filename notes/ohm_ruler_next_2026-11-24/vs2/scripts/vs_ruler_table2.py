"""Tables of the ohm ruler dry runs with ruler (c) (workplace VS, 2026-11-24, sono2; author The Architect). Reads, per
run, the declared tool's scores_{tag}_s{seed}.json and the candidate tool's scores2_{tag}_s{seed}.json (gpu/
ohm_ruler_night2.py score2) and prints, per setting and t: the share of cells reading AGREES for rulers (a), (b), (c)
at 2 SE and at the t quantile, the mean of r_pool - rho_c (the window's pooled shrink against the square root of the
mirror on the window), r_pool - rho_b (against the whole mirror) and r_pool - rho_a (against the circuit's own total),
and the share of UNIFORM. No exact value is printed. ILLUSTRATIVE noise, never fitted.

  python vs_ruler_table2.py DIR [DIR ...] [--t 1 3]
"""
import collections
import glob
import json
import os
import re
import sys

import numpy as np


def main():
    args = sys.argv[1:]
    only = None
    if "--t" in args:
        i = args.index("--t")
        only, args = {int(x) for x in args[i + 1:]}, args[:i]
    agg = collections.defaultdict(lambda: collections.defaultdict(list))
    seeds = collections.defaultdict(set)
    for f2 in sorted(sum((glob.glob(os.path.join(d, "scores2_*.json")) for d in args), [])):
        m = re.match(r"scores2_(.+)_s(\d+)\.json$", os.path.basename(f2))
        if not m:
            continue
        tag = m.group(1)
        f1 = os.path.join(os.path.dirname(f2), os.path.basename(f2).replace("scores2_", "scores_", 1))
        s1, s2 = json.load(open(f1)), json.load(open(f2))
        seeds[tag].add(m.group(2))
        for key, c2 in s2["cells"].items():
            t = int(re.search(r"_t(\d)_", key).group(1))
            if only is not None and t not in only:
                continue
            g = agg[(tag, t)]
            g["n"].append(1)
            for r in "abc":
                if r in c2:
                    for w in ("2se", "t"):
                        g[f"{r}_{w}"].append(c2[r]["words"][w] == "AGREES")
            u = s1.get("uniform", {}).get(key)
            if u and u["word"] in ("UNIFORM", "NOT UNIFORM"):
                g["u"].append(u["word"] == "UNIFORM")
                if np.isfinite(u["r_pool"]):
                    if "c" in c2:
                        g["r_c"].append(u["r_pool"] - c2["c"]["rho"])
                    if "b" in c2:
                        g["r_b"].append(u["r_pool"] - c2["b"]["rho"])
                    if "rho_a" in s1["cells"][key]:
                        g["r_a"].append(u["r_pool"] - float(np.mean(s1["cells"][key]["rho_a"])))
    fr = lambda v: f"{sum(v)}/{len(v)} ({100 * sum(v) / len(v):.0f} %)" if v else "-"
    mn = lambda v: f"{np.mean(v):+.3f}" if v else "-"
    print("| setting | t | seeds | cells | (a) 2 SE | (a) t | (b) 2 SE | (b) t | (c) 2 SE | (c) t | UNIFORM | "
          "r - sqrt(window mirror) | r - sqrt(mirror) | r - rho_a |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for (tag, t), g in sorted(agg.items()):
        print(f"| {tag} | {t} | {len(seeds[tag])} | {len(g['n'])} | " + " | ".join(
            fr(g[f"{r}_{w}"]) for r in "abc" for w in ("2se", "t"))
            + f" | {fr(g['u'])} | {mn(g['r_c'])} | {mn(g['r_b'])} | {mn(g['r_a'])} |")


if __name__ == "__main__":
    main()
