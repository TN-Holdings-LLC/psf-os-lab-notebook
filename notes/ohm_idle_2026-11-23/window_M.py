"""Beside, never judged (home VS, 2026-11-23; desk, no device): the Ohm records scored with M summed over a window of
the right half next to the wall instead of the whole right half.

M_w = sum over chain positions N/2 .. N/2 + w - 1 of (1 - z) / 2 minus the string's own count of 1 there. w = N/2 is
gpu/ohm_score.py's M (checked against scores.json). For w < N/2, M_w is a different quantity from M: the number of 1 in
the window changes through the wall AND through the window's far edge (the right half's own dynamics), so its exact
value is computed from the sealed exact per-qubit answers, and the device's M_w is compared with that. The logical
light cone of the wall after t cycles (even bonds, then odd bonds; the wall is the odd bond (N/2 - 1, N/2)) reaches
2t - 1 sites into the right half. Same rule as the declaration's: READS if the mean squared M_w error is at most half
the mean square of the exact M_w, per device, arm and cycle count. Raw counts, nothing corrected, no shot discarded;
the declared verdicts stay those of scores.json.

usage: PYTHONPATH=<psf-os 0.3.3> python notes/ohm_idle_2026-11-23/window_M.py OUT.json
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shrink_bound as SB  # noqa: E402


def main(out):
    res = dict(note="beside, never judged; M over a window next to the wall is a different quantity from the declared "
                    "M (exact values from the sealed answers); raw counts, nothing corrected", cells={})
    for dev in SB.RUNS:
        vals, worst = SB.device_values(dev)
        b = json.load(open(os.path.join(SB.NB, SB.RUNS[dev][0], "build.json")))
        N = b["N"]
        h = N // 2
        res[f"{dev}_full_M_vs_scores_json_worst"] = worst
        for arm in ("A0", "A1", "A2"):
            for t in b["cycles"]:
                tags = sorted(k for k in vals if k.startswith(f"{arm}_t{t}_"))
                rows = {}
                for w in range(1, h + 1):
                    d, ex = [], []
                    for tg in tags:
                        z, e, _, _ = vals[tg]
                        bits = np.array([int(x) for x in b["strings"][tg.split("_")[2]]])
                        sl = slice(h, h + w)
                        m0 = bits[sl].sum()
                        Md = ((1 - z[sl]) / 2).sum() - m0
                        Me = ((1 - e[sl]) / 2).sum() - m0
                        d.append(Md - Me)
                        ex.append(Me)
                    mse, msq = float(np.mean(np.square(d))), float(np.mean(np.square(ex)))
                    rows[w] = dict(mse=mse, mean_square=msq, ratio=mse / msq if msq else None,
                                   reads=bool(msq and mse <= msq / 2))
                lc = 2 * t - 1

                def mw(tg, w, dev_values):
                    z, e, _, _ = vals[tg]
                    v = z if dev_values else e
                    bits = np.array([int(x) for x in b["strings"][tg.split("_")[2]]])
                    return float(((1 - v[h:h + w]) / 2).sum() - bits[h:h + w].sum())
                ks = sorted({tg.split("_")[2][1:] for tg in tags})

                def wall(w, dev_values):     # W over the window: string minus its complement, halved, mean over pairs
                    return float(np.mean([(mw(f"{arm}_t{t}_s{k}", w, dev_values) -
                                           mw(f"{arm}_t{t}_c{k}", w, dev_values)) / 2 for k in ks]))
                ew = np.array([mw(tg, lc, False) for tg in tags])
                ef = np.array([mw(tg, h, False) for tg in tags])
                res["cells"][f"{dev}_{arm}_t{t}"] = dict(
                    light_cone_width=lc, windows=rows,
                    exact_corr_window_vs_half=float(np.corrcoef(ew, ef)[0, 1]),
                    W_window=dict(device=wall(lc, True), exact=wall(lc, False)),
                    W_half=dict(device=wall(h, True), exact=wall(h, False)))
        res.setdefault("exponent_window", {})[dev] = {
            arm: dict(device=float(np.log2(res["cells"][f"{dev}_{arm}_t6"]["W_window"]["device"] /
                                           res["cells"][f"{dev}_{arm}_t3"]["W_window"]["device"])),
                      exact=float(np.log2(res["cells"][f"{dev}_{arm}_t6"]["W_window"]["exact"] /
                                          res["cells"][f"{dev}_{arm}_t3"]["W_window"]["exact"])))
            for arm in ("A0", "A1", "A2")}
    json.dump(res, open(out, "w"), indent=1)
    for dev in SB.RUNS:
        print(f"{dev}: full-half M against scores.json, worst {res[f'{dev}_full_M_vs_scores_json_worst']:.1e}")
    print("cell                 w=lc  ratio(lc)  reads   ratio(lc+2) | full half ratio | smallest ratio (w)")
    for k, c in res["cells"].items():
        W = c["windows"]
        lc = c["light_cone_width"]
        best = min((v["ratio"], w) for w, v in W.items() if v["ratio"] is not None)
        r2 = W.get(lc + 2, W[max(W)])["ratio"]
        print(f"{k:20} {lc:4}  {W[lc]['ratio']:9.3f}  {'READS' if W[lc]['reads'] else '-':5}  {r2:10.3f} | "
              f"{W[max(W)]['ratio']:15.3f} | {best[0]:.3f} ({best[1]})")
    print("cell                 corr(exact M_lc, exact M)  W_lc device / exact   W half device / exact")
    for k, c in res["cells"].items():
        print(f"{k:20} {c['exact_corr_window_vs_half']:25.3f}  {c['W_window']['device']:6.3f} / "
              f"{c['W_window']['exact']:6.3f}   {c['W_half']['device']:6.3f} / {c['W_half']['exact']:6.3f}")
    for dev, ex in res["exponent_window"].items():
        print(f"{dev}: exponent log2(W(6) / W(3)) over the light-cone windows: " + ", ".join(
            f"{a} {v['device']:.3f} (exact {v['exact']:.3f})" for a, v in ex.items()))


if __name__ == "__main__":
    main(sys.argv[1])
