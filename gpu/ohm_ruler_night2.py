"""Ohm with rulers inside the circuit, the next night's candidates (workplace Claude, 2026-11-24; not declared).

The declared tool of 2026-11-24, gpu/ohm_ruler_night.py, is read only and not changed: this file imports it and adds
one subcommand, `score2`, which writes `scores2.json` beside the declared `scores.json` (never over it).

  (c) the mirror on the window alone: rho_c = sqrt(mean over the window's qubits of the cell's mirror <Z>). The mirror
      is ideally |0> on every qubit, so its per-qubit shrink is read where the window sits, not over the whole circuit.
      Its SE adds the mirror's shot noise on the window (the per-shot window mean), through the square root.

For each ruler (a), (b), (c) the words are given at two widths, side by side:
  2se  AGREES when |d| < 2 SE (the declared rule)
  t    AGREES when |d| < t_{0.975, K-1} SE (Student's t, K pairs; 2.447 at K = 7, 2.306 at K = 9)
(a) and (b) are recomputed here with the declared formulas; `score2` stops if they differ from the declared tool's
scores.json in the same folder by more than 1e-12 (when that file is there).

The one-factor test on the window (the declared tool's `score`, read from its scores.json, not recomputed here): per
window position q, r_q = sum_k O_device,kq O_exact,kq / sum_k O_exact,kq^2, and its SE is the shot noise of the counts,
SE_q = sqrt(sum_k O_exact,kq^2 (var Z_s + var Z_c) / 4) / sum_k O_exact,kq^2 with var Z = (1 - Z^2) / shots; the pool
is weighted by 1 / SE_q^2 and chi2 has n - 1 degrees of freedom. No bootstrap over pairs is used (the declared tool's
comment "bootstrap SEs over pairs" does not match its computation; that tool is declared and is not changed).

  PYTHONPATH=<psf-os 0.3.3>:<TOQB> python gpu/ohm_ruler_night2.py score2 OUT ANS_BY_LABEL.json
"""
import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ohm_ruler_night as ORN  # noqa: E402  (read only: the declared tool of 2026-11-24)

T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
        11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086}


def t975(dof):
    """Two-sided 95 % quantile of Student's t (table to 20 degrees of freedom, 1.96 beyond)."""
    return T975.get(dof, 1.96)


def words(d, se, K):
    return {"2se": "AGREES" if abs(d) < 2 * se else "DIFFERS",
            "t": "AGREES" if abs(d) < t975(K - 1) * se else "DIFFERS"}


def z_and_subset_se(counts, rec_labels, labels, idx):
    """Per-label <Z>, and the shot-noise SE of the mean <Z> over labels[idx] (per-shot mean, as the declared tool does
    over all labels)."""
    k_of = {lb: k for k, lb in enumerate(rec_labels)}
    tot = sum(counts.values())
    z = np.zeros(len(labels))
    per = []
    for key, c in counts.items():
        s = key.replace(" ", "")
        v = np.array([1 - 2 * int(s[-1 - k_of[lb]]) for lb in labels])
        z += c * v
        per.append((float(v[idx].mean()), c))
    z /= tot
    mu = sum(m * c for m, c in per) / tot
    var = sum(c * (m - mu) ** 2 for m, c in per) / (tot - 1)
    return z, math.sqrt(var / tot)


def ruler_from_mirror(Od_w, const, w_ex, m, m_se, K):
    """W through rho = sqrt(m), its d against the exact W, and the SE with the mirror's shot noise propagated."""
    rho = math.sqrt(m)
    w = -(Od_w / rho) / 2 + const
    d = w - w_ex
    se_pairs = float(np.std(d, ddof=1) / np.sqrt(K))
    dwdm = float(np.mean(Od_w) / (4 * m ** 1.5))
    se = math.sqrt(se_pairs ** 2 + (dwdm * m_se) ** 2)
    return dict(rho=rho, W=float(w.mean()), d=float(d.mean()), se=se, words=words(float(d.mean()), se, K))


