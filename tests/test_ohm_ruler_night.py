"""Tests for the declared tool gpu/ohm_ruler_night.py (2026-11-24) and its next-night companion gpu/ohm_ruler_night2.py
(workplace Claude; author The Architect). No device, no sealed answers: the scoring tests feed the declared `score`
a synthetic job (psf-os's job reader replaced by a stub) whose <Z> are known.

Fixed here:
  - the string rule gives the same strings (plan B's, by hash), each pair complementary, each cone |T0| >= 6;
  - the circuit's total <Z> equals T0 (fSim and RZ keep the number of 1s), on the tool's own answer paths;
  - without noise, and with one uniform factor, every read ruler AGREES and the ruled W equals the exact W;
  - the uniformity test's chi2 and p equal a hand computation (scipy's chi2 beside the tool's own survival function);
  - ruler (c) of ohm_ruler_night2 equals ruler (b) when the mirror is uniform, and its (a), (b) equal the declared ones.
"""
import argparse
import hashlib
import json
import math
import os
import sys

import numpy as np
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "gpu"))

ORN = pytest.importorskip("ohm_ruler_night")
pytest.importorskip("psf_os.job")

PLAN_B_SHA256 = "8324e787b4f00fa03f99e39881493196356444e5356a36144899abe0e495197f"


# ------------------------------------------------------------------------------------------------------ strings

def test_strings_plan_b_fixed_complementary_and_bounded():
    s, tried = ORN.strings(7, [1, 3, 4], ["L"])
    assert tried == 26
    assert hashlib.sha256(json.dumps(s).encode()).hexdigest() == PLAN_B_SHA256
    again, _ = ORN.strings(7, [1, 3, 4], ["L"])
    assert again == s
    by = dict(s)
    reg = ORN.regions([1, 3, 4], ["L"])
    assert set(reg) == {"cone_t3", "cone_t4"}
    for k in range(7):
        b, c = by[f"s{k:02d}"], by[f"c{k:02d}"]
        assert [1 - x for x in b] == c
        for qs in reg.values():
            assert abs(ORN.t0(b, qs)) >= ORN.THRESH["cone"]


def test_strings_more_pairs_extend_the_same_draws():
    s7, _ = ORN.strings(7, [1, 3, 4], ["L"])
    s9, tried = ORN.strings(9, [1, 3, 4], ["L"])
    assert tried == 31
    assert s9[:14] == s7


# ------------------------------------------------------------------------------------------------ total = T0

@pytest.mark.parametrize("t", [1, 3, 4])
def test_total_equals_t0_free_fermions_full_chain(t):
    s, _ = ORN.strings(2, [3, 4], ["L"])
    for _, bits in s:
        z = ORN.OA.z_free(ORN.N, t, bits)
        assert abs(float(np.sum(z)) - ORN.t0(bits, range(ORN.N))) < 1e-10


@pytest.mark.parametrize("arm", ["A1", "A2"])
def test_total_equals_t0_light_cone_t1(arm):
    s, _ = ORN.strings(1, [3, 4], ["L"])
    for _, bits in s:
        z = ORN.OW.z_cone_quimb(arm, 1, bits)
        assert abs(float(np.sum(z)) - ORN.t0(bits, ORN.positions(1, "L"))) < 1e-8


# ----------------------------------------------------------------------------------------- a synthetic job

def _counts(z, n_shots):
    """Weighted bit strings with exactly the per-qubit <Z> given (a comonotone joint: qubit k is 1 when u < p1_k)."""
    p1 = (1 - np.asarray(z)) / 2
    cuts = sorted(set([0.0, 1.0] + [float(x) for x in p1]))
    out = {}
    n = len(z)
    for lo, hi in zip(cuts[:-1], cuts[1:]):
        if hi - lo <= 0:
            continue
        u = (lo + hi) / 2
        key = "".join("1" if u < p1[n - 1 - j] else "0" for j in range(n))
        out[key] = out.get(key, 0.0) + (hi - lo) * n_shots
    return out


def _exact(bits, pos, win, delta):
    """A made-up exact <Z> with sum_q O_q = T0: the initial +-1, a window qubit at +1 and an outside qubit at -1 pulled
    in by delta (a transfer out of the window: W_exact = delta / 2, the total kept)."""
    z = np.array([1.0 - 2 * bits[p] for p in pos])
    plus = [i for i, p in enumerate(pos) if p in win and bits[p] == 0]
    minus = [i for i, p in enumerate(pos) if p not in win and bits[p] == 1]
    if plus and minus:
        z[plus[0]] *= 1 - delta
        z[minus[0]] *= 1 - delta
    return z


