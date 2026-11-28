"""Analysis D: how much the same circuit's raw value moves from day to day, against its shot-noise SE.
Reads only (results/ is never written). The counting is the one fixed in home's instruction of 2026-11-28 before
the run: per unit, the daily values v_d with their shot SE s_d; chi2 = sum (v_d - weighted mean)^2 / s_d^2 with
(days - 1) degrees of freedom and its p; the SD of the v_d against the median s_d. Word: p < 0.05 -> "DAY TO DAY
LARGER THAN SHOT NOISE", else "WITHIN SHOT NOISE". Copies inside one job (loopvar 2026-11-20, LV-1) are set beside
with the same counting.

Units (only where the circuits as sent are the same, checked here gate by gate on the sent circuits):
- FX-A of the daily record: M - M_exact per day, per device (marrakesh 5 days, fez 3; kingston 1 day, beside).
- Ohm ruler nights on ibm_fez, copy drow 4: raw W per cell and ruler (d)'s d per cell, 11-25 and 11-26 (the same
  169 circuits); raw W also with 11-24 on the pairs the three nights share. 11-27 (kingston) is another device.
- The balanced neuron chain, 11-17 and 11-18 (ibm_marrakesh, the same qubits): the pooled value per L.

qiskit and numpy only. usage: python notes/synthesis_2026-11-28/spread_d.py [--json OUT]
Author: The Architect <love.os.architect@proton.me>
"""
import gzip
import io
import json
import math
import os
import sys

import numpy as np
from qiskit import qpy

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RES = os.path.join(ROOT, "results")
LEVEL = 0.05


# ---- statistics -----------------------------------------------------------------------------------------------------
def chi2_sf(x, k):
    """Upper tail of the chi-square distribution (regularised incomplete gamma)."""
    a, x2 = k / 2.0, x / 2.0
    if x2 <= 0:
        return 1.0
    if x2 < a + 1:
        s = term = 1.0 / a
        n = 0
        while abs(term) > 1e-16 * abs(s):
            n += 1
            term *= x2 / (a + n)
            s += term
        return 1.0 - s * math.exp(-x2 + a * math.log(x2) - math.lgamma(a))
    b, c, d = x2 + 1 - a, 1e300, 1 / (x2 + 1 - a)
    h = d
    for i in range(1, 500):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = 1 / d if d != 0 else 1e300
        c = b + an / c
        h *= d * c
    return math.exp(-x2 + a * math.log(x2) - math.lgamma(a)) * h


def spread(days, v, s):
    """The declared counting for one unit."""
    v, s = np.asarray(v, float), np.asarray(s, float)
    w = 1 / s ** 2
    mean = float(np.sum(w * v) / np.sum(w))
    chi2 = float(np.sum((v - mean) ** 2 / s ** 2))
    df = len(v) - 1
    p = chi2_sf(chi2, df)
    sd = float(np.std(v, ddof=1))
    med = float(np.median(s))
    return dict(days=list(days), v=[float(x) for x in v], s=[float(x) for x in s], weighted_mean=mean, chi2=chi2,
                df=df, p=p, sd=sd, median_s=med, sd_over_median_s=sd / med,
                word="DAY TO DAY LARGER THAN SHOT NOISE" if p < LEVEL else "WITHIN SHOT NOISE")


# ---- jobs -----------------------------------------------------------------------------------------------------------
def load_job(job):
    man = json.load(open(f"{job}/manifest.json"))
    raw = json.load(open(f"{job}/raw_counts.json"))
    qp = f"{job}/circuits.qpy"
    blob = open(qp, "rb").read() if os.path.exists(qp) else gzip.open(qp + ".gz").read()
    circs = qpy.load(io.BytesIO(blob))
    cell = {c["cell"]: c["name"] for c in man["cells"]}
    names = [cell[p["cell"]] + (f"#{p['point']}" if cell[p["cell"]].startswith("ksent") else "") for p in man["pubs"]]
    rows = {r["pub"]: r["counts"] for r in raw["rows"]}
    return {n: (circs[i], rows[i]) for i, n in enumerate(names)}


