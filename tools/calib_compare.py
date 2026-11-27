"""Our records against IBM's calibration, counted as notes/calib_compare_2026-11-26/memo.md fixes (workplace VS,
2026-11-26; author The Architect). Comparison only: nothing here enters a verdict, a placement or a correction.

  findings  from the records alone (no calibration number is opened: no fetch_in/*/dev file, no calib_history file,
            and of a manifest's "device" only the couplers): per job of the targets list, the findings of each kind
            (mirror_low, r_low, sentinel_dead, sentinel_weak, scan_listed) with the set they were found in and the
            record file they come from
  score     with home's snapshots (fetch_calib_history.py's OUT_DIR): IBM's marks on each set (worst k of the set per
            column, k = max(1, round(n / 8))), and the counts both ways (IBM hit, IBM miss, our miss) per kind, device
            and column, with the chance rate k / n beside; plus the age of each snapshot

  python tools/calib_compare.py findings TARGETS.json OUT_FINDINGS.json [--root .]
  python tools/calib_compare.py score FINDINGS.json SNAPSHOT_DIR OUT_SCORE.json
"""
import argparse
import collections
import datetime as dtm
import glob
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

TAU_MIRROR = 0.3           # memo 1: mirror_low below this mean <Z> (the third night's tau) ...
MIRROR_SET_MEDIAN = 0.6    # ... in a set whose median mirror <Z> is at least this (else: too deep, not read)
R_LOW_SIGMA = -2.0         # memo 1: r_low when (r_q - r_pool) / SE_q is below this, in a NOT UNIFORM cell
KINDS = ("mirror_low", "r_low", "sentinel_dead", "sentinel_weak", "scan_listed")
QUBIT_COLUMNS = (("readout_error", "high"), ("T1", "low"), ("T2", "low"))
EDGE_COLUMN = ("cz", "gate_error")


def k_of(n):
    """memo 2: the worst k of a set of n."""
    return max(1, int(round(n / 8))) if n else 0


# ------------------------------------------------------------------------------------------------ findings
def _couplers(manifest):
    return [tuple(sorted(int(x) for x in c)) for c in manifest.get("device", {}).get("couplers", [])]


def _edges_in(qubits, couplers, ring=None):
    """The set's edges: the device's couplers with both ends in the set; when the record holds no couplers (the
    records before 2026-11-03) and the set is a ring, the ring's neighbouring pairs, cyclic (memo addendum A3)."""
    s = set(qubits)
    if couplers:
        return sorted({c for c in couplers if c[0] in s and c[1] in s})
    if ring:
        return sorted({tuple(sorted((int(ring[i]), int(ring[(i + 1) % len(ring)])))) for i in range(len(ring))})
    return []


def mirror_findings(job, job_meta, couplers, record, job_dir=None):
    """mirror_low per |0> mirror pub (cell role "mirror" and run record kind "user2d_mirror": ideal |0> on every
    measured qubit): the set is the mirror's measured qubits. A set whose median mirror <Z> is below
    MIRROR_SET_MEDIAN is too deep to place a fault: it is kept as kind "mirror_too_deep" with no finding."""
    import numpy as np
    import independent_recount as IR
    role = {c["cell"]: c.get("role") for c in job["manifest"]["cells"]}
    runs = os.path.join(os.path.dirname(job_dir or record), "runs")
    out = []
    for p, pb in zip(job["pubs"], job["manifest"]["pubs"]):
        if role.get(pb["cell"]) != "mirror" or not p["counts"]:
            continue
        rf = os.path.join(runs, p["name"].split("#")[0] + ".json")
        kind = json.load(open(rf)).get("psfos_job", {}).get("kind") if os.path.exists(rf) else None
        if kind != "user2d_mirror":
            out.append(dict(job_meta, kind="mirror_other", context=p["name"], set=[], edges=[], found=[],
                            source=f"{record} (mirror pub {p['name']}, run kind {kind}: not a |0> mirror)"))
            continue
        qs = sorted(p["meas"])
        z = IR.z_from_counts(p["counts"], [p["meas"][q] for q in qs])
        src = os.path.join(record, "raw_counts.json").replace("\\", "/") + " (mirror pub " + p["name"] + ")"
        if float(np.median(z)) < MIRROR_SET_MEDIAN:
            out.append(dict(job_meta, kind="mirror_too_deep", context=p["name"], set=qs, edges=[], found=[],
                            source=src))
            continue
        low = [q for q, v in zip(qs, z) if v < TAU_MIRROR]
        out.append(dict(job_meta, kind="mirror_low", context=p["name"], set=qs, edges=_edges_in(qs, couplers),
                        found=low, source=src))
    return out


