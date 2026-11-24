"""Tests for the three notebook tools of 2026-11-24 (workplace VS; author The Architect): check_readme_numbers.py's
arguments and its refusal to check nothing, lint_beside.py, independent_recount.py. No device."""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)

import check_readme_numbers as CRN  # noqa: E402
import independent_recount as IR  # noqa: E402
import lint_beside as LB  # noqa: E402


def _night(base, name, with_job):
    d = os.path.join(base, name)
    os.makedirs(os.path.join(d, "job"))
    open(os.path.join(d, "README.md"), "w").write("# a night\n")
    if with_job:
        json.dump(dict(job_id="dabcdefghijklmnopqrs", rows=[]), open(os.path.join(d, "job", "raw_counts.json"), "w"))
    return d


def test_resolve_names_paths_and_missing(tmp_path):
    base = str(tmp_path / "results")
    a = _night(base, "night-a", True)
    _night(base, "night-b", True)
    by_path, miss = CRN.resolve([a], None, default_results=base)
    by_name, miss2 = CRN.resolve(["night-a"], None, default_results=base)
    by_opt, miss3 = CRN.resolve(None, [a], default_results=base)
    old_form, miss4 = CRN.resolve([base], ["night-b"], default_results="elsewhere")
    whole, _ = CRN.resolve([base], None, default_results="elsewhere")
    assert [os.path.basename(x) for x in by_path] == ["night-a"] and not miss
    assert [os.path.basename(x) for x in by_name] == ["night-a"] and not miss2
    assert [os.path.basename(x) for x in by_opt] == ["night-a"] and not miss3
    assert [os.path.basename(x) for x in old_form] == ["night-b"] and not miss4
    assert sorted(os.path.basename(x) for x in whole) == ["night-a", "night-b"]
    assert CRN.resolve(["no-such-night"], None, default_results=base)[1] == ["no-such-night"]


def _run_crn(args, cwd):
    return subprocess.run([sys.executable, os.path.join(TOOLS, "check_readme_numbers.py")] + args, cwd=cwd,
                          capture_output=True, text=True)


def test_checking_nothing_stops(tmp_path):
    base = tmp_path / "results"
    _night(str(base), "no-record", False)               # a README but no job record: nothing to check
    r = _run_crn([str(base / "no-record")], str(tmp_path))
    assert r.returncode == 1 and "no night checked" in r.stderr
    r2 = _run_crn([str(base / "absent")], str(tmp_path))
    assert r2.returncode == 2 and "night not found" in r2.stderr


def test_one_night_by_path_and_by_name_agree(tmp_path):
    base = tmp_path / "results"
    _night(str(base), "night-a", True)
    r1 = _run_crn([str(base / "night-a")], str(tmp_path))
    r2 = _run_crn(["night-a"], str(tmp_path))
    assert r1.returncode == 0 and r2.returncode == 0
    assert "1 nights checked" in r1.stdout and r1.stdout == r2.stdout


def test_lint_selftest_and_words():
    assert LB.selftest()
    words = LB.style_words(os.path.join(ROOT, "notes", "style_beside.md"))
    for w in ("at most", "at least", "only", "lies elsewhere"):
        assert w in words


def test_lint_exit_code_is_zero(tmp_path):
    f = tmp_path / "x.md"
    f.write_text("Beside: the share 0.845 here.\nThe cost is at most 0.01.\n", encoding="utf-8")
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "lint_beside.py"), "--no-results", str(f)], cwd=ROOT,
                       capture_output=True, text=True)
    assert r.returncode == 0 and "2 lines listed" in r.stdout


def test_recount_selftest():
    assert IR.selftest()


@pytest.mark.skipif(not os.path.exists(os.path.join(ROOT, "results", "ohm-window-night-2026-11-23", "ow", "job",
                                                    "raw_counts.json")), reason="the ohm-window record is not here")
def test_recount_ohm_window_equals_the_home_vs_check():
    night = os.path.join(ROOT, "results", "ohm-window-night-2026-11-23")
    job = IR.load_job(os.path.join(night, "ow", "job"))
    cc = IR.common_checks(job)
    assert cc["qpy_sha256_matches_manifest"] and cc["shots_as_manifest"]
    score = IR.score_ohm_window(night, job)
    ref = json.load(open(os.path.join(ROOT, "notes", "verify_2026-11-23", "ow_independent_check.json")))
    assert IR.compare(score, ref) == []
    assert score["chain_from_records"]["directions_agreeing_with_the_answers"] == 1
