"""An upper bound, a rough guide only (home VS, 2026-11-23; desk, no device): how much of the Ohm records' uniform
shrink the probably-|1> idle time could explain, and what M's error would become if that part were gone.

ASSUMED MODEL (an assumption, not fitted to the device, nothing corrected in the records):
  * each circuit's device values split as z = r e + rest (rest orthogonal to the exact values e; as
    notes/noise_structure_2026-11-13 and notes/paper9/r_thread_2026-11-13); r < 1 is the uniform shrink;
  * ALL of the shrink 1 - r grows in proportion to qubit-time, so the share that idle time in |1> could carry is at
    most phi = (idle time weighted by P(|1>)) / (all qubit-time), the (c) share of ohm_idle.py (the larger of the two
    schedules), and parking could remove at most that share: z' = z + phi (1 - r) e;
  * the rest (the part that is not a uniform shrink) is left as it is.
  This overstates what parking could do: readout shrink does not grow with idle time, and X, delay, X only turns
  P(|1>) into 1 - P(|1>) on the spans long enough for it (the "gain" and "parked" shares are given beside).
M and the READS line are as gpu/ohm_score.py: M = sum over the right half of (1 - z) / 2 minus the string's own count;
READS if the mean squared M error is at most half the mean square of the exact M. Also: phi needed to reach the line
(None if even phi = 1, all of the uniform shrink gone, does not reach it).

usage: PYTHONPATH=<psf-os 0.3.3> python notes/ohm_idle_2026-11-23/shrink_bound.py SUMMARY.json PARK.json OUT.json
"""
import json
import os
import sys

import numpy as np

NB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RUNS = {"fez": ("results/ohm-2026-11-12/ibm_fez", "results/ohm-2026-11-12/answers/ohm_ibm_fez_ans.json"),
        "kingston": ("results/ohm-kingston-2026-11-12/ibm_kingston",
                     "results/ohm-kingston-2026-11-12/answers/ohm_ibm_kingston_ans.json")}


def z_of(counts, n):
    """Per-clbit <Z> (the reading of notes/ohm_postsel_2026-11-12/postsel.py)."""
    tot = sum(counts.values())
    m = np.zeros(n)
    for key, c in counts.items():
        b = key.replace(" ", "")
        m += c * (1 - 2 * np.array([int(b[-1 - k]) for k in range(n)]))
    return m / tot


