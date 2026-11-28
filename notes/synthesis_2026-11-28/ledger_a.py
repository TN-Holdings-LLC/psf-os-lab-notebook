"""Analysis A, first part: the ledger of declared predictions on the nights of 2026-11-16 to 2026-11-27, read from the
"Against the declaration" section of every results/*/README.md (table rows and bold bullets). Reads only.

usage: python notes/synthesis_2026-11-28/ledger_a.py [--json OUT] [--show]
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VERDICT = re.compile(r"\b(held|failed|not read|NOT READ|HELD|FAILED)\b")
ROW = re.compile(r"^\|\s*([A-Z][A-Za-z0-9]*-[0-9A-Za-z]+)\b(.*?)\|(.*)\|\s*([^|]*)\|\s*$")
BUL = re.compile(r"^- \*\*([A-Z][A-Za-z0-9]*-[0-9A-Za-z]+)\b(.*)")


def section(text):
    """The text under '## Against the declaration' up to the next '## ' heading."""
    m = re.search(r"^##+ Against the declaration.*?$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def verdict_of(s):
    m = VERDICT.search(s)
    return m.group(1).lower() if m else None


TOKEN = r"(?:[A-Z][A-Za-z0-9]*-[0-9A-Za-z]+ )?(?:held|failed|not read)(?: \([^)]*\))?"
CELL = re.compile(rf"^{TOKEN}(?:, {TOKEN})*$")
TOK = re.compile(r"(?:([A-Z][A-Za-z0-9]*-[0-9A-Za-z]+) )?(held|failed|not read)")


def read(path):
    """Every table row whose last cell is a verdict list, and every bold bullet whose head ends in a verdict."""
    text = open(path, encoding="utf-8").read()
    rows = []
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith("|") and ln.rstrip().endswith("|"):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            last = cells[-1] if cells else ""
            if last and CELL.match(last):
                first = cells[0]
                for pid, v in TOK.findall(last):
                    rows.append({"id": pid or first.split(" ")[0].rstrip("."), "text": first, "verdict": v,
                                 "numbers": " | ".join(cells[1:-1])[:200]})
            continue
        m = BUL.match(ln)
        if m:
            unit = ln
            j = i + 1
            while j < len(lines) and lines[j].startswith("  "):
                unit += " " + lines[j].strip()
                j += 1
            head = unit.split("**")[1] if unit.count("**") >= 2 else ""
            v = verdict_of(head)
            if v:
                rows.append({"id": m.group(1), "text": head.strip(), "verdict": v, "numbers": unit[len(head) + 6:][:200]})
    return rows


def main():
    out = None
    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
    ledger = []
    for path in sorted(glob.glob(os.path.join(ROOT, "results", "*", "README.md"))):
        night = os.path.basename(os.path.dirname(path))
        m = re.search(r"(2026-11-(\d\d))", night)
        if not m or not ("2026-11-16" <= m.group(1) <= "2026-11-27"):
            continue
        for r in read(path):
            r["night"] = night
            r["date"] = m.group(1)
            ledger.append(r)
    n = {}
    for r in ledger:
        n[r["verdict"]] = n.get(r["verdict"], 0) + 1
    print(f"{len(ledger)} rows; " + ", ".join(f"{k}: {v}" for k, v in sorted(n.items(), key=lambda x: str(x[0]))))
    if "--show" in sys.argv:
        for r in ledger:
            print(f"{r['date']} {r['night'][:34]:34s} {r['id']:10s} {str(r['verdict']):9s} {r['text'][:70]}")
    if out:
        json.dump(ledger, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()


# ---- kinds (rules written 2026-11-28 before the counts below were read; first match wins) ----
# Rows whose README text is only a test label (ff-night T*, N*) take the declaration's words
# (prereg/ff_night_2026-11-17.md, ff_night_2026-11-17_T4.md, ff_night2_2026-11-17.md).
DECLARED_WORDS = {
    "T1-1": "CLOSER WITH CONTROL", "T1-2": "CLOSER WITH CONTROL",
    "T2-1": "BEYOND THE CORRECTION CEILING", "T2-2": "COMPOUNDS",
    "T3-1": "BEYOND THE CEILING", "T3-2": "GROWS", "T3-3": "BEYOND THE CEILING",
    "T4-1": "BEYOND THE CORRECTION CEILING", "T4-2": "COMPOUNDS", "T4-3": "EARLY KEEPS MORE",
    "N1-1": "CLOSER WITH CONTROL", "N1-2": "CLOSER WITH CONTROL",
    "N2-1": "BEYOND", "N2-2": "COMPOUNDS", "N3-1": "BEYOND THE CEILING",
}
KINDS = [
    ("per-qubit record", r"physical \d"),
    ("cost", r"charged"),
    ("loop behaviour", r"rule changes|prescription picked"),
    ("timing", r"RESOLVED|IN PARALLEL|WAIT FOR EACH OTHER"),
    ("null (no difference)", r"SAME WITHIN ERROR|not PACKING|NOT BEYOND|overshoot|at or under|never fire"),
    ("trend over size", r"COMPOUNDS|GROWS"),
    ("beyond a bound", r"BEYOND|CLOSER|ABOVE THE BOUND|READS"),
    ("direction between arms", r"KEEPS MORE|KEEPS LESS|gain|D_\w+|below|loses|loss remains|HELPS"),
]


def kind_of(row):
    text = DECLARED_WORDS.get(row["id"], row["text"]) if row["night"].startswith("ff-night") else row["text"]
    for name, pat in KINDS:
        if re.search(pat, text):
            return name
    return "other"


def summary(ledger):
    """Counts by period (paper 10's nights 11-16..11-19, after them 11-20..11-27) and by kind."""
    for r in ledger:
        r["kind"] = kind_of(r)
        r["period"] = "paper 10 nights (11-16..11-19)" if r["date"] <= "2026-11-19" else "after (11-20..11-27)"
    tab = {}
    for r in ledger:
        for key in ((r["period"], None), (None, r["kind"]), (r["period"], r["kind"])):
            tab.setdefault(key, {"held": 0, "failed": 0, "not read": 0})[r["verdict"]] += 1
    return tab


if __name__ == "__main__" and "--summary" in sys.argv:
    led = []
    for path in sorted(glob.glob(os.path.join(ROOT, "results", "*", "README.md"))):
        night = os.path.basename(os.path.dirname(path))
        m = re.search(r"(2026-11-(\d\d))", night)
        if m and "2026-11-16" <= m.group(1) <= "2026-11-27":
            for r in read(path):
                r["night"], r["date"] = night, m.group(1)
                led.append(r)
    tab = summary(led)
    print("| period | kind | declared | held | failed | not read |")
    print("|---|---|---|---|---|---|")
    for key in sorted(tab, key=lambda k: (str(k[0]), str(k[1]))):
        c = tab[key]
        print(f"| {key[0] or 'all'} | {key[1] or 'all'} | {sum(c.values())} | {c['held']} | {c['failed']} | {c['not read']} |")
    others = [r for r in led if r["kind"] == "other"]
    print("other:", [(r["night"], r["id"], r["text"]) for r in others])
    json.dump(led, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ledger_a.json"), "w"), indent=1)
