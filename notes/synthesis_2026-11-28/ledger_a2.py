"""Analysis A, second part: the ledger of predictions declared up to 2026-11-15 (papers 1 to 9's period).

The rows in ledger_a2.json were read by hand (home VS, 2026-11-28) from the declarations and the records: psf-zero's
preregistrations (full history), the notebook's prereg/ (2026-10-08 to 11-15) and the results' READMEs, one row per
declared prediction, the verdict copied as the record states it (held / failed / not read), `unclear` with a reason
where the record does not let a verdict be read. Nothing is re-judged.

This tool reads only. It
- checks that every cited place exists (declared_in, verdict_source: a notebook path:line, or psf-zero's
  path:line or commit:path:line in the full-history copy given by --psf-zero);
- sets beside each row the kind ledger_a.py's rules give its words (KINDS, first match wins), against the hand
  kind (which adds "declared model": a declared noise model, expected number or volume);
- prints the counts by paper, by period and by kind.

usage: python notes/synthesis_2026-11-28/ledger_a2.py [--psf-zero PATH] [--json OUT]
Author: The Architect <love.os.architect@proton.me>
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from ledger_a import KINDS  # noqa: E402

VERDICTS = ("held", "failed", "not read", "unclear")


def regex_kind(text):
    for name, pat in KINDS:
        if re.search(pat, text):
            return name
    return "other"


def line_exists(ref, psf_zero):
    """'path:line' in the notebook, or in psf-zero ('psf-zero:path:line', 'repo:path:line', 'commit:path:line')."""
    if not ref:
        return False
    ref = ref.strip()
    m = re.match(r"^(?:(psf-zero|repo|[0-9a-f]{7,40}):)?(\S+?):(\d+)", ref)  # a note after the line number is allowed
    if not m:
        return False
    where, path, ln = m.group(1), m.group(2).strip(), int(m.group(3))
    if where is None and os.path.exists(os.path.join(ROOT, path)):
        txt = open(os.path.join(ROOT, path), encoding="utf-8", errors="replace").read()
    elif psf_zero and where in (None, "psf-zero", "repo") and os.path.exists(os.path.join(psf_zero, path)):
        txt = open(os.path.join(psf_zero, path), encoding="utf-8", errors="replace").read()
    elif psf_zero and where and re.fullmatch(r"[0-9a-f]{7,40}", where):
        r = subprocess.run(["git", "-C", psf_zero, "show", f"{where}:{path}"], capture_output=True, text=True)
        if r.returncode != 0:
            return False
        txt = r.stdout
    else:
        return False
    return 1 <= ln <= len(txt.splitlines())


def table(rows, key):
    tab = {}
    for r in rows:
        tab.setdefault(key(r), {v: 0 for v in VERDICTS})[r["verdict"]] += 1
    return tab


def main():
    psf_zero = sys.argv[sys.argv.index("--psf-zero") + 1] if "--psf-zero" in sys.argv else None
    rows = json.load(open(os.path.join(HERE, "ledger_a2.json")))
    bad_verdict = [r for r in rows if r["verdict"] not in VERDICTS]
    no_reason = [r for r in rows if r["verdict"] in ("unclear", "not read") and not r.get("reason")]
    cites = {"declared_in": 0, "verdict_source": 0}
    missing = []
    for r in rows:
        for k in cites:
            refs = [x for x in re.split(r";\s*|,\s+(?=\S+:\d)", str(r.get(k) or "")) if x.strip()]
            ok = any(line_exists(x, psf_zero) for x in refs)
            cites[k] += ok
            if not ok:
                missing.append((r["date"], r.get("id"), k, r.get(k)))
    for r in rows:
        r["kind_by_ledger_a_rules"] = regex_kind(r["prediction"])
    agree = sum(r["kind"] == r["kind_by_ledger_a_rules"] for r in rows)
    print(f"{len(rows)} rows; " + ", ".join(f"{v} {sum(r['verdict'] == v for r in rows)}" for v in VERDICTS))
    print(f"cited places found: declared_in {cites['declared_in']} / {len(rows)}, verdict_source "
          f"{cites['verdict_source']} / {len(rows)}; bad verdict words {len(bad_verdict)}; unclear or not read "
          f"without a reason {len(no_reason)}")
    print(f"hand kind equal to ledger_a's rules on the prediction's words: {agree} / {len(rows)}")
    out = {"rows": len(rows), "cites_found": cites, "missing_cites": missing,
           "kind_agreement_with_ledger_a_rules": agree}
    for name, key in (("paper", lambda r: str(r["paper"])), ("kind", lambda r: r["kind"]),
                      ("period", lambda r: "up to 10-31" if r["date"] <= "2026-10-31" else "11-01 to 11-15"),
                      ("source", lambda r: r.get("part", ""))):
        tab = table(rows, key)
        out[f"by_{name}"] = tab
        print(f"\n| {name} | declared | held | failed | not read | unclear |\n|---|---|---|---|---|---|")
        for k in sorted(tab, key=lambda x: (len(x), x)):
            c = tab[k]
            print(f"| {k} | {sum(c.values())} | {c['held']} | {c['failed']} | {c['not read']} | {c['unclear']} |")
    if missing:
        print("\ncited places not found:")
        for m in missing:
            print("  ", m)
    if "--json" in sys.argv:
        json.dump(out, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1)


if __name__ == "__main__":
    main()
