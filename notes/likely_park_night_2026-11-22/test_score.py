"""The rule for the default in gpu/likely_park_night.py (home VS, 2026-11-22): every branch, with items left out for
OVERSHOOT. Plain asserts (no psf-os needed): python notes/likely_park_night_2026-11-22/test_score.py"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "gpu"))
import likely_park_night as LP  # noqa: E402

M, S, L = "KEEPS MORE", "SAME WITHIN ERROR", "KEEPS LESS"
cases = [
    (dict(nfl3m3=M, p0l3=S, p3l3=S), M, (), "the default"),
    (dict(nfl3m3=M, p0l3=L, p3l3=S), M, (), "opt-in (a counted item KEEPS LESS)"),
    (dict(nfl3m3=S, p0l3=S, p3l3=S), M, (), "opt-in (no counted item KEEPS MORE)"),
    (dict(nfl3m3=M, p0l3=M, p3l3=M), S, (), "opt-in (the gate is closed"),
    # a KEEPS LESS on an overshooting item is recorded but not counted
    (dict(nfl3m3=M, p0l3=L, p3l3=S), M, ("p0l3",), "the default"),
    # a lone KEEPS MORE on an overshooting item does not make it the default
    (dict(nfl3m3=S, p0l3=M, p3l3=S), M, ("p0l3",), "opt-in (no counted item KEEPS MORE)"),
    # every item out
    (dict(nfl3m3=M, p0l3=M, p3l3=M), M, ("nfl3m3", "p0l3", "p3l3"), "opt-in (no item counted"),
    # the gate wins over everything
    (dict(nfl3m3=M, p0l3=S, p3l3=S), L, ("p0l3",), "opt-in (the gate is closed"),
]
for words, gate, excl, want in cases:
    got = LP.decision(words, gate, excl)
    assert got.startswith(want), (words, gate, excl, got)
print(f"{len(cases)} cases: every branch as declared")
