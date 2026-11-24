"""A lint for the way values beside the verdicts are written (workplace VS, 2026-11-24; home instruction "研究ノートの
道具の直し", 2). Warnings only: the exit code is always 0, nothing is written, and nothing is corrected (home Claude
corrects by hand, against notes/style_beside.md).

Two kinds of line are listed, with the file, the line number and the reason:
  word     a word or phrase that notes/style_beside.md says not to use ("Words not used": at most, at least, only,
           merely, just, far longer, much smaller, negligible, a few thousandths, lies elsewhere, is caused by, is due
           to), plus "nothing" (home instruction); the list is read from style_beside.md's quoted words when the note
           is there, and EXTRA_WORDS below are always added (one place to change). "only", "just" and "nothing" are
           listed only when the same sentence holds a number or a comparison (than, against, more, less, larger,
           smaller, faster, slower, cost, gain); --all lists them everywhere (home instruction, 2026-11-24 tools2)
  no SE    a sentence about a value beside (it holds the word "beside", or it stands under a heading or a paragraph
           title that holds "beside") with a decimal number and neither "2 SE" nor "SE". The unit is a sentence of a
           paragraph (tex, README) or one whole bullet (README), so a "2 SE" on the next line of the same sentence
           counts; a table row and a heading are their own units. Fenced code and tex comments are not read.

Read by default: every results/*/README.md. Further files (e.g. notes/paper11/paper11.tex) are given as arguments.
A word inside an inline code span (`...`) is not counted.

  python tools/lint_beside.py [FILE ...] [--results RESULTS_DIR] [--style STYLE.md] [--no-results] [--max N] [--all]
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
SE = re.compile(r"\bSE(?![A-Za-z])")      # "2 SE", "SE_d", "SE 0.008"; not a word such as "SEED"
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


GUARDED = ("only", "just", "nothing")     # home instruction 2026-11-24 (tools2): listed only beside a number or a
COMPARE = re.compile(r"\b(than|against|more|less|larger|smaller|faster|slower|costs?|gains?)\b", re.I)  # comparison
DIGIT = re.compile(r"\d")
BULLET = re.compile(r"^\s*([-*+]|\d+[.)])\s")
TEX_PARA = re.compile(r"^\s*\\paragraph\*?\{([^}]*)\}")
ABBREV = re.compile(r"(\b(e\.g|i\.e|vs|cf|etc|Fig|Figs|Eq|Eqs|Ref|Sec|No|approx)\.|\b[A-Z]\.)$")
BOUNDARY = re.compile(r"(?:(?<=[.!?])|(?<=[.!?][)\]}\"']))\s+(?=\S)")


def sentences(s):
    """[(start, end)] of the sentences of one block's text: split after . ! ? (or one closing bracket or quote after
    them) and white space, never after an abbreviation such as e.g. or an initial; a decimal point has no space after
    it, so 0.579 is never split."""
    out, a = [], 0
    for m in BOUNDARY.finditer(s):
        if ABBREV.search(s[a:m.start()]):
            continue
        out.append((a, m.start()))
        a = m.end()
    if s[a:].strip():
        out.append((a, len(s)))
    return out


def blocks(text, tex):
    """The file cut into blocks: [(kind, first line index, text, beside context)], kind one of heading, table,
    bullet, para. A bullet runs to its last continuation line, a paragraph to the next blank line, heading, bullet or
    table row; fenced code (```) and tex comment lines are left out. The beside context is set by the last heading or
    paragraph title (it holds "beside") and kept until the next one."""
    out, cur, beside_block, fence = [], None, False, False
    def close():
        nonlocal cur
        if cur:
            out.append((cur[0], cur[1], "\n".join(cur[2]), cur[3]))
        cur = None
    for i, line in enumerate(text.splitlines()):
        st = line.strip()
        if not tex and st.startswith("```"):
            close()
            fence = not fence
            continue
        if fence or (tex and st.startswith("%")):
            continue
        if not st:
            close()
            continue
        pm = TEX_PARA.match(line) if tex else None
        if pm:
            close()
            beside_block = "beside" in pm.group(1).lower()
            cur = ["para", i, [line], beside_block]
            continue
        if HEADING.match(line):
            close()
            beside_block = "beside" in line.lower()
            out.append(("heading", i, line, beside_block))
            continue
        if not tex and st.startswith("|"):
            close()
            out.append(("table", i, line, beside_block))
            continue
        if not tex and BULLET.match(line):
            close()
            cur = ["bullet", i, [line], beside_block]
            continue
        if cur is None:
            cur = ["para", i, [line], beside_block]
        else:
            cur[2].append(line)
    close()
    return out


def lint_text(text, pats, tex=False, all_words=False):
    """[(line number, reason, line)] for one file's text.

    The SE check reads a sentence of a paragraph (tex, README), or one whole bullet, table row or heading (README):
    a unit about a value beside (it holds "beside", or stands under a heading or paragraph title that holds it) with a
    decimal number and neither "2 SE" nor "SE" is listed once, at the line of its first decimal. The word check reads
    sentences; "only", "just" and "nothing" are listed only when their sentence also holds a number or a comparison
    (than, against, more, less, larger, smaller, faster, slower, cost, gain), unless all_words."""
    lines = text.splitlines()
    out = []
    for kind, i0, body, beside_block in blocks(text, tex):
        bare = CODE.sub(lambda m: " " * len(m.group(0)), body)     # same length: offsets still map to lines
        line_of = lambda off: i0 + bare.count("\n", 0, off)
        sents = sentences(bare) if kind in ("para", "bullet") else [(0, len(bare))]
        se_units = sents if kind == "para" else [(0, len(bare))]
        for a, b in sents:
            s = bare[a:b]
            for w, p in pats:
                for m in p.finditer(s):
                    if (w.lower() in GUARDED and not all_words and not DIGIT.search(s) and not COMPARE.search(s)):
                        continue
                    n = line_of(a + m.start())
                    out.append((n + 1, f'word "{w}"', lines[n].strip()))
                    break
        for a, b in se_units:
            s = bare[a:b]
            about_beside = beside_block or "beside" in s.lower()
            d = DEC.search(s)
            if about_beside and d and not SE.search(s):
                n = line_of(a + d.start())
                out.append((n + 1, "no SE: a value beside without 2 SE", lines[n].strip()))
    out.sort(key=lambda r: r[0])
    return out


def selftest():
    pats = word_patterns(FALLBACK_WORDS + EXTRA_WORDS)
    sample = "\n".join([
        "## Results",
        "- the difference is at most +0.01 here",                     # 2 word
        "- Beside: +0.004 (2 SE 0.006): not separated from 0.",         # fine
        "- beside, never judged: the share 0.845 on the other phases",  # 4 no SE
        "## Beside",
        "- F16 reads 0.751 tonight",                                     # 6 no SE (under a Beside heading)
        "## Reading",
        "- the loss belongs to the first item; `only` in code is not a word",  # fine
        "- nothing is compared across nights",                          # fine: no number, no comparison
        "- the gain is only seen on two phases",                        # 10 word (a comparison)
        "",
        "Beside, the loss grew (0.127 then 0.185, acceleration +0.058,",  # fine: 2 SE on the next line of the sentence
        "2 SE 0.028). It was only read once.",                          # fine: no number in that sentence
    ])
    got = [(n, "word" if r.startswith("word") else "no SE") for n, r, _ in lint_text(sample, pats)]
    want = [(2, "word"), (4, "no SE"), (6, "no SE"), (10, "word")]
    got_all = [(n, "word" if r.startswith("word") else "no SE") for n, r, _ in lint_text(sample, pats, all_words=True)]
    want_all = sorted(want + [(9, "word"), (13, "word")])
    ok = got == want and got_all == want_all
    print(f"lint_beside selftest: {'PASS' if ok else 'FAIL'} got {got}, with --all {got_all}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--results", default="results")
    ap.add_argument("--style", default=os.path.join("notes", "style_beside.md"))
    ap.add_argument("--no-results", action="store_true")
    ap.add_argument("--max", type=int, default=0, help="print at most N lines (0: all); the counts are always full")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--all", action="store_true", help='list "only", "just" and "nothing" everywhere (no number or '
                    "comparison needed in the sentence)")
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
        for n, reason, line in lint_text(open(f, encoding="utf-8", errors="replace").read(), pats,
                                         tex=f.endswith(".tex"), all_words=a.all):
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
