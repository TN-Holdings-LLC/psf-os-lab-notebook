"""Check every row of notes/paper12/numbers.md: its literal stands word for word in its source at its ref (workplace
Claude, 2026-11-27; author The Architect). Rows with ref '-' or 'PENDING COMMIT' are listed as not checked.

  python notes/paper12/numbers_check.py [--calib-ref REF]      (REF default: calib-compare2-2026-11-27)
Exit 1 if any checked row's literal is missing.
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))


def cells(line):
    out, cur, esc = [], "", False
    for ch in line.strip()[1:-1]:
        if esc:
            cur += ch
            esc = False
        elif ch == "\\":
            esc = True
        elif ch == "|":
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    out.append(cur.strip())
    return out


def text_at(ref, path):
    if ref == "HEAD":
        return open(os.path.join(ROOT, path), encoding="utf-8").read()
    return subprocess.run(["git", "-C", ROOT, "show", f"{ref}:{path}"], capture_output=True, text=True,
                          check=True).stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--calib-ref", default="calib-compare2-2026-11-27")
    a = ap.parse_args()
    rows = [l for l in open(os.path.join(HERE, "numbers.md"), encoding="utf-8") if l.startswith("| ")][1:]
    bad = skipped = ok = 0
    for l in rows:
        c = cells(l)
        rid, ref, src, lit = c[0], c[3], c[4], c[5]
        if ref in ("-", "PENDING COMMIT") or lit == "-":
            skipped += 1
            print(f"not checked  {rid} ({ref})")
            continue
        r = a.calib_ref if ref == "calib" else ref
        try:
            found = lit.replace("\\|", "|") in text_at(r, src)
        except subprocess.CalledProcessError:
            found = False
        ok += found
        bad += not found
        print(("ok           " if found else "MISSING      ") + rid)
    print(f"numbers_check: {ok} ok, {bad} missing, {skipped} not checked")
    if ok + bad == 0:
        sys.exit("FAIL: 0 rows checked")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
