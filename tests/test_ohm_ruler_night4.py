"""Tests for gpu/ohm_ruler_night4.py (workplace Claude, 2026-11-26; author The Architect). No device, no sealed answers:
score4 reads test_ohm_ruler_night3's synthetic job (psf-os's job reader replaced by a stub) with readout records added,
whose <Z> are known exactly.

Fixed here:
  - a readout circuit returns its string (statevector) and measures in the order of the user records' labels;
  - gates alone shrink (readout ideal): (de) = sqrt(m e) equals the window's factor and AGREES, (e) reads 1;
  - the readout alone shrinks: (e) and (de) AGREE, (d) = sqrt(e) does not reach it, and (de) against (d) is SMALLER;
  - a one-sided readout shift cancels in the odd part (e_q is 1 - p01 - p10 only);
  - (a') leaves the low-mirror qubits outside the window out (tau 0.2, 0.3, 0.4 beside); NOT READ when fewer than half
    are kept; the direction with rho_a' judged, with rho_a beside;
  - qubits.csv keeps MIRROR LOW and R LOW as two columns;
  - OR4-2 is read only on its device and copy;
  - reading table C stands word for word in the draft.
"""
import csv
import json
import os
import sys

import numpy as np
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "gpu"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ORN4 = pytest.importorskip("ohm_ruler_night4")
pytest.importorskip("psf_os.job")
from test_ohm_ruler_night import _counts  # noqa: E402
from test_ohm_ruler_night3 import _job3  # noqa: E402

ORN = ORN4.ORN


def _job4(tmp_path, monkeypatch, e_of=None, offset=0.0, drow=4, device="stub", **kw):
    """_job3 plus the four readout records on the cell's positions. e_of(pos) gives e_q per position (default 1);
    offset shifts both strings of a pair the same way (a one-sided readout lean), which the odd part cancels."""
    import psf_os.job as J
    a = _job3(tmp_path, monkeypatch, **kw)
    read = dict(J.read(None, None))
    b = json.load(open(os.path.join(a.out, "build.json")))
    t = b["cycles"][0]
    pos = ORN.positions(t, "L")
    e = np.ones(len(pos)) if e_of is None else np.array(e_of(pos))
    for nm in ORN4.READOUT_STRINGS:
        sig = np.array([1 - 2 * int(b["strings"][nm][p]) for p in pos], dtype=float)
        read[f"p2d_readout_{nm}"] = (dict(psfos_job=dict(kind="user2d_readout"), labels=list(pos),
                                          points=[dict(input="r")], string=nm), {("r", "z"): _counts(
                                              np.clip(sig * e + offset, -1, 1), 10 ** 6)})
    b.update(readout=dict(strings=list(ORN4.READOUT_STRINGS), positions=list(pos), physical=list(pos), t=t),
             copy_of_F=dict(drow=drow), device=device)
    json.dump(b, open(os.path.join(a.out, "build.json"), "w"))
    os.makedirs(os.path.join(a.out, "job"), exist_ok=True)
    json.dump(dict(device=dict(source=dict(calibration_time="2026-11-26T00:00:00Z"))),
              open(os.path.join(a.out, "job", "manifest.json"), "w"))
    monkeypatch.setattr(J, "read", lambda jobd, runs: read)
    return a


def _s4(a):
    ORN4.cmd_score4(a)
    return json.load(open(os.path.join(a.out, "scores4.json")))


def test_readout_circuit_returns_its_string_in_label_order():
    from qiskit.quantum_info import Statevector
    qc = ORN4.readout_circuit(5, [4, 1, 3], "101", [3, 4, 1])
    ops = [i.operation.name for i in qc.data]
    assert ops.count("x") == 2 and ops.count("measure") == 3 and "cz" not in ops
    assert [qc.find_bit(i.qubits[0]).index for i in qc.data if i.operation.name == "measure"] == [3, 4, 1]
    probs = Statevector(qc.remove_final_measurements(inplace=False)).probabilities_dict()
    # qubit 4 and 3 in |1>, qubit 1 in |0> (Qiskit's string: qubit 0 rightmost)
    assert abs(probs.get("11000", 0.0) - 1.0) < 1e-12


def test_gates_alone_de_equals_the_window_factor(tmp_path, monkeypatch):
    res = _s4(_job4(tmp_path, monkeypatch, K=5, eta=0.002))
    for k, c in res["cells"].items():
        assert abs(c["e"]["rho"] - 1.0) < 1e-3
        assert np.allclose(c["de"]["rho_q"], 0.85, atol=1e-3)
        assert c["de"]["words"]["t"] == "AGREES", (k, c["de"])
        assert c["e"]["words"]["t"] == "DIFFERS"           # the readout ruler alone does not see the gates


def test_readout_alone_de_and_e_agree_d_does_not_reach(tmp_path, monkeypatch):
    e = 0.9
    a = _job4(tmp_path, monkeypatch, r_win=e, smirror_r2=lambda pos, win: [e] * len(pos),
              mirror=lambda pos, win: [e] * len(pos), e_of=lambda pos: [e] * len(pos), K=5, eta=0.002)
    res = _s4(a)
    s3 = json.load(open(os.path.join(a.out, "scores3.json")))
    for k, c in res["cells"].items():
        assert c["e"]["words"]["t"] == "AGREES" and c["de"]["words"]["t"] == "AGREES", (k, c)
        assert s3["cells"][k]["rulers"]["d"]["words"]["t"] == "DIFFERS"     # sqrt(0.9) = 0.949
        assert c["de_vs_d"] == "SMALLER"


