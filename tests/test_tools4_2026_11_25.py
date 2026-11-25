"""Tests for the fourth round of the notebook tools (workplace VS, 2026-11-25 b; author The Architect):
procedure_dry skips score, score2 and score3; declaration_check reads "- name: description" beside lists strictly and
reading tables with "|0>" in a cell and "(a)" keys; independent_recount's frame for the third night. No device."""
import importlib.util
import json
import os
import shutil
import sys

import numpy as np
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)

import declaration_check as DC  # noqa: E402
import independent_recount as IR  # noqa: E402
import procedure_dry as PD  # noqa: E402

OR_PREREG = os.path.join(ROOT, "prereg", "ohm_ruler_night_2026-11-24.md")
DRAFT3 = os.path.join(ROOT, "prereg", "drafts-2026-11-25", "ohm_ruler3_night_DRAFT.md")
OR_NIGHT = os.path.join(ROOT, "results", "ohm-ruler-night-2026-11-24")
HAS_PSFOS = importlib.util.find_spec("psf_os") is not None


def _read(p):
    return open(p, encoding="utf-8").read()


# ---- 1. procedure_dry skips every score line ---------------------------------------------------------------------
def test_score_score2_score3_are_skipped():
    lines = ["python gpu/x.py build OUT/fetch_in/$DEV/dev OUT/o ANSWERS_SEALED OUT/a",
             "python gpu/x.py score OUT/o OUT/a", "python gpu/x2.py score2 OUT/o OUT/a",
             "python gpu/x3.py score3 OUT/o OUT/a --tau 0.3", "python gpu/x3.py scoreboard OUT/o"]
    steps = PD.plan(lines, "/tmp/o", "/tmp/a.json", "py")
    assert [s[1] is None for s in steps] == [False, True, True, True, False]


@pytest.mark.skipif(not os.path.exists(DRAFT3), reason="the third night's draft is not here")
def test_draft3_plan_skips_score3():
    steps = PD.plan(PD.procedure_lines(_read(DRAFT3)), "/tmp/o", "/tmp/a.json", "py")
    run = [ln for ln, cmd, _ in steps if cmd is not None]
    assert [r.split()[2] if "ohm_ruler" in r else r.split()[0] for r in run][-2:] == ["build3", "check3"]
    assert any("score3" in ln and cmd is None for ln, cmd, _ in steps)


@pytest.mark.skipif(not (HAS_PSFOS and os.path.exists(DRAFT3) and os.path.exists(os.path.join(OR_NIGHT, "fetch_in"))
                         and shutil.which("bash")), reason="psf-os, bash, the draft or the 11-24 record is missing")
def test_draft3_procedure_passes_pick_build3_check3(tmp_path):
    ans = os.path.join(OR_NIGHT, "answers", "ohm_ruler_answers.json")       # 7 pairs (11-24, published)
    if "4:9" in _read(DRAFT3):                                               # the draft builds 9 pairs at t = 4
        ans = os.environ.get("OHM3_ANS9", "")
        if not os.path.exists(ans):
            pytest.skip("the draft builds 9 pairs at t = 4: set OHM3_ANS9 to the 9-pair answers (made by "
                        "gpu/ohm_ruler_night.py answers ... --pairs 9 --ts 1 3 4 --forms L; kept outside the notebook)")
    res = PD.run(DRAFT3, os.path.join(OR_NIGHT, "fetch_in"), ans, out_dir=str(tmp_path), cwd=ROOT)
    st = {r["line"].split()[2] if "ohm_ruler" in r["line"] else r["line"].split()[0]: r["status"] for r in res}
    assert "FAIL" not in st.values()
    assert [r["status"] for r in res if "score3" in r["line"]] == ["SKIPPED"]
    assert sum(r["status"] == "PASS" for r in res) == 3          # pick, build3, check3


# ---- 2. beside lists written as "- name: description" -------------------------------------------------------------
NAMED_BLOCK = "\n".join([
    "- Beside, never judged:",
    "  - order: the order of W, W_a, W_b, W_b', W_c and W_d at t = 3 and 4 (A0 > A1 > A2)",
    "  - growth: W(t) / W(1), raw and exact",
    "  - smallest difference: each ruler's t SE per cell",
    "  - left out: the qubits (b') leaves out, per cell",
    "  - sentinel: the sentinel's word and its overlap with the user's qubits",
])


def test_named_beside_list_is_read_by_name_only():
    readme = "- Order (A0 > A1 > A2): yes.\n- Growth W(3)/W(1): 2.3.\n- The sentinel: DEAD.\n- left out: none\n"
    rows = DC.beside_coverage(NAMED_BLOCK, readme)
    assert {r["form"] for r in rows} == {"named"}
    found = {r["head"]: r["found"] for r in rows}
    assert found == {"order": "name", "growth": "name", "smallest difference": None, "left out": "name",
                     "sentinel": "name"}