def _job(tmp_path, monkeypatch, r=1.0, eta=0.0, mirror_shape=None, K=3, t=3):
    """Write build.json and answers for plan-B-like cells (form L, one t) and stub psf-os's reader."""
    import psf_os.job as J
    import psf_os.sentinel as SN
    import psf_os.user2d as U
    strs, _ = ORN.strings(K, [t], ["L"])
    by = dict(strs)
    pos, win = ORN.positions(t, "L"), ORN.window(t)
    shots = 1000
    items, ans, read = {}, {}, {}
    for arm in ORN.ARMS:
        for k in range(K):
            ez = _exact(by[f"s{k:02d}"], pos, win, 0.1 + 0.1 * k)
            for nm, zex in ((f"s{k:02d}", ez), (f"c{k:02d}", -ez)):
                tg = ORN.tag(arm, t, "L", nm)
                items[tg] = dict(given_labels=list(pos), positions=list(pos))
                ans[tg] = {str(p): float(v) for p, v in zip(pos, zex)}
                zd = r * zex
                if eta:
                    j = pos.index(win[0])
                    shift = eta * (k - (K - 1) / 2)
                    zd = zd.copy()
                    zd[j] += shift if nm.startswith("s") else -shift
                read[tg] = (dict(psfos_job=dict(kind="user2d"), labels=list(pos), points=[dict(input="x")], tag=tg),
                            {("x", "z"): _counts(zd, shots)})
        mt = ORN.tag(arm, t, "L", "s00")
        zm = np.full(len(pos), r * r) if mirror_shape is None else np.array(mirror_shape(pos, win))
        read[mt + "_mirror"] = (dict(psfos_job=dict(kind="user2d_mirror"), labels=list(pos), points=[dict(input="x")],
                                     tag=mt), {("x", "z"): _counts(zm, shots)})
    out = tmp_path / "out"
    out.mkdir()
    json.dump(dict(device="stub", items=items, strings={n: "".join(map(str, b)) for n, b in strs}, cycles=[t],
                   forms=["L"], shots=shots), open(out / "build.json", "w"))
    json.dump(dict(z=ans), open(tmp_path / "ans.json", "w"))
    monkeypatch.setattr(J, "read", lambda jobd, runs: read)
    monkeypatch.setattr(U, "_tag_of", lambda name, rec: rec["tag"])
    monkeypatch.setattr(SN, "verdict", lambda jobd, runs: dict(status="stub"))
    return argparse.Namespace(out=str(out), answers=str(tmp_path / "ans.json"))


def _score(a):
    ORN.cmd_score(a)
    return json.load(open(os.path.join(a.out, "scores.json")))


# ----------------------------------------------------------------------------------------------- the words

def test_no_noise_ruled_w_equals_exact(tmp_path, monkeypatch):
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)       # no scatter at all: see the edge test below
        res = _score(_job(tmp_path, monkeypatch, r=1.0))
    for k, c in res["cells"].items():
        assert abs(c["W_exact"]) > 0.01, k
        assert abs(c["W_device"] - c["W_exact"]) < 1e-9, k
        assert abs(c["d_a"]) < 1e-9 and abs(c["d_b"]) < 1e-9, k
        assert c["W"] == "READS" and c["M"] == "READS"


def test_one_uniform_factor_every_ruler_agrees(tmp_path, monkeypatch):
    res = _score(_job(tmp_path, monkeypatch, r=0.85, eta=0.02))
    for k, c in res["cells"].items():
        assert c["ruler_a"] == "AGREES", (k, c["d_a"], c["d_a_2se"])
        assert c["ruler_b"] == "AGREES", (k, c["d_b"], c["d_b_2se"])
        assert c["W_excess"] > 0                     # the raw W sits above the exact one under a shrink
    for v in res["tables"].values():
        assert v["table2"] == ORN.READ_A_B[("AGREES", "AGREES")]


def test_readout_like_mirror_parts_ruler_b(tmp_path, monkeypatch):
    # the mirror shrunk once (r), not twice: sqrt(mirror) above r, ruler (b) DIFFERS, ruler (a) AGREES
    res = _score(_job(tmp_path, monkeypatch, r=0.85, eta=0.002, mirror_shape=lambda pos, win: [0.85] * len(pos)))
    for k, c in res["cells"].items():
        assert c["ruler_a"] == "AGREES", k
        assert c["ruler_b"] == "DIFFERS", k


# ------------------------------------------------------------------------------------------------ uniformity

def test_chi2_sf_equals_scipy():
    st = pytest.importorskip("scipy.stats")
    for k in (1, 2, 3, 4, 5, 8):
        for x in (0.1, 1.0, 3.7, 9.0, 20.0):
            assert abs(ORN.chi2_sf(x, k) - st.chi2.sf(x, k)) < 1e-12


