"""Independent recount of results/ipe-branch-cost-night-2026-11-22 (home VS): qiskit and numpy only, no psf-os and no
notebook scoring code. Success bits from the phase itself (clbit m holds bit m + 1 of j / 2^n), counts from
raw_counts.json, circuits from circuits.qpy. Also, beside (the owner's two asks): the R twin, and the per-round
first-error hazard of F against S (does the n = 8 round-6 peak near pi stay without the branch?)."""
import json
import math
import re
import sys
from collections import defaultdict

from qiskit import qpy

R = sys.argv[1]
J = R + "/bc/job0/job"
man = json.load(open(J + "/manifest.json"))
raw = json.load(open(J + "/raw_counts.json"))
cs = qpy.load(open(J + "/circuits.qpy", "rb"))
cells = {c["cell"]: c for c in man["cells"]}
cnt = {r["pub"]: r["counts"] for r in raw["rows"]}
DT = float(open(R + "/dt.txt").read().strip())
L = 4500


def a_of(n):
    a = int(round(2 ** n * (math.sqrt(5) - 1) / 2))
    return a + (a % 2 == 0)


def bits(n, j):
    return {m: (j >> (n - 1 - m)) & 1 for m in range(n)}


def bit(k, m):
    return int(k.replace(" ", "")[-1 - m])


items = {}
for i, p in enumerate(man["pubs"]):
    c = cells[p["cell"]]
    mm = re.match(r"^ff_ip([a-z])(\d)_(\d+)$", c["name"])
    if c["role"] == "user" and mm:
        items[(mm.group(1), int(mm.group(2)), int(mm.group(3)))] = i
print(f"circuits {len(cs)}, pubs {len(man['pubs'])}, user items {len(items)}, shots {man['shots']}, "
      f"forms {sorted({f for f, _, _ in items})}, R twins {sum(1 for f, _, _ in items if f == 'r')}")
for n in (6, 8):
    want = sorted((k * a_of(n)) % 2 ** n for k in range(1, 9))
    for f in "fsde":
        got = sorted(j for ff, nn, j in items if ff == f and nn == n)
        assert got == want, (f, n, got, want)
    print(f"n {n}: phases as declared (k a mod 2^n, a = {a_of(n)}): {[(k * a_of(n)) % 2 ** n for k in range(1, 9)]}")

# 1. P per form and n, differences, words, row
P = {}
for f in "fsde":
    for n in (6, 8):
        ok = tot = 0
        for (ff, nn, j), i in items.items():
            if ff == f and nn == n:
                b = bits(n, j)
                for k, v in cnt[i].items():
                    tot += v
                    ok += v if all(bit(k, m) == x for m, x in b.items()) else 0
        p = ok / tot
        P[(f, n)] = (p, math.sqrt(p * (1 - p) / tot), tot)
for n in (6, 8):
    print(f"n {n}: " + ", ".join(f"{f} {P[(f, n)][0]:.4f} (2 SE {2 * P[(f, n)][1]:.4f}, {P[(f, n)][2]})" for f in "fsde"))


def diff(a, b):
    v = [(P[(a, n)][0] - P[(b, n)][0], math.hypot(P[(a, n)][1], P[(b, n)][1])) for n in (6, 8)]
    return v, sum(x for x, _ in v) / 2, math.sqrt(sum(s ** 2 for _, s in v)) / 2


def word(d, se, w):
    return f"{w} COSTS" if d > 0 and d >= 2 * se else f"{w} GAINS" if d < 0 and d <= -2 * se else f"NO {w} COST SEEN"


for name, a, b, w in (("SD - F", "d", "f", "FEEDBACK"), ("S - SD", "s", "d", "WAIT"), ("SD(L) - SD(2L)", "d", "e", None),
                      ("S - F (beside)", "s", "f", None)):
    v, m, se = diff(a, b)
    print(f"{name}: per n " + ", ".join(f"{x:+.4f} ({2 * s:.4f})" for x, s in v) + f"; mean {m:+.4f} (2 SE {2 * se:.4f})"
          + (f" -> {word(m, se, w)}" if w else ""))

# 2. what was sent: conditionals, delays per SD circuit
inv = {i: key for key, i in items.items()}
cond, dly = defaultdict(set), defaultdict(set)
for i, c in enumerate(cs):
    if i not in inv:
        continue
    f, n, j = inv[i]
    nc = sum(1 for x in c.data if x.operation.name == "if_else")
    d = defaultdict(int)
    per_round = []
    for x in c.data:
        if x.operation.name == "delay":
            assert x.operation.unit == "dt"
            d[c.find_bit(x.qubits[0]).index] += x.operation.duration
            per_round.append(x.operation.duration)
    cond[(f, n)].add(nc)
    if d:
        rounds = sorted(set(per_round))
        dly[(f, n)].add((len(d), tuple(sorted(set(d.values()))), tuple(rounds)))
    else:
        dly[(f, n)].add(None)
