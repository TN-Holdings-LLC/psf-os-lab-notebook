"""Tests for tools/calib_compare.py (workplace VS, 2026-11-26; author The Architect). Every calibration value here is
made by hand: no real snapshot is read."""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import calib_compare as CC  # noqa: E402


def _snapshot(readout, t1, t2, cz):
    """A BackendProperties.to_dict()-like snapshot from hand-made values (lists by qubit; cz by edge)."""
    qubits = [[dict(name="readout_error", value=r), dict(name="T1", value=a), dict(name="T2", value=b)]
              for r, a, b in zip(readout, t1, t2)]
    gates = [dict(gate="cz", qubits=list(e), parameters=[dict(name="gate_error", value=v)]) for e, v in cz.items()]
    return dict(qubits=qubits, gates=gates, last_update_date="2026-11-20T08:00:00+00:00")


def test_k_of():
    assert [CC.k_of(n) for n in (0, 1, 5, 16, 22, 40)] == [0, 1, 1, 2, 3, 5]


def test_worst_with_ties_and_none():
    assert CC.worst({1: 0.1, 2: 0.3, 3: 0.3, 4: None}, 1, True) == {2, 3}
    assert CC.worst({1: 50.0, 2: 10.0, 3: 80.0}, 1, False) == {2}
    assert CC.worst({1: None}, 1, True) == set()


def test_parse_snapshot_and_marks():
    snap = CC.parse_snapshot(_snapshot(readout=[0.01] * 8 + [0.2], t1=[100.0] * 9, t2=[100.0] * 4 + [5.0] + [100.0] * 4,
                                       cz={(0, 1): 0.003, (1, 2): 0.05, (2, 3): 0.003}))
    assert snap["edges"][(1, 2)] == 0.05 and snap["qubits"][8]["readout_error"] == 0.2
    row = dict(set=list(range(9)), edges=[[0, 1], [1, 2], [2, 3]], found=[8, 4, 6])
    m, na = CC.marks(row, snap)
    assert m["readout_error"] == {8} and m["T2"] == {4} and m["cz"] == {1, 2} and na == []
    assert m["T1"] == set(range(9))                       # all tied: every qubit is at the worst value
    assert m["any"] >= {1, 2, 4, 8}


def test_score_counts_both_ways():
    snap = CC.parse_snapshot(_snapshot(readout=[0.01] * 8 + [0.2], t1=[100.0 + i for i in range(9)],
                                       t2=[100.0] * 4 + [5.0] + [100.0] * 4, cz={(0, 1): 0.003, (1, 2): 0.05}))
    rows = [dict(night="n", device="ibm_x", job_id="j1", job_created_utc="2026-11-20T10:00:00Z", kind="mirror_low",
                 context="c", set=list(range(9)), edges=[[0, 1], [1, 2]], found=[8, 6], source="hand")]
    res = CC.score(rows, {"j1": snap})
    t = {r["column"]: r for r in res["table"]}
    assert (t["readout_error"]["ibm_hit"], t["readout_error"]["ibm_miss"], t["readout_error"]["our_miss"]) == (1, 1, 0)
    assert (t["T2"]["ibm_hit"], t["T2"]["our_miss"]) == (0, 1)                     # qubit 4 marked, read normal
    assert (t["cz"]["ibm_hit"], t["cz"]["our_miss"]) == (0, 2)                     # edge (1, 2) marks 1 and 2
    assert t["T1"]["ibm_hit"] == 0 and t["T1"]["our_miss"] == 1                    # qubit 0 is the lowest T1
    assert t["any"]["ibm_hit"] == 1 and t["any"]["ibm_miss"] == 1
    assert abs(res["snapshot_age_hours"][0]["hours"] - 2.0) < 1e-9


def test_score_not_available_and_missing_snapshot():
    snap = CC.parse_snapshot(dict(qubits=[], gates=[], last_update_date=None))
    rows = [dict(night="n", device="d", job_id="j1", job_created_utc="2026-11-20T10:00:00Z", kind="r_low", context="c",
                 set=[3, 4], edges=[[3, 4]], found=[3], source="hand"),
            dict(night="n", device="d", job_id="j2", job_created_utc="2026-11-20T10:00:00Z", kind="r_low", context="c",
                 set=[3, 4], edges=[], found=[3], source="hand")]
    res = CC.score(rows, {"j1": snap})
    assert res["jobs_without_snapshot"] == ["j2"]
    assert all(r.get("not_available_sets") == 1 for r in res["table"] if r["column"] != "any")


def test_findings_never_open_a_calibration_file(monkeypatch, tmp_path):
    """findings reads no fetch_in/*/dev file and no calib_history file: opening one raises here."""
    import builtins
    real_open = builtins.open

    def guarded(path, *a, **k):
        p = str(path).replace("\\", "/")
        assert "/fetch_in/" not in p and "calib_history" not in p, p
        return real_open(path, *a, **k)
    monkeypatch.setattr(builtins, "open", guarded)
    night = os.path.join(ROOT, "results", "ohm-ruler-night-2026-11-24")
    if not os.path.exists(os.path.join(night, "or", "job", "manifest.json")):
        import pytest
        pytest.skip("the 11-24 record is not here")
    raw = json.load(real_open(os.path.join(night, "or", "job", "raw_counts.json")))
    t = [dict(night="ohm-ruler-night-2026-11-24", record="results/ohm-ruler-night-2026-11-24/or/job",
              device="ibm_fez", job_created_utc=raw.get("metrics", {}).get("timestamps", {}).get("created", ""),
              job_id=raw["job_id"])]
    cwd = os.getcwd()
    os.chdir(ROOT)
    try:
        rows, skipped = CC.findings(t, ".")
    finally:
        os.chdir(cwd)
    kinds = {r["kind"] for r in rows}
    assert not skipped and {"r_low"} <= kinds and ({"mirror_low", "mirror_too_deep"} & kinds)