def signature(qc):
    """The circuit as sent, gate by gate: name, parameters, physical qubits, classical bits (its name left out)."""
    def par(p):
        if hasattr(p, "data") and hasattr(p, "find_bit"):        # a control-flow block (feed-forward circuits)
            return signature(p)
        try:
            return round(float(p), 12)
        except (TypeError, ValueError):
            return str(p)

    out = []
    for ins in qc.data:
        cond = getattr(ins.operation, "condition", None)
        if cond is not None:
            tgt, val = cond
            cond = (tuple(qc.find_bit(c).index for c in (tgt if hasattr(tgt, "__iter__") else [tgt])), int(val))
        out.append((ins.operation.name, tuple(par(p) for p in ins.operation.params), cond,
                    tuple(qc.find_bit(q).index for q in ins.qubits), tuple(qc.find_bit(c).index for c in ins.clbits)))
    return tuple(out)


def measured(qc):
    return {qc.find_bit(i.qubits[0]).index: qc.find_bit(i.clbits[0]).index for i in qc.data if i.operation.name == "measure"}


def per_shot(counts, clbits, weights=None):
    """Per qubit <Z>; the per-shot weighted sum over the qubits: its mean and the variance of one shot."""
    w = np.ones(len(clbits)) if weights is None else np.asarray(weights, float)
    tot = sum(counts.values())
    z, s1, s2 = np.zeros(len(clbits)), 0.0, 0.0
    for key, c in counts.items():
        b = key.replace(" ", "")
        v = np.array([1 - 2 * int(b[-1 - k]) for k in clbits])
        z += c * v
        x = float(w @ v)
        s1 += c * x
        s2 += c * x * x
    z /= tot
    mu = s1 / tot
    return z, mu, (s2 / tot - mu * mu) * tot / (tot - 1), tot


# ---- unit 1: FX-A of the daily record -----------------------------------------------------------------------------
def fxa():
    rec, sigs = {}, {}
    for day in sorted(os.listdir(f"{RES}/daily")):
        if not day.startswith("2026-"):
            continue
        ans = json.load(open(f"{RES}/daily/{day}/answers.json"))["FX-A"]
        for dev in sorted(os.listdir(f"{RES}/daily/{day}")):
            run = f"{RES}/daily/{day}/{dev}/run"
            if not dev.startswith("ibm_") or not os.path.isdir(f"{run}/job"):
                continue
            jobs = load_job(f"{run}/job")
            tag = "p2d_FX-A" if "p2d_FX-A" in jobs else "p2d_user"   # 11-06: FX-A run alone, psf-os tag 'user'
            if tag not in jobs:
                continue
            rj = json.load(open(f"{run}/runs/{tag}.json"))
            mp = rj["mapping"] if isinstance(rj["mapping"], dict) else json.loads(rj["mapping"].replace("'", '"'))
            qc, counts = jobs[tag]
            m = measured(qc)
            labs = sorted(ans, key=int)
            phys = [int(mp[l]) for l in labs]
            z, mu, var1, n = per_shot(counts, [m[q] for q in phys])
            exact = np.array([ans[l] for l in labs])
            v = float(z.mean() - exact.mean())
            se = math.sqrt(var1 / n) / len(phys)       # SE of the mean over the qubits, from the per-shot sum
            sc = f"{run}/scores.json"
            prob = json.load(open(sc))["problems"] if os.path.exists(sc) else {}
            rec_diff = (prob.get("FX-A") or prob.get("user") or {}).get("diff")
            rec.setdefault(dev, []).append(dict(day=day, v=v, s=se, shots=n, copy=rj["copy"]["drow"],
                                                physical=sorted(phys), recorded_diff=rec_diff))
            sigs.setdefault(dev, {})[day] = signature(qc)
    out = {}
    for dev, rows in rec.items():
        same = len({sigs[dev][r["day"]] for r in rows}) == 1
        same_q = len({tuple(r["physical"]) for r in rows}) == 1
        u = dict(rows=rows, same_sent_circuit=same, same_physical_qubits=same_q)
        if len(rows) >= 2:
            u.update(spread([r["day"] for r in rows], [r["v"] for r in rows], [r["s"] for r in rows]))
        else:
            u["word"] = "BESIDE (one day)"
        out[f"FX-A {dev}"] = u
    return out


