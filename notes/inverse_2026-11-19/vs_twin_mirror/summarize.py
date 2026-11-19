"""Tables for the twin / mirror look (workplace VS, 2026-11-19; author The Architect). ILLUSTRATIVE noise only.

  python summarize.py inf_n8.json shots_n8.json inf_n12.json shots_n12.json > summary.md
Numbers printed to 3 decimals.
"""
import json
import math
import sys

import numpy as np


def tag(r):
    return r["noise"] if r["noise"] != "C" else f"C {r['eps']:g}"


def load(p):
    return json.load(open(p))["rows"]


def main():
    inf8, sh8, inf12, sh12 = (load(p) for p in sys.argv[1:5])
    print("## Infinite shots (density matrix), n = 8 and n = 12 (L = 8)\n")
    print("| n | L (cz) | noise | exact | raw | k_true | k_twin | k_mirror | g | twin err | mirror err |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in inf8 + inf12:
        print(f"| {r['n']} | {r['L']} ({r['cz']}) | {tag(r)} | {r['exact_mid']:+.3f} | {r['raw']:+.3f} | {r['k_true']:.3f} | "
              f"{r['k_twin']:.3f} | {r['k_mirror']:.3f} | {r['g']:+.3f} | {r['twin_err']:+.3f} | {r['mirror_err']:+.3f} |")
    print("\n## g against noise A at infinite shots (the same L): g - g_A, and |g - g_A| of C over that of D\n")
    print("| n | L | g_A | D: g - g_A | C 0.02: g - g_A | C 0.05: g - g_A | C 0.1: g - g_A | C 0.05 / D |")
    print("|---|---|---|---|---|---|---|---|")
    for rows in (inf8, inf12):
        for L in sorted({r["L"] for r in rows}):
            d = {tag(r): r["g"] for r in rows if r["L"] == L}
            a = d["A"]
            ratio = abs(d["C 0.05"] - a) / abs(d["D"] - a)
            print(f"| {rows[0]['n']} | {L} | {a:+.3f} | {d['D'] - a:+.3f} | {d['C 0.02'] - a:+.3f} | {d['C 0.05'] - a:+.3f} | "
                  f"{d['C 0.1'] - a:+.3f} | {ratio:.1f} |")
    print("\n## 40 000 shots per circuit (user, twin, mirror each): g and its 2 SE (mean over repeats; spread = SD of "
          "the repeats)\n")
    print("| n | L | noise | reps | g | 2 SE (one run) | SD of repeats | g / 2 SE | shots per circuit for g - g_A = 2 SE of the difference |"
          " twin err | mirror err |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for rows in (sh8, sh12):
        byL = {}
        for r in rows:
            byL.setdefault(r["L"], {})[tag(r)] = r
        for L in sorted(byL):
            ga = np.mean([x["g"] for x in byL[L]["A"]["reps"]])
            sea = np.mean([x["two_se_g"] for x in byL[L]["A"]["reps"]]) / 2
            for t, r in byL[L].items():
                gs = [x["g"] for x in r["reps"]]
                se = np.mean([x["two_se_g"] for x in r["reps"]]) / 2
                sd = float(np.std(gs, ddof=1)) if len(gs) > 1 else float("nan")
                g = float(np.mean(gs))
                if t == "A":
                    need = "-"
                else:
                    diff = abs(g - ga)
                    need = f"{r['shots'] * (2 * math.hypot(se, sea) / diff) ** 2:.0f}" if diff > 0 else "inf"
                te = np.mean([x["twin_err"] for x in r["reps"]])
                me = np.mean([x["mirror_err"] for x in r["reps"]])
                print(f"| {r['n']} | {L} | {t} | {len(gs)} | {g:+.3f} | {2 * se:.3f} | {sd:.3f} | {abs(g) / (2 * se):.1f} | "
                      f"{need} | {te:+.3f} | {me:+.3f} |")
    print("\n## The twin's exact pattern (from twin.z_exact)\n")
    for rows in (inf8, inf12):
        for r in rows:
            if r["noise"] == "A":
                print(f"- n {r['n']} L {r['L']}: {[int(round(v)) for v in r['twin_exact']]}")


if __name__ == "__main__":
    main()
