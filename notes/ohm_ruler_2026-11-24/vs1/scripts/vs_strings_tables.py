"""The ohm ruler tool's string rule and reading tables, checked independently (workplace VS, 2026-11-24, sono1; author
The Architect). No device; no answer value is read or printed.

  1. strings: the 11-12 generator written here again (numpy default_rng(SEED); bit k is 1 with probability 0.75 on the
     left half, 0.25 on the right; each draw kept when |T0| >= 6 on every light cone at t >= 3 and >= 8 on the whole
     chain when F is built), compared with build.json's strings; every kept string meets the thresholds, every draw
     skipped before the last kept one misses one; and the tool's strings() reads nothing but the generator and T0
     (checked on its source: no answer, no device file, no count)
  2. the reading tables of the tool: every combination of the words falls on exactly one row

  python vs_strings_tables.py NOTEBOOK BUILD_DIR [BUILD_DIR ...]
"""
import ast
import itertools
import json
import os
import sys

import numpy as np

nb = sys.argv[1]
N, H, BIAS, SEED = 40, 20, 0.5, 20261124
CONES = {1: list(range(18, 22)), 3: list(range(14, 30)), 4: list(range(12, 34))}


def t0(b, qs):
    return sum(1 - 2 * b[q] for q in qs)


def regions(ts, forms):
    r = {f"cone{t}": CONES[t] for t in ts if t >= 3}
    if "F" in forms:
        r["full"] = list(range(N))
    return r


def gen(pairs, ts, forms):
    rng = np.random.default_rng(SEED)
    reg = regions(ts, forms)
    kept, skipped = [], []
    while len(kept) < pairs:
        b = [int(rng.random() < ((1 + BIAS) / 2 if k < H else (1 - BIAS) / 2)) for k in range(N)]
        ok = all(abs(t0(b, qs)) >= (8 if r == "full" else 6) for r, qs in reg.items())
        (kept if ok else skipped).append(b)
    return kept, skipped, reg


for d in sys.argv[2:]:
    bj = json.load(open(os.path.join(d, "build.json")))
    ts, forms = bj["cycles"], bj["forms"]
    strs = bj["strings"]
    pairs = len([n for n in strs if n.startswith("s")])
    kept, skipped, reg = gen(pairs, ts, forms)
    same = all("".join(map(str, kept[i])) == "".join(map(str, strs[f"s{i:02d}"])) if not isinstance(strs[f"s{i:02d}"], str)
               else "".join(map(str, kept[i])) == strs[f"s{i:02d}"] for i in range(pairs))
    comp = all(all(int(x) + int(y) == 1 for x, y in zip(strs[f"s{i:02d}"], strs[f"c{i:02d}"])) for i in range(pairs))
    meet = all(all(abs(t0([int(x) for x in strs[f"s{i:02d}"]], qs)) >= (8 if r == "full" else 6) for r, qs in reg.items())
               for i in range(pairs))
    print(f"{os.path.basename(d)}: {pairs} pairs, t {ts}, forms {forms}: generator written here gives build.json's strings "
          f"{same}; complements {comp}; every kept string meets the thresholds {meet}; draws skipped before the last "
          f"kept {len(skipped)} (each misses a threshold by construction)")

src = open(os.path.join(nb, "gpu", "ohm_ruler_night.py"), encoding="utf-8").read()
tree = ast.parse(src)
fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "strings")
names = sorted({n.id for n in ast.walk(fn) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(fn) if isinstance(n, ast.Attribute)})
reads_files = any(isinstance(n, ast.Call) and getattr(n.func, "id", "") in ("open",) for n in ast.walk(fn))
print(f"strings() in the tool: names used {names}; opens a file {reads_files}")

sys.path.insert(0, os.path.join(nb, "gpu"))
ns = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and any(getattr(t, "id", "") in ("READ_UNIFORM_A", "READ_A_B") for t in node.targets):
        exec(compile(ast.Module(body=[node], type_ignores=[]), "x", "exec"), ns)
t1 = ns["READ_UNIFORM_A"]
t2 = ns["READ_A_B"]
c1 = list(itertools.product(("UNIFORM", "NOT UNIFORM", "NOT READ"), ("AGREES", "DIFFERS")))
c2 = list(itertools.product(("AGREES", "DIFFERS"), ("AGREES", "DIFFERS")))
print(f"table 1: {len(c1)} combinations, rows {len(t1)}, every combination on one row {all(c in t1 for c in c1)}, "
      f"no extra row {set(t1) <= set(c1)}")
print(f"table 2: {len(c2)} combinations, rows {len(t2)}, every combination on one row {all(c in t2 for c in c2)}, "
      f"no extra row {set(t2) <= set(c2)}")
