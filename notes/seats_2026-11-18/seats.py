"""Seat ledger: how many distance-d bit-flip repetition-code blocks fit on a device record, side by side, night by
night (workplace VS Claude, 2026-11-18; home instruction 18h, item 2). Desk only.

Reads only the device record's coupling graph and failed marks (`dev/device.json`: num_qubits, couplers,
failed_couplers, failed_qubits; name and fetched for the table). No calibration error number is read. psf-os is not
imported: the health rule is written again here from its text.

Block. A distance-d block is a simple path of 2d - 1 qubits (data, ancilla, data, ..., data: d data and d - 1
ancillas alternating along the line), as rule C's chains are:
  - every qubit usable: not failed, and not an end of a failed coupler ("suspect", rule C's default, the judgement
    of the user entrance);
  - every link of the path usable: a coupler of the record, not failed.
Side by side. Two blocks may share no qubit, and no coupler of the record (working or failed) may join a qubit of one
to a qubit of the other.

Counts, per record and d = 3, 5, 7:
  - max: the largest number of blocks, by an integer programme over every block (scipy.optimize.milp, HiGHS):
    one variable per block, and for every coupler (u, v) of the record, the blocks holding u or v sum to at most 1.
    This is exactly "no shared qubit and no joining coupler", because every qubit has a coupler. The solver's status
    is recorded; "optimal" means proven.
  - fixed order: blocks taken in one fixed order (by their smallest label, then lexicographically), each kept if it
    clashes with none kept so far. A reproducible lower bound with no solver.

  python seats.py RESULTS_DIR [--json OUT.json] [--from 2026-11-13]
"""
import json
import os
import re
import sys

DEVICES = ("ibm_marrakesh", "ibm_fez", "ibm_kingston")


def load(path):
    d = json.load(open(path))
    return dict(name=d["name"], n=d["num_qubits"], couplers=[tuple(c) for c in d["couplers"]],
                failed_couplers=[tuple(c) for c in d["failed_couplers"]], failed_qubits=list(d["failed_qubits"]),
                fetched=d.get("fetched"))


def health(dev):
    bad = set(dev["failed_qubits"]) | {q for c in dev["failed_couplers"] for q in c}
    badc = {frozenset(c) for c in dev["failed_couplers"]}
    adj = {q: set() for q in range(dev["n"])}
    for a, b in dev["couplers"]:
        if frozenset((a, b)) in badc or a in bad or b in bad:
            continue
        adj[a].add(b)
        adj[b].add(a)
    return [q for q in range(dev["n"]) if q not in bad], adj


def blocks(dev, length):
    """Every simple path of `length` usable qubits on usable links, each once (as the tuple smaller than its reverse)."""
    usable, adj = health(dev)
    out = set()

    def grow(path, seen):
        if len(path) == length:
            t = tuple(path)
            out.add(min(t, t[::-1]))
            return
        for x in sorted(adj[path[-1]]):
            if x not in seen:
                seen.add(x)
                path.append(x)
                grow(path, seen)
                path.pop()
                seen.discard(x)

    for s in usable:
        grow([s], {s})
    return sorted(out, key=lambda t: (min(t), t))


def clash_sets(dev, bl):
    """For every coupler of the record, the indices of the blocks holding either end."""
    holds = {}
    for i, b in enumerate(bl):
        for q in b:
            holds.setdefault(q, set()).add(i)
    rows = []
    for a, b in dev["couplers"]:
        s = holds.get(a, set()) | holds.get(b, set())
        if len(s) > 1:
            rows.append(sorted(s))
    return rows


def fixed_order(dev, bl):
    nb = {q: set() for q in range(dev["n"])}
    for a, b in dev["couplers"]:
        nb[a].add(b)
        nb[b].add(a)
    taken, kept = set(), []
    for b in bl:
        zone = set(b) | {x for q in b for x in nb[q]}
        if zone & taken:
            continue
        kept.append(b)
        taken |= set(b)
    return kept


