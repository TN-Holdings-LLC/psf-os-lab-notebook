"""Beside, never judged (home VS, 2026-11-23; desk, no device; computed AFTER the records were seen): does the Ohm
records' transfer reverse with the wall, S_k = M(s_k) + M(c_k) (s_k a string, c_k its complement), as the exact
answers say? (Onsager-type reciprocity J(+V) = -J(-V), the outside AI's proposal 3; home's instruction
"オームの相反の机上計算".)

Per device, arm (A0, A1, A2), cycle count (3, 6), pair k and window w:
  M_w = sum over chain positions N/2 .. N/2 + w - 1 of (1 - z) / 2 minus the string's own count of 1 there
        (w = N/2: the declared M of gpu/ohm_score.py; w = 2t - 1: the wall's light-cone window; w = 1: the site next
        to the wall, proposal 3's "one link");
  S_k device and exact (exact from the sealed per-qubit answers), dS_k = device - exact;
  the shot error of S_k from the raw counts: M_w is the mean over shots of the count of 1 in the window, so its
  standard error is the per-shot standard deviation of that count over sqrt(shots), and S_k's adds the pair's two.
Per cell: the mean of dS_k, its standard error from the pairs' spread (sd / sqrt(K)) and from the shots alone
(sqrt(sum SE_k^2) / K), and whether the mean is more than 2 SE (the larger of the two) from 0. The direction "decay"
is dS < 0 (fewer 1 than the exact value).
What a shift of the per-qubit Z explains: dS_k = -1/2 sum over the window of (dz(s_k) + dz(c_k)), dz = z - e, exactly;
split as each circuit's z = r e + rest (notes/noise_structure_2026-11-13): the uniform shrink part (r - 1) e and the
rest. Beside: the floor circuits' mean <Z> from scores.json (1 for a perfect device).
Raw counts, nothing corrected, no shot discarded; scores.json's verdicts are not changed.

usage: PYTHONPATH=<psf-os 0.3.3> python notes/ohm_idle_2026-11-23/reciprocity.py OUT.json
"""
import json
import os
import sys

import numpy as np

NB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RUNS = {"fez": ("results/ohm-2026-11-12/ibm_fez", "results/ohm-2026-11-12/answers/ohm_ibm_fez_ans.json"),
        "kingston": ("results/ohm-kingston-2026-11-12/ibm_kingston",
                     "results/ohm-kingston-2026-11-12/answers/ohm_ibm_kingston_ans.json")}


def circuits(dev):
    """{tag: dict(counts, clbit of each chain position, z, e, bits)} for the user circuits, chain order."""
    from psf_os import job as J
    from psf_os import user2d as U
    out, ans = (os.path.join(NB, p) for p in RUNS[dev])
    b = json.load(open(os.path.join(out, "build.json")))
    A = json.load(open(ans))["z"]
    chain = b["chain"]["labels"]
    res = {}
    for name, (rec, cc) in J.read(os.path.join(out, "job"), os.path.join(out, "runs")).items():
        if rec.get("psfos_job", {}).get("kind") != "user2d":
            continue
        tag = U._tag_of(name, rec)
        counts = cc[(rec["points"][0]["input"], "z")]
        k_of = {lab: k for k, lab in enumerate(rec["labels"])}
        cl = [k_of[lab] for lab in chain]
        keys = [key.replace(" ", "") for key in counts]
        bitsarr = np.array([[int(key[-1 - k]) for k in cl] for key in keys])    # shots-kinds x chain positions
        w = np.array(list(counts.values()), dtype=float)
        z = 1 - 2 * (w @ bitsarr) / w.sum()
        res[tag] = dict(bits_by_kind=bitsarr, weights=w, z=z, e=np.array([A[tag][str(lab)] for lab in chain]),
                        init=np.array([int(x) for x in b["strings"][tag.split("_")[2]]]))
    return res, b


def m_and_se(c, lo, hi):
    """(device M_w, its shot standard error, exact M_w) over chain positions lo .. hi - 1."""
    w = c["weights"]
    n1 = c["bits_by_kind"][:, lo:hi].sum(axis=1)
    mean = float(w @ n1 / w.sum())
    var = float(w @ (n1 - mean) ** 2 / (w.sum() - 1))
    m0 = int(c["init"][lo:hi].sum())
    exact = float(((1 - c["e"][lo:hi]) / 2).sum() - m0)
    return mean - m0, (var / w.sum()) ** 0.5, exact


