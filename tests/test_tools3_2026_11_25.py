"""Tests for the third round of the notebook tools (workplace VS, 2026-11-25; author The Architect):
declaration_check.py (beside items in the README, reading tables against the tool's strings), procedure_dry.py (the
declared device procedure run word for word without the device), and independent_recount.py's sentinel overlap and
Ohm ruler night scorer. No device."""
import json
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)

import declaration_check as DC  # noqa: E402
import independent_recount as IR  # noqa: E402
import procedure_dry as PD  # noqa: E402

OR_PREREG = os.path.join(ROOT, "prereg", "ohm_ruler_night_2026-11-24.md")
OR_NIGHT = os.path.join(ROOT, "results", "ohm-ruler-night-2026-11-24")
OW_NIGHT = os.path.join(ROOT, "results", "ohm-window-night-2026-11-23")
OLD_REV = "22d1c8c7"                       # the record's README before d4aa2f3c (read from git, not copied)
need_or = pytest.mark.skipif(not os.path.exists(os.path.join(OR_NIGHT, "or", "scores.json")),
                             reason="the Ohm ruler record is not here")


def _read(p):
    return open(p, encoding="utf-8").read()


def _old_readme():
    r = subprocess.run(["git", "show", f"{OLD_REV}:results/ohm-ruler-night-2026-11-24/README.md"], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        pytest.skip(f"git show {OLD_REV} is not available here")
    return r.stdout


# ---- 1. beside items ---------------------------------------------------------------------------------------------
def test_beside_items_bullets_inline_and_condition():
    prereg = "\n".join([
        "- Beside, never judged:",
        "  - the order of W at t = 3 (A0 > A1);",
        "  - with F, the twins' word (MSE F - MSE L);",
        "  - the sentinel.",
        "",
        "Beside, never judged: the margins p - C(n) across n; floors; CZ and depth per item.",
    ])
    items = [t for _, t in DC.beside_items(prereg)]
    assert items == ["the order of W at t = 3 (A0 > A1)", "with F, the twins' word (MSE F - MSE L)", "the sentinel",
                     "the margins p - C(n) across n", "floors", "CZ and depth per item"]
    assert DC.head_of(items[1]) == ("F", "twins' word")
    rows = DC.beside_coverage(prereg, "- Order: yes.\n- Floor 0.97, mirror 0.87.\n", forms=["L"])
    by = {r["head"]: r for r in rows}
    assert by["order"]["found"] == "exact" and by["twins' word"]["checked"] is False
    assert by["sentinel"]["found"] is None and by["floors"]["found"] is None


@need_or
def test_beside_finds_the_missing_sentinel_of_11_24_before_d4aa2f3c():
    prereg = _read(OR_PREREG)
    forms = json.load(open(os.path.join(OR_NIGHT, "or", "build.json")))["forms"]
    old = DC.beside_coverage(prereg, _old_readme(), forms)
    new = DC.beside_coverage(prereg, _read(os.path.join(OR_NIGHT, "README.md")), forms)
    assert [r["head"] for r in old if r["checked"] and not r["found"]] == ["sentinel"]
    assert [r["head"] for r in new if r["checked"] and not r["found"]] == []


@pytest.mark.skipif(not os.path.exists(os.path.join(OW_NIGHT, "README.md")), reason="the 11-23 record is not here")
def test_beside_11_23_all_found():
    rows = DC.beside_coverage(_read(os.path.join(ROOT, "prereg", "ohm_window_night_2026-11-23.md")),
                              _read(os.path.join(OW_NIGHT, "README.md")), None)      # no conditional item there
    assert len(rows) == 5 and all(r["found"] for r in rows)


# ---- 2. reading tables against the tool ----------------------------------------------------------------------------
# Known: the declared tool's table 1 row (NOT UNIFORM, AGREES) ends "on the mean only" where the declaration reads
# "on the mean, not per position" (the home VS, 2026-11-24); the tool is declared and is not changed. Table 2's rows
# 2 to 4 carry the row's naming part only (the declaration adds its reading of the kind of shrink after a colon).
KNOWN_DIFFERENT = {(1, ("NOT UNIFORM", "AGREES"))}
KNOWN_PREFIX = {(2, ("AGREES", "DIFFERS")), (2, ("DIFFERS", "AGREES")), (2, ("DIFFERS", "DIFFERS"))}


def test_tables_of_the_ohm_ruler_declaration_against_the_tool():
    src = _read(os.path.join(ROOT, "gpu", "ohm_ruler_night.py"))
    rows = DC.compare_tables(_read(OR_PREREG), DC.tool_tables(src, ["READ_UNIFORM_A", "READ_A_B"]))
    assert len(rows) == 10 and not [r for r in rows if r["status"] == "NO TABLE"]
    assert {(r["table"], r["row"]) for r in rows if r["status"] == "DIFFERENT"} == KNOWN_DIFFERENT
    assert {(r["table"], r["row"]) for r in rows if r["status"] == "PREFIX"} == KNOWN_PREFIX
    diff = next(r for r in rows if r["status"] == "DIFFERENT")
    assert diff["tool"].endswith("on the mean only") and diff["declaration"].endswith("on the mean, not per position")


def test_tables_catch_a_changed_word():
    prereg = "Table 1, x:\n\n| a | b | reading |\n|---|---|---|\n| U | A | one: two |\n| U | D | three |\n"
    rows = DC.compare_tables(prereg, {"T": {("U", "A"): "one", ("U", "D"): "three!"}})
    assert [r["status"] for r in rows] == ["PREFIX", "DIFFERENT"]


# ---- 3. the device procedure, word for word --------------------------------------------------------------------------
def test_procedure_lines_and_plan():
    lines = PD.procedure_lines(_read(OR_PREREG))
    assert len(lines) == 6 and lines[0].startswith("python gpu/daily_fetch.py")
    steps = PD.plan(lines, "/tmp/o", "/tmp/a.json", "py")
    assert [s[1] is None for s in steps] == [True, False, False, False, True, True]
    assert steps[2][1] == '"py" gpu/ohm_ruler_night.py build /tmp/o/fetch_in/$DEV/dev /tmp/o/or /tmp/a.json ' \
                          '/tmp/o/or_answers --pairs 7 --ts 1 3 4 --forms L'


@need_or
@pytest.mark.skipif(shutil.which("bash") is None, reason="no bash")
def test_procedure_of_c4518f53_stops_where_the_first_try_stopped(tmp_path):
    res = PD.run(OR_PREREG, os.path.join(OR_NIGHT, "fetch_in"), os.path.join(OR_NIGHT, "answers",
                 "ohm_ruler_answers.json"), out_dir=str(tmp_path), cwd=ROOT)
    st = [r["status"] for r in res]
    assert st == ["SKIPPED", "PASS", "FAIL", "NOT REACHED", "SKIPPED", "SKIPPED"]
    first_try = _read(os.path.join(OR_NIGHT, "try1_argerror", "build.txt")).splitlines()[1]
    assert first_try in res[2]["tail"]           # the same argument error as the night's first try


# ---- 4. the sentinel against the users -------------------------------------------------------------------------------
@need_or
def test_sentinel_overlap_11_24_none():
    so = IR.sentinel_overlap(IR.load_job(os.path.join(OR_NIGHT, "or", "job")))
    assert so["overlap"] == 0 and so["word"] == "NOT ON USER QUBITS" and so["sentinel_circuits"] == 4


@pytest.mark.skipif(not os.path.exists(os.path.join(OW_NIGHT, "ow", "job", "manifest.json")),
                    reason="the 11-23 record is not here")
def test_sentinel_overlap_11_23_fifteen():
    so = IR.sentinel_overlap(IR.load_job(os.path.join(OW_NIGHT, "ow", "job")))
    assert so["overlap"] == 15 and so["word"] == "ON USER QUBITS"


# ---- 5. the Ohm ruler night's second count ---------------------------------------------------------------------------
@need_or
def test_ohm_ruler_night_equals_its_record():
    jobs_rel, fn, keys, tol, skip = IR.SCORERS["ohm-ruler-night-2026-11-24"]
    job = IR.load_job(os.path.join(OR_NIGHT, jobs_rel))
    cc = IR.common_checks(job)
    assert cc["qpy_sha256_matches_manifest"] and cc["shots_as_manifest"]
    score = fn(OR_NIGHT, job)
    ref = json.load(open(os.path.join(OR_NIGHT, "or", "scores.json")))
    assert IR.compare(score, ref, keys, tol, skip) == []
    assert len(score["cells"]) == 9 and len(score["uniform"]) == 6


def test_compare_lists_and_skip():
    ref = {"cells": {"x": {"r": [0.5, 0.25], "sentinel": "DEAD"}}}
    assert IR.compare({"cells": {"x": {"r": [0.5, 0.26]}}}, ref, ("cells",), {}, ("sentinel",)) == \
        [("cells/x/r/1", 0.26, 0.25)]
