"""Checks of a night's record and tool against its declaration (workplace VS, 2026-11-25; home instruction "道具の直し、
その 3", 1 and 2). Author The Architect. Read only: nothing is written and nothing is corrected.

  beside   every item of the declaration's "Beside, never judged" list has a line in the night's README.
           Each item's head (its first words, before " of ", a comma, a bracket, a colon or a semicolon, without "the")
           is looked for in the README, case and spacing aside. An item that starts "with X," is conditional on X: it
           is checked only when X is one of the night's forms (--forms, or the forms in --build build.json).
           A list written as "- name: description" on every item (from the 11-25 drafts) is read strictly: each name
           must stand in the README as written (case and spacing aside); no head guessing, no word match.
  tables   every row of the declaration's reading tables (the markdown tables after "Table 1", "Table A", ...) against
           the tool's strings (dicts keyed by the row's words, e.g. READ_UNIFORM_A, read from the tool's source
           without importing it). A row is SAME (equal text), PREFIX (the tool's text is the declaration's text up to
           a colon: the tool names the row, the declaration adds its reading of the kind of shrink) or DIFFERENT.
           A table of three columns is keyed by its first two cells; a wider one (e.g. "| ruler | AGREES | DIFFERS |
           NOT READ |") by (first cell, column word), a "-" cell being no row. A cell is split only at a "|" with white
           space on both sides ("|0>" stays in its cell), and a key "(a)" in the declaration matches "a" in the tool.

  python tools/declaration_check.py beside PREREG.md README.md [--forms L F | --build build.json]
  python tools/declaration_check.py tables PREREG.md TOOL.py NAME [NAME ...]
Exit code: 0 when every item is found / every row is SAME or PREFIX; 1 otherwise; 2 when beside reads no item at all
(2026-11-27: a heading "## Beside, never judged" without a colon is read too, its top-level bullets up to the next
heading, and "X's beside values (a, b, c)" stands for a, b and c).
"""
import argparse
import ast
import json
import re
import sys

BESIDE_HEAD = re.compile(r"^\s*(?:[-*]\s*)?(?:\*\*)?Beside, never judged[^:]*:\s*(.*)$", re.I)
BULLET = re.compile(r"^\s*[-*]\s+(.*)$")
# 2026-11-27 (tools6): the heading form "## Beside, never judged" (no colon), read up to the next heading
BESIDE_HEADING = re.compile(r"^\s*#{1,6}\s+Beside, never judged[^:]*:?\s*$", re.I)
VALUES_LIST = re.compile(r"beside values\s*\((.*)\)", re.I)


def _norm(s):
    return re.sub(r"\s+", " ", s.replace("`", "").replace("*", "")).strip().lower()


NAMED = re.compile(r"^`?(?:\*\*)?([^:`*]{1,60}?)(?:\*\*)?`?:\s+\S")


def beside_items(prereg):
    """The items of every "Beside, never judged" list: [(line number, text)] (see beside_lists)."""
    return [it for _, items in beside_lists(prereg) for it in items]


def beside_lists(prereg):
    """Every "Beside, never judged" list: [(line number of its head, [(line number, text)])]. A list is the bullets
    right under the line, or, when the line itself goes on, that text up to the next blank line, split at semicolons
    (else commas)."""
    lines, lists = prereg.splitlines(), []
    for i, ln in enumerate(lines):
        if BESIDE_HEADING.match(ln):
            lists.append((i + 1, _heading_items(lines, i)))
            continue
        m = BESIDE_HEAD.match(ln)
        if not m:
            continue
        indent = len(ln) - len(ln.lstrip())
        if m.group(1).strip():
            j, text = i + 1, m.group(1)
            while j < len(lines) and lines[j].strip() and not BULLET.match(lines[j]):
                text += " " + lines[j].strip()
                j += 1
            parts = text.split(";") if ";" in text else re.split(r",\s+(?![^()]*\))", text)
            lists.append((i + 1, [(i + 1, p.strip().rstrip(".")) for p in parts if p.strip()]))
            continue
        out = []
        j = i + 1
        while j < len(lines):
            b = BULLET.match(lines[j])
            if b and len(lines[j]) - len(lines[j].lstrip()) >= indent:
                text, k = b.group(1), j + 1
                while k < len(lines) and lines[k].strip() and not BULLET.match(lines[k]) and \
                        len(lines[k]) - len(lines[k].lstrip()) > len(lines[j]) - len(lines[j].lstrip()):
                    text += " " + lines[k].strip()
                    k += 1
                out.append((j + 1, text.strip().rstrip(";.")))
                j = k
            else:
                break
        lists.append((i + 1, out))
    return lists