def split(c, lo, hi):
    """Contribution to M_w's error of the uniform shrink and of the rest (z = r e + rest)."""
    z, e = c["z"], c["e"]
    r = float(z @ e / (e @ e))
    shrink = -0.5 * float(((r - 1) * e)[lo:hi].sum())
    total = -0.5 * float((z - e)[lo:hi].sum())
    return shrink, total - shrink


def main(out):
    sc_all = {}
    res = dict(note="beside, never judged; computed after the records were seen; raw counts, nothing corrected, no "
                    "shot discarded", cells={})
    for dev in RUNS:
        cs, b = circuits(dev)
        sc = json.load(open(os.path.join(NB, RUNS[dev][0], "scores.json")))["circuits"]
        sc_all[dev] = sc
        N, h = b["N"], b["N"] // 2
        ks = sorted({n[1:] for n in b["strings"]})
        worst = max(abs(m_and_se(cs[t], h, N)[0] - sc[t]["M"]) for t in cs)
        res[f"{dev}_M_vs_scores_json_worst"] = worst
        for arm in ("A0", "A1", "A2"):
            for t in b["cycles"]:
                cell = {}
                for wname, w in (("half", h), ("light_cone", 2 * t - 1), ("one_site", 1)):
                    pairs = []
                    for k in ks:
                        a, c = cs[f"{arm}_t{t}_s{k}"], cs[f"{arm}_t{t}_c{k}"]
                        ma, sa, ea = m_and_se(a, h, h + w)
                        mc, sc_, ec = m_and_se(c, h, h + w)
                        sha, rea = split(a, h, h + w)
                        shc, rec = split(c, h, h + w)
                        pairs.append(dict(k=k, S_device=ma + mc, S_exact=ea + ec, dS=ma + mc - ea - ec,
                                          se_shots=(sa ** 2 + sc_ ** 2) ** 0.5, dS_shrink=sha + shc,
                                          dS_rest=rea + rec))
                    d = np.array([p["dS"] for p in pairs])
                    se_pairs = float(d.std(ddof=1) / len(d) ** 0.5)
                    se_shots = float(np.sqrt(sum(p["se_shots"] ** 2 for p in pairs)) / len(d))
                    se = max(se_pairs, se_shots)
                    cell[wname] = dict(
                        width=w, pairs=pairs, S_exact_mean=float(np.mean([p["S_exact"] for p in pairs])),
                        S_exact_max_abs=float(max(abs(p["S_exact"]) for p in pairs)),
                        S_device_mean=float(np.mean([p["S_device"] for p in pairs])),
                        dS_mean=float(d.mean()), dS_sd=float(d.std(ddof=1)), se_pairs=se_pairs, se_shots=se_shots,
                        dS_in_2se_shots_per_pair=int(sum(abs(p["dS"]) <= 2 * p["se_shots"] for p in pairs)),
                        off_zero=bool(abs(d.mean()) > 2 * se), direction="decay (fewer 1)" if d.mean() < 0 else
                        "more 1", dS_shrink_mean=float(np.mean([p["dS_shrink"] for p in pairs])),
                        dS_rest_mean=float(np.mean([p["dS_rest"] for p in pairs])))
                cell["floor_mean"] = float(np.mean([sc[f"{arm}_t{t}_{n}"]["floor"] for n in b["strings"]]))
                res["cells"][f"{dev}_{arm}_t{t}"] = cell
    json.dump(res, open(out, "w"), indent=1)
    for dev in RUNS:
        print(f"{dev}: declared M recomputed from the shots against scores.json, worst {res[f'{dev}_M_vs_scores_json_worst']:.1e}")
    print("cell              window      S exact (max|.|)  S device  mean dS   SE pairs SE shots  >2SE  dir    "
          "pairs in 2SE  shrink part  rest part  floor")
    for key, cell in res["cells"].items():
        for wname in ("half", "light_cone", "one_site"):
            x = cell[wname]
            print(f"{key:17} {wname:10} {x['S_exact_mean']:+7.3f} ({x['S_exact_max_abs']:.1e}) {x['S_device_mean']:+8.3f} "
                  f"{x['dS_mean']:+8.3f}  {x['se_pairs']:7.3f} {x['se_shots']:8.3f}  {'yes' if x['off_zero'] else 'no':4} "
                  f"{'decay' if x['dS_mean'] < 0 else 'more1':6} {x['dS_in_2se_shots_per_pair']:5d}/14  "
                  f"{x['dS_shrink_mean']:+11.3f} {x['dS_rest_mean']:+10.3f}  {cell['floor_mean']:.3f}")


if __name__ == "__main__":
    main(sys.argv[1])