def test_uniformity_chi2_by_hand(tmp_path, monkeypatch):
    st = pytest.importorskip("scipy.stats")
    a = _job(tmp_path, monkeypatch, r=0.85, eta=0.03)
    res = _score(a)
    b = json.load(open(os.path.join(a.out, "build.json")))
    ans = json.load(open(a.answers))["z"]
    import psf_os.job as J
    read = J.read(None, None)
    K = 3
    for arm in ORN.ARMS:
        key = f"{arm}_t3_L"
        pos = b["items"][ORN.tag(arm, 3, "L", "s00")]["positions"]
        wi = [i for i, p in enumerate(pos) if p in ORN.window(3)]
        zd = {}
        for nm in [f"{p}{k:02d}" for k in range(K) for p in "sc"]:
            tg = ORN.tag(arm, 3, "L", nm)
            cnt = read[tg][1][("x", "z")]
            tot = sum(cnt.values())
            zd[nm] = np.array([sum(c * (1 - 2 * int(s[-1 - j])) for s, c in cnt.items()) / tot for j in range(len(pos))])
        ze = {nm: np.array([ans[ORN.tag(arm, 3, "L", nm)][str(p)] for p in pos]) for nm in zd}
        r_q, se_q = [], []
        for i in wi:
            od = np.array([(zd[f"s{k:02d}"][i] - zd[f"c{k:02d}"][i]) / 2 for k in range(K)])
            oe = np.array([(ze[f"s{k:02d}"][i] - ze[f"c{k:02d}"][i]) / 2 for k in range(K)])
            if np.sum(oe ** 2) < ORN.UNIFORM_FLOOR * K:
                continue
            var_o = np.array([((1 - zd[f"s{k:02d}"][i] ** 2) + (1 - zd[f"c{k:02d}"][i] ** 2)) / 1000 / 4
                              for k in range(K)])
            r_q.append(np.sum(od * oe) / np.sum(oe ** 2))
            se_q.append(math.sqrt(np.sum(oe ** 2 * var_o)) / np.sum(oe ** 2))
        r_q, se_q = np.array(r_q), np.array(se_q)
        w = 1 / se_q ** 2
        pool = np.sum(w * r_q) / np.sum(w)
        chi2 = np.sum(((r_q - pool) / se_q) ** 2)
        u = res["uniform"][key]
        assert u["dof"] == len(r_q) - 1
        assert abs(u["r_pool"] - pool) < 1e-10 and abs(u["chi2"] - chi2) < 1e-8
        assert abs(u["p"] - st.chi2.sf(chi2, len(r_q) - 1)) < 1e-10
        assert u["word"] == ("UNIFORM" if u["p"] >= ORN.LEVEL else "NOT UNIFORM")


# ------------------------------------------------------------------------------------------- ohm_ruler_night2

def test_ruler_c_equals_b_on_a_uniform_mirror_and_a_b_equal_declared(tmp_path, monkeypatch):
    ORN2 = pytest.importorskip("ohm_ruler_night2")
    a = _job(tmp_path, monkeypatch, r=0.85, eta=0.02)
    res = _score(a)                                  # writes the declared scores.json first
    ORN2.cmd_score2(a)                               # stops if (a), (b) differ from it
    s2 = json.load(open(os.path.join(a.out, "scores2.json")))
    assert json.load(open(os.path.join(a.out, "scores.json"))) == res      # not written over
    for k, c in s2["cells"].items():
        assert abs(c["c"]["d"] - c["b"]["d"]) < 1e-12, k
        assert c["c"]["words"]["2se"] == "AGREES" and c["c"]["words"]["t"] == "AGREES", k


def test_ruler_c_reads_a_window_heavier_mirror(tmp_path, monkeypatch):
    # the mirror shrunk r^2 on the window only (outside it stays 1): (b) underestimates the shrink, (c) does not
    ORN2 = pytest.importorskip("ohm_ruler_night2")
    shape = lambda pos, win: [0.85 ** 2 if p in win else 1.0 for p in pos]
    a = _job(tmp_path, monkeypatch, r=0.85, eta=0.002, mirror_shape=shape)
    _score(a)
    ORN2.cmd_score2(a)
    s2 = json.load(open(os.path.join(a.out, "scores2.json")))
    for k, c in s2["cells"].items():
        assert c["c"]["words"]["2se"] == "AGREES", k
        assert c["b"]["words"]["2se"] == "DIFFERS", k


def test_t_quantile_table():
    ORN2 = pytest.importorskip("ohm_ruler_night2")
    st = pytest.importorskip("scipy.stats")
    for dof in range(1, 21):
        assert abs(ORN2.t975(dof) - st.t.ppf(0.975, dof)) < 5e-4


def test_edge_zero_scatter_as_declared(tmp_path, monkeypatch):
    # Documents the declared tool's behaviour on data with no scatter at all (not a device case): d = 0 with SE = 0
    # reads DIFFERS (the rule is |d| < 2 SE), and window qubits at exactly |<Z>| = 1 have shot SE 0, so the chi2 is NaN
    # and the word is NOT UNIFORM. Left as declared; reported to home (2026-11-24).
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        res = _score(_job(tmp_path, monkeypatch, r=1.0))
    for k, c in res["cells"].items():
        assert c["d_a_2se"] == 0 and c["ruler_a"] == "DIFFERS", k
    for k, u in res["uniform"].items():
        assert math.isnan(u["p"]) and u["word"] == "NOT UNIFORM", k
