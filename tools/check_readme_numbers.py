"""Check the numbers written in results/*/README.md against each night's records (home VS, 2026-11-23; home
instruction "README の数の照合", C). Reads only; nothing under results/ is written. Mismatches are listed for home
Claude to correct by hand.

What is checked, per night folder holding a README.md and at least one job record (job/raw_counts.json):
  1. job tables: every table row holding a job id of the night is compared, column by column, with that job's record:
     circuits (manifest pubs), shots (manifest), s model (manifest qpu_seconds_model), s charged and RU
     (raw_counts.json metrics.usage); a job id in the README that no record of the night holds is listed;
  2. charge in the text: "N s charged" / "charged N s" and "X RU" against the night's jobs (one job, or their sum);
  3. delays: "N µs" on a line about a delay or an idle, against the per-circuit delay totals of the night's
     circuits (dt from the night's dt.txt or the device record; nights without delays are skipped);
  4. P and differences: every 4-decimal value (0.1234, +0.0045, -0.6751) on a table row or a line with "2 SE" is
     looked for among the numbers of the night's score files (*.json and score*.txt outside the job folders),
     rounded to 4 places (and twice each number: a 2 SE from a stored SE); a value found nowhere is listed as "not found" (it may be quoted from another night: the
     line is shown so that a reader can tell).

  python tools/check_readme_numbers.py [RESULTS_DIR] [--json OUT.json] [--night NAME ...]
"""
import argparse
import glob
import json
import math
import os
import re
import sys

ID = re.compile(r"\b(d[a-z0-9]{19})\b")
DEC4 = re.compile(r"(?<![\w.])([+\-−]?\d\.\d{4})(?![\d])")
NUM = re.compile(r"[+\-−]?\d+(?:\.\d+)?(?:[eE][+\-]?\d+)?")


def fnum(s):
    return float(s.replace("−", "-").replace(",", ""))


def jobs_of(night):
    """{job id: dict(folder, circuits, shots, model, charged, ru)} from every job/raw_counts.json of the night."""
    out = {}
    for rc in sorted(glob.glob(os.path.join(night, "**", "raw_counts.json"), recursive=True)):
        try:
            raw = json.load(open(rc))
        except Exception:  # noqa: BLE001
            continue
        jid = raw.get("job_id")
        if not jid or str(jid).startswith("local"):
            continue
        usage = (raw.get("metrics") or {}).get("usage") or {}
        rec = dict(folder=os.path.relpath(os.path.dirname(rc), night), charged=usage.get("qpu_charge_time_seconds"),
                   ru=usage.get("value"), circuits=len(raw.get("rows", [])) or None, shots=None, model=None)
        mf = os.path.join(os.path.dirname(rc), "manifest.json")
        if os.path.exists(mf):
            man = json.load(open(mf))
            rec.update(circuits=len(man.get("pubs", [])) or rec["circuits"], shots=man.get("shots"),
                       model=man.get("qpu_seconds_model"))
        out[jid] = rec
    return out


def delays_of(night):
    """Sorted delay lengths in µs: per circuit the total (the longest sum over one qubit) and every single delay
    instruction (e.g. L per conditional); None when no circuit has a delay."""
    qfs = sorted(glob.glob(os.path.join(night, "**", "job", "circuits.qpy"), recursive=True))
    if not qfs:
        return None
    from qiskit import qpy
    dt = None
    if os.path.exists(os.path.join(night, "dt.txt")):
        dt = float(open(os.path.join(night, "dt.txt")).read().split()[0])
    tots = set()
    for q in qfs:
        mf = os.path.join(os.path.dirname(q), "manifest.json")
        d_dt = dt or (json.load(open(mf)).get("device", {}).get("dt") if os.path.exists(mf) else None)
        try:
            cs = qpy.load(open(q, "rb"))
        except Exception:  # noqa: BLE001
            continue
        for c in cs:
            per = {}
            for x in c.data:
                if x.operation.name == "delay":
                    k = c.find_bit(x.qubits[0]).index
                    per[k] = per.get(k, 0) + x.operation.duration
                    if d_dt:
                        tots.add(round(x.operation.duration * d_dt * 1e6, 3))
            if per and d_dt:
                tots.add(round(max(per.values()) * d_dt * 1e6, 3))
    return sorted(tots) or None


def score_numbers(night):
    """Every number in the night's score files (JSON outside the job folders and runs, score*.txt), rounded to 4."""
    vals = set()

    def walk(v):
        if isinstance(v, bool):
            return
        if isinstance(v, (int, float)):
            if math.isfinite(v):
                vals.add(round(float(v), 4))
                vals.add(round(2 * float(v), 4))          # a 2 SE written from a stored SE
        elif isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    for f in glob.glob(os.path.join(night, "**", "*.json"), recursive=True):
        parts = f.split(os.sep)
        if "job" in parts or "runs" in parts or "fetch_in" in parts or os.path.getsize(f) > 20_000_000:
            continue
        try:
            walk(json.load(open(f)))
        except Exception:  # noqa: BLE001
            pass
    for f in glob.glob(os.path.join(night, "**", "*.txt"), recursive=True):
        if "job" in f.split(os.sep) or os.path.getsize(f) > 5_000_000:
            continue
        for m in NUM.finditer(open(f, errors="replace").read()):
            try:
                vals.add(round(fnum(m.group(0)), 4))
            except ValueError:
                pass
    return vals