def maximum(dev, bl):
    import numpy as np
    from scipy.optimize import Bounds, LinearConstraint, milp
    from scipy.sparse import lil_matrix
    if not bl:
        return 0, "no block", []
    rows = clash_sets(dev, bl)
    c = -np.ones(len(bl))
    if not rows:
        return len(bl), "optimal (no clash)", bl
    A = lil_matrix((len(rows), len(bl)))
    for r, s in enumerate(rows):
        for i in s:
            A[r, i] = 1
    res = milp(c, constraints=LinearConstraint(A.tocsr(), -np.inf, 1), integrality=np.ones(len(bl)),
               bounds=Bounds(0, 1), options=dict(time_limit=600))
    chosen = [bl[i] for i in range(len(bl)) if res.x is not None and res.x[i] > 0.5]
    status = {0: "optimal", 1: "time or iteration limit (best found, not proven)"}.get(res.status, res.message)
    return len(chosen), status, chosen


def verify(dev, chosen, length):
    """Independent re-check of a placement: length, health, links, no shared qubit, no joining coupler."""
    usable, adj = health(dev)
    us = set(usable)
    cp = {frozenset(c) for c in dev["couplers"]}
    owner = {}
    for k, b in enumerate(chosen):
        assert len(b) == length and len(set(b)) == length
        assert all(q in us for q in b)
        assert all(b[i + 1] in adj[b[i]] for i in range(length - 1))
        for q in b:
            assert q not in owner
            owner[q] = k
    for e in cp:
        a, b = tuple(e)
        if a in owner and b in owner:
            assert owner[a] == owner[b], f"blocks {owner[a]} and {owner[b]} joined by {sorted(e)}"
    return True


def records(results, since):
    rows = []
    for exp in sorted(os.listdir(results)):
        m = re.search(r"2026-11-(\d\d)", exp)
        if not m or f"2026-11-{m.group(1)}" < since:
            continue
        fi = os.path.join(results, exp, "fetch_in")
        if not os.path.isdir(fi):
            continue
        for dv in sorted(os.listdir(fi)):
            p = os.path.join(fi, dv, "dev", "device.json")
            if dv in DEVICES and os.path.exists(p):
                rows.append((f"2026-11-{m.group(1)}", dv, exp, p))
    return rows


def main():
    args = sys.argv[1:]
    js = since = None
    if "--json" in args:
        k = args.index("--json"); js = args[k + 1]; del args[k:k + 2]
    if "--from" in args:
        k = args.index("--from"); since = args[k + 1]; del args[k:k + 2]
    results = args[0]
    since = since or "2026-11-13"
    seen, table = {}, []
    for night, dv, exp, p in records(results, since):
        dev = load(p)
        key = (dv, tuple(sorted(map(tuple, map(sorted, dev["failed_couplers"])))), tuple(sorted(dev["failed_qubits"])),
               len(dev["couplers"]))
        row = dict(night=night, device=dv, experiment=exp, fetched=dev["fetched"],
                   failed_qubits=sorted(dev["failed_qubits"]), failed_couplers=sorted(map(sorted, dev["failed_couplers"])),
                   couplers=len(dev["couplers"]))
        if key in seen:
            row["same_record_as"] = seen[key]
            row["counts"] = None
            table.append(row)
            continue
        seen[key] = f"{night} {exp}"
        usable, _ = health(dev)
        row["usable_qubits"] = len(usable)
        row["counts"] = {}
        for d in (3, 5, 7):
            L = 2 * d - 1
            bl = blocks(dev, L)
            mx, st, chosen = maximum(dev, bl)
            verify(dev, chosen, L)
            fo = fixed_order(dev, bl)
            verify(dev, fo, L)
            row["counts"][d] = dict(blocks_possible=len(bl), max=mx, status=st, fixed_order=len(fo),
                                    max_placement=[list(b) for b in chosen])
        table.append(row)
        c = row["counts"]
        print(f"{night} {dv:14s} {exp:32s} usable {len(usable):3d}  " +
              "  ".join(f"d{d}: max {c[d]['max']:2d} ({c[d]['status'][:7]}), fixed {c[d]['fixed_order']:2d}"
                        for d in (3, 5, 7)), flush=True)
    if js:
        json.dump(table, open(js, "w"), indent=1)


if __name__ == "__main__":
    main()
