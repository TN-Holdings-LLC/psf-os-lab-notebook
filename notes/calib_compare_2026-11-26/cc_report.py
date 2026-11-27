"""Tables for the calib_compare report of 2026-11-27 (workplace VS; author The Architect). Read only: findings.json
(fixed before the seal), the snapshots, and score.json from tools/calib_compare.py score. Writes markdown tables
and a JSON of the same numbers. Calibration numbers enter no verdict: they are written beside, as the memo says.

  python cc_report.py NOTEBOOK FINDINGS SNAPDIR SCORE OUT_MD OUT_JSON
"""
import collections
import datetime as dtm
import json
import os
import statistics as st
import sys

nb, fpath, sdir, spath, out_md, out_json = sys.argv[1:7]
sys.path.insert(0, os.path.join(nb, "tools"))
import calib_compare as CC  # noqa: E402

rows = [r for r in json.load(open(fpath))["rows"] if r["kind"] in CC.KINDS]
snaps, idx = CC.load_snapshots(sdir)
score = json.load(open(spath))
COLS = ["readout_error", "T1", "T2", "cz", "any"]
f3 = lambda x: "" if x is None else f"{x:.3f}"
f2 = lambda x: "" if x is None else f"{x:.2f}"
md, js = [], {}

# ---- 1. counts per kind (all devices) and per kind x device -------------------------------------------------------
agg = collections.defaultdict(collections.Counter)
chance = collections.defaultdict(list)
miss_q = collections.defaultdict(collections.Counter)          # IBM misses: (kind, device) -> physical qubit counts
ourmiss_col = collections.defaultdict(collections.Counter)     # our misses by the column(s) that mark them
for r in rows:
    s = snaps.get(r["job_id"])
    if s is None or not r["set"]:
        continue
    m, na = CC.marks(r, s)
    found, normal, n = set(r["found"]), set(r["set"]) - set(r["found"]), len(r["set"])
    for dev in (r["device"], "all"):
        for c in COLS:
            if c in na:
                agg[(r["kind"], dev, c)]["na_sets"] += 1
                continue
            a = agg[(r["kind"], dev, c)]
            a["sets"] += 1
            a["findings"] += len(found)
            a["hit"] += len(found & m[c])
            a["our_miss"] += len(normal & m[c])
            a["normal"] += len(normal)
            chance[(r["kind"], dev, c)].append(len(m[c] & set(r["set"])) / n)
    for q in found - m["any"]:
        miss_q[(r["kind"], r["device"])][q] += 1
    for q in normal & m["any"]:
        cols = tuple(c for c in ("readout_error", "T1", "T2", "cz") if q in m[c])
        ourmiss_col[r["kind"]][cols if len(cols) == 1 else ("several",)] += 1

