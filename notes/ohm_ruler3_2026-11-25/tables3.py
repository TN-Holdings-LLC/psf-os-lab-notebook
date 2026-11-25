"""The draft's dry-run tables written from the scores themselves, never copied by hand (workplace Claude, 2026-11-25).

Reads score3's <case>_<seed>.scores3.json files and writes, per table of a spec, one Markdown row per case:
"| label | n_t (n_2se) | ..." where n_t is the number of cells whose ruler AGREES at the t quantile and n_2se at 2 SE.
With --check DRAFT, every row it writes must stand word for word in the draft (exit 1 otherwise), so a number typed
into the draft cannot drift from the scores.

  python notes/ohm_ruler3_2026-11-25/tables3.py ROOT notes/ohm_ruler3_2026-11-25/tables3_spec.json [--check DRAFT]

The spec (JSON): a list of tables {"name", "folder" (under ROOT), "t" ("3" or "ge3"), "rulers": [score3 keys],
"labels": {key: column label}, "rows": [[row label, case name], ...]}.
"""
import argparse
import glob
import json
import os
import sys
from collections import defaultdict


def counts(folder, t_sel, rulers):
    out = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for p in sorted(glob.glob(os.path.join(folder, "*_*.scores3.json"))):
        case = os.path.basename(p).split(".scores3")[0].rsplit("_", 1)[0]
        for k, c in json.load(open(p, encoding="utf-8"))["cells"].items():
            t = int(k.split("_t")[1].split("_")[0])
            if (t_sel == "3" and t != 3) or (t_sel == "ge3" and t < 3):
                continue
            for r in rulers:
                w = c["rulers"][r]["words"]
                out[case][r][0] += w["t"] == "AGREES"
                out[case][r][1] += w["2se"] == "AGREES"
    return out


def table(root, spec):
    c = counts(os.path.join(root, spec["folder"]), spec["t"], spec["rulers"])
    head = "| case | " + " | ".join(spec["labels"].get(r, f"({r})") for r in spec["rulers"]) + " |"
    rows = []
    for label, case in spec["rows"]:
        if case not in c:
            raise SystemExit(f"STOP: no scores for case {case} in {spec['folder']}")
        rows.append(f"| {label} | " + " | ".join(f"{c[case][r][0]} ({c[case][r][1]})" for r in spec["rulers"]) + " |")
    return head, rows


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
        head, rows = table(a.root, sp)
        print(f"## {sp['name']}\n\n{head}\n|" + "---|" * (len(sp["rulers"]) + 1))
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
