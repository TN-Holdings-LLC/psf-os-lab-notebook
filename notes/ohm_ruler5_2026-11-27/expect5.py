"""The fifth night draft's table of expected words, written from the fourth night's dry runs, never copied by hand
(workplace Claude, 2026-11-27).

Per ruler and t, the share of cells that AGREE at the t quantile in each dry-run case:
  - the workplace's readout cases (notes/ohm_ruler4_2026-11-26/scores4_dryruns.tar.gz: none, ro1, ro2, bo04);
  - the workplace VS's gate-noise and damping cases (notes/ohm_ruler4_2026-11-26/vs_2026-11-26/tab4_t13.md and
    tab4_t4.md, as its vs_ruler_table4.py printed them: dep0.01, dep0.02, damp0.005, damp0.01, rop2).
The fifth night's job is the fourth night's with its readout circuits moved (no gate changed), so these runs carry
over. Each (ruler, t) gets a class, by a rule fixed before any fifth-night data:
  EXPECTED TO AGREE   the share is at least 85 % in every case;
  EXPECTED TO DIFFER  the share is at most 15 % in every gate-noise or damping case (dep, damp, rop2);
  MIXED               otherwise.
With --check DRAFT, every row it prints must stand word for word in the draft (exit 1 otherwise).

  python notes/ohm_ruler5_2026-11-27/expect5.py [--check DRAFT]
"""
import argparse
import glob
import json
import os
import sys
import tarfile
import tempfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
N4 = os.path.join(ROOT, "notes", "ohm_ruler4_2026-11-26")
RULERS = (("de", "(de)"), ("a_prime", "(a')"), ("d", "(d)"), ("e", "(e)"))
WP_CASES = ("none", "ro1", "ro2", "bo04")
VS_CASES = ("dep0.01", "dep0.02", "damp0.005", "damp0.01", "rop2")
GATE = set(VS_CASES)


def workplace():
    out = defaultdict(lambda: [0, 0])          # (case, t, ruler) -> [agrees, cells]
    with tempfile.TemporaryDirectory() as tmp:
        with tarfile.open(os.path.join(N4, "scores4_dryruns.tar.gz")) as tf:
            tf.extractall(tmp, filter="data")
        for p in glob.glob(os.path.join(tmp, "seeds", "*.scores4.json")):
            case = os.path.basename(p).split(".scores4")[0].rsplit("_", 1)[0]
            s4 = json.load(open(p, encoding="utf-8"))
            s3 = json.load(open(p.replace(".scores4.", ".scores3."), encoding="utf-8"))
            for k, c4 in s4["cells"].items():
                t = int(k.split("_t")[1].split("_")[0])
                for r, _ in RULERS:
                    w = s3["cells"][k]["rulers"][r]["words"] if r == "d" else (c4.get(r) or {}).get("words")
                    if w is None:
                        continue
                    out[(case, t, r)][0] += w["t"] == "AGREES"
                    out[(case, t, r)][1] += 1
    return {k: 100.0 * a / n for k, (a, n) in out.items() if n}


def vs():
    out = {}
    cols = {"(a')": "a_prime", "(d)": "d", "(e)": "e", "(de)": "de"}
    for f in ("tab4_t13.md", "tab4_t4.md"):
        lines = [l for l in open(os.path.join(N4, "vs_2026-11-26", f), encoding="utf-8") if l.startswith("|")]
        head = [h.strip() for h in lines[0].strip("|\n").split("|")]
        for l in lines[2:]:
            v = [x.strip() for x in l.strip("|\n").split("|")]
            case, t = v[0].replace("t4", ""), int(v[1])
            for h, r in cols.items():
                cell = v[head.index(h)]
                if cell.startswith("-"):
                    continue
                out[(case, t, r)] = float(cell.split("/")[0])
    return out


def classify(shares):
    if all(x >= 85 for x in shares.values()):
        return "EXPECTED TO AGREE"
    g = [x for c, x in shares.items() if c in GATE]
    if g and all(x <= 15 for x in g):
        return "EXPECTED TO DIFFER"
    return "MIXED"


def table():
    wp, v = workplace(), vs()
    cases = WP_CASES + VS_CASES
    head = "| ruler | t | " + " | ".join(cases) + " | class |"
    rows, classes = [], {}
    for r, lab in RULERS:
        for t in (1, 3, 4):
            sh = {}
            for c in cases:
                x = wp.get((c, t, r)) if c in WP_CASES else v.get((c, t, r))
                if x is not None:
                    sh[c] = x
            if not sh:
                continue
            cls = classify(sh)
            classes[(r, t)] = cls
            rows.append(f"| {lab} | {t} | " + " | ".join("-" if c not in sh else f"{sh[c]:.0f}" for c in cases)
                        + f" | {cls} |")
    return head, rows, classes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check")
    ap.add_argument("--json", action="store_true", help="print the classes as JSON (for the tool's EXPECT table)")
    a = ap.parse_args()
    head, rows, classes = table()
    if a.json:
        print(json.dumps({f"{r}|{t}": c for (r, t), c in classes.items()}, indent=1))
        return
    print(head + "\n|" + "---|" * (len(head.split("|")) - 2))
    bad = 0
    draft = open(a.check, encoding="utf-8").read() if a.check else None
    for r in rows:
        ok = draft is None or r in draft
        bad += not ok
        print(r + ("" if ok else "   <- NOT IN THE DRAFT"))
    if draft is not None:
        print(f"check: {bad} row(s) not in the draft")
        sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