def r_findings(night_dir, job_meta, couplers):
    """r_low from the Ohm ruler nights' scores (uniform per position), positions to qubits by build.json."""
    out = []
    for sf in sorted(glob.glob(os.path.join(night_dir, "*", "scores.json")) +
                     glob.glob(os.path.join(night_dir, "*", "scores3.json"))):
        sc = json.load(open(sf))
        if "uniform" not in sc:
            continue
        bj = os.path.join(os.path.dirname(sf), "build.json")
        if not os.path.exists(bj):
            continue
        items = json.load(open(bj)).get("items", {})
        for cell, u in sorted(sc["uniform"].items()):
            it = items.get(f"{cell}_s00")
            if not it or "positions" not in u or not u.get("se"):
                continue
            phys = dict(zip(it["positions"], it["physical"]))
            qs = [phys[p] for p in u["positions"]]
            low = []
            if u.get("word") == "NOT UNIFORM":
                low = [phys[p] for p, r, se in zip(u["positions"], u["r"], u["se"])
                       if se > 0 and (r - u["r_pool"]) / se < R_LOW_SIGMA]
            out.append(dict(job_meta, kind="r_low", context=cell, set=sorted(qs), edges=_edges_in(qs, couplers),
                            found=sorted(low), source=os.path.relpath(sf).replace("\\", "/") + f" (uniform {cell})"))
    return out


def sentinel_findings(job_dir, job_meta, couplers, record):
    """sentinel_dead / sentinel_weak from psf-os's own verdict on the record (the ring is the set)."""
    from psf_os import sentinel
    runs = os.path.join(os.path.dirname(job_dir), "runs")
    if not os.path.isdir(runs):
        return []
    try:
        v = sentinel.verdict(job_dir, runs)
    except Exception as e:                                # recorded, not hidden
        return [dict(job_meta, kind="sentinel_error", context="", set=[], edges=[], found=[],
                     source=f"{record} ({type(e).__name__})")]
    out = []
    for name, c in sorted(v["cells"].items()):
        ring_order = [int(q) for q in c["ring"]]
        ring = sorted(ring_order)
        dead = sorted({int(q) for r in c["dead"] for q in r["qubits"]})
        weak = sorted({int(q) for r in c["weak"] for q in r["qubits"]} - set(dead))
        src = f"{record} (psf_os.sentinel.verdict, cell {name})"
        if len(dead) > len(ring) / 2:              # memo 1: more than half the ring dead places no fault
            out.append(dict(job_meta, kind="sentinel_dead_wide", context=name, set=ring, edges=[], found=[],
                            source=src))
            dead = []
        for kind, found in (("sentinel_dead", dead), ("sentinel_weak", weak)):
            out.append(dict(job_meta, kind=kind, context=name, set=ring, edges=_edges_in(ring, couplers, ring_order),
                            found=found, source=src))
    return out


def scan_observe_findings(job_dir, job_meta, couplers, record):
    """scan_listed read from the job itself (memo addendum A2): psf-os's own scan reading (psf_os.scan.observe, the
    reading that wrote the coverage days' observations) on the job's echo-scan rings; a job without such a ring gives
    nothing. The runs folder is the job folder's sibling named with "runs" for "job" (job -> runs,
    job_fold_rule -> runs_fold_rule)."""
    from psf_os import scan as SC
    base = os.path.basename(os.path.normpath(job_dir))
    runs = os.path.join(os.path.dirname(os.path.normpath(job_dir)), base.replace("job", "runs", 1))
    if not os.path.isdir(runs):
        return []
    try:
        obs = SC.observe([(job_meta["device"], job_dir, runs, "calib_compare")])
    except Exception as e:                                # recorded, not hidden
        return [dict(job_meta, kind="scan_error", context="", set=[], edges=[], found=[],
                     source=f"{record} (psf_os.scan.observe: {type(e).__name__})")]
    out = []
    for o in obs:
        ring_order = [int(q) for q in o["ring"]]
        found = sorted({int(q) for r in o.get("dead", []) for q in r["qubits"]})
        out.append(dict(job_meta, kind="scan_listed", context=f"n{o['n']}", set=sorted(ring_order),
                        edges=_edges_in(ring_order, couplers, ring_order), found=found,
                        source=f"{record} (psf_os.scan.observe, ring n {o['n']})"))
    return out


