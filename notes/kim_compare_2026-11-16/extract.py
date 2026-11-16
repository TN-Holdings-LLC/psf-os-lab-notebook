"""Read Fig. 3 of Kim et al. (2023) from the vector drawing of the published PDF (page 4): the axis ticks give the
scale, the blue filled circles are the mitigated values, the green circles the unmitigated ones, the grey trace the
exact curve. usage: python extract.py PDF   (writes fig3_points.json and fig3_exact_curve.json next to this file)"""
import json
import math
import os
import sys

import pymupdf as fitz

H = os.path.dirname(os.path.abspath(__file__))
# (x at theta 0, x at pi/2, y at 0, y at 1) per panel, from the tick marks of page 4
AX = {"a": (60.11, 203.85, 206.47, 92.29), "b": (236.71, 380.88, 206.42, 92.28), "c": (408.80, 552.55, 206.47, 92.29)}


def panel(x):
    return "a" if x < 215 else "b" if x < 392 else "c"


def conv(p, x, y):
    x0, x1, y0, y1 = AX[p]
    return (x - x0) / (x1 - x0) * math.pi / 2, (y - y0) / (y1 - y0)


pts, cur = {"mit": {}, "unmit": {}}, {}
for d in fitz.open(sys.argv[1])[3].get_drawings():
    r, f = d["rect"], d["fill"]
    if r.y1 > 215 or r.y0 < 80 or r.x0 < 55 or not f:
        continue
    cx, cy, w = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2, round(r.width, 1)
    p = panel(cx)
    if f == (0.0, 0.0, 1.0) and w == 3.7:
        pts["mit"].setdefault(p, []).append(conv(p, cx, cy))
    elif abs(f[0]) < 1e-6 and abs(f[1] - 0.5) < 0.01 and abs(f[2]) < 1e-6 and w == 4.2:
        pts["unmit"].setdefault(p, []).append(conv(p, cx, cy))
    elif all(abs(c - 0.4) < 0.01 for c in f) and w <= 1.2:
        cur.setdefault(p, []).append(conv(p, cx, cy))
json.dump({k: {p: sorted(v) for p, v in d.items()} for k, d in pts.items()}, open(os.path.join(H, "fig3_points.json"), "w"))
json.dump({p: sorted(v) for p, v in cur.items()}, open(os.path.join(H, "fig3_exact_curve.json"), "w"))