def tables(lines):
    """[(line number, header cells, row cells)] for every markdown table row under a header."""
    out, head = [], None
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith("|") and s.endswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if head is None:
                head = [c.lower() for c in cells]
            elif all(set(c) <= set("-: ") for c in cells):
                continue
            else:
                out.append((i + 1, head, cells))
        else:
            head = None
    return out


COLS = (("circuits", ("circuits",)), ("shots", ("shots",)), ("model", ("s model", "model")),
        ("charged", ("s charged", "charged")), ("ru", ("ru",)))


def close(a, b, tol):
    return a is not None and b is not None and abs(a - b) <= tol


def check_night(night):
    readme = os.path.join(night, "README.md")
    jobs = jobs_of(night)
    if not os.path.exists(readme) or not jobs:
        return None
    lines = open(readme, encoding="utf-8", errors="replace").read().splitlines()
    found, notfound = [], []
    # 1. job tables
    for ln, head, cells in tables(lines):
        ids = [m.group(1) for c in cells for m in ID.finditer(c)]
        for jid in ids:
            if jid not in jobs:
                found.append(dict(line=ln, what="job id", readme=jid, record="not in this night's records"))
                continue
            rec = jobs[jid]
            for key, names in COLS:
                col = next((k for k, h in enumerate(head) if any(h == n or h.startswith(n) for n in names)), None)
                if col is None or col >= len(cells) or rec.get(key) is None:
                    continue
                m = NUM.search(cells[col].replace("*", ""))
                if not m:
                    continue
                v = fnum(m.group(0))
                tol = {"ru": 0.0006, "model": 0.051}.get(key, 0.5 if key == "charged" else 0)
                if not close(v, float(rec[key]), tol):
                    found.append(dict(line=ln, what=f"{key} of {jid}", readme=v, record=rec[key]))
    # 2. charge and RU in the text
    charged = [float(r["charged"]) for r in jobs.values() if r["charged"] is not None]
    rus = [float(r["ru"]) for r in jobs.values() if r["ru"] is not None]
    for i, ln in enumerate(lines):
        if ln.strip().startswith("|"):
            continue
        for m in re.finditer(r"(\d+(?:\.\d+)?)\s*s(?:econds)?\s+charged|charged\s+(\d+(?:\.\d+)?)\s*s\b", ln):
            v = float(m.group(1) or m.group(2))
            if charged and not (any(close(v, c, 0.5) for c in charged) or close(v, sum(charged), 0.5 + len(charged))):
                found.append(dict(line=i + 1, what="s charged (text)", readme=v, record=charged, text=ln.strip()))
        for m in re.finditer(r"(\d+\.\d+)\s*RU\b", ln):
            v = float(m.group(1))
            if rus and not (any(close(v, r, 0.0006) for r in rus) or close(v, sum(rus), 0.001 * len(rus))):
                found.append(dict(line=i + 1, what="RU (text)", readme=v, record=[round(r, 6) for r in rus],
                                  text=ln.strip()))
    # 3. delays
    dl = delays_of(night)
    if dl:
        for i, ln in enumerate(lines):
            if not re.search(r"delay|idle|idling|wait", ln, re.I):
                continue
            for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:µs|μs|us)\b", ln):
                v = float(m.group(1))
                if not any(abs(v - d) <= max(0.5, 0.005 * d) for d in dl):
                    found.append(dict(line=i + 1, what="delay µs", readme=v, record=dl, text=ln.strip()))
    # 4. P and differences
    vals = score_numbers(night)
    for i, ln in enumerate(lines):
        if not (ln.strip().startswith("|") or "2 SE" in ln):
            continue
        for m in DEC4.finditer(ln):
            v = round(fnum(m.group(1)), 4)
            if v not in vals and -v not in vals and not any(abs(v - x) <= 0.00011 for x in vals):
                notfound.append(dict(line=i + 1, value=m.group(1), text=ln.strip()[:160]))
    return dict(jobs=len(jobs), mismatches=found, not_found=notfound, delays_us=dl)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results", nargs="?", default="results")
    ap.add_argument("--json")
    ap.add_argument("--night", nargs="*")
    a = ap.parse_args()
    nights = sorted(d for d in glob.glob(os.path.join(a.results, "*")) if os.path.isdir(d))
    if a.night:
        nights = [n for n in nights if os.path.basename(n) in a.night]
    res, nm, nn, checked = {}, 0, 0, 0
    for n in nights:
        r = check_night(n)
        if r is None:
            continue
        checked += 1
        res[os.path.basename(n)] = r
        nm += len(r["mismatches"])
        nn += len(r["not_found"])
        for x in r["mismatches"]:
            print(f"MISMATCH {os.path.basename(n)}/README.md:{x['line']}: {x['what']}: README {x['readme']}, record "
                  f"{x['record']}" + (f"  | {x['text'][:120]}" if "text" in x else ""))
    for n, r in res.items():
        for x in r["not_found"]:
            print(f"not found {n}/README.md:{x['line']}: {x['value']}  | {x['text'][:120]}")
    print(f"{checked} nights checked (README and a job record); {nm} mismatches; {nn} values not found in the "
          "night's score files")
    if a.json:
        json.dump(res, open(a.json, "w"), indent=1, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
