"""Per (phase, round): the round's controlled-phase angle as a fraction of a turn, f = (j 2^m mod 2^n) / 2^n (round
reading clbit m), and the hazard of that round for that phase alone (beside, after the declaration; a hypothesis
search). Prints the highest hazards with their f, and the hazard binned by the distance of f from 1/2."""
import json
import math
import re
import sys

R = sys.argv[1]
rows = []
for jd in sys.argv[2:]:
    man = json.load(open(f"{R}/{jd}/job/manifest.json"))
    raw = json.load(open(f"{R}/{jd}/job/raw_counts.json"))
    cells = {c["cell"]: c for c in man["cells"]}
    cnt = {r["pub"]: r["counts"] for r in raw["rows"]}
    for i, p in enumerate(man["pubs"]):
        c = cells[p["cell"]]
        m_ = re.match(r"^ff_([a-z]+)(\d)_(\d+)$", c["name"])
        if c["role"] != "user" or not m_:
            continue
        form, n, j = m_.group(1), int(m_.group(2)), int(m_.group(3))
        rec = json.load(open(f"{R}/{jd}/runs/{c['name']}.json"))
        succ = {int(b): v for b, v in rec["success"].items()}
        if len(succ) != n:
            continue
        alive = cnt[i]
        for r, m in enumerate(range(n - 1, -1, -1)):
            tot = sum(alive.values())
            wrong = {k: v for k, v in alive.items() if int(k.replace(" ", "")[-1 - m]) != succ[m]}
            h = sum(wrong.values()) / tot if tot else 0
            f = ((j * 2 ** m) % 2 ** n) / 2 ** n
            rows.append((jd.split("/")[1], form, n, j, r + 1, f, h, tot))
            alive = {k: v for k, v in alive.items() if k not in wrong}
rows.sort(key=lambda x: -x[6])
print("highest per-round hazards (record, form, n, j, round, f, hazard, shots alive):")
for r in rows[:14]:
    print(f"  {r[0]:28s} {r[1]} n{r[2]} j{r[3]:3d} round {r[4]} f {r[5]:.4f} h {r[6]:.3f} ({r[7]})")
nontriv = [r for r in rows if r[5] not in (0.0,) and r[4] > 1]
for lo, hi in ((0.0, 0.02), (0.02, 0.05), (0.05, 0.15), (0.15, 0.3), (0.3, 0.5)):
    s = [r for r in nontriv if lo <= abs(r[5] - 0.5) < hi]
    if s:
        w = sum(r[7] for r in s)
        h = sum(r[6] * r[7] for r in s) / w
        print(f"|f - 1/2| in [{lo:.2f}, {hi:.2f}): {len(s)} rounds, hazard {h:.3f} (shots-weighted)")