def scan_findings(root, by_job):
    """scan_listed from the coverage days' list_after.json observations (deduplicated by job and path)."""
    seen, out = set(), []
    for f in sorted(glob.glob(os.path.join(root, "results", "*", "list_after.json"))):
        d = json.load(open(f))
        for o in d.get("observations", []):
            meta = by_job.get(o.get("job"))
            if meta is None:
                continue
            ring_order = [int(q) for q in o.get("ring", [])]
            ring = sorted(ring_order)
            found = sorted({int(q) for r in o.get("dead", []) for q in r["qubits"]})
            key = (o["job"], tuple(ring), tuple(found))
            if key in seen:
                continue
            seen.add(key)
            out.append(dict(meta["meta"], kind="scan_listed", context=f"n{o.get('n', len(ring))}", set=ring,
                            edges=_edges_in(ring, meta["couplers"], ring_order), found=found,
                            source=os.path.relpath(f).replace("\\", "/") + f" (observation {o['label']})"))
    return out


def findings(targets, root="."):
    import independent_recount as IR
    rows, by_job, skipped = [], {}, []
    for t in targets:
        job_dir = os.path.join(root, t["record"])
        meta = {k: t[k] for k in ("night", "device", "job_id", "job_created_utc")}
        if not os.path.exists(os.path.join(job_dir, "manifest.json")):
            skipped.append(dict(meta, why="no manifest"))
            continue
        man = json.load(open(os.path.join(job_dir, "manifest.json")))
        couplers = _couplers(man)
        by_job[t["job_id"]] = dict(meta=meta, couplers=couplers)
        rows += scan_observe_findings(job_dir, meta, couplers, t["record"])       # addendum A2: every job
        try:
            job = IR.load_job(job_dir)
        except Exception as e:
            # addendum A1: a record in the layout before 2026-11-03 (raw_counts.json.gz, no circuits in the job
            # folder, no cell roles) holds no |0> mirror, sentinel or Ohm cell: it is read for the scan alone
            old = os.path.exists(os.path.join(job_dir, "raw_counts.json.gz"))
            skipped.append(dict(meta, why=("old layout: read for the scan only" if old else
                                           f"load_job {type(e).__name__}: {e}"[:200]), read_scan=old))
            continue
        rows += mirror_findings(job, meta, couplers, t["record"], job_dir)
        rows += sentinel_findings(job_dir, meta, couplers, t["record"])
        night_dir = os.path.join(root, "results", t["record"].replace("\\", "/").split("/")[1])
        if t["record"].replace("\\", "/").split("/")[0] == "results":
            rows += r_findings(night_dir, meta, couplers)
    rows += scan_findings(root, by_job)
    # r_findings reads a night's scores once per job of that night: keep one row per (job, kind, context)
    uniq, out = set(), []
    for r in rows:
        key = (r["job_id"], r["kind"], r["context"]) if r["kind"] == "scan_listed" else             (r["job_id"], r["kind"], r["context"], r["source"])
        if key not in uniq:
            uniq.add(key)
            out.append(r)
    return out, skipped


def summarize(rows):
    c = collections.Counter()
    q = collections.Counter()
    for r in rows:
        c[r["kind"]] += 1
        q[r["kind"]] += len(r["found"])
    return {k: dict(sets=c[k], findings=q[k]) for k in sorted(c)}


# ------------------------------------------------------------------------------------------------ scoring
def parse_snapshot(d):
    """{"qubits": {q: {name: value}}, "edges": {(a, b): cz gate_error}, "last_update": str} from
    BackendProperties.to_dict()."""
    qubits = {}
    for i, props in enumerate(d.get("qubits", [])):
        qubits[i] = {p["name"]: p.get("value") for p in props if "name" in p}
    edges = {}
    for g in d.get("gates", []):
        if g.get("gate") != EDGE_COLUMN[0] or len(g.get("qubits", [])) != 2:
            continue
        val = next((p.get("value") for p in g.get("parameters", []) if p.get("name") == EDGE_COLUMN[1]), None)
        e = tuple(sorted(int(x) for x in g["qubits"]))
        if val is not None:
            edges[e] = val if e not in edges else max(edges[e], val)
    return dict(qubits=qubits, edges=edges, last_update=d.get("last_update_date"))


def worst(values, k, high_is_worse):
    """The keys among the worst k (ties at the k-th value included); values with None are left out."""
    vals = {key: v for key, v in values.items() if v is not None}
    if not vals or k <= 0:
        return set()
    order = sorted(vals.values(), reverse=high_is_worse)
    cut = order[min(k, len(order)) - 1]
    return {key for key, v in vals.items() if (v >= cut if high_is_worse else v <= cut)}