# ---- unit 2: the Ohm ruler nights on ibm_fez, copy drow 4 ----------------------------------------------------------
RULER = {"2026-11-24": "ohm-ruler-night-2026-11-24/or", "2026-11-25": "ohm-ruler3-night-2026-11-25/or3",
         "2026-11-26": "ohm-ruler4-night-2026-11-26/or4"}
ANS = f"{RES}/ohm-ruler3-night-2026-11-25/answers/ohm_ruler3_answers_by_label.json"


def window(t):
    return list(range(20, 20 + 2 * t - 1))


def ruler_cell(night, jobs, B, AL, a, t, K, with_d):
    strs = B["strings"]
    W, VW, WE, S_O = [], [], [], []
    for k in range(K):
        lab = {x: f"{a}_t{t}_L_{x}{k:02d}" for x in "sc"}
        it = B["items"][lab["s"]]
        ph = dict(zip(it["positions"], it["physical"]))
        wq = [ph[p] for p in window(t)]
        sums, vars_, ex = {}, {}, {}
        for x in "sc":
            qc, counts = jobs[f"p2d_{lab[x]}"]
            m = measured(qc)
            z, mu, var1, n = per_shot(counts, [m[q] for q in wq])
            sums[x], vars_[x] = mu, var1 / n
            ex[x] = sum(AL["z"][lab[x]][str(q)] for q in wq)
        ms = sum(int(strs[f"s{k:02d}"][p]) for p in window(t))
        mc = sum(int(strs[f"c{k:02d}"][p]) for p in window(t))
        const = -(ms - mc) / 2
        W.append(-(sums["s"] - sums["c"]) / 4 + const)          # -sum_window O / 2 + const, O = (Z_s - Z_c) / 2
        VW.append((vars_["s"] + vars_["c"]) / 16)
        WE.append(-(ex["s"] - ex["c"]) / 4 + const)
        S_O.append((sums["s"] - sums["c"]) / 2)
    W, VW, WE, S_O = map(np.array, (W, VW, WE, S_O))
    res = dict(W=float(W.mean()), W_se=float(math.sqrt(VW.sum()) / K))
    if with_d:
        it = B["items"][f"{a}_t{t}_L_s00"]
        ph = dict(zip(it["positions"], it["physical"]))
        wq = [ph[p] for p in window(t)]
        sign = np.array([1 - 2 * int(strs["s00"][p]) for p in window(t)])
        zz, vv = {}, {}
        for x in ("s00", "c00"):
            qc, counts = jobs[f"p2d_{a}_t{t}_L_{x}_smirror"]
            m = measured(qc)
            z, mu, var1, n = per_shot(counts, [m[q] for q in wq], sign)
            zz[x], vv[x] = z, var1 / n / len(wq) ** 2            # SE^2 of the per-shot weighted mean
        mq = (zz["s00"] - zz["c00"]) / 2 * sign
        md = float(mq.mean())
        rho = math.sqrt(md)
        consts = W + S_O / 2                                    # W = -S_O / 2 + const
        Wd = -(S_O / rho) / 2 + consts
        dd = Wd - WE
        se_md = math.sqrt(vv["s00"] + vv["c00"]) / 2
        slope = float(np.mean(S_O)) / (4 * md ** 1.5)
        res.update(d=float(dd.mean()), d_se=math.sqrt(float(VW.sum()) / K ** 2 / md + (slope * se_md) ** 2), rho_d=rho)
    return res


def ruler():
    AL = json.load(open(ANS))
    nights = {d: (load_job(f"{RES}/{p}/job"), json.load(open(f"{RES}/{p}/build.json"))) for d, p in RULER.items()}
    out, checks = {}, {}
    # the circuits as sent, compared gate by gate on every user circuit the nights share
    for d1, d2 in (("2026-11-25", "2026-11-26"), ("2026-11-24", "2026-11-25")):
        j1, j2 = nights[d1][0], nights[d2][0]
        common = sorted(n for n in j1 if n in j2 and n.startswith("p2d_"))
        same = [n for n in common if signature(j1[n][0]) == signature(j2[n][0])]
        checks[f"{d1} vs {d2}"] = dict(common_p2d=len(common), same=len(same),
                                       differ=sorted(set(common) - set(same))[:20])
    pairs = {"2026-11-24": {1: 7, 3: 7, 4: 7}, "2026-11-25": {1: 7, 3: 7, 4: 9}, "2026-11-26": {1: 7, 3: 7, 4: 9}}
    for a in ("A0", "A1", "A2"):
        for t in (1, 3, 4):
            # 11-25 and 11-26, the full job: raw W and ruler (d)
            r = {d: ruler_cell(d, *nights[d], AL, a, t, pairs[d][t], True) for d in ("2026-11-25", "2026-11-26")}
            out[f"ruler raw W {a} t{t}"] = spread(list(r), [x["W"] for x in r.values()], [x["W_se"] for x in r.values()])
            out[f"ruler (d) d {a} t{t}"] = spread(list(r), [x["d"] for x in r.values()], [x["d_se"] for x in r.values()])
            # with 11-24, on the pairs the three nights share (7)
            r3 = {d: ruler_cell(d, *nights[d], AL, a, t, 7, False) for d in RULER}
            out[f"ruler raw W {a} t{t}, three nights, 7 shared pairs"] = spread(
                list(r3), [x["W"] for x in r3.values()], [x["W_se"] for x in r3.values()])
    return out, checks