def test_free_lists_keep_the_old_reading():
    prereg = "- Beside, never judged:\n  - the order of W at t = 3 (A0 > A1)\n  - the sentinel\n"
    rows = DC.beside_coverage(prereg, "- Order: yes.\n")
    assert [(r["head"], r["found"], r["form"]) for r in rows] == [("order", "exact", "free"),
                                                                  ("sentinel", None, "free")]


@pytest.mark.skipif(not os.path.exists(DRAFT3), reason="the third night's draft is not here")
def test_draft3_beside_list_form():
    rows = DC.beside_coverage(_read(DRAFT3), "")
    assert rows                                                      # the draft has a beside list
    forms = {r["form"] for r in rows}
    if forms == {"named"}:                                           # the draft as finished on 2026-11-25 b
        assert [r["head"] for r in rows] == ["order", "growth", "smallest difference", "left out", "sentinel"]


# ---- 3. reading tables: "|0>" inside a cell, "(a)" against the tool's "a" ------------------------------------------
def test_table_cells_with_a_ket_and_bracketed_keys():
    prereg = "\n".join(["Table A, x:", "", "| ruler | word | reading |", "|---|---|---|",
                        "| (b) | AGREES | the |0> mirror's mean carries it |",
                        "| (b_out) | DIFFERS | the |0> mirror, low qubits left out, does not |"])
    tool = {("b", "AGREES"): "the |0> mirror's mean carries it",
            ("b_out", "DIFFERS"): "the |0> mirror, low qubits left out, does not"}
    rows = DC.compare_tables(prereg, {"T": tool})
    assert [r["status"] for r in rows] == ["SAME", "SAME"]


def test_ohm_ruler_11_24_tables_unchanged():
    rows = DC.compare_tables(_read(OR_PREREG), DC.tool_tables(_read(os.path.join(ROOT, "gpu", "ohm_ruler_night.py")),
                                                              ["READ_UNIFORM_A", "READ_A_B"]))
    assert [sum(r["status"] == s for r in rows) for s in ("SAME", "PREFIX", "DIFFERENT")] == [6, 3, 1]


@pytest.mark.skipif(not os.path.exists(DRAFT3), reason="the third night's draft is not here")
def test_draft3_tables_word_for_word():
    tool = DC.tool_tables(_read(os.path.join(ROOT, "gpu", "ohm_ruler_night3.py")), ["READ_TABLE_A", "READ_TABLE_B"])
    if len(tool) < 2:
        pytest.skip("the third night's tool has no READ_TABLE_A / READ_TABLE_B here (the workplace Claude's branch "
                    "ohm-ruler3b-2026-11-25 adds them)")
    rows = DC.compare_tables(_read(DRAFT3), tool)
    assert rows and all(r["status"] == "SAME" for r in rows)


# ---- 5. the third night's frame -----------------------------------------------------------------------------------
def test_words_rule4_rule5():
    assert IR._words(0.01, 0.0, 7) == {"t": "NOT READ", "2se": "NOT READ"}
    assert IR._words(0.045, 0.02, 7) == {"t": "AGREES", "2se": "DIFFERS"}     # 2 SE 0.04 < 0.045 < 2.447 SE 0.049
    assert IR._words(0.045, 0.02, 9) == {"t": "AGREES", "2se": "DIFFERS"}     # 2.306 SE 0.046


def test_mirror_mean_se_weights_and_subset():
    pub = dict(meas={10: 0, 11: 1, 12: 2}, counts={"000": 6, "011": 4})        # clbit 0 rightmost
    z, se = IR._mirror_mean_se(pub, [10, 11, 12], [0, 1], np.array([1.0, -1.0, 1.0]))
    assert np.allclose(z, [0.2, 0.2, 1.0])
    per = [(1 - 1) / 2] * 6 + [(-1 + 1) / 2] * 4                               # w * Z over labels 10, 11 per shot
    assert abs(se - float(np.std(per, ddof=1) / np.sqrt(10))) < 1e-12


@pytest.mark.skipif(not os.environ.get("OHM3_TRYBUILD"), reason="set OHM3_TRYBUILD=OUT;ANS_BY_LABEL (a build3 "
                    "folder with counts and its scores3.json) to compare the frame with score3")
def test_frame_equals_score3_on_a_try_build():
    out, ans = os.environ["OHM3_TRYBUILD"].split(";")
    mine = IR.score_ohm_ruler3(out, IR.load_job(os.path.join(out, "job")), ans)
    assert IR.compare_ruler3(mine, json.load(open(os.path.join(out, "scores3.json")))) == []
