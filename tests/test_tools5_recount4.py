"""Tests for independent_recount.py's fourth-night frame (workplace VS, 2026-11-26; author The Architect): (a') on the
third night's record against the home VS's beside values, and (a'), (e), (de) against score4 on a try-build. No
device."""
import json
import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import independent_recount as IR  # noqa: E402

OR3 = os.path.join(ROOT, "results", "ohm-ruler3-night-2026-11-25")
HOME_VS = os.path.join(ROOT, "notes", "verify_2026-11-25", "or3_beside_aprime_dq.json")


@pytest.mark.skipif(not (os.path.exists(os.path.join(OR3, "or3", "job", "raw_counts.json")) and os.path.exists(HOME_VS)),
                    reason="the third night's record or the home VS's values are not here")
def test_a_prime_on_the_third_night_equals_the_home_vs():
    job = IR.load_job(os.path.join(OR3, "or3", "job"))
    mine = IR.score_ohm_ruler4(os.path.join(OR3, "or3"), job,
                               os.path.join(OR3, "answers", "ohm_ruler3_answers_by_label.json"))
    ref = json.load(open(HOME_VS))
    n = 0
    for cell, c in mine["cells"].items():
        if "a_prime" not in c["rulers"]:
            continue
        a, b = c["rulers"]["a_prime"], ref[cell.replace("_L", "")]["a_prime"]
        for k in ("rho_mean", "d", "se"):
            assert abs(a[k] - b[k]) < 1e-12, (cell, k)
            n += 1
        assert a["words"] == b["words"], cell
        assert sorted(a["left_out"]) == sorted(ref[cell.replace("_L", "")]["left_out"]), cell
    assert n == 18                                     # six cells at t >= 3
    assert not any("e" in c["rulers"] for c in mine["cells"].values())    # no readout circuits on 11-25
    q = mine["qubits"]
    assert {"MIRROR_LOW", "R_LOW", "mirror_z", "m_q", "r_q", "e_q"} <= set(q[0])
    assert all(r["e_q"] is None for r in q)


def test_frame_handles_no_scatter_as_not_read():
    assert IR._words(0.0, 0.0, 9) == {"t": "NOT READ", "2se": "NOT READ"}


@pytest.mark.skipif(not os.environ.get("OHM4_TRYBUILD"), reason="set OHM4_TRYBUILD=OUT;ANS_BY_LABEL (a build4 folder "
                    "with counts and its scores4.json) to compare the frame with score4")
def test_frame_equals_score4_on_a_try_build():
    out, ans = os.environ["OHM4_TRYBUILD"].split(";")
    mine = IR.score_ohm_ruler4(out, IR.load_job(os.path.join(out, "job")), ans)
    assert IR.compare_ruler4(mine, json.load(open(os.path.join(out, "scores4.json")))) == []
    assert all({"e", "de"} <= set(c["rulers"]) for c in mine["cells"].values())