# ---- unit 3: the balanced neuron chain, 11-17 and 11-18 --------------------------------------------------------------
def balanced():
    days = {"2026-11-17": "balanced-night-2026-11-17", "2026-11-18": "balanced-repeat-2026-11-18"}
    sc = {d: json.load(open(f"{RES}/{p}/balanced_scores.json"))["rows"] for d, p in days.items()}
    j = {d: load_job(f"{RES}/{p}/job") for d, p in days.items()}
    names = sorted(n for n in j["2026-11-17"] if n.startswith("ff_"))
    same = [n for n in names if n in j["2026-11-18"] and signature(j["2026-11-17"][n][0]) == signature(j["2026-11-18"][n][0])]
    out = {}
    for L in sorted(sc["2026-11-17"], key=int):
        out[f"balanced pooled L{L}"] = spread(list(days), [sc[d][L]["p_pooled"] for d in days], [sc[d][L]["se"] for d in days])
    return out, dict(ff_circuits=len(names), same=len(same), differ=sorted(set(names) - set(same)))


# ---- beside: copies inside one job (loopvar, LV-1) and the three jobs a minute apart ---------------------------------
def loopvar():
    rows = json.load(open(f"{RES}/loopvar-night-2026-11-20/loopvar_scores.json"))["rows"]
    within, between = {}, {}
    for L, r in rows.items():
        for job, cp in r["per_job_copy"].items():
            within[f"copies L{L} {job}"] = spread(["a", "b"], [cp["a"]["g"], cp["b"]["g"]], [cp["a"]["se"], cp["b"]["se"]])
        between[f"jobs L{L}"] = spread(list(r["g_job"]), list(r["g_job"].values()), list(r["se_job"].values()))
    return within, between


def main():
    res = {}
    res["fxa"] = fxa()
    res["ruler"], res["ruler_circuit_check"] = ruler()
    res["balanced"], res["balanced_circuit_check"] = balanced()
    res["beside_copies_in_one_job"], res["beside_jobs_a_minute_apart"] = loopvar()
    summ = {}
    for grp in ("fxa", "ruler", "balanced", "beside_copies_in_one_job", "beside_jobs_a_minute_apart"):
        u = [v for v in res[grp].values() if "p" in v]
        summ[grp] = dict(units=len(u), larger=sum(v["p"] < LEVEL for v in u),
                         median_sd_over_median_s=float(np.median([v["sd_over_median_s"] for v in u])) if u else None)
    res["summary"] = summ
    if "--json" in sys.argv:
        json.dump(res, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1)
    for grp in ("fxa", "ruler", "balanced", "beside_copies_in_one_job", "beside_jobs_a_minute_apart"):
        print(f"== {grp}")
        for k, v in res[grp].items():
            if "p" in v:
                print(f"  {k:52s} n {len(v['v'])} chi2 {v['chi2']:8.2f} df {v['df']} p {v['p']:.3g}  SD/med s "
                      f"{v['sd_over_median_s']:6.2f}  {v['word']}")
            else:
                print(f"  {k:52s} {v.get('word')}")
    print("ruler circuits:", res["ruler_circuit_check"])
    print("balanced circuits:", res["balanced_circuit_check"])
    print("summary:", json.dumps(summ))


if __name__ == "__main__":
    main()