def _heading_items(lines, i):
    """The top-level bullets under a "## Beside, never judged" heading, up to the next heading: deeper bullets and
    indented lines continue the item above. An item "X's beside values (a, b, c) ..." stands for its listed names, one
    item each (the fourth night's last item lists the third night's beside values so)."""
    out, j, top = [], i + 1, None
    while j < len(lines) and not re.match(r"^\s*#{1,6}\s", lines[j]):
        b = BULLET.match(lines[j])
        ind = len(lines[j]) - len(lines[j].lstrip())
        if b and (top is None or ind <= top):
            top = ind if top is None else top
            text, k = b.group(1), j + 1
            while k < len(lines) and lines[k].strip() and not re.match(r"^\s*#{1,6}\s", lines[k]) and                     (len(lines[k]) - len(lines[k].lstrip()) > top):
                text += " " + lines[k].strip()
                k += 1
            text = text.strip().rstrip(";.")
            v = VALUES_LIST.search(text)
            if v:
                names = re.split(r",\s*(?![^()]*\))", v.group(1))
                out += [(j + 1, n.strip()) for n in names if n.strip()]
            else:
                out.append((j + 1, text))
            j = k
        else:
            j += 1
    return out


def head_of(item):
    """(condition or None, head): "with F, the 11-23 twins' word (...)" -> ("F", "11-23 twins' word")."""
    cond = None
    m = re.match(r"with ([A-Za-z0-9]+),\s*(.*)$", item)
    if m:
        cond, item = m.group(1), m.group(2)
    bold = re.match(r"^\*\*(.+?)\*\*", item.strip())
    if bold:                                   # 2026-11-27: "**name**, ..." -> the bold name
        h = bold.group(1).replace("`", "").strip()
        h = re.sub(r"^(the|a|an)\s+", "", h, flags=re.I)
        if "/" in h and "." in h.rsplit("/", 1)[-1]:
            h = h.rsplit("/", 1)[-1]           # a file's path -> its name (results/<night>/qubits.csv -> qubits.csv)
        return cond, h
    item = re.sub(r"^(the|a|an)\s+", "", item.strip(), flags=re.I)
    h = re.split(r"\s+of\s+|\s+per\s+|,|\s+\(|:|;", item, maxsplit=1)[0].strip()
    return cond, h


GENERIC = {"and", "the", "mean", "means", "value", "values", "word", "words", "item", "items", "with", "for"}


def _found(head, readme):
    """"exact" when the head is in the README; "words" when every content word of the head (3 letters or more, not
    a generic word such as "means") stands on one README line; None otherwise."""
    if _norm(head) in _norm(readme):
        return "exact"
    words = [w for w in re.findall(r"[a-z0-9][a-z0-9_'()/-]{2,}", _norm(head)) if w not in GENERIC]
    if words:
        for ln in readme.splitlines():
            n = _norm(ln)
            if all(re.search(r"(?<![a-z0-9])" + re.escape(w), n) for w in words):
                return "words"
    return None


def beside_coverage(prereg, readme, forms=None):
    """[dict(line, item, head, condition, checked, found, form)] for every beside item of the declaration. In a list
    whose every item is "name: description" (form "named") the head is the name and found is "name" when the name
    stands in the README, else None; otherwise (form "free") found is "exact", "words" (see _found) or None."""
    out, text = [], _norm(readme)
    for _, items in beside_lists(prereg):
        named = bool(items) and all(NAMED.match(t) for _, t in items)
        for n, item in items:
            if named:
                h = NAMED.match(item).group(1).strip()
                out.append(dict(line=n, item=item, head=h, condition=None, checked=True,
                                found="name" if _norm(h) in text else None, form="named"))
                continue
            cond, h = head_of(item)
            checked = cond is None or forms is None or cond in forms
            out.append(dict(line=n, item=item, head=h, condition=cond, checked=checked,
                            found=_found(h, readme) if checked else None, form="free"))
    return out


def _cells(row):
    """The cells of a markdown table row, split only at a "|" with white space on both sides (or at the row's ends),
    so a "|0>" inside a cell stays in its cell."""
    inner = re.sub(r"^\s*\|\s?", "", row.rstrip())
    inner = re.sub(r"\s?\|\s*$", "", inner)
    return [c.strip() for c in re.split(r"\s\|\s", " " + inner + " ")]