def cmd_score2(a):
    from psf_os import job as J
    from psf_os import user2d as U
    b = json.load(open(os.path.join(a.out, "build.json")))
    ans = json.load(open(a.answers))["z"]
    runs, jobd = os.path.join(a.out, "runs"), os.path.join(a.out, "job")
    zz, mrec = {}, {}
    for name, (rec, cc) in J.read(jobd, runs).items():
        kind = rec.get("psfos_job", {}).get("kind")
        if kind not in ("user2d", "user2d_mirror"):
            continue
        tg = U._tag_of(name, rec)
        labels = b["items"][tg]["given_labels"]
        counts = cc[(rec["points"][0]["input"], "z")]
        if kind == "user2d":
            zz[tg], _ = z_and_subset_se(counts, rec["labels"], labels, slice(None))
        else:
            mrec[tg] = (counts, rec["labels"], labels)
    strs = b["strings"]
    ks = sorted({n[1:] for n in strs})
    K = len(ks)
    declared = None
    if os.path.exists(os.path.join(a.out, "scores.json")):
        declared = json.load(open(os.path.join(a.out, "scores.json")))["cells"]
    res = dict(device=b["device"], K=K, t975=t975(K - 1), cells={})
    for arm in ORN.ARMS:
        for t in b["cycles"]:
            for form in b["forms"]:
                mt = ORN.tag(arm, t, form, "s00")
                pos = b["items"][mt]["positions"]
                wi = [i for i, p in enumerate(pos) if p in ORN.window(t)]
                Od, Oe, T0, const = [], [], [], []
                for k in ks:
                    s, c = ORN.tag(arm, t, form, "s" + k), ORN.tag(arm, t, form, "c" + k)
                    zex = lambda tg: np.array([ans[tg][str(lb)] for lb in b["items"][tg]["given_labels"]])
                    Od.append((zz[s] - zz[c]) / 2)
                    Oe.append((zex(s) - zex(c)) / 2)
                    T0.append(sum(1 - 2 * int(strs["s" + k][p]) for p in pos))
                    ms = sum(int(strs["s" + k][p]) for p in ORN.window(t))
                    mc = sum(int(strs["c" + k][p]) for p in ORN.window(t))
                    const.append(-(ms - mc) / 2)
                Od, Oe, T0, const = np.array(Od), np.array(Oe), np.array(T0, dtype=float), np.array(const)
                w_ex = -Oe[:, wi].sum(axis=1) / 2 + const
                Od_w = Od[:, wi].sum(axis=1)
                cell = {}
                if ORN.ruler_a_read(t, form):
                    rho_a = Od.sum(axis=1) / T0
                    d_a = (-(Od_w / rho_a) / 2 + const) - w_ex
                    se_a = float(np.std(d_a, ddof=1) / np.sqrt(K))
                    cell["a"] = dict(d=float(d_a.mean()), se=se_a, words=words(float(d_a.mean()), se_a, K))
                if mt in mrec:
                    counts, rl, labels = mrec[mt]
                    zm, se_all = z_and_subset_se(counts, rl, labels, slice(None))
                    _, se_win = z_and_subset_se(counts, rl, labels, wi)
                    if zm.mean() > 0:
                        cell["b"] = ruler_from_mirror(Od_w, const, w_ex, float(zm.mean()), se_all, K)
                    if zm[wi].mean() > 0:
                        cell["c"] = ruler_from_mirror(Od_w, const, w_ex, float(zm[wi].mean()), se_win, K)
                        cell["c"]["mirror_window"] = float(zm[wi].mean())
                if declared is not None:
                    dc = declared[f"{arm}_t{t}_{form}"]
                    for r, key in (("a", "d_a"), ("b", "d_b")):
                        if r in cell and abs(cell[r]["d"] - dc[key]) > 1e-12:
                            raise SystemExit(f"STOP: ruler ({r}) differs from the declared tool at {arm}_t{t}_{form}")
                        if r in cell and abs(2 * cell[r]["se"] - dc[key + "_2se"]) > 1e-12:
                            raise SystemExit(f"STOP: ruler ({r}) SE differs from the declared tool at {arm}_t{t}_{form}")
                res["cells"][f"{arm}_t{t}_{form}"] = cell
    json.dump(res, open(os.path.join(a.out, "scores2.json"), "w"), indent=1)
    print(f"K = {K}; t quantile {t975(K - 1):.3f}" + ("; (a) and (b) equal the declared scores.json" if declared else ""))
    for k, c in res["cells"].items():
        print(f"{k}: " + "; ".join(f"({r}) d {v['d']:+.4f} SE {v['se']:.4f} 2se {v['words']['2se']} t {v['words']['t']}"
                                   + (f" sqrt(window mirror) {v['rho']:.3f}" if r == "c" else "")
                                   for r, v in c.items()))


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("score2")
    p.add_argument("out")
    p.add_argument("answers")
    a = ap.parse_args()
    dict(score2=cmd_score2)[a.cmd](a)


if __name__ == "__main__":
    main()
