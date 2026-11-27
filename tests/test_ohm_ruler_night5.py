"""Tests for gpu/ohm_ruler_night5.py (workplace Claude, 2026-11-27; author The Architect). No device, no sealed answers:
score5 reads test_ohm_ruler_night3's synthetic job (psf-os's job reader replaced by a stub) with the six readout
records added (s00 and c00 at the head and the tail, s01 and c01 at the tail), whose <Z> are known exactly.

Fixed here:
  - the readout records' names sort as planned: the head pair before ksent_ and p2d_, the tail ones after p2d_;
  - e_q is the mean of the head and tail pairs; tail minus head is written beside, as is s01/c01 minus s00/c00;
  - gates alone shrink: (de) equals the window's factor and AGREES; the readout alone: (de) AGREES, (d) does not;
  - qubits.csv carries e_head, e_tail and r_over_e = r_q / e_q, R_LOW and R_HIGH False at t = 1;
  - OR5-2 is read only on its device and copy, on all four qubits;
  - the reading tables stand word for word in the draft.
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

ORN5 = pytest.importorskip("ohm_ruler_night5")
pytest.importorskip("psf_os.job")
from test_ohm_ruler_night import _counts  # noqa: E402
from test_ohm_ruler_night3 import _job3  # noqa: E402

ORN = ORN5.ORN


def _job5(tmp_path, monkeypatch, e_head=None, e_tail=None, e_nb=None, drow=4, device="stub", **kw):
    """_job3 plus the six readout records. e_head / e_tail / e_nb (pos -> list) give e_q of the head pair, the tail
    s00/c00 pair and the tail s01/c01 pair (default 1)."""
    import psf_os.job as J
    a = _job3(tmp_path, monkeypatch, **kw)
    read = dict(J.read(None, None))
    b = json.load(open(os.path.join(a.out, "build.json")))
    t = b["cycles"][0]
    pos = ORN.positions(t, "L")
    one = np.ones(len(pos))
    ev = {("s00", "head"): e_head, ("c00", "head"): e_head, ("s00", "tail"): e_tail, ("c00", "tail"): e_tail,
          ("s01", "tail"): e_nb, ("c01", "tail"): e_nb}
    for name, nm, place in ORN5.READOUT:
        f = ev[(nm, place)]
        e = one if f is None else np.array(f(pos))
        sig = np.array([1 - 2 * int(b["strings"][nm][p]) for p in pos], dtype=float)
        read[name] = (dict(psfos_job=dict(kind="user2d_readout"), labels=list(pos), points=[dict(input="r")],
                           string=nm, place=place), {("r", "z"): _counts(np.clip(sig * e, -1, 1), 10 ** 6)})
    b.update(readout=dict(records=[list(r) for r in ORN5.READOUT], positions=list(pos), physical=list(pos), t=t),
             copy_of_F=dict(drow=drow), device=device)
    json.dump(b, open(os.path.join(a.out, "build.json"), "w"))
    os.makedirs(os.path.join(a.out, "job"), exist_ok=True)
    json.dump(dict(device=dict(source=dict(calibration_time="2026-11-27T00:00:00Z"))),
              open(os.path.join(a.out, "job", "manifest.json"), "w"))
    monkeypatch.setattr(J, "read", lambda jobd, runs: read)
    return a


def _s5(a):
    ORN5.cmd_score5(a)
    return json.load(open(os.path.join(a.out, "scores5.json")))


def test_readout_names_sort_at_the_head_and_the_tail():
    others = ["ksent_n40_D24-fold_rule", "p2d_A0_t1_L_c00", "p2d_A2_t4_L_s08_smirror", "p2d_A2_t4_L_s08"]
    names = sorted(others + [r[0] for r in ORN5.READOUT])
    heads = [r[0] for r in ORN5.READOUT if r[2] == "head"]
    tails = [r[0] for r in ORN5.READOUT if r[2] == "tail"]
    assert names[:len(heads)] == sorted(heads) and names[-len(tails):] == sorted(tails)
    assert sum(1 for r in ORN5.READOUT if r[1] in ("s00", "c00")) == 4 and len(ORN5.READOUT) == 6


def test_e_is_the_mean_of_head_and_tail_and_the_changes_are_beside(tmp_path, monkeypatch):
    res = _s5(_job5(tmp_path, monkeypatch, e_head=lambda pos: [0.94] * len(pos),
                    e_tail=lambda pos: [0.90] * len(pos), e_nb=lambda pos: [0.88] * len(pos), K=5, eta=0.002))
    for p, v in res["readout_beside"].items():
        assert abs(v["e_head"] - 0.94) < 2e-3 and abs(v["e_tail"] - 0.90) < 2e-3
        assert abs(v["tail_minus_head"] + 0.04) < 3e-3 and v["tail_minus_head_se"] > 0
        assert abs(v["s01_minus_s00_tail"] + 0.02) < 3e-3
    for k, c in res["cells"].items():
        assert abs(c["e"]["rho"] - 0.92) < 2e-3


def test_gates_alone_and_readout_alone(tmp_path, monkeypatch):
    res = _s5(_job5(tmp_path, monkeypatch, K=5, eta=0.002))
    for k, c in res["cells"].items():
        assert np.allclose(c["de"]["rho_q"], 0.85, atol=1e-3) and c["de"]["words"]["t"] == "AGREES", (k, c["de"])
    e = 0.9
    tmp2 = tmp_path / "ro"
    tmp2.mkdir()
    a = _job5(tmp2, monkeypatch, r_win=e, smirror_r2=lambda pos, win: [e] * len(pos),
              mirror=lambda pos, win: [e] * len(pos), e_head=lambda pos: [e] * len(pos),
              e_tail=lambda pos: [e] * len(pos), K=5, eta=0.002)
    res = _s5(a)
    s3 = json.load(open(os.path.join(a.out, "scores3.json")))
    for k, c in res["cells"].items():
        assert c["de"]["words"]["t"] == "AGREES" and s3["cells"][k]["rulers"]["d"]["words"]["t"] == "DIFFERS"
        assert c["de_vs_d"] == "SMALLER"


def test_qubits_csv_r_over_e_and_r_columns(tmp_path, monkeypatch):
    a = _job5(tmp_path, monkeypatch, e_head=lambda pos: [0.9] * len(pos), e_tail=lambda pos: [0.9] * len(pos),
              K=5, eta=0.002)
    _s5(a)
    rows = list(csv.DictReader(open(os.path.join(a.out, "qubits.csv"), encoding="utf-8")))
    assert {"e_head", "e_tail", "r_over_e", "R_LOW", "R_HIGH", "MIRROR_LOW"} <= set(rows[0])
    for r in rows:
        if r["r_q"] != "":
            assert abs(float(r["r_over_e"]) - float(r["r_q"]) / float(r["e_q"])) < 2e-3
        assert all(len(v.split(".")[1]) <= 3 for v in (r["mirror_z"], r["m_q"], r["e_q"]) if "." in v)


def test_or5_2_on_its_device_and_copy_only():
    b = dict(device="ibm_fez", copy_of_F=dict(drow=4), cycles=[1, 3, 4])
    low = {f"{arm}_t4_L": {101: 0.1, 102: 0.0, 103: 0.2, 104: -0.1} for arm in ORN.ARMS}
    assert ORN5.or5_2(b, low)["word"] == "HELD"
    one = dict(low)
    one["A2_t4_L"] = {101: 0.31, 102: 0.0, 103: 0.2, 104: -0.1}
    assert ORN5.or5_2(b, one)["word"] == "NOT HELD"
    assert ORN5.or5_2(dict(b, device="ibm_kingston"), low)["word"] == "NOT READ"
    assert ORN5.or5_2(dict(b, copy_of_F=dict(drow=3)), low)["word"] == "NOT READ"
    gone = {k: {102: 0.0, 103: 0.0, 104: 0.0} for k in low}
    assert ORN5.or5_2(b, gone)["word"] == "NOT READ"


def test_reading_tables_word_for_word_in_the_draft():
    p = os.path.join(ROOT, "prereg", "drafts-2026-11-27", "ohm_ruler5_night_DRAFT.md")
    if not os.path.exists(p):
        pytest.skip("draft not written yet")
    draft = open(p, encoding="utf-8").read()
    for (r, w), text in ORN5.READ_TABLE_C.items():
        lab = "a'" if r == "a_prime" else r
        assert f"| ({lab}) | {w} | {text} |" in draft, (r, w)
    for (cls, w), text in ORN5.READ_EXPECTED.items():
        assert f"| {cls} | {w} | {text} |" in draft, (cls, w)


def test_expect_table_equals_expect5():
    import subprocess
    out = subprocess.run([sys.executable, os.path.join(ROOT, "notes", "ohm_ruler5_2026-11-27", "expect5.py"), "--json"],
                         capture_output=True, text=True, check=True).stdout
    got = {tuple((k.split("|")[0], int(k.split("|")[1]))): v for k, v in json.loads(out).items()}
    for key, cls in ORN5.EXPECT.items():
        assert got[key] == cls, key
    assert set(k for k in got if k[0] in ("de", "a_prime", "e")) == set(ORN5.EXPECT)


def test_cells_carry_the_expectation(tmp_path, monkeypatch):
    res = _s5(_job5(tmp_path, monkeypatch, K=5, eta=0.002))
    for k, c in res["cells"].items():
        assert c["de"]["expected"] == "EXPECTED TO AGREE"
        assert c["de"]["against_expectation"] == ORN5.READ_EXPECTED[("EXPECTED TO AGREE", c["de"]["words"]["t"])]
