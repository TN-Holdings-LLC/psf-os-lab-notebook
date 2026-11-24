"""Tables of the ohm ruler dry runs (workplace VS, 2026-11-24, sono1; author The Architect). Reads the tool's
scores.json of every run (named scores_{tag}_s{seed}.json, tag = the noise setting or plan) and prints, per setting and
t, the share of cells reading AGREES for ruler (a) and (b), UNIFORM, the mean raw W excess (device - exact), and the
mean of r_pool - rho_b (the window's pooled shrink against the mirror's square root). No exact value is printed.
ILLUSTRATIVE noise, never fitted.

  python vs_ruler_table.py DIR [DIR ...] [--t 1 3]   (--t: only these t; the noisy pod runs skipped t = 4 for cost)
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
    for f in sorted(sum((glob.glob(os.path.join(d, "scores_*.json")) for d in args), [])):
        m = re.match(r"scores_(.+)_s(\d+)\.json$", os.path.basename(f))
        if not m:
            continue
        tagn = m.group(1)
        sc = json.load(open(f))
        for key, c in sc["cells"].items():
            t = int(re.search(r"_t(\d)_", key).group(1))
            if only is not None and t not in only:
                continue
            g = agg[(tagn, t)]
            g["W_excess"].append(c["W_excess"])
            if c.get("ruler_a") in ("AGREES", "DIFFERS"):
                g["a"].append(c["ruler_a"] == "AGREES")
            if "ruler_b" in c:
                g["b"].append(c["ruler_b"] == "AGREES")
            u = sc.get("uniform", {}).get(key)
            if u and u["word"] in ("UNIFORM", "NOT UNIFORM"):
                g["u"].append(u["word"] == "UNIFORM")
                if "rho_b" in c and np.isfinite(u["r_pool"]):
                    g["r_minus_rb"].append(u["r_pool"] - c["rho_b"])
                if "rho_a" in c:
                    g["r_minus_ra"].append(u["r_pool"] - float(np.mean(c["rho_a"])))
    print("| setting | t | cells | (a) AGREES | (b) AGREES | UNIFORM | W excess (mean) | r_pool - sqrt(mirror) (mean) | "
          "r_pool - rho_a (mean) |")
    print("|---|---|---|---|---|---|---|---|---|")
    fr = lambda v: f"{sum(v)}/{len(v)} ({100 * sum(v) / len(v):.0f} %)" if v else "-"
    mn = lambda v: f"{np.mean(v):+.3f}" if v else "-"
    for (tagn, t), g in sorted(agg.items()):
        print(f"| {tagn} | {t} | {len(g['W_excess'])} | {fr(g['a'])} | {fr(g['b'])} | {fr(g['u'])} | {mn(g['W_excess'])} | "
              f"{mn(g['r_minus_rb'])} | {mn(g['r_minus_ra'])} |")


if __name__ == "__main__":
    main()
