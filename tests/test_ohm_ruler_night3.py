"""Tests for gpu/ohm_ruler_night3.py (workplace Claude, 2026-11-25; author The Architect). No device, no sealed answers:
score3 reads a synthetic job (psf-os's job reader replaced by a stub) whose <Z> are known exactly.

Fixed here:
  - the words follow rule 4 (t quantile, K - 1 dof) and rule 5 (SE 0: NOT READ), with the 2 SE word beside;
  - the string mirror returns its string (statevector, a small circuit);
  - one uniform shrink: every ruler AGREES, and (d) equals (b) when the string mirrors shrink as the |0> mirror;
  - candidate 1 leaves a low mirror qubit out of the mean, and reads NOT READ when fewer than half are left;
  - candidate 3 reads WINDOW SHRINKS LESS when the window keeps more than the circuit's total;
  - score3's (a), (b) and the one-factor test equal the declared tool's.
"""
import json
import math
import os
import sys

import numpy as np
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "gpu"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ORN3 = pytest.importorskip("ohm_ruler_night3")
pytest.importorskip("psf_os.job")
from test_ohm_ruler_night import _counts, _exact  # noqa: E402

ORN = ORN3.ORN


def test_words_rule4_rule5():
    assert ORN3.word(0.0, 0.0, 7) == {"t": "NOT READ", "2se": "NOT READ"}
    assert ORN3.word(0.01, float("nan"), 7)["t"] == "NOT READ"
    w = ORN3.word(2.2, 1.0, 7)                      # between 2 SE and 2.447 SE
    assert w == {"t": "AGREES", "2se": "DIFFERS"}
    assert ORN3.word(2.5, 1.0, 7) == {"t": "DIFFERS", "2se": "DIFFERS"}
    assert ORN3.word(2.2, 1.0, 9)["t"] == "AGREES" and ORN3.word(2.35, 1.0, 9)["t"] == "DIFFERS"   # 2.306


def test_pairs_by_t():
    assert ORN3.pairs_by_t(["4:9"], (1, 3, 4), 9) == {1: 9, 3: 9, 4: 9}
    assert ORN3.pairs_by_t(None, (1, 3), 7) == {1: 7, 3: 7}
    with pytest.raises(SystemExit):
        ORN3.pairs_by_t(["4:9"], (1, 3, 4), 7)


def test_string_mirror_returns_the_string():
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    body = QuantumCircuit(3)
    body.x([0, 2])                                   # the string 1 0 1 on qubits 0, 1, 2
    body.h(1)
    body.cz(0, 1)
    body.rx(0.7, 2)
    body.cz(1, 2)
    m = QuantumCircuit(3, 3)
    m.compose(body, inplace=True)
    m.barrier()
    m.compose(body.inverse(), inplace=True)
    m.measure([0, 1, 2], [0, 1, 2])
    sm = ORN3.string_mirror(m, [0, 2])
    assert [i.operation.name for i in sm.data][-3:] == ["measure"] * 3
    nm = sm.remove_final_measurements(inplace=False)
    probs = Statevector(nm).probabilities_dict()
    assert abs(probs.get("101", 0.0) - 1.0) < 1e-12


