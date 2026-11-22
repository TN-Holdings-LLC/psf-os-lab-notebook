"""The anatomy of IPE on the device, round by round (home VS, 2026-11-22 night; home instruction "IPE の解剖", part A).
**Beside, after the declarations: every number here was cut from records after their nights were declared and scored;
the patterns are hypotheses, to be settled only by a declared test (part B).**

For every IPE item of the recorded nights (apps.ipe: round 1 reads clbit n-1, round n reads clbit 0; round r holds r - 1
phase-feedback conditionals, and every round but the last a reset conditional):
  hazard h_r = P(round r's bit wrong | every earlier round's bit right), pooled over the odd phases (every round
  non-trivial), per night, form and n, with 2 SE;
  where each round's read sits in the compiled circuit: its layer (a running depth over the qubits, barriers
  synchronising), and the reads and conditionals before it (the record has no durations: no time in microseconds);
  beside, within each n, log P against the compiled CZ over all phases (slope per CZ).

  python notes/ipe_anatomy_2026-11-22/anatomy.py NOTEBOOK OUT.json
"""
import json
import math
import os
import re
import sys

import numpy as np
from qiskit import qpy

NB = sys.argv[1]
OUT = sys.argv[2]
# night, job folders, tag prefix -> form
NIGHTS = [
    ("11-19 marrakesh (0.2, as sent)", ["results/qpe-repro-night-2026-11-19/qA", "results/qpe-repro-night-2026-11-19/qB"],
     {"ipe": "unparked"}),
    ("11-21 weekend marrakesh", ["results/weekend-shared-night-2026-11-21/BC/job0",
                                 "results/weekend-shared-night-2026-11-21/BC/job1"],
     {"ipe": "unparked", "pl": "unparked (C pl)", "fe": "fenced |1>", "pk": "parked"}),
    ("11-21 parked marrakesh", ["results/qpe-parked-night-2026-11-21/qp/job0",
                                "results/qpe-parked-night-2026-11-21/qp/job1"], {"ipe": "parked", "ipu": "unparked"}),
    ("11-21 RUS fence fez (control)", ["results/rus-fence-night-2026-11-21/rf/job0"], {"ipk": "parked", "ipu": "unparked"}),
    ("11-22 0.3.1 candidate kingston (control)", ["results/likely-park-night-2026-11-22/lp/job0"],
     {"ipk": "parked", "ipu": "unparked"}),
    ("11-22 n = 6, 7, 8 fez", ["results/qpe-n78-night-2026-11-22/qn/job0"], {"ipk": "parked", "ipu": "unparked"}),
]


def bit(k, i):
    return int(k.replace(" ", "")[-1 - i])


def positions(c):
    """Per measurement in program order: (clbit, layer, reads before, conditionals before)."""
    t = {}
    out = []
    reads = conds = 0
    for x in c.data:
        qs = [c.find_bit(q).index for q in x.qubits]
        name = x.operation.name
        if name == "barrier":
            m = max((t.get(q, 0) for q in qs), default=0)
            for q in qs:
                t[q] = m
            continue
        m = max((t.get(q, 0) for q in qs), default=0) + 1
        for q in qs:
            t[q] = m
        if name == "measure":
            out.append((c.find_bit(x.clbits[0]).index, m, reads, conds))
            reads += 1
        elif name == "if_else":
            conds += 1
    return out


