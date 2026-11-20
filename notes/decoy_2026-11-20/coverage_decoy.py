"""Does every outcome of the decoy test fall on exactly one row of its reading table? (the workplace VS's
coverage_decoy.py of 2026-11-20, rewritten by the workplace Claude for the table of the owner's decision of
2026-11-20 morning; it calls the tool's own reading_row). No data: the three words per sub-item, enumerated.

  python notes/decoy_2026-11-20/coverage_decoy.py
"""
import itertools
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "gpu"))
import decoy_night as DN  # noqa: E402

W = ("LESS", "SAME", "MORE")
KEYS = ["d0a", "d0b", "d1a", "d1b", "d2a", "d2b"]


def main():
    by = {}
    for ws in itertools.product(W, repeat=len(KEYS)):
        lose = {k: w == "LESS" for k, w in zip(KEYS, ws)}
        r = DN.reading_row(lose)
        by[r] = by.get(r, 0) + 1
    total = 3 ** len(KEYS)
    print(f"outcomes {total}; on a row {sum(by.values())} (one row each, by construction: rows are tested in order)")
    for r in sorted(by):
        print(f"  row {r}: {by[r]:3d}  {DN.READING[r]}")
    print(f"on no row: {total - sum(by.values())}")
    # every row reachable, and the rows as conditions are disjoint (each outcome checked against all six)
    conds = {
        4: lambda L: not L["d0a"] or L["d0b"],
        2: lambda L: L["d0a"] and not L["d0b"] and L["d1a"] and L["d2a"],
        6: lambda L: L["d0a"] and not L["d0b"] and L["d1a"] and not L["d2a"],
        3: lambda L: L["d0a"] and not L["d0b"] and not L["d1a"] and L["d1b"],
        1: lambda L: L["d0a"] and not L["d0b"] and not L["d1a"] and not L["d1b"] and L["d2a"],
        5: lambda L: L["d0a"] and not L["d0b"] and not L["d1a"] and not L["d1b"] and not L["d2a"],
    }
    multi = none = 0
    for ws in itertools.product(W, repeat=len(KEYS)):
        L = {k: w == "LESS" for k, w in zip(KEYS, ws)}
        hits = [r for r, c in conds.items() if c(L)]
        multi += len(hits) > 1
        none += not hits
        assert hits == [DN.reading_row(L)] or len(hits) != 1
    print(f"as stand-alone conditions: on no row {none}, on more than one row {multi}")


if __name__ == "__main__":
    main()