def _key(k):
    """A row key as the tool writes it: a cell "(a)" or "(b_out)" matches the tool's "a" or "b_out"."""
    return tuple(re.sub(r"^\((.*)\)$", lambda m: m.group(1), x.strip()) for x in k)


def reading_tables(prereg):
    """{table label: {key: reading}} for the markdown tables that follow a "Table N" / "Table A" line (the label an int
    when it is a number). Three columns: key (cell 1, cell 2). Wider: key (cell 1, column word) for every cell that is
    not "-"."""
    lines, out, cur, header = prereg.splitlines(), {}, None, None
    for ln in lines:
        m = re.match(r"^\s*Table ([0-9]+|[A-Z])\b", ln)
        if m:
            cur = int(m.group(1)) if m.group(1).isdigit() else m.group(1)
            out[cur], header = {}, None
            continue
        if cur is None:
            continue
        if ln.startswith("|"):
            cells = _cells(ln)
            if set("".join(cells)) <= set("-:| "):
                continue
            if header is None:
                header = cells
                continue
            if len(header) == 3:
                out[cur][(cells[0], cells[1])] = cells[2]
            else:
                for word, text in zip(header[1:], cells[1:]):
                    if text != "-":
                        out[cur][(cells[0], word)] = text
        elif out[cur]:
            cur = None
    return out


def tool_tables(src, names):
    """{name: dict} for the module-level dict assignments of the tool's source (evaluated alone, nothing imported)."""
    tree, ns = ast.parse(src), {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") in names for t in node.targets):
            exec(compile(ast.Module(body=[node], type_ignores=[]), "tool", "exec"), ns)
    return {n: ns[n] for n in names if n in ns}


def compare_tables(prereg, tables_by_name):
    """[dict(table, name, row, declaration, tool, status)] matching each tool dict to the declared table holding the
    same row keys."""
    decl, out = reading_tables(prereg), []
    for name, tdict in tables_by_name.items():
        tkeys = {_key(k): k for k in tdict}
        num = next((n for n, rows in decl.items() if {_key(k) for k in rows} == set(tkeys)), None)
        if num is None:
            out.append(dict(table=None, name=name, row=None, declaration=None, tool=None, status="NO TABLE"))
            continue
        for row, dtext in decl[num].items():
            ttext = tdict[tkeys[_key(row)]]
            st = "SAME" if _norm(dtext) == _norm(ttext) else \
                "PREFIX" if _norm(dtext).startswith(_norm(ttext) + ":") else "DIFFERENT"
            out.append(dict(table=num, name=name, row=row, declaration=dtext, tool=ttext, status=st))
    return out


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("beside")
    p.add_argument("prereg")
    p.add_argument("readme")
    p.add_argument("--forms", nargs="*")
    p.add_argument("--build")
    p = sp.add_parser("tables")
    p.add_argument("prereg")
    p.add_argument("tool")
    p.add_argument("names", nargs="+")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    prereg = open(a.prereg, encoding="utf-8").read()
    if a.cmd == "beside":
        forms = a.forms if a.forms is not None else (json.load(open(a.build)).get("forms") if a.build else None)
        rows = beside_coverage(prereg, open(a.readme, encoding="utf-8").read(), forms)
        if not rows:                           # 2026-11-27: reading no item is a failure, not a pass
            print(f"declaration_check beside: no 'Beside, never judged' item read from {a.prereg}: nothing checked "
                  "(FAIL)")
            return 2
        for r in rows:
            st = "not checked (condition " + r["condition"] + ")" if not r["checked"] else \
                ("found (" + r["found"] + ")") if r["found"] else "MISSING"
            print(f"{a.prereg}:{r['line']}: [{r['head']}] {st}: {r['item'][:100]}")
        miss = [r for r in rows if r["checked"] and not r["found"]]
        print(f"declaration_check beside: {len(rows)} items, {len(miss)} missing in the README"
              + (f" ({', '.join(r['head'] for r in miss)})" if miss else ""))
        return 1 if miss else 0
    rows = compare_tables(prereg, tool_tables(open(a.tool, encoding="utf-8").read(), a.names))
    for r in rows:
        print(f"table {r['table']} {r['name']} {r['row']}: {r['status']}"
              + ("" if r["status"] == "SAME" else f"\n   declaration: {r['declaration']}\n   tool:        {r['tool']}"))
    bad = [r for r in rows if r["status"] not in ("SAME", "PREFIX")]
    print(f"declaration_check tables: {len(rows)} rows, " + ", ".join(
        f"{s} {sum(r['status'] == s for r in rows)}" for s in ("SAME", "PREFIX", "DIFFERENT", "NO TABLE")))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