res = {}
for night, folders, forms in NIGHTS:
    data = {}                       # (form, n) -> dict(first, alive, items, layers, logp_cz)
    for f in folders:
        jd = os.path.join(NB, f)
        man = json.load(open(os.path.join(jd, "job", "manifest.json")))
        raw = json.load(open(os.path.join(jd, "job", "raw_counts.json")))
        cs = qpy.load(open(os.path.join(jd, "job", "circuits.qpy"), "rb"))
        cells = {c["cell"]: c for c in man["cells"]}
        cnt = {r["pub"]: r["counts"] for r in raw["rows"]}
        for i, p in enumerate(man["pubs"]):
            c = cells[p["cell"]]
            m_ = re.match(r"^ff_([a-z]+)(\d)_(\d+)$", c["name"])
            if c["role"] != "user" or not m_ or m_.group(1) not in forms:
                continue
            form, n, j = forms[m_.group(1)], int(m_.group(2)), int(m_.group(3))
            rec = json.load(open(os.path.join(jd, "runs", c["name"] + ".json")))
            succ = {int(b): v for b, v in rec["success"].items()}
            if len(succ) != n:
                continue
            d = data.setdefault((form, n), dict(first=[0] * n, alive=[0] * n, layers=[], cz_logp=[]))
            N = sum(cnt[i].values())
            ok = sum(v for k, v in cnt[i].items() if all(bit(k, b) == x for b, x in succ.items()))
            cz = sum(1 for x in cs[i].data if x.operation.name == "cz")
            d["cz_logp"].append((cz, math.log(max(ok, 1) / N)))
            tz = (j & -j).bit_length() - 1 if j else n
            d.setdefault("items", []).append((tz, cnt[i], succ, positions(cs[i])))
    for (form, n), d in sorted(data.items()):
        # the phases with the fewest trailing zeros: odd phases where present (every round non-trivial); a night
        # with even phases only (the controls: 2, 6, 10, 14) falls back to tz = 1, where round 1 is trivial
        tz0 = min(t for t, *_ in d["items"])
        if tz0 >= n:
            continue
        for tz, counts, succ, pos in d["items"]:
            if tz != tz0:
                continue
            order = [cl for cl, *_ in pos][:n]
            d["layers"].append([(lay, rd, cd) for _cl, lay, rd, cd in pos[:n]])
            for k, v in counts.items():
                for r, b in enumerate(order):
                    d["alive"][r] += v
                    if bit(k, b) != succ[b]:
                        d["first"][r] += v
                        break
        h = [d["first"][r] / d["alive"][r] for r in range(n)]
        se = [2 * math.sqrt(h[r] * (1 - h[r]) / d["alive"][r]) for r in range(n)]
        lay = np.mean([[x[0] for x in L] for L in d["layers"]], axis=0)
        conds = d["layers"][0]
        x = np.array([a for a, _ in d["cz_logp"]], float)
        y = np.array([b for _, b in d["cz_logp"]])
        slope = float(np.linalg.lstsq(np.c_[np.ones(len(x)), x], y, rcond=None)[0][1]) if len(set(x)) > 1 else None
        res.setdefault(night, {})[f"{form} n={n}"] = dict(
            hazard=[round(v, 4) for v in h], two_se=[round(v, 4) for v in se], shots=d["alive"][0],
            layer=[round(float(v), 1) for v in lay], conditionals_before=[c for _l, _r, c in conds],
            reads_before=[r for _l, r, _c in conds], cz_slope=slope, phases_all=len(d["cz_logp"]),
            trivial_rounds=list(range(1, tz0 + 1)), phases_used="odd" if tz0 == 0 else f"tz={tz0}",
            jump_1_2=round(h[1] - h[0], 4) if n > 1 and tz0 == 0 else None,
            jump_2_3=round(h[2] - h[1], 4) if n > 2 and tz0 == 1 else None)
lines = ["Beside, after the declarations (hypotheses, not verdicts). Hazard h_r by round (round 1 read first), odd phases."]
for night, forms_ in res.items():
    lines.append(f"== {night}")
    for key, v in forms_.items():
        jump = (f" | jump 1->2 {v['jump_1_2']:+.3f}" if v["jump_1_2"] is not None else
                f" | round 1 trivial (phases {v['phases_used']}); jump 2->3 {v['jump_2_3']:+.3f}"
                if v["jump_2_3"] is not None else f" | phases {v['phases_used']}")
        lines.append(f"  {key} ({v['shots']} shots): h " + " ".join(f"{x:.3f}" for x in v["hazard"]) +
                     " | 2 SE " + " ".join(f"{x:.3f}" for x in v["two_se"]) + jump)
        lines.append(f"      layer of each read " + " ".join(f"{x:.0f}" for x in v["layer"]) + "; conditionals before "
                     + " ".join(str(x) for x in v["conditionals_before"]) +
                     (f"; within-n dlogP/dCZ {v['cz_slope']:+.4f} over {v['phases_all']} phases" if v["cz_slope"] is not None
                      else ""))
print("\n".join(lines))
open(OUT.replace(".json", ".txt"), "w").write("\n".join(lines) + "\n")
json.dump(res, open(OUT, "w"), indent=1)
