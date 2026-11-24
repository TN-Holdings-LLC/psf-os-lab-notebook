"""Tests for the second round of the notebook tools of 2026-11-24 (workplace VS; author The Architect): lint_beside.py
reads sentences (the SE check by sentence or bullet, "only" / "just" / "nothing" only beside a number or a comparison,
--all), and independent_recount.py scores the two phase estimation nights. No device."""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)

import independent_recount as IR  # noqa: E402
import lint_beside as LB  # noqa: E402

PATS = LB.word_patterns(LB.FALLBACK_WORDS + LB.EXTRA_WORDS)


def _kinds(text, **kw):
    return [(n, "word" if r.startswith("word") else "no SE") for n, r, _ in LB.lint_text(text, PATS, **kw)]


def test_guarded_words_need_a_number_or_a_comparison():
    text = "\n".join([
        "- nothing is compared across nights",           # 1: no number, no comparison
        "- only the first item was read",                 # 2: no number, no comparison
        "- it was only 3 of 16",                          # 3: a number
        "- just more than the other arm",                 # 4: a comparison
        "- the cost is only paid once",                   # 5: a comparison word (cost)
        "- at most once",                                 # 6: other words are listed as before
    ])
    assert _kinds(text) == [(3, "word"), (4, "word"), (5, "word"), (6, "word")]
    assert _kinds(text, all_words=True) == [(1, "word"), (2, "word"), (3, "word"), (4, "word"), (5, "word"),
                                            (6, "word")]


def test_guarded_word_is_read_in_its_own_sentence():
    text = "The share was 0.874 tonight. It was only read once.\n"
    assert _kinds(text) == []
    assert _kinds("It was only read once, on 2 phases.\n") == [(1, "word")]


def test_se_on_the_next_line_of_the_same_sentence_counts_tex():
    tex = "\n".join([
        r"\paragraph{To $n = 8$, parked.} The declared reading holds. Beside, the loss per added bit grew ($0.127$ then",
        r"$0.185$, acceleration $+0.058$, 2 SE 0.028). On another device it grew.",
        "",
        r"No beside value is read on its own (two lie near the line: P0's M $-$ F, $+0.014$",
        r"against 2 SE 0.012, and the acceleration, about 2.1 SE). A peak was seen.",
        "",
        r"Beside, the fez night read 0.424 on another device.",
    ])
    assert _kinds(tex, tex=True) == [(7, "no SE")]


def test_se_unit_is_a_whole_bullet_and_a_table_row_is_its_own():
    md = "\n".join([
        "## Beside",
        "- F16 reads 0.751 tonight. The",           # 2: one bullet, one unit: listed once, at its first decimal
        "  other reads 0.702.",
        "- F17 reads 0.612 (2 SE 0.010).",          # 4: the SE is in the bullet
        "| F18 | 0.555 |",                           # 5: a table row under the Beside heading
        "| F19 | 0.555 (2 SE 0.01) |",
    ])
    assert _kinds(md) == [(2, "no SE"), (5, "no SE")]


def test_decimals_and_abbreviations_do_not_split_sentences():
    s = "The share read 0.579, e.g. on fez. Beside it 0.424 (2 SE 0.006) was read."
    spans = LB.sentences(s)
    assert len(spans) == 2 and s[spans[0][0]:spans[0][1]].endswith("on fez.")


@pytest.mark.skipif(not os.path.exists(os.path.join(ROOT, "notes", "paper11", "paper11.tex")),
                    reason="paper 11 is not here")
def test_paper11_two_next_line_se_are_not_listed():
    text = open(os.path.join(ROOT, "notes", "paper11", "paper11.tex"), encoding="utf-8").read()
    lines = text.splitlines()
    at = {i + 1 for i, ln in enumerate(lines) if "loss per added bit grew" in ln} | \
         {i + 1 for i, ln in enumerate(lines) if "P0's M $-$ F" in ln}
    assert len(at) == 2
    listed = {n for n, r, _ in LB.lint_text(text, PATS, tex=True) if r.startswith("no SE")}
    assert not (listed & at)


def test_lint_all_flag_and_exit_code(tmp_path):
    f = tmp_path / "x.md"
    f.write_text("- nothing is compared\n- only 2 of 3\n", encoding="utf-8")
    run = lambda *a: subprocess.run([sys.executable, os.path.join(TOOLS, "lint_beside.py"), "--no-results", str(f)]
                                    + list(a), cwd=ROOT, capture_output=True, text=True)
    r, r_all = run(), run("--all")
    assert r.returncode == 0 and "1 lines listed" in r.stdout
    assert r_all.returncode == 0 and "2 lines listed" in r_all.stdout


def test_compare_tolerance_by_key():
    ref = {"per_n": {"6": {"ceiling": 0.30650912926478213, "p": 0.5}}}
    mine = {"per_n": {"6": {"ceiling": 0.3065, "p": 0.5}}}
    assert IR.compare(mine, ref, ("per_n",)) != []
    assert IR.compare(mine, ref, ("per_n",), {"ceiling": 5e-5}) == []


def test_scorers_registered_with_declared_ceilings():
    assert {"qpe-parked-night-2026-11-21", "qpe-n78-night-2026-11-22"} <= set(IR.SCORERS)
    assert [IR.CEILINGS[n][0] for n in (4, 6, 7, 8)] == [0.4706, 0.3065, 0.2480, 0.2007]


NIGHTS = [("qpe-parked-night-2026-11-21", os.path.join("qp", "parked_scores.json")),
          ("qpe-n78-night-2026-11-22", os.path.join("qn", "qpe78_scores.json"))]


@pytest.mark.parametrize("name,ref", NIGHTS)
def test_qpe_night_equals_its_record(name, ref):
    night = os.path.join(ROOT, "results", name)
    if not os.path.exists(os.path.join(night, ref)):
        pytest.skip("the record is not here")
    jobs_rel, fn, keys, tol = IR.SCORERS[name]
    jobs = [(os.path.join(night, j), IR.load_job(os.path.join(night, j))) for j in jobs_rel]
    for _, job in jobs:
        cc = IR.common_checks(job)
        assert cc["qpy_sha256_matches_manifest"] and cc["shots_as_manifest"]
    score = fn(night, jobs)
    assert IR.compare(score, json.load(open(os.path.join(night, ref))), keys, tol) == []
    assert all(not miss for _, _, miss in IR.readme_rows(night, score))