def device_values(dev):
    """{tag: (z, e, m0, right indices)} in chain order, and the largest |M - scores.json's M|."""
    from psf_os import job as J
    from psf_os import user2d as U
    out, ans = RUNS[dev]
    out, ans = os.path.join(NB, out), os.path.join(NB, ans)
    b = json.load(open(os.path.join(out, "build.json")))
    sc = json.load(open(os.path.join(out, "scores.json")))
    A = json.load(open(ans))["z"]
    chain, N = b["chain"]["labels"], b["N"]
    res, worst = {}, 0.0
    for name, (rec, cc) in J.read(os.path.join(out, "job"), os.path.join(out, "runs")).items():
        if rec.get("psfos_job", {}).get("kind") != "user2d":
            continue
        tag = U._tag_of(name, rec)
        counts = cc[(rec["points"][0]["input"], "z")]
        zz = z_of(counts, len(rec["labels"]))
        zl = {lab: zz[k] for k, lab in enumerate(rec["labels"])}
        z = np.array([zl[lab] for lab in chain])
        e = np.array([A[tag][str(lab)] for lab in chain])
        m0 = sum(int(x) for x in b["strings"][tag.split("_")[2]][N // 2:])
        M = float(((1 - z[N // 2:]) / 2).sum() - m0)
        worst = max(worst, abs(M - sc["circuits"][tag]["M"]))
        res[tag] = (z, e, m0, N // 2)
    return res, worst


def cell_mse(vals, phi):
    d, ex = [], []
    for z, e, m0, h in vals:
        r = float(z @ e / (e @ e))
        zp = z + phi * (1 - r) * e
        M = ((1 - zp[h:]) / 2).sum() - m0
        Me = ((1 - e[h:]) / 2).sum() - m0
        d.append(M - Me)
        ex.append(Me)
    return float(np.mean(np.square(d)) / np.mean(np.square(ex)))


def phi_needed(vals):
    if cell_mse(vals, 1.0) > 0.5:
        return None
    lo, hi = 0.0, 1.0
    for _ in range(50):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if cell_mse(vals, mid) > 0.5 else (lo, mid)
    return hi


def main(summary_file, park_file, out):
    S = json.load(open(summary_file))["cells"]
    P = json.load(open(park_file))
    parked = {}
    for r in P["circuits"]:
        arm, t, _ = r["tag"].split("_")
        parked.setdefault(f"{r['device']}_{arm}_{t}", []).append(r)
    res = dict(note="assumed model (all of the uniform shrink proportional to qubit-time); a rough guide, an upper "
                    "bound; nothing fitted to the device, nothing corrected", cells={})
    for dev in RUNS:
        vals, worst = device_values(dev)
        res[f"{dev}_M_vs_scores_json_worst"] = worst
        for arm in ("A0", "A1", "A2"):
            for t in (3, 6):
                key = f"{dev}_{arm}_t{t}"
                v = [vals[k] for k in sorted(vals) if k.startswith(f"{arm}_t{t}_")]
                s = S[key]
                phi_c = max(s["asap"]["c_share_of_qubit_time"], s["alap"]["c_share_of_qubit_time"])
                phi_g = max(s["asap"]["park_gain_share_of_qubit_time"], s["alap"]["park_gain_share_of_qubit_time"])
                pr = parked.get(key, [])
                phi_p = sum(r["parked_gain_dt"] for r in pr) / (s[P["schedule"]]["qubit_time_us_per_circuit"] /
                                                               4e-3 * len(pr)) if pr else 0.0
                rs = [float(z @ e / (e @ e)) for z, e, _, _ in v]
                m0, m1 = cell_mse(v, 0.0), cell_mse(v, 1.0)
                res["cells"][key] = dict(
                    circuits=len(v), r_mean=float(np.mean(rs)), mse_ratio_recorded=m0,
                    uniform_shrink_share_of_M_mse=(m0 - m1) / m0,
                    phi_upper_c=phi_c, mse_ratio_at_phi_upper=cell_mse(v, phi_c),
                    phi_gain=phi_g, mse_ratio_at_phi_gain=cell_mse(v, phi_g),
                    phi_parked=phi_p, mse_ratio_at_phi_parked=cell_mse(v, phi_p),
                    mse_ratio_all_uniform_shrink_gone=m1, phi_needed_for_line=phi_needed(v))
    json.dump(res, open(out, "w"), indent=1)
    for dev in RUNS:
        print(f"{dev}: M recomputed against scores.json, worst {res[f'{dev}_M_vs_scores_json_worst']:.1e}")
    print("cell                r mean  recorded  shrink share  phi(c)  ->ratio   phi(gain) ->ratio  all shrink gone  phi needed")
    for k, c in res["cells"].items():
        pn = c["phi_needed_for_line"]
        print(f"{k:18}  {c['r_mean']:6.3f}  {c['mse_ratio_recorded']:8.3f}  {c['uniform_shrink_share_of_M_mse']:12.2f}  "
              f"{c['phi_upper_c']:6.3f}  {c['mse_ratio_at_phi_upper']:7.3f}   {c['phi_gain']:7.4f}  "
              f"{c['mse_ratio_at_phi_gain']:7.3f}  {c['mse_ratio_all_uniform_shrink_gone']:15.3f}  "
              f"{'none' if pn is None else round(pn, 3)}")


if __name__ == "__main__":
    main(*sys.argv[1:])