for key in sorted(cond):
    print(f"{key}: conditionals {sorted(cond[key])}; delays (qubits, total dt per qubit, per-round values) "
          f"{sorted(dly[key], key=str)}")
for n in (6, 8):
    for f, x in (("d", 1), ("e", 2)):
        tot_dt = L * x * sum(range(n))
        print(f"n {n} {'SD' if x == 1 else 'SD(2L)'}: expected {tot_dt} dt per qubit = {tot_dt * DT * 1e6:.0f} us")
print("psf_os_build", man["psf_os_build"])
q = json.load(open(R + "/fetch_in/queue.json"))
order = [d for d in q["chosen"] if d != "ibm_marrakesh" and d in q["pending"]]
print("device rule:", min(order, key=lambda d: (q["pending"][d], order.index(d))), "| recorded", man["fetch"]["backend"])

# 4. charge: delay seconds summed over circuits x shots
S = man["shots"]
delay_s = 0.0
for i, c in enumerate(cs):
    d = defaultdict(int)
    for x in c.data:
        if x.operation.name == "delay":
            d[c.find_bit(x.qubits[0]).index] += x.operation.duration
    delay_s += (max(d.values()) if d else 0) * DT * S
N = len(cs)
model = N * 0.036 + N * S * 0.00027 + 3.0
rel = 2.6 + 0.000269 * N * S
print(f"delay x shots summed: {delay_s:.1f} s; model {model:.1f} s -> + delays {model + delay_s:.1f}; "
      f"105-job relation {rel:.1f} s -> + delays {rel + delay_s:.1f}; charged 112 s")

# beside: R twin
print("R twin in the job:", any(f == "r" for f, _, _ in items))

# beside: per-round first-error hazard, F against S (and SD), odd phases pooled, and per (phase, round) at f = angle
for n in (6, 8):
    for f in "fsd":
        first, alive = [0] * n, [0] * n
        for (ff, nn, j), i in items.items():
            if ff != f or nn != n or j % 2 == 0:
                continue
            b = bits(n, j)
            for k, v in cnt[i].items():
                for r, m in enumerate(range(n - 1, -1, -1)):
                    alive[r] += v
                    if bit(k, m) != b[m]:
                        first[r] += v
                        break
        h = [first[r] / alive[r] for r in range(n)]
        se = [2 * math.sqrt(x * (1 - x) / a) for x, a in zip(h, alive)]
        print(f"hazard n {n} {f} (odd phases): " + " ".join(f"{x:.3f}" for x in h) + " | 2 SE " + " ".join(f"{x:.3f}" for x in se))
rows = []
for (f, n, j), i in items.items():
    if f not in "fs":
        continue
    b = bits(n, j)
    alive = cnt[i]
    for r, m in enumerate(range(n - 1, -1, -1)):
        tot = sum(alive.values())
        wrong = {k: v for k, v in alive.items() if bit(k, m) != b[m]}
        fr = ((j * 2 ** m) % 2 ** n) / 2 ** n
        rows.append((f, n, j, r + 1, fr, sum(wrong.values()) / tot if tot else 0, tot))
        alive = {k: v for k, v in alive.items() if k not in wrong}
by = {(f, n, j, r): (fr, h, t) for f, n, j, r, fr, h, t in rows}
print("rounds at f = 0.4844 (and the highest F hazards), F against S:")
top = sorted([x for x in rows if x[0] == "f" and x[3] > 1], key=lambda x: -x[5])[:8]
for f, n, j, r, fr, h, t in top:
    hs, ts = by[("s", n, j, r)][1:]
    se = 2 * math.sqrt(h * (1 - h) / t + hs * (1 - hs) / ts)
    print(f"  n {n} j {j} round {r} f {fr:.4f}: F {h:.3f} ({t}), S {hs:.3f} ({ts}); S - F {hs - h:+.3f} (2 SE {se:.3f})")
for f in "fs":
    for lo, hi in ((0.0, 0.02), (0.02, 0.05), (0.05, 0.15), (0.15, 0.5)):
        s = [x for x in rows if x[0] == f and x[3] > 1 and x[4] != 0 and lo <= abs(x[4] - 0.5) < hi]
        w = sum(x[6] for x in s)
        print(f"  {f} |f - 1/2| in [{lo}, {hi}): {len(s)} rounds, hazard {sum(x[5] * x[6] for x in s) / w:.3f}")
print("every F round with f within 0.05 of 1/2 but not 1/2 (after round 1), F against S:")
for (f, n, j, r), (fr, h, t) in sorted(by.items()):
    if f == "f" and r > 1 and fr != 0.5 and abs(fr - 0.5) < 0.05:
        hs, ts = by[("s", n, j, r)][1:]
        se = 2 * math.sqrt(h * (1 - h) / t + hs * (1 - hs) / ts)
        print(f"  n {n} j {j} round {r} f {fr:.4f}: F {h:.3f} ({t}), S {hs:.3f} ({ts}); S - F {hs - h:+.3f} (2 SE {se:.3f})")