def _job3(tmp_path, monkeypatch, r_win=0.85, r_out=None, eta=0.02, mirror=None, smirror_r2=None, K=3, t=3):
    """A synthetic plan-B-like job at one t with |0> mirrors and string mirrors (s00, c00) per arm. The mirrors carry
    10^6 shots: the comonotone counts move every qubit together, which would make their shot SE far larger than a
    device's."""
    import psf_os.job as J
    import psf_os.sentinel as SN
    import psf_os.user2d as U
    r_out = r_win if r_out is None else r_out
    strs, _ = ORN.strings(K, [t], ["L"])
    by = dict(strs)
    pos, win = ORN.positions(t, "L"), ORN.window(t)
    fac = np.array([r_win if p in win else r_out for p in pos])
    shots = 1000
    items, ans, read = {}, {}, {}
    for arm in ORN.ARMS:
        for k in range(K):
            ez = _exact(by[f"s{k:02d}"], pos, win, 0.1 + 0.1 * k)
            for nm, zex in ((f"s{k:02d}", ez), (f"c{k:02d}", -ez)):
                tg = ORN.tag(arm, t, "L", nm)
                items[tg] = dict(given_labels=list(pos), positions=list(pos), physical=list(pos))
                ans[tg] = {str(p): float(v) for p, v in zip(pos, zex)}
                zd = fac * zex
                if eta:
                    j = pos.index(win[0])
                    sh = eta * (k - (K - 1) / 2)
                    zd = zd.copy()
                    zd[j] += sh if nm.startswith("s") else -sh
                read[tg] = (dict(psfos_job=dict(kind="user2d"), labels=list(pos), points=[dict(input="x")], tag=tg),
                            {("x", "z"): _counts(zd, shots)})
        mt = ORN.tag(arm, t, "L", "s00")
        zm = fac ** 2 if mirror is None else np.array(mirror(pos, win))
        read[mt + "_mirror"] = (dict(psfos_job=dict(kind="user2d_mirror"), labels=list(pos), points=[dict(input="x")],
                                     tag=mt), {("x", "z"): _counts(zm, 10 ** 6)})
        s2 = fac ** 2 if smirror_r2 is None else np.array(smirror_r2(pos, win))
        for nm in ("s00", "c00"):
            sig = np.array([1 - 2 * int(by[nm][p]) for p in pos], dtype=float)
            tg = ORN.tag(arm, t, "L", nm)
            read[tg + "_smirror"] = (dict(psfos_job=dict(kind="user2d_smirror"), labels=list(pos),
                                          points=[dict(input="x")], tag=tg), {("x", "z"): _counts(s2 * sig, 10 ** 6)})
    out = tmp_path / "out"
    out.mkdir()
    json.dump(dict(device="stub", items=items, strings={n: "".join(map(str, b)) for n, b in strs}, cycles=[t],
                   forms=["L"], shots=shots, smirrors=[]), open(out / "build.json", "w"))
    json.dump(dict(z=ans), open(tmp_path / "ans.json", "w"))
    monkeypatch.setattr(J, "read", lambda jobd, runs: read)
    monkeypatch.setattr(U, "_tag_of", lambda name, rec: rec["tag"])
    monkeypatch.setattr(SN, "verdict", lambda jobd, runs: dict(status="stub"))
    import argparse
    return argparse.Namespace(out=str(out), answers=str(tmp_path / "ans.json"), tau=ORN3.TAU)


def _s3(a):
    ORN3.cmd_score3(a)
    return json.load(open(os.path.join(a.out, "scores3.json")))


def test_uniform_shrink_every_ruler_agrees_and_d_equals_b(tmp_path, monkeypatch):
    res = _s3(_job3(tmp_path, monkeypatch))
    for k, c in res["cells"].items():
        R = c["rulers"]
        for r in ("a", "b", "c", "d", "d1", "b_tau", "c_tau", "d_tau", "d1_tau"):
            assert R[r]["words"]["t"] == "AGREES", (k, r, R[r])
        assert abs(R["d"]["d"] - R["b"]["d"]) < 1e-12
        assert abs(R["d"]["rho"] - 0.85) < 1e-12 and abs(R["c"]["rho"] - 0.85) < 1e-12


def test_candidate1_leaves_a_low_qubit_out_and_reads_not_read_when_too_few(tmp_path, monkeypatch):
    def one_low(pos, win):
        return [0.1 if p == win[1] else 0.85 ** 2 for p in pos]
    res = _s3(_job3(tmp_path, monkeypatch, mirror=one_low, K=5, eta=0.002))
    for k, c in res["cells"].items():
        R = c["rulers"]
        assert R["c_tau"]["left_out"] == [ORN.window(3)[1]] and R["c_tau"]["kept"] == 4
        assert R["b_tau"]["left_out"] == [ORN.window(3)[1]]
        assert R["c_tau"]["words"]["t"] == "AGREES"
        assert R["c"]["words"]["t"] == "DIFFERS"          # the low qubit pulls the window's mean down
    tmp2 = tmp_path / "b"
    tmp2.mkdir()

    def most_low(pos, win):
        return [0.1 if p in win[:3] else 0.85 ** 2 for p in pos]
    res = _s3(_job3(tmp2, monkeypatch, mirror=most_low, K=5, eta=0.002))
    for k, c in res["cells"].items():
        assert c["rulers"]["c_tau"]["words"]["t"] == "NOT READ"
        assert c["rulers"]["c_tau"]["kept"] == 2 and c["rulers"]["c_tau"]["of"] == 5


