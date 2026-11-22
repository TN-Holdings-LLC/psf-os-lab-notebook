"""Per round, the number of phase-feedback conditionals that FIRE when every earlier bit is right (the earlier bits'
ones: c[m + d] = 1 fires the correction from bit m + d) against the round's hazard (beside, after the declaration; a
hypothesis). Pooled over every phase and every round after the first, per record and form: hazard by fired count, and
by fired count at a fixed number of conditionals present (r - 1) to tell 'fired' from 'present'."""
import json
import math
import re
import sys
from collections import defaultdict

R = sys.argv[1]
for jd in sys.argv[2:]:
    man = json.load(open(f"{R}/{jd}/job/manifest.json"))
    raw = json.load(open(f"{R}/{jd}/job/raw_counts.json"))
    cells = {c["cell"]: c for c in man["cells"]}
    cnt = {r["pub"]: r["counts"] for r in raw["rows"]}
    acc = defaultdict(lambda: [0, 0])          # (form, present, fired) -> [wrong, alive]
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
            present = r                                   # conditionals on the earlier bits c[m+1 .. n-1]
            fired = sum(succ[m + d] for d in range(1, n - m))
            trivial = ((j * 2 ** m) % 2 ** n) == 0        # the round's controlled phase is a whole turn
            tot = sum(alive.values())
            wrong = {k: v for k, v in alive.items() if int(k.replace(" ", "")[-1 - m]) != succ[m]}
            if r > 0 and not trivial and tot:
                a = acc[(form, present, fired)]
                a[0] += sum(wrong.values())
                a[1] += tot
            alive = {k: v for k, v in alive.items() if k not in wrong}
    print(f"== {jd}")
    for form in sorted({k[0] for k in acc}):
        byf = defaultdict(lambda: [0, 0])
        for (fm, pr, fi), (w, t) in acc.items():
            if fm == form:
                byf[fi][0] += w
                byf[fi][1] += t
        print(f"  {form}: hazard by fired corrections (rounds 2.., non-trivial): " + "; ".join(
            f"{fi}: {w / t:.3f} ({t})" for fi, (w, t) in sorted(byf.items())))
        # at fixed present count: the slope of hazard on fired
        for pr in sorted({k[1] for k in acc if k[0] == form}):
            cells_ = sorted((fi, w / t, t) for (fm, p2, fi), (w, t) in acc.items() if fm == form and p2 == pr)
            if len(cells_) >= 3:
                print(f"     present {pr}: " + ", ".join(f"fired {fi} {h:.3f}" for fi, h, t in cells_))
