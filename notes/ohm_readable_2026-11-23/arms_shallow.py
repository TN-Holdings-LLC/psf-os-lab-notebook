"""Can shallow times tell the Ohm arms apart? Exact answers only (home VS, 2026-11-23; desk, no device).

The circuits of gpu/ohm_answers.py (N 40, the 11-12 strings: K 14 and their complements, m 0.5, seed 20261112), at
t = 1, 2, 3, 4 cycles, arms A0 / A1 / A2. Per-qubit <Z> by gpu/ohm_answers.py's own functions (A0 free fermions, A1 /
A2 quimb CircuitMPS, chi 2048, cutoff 1e-10); t = 3 is checked against the sealed answers.
The wall's transfer over a window, W_w(t) = mean over the pairs of (M_w(s) - M_w(c)) / 2, with M_w summed over the
light-cone window (2t - 1 sites next to the wall) and over the declared right half (20 sites).
Measures (to tell the arms apart):
  slope: least-squares slope of log W against log t over t = 1..4 (a transport exponent over shallow times);
  growth: W(4) / W(1) (and, beside, W(3) / W(1));
  level: W(3) itself.
Beside, never judged: the same kinds of measure on the 11-12 records (t = 3 and 6; notes/ohm_idle_2026-11-23/
window_M.json): log2(W(6) / W(3)) and W(6) / W(3), device and exact.

usage: python notes/ohm_readable_2026-11-23/arms_shallow.py OUT.json
"""
import json
import os
import sys
import time

import numpy as np

NB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(NB, "gpu"))
import ohm_answers as OA  # noqa: E402

N, K, M, SEED = 40, 14, 0.5, 20261112
TS = (1, 2, 3, 4)


def z_of(arm, t, bits):
    if arm == "A0":
        return OA.z_free(N, t, bits)
    return OA.z_quimb(N, t, arm, bits, 2048, 1e-10)[0]


def wall(zs, strs, t, w):
    h = N // 2
    mw = {}
    for name, bits in strs:
        z = zs[name]
        mw[name] = float(((1 - z[h:h + w]) / 2).sum() - sum(bits[h:h + w]))
    ks = sorted({n[1:] for n, _ in strs})
    return float(np.mean([(mw["s" + k] - mw["c" + k]) / 2 for k in ks]))


def main(out):
    if os.path.exists(out):
        raise SystemExit(f"STOP: {out} exists")
    strs = OA.strings(N, K, M, SEED)
    sealed = json.load(open(os.path.join(NB, "results/ohm-2026-11-12/answers/ohm_answers.json")))["z"]
    res = dict(note="exact answers only; N 40, the 11-12 strings", W={}, check_t3_vs_sealed=0.0)
    t0 = time.time()
    for arm in ("A0", "A1", "A2"):
        for t in TS:
            zs = {name: np.array(z_of(arm, t, bits)) for name, bits in strs}
            if t == 3:
                for name, _ in strs:
                    res["check_t3_vs_sealed"] = max(res["check_t3_vs_sealed"], float(np.max(np.abs(
                        zs[name] - np.array(sealed[OA.tag(arm, t, name)])))))
            res["W"][f"{arm}_t{t}"] = dict(light_cone=wall(zs, strs, t, 2 * t - 1), half=wall(zs, strs, t, N // 2))
        print(f"{arm}: {time.time() - t0:.0f} s", flush=True)
    meas = {}
    lt = np.log(np.array(TS, dtype=float))
    for win in ("light_cone", "half"):
        for arm in ("A0", "A1", "A2"):
            W = np.array([res["W"][f"{arm}_t{t}"][win] for t in TS])
            meas[f"{win}_{arm}"] = dict(W=W.tolist(), slope=float(np.polyfit(lt, np.log(W), 1)[0]),
                                        growth_4_1=float(W[3] / W[0]), growth_3_1=float(W[2] / W[0]), level_3=float(W[2]))
    res["measures"] = meas
    wm = json.load(open(os.path.join(NB, "notes/ohm_idle_2026-11-23/window_M.json")))["cells"]
    side = {}
    for dev in ("fez", "kingston"):
        for win, key in (("light_cone", "W_window"), ("half", "W_half")):
            for arm in ("A0", "A1", "A2"):
                a, b = wm[f"{dev}_{arm}_t3"][key], wm[f"{dev}_{arm}_t6"][key]
                side[f"{dev}_{win}_{arm}"] = dict(
                    device=dict(log2_6_3=float(np.log2(b["device"] / a["device"])), ratio_6_3=b["device"] / a["device"],
                                level_3=a["device"]),
                    exact=dict(log2_6_3=float(np.log2(b["exact"] / a["exact"])), ratio_6_3=b["exact"] / a["exact"],
                               level_3=a["exact"]))
    res["records_beside"] = side
    json.dump(res, open(out, "w"), indent=1)
    print(f"t = 3 against the sealed answers: worst {res['check_t3_vs_sealed']:.1e}")
    for win in ("light_cone", "half"):
        print(f"[{win}]  W(t=1..4)                         slope   W4/W1   W3/W1   W(3)")
        for arm in ("A0", "A1", "A2"):
            x = meas[f"{win}_{arm}"]
            print(f"  {arm}  " + " ".join(f"{w:6.3f}" for w in x["W"]) + f"   {x['slope']:6.3f}  {x['growth_4_1']:6.3f}  "
                  f"{x['growth_3_1']:6.3f}  {x['level_3']:6.3f}")
    print("records (beside): log2 W6/W3 device (exact), W(3) device (exact)")
    for k, v in side.items():
        print(f"  {k:22} {v['device']['log2_6_3']:6.3f} ({v['exact']['log2_6_3']:6.3f})   "
              f"{v['device']['level_3']:6.3f} ({v['exact']['level_3']:6.3f})")


if __name__ == "__main__":
    main(sys.argv[1])
