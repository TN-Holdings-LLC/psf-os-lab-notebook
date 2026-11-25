"""Checks of a night's record and tool against its declaration (workplace VS, 2026-11-25; home instruction "道具の直し、
その 3", 1 and 2). Author The Architect. Read only: nothing is written and nothing is corrected.

  beside   every item of the declaration's "Beside, never judged" list has a line in the night's README.
           Each item's head (its first words, before " of ", a comma, a bracket, a colon or a semicolon, without "the")
           is looked for in the README, case and spacing aside. An item that starts "with X," is conditional on X: it
           is checked only when X is one of the night's forms (--forms, or the forms in --build build.json).
  tables   every row of the declaration's reading tables (the markdown tables after "Table 1" and "Table 2") against
           the tool's strings (dicts keyed by the row's words, e.g. READ_UNIFORM_A, read from the tool's source
           without importing it). A row is SAME (equal text), PREFIX (the tool's text is the declaration's text up to
           a colon: the tool names the row, the declaration adds its reading of the kind of shrink) or DIFFERENT.

  python tools/declaration_check.py beside PREREG.md README.md [--forms L F | --build build.json]
  python tools/declaration_check.py tables PREREG.md TOOL.py NAME [NAME ...]
Exit code: 0 when every item is found / every row is SAME or PREFIX; 1 otherwise.
"""
import argparse
import ast
import json
import re
import sys

BESIDE_HEAD = re.compile(r"^\s*(?:[-*]\s*)?(?:\*\*)?Beside, never judged[^:]*:\s*(.*)$", re.I)
BULLET = re.compile(r"^\s*[-*]\s+(.*)$")


def _norm(s):
    return re.sub(r"\s+", " ", s.replace("`", "").replace("*", "")).strip().lower()


def beside_items(prereg):
    """The items of every "Beside, never judged" list: [(line number, text)]. A list is the bullets right under the
    line, or, when the line itself goes on, that text up to the next blank line, split at semicolons (else commas)."""
    lines, out = prereg.splitlines(), []
    for i, ln in enumerate(lines):
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
            out += [(i + 1, p.strip().rstrip(".")) for p in parts if p.strip()]
            continue
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
    return out


def head_of(item):
    """(condition or None, head): "with F, the 11-23 twins' word (...)" -> ("F", "11-23 twins' word")."""
    cond = None
    m = re.match(r"with ([A-Za-z0-9]+),\s*(.*)$", item)
    if m:
        cond, item = m.group(1), m.group(2)
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
    """[dict(line, item, head, condition, checked, found)] for every beside item of the declaration; found is
    "exact", "words" (see _found) or None."""
    out = []
    for n, item in beside_items(prereg):
        cond, h = head_of(item)
        checked = cond is None or forms is None or cond in forms
        out.append(dict(line=n, item=item, head=h, condition=cond, checked=checked,
                        found=_found(h, readme) if checked else None))
    return out


def reading_tables(prereg):
    """{table number: {(word, word): reading}} for the markdown tables that follow a "Table N" line."""
    lines, out, cur = prereg.splitlines(), {}, None
    for ln in lines:
        m = re.match(r"^\s*Table (\d+)\b", ln)
        if m:
            cur = int(m.group(1))
            out[cur] = {}
            continue
        if cur is None:
            continue
        if ln.startswith("|"):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if len(cells) == 3 and not set(cells[0]) <= set("-: ") and cells[2] != "reading":
                out[cur][(cells[0], cells[1])] = cells[2]
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
        num = next((n for n, rows in decl.items() if set(rows) == set(tdict)), None)
        if num is None:
            out.append(dict(table=None, name=name, row=None, declaration=None, tool=None, status="NO TABLE"))
            continue
        for row, dtext in decl[num].items():
            ttext = tdict[row]
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