def test_candidate3_window_shrinks_less(tmp_path, monkeypatch):
    res = _s3(_job3(tmp_path, monkeypatch, r_win=0.9, r_out=0.8, eta=0.002, K=5))
    for k, v in res["direction"].items():
        assert v["r_minus_rho_a"] > 0
        assert v["word"] == "WINDOW SHRINKS LESS", (k, v)
        assert res["cells"][k]["rulers"]["a"]["words"]["t"] == "DIFFERS"


def test_score3_equals_declared_score(tmp_path, monkeypatch):
    a = _job3(tmp_path, monkeypatch)
    res3 = _s3(a)
    ORN.cmd_score(a)
    dec = json.load(open(os.path.join(a.out, "scores.json")))
    for k, c in dec["cells"].items():
        R = res3["cells"][k]["rulers"]
        assert abs(R["a"]["d"] - c["d_a"]) < 1e-12 and abs(2 * R["a"]["se"] - c["d_a_2se"]) < 1e-12
        assert abs(R["b"]["d"] - c["d_b"]) < 1e-12 and abs(2 * R["b"]["se"] - c["d_b_2se"]) < 1e-12
        assert abs(res3["cells"][k]["W_ratio"] - c["W_ratio"]) < 1e-12
    for k, u in dec["uniform"].items():
        assert abs(res3["uniform"][k]["p"] - u["p"]) < 1e-12 and res3["uniform"][k]["word"] == u["word"]


def test_no_scatter_reads_not_read(tmp_path, monkeypatch):
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        res = _s3(_job3(tmp_path, monkeypatch, r_win=1.0, eta=0.0))
    for k, c in res["cells"].items():
        assert c["rulers"]["a"]["words"]["t"] == "NOT READ", k
    for k, u in res["uniform"].items():
        assert u["word"] == "NOT READ", k
    for k, v in res["direction"].items():
        assert v["word"] == "NOT READ", k


def test_candidate1_outside_window_form(tmp_path, monkeypatch):
    # low |0> mirror values outside the window are left out of (b_out); a low value inside the window is kept
    def low_out(pos, win):
        out = [p for p in pos if p not in win][:3]
        return [0.1 if p in out else 0.85 ** 2 for p in pos]
    res = _s3(_job3(tmp_path, monkeypatch, mirror=low_out, K=5, eta=0.002))
    for k, c in res["cells"].items():
        R = c["rulers"]
        assert len(R["b_out"]["left_out"]) == 3 and not set(R["b_out"]["left_out"]) & set(ORN.window(3))
        assert R["b_out"]["words"]["t"] == "AGREES" and R["b"]["words"]["t"] == "DIFFERS", k
    tmp2 = tmp_path / "in"
    tmp2.mkdir()

    def low_in(pos, win):
        return [0.1 if p == win[1] else 0.85 ** 2 for p in pos]
    res = _s3(_job3(tmp2, monkeypatch, mirror=low_in, K=5, eta=0.002))
    for k, c in res["cells"].items():
        assert not c["rulers"]["b_out"].get("left_out"), k
        assert c["rulers"]["b_tau"]["left_out"] == [ORN.window(3)[1]]


def test_reading_tables_word_for_word_in_the_draft():
    draft = open(os.path.join(ROOT, "prereg", "drafts-2026-11-25", "ohm_ruler3_night_DRAFT.md")).read()
    for (r, w), text in ORN3.READ_TABLE_A.items():
        assert f"| ({r}) | {w} | {text} |" in draft, (r, w)
    for (d, w), text in ORN3.READ_TABLE_B.items():
        assert f"| {d} | {w} | {text} |" in draft, (d, w)


def test_scores3_tables_and_sentinel_beside(tmp_path, monkeypatch):
    res = _s3(_job3(tmp_path, monkeypatch, K=5, eta=0.002))
    for k, v in res["tables"].items():
        assert v["A"]["d"] == ORN3.READ_TABLE_A[("d", res["cells"][k]["rulers"]["d"]["words"]["t"])]
        assert v["B"] in ORN3.READ_TABLE_B.values()