def ctab(dev_filter):
    out = ["| kind | device | sets | findings | column | IBM hit | hit rate | chance | hit / chance | IBM miss | our miss |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for (kind, dev, c), a in sorted(agg.items()):
        if not dev_filter(dev) or not a["findings"] and not a["sets"]:
            continue
        ch = st.mean(chance[(kind, dev, c)]) if chance[(kind, dev, c)] else None
        rate = a["hit"] / a["findings"] if a["findings"] else None
        out.append(f"| {kind} | {dev} | {a['sets']} | {a['findings']} | {c} | {a['hit']} | {f3(rate)} | {f3(ch)} | "
                   f"{f2(rate / ch) if rate is not None and ch else ''} | {a['findings'] - a['hit']} | {a['our_miss']} |")
        js.setdefault("counts", []).append(dict(kind=kind, device=dev, column=c, **a, chance=ch))
    return out

md += ["## 1. Counts, all devices together", ""] + ctab(lambda d: d == "all") + [""]
md += ["## 2. Counts per device", ""] + ctab(lambda d: d != "all") + [""]

# check against score.json (the tool's own table)
tool = {(t["kind"], t["device"], t["column"]): t for t in score["table"]}
bad = [k for k, a in agg.items() if k[1] != "all" and k in tool and
       (tool[k].get("findings", 0), tool[k].get("ibm_hit", 0), tool[k].get("our_miss", 0)) != (a["findings"], a["hit"], a["our_miss"])]
md += [f"(Recount against the tool's score.json: {len(tool)} rows, {len(bad)} differ.)", ""]

# ---- 3. our misses by column ----------------------------------------------------------------------------------------
md += ["## 3. Our misses: which IBM column marks them (one column alone, or several)", "",
       "| kind | readout_error | T1 | T2 | cz | several |", "|---|---|---|---|---|---|"]
for kind, c in sorted(ourmiss_col.items()):
    md.append(f"| {kind} | " + " | ".join(str(c[(x,)]) for x in ("readout_error", "T1", "T2", "cz", "several")) + " |")
js["our_miss_by_column"] = {k: {"+".join(x): v for x, v in c.items()} for k, c in ourmiss_col.items()}
md.append("")

# ---- 4. IBM misses: the qubits we find most often that IBM marks on no column --------------------------------------
md += ["## 4. IBM misses: physical qubits found most often with no IBM mark on any column (top 5 per kind and device)",
       "", "| kind | device | qubit: times |", "|---|---|---|"]
for (kind, dev), c in sorted(miss_q.items()):
    md.append(f"| {kind} | {dev} | " + ", ".join(f"{q}: {v}" for q, v in c.most_common(5)) + " |")
js["ibm_miss_top"] = {f"{k}|{d}": c.most_common(10) for (k, d), c in miss_q.items()}
md.append("")

# ---- 5. age of the map ----------------------------------------------------------------------------------------------
ages = collections.defaultdict(list)
for a in score["snapshot_age_hours"]:
    ages[a["device"]].append(a["hours"])
md += ["## 5. Age of the map (job time minus the snapshot's last_update_date, hours; one per job)", "",
       "| device | jobs | median | min | max | over 24 h |", "|---|---|---|---|---|---|"]
for d, h in sorted(ages.items()):
    md.append(f"| {d} | {len(h)} | {f2(st.median(h))} | {f2(min(h))} | {f2(max(h))} | {sum(x > 24 for x in h)} |")
js["age_hours"] = {d: dict(n=len(h), median=st.median(h), min=min(h), max=max(h)) for d, h in ages.items()}
md.append("")

# ---- 6. day to day on one device: same qubit across snapshot days ---------------------------------------------------
meta = {r["job_id"]: (r["device"], r["job_created_utc"]) for r in json.load(open(fpath))["rows"] if r.get("job_created_utc")}
byday = collections.defaultdict(dict)          # (device, day) -> the snapshot of the day's earliest job
for jid in sorted((j for j in snaps if j in meta), key=lambda j: meta[j][1]):
    byday[(meta[jid][0], meta[jid][1][:10])].setdefault("s", snaps[jid])
ours = collections.defaultdict(set)            # device -> qubits that were in our sets
for r in rows:
    ours[r["device"]] |= set(r["set"])
md += ["## 6. Day to day: one snapshot per (device, day), that of the day's earliest job; per qubit of our sets, the largest over the smallest value "
       "across days (median over qubits), and how often a qubit in the device's worst eighth on one day is outside it on "
       "another", "", "| device | days | column | median max/min | worst-eighth turnover |", "|---|---|---|---|---|"]
js["day_to_day"] = []
for dev in sorted(ours):
    days = sorted(d for (dv, d) in byday if dv == dev)
    if len(days) < 2:
        continue
    for name, direction in CC.QUBIT_COLUMNS:
        ratios, worst_sets = [], []
        for q in ours[dev]:
            v = [byday[(dev, d)]["s"]["qubits"].get(q, {}).get(name) for d in days]
            v = [x for x in v if x]
            if len(v) >= 2:
                ratios.append(max(v) / min(v))
        for d in days:
            vals = {q: x.get(name) for q, x in byday[(dev, d)]["s"]["qubits"].items()}
            worst_sets.append(CC.worst(vals, CC.k_of(len(vals)), direction == "high"))
        turn = [len(a - b) / len(a) for a, b in zip(worst_sets, worst_sets[1:]) if a]
        md.append(f"| {dev} | {len(days)} | {name} | {f2(st.median(ratios)) if ratios else ''} | "
                  f"{f3(st.mean(turn)) if turn else ''} |")
        js["day_to_day"].append(dict(device=dev, days=len(days), column=name,
                                     median_ratio=st.median(ratios) if ratios else None,
                                     turnover=st.mean(turn) if turn else None))
md.append("")

# ---- 7. headline (device median) against our sets' values ----------------------------------------------------------
md += ["## 7. Headline (median over all qubits / all cz edges of the device) against the median over our set, per job "
       "and kind; shown: the median over jobs of (our set / headline)", "",
       "| kind | device | jobs | readout_error | T1 | T2 | cz |", "|---|---|---|---|---|---|---|"]
hv = collections.defaultdict(lambda: collections.defaultdict(list))
seen = set()
for r in rows:
    s = snaps.get(r["job_id"])
    key = (r["kind"], r["device"], r["job_id"], tuple(r["set"]))
    if s is None or not r["set"] or key in seen:
        continue
    seen.add(key)
    for name, _ in CC.QUBIT_COLUMNS:
        allv = [x.get(name) for x in s["qubits"].values() if x.get(name)]
        setv = [s["qubits"].get(q, {}).get(name) for q in r["set"]]
        setv = [x for x in setv if x]
        if allv and setv:
            hv[(r["kind"], r["device"])][name].append(st.median(setv) / st.median(allv))
    ev = [s["edges"].get(tuple(e)) for e in r["edges"]]
    ev = [x for x in ev if x]
    if ev and s["edges"]:
        hv[(r["kind"], r["device"])]["cz"].append(st.median(ev) / st.median(list(s["edges"].values())))
js["headline_ratio"] = {}
for (kind, dev), c in sorted(hv.items()):
    n = max(len(v) for v in c.values())
    md.append(f"| {kind} | {dev} | {n} | " + " | ".join(f2(st.median(c[x])) if c[x] else "" for x in
                                                        ("readout_error", "T1", "T2", "cz")) + " |")
    js["headline_ratio"][f"{kind}|{dev}"] = {x: st.median(v) for x, v in c.items() if v}
md.append("")

open(out_md, "w", encoding="utf-8").write("\n".join(md) + "\n")
def _r3(x):
    if isinstance(x, float):
        return round(x, 3)
    if isinstance(x, dict):
        return {k: _r3(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_r3(v) for v in x]
    return x


js["note"] = "floats rounded to 3 decimals"
json.dump(_r3(js), open(out_json, "w"), indent=1, default=str)
print(f"report tables: {len(rows)} rows read; {len(snaps)} snapshots; recount differences {len(bad)}")
