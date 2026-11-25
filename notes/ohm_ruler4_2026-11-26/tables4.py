"""The fourth night draft's dry-run tables written from the scores themselves, never copied by hand (workplace Claude,
2026-11-26; tables3.py's form, extended to score4's rulers).

Reads <case>_<seed>.scores3.json (rulers a, b, b_out, c, d) and <case>_<seed>.scores4.json (rulers e, de, a_prime;
de_vs_d; the direction with rho_a' and with rho_a) and writes, per table of a spec, one Markdown row per case:
"| label | n_t (n_2se) | ..." where n_t counts the cells whose ruler AGREES at the t quantile and n_2se at 2 SE.
A column "de<d" counts the cells where (de)'s |d| is below (d)'s (beside, a reading row); columns "dir:a'" and
"dir:a" give the direction's words as LESS/MORE/NOT SEEN counts. With --check DRAFT, every row must stand word for
word in the draft (exit 1 otherwise).

  python notes/ohm_ruler4_2026-11-26/tables4.py ROOT notes/ohm_ruler4_2026-11-26/tables4_spec.json [--check DRAFT]

The spec (JSON): a list of tables {"name", "folder" (under ROOT), "t" ("3", "4" or "ge3"), "rulers": [keys],
"labels": {key: column label}, "rows": [[row label, case name], ...]}. Keys: a, b, b_out, c, d (score3), e, de,
a_prime (score4), de_lt_d, dir_a_prime, dir_a.
"""
import argparse
import glob
import json
import os
import sys
from collections import defaultdict

S3 = ("a", "b", "b_out", "c", "d")
S4 = ("e", "de", "a_prime")
SHORT = {"WINDOW SHRINKS LESS": "L", "WINDOW SHRINKS MORE": "M", "NOT SEEN": "N", "NOT READ": "R", None: "-"}


def _t_ok(k, t_sel):
    t = int(k.split("_t")[1].split("_")[0])
    return (t_sel == "3" and t == 3) or (t_sel == "4" and t == 4) or (t_sel == "ge3" and t >= 3)


def counts(folder, t_sel, rulers):
    out = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    dirs = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    seeds = defaultdict(int)
    for p in sorted(glob.glob(os.path.join(folder, "*_*.scores4.json"))):
        stem = os.path.basename(p).split(".scores4")[0]
        case = stem.rsplit("_", 1)[0]
        seeds[case] += 1
        s4 = json.load(open(p, encoding="utf-8"))
        s3 = json.load(open(p.replace(".scores4.", ".scores3."), encoding="utf-8"))
        for k, c3 in s3["cells"].items():
            if not _t_ok(k, t_sel):
                continue
            c4 = s4["cells"][k]
            for r in rulers:
                if r in S3:
                    w = c3["rulers"][r]["words"]
                elif r in S4:
                    w = c4[r]["words"]
                elif r == "de_lt_d":
                    out[case][r][0] += c4.get("de_vs_d") == "SMALLER"
                    continue
                elif r in ("dir_a_prime", "dir_a"):
                    v = s4["direction"].get(k, {})
                    v = v.get("judged_a_prime" if r == "dir_a_prime" else "beside_a") or {}
                    dirs[case][r][SHORT[v.get("word")]] += 1
                    continue
                else:
                    raise SystemExit(f"STOP: unknown key {r}")
                out[case][r][0] += w["t"] == "AGREES"
                out[case][r][1] += w["2se"] == "AGREES"
    return out, dirs, seeds


def table(root, spec):
    c, dirs, seeds = counts(os.path.join(root, spec["folder"]), spec["t"], spec["rulers"])
    head = "| case | " + " | ".join(spec["labels"].get(r, f"({r})") for r in spec["rulers"]) + " |"
    rows = []
    for label, case in spec["rows"]:
        if case not in seeds:
            raise SystemExit(f"STOP: no scores for case {case} in {spec['folder']}")
        cells = []
        for r in spec["rulers"]:
            if r == "de_lt_d":
                cells.append(str(c[case][r][0]))
            elif r.startswith("dir_"):
                d = dirs[case][r]
                cells.append(" ".join(f"{k}{d[k]}" for k in ("L", "M", "N", "R") if d.get(k)))
            else:
                cells.append(f"{c[case][r][0]} ({c[case][r][1]})")
        rows.append(f"| {label} | " + " | ".join(cells) + " |")
    return head, rows, seeds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("spec")
    ap.add_argument("--check")
    a = ap.parse_args()
    specs = json.load(open(a.spec, encoding="utf-8"))
    draft = open(a.check, encoding="utf-8").read() if a.check else None
    bad = 0
    for sp in specs:
        head, rows, seeds = table(a.root, sp)
        print(f"## {sp['name']}  (seeds per case: " + ", ".join(f"{k} {v}" for k, v in sorted(seeds.items())) + ")\n")
        print(f"{head}\n|" + "---|" * (len(sp["rulers"]) + 1))
        for r in rows:
            mark = ""
            if draft is not None:
                ok = r in draft
                bad += not ok
                mark = "" if ok else "   <- NOT IN THE DRAFT"
            print(r + mark)
        print()
    if draft is not None:
        print(f"check: {bad} row(s) not in the draft")
        sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
