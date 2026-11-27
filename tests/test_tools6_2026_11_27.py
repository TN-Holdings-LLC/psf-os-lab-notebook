"""Tests for the sixth round of the notebook tools (workplace VS, 2026-11-27; author The Architect):
declaration_check beside reads "## Beside, never judged" headings and fails on no item; check_readme_numbers checks
"at most" / range sentences against the record they name; qubits_across rebuilds qubits.csv's columns from a record.
No device."""
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)

import check_readme_numbers as CRN  # noqa: E402
import declaration_check as DC  # noqa: E402
import qubits_across as QA  # noqa: E402

N4 = os.path.join(ROOT, "results", "ohm-ruler4-night-2026-11-26")
P4 = os.path.join(ROOT, "prereg", "ohm_ruler4_night_2026-11-26.md")
BEFORE = "697ca450"                       # the fourth night's README before the home VS's corrections (c32e1f56)


def _git_show(rev, path):
    r = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        pytest.skip(f"git show {rev} is not available here")
    return r.stdout


# ---- 1. beside: the heading form, and no item is a failure -----------------------------------------------------------
def test_heading_form_and_values_list():
    prereg = "\n".join(["## Beside, never judged", "", "- **(e)**, the readout ruler.", "- **tau 0.2, 0.3**: words.",
                        "- **`results/<night>/qubits.csv`**, columns:", "  - device: the device", "  - arm: the cell",
                        "- 11-25's beside values (order, growth, (b'), sentinel) as declared then.", "", "## Next",
                        "- not an item"])
    heads = [DC.head_of(t)[1] for _, t in DC.beside_items(prereg)]
    assert heads == ["(e)", "tau 0.2, 0.3", "qubits.csv", "order", "growth", "(b')", "sentinel"]


@pytest.mark.skipif(not os.path.exists(P4), reason="the fourth night's declaration is not here")
def test_fourth_night_outlying_positions_missing_before_c32e1f56():
    prereg = open(P4, encoding="utf-8").read()
    old = DC.beside_coverage(prereg, _git_show(BEFORE, "results/ohm-ruler4-night-2026-11-26/README.md"))
    new = DC.beside_coverage(prereg, open(os.path.join(N4, "README.md"), encoding="utf-8").read())
    miss = lambda rows: {r["head"] for r in rows if r["checked"] and not r["found"]}
    assert len(old) == len(new) == 11
    assert "outlying positions" in miss(old) and "outlying positions" not in miss(new)


def test_no_item_fails(tmp_path):
    p, r = tmp_path / "p.md", tmp_path / "r.md"
    p.write_text("# a declaration without a beside list\n", encoding="utf-8")
    r.write_text("# a README\n", encoding="utf-8")
    res = subprocess.run([sys.executable, os.path.join(TOOLS, "declaration_check.py"), "beside", str(p), str(r)],
                         capture_output=True, text=True)
    assert res.returncode == 2 and "FAIL" in res.stdout


# ---- 2. check_readme_numbers: "at most" and ranges against the named record ----------------------------------------
def test_range_claims_and_values_under():
    u = "e_q from `or4/scores4.json` readout_pairs differ by at most 0.020; d ranges from +0.14 to +0.47 at t = 1 to 3."
    claims = CRN.range_claims(u)
    assert ("largest", "0.020") in [(k, c) for k, c, _ in claims]
    assert ("range", ("+0.14", "+0.47")) in [(k, c) for k, c, _ in claims]
    assert not any(c == ("1", "3") for _, c, _ in claims)          # "t = 1 to 3" is not a value range
    doc = {"readout_pairs": {"93": {"e_s00c00": 0.8, "difference": -0.02}, "102": {"e_s00c00": 0.85, "difference": 0.027}}}
    assert sorted(CRN.values_under(doc, "readout_pairs", "they differ by")) == [-0.02, 0.027]


@pytest.mark.skipif(not os.path.exists(os.path.join(N4, "or4", "scores4.json")), reason="the 11-26 record is not here")
def test_fourth_night_at_most_0020_is_caught(tmp_path):
    night = tmp_path / "ohm-ruler4-night-2026-11-26"
    shutil.copytree(os.path.join(N4, "or4"), night / "or4")
    (night / "README.md").write_text(_git_show(BEFORE, "results/ohm-ruler4-night-2026-11-26/README.md"), encoding="utf-8")
    r = CRN.check_night(str(night))
    hits = [m for m in r["mismatches"] if m["what"].startswith("largest")]
    assert len(hits) == 1 and hits[0]["readme"] == "0.020" and abs(hits[0]["record"] - 0.027) < 5e-4
    assert not [m for m in CRN.check_night(N4)["mismatches"] if m["what"].startswith(("largest", "range"))]


# ---- 3. qubits_across ----------------------------------------------------------------------------------------------
@pytest.mark.skipif(not os.path.exists(os.path.join(N4, "qubits.csv")), reason="the 11-26 record is not here")
def test_rebuilt_columns_equal_the_fourth_nights_qubits_csv():
    pytest.importorskip("qiskit")
    written = {(r["arm"], r["t"], r["position"]): r for r in QA.from_csv(N4)}
    rebuilt = {(r["arm"], r["t"], r["position"]): r for r in QA.from_record(N4)}
    assert set(written) == set(rebuilt) and len(written) == 126
    for k, w in written.items():
        b = rebuilt[k]
        assert w["physical"] == b["physical"]
        for c in ("mirror_z", "m_q", "e_q"):
            assert (w[c] is None and b[c] is None) or abs(w[c] - b[c]) <= 5e-4 + 1e-12, (k, c)
        if w["r_q"] is not None:
            assert abs(w["r_q"] - b["r_q"]) <= 5e-4 + 1e-12, k
        assert (w["MIRROR_LOW"], w["R_LOW"], w["R_HIGH"]) == (b["MIRROR_LOW"], b["R_LOW"], b["R_HIGH"]), k
