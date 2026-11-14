"""A post-hoc rescaling, computed beside the verdicts and never used for them (desk, 2026-11-14, for paper 9).

If the device's error were a pure shrink, dividing the raw values by the kept share would restore them. Three versions:
  oracle   z / r, with r from the exact answer itself (not available to a user; the best any single scale can do):
           its MSE / mean square is rest / r^2, the shape error blown up by 1/r^2;
  ruler    pi/4 values divided by r of the pi/2 circuit of the same chain, depth and job (XX size test and repeat):
           a scale a user could have, from a Clifford circuit with the same gates;
  twin     the user circuit divided by r of its Clifford twin in the same job (twin test, 11-13).
Reported: how many results would read after each, and what is left (rest / r^2).
usage: python notes/paper9_posthoc/rescale.py   (from the repository root)"""
import glob
import json

import numpy as np

rows = json.load(open("notes/paper9_yardstick/line_all.json"))
before = sum(r["reads"] for r in rows)
after = [r for r in rows if r["r"] > 0 and r["rest"] / r["r"] ** 2 <= 0.5]
print(f"oracle z / r over the yardstick's {len(rows)} results: reads before {before}, after {len(after)}")
gain = [r for r in rows if not r["reads"] and r["rest"] / r["r"] ** 2 <= 0.5]
lost = [r for r in rows if r["reads"] and r["rest"] / r["r"] ** 2 > 0.5]
print(f"  gained {len(gain)} (r {min(r['r'] for r in gain):.3f} to {max(r['r'] for r in gain):.3f}), lost {len(lost)}:",
      [(r["record"], r["item"]) for r in lost])
a = np.array([r["ratio"] for r in rows]); b = np.array([r["rest"] / r["r"] ** 2 for r in rows])
print(f"  median MSE / mean square {np.median(a):.3f} -> {np.median(b):.3f}; larger after in {int((b > a).sum())}")
still = [r for r in rows if r["r"] > 0 and r["rest"] / r["r"] ** 2 > 0.5]
print("  still not reading after the oracle scale:", [(r["family"], r["record"].split("/")[0], r["item"].split(":")[-1],
      round(r["r"], 3), round(r["rest"] / r["r"] ** 2, 3)) for r in still])
neg = [r for r in rows if r["r"] <= 0]
print("  r <= 0 (no scale helps):", len(neg))

print("\nruler: pi/4 circuits divided by r of the pi/2 circuit of the same chain, depth and job")
tot = ok_b = ok_a = 0
lines = []
for base in sorted(glob.glob("results/xxsize-2026-11-14-*")) + ["results/xxcone-2026-11-14"]:
    for f in sorted(glob.glob(f"{base}/*/scores.json")):
        c = json.load(open(f))["circuits"]
        for t, v in c.items():
            if "_th0785_" not in t:
                continue
            ru = c[t.replace("_th0785_", "_th1571_")]
            z, e = np.array(v["z"]), np.array(v["exact"])
            zr, er = np.array(ru["z"]), np.array(ru["exact"])
            s = float(np.dot(zr, er) / np.dot(er, er))
            mse_a = float(np.mean((z / s - e) ** 2)); msq = float(np.mean(e ** 2))
            tot += 1; ok_b += v["reads"] == "READS"; ok_a += mse_a <= msq / 2
            lines.append(f"  {f.split('/')[1]:28s} {t:16s} r {v['amplitude_ratio']:.3f} ruler {s:.3f} | MSE/msq {v['mse'] / v['mean_square']:.3f} -> {mse_a / msq:.3f}")
print(f"  {tot} circuits: read before {ok_b}, after {ok_a}")
print("\n".join(lines))

print("\ntwin: the user circuit divided by r of its Clifford twin in the same job (11-13)")
for f in glob.glob("results/twin-2026-11-13/*/twin_scores.json"):
    for t, p in json.load(open(f))["pairs"].items():
        u, w = p["user"], p["twin"]
        # user MSE after dividing by s = r_twin: mean((z/s - e)^2) = (rest*msq + (r - s)^2 msq ... ) / s^2 computed exactly:
        r_, s, msq = u["r"], w["r"], u["mean_square"]
        rest = u["mse"] / msq - (1 - r_) ** 2
        ratio_after = (rest + (r_ - s) ** 2) / s ** 2
        print(f"  {t:16s} r {r_:.3f} r_twin {s:.3f} | MSE/msq {u['mse'] / msq:.3f} -> {ratio_after:.3f} "
              f"{'reads' if ratio_after <= 0.5 else 'does not read'} (before: {u['reads']})")
