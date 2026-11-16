"""IBM 2023 (Kim et al., Nature 618, 500) Fig. 3 against its exact curve and against our raw run (exploratory,
2026-11-16; owner: "生データと比べて精度を測る？"). Not declared: the 11-10 / 11-11 declarations say IBM's mitigated
values are not compared numerically; this note is beside the records and changes no verdict.

Input: the markers and the grey exact curve of Fig. 3 read from the vector drawing of the published PDF (page 4) by
extract.py (axis ticks give the scale; the exact curve, sampled every 0.01 rad, agrees with our own exact values at our
17 angles to 1e-4 for weight-10 and 2e-4 for weight-17, so the plot coordinates are reliable to about that).
The weight-17 panel is drawn negated in the paper; values are turned back to the observable's sign here.
usage: python notes/kim_compare_2026-11-16/compare.py   (from the repository root)"""
import json
import os

import numpy as np

H = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(H, "fig3_points.json")))
C = json.load(open(os.path.join(H, "fig3_exact_curve.json")))


def interp(p, th):
    c = np.array(C[p])
    return np.interp(th, c[:, 0], c[:, 1])


def ours(obs):
    rows = [json.loads(line) for line in open(f"results/utility-2026-11-10/answers/{obs}.jsonl") if '"k"' in line]
    return np.array([r["theta"] for r in rows]), np.array([r["re"] for r in rows])


def split(z, e):
    z, e = np.asarray(z), np.asarray(e)
    r = float(np.dot(z, e) / np.dot(e, e))
    ratio = float(np.mean((z - e) ** 2) / np.mean(e ** 2))
    return ratio, r, ratio - (1 - r) ** 2


for p, obs in (("b", "w10_t5"), ("c", "w17_t5")):
    th, ex = ours(obs)
    sign = 1 if abs(ex[-1] - interp(p, th[-1])) < 0.1 else -1
    d = sign * interp(p, th) - ex
    print(f"check {obs}: the figure's exact curve against ours at our 17 angles, max |diff| {np.max(abs(d)):.4f}")

for p, obs, name in (("a", None, "Mz"), ("b", "w10_t5", "weight-10"), ("c", "w17_t5", "weight-17")):
    sign = 1
    if obs:
        th, ex = ours(obs)
        sign = 1 if abs(ex[-1] - interp(p, th[-1])) < 0.1 else -1
    print(f"\n{name}, 5 steps (MSE / mean square, r, rest)")
    out = {}
    for k, lab in (("unmit", "IBM unmitigated (twirled, gain 1), Eagle 2023"), ("mit", "IBM ZNE-mitigated")):
        pts = np.array(P[k][p])
        out[k] = split(sign * pts[:, 1], sign * interp(p, pts[:, 0]))
        print(f"  {lab:46s} n={len(pts):2d}  {out[k][0]:.3f}  {out[k][1]:.3f}  {out[k][2]:.3f}")
    if obs:
        s = json.load(open("results/utility-2026-11-10/ibm_fez/scores.json"))["observables"][obs]["points"]
        o = split([q["z"] for q in s], [q["exact"] for q in s])
        print(f"  {'ours raw (no twirling), Heron fez 2026-11-10':46s} n={len(s):2d}  {o[0]:.3f}  {o[1]:.3f}  {o[2]:.3f}")
    u = out["unmit"]
    print(f"  dividing IBM's unmitigated by its own single r would leave {u[2] / u[1] ** 2:.3f}; ZNE left {out['mit'][0]:.3f}")
    um, mm = np.array(P["unmit"][p]), np.array(P["mit"][p])
    kept, gain = [], []
    for t, mv in mm:
        j = np.argmin(abs(um[:, 0] - t))
        e = interp(p, t)
        if abs(um[j, 0] - t) < 0.005 and abs(e) >= 0.15:
            kept.append(um[j, 1] / e)
            gain.append(mv / um[j, 1])
    kept, gain = np.array(kept), np.array(gain)
    print(f"  points with |exact| >= 0.15: kept share {kept.min():.3f}-{kept.max():.3f}, ZNE gain {gain.min():.2f}-"
          f"{gain.max():.2f}, gain x kept {np.round(gain * kept, 2).tolist()}")
