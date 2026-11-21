"""Copies per form for a smallest difference worth taking (home VS, 2026-11-21 night; desk). A difference d between
two forms, each pooled over c copies at S shots, is seen at 2 SE with about 80 % power when c >= 2 z^2 p(1-p) / (S d^2),
z = 2 + 0.84; p(1-p) = 0.21 (P about 0.7, the RUS items' range 0.5-0.85; 0.25 at worst). The table gives c per item and
form, and the circuits (3 forms) and model seconds per item at that shot count.

  python notes/rus_fence_2026-11-21/alloc.py OUT.txt
"""
import math
import sys

Z = 2 + 0.84


def copies(d, shots, pq=0.21):
    return max(1, math.ceil(2 * Z * Z * pq / (shots * d * d)))


def seconds(n, shots):
    return n * 0.036 + n * shots * 0.00027


lines = ["smallest difference d | shots | copies per form (p(1-p) 0.21; 0.25) | circuits per item (3 forms) | "
         "model seconds per item (no job overhead)"]
for d in (0.01, 0.02, 0.03, 0.05):
    for s in (1950, 4000):
        c, cw = copies(d, s), copies(d, s, 0.25)
        lines.append(f"{d:.2f} | {s} | {c} ({cw}) | {3 * c} | {seconds(3 * c, s):.1f}")
lines.append("")
lines.append("Desk expectations per item (expect.txt; ILLUSTRATIVE noise): the parking difference M - F under damping is "
             "+0.32 (NF m3 L3), +0.21 (NF m2 L3), +0.10 (P0 L3, P3 L3), +0.05 (P0 L2), 0 (P2 m3 L3); the fence "
             "difference F - D is 0.004-0.07 in size, with signs that depend on the noise. Copies follow: NF 2-3 (its "
             "parking difference is the largest), P0 and P2 5-7 (the fence difference near 0.02-0.04 is the one to "
             "see), P3 2-3 (beside).")
print("\n".join(lines))
open(sys.argv[1], "w").write("\n".join(lines) + "\n")
