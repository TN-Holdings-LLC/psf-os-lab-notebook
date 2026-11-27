"""Tests for tools/calib_compare.py's addendum A of 2026-11-27 (workplace VS; author The Architect): records in the
layout before 2026-11-03 read for the scan, edges of a ring without couplers. Every calibration value here is made by
hand: no real snapshot is read."""
import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import calib_compare as CC  # noqa: E402

OLD_SCAN = os.path.join(ROOT, "results", "device-2026-10-31-fez", "job")


def test_ring_edges_without_couplers():
    ring = [5, 3, 9, 7]
    assert CC._edges_in(sorted(ring), [], ring) == [(3, 5), (3, 9), (5, 7), (7, 9)]
    assert CC._edges_in([1, 2, 3], [(1, 2), (2, 3), (3, 4)]) == [(1, 2), (2, 3)]   # couplers win when present
    assert CC._edges_in([1, 2, 3], []) == []                                       # no ring, no couplers


def test_marks_on_a_ring_without_couplers():
    snap = CC.parse_snapshot(dict(qubits=[[dict(name="readout_error", value=0.01), dict(name="T1", value=100.0),
                                           dict(name="T2", value=100.0)]] * 8,
                                  gates=[dict(gate="cz", qubits=[3, 5], parameters=[dict(name="gate_error", value=0.2)]),
                                         dict(gate="cz", qubits=[5, 7], parameters=[dict(name="gate_error", value=0.01)])],
                                  last_update_date=None))
    ring = [3, 5, 7]
    row = dict(set=sorted(ring), edges=CC._edges_in(sorted(ring), [], ring), found=[3])
    m, na = CC.marks(row, snap)
    assert m["cz"] == {3, 5} and "cz" not in na                     # the edge (3, 7) has no value: left out


@pytest.mark.skipif(not os.path.exists(os.path.join(OLD_SCAN, "raw_counts.json.gz")),
                    reason="the 2026-10-31 fez record is not here")
def test_old_layout_scan_is_read():
    meta = dict(night="device-2026-10-31-fez", device="ibm_fez", job_id="dbilc0ghoj4c73b6fkq0",
                job_created_utc="2026-10-31T02:44:02Z")
    cwd = os.getcwd()
    os.chdir(ROOT)
    try:
        rows = CC.scan_observe_findings("results/device-2026-10-31-fez/job", meta, [], "results/device-2026-10-31-fez/job")
    finally:
        os.chdir(cwd)
    assert [r["context"] for r in rows] == ["n20", "n36", "n40", "n72"]
    assert all(r["kind"] == "scan_listed" and len(r["edges"]) == len(r["set"]) for r in rows)   # a ring: n edges
    assert sum(len(r["found"]) for r in rows) > 0