def test_one_sided_readout_lean_cancels_in_the_odd_part(tmp_path, monkeypatch):
    res = _s4(_job4(tmp_path, monkeypatch, e_of=lambda pos: [0.9] * len(pos), offset=0.05, K=5, eta=0.002))
    for p, v in res["readout_pairs"].items():
        assert abs(v["e_s00c00"] - 0.9) < 2e-3 and abs(v["difference"]) < 2e-3


def test_a_prime_leaves_low_outside_qubits_out(tmp_path, monkeypatch):
    def low_out(pos, win):
        out = [p for p in pos if p not in win][:3]
        return [0.04 if p in out else 0.9 ** 2 for p in pos]
    a = _job4(tmp_path, monkeypatch, r_win=0.9, mirror=low_out, K=5, eta=0.002)
    t = json.load(open(os.path.join(a.out, "build.json")))["cycles"][0]
    pos, win = ORN.positions(t, "L"), ORN.window(t)
    out3 = [p for p in pos if p not in win][:3]
    res = _s4(a)
    for k, c in res["cells"].items():
        ap = c["a_prime"]
        assert sorted(ap["left_out"]) == sorted(out3) and ap["kept"] == len(pos) - 3
        assert ap["words"]["t"] == "AGREES", (k, ap)
        assert res["direction"][k]["judged_a_prime"]["word"] in ("NOT SEEN", "WINDOW SHRINKS LESS",
                                                                 "WINDOW SHRINKS MORE")
        assert set(res["tau_beside"][k]) == {"0.2", "0.3", "0.4"}


def test_a_prime_not_read_when_too_few_kept(tmp_path, monkeypatch):
    def most_low(pos, win):
        return [0.9 ** 2 if p in win else 0.04 for p in pos]
    res = _s4(_job4(tmp_path, monkeypatch, mirror=most_low, K=5, eta=0.002))
    for k, c in res["cells"].items():
        if 2 * len(ORN.window(3)) < len(ORN.positions(3, "L")):
            assert c["a_prime"]["words"]["t"] == "NOT READ", k


def test_qubits_csv_mirror_low_and_r_low_apart(tmp_path, monkeypatch):
    def one_low(pos, win):
        return [0.1 if p == win[1] else 0.85 ** 2 for p in pos]
    a = _job4(tmp_path, monkeypatch, mirror=one_low, K=5, eta=0.002)
    _s4(a)
    rows = list(csv.DictReader(open(os.path.join(a.out, "qubits.csv"), encoding="utf-8")))
    assert {"MIRROR_LOW", "R_LOW", "R_HIGH", "mirror_z", "m_q", "r_q", "e_q", "calibration_time", "copy_drow"} <= set(rows[0])
    low = [r for r in rows if r["MIRROR_LOW"] == "True"]
    assert len(low) == len(ORN.ARMS) and all(r["position"] == str(ORN.window(3)[1]) for r in low)
    assert all(r["R_LOW"] == "False" for r in low)     # its mirror is low, its r is not: two columns, two facts
    assert not any(r["R_LOW"] == "True" and r["R_HIGH"] == "True" for r in rows)
    assert {r["calibration_time"] for r in rows} == {"2026-11-26T00:00:00Z"}


def test_or4_2_read_only_on_its_device_and_copy():
    b = dict(device="ibm_fez", copy_of_F=dict(drow=4), cycles=[1, 3, 4])
    low = {f"{arm}_t4_L": {104: 0.01, 102: 0.2, 101: 0.9} for arm in ORN.ARMS}
    assert ORN4.or4_2(b, low)["word"] == "HELD"
    one = dict(low)
    one["A2_t4_L"] = {104: 0.01, 102: 0.31}
    assert ORN4.or4_2(b, one)["word"] == "NOT HELD"
    assert ORN4.or4_2(dict(b, device="ibm_kingston"), low)["word"] == "NOT READ"
    assert ORN4.or4_2(dict(b, copy_of_F=dict(drow=5)), low)["word"] == "NOT READ"
    gone = {k: {104: 0.0} for k in low}
    assert ORN4.or4_2(b, gone)["word"] == "NOT READ"


def test_reading_table_c_word_for_word_in_the_draft():
    p = os.path.join(ROOT, "prereg", "drafts-2026-11-26", "ohm_ruler4_night_DRAFT.md")
    if not os.path.exists(p):
        pytest.skip("draft not written yet")
    draft = open(p, encoding="utf-8").read()
    for (r, w), text in ORN4.READ_TABLE_C.items():
        lab = "a'" if r == "a_prime" else r
        assert f"| ({lab}) | {w} | {text} |" in draft, (r, w)
    for w, text in ORN4.READ_DE_VS_D.items():
        assert f"| {w} | {text} |" in draft, w
