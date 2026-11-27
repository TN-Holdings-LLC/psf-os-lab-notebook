"""The per-qubit records of several Ohm ruler nights side by side (workplace VS, 2026-11-27; home instruction 2, 3).
Read only: it writes a CSV and a summary of what the nights' records already say, and it is no part of any verdict.

Per night (results/<night>):
  - when the night holds qubits.csv (the fourth night on), its rows as written;
  - otherwise (2026-11-24, 2026-11-25) the same columns rebuilt from the record's raw counts by
    tools/independent_recount.py's score_ohm_ruler4 (the |0> mirror, r_q, and m_q where string mirrors were sent;
    e_q only where readout circuits were sent: empty otherwise).
Columns: night, device, calibration_time (a time only), copy_drow, arm, t, position, physical, in_window, mirror_z,
m_q, r_q, e_q, r_over_e (r_q / e_q where both exist), MIRROR_LOW, R_LOW, R_HIGH (R_LOW / R_HIGH at t >= 3 only, as the
declared tool). Values are written to 3 decimals.

  python tools/qubits_across.py results/NIGHT [results/NIGHT ...] --out qubits_across.csv [--summary summary.md]
"""
import argparse
import csv
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

COLS = ["night", "device", "calibration_time", "copy_drow", "arm", "t", "position", "physical", "in_window",
        "mirror_z", "m_q", "r_q", "e_q", "r_over_e", "MIRROR_LOW", "R_LOW", "R_HIGH", "source"]


def _f(x):
    if x in (None, "", "nan"):
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _b(x):
    return str(x).strip().lower() == "true" if isinstance(x, str) else bool(x)


def _r3(x):
    return "" if x is None else f"{x:.3f}"


def from_csv(night):
    rows = []
    for r in csv.DictReader(open(os.path.join(night, "qubits.csv"), encoding="utf-8")):
        rows.append(dict(device=r.get("device", ""), calibration_time=r.get("calibration_time", ""),
                         copy_drow=r.get("copy_drow", ""), arm=r["arm"], t=int(r["t"]), position=int(r["position"]),
                         physical=int(r["physical"]), in_window=_b(r.get("in_window")), mirror_z=_f(r.get("mirror_z")),
                         m_q=_f(r.get("m_q")), r_q=_f(r.get("r_q")), e_q=_f(r.get("e_q")),
                         MIRROR_LOW=_b(r.get("MIRROR_LOW")), R_LOW=_b(r.get("R_LOW")), R_HIGH=_b(r.get("R_HIGH")),
                         source="qubits.csv"))
    return rows


def from_record(night):
    import independent_recount as IR
    outs = [os.path.dirname(b) for b in glob.glob(os.path.join(night, "*", "build.json"))
            if os.path.exists(os.path.join(os.path.dirname(b), "job", "raw_counts.json"))]
    ans = sorted(glob.glob(os.path.join(night, "answers", "*by_label*.json")))
    if not outs or not ans:
        return []
    out_dir = outs[0]
    b = json.load(open(os.path.join(out_dir, "build.json")))
    man = json.load(open(os.path.join(out_dir, "job", "manifest.json")))
    src = man.get("device", {}).get("source")
    cal = src.get("calibration_time", "") if isinstance(src, dict) else ""
    res = IR.score_ohm_ruler4(out_dir, IR.load_job(os.path.join(out_dir, "job")), ans[0])
    rows = []
    for q in res["qubits"]:
        rows.append(dict(device=b.get("device", ""), calibration_time=cal,
                         copy_drow=(b.get("copy_of_F") or {}).get("drow", ""), arm=q["arm"], t=q["t"],
                         position=q["position"], physical=q["physical"], in_window=q["in_window"],
                         mirror_z=q["mirror_z"], m_q=q["m_q"], r_q=q["r_q"], e_q=q["e_q"],
                         MIRROR_LOW=q["MIRROR_LOW"], R_LOW=q["R_LOW"] and q["t"] >= 3,
                         R_HIGH=q["R_HIGH"] and q["t"] >= 3,
                         source=f"rebuilt from {os.path.relpath(out_dir, night)} by independent_recount"))
    return rows


def across(nights):
    out = []
    for n in nights:
        rows = from_csv(n) if os.path.exists(os.path.join(n, "qubits.csv")) else from_record(n)
        for r in rows:
            r["night"] = os.path.basename(os.path.normpath(n))
            r["r_over_e"] = (r["r_q"] / r["e_q"]) if (r["r_q"] is not None and r["e_q"]) else None
            out.append(r)
    return out


def summary(rows):
    """Per physical qubit at t = 4: in how many nights MIRROR_LOW / R_LOW / R_HIGH (any arm), and its |0> mirror by
    night (the lowest over the arms)."""
    nights = sorted({r["night"] for r in rows})
    per = {}
    for r in rows:
        if r["t"] != 4:
            continue
        p = per.setdefault(r["physical"], dict(ml=set(), rl=set(), rh=set(), mirror={}))
        if r["MIRROR_LOW"]:
            p["ml"].add(r["night"])
        if r["R_LOW"]:
            p["rl"].add(r["night"])
        if r["R_HIGH"]:
            p["rh"].add(r["night"])
        if r["mirror_z"] is not None:
            p["mirror"][r["night"]] = min(p["mirror"].get(r["night"], 9.0), r["mirror_z"])
    lines = ["| physical (t = 4) | MIRROR_LOW nights | R_LOW nights | R_HIGH nights | " +
             " | ".join(f"lowest mirror {n}" for n in nights) + " |",
             "|" + "---|" * (4 + len(nights))]
    for q in sorted(per, key=lambda q: (-len(per[q]["ml"]), q)):
        p = per[q]
        if not (p["ml"] or p["rl"] or p["rh"]):
            continue
        lines.append(f"| {q} | {len(p['ml'])} | {len(p['rl'])} | {len(p['rh'])} | " +
                     " | ".join(_r3(p["mirror"].get(n)) for n in nights) + " |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nights", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--summary")
    a = ap.parse_args()
    rows = across(a.nights)
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow({k: (_r3(r[k]) if k in ("mirror_z", "m_q", "r_q", "e_q", "r_over_e") else r.get(k, ""))
                        for k in COLS})
    s = summary(rows)
    if a.summary:
        open(a.summary, "w", encoding="utf-8").write(s + "\n")
    print(f"qubits_across: {len(rows)} rows from {len(a.nights)} nights -> {a.out}")
    print(s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
