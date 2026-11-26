"""Tables of the fourth Ohm ruler dry runs (workplace VS, 2026-11-26; author The Architect). Reads, per run, score4's
scores4.json and scores3.json (named scores4_{tag}_q{q}_s{seed}.json and scores3_{tag}_q{q}_s{seed}.json) and prints,
per setting and t: the share of AGREES (t quantile / 2 SE, %) of rulers (a), (b), (c), (d) from scores3 and (e), (de),
(a') from scores4; the share of cells where (de)'s |d| is below (d)'s ("(de) against (d)": SMALLER); the direction
words with rho_a' (judged) and with rho_a (beside); and the means of d for (d), (de), (e). No exact value is printed.
ILLUSTRATIVE noise, never fitted.

  python vs_ruler_table4.py DIR [DIR ...] [--t 1 3]
"""
import collections
import glob
import json
import os
import re
import sys

import numpy as np

NAME = re.compile(r"scores4_(.+)_q([0-9.]+)_s(\d+)\.json$")


def main():
    args = sys.argv[1:]
    only = None
    if "--t" in args:
        i = args.index("--t")
        only, args = {int(x) for x in args[i + 1:]}, args[:i]
    agg = collections.defaultdict(lambda: collections.defaultdict(list))
    seeds = collections.defaultdict(set)
    for f4 in sorted(sum((glob.glob(os.path.join(d, "scores4_*.json")) for d in args), [])):
        m = NAME.match(os.path.basename(f4))
        if not m:
            continue
        tag = m.group(1)
        f3 = os.path.join(os.path.dirname(f4), os.path.basename(f4).replace("scores4_", "scores3_", 1))
        s4, s3 = json.load(open(f4)), json.load(open(f3))
        seeds[tag].add(m.group(3))
        for key, c4 in s4["cells"].items():
            t = int(re.search(r"_t(\d)_", key).group(1))
            if only is not None and t not in only:
                continue
            g = agg[(tag, t)]
            g["n"].append(1)
            r3 = s3["cells"][key]["rulers"]
            for r in ("a", "b", "c", "d"):
                if r in r3:
                    g[r + "_t"].append(r3[r]["words"]["t"] == "AGREES")
                    g[r + "_2"].append(r3[r]["words"]["2se"] == "AGREES")
            for r in ("e", "de", "a_prime"):
                if r in c4:
                    g[r + "_t"].append(c4[r]["words"]["t"] == "AGREES")
                    g[r + "_2"].append(c4[r]["words"]["2se"] == "AGREES")
            for r, src in (("d", r3.get("d", {})), ("de", c4.get("de", {})), ("e", c4.get("e", {}))):
                if src.get("d") is not None:
                    g["dmean_" + r].append(src["d"])
            if "de_vs_d" in c4:
                g["smaller"].append(c4["de_vs_d"] == "SMALLER")
            dr = s4.get("direction", {}).get(key)
            if dr:
                g["dir_ap"].append((dr.get("judged_a_prime") or {}).get("word", "NOT READ"))
                g["dir_a"].append(dr["beside_a"]["word"])
    pct = lambda v: f"{100 * sum(v) / len(v):.0f}" if v else "-"
    mn = lambda v: f"{np.mean(v):+.3f}" if v else "-"
    words = lambda v: ", ".join(f"{w} {100 * n / len(v):.0f}" for w, n in sorted(collections.Counter(v).items())) if v else "-"
    print("| setting | t | seeds | cells | (a) | (b) | (c) | (d) | (e) | (de) | (a') | (de) smaller than (d) | "
          "direction with rho_a' | direction with rho_a | d of (d) | d of (de) | d of (e) |")
    print("|" + "---|" * 17)
    for (tag, t), g in sorted(agg.items()):
        print(f"| {tag} | {t} | {len(seeds[tag])} | {len(g['n'])} | " +
              " | ".join(f"{pct(g[r + '_t'])} / {pct(g[r + '_2'])}" for r in ("a", "b", "c", "d", "e", "de", "a_prime"))
              + f" | {pct(g['smaller'])} | {words(g['dir_ap'])} | {words(g['dir_a'])} | {mn(g['dmean_d'])} | "
                f"{mn(g['dmean_de'])} | {mn(g['dmean_e'])} |")


if __name__ == "__main__":
    main()