def marks(row, snap):
    """{column: set of marked qubits} for one finding row's set, and the NOT AVAILABLE columns."""
    qs, out, na = row["set"], {}, []
    k = k_of(len(qs))
    for name, direction in QUBIT_COLUMNS:
        vals = {q: snap["qubits"].get(q, {}).get(name) for q in qs}
        if all(v is None for v in vals.values()):
            na.append(name)
        out[name] = worst(vals, k, direction == "high")
    ev = {e: snap["edges"].get(tuple(e)) for e in map(tuple, row["edges"])}
    if not ev or all(v is None for v in ev.values()):
        na.append("cz")
        out["cz"] = set()
    else:
        bad = worst(ev, k_of(len(ev)), True)
        out["cz"] = {q for e in bad for q in e}
    out["any"] = set().union(*[out[c] for c in out])
    return out, na


def score(rows, snapshots, now=None):
    """Counts both ways per (kind, device, column)."""
    cols = [c for c, _ in QUBIT_COLUMNS] + ["cz", "any"]
    cnt = collections.defaultdict(lambda: collections.Counter())
    chance = collections.defaultdict(list)
    ages, missing = [], []
    for r in rows:
        if r["kind"] not in KINDS:
            continue
        snap = snapshots.get(r["job_id"])
        if snap is None:
            missing.append(r["job_id"])
            continue
        m, na = marks(r, snap)
        found, normal = set(r["found"]), set(r["set"]) - set(r["found"])
        for c in cols:
            key = (r["kind"], r["device"], c)
            if c in na:
                cnt[key]["not_available_sets"] += 1
                continue
            cnt[key]["findings"] += len(found)
            cnt[key]["ibm_hit"] += len(found & m[c])
            cnt[key]["ibm_miss"] += len(found - m[c])
            cnt[key]["our_miss"] += len(normal & m[c])
            if c != "any" and r["set"]:
                chance[key].append(len(m[c] & set(r["set"])) / len(r["set"]))
        if snap.get("last_update") and r.get("job_created_utc"):
            try:
                t_job = dtm.datetime.fromisoformat(r["job_created_utc"].replace("Z", "+00:00"))
                t_cal = dtm.datetime.fromisoformat(str(snap["last_update"]).replace("Z", "+00:00"))
                if t_cal.tzinfo is None:
                    t_cal = t_cal.replace(tzinfo=dtm.timezone.utc)
                ages.append(dict(job_id=r["job_id"], device=r["device"], hours=(t_job - t_cal).total_seconds() / 3600))
            except ValueError:
                pass
    table = []
    for (kind, device, c), v in sorted(cnt.items()):
        ch = chance.get((kind, device, c))
        table.append(dict(kind=kind, device=device, column=c, **v,
                          chance_rate=(sum(ch) / len(ch)) if ch else None))
    by_job_age = {a["job_id"]: a for a in ages}
    return dict(table=table, snapshot_age_hours=sorted(by_job_age.values(), key=lambda a: a["job_id"]),
                jobs_without_snapshot=sorted(set(missing)))


def load_snapshots(snap_dir):
    idx = json.load(open(os.path.join(snap_dir, "index.json")))
    out = {}
    for r in idx["rows"]:
        if r.get("ok"):
            out[r["job_id"]] = parse_snapshot(json.load(open(os.path.join(snap_dir, r["file"]))))
    return out, idx


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("findings")
    p.add_argument("targets")
    p.add_argument("out")
    p.add_argument("--root", default=".")
    p = sp.add_parser("score")
    p.add_argument("findings")
    p.add_argument("snapshots")
    p.add_argument("out")
    a = ap.parse_args()
    if a.cmd == "findings":
        targets = json.load(open(a.targets, encoding="utf-8"))
        rows, skipped = findings(targets, a.root)
        summ = summarize(rows)
        json.dump(dict(memo="notes/calib_compare_2026-11-26/memo.md", targets=len(targets), skipped=skipped,
                       summary=summ, rows=rows), open(a.out, "w"), indent=1)
        print(f"calib_compare findings: {len(targets)} jobs, {len(skipped)} skipped; " +
              "; ".join(f"{k} {v['findings']} in {v['sets']} sets" for k, v in summ.items()))
        return 0
    rows = json.load(open(a.findings))["rows"]
    snaps, idx = load_snapshots(a.snapshots)
    res = score(rows, snaps)
    res.update(memo_sha256_at_fetch=idx.get("memo_sha256"), snapshots=len(snaps))
    json.dump(res, open(a.out, "w"), indent=1, default=str)
    print(f"calib_compare score: {len(snaps)} snapshots; {len(res['table'])} rows written to {a.out} (no number here)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
