"""A lint for the way values beside the verdicts are written (workplace VS, 2026-11-24; home instruction "研究ノートの
道具の直し", 2). Warnings only: the exit code is always 0, nothing is written, and nothing is corrected (home Claude
corrects by hand, against notes/style_beside.md).

Two kinds of line are listed, with the file, the line number and the reason:
  word     a word or phrase that notes/style_beside.md says not to use ("Words not used": at most, at least, only,
           merely, just, far longer, much smaller, negligible, a few thousandths, lies elsewhere, is caused by, is due
           to), plus "nothing" (home instruction); the list is read from style_beside.md's quoted words when the note
           is there, and EXTRA_WORDS below are always added (one place to change)
  no SE    a line about a value beside (it holds the word "beside", or it stands under a heading or a paragraph
           title that holds "beside") with a decimal number and neither "2 SE" nor "SE"

Read by default: every results/*/README.md. Further files (e.g. notes/paper11/paper11.tex) are given as arguments.
A word inside an inline code span (`...`) is not counted.

  python tools/lint_beside.py [FILE ...] [--results RESULTS_DIR] [--style STYLE.md] [--no-results] [--max N]
  python tools/lint_beside.py --selftest
"""
import argparse
import glob
import os
import re
import sys

EXTRA_WORDS = ["nothing"]                  # home instruction, 2026-11-24 (not in style_beside.md's list)
FALLBACK_WORDS = ["at most", "at least", "only", "merely", "just", "far longer", "much smaller", "negligible",
                  "a few thousandths", "lies elsewhere", "is caused by", "is due to"]
DEC = re.compile(r"(?<![\w.])[+\-−]?\d+\.\d+")
SE = re.compile(r"\bSE\b")
HEADING = re.compile(r"^\s*(#{1,6}\s|\\(sub)*section\*?\{|\\paragraph\{|\*\*[^*]+\*\*\s*$)")
CODE = re.compile(r"`[^`]*`")


def style_words(path):
    """The quoted words of the 'Words not used' section of style_beside.md (each bullet's "..." items)."""
    if not path or not os.path.exists(path):
        return list(FALLBACK_WORDS)
    text = open(path, encoding="utf-8", errors="replace").read()
    m = re.search(r"##\s*Words not used(.*?)(\n##\s|\Z)", text, re.S)
    if not m:
        return list(FALLBACK_WORDS)
    words = []
    for line in m.group(1).splitlines():
        if not line.lstrip().startswith("-"):
            continue
        head = line.split(":", 1)[0]                    # the words come before the bullet's colon
        words += [w.strip() for w in re.findall(r'"([^"]+)"', head)]
    words = [re.sub(r"\s*\(.*?\)\s*$", "", w) for w in words]   # "a few thousandths" (as a bound) -> the words
    return sorted(set(w for w in words if w)) or list(FALLBACK_WORDS)


def word_patterns(words):
    return [(w, re.compile(r"(?<![\w-])" + r"\s+".join(map(re.escape, w.split())) + r"(?![\w-])", re.I)) for w in words]


def lint_text(text, pats):
    """[(line number, reason, line)] for one file's text."""
    out, beside_block = [], False
    for i, line in enumerate(text.splitlines(), 1):
        bare = CODE.sub("", line)
        if HEADING.match(line):
            beside_block = "beside" in line.lower()
        elif not line.strip():
            pass
        for w, p in pats:
            if p.search(bare):
                out.append((i, f'word "{w}"', line.strip()))
        about_beside = "beside" in bare.lower() or beside_block or re.match(r"^\s*[-*]?\s*\**beside", bare, re.I)
        if about_beside and DEC.search(bare) and not SE.search(bare):
            out.append((i, "no SE: a value beside without 2 SE", line.strip()))
    return out


def selftest():
    pats = word_patterns(FALLBACK_WORDS + EXTRA_WORDS)
    sample = "\n".join([
        "## Results",
        "the difference is at most +0.01 here",                       # word
        "Beside: +0.004 (2 SE 0.006): not separated from 0.",           # fine
        "beside, never judged: the share 0.845 on the other phases",    # no SE
        "## Beside",
        "- F16 reads 0.751 tonight",                                     # no SE (under a Beside heading)
        "## Reading",
        "the loss belongs to the first item; `only` in code is not a word",  # fine
        "nothing is compared across nights",                            # word
    ])
    got = [(n, "word" if r.startswith("word") else "no SE") for n, r, _ in lint_text(sample, pats)]
    want = [(2, "word"), (4, "no SE"), (6, "no SE"), (9, "word")]
    ok = got == want
    print(f"lint_beside selftest: {'PASS' if ok else 'FAIL'} got {got}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--results", default="results")
    ap.add_argument("--style", default=os.path.join("notes", "style_beside.md"))
    ap.add_argument("--no-results", action="store_true")
    ap.add_argument("--max", type=int, default=0, help="print at most N lines (0: all); the counts are always full")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    try:                                       # README lines hold µ, −, ≥ ...: never stop on a console's code page
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    if a.selftest:
        selftest()
        return 0
    words = sorted(set(style_words(a.style) + EXTRA_WORDS))
    pats = word_patterns(words)
    files = [] if a.no_results else sorted(glob.glob(os.path.join(a.results, "*", "README.md")))
    files += a.files
    total, by_reason, by_file, shown = 0, {}, {}, 0
    for f in files:
        if not os.path.exists(f):
            print(f"lint_beside: not found: {f}", file=sys.stderr)
            continue
        for n, reason, line in lint_text(open(f, encoding="utf-8", errors="replace").read(), pats):
            total += 1
            key = reason.split(":")[0]
            by_reason[key] = by_reason.get(key, 0) + 1
            by_file[f] = by_file.get(f, 0) + 1
            if not a.max or shown < a.max:
                print(f"{f}:{n}: {reason}: {line[:150]}")
                shown += 1
    print(f"lint_beside: {len(files)} files read, {total} lines listed ({len(by_file)} files with any); by reason "
          + ", ".join(f"{k} {v}" for k, v in sorted(by_reason.items(), key=lambda kv: -kv[1]))
          + f"; words from {'notes/style_beside.md + ' if os.path.exists(a.style) else 'the fallback list + '}"
          + ", ".join(EXTRA_WORDS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
