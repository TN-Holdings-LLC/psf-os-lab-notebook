"""The two rules on simulated nights with a drift between jobs (home VS Claude, 2026-11-21; desk only).

THE NOISE IS AN ILLUSTRATION (notes/os2_2026-11-18/branch_noise.py's form; never fitted to a device). On top of it, a
drift between jobs of the TYPE seen on 2026-11-20 (results/loopvar-night-2026-11-20: copies inside one job agree, jobs
minutes apart move): each job's damping is gamma * (1 + eps), eps ~ Normal(0, s) drawn per job. s is chosen so that the
excess between-job SD of g it produces is of the size loopvar read (0.007 - 0.014); the value is written in the output.
This sets the shape of the drift, not the noise's size to a device.

Every night uses the same diagnostics' pick (the dry diagnostics of the noise) and the same series of drifts and shot
seeds for both rules (night i: eps of job j and the counts of a circuit in job j drawn from seeds (SEED, i, j, tag)).
The shares come from catalog.py (exact, per circuit, on a grid of eps; linear between grid points); each job's counts
are Binomial(4000, share). The rules are psf-os's own: psf_os.loop.next_stacks (as declared for 2026-11-19) and
psf_os.loop.next_stacks_paired (branch loop-paired-2026-11-21), applied to rows built as gpu/os3_night.py's score and
gpu/os_loop_paired.py's score build them. Seconds: psf-os's time model per job (0.036 s per circuit + 0.00027 s per
shot + 3 s), the diagnostics 55.2 s, budget 240 s, as the night runner counts them.

What is true is decided without drift and without shot noise: d_true(a -> b) = |P(a) - exact| - |P(b) - exact| from
the exact shares at eps = 0, a share above the stack's noiseless value (a readout artifact, what the rules call
OVERSHOOT) credited as P0's. Counted per night (summed over L):
  wrong step     a change of stack the rule made with d_true <= MARGIN (not truly effective; the first step from P0
                 counts too, as it is a step the night takes)
  harmful step   a change with d_true < -MARGIN (beside)
  missed         an L whose final stack has a neighbour (one step of the shared ladder: the base on P0, B, M, F, Q)
                 with d_true > MARGIN
  distance       mean over L of |P(final) - exact| (exact shares at eps = 0)
  seconds        model seconds of the night (diagnostics and rounds run)

  python sim_compare.py CATALOG.json PICK_JSON --nights 50 --drift S [--k-max-paired K] [--out OUT.json]
  python sim_compare.py CATALOG.json PICK_JSON --calibrate      the between-job SD of g per L for a given s"""
import argparse
import json
import math
import os
import sys
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(NB, "gpu"))

from psf_os import loop as LP  # noqa: E402

LS = (1, 2, 3)
SHOTS = 4000
DIAG_S = 55.2
BUDGET = 240.0
MARGIN = 0.005
SEED = 20261121
PROBE_POS = (1, 3, 5, 7, 9)
OFFSETS = (0, 2, 4)
EXACT = {L: math.sin(math.atan(math.tan(1.1) ** 2)) ** (2 * L) for L in LS}


def seconds(n):
    return round(n * 0.036 + n * SHOTS * 0.00027 + 3.0, 1)


class Cat:
    def __init__(self, path):
        c = json.load(open(path))
        self.noise, self.grid, self.items, self.probe = c["noise"], c["grid"], c["items"], c["probe_chain"]

    def share(self, tag, eps):
        return float(np.interp(eps, self.grid, self.items[tag]["p"]))

    def tags(self, st, L):
        if list(st) == ["P0"]:
            return [f"p0_{L}"]
        m = 3 if "M" in st else 2
        o = int([x for x in st if x.startswith("Q")][0][1:]) if any(x.startswith("Q") for x in st) else 0
        if "B" in st:
            return [f"P2m{m}L{L}o{o}", f"NFm{m}L{L}o{o}"]
        return [f"P1m{m}L{L}"] if st[0] == "P1" else [f"P2m{m}L{L}o0"]

    def true_p(self, st, L):
        ts = self.tags(st, L)
        return sum(self.share(t, 0.0) for t in ts) / len(ts)

    def noiseless(self, st, L):
        ts = self.tags(st, L)
        return sum(self.items[t]["noiseless"] for t in ts) / len(ts)

    def credible(self, st, L):
        """The true share, credited only when it does not exceed the stack's noiseless value by more than 2 SE of
        4000 shots (the rules' OVERSHOOT test at its expected value): a share above it is an artifact of the noise
        and is credited as P0's."""
        p = self.true_p(st, L)
        return self.true_p(["P0"], L) if p > self.noiseless(st, L) + 2 * se(p, SHOTS) * (
            1 if len(self.tags(st, L)) == 1 else 1 / math.sqrt(2)) else p

    def value(self, st, L, literal):
        return self.true_p(st, L) if literal else self.credible(st, L)


def rng_for(night, job, tag):
    return np.random.default_rng([SEED, night, job, zlib.crc32(tag.encode())])


def se(p, n):
    return math.sqrt(max(p * (1 - p), 0.0) / n)


def read(cat, st, L, night, job, eps):
    """One stack read in one job: p, its SE, noiseless, overshoot, and the readings the rules use."""
    ts = cat.tags(st, L)
    ps = [rng_for(night, job, t).binomial(SHOTS, cat.share(t, eps)) / SHOTS for t in ts]
    if len(ts) == 1:
        p, s = ps[0], se(ps[0], SHOTS)
        nl = cat.noiseless(st, L)
        info = dict(output_qubit=cat.items[ts[0]]["output_qubit"])
    else:
        pr, pn = ps
        nlr, nln = cat.items[ts[0]]["noiseless"], cat.items[ts[1]]["noiseless"]
        p, s, nl = (pr + pn) / 2, math.sqrt(se(pr, SHOTS) ** 2 + se(pn, SHOTS) ** 2) / 2, (nlr + nln) / 2
        info = dict(share_gap=pr / nlr - pn / nln,
                    share_gap_two_se=2 * math.sqrt((se(pr, SHOTS) / nlr) ** 2 + (se(pn, SHOTS) / nln) ** 2),
                    output_qubit_nf=cat.items[ts[1]]["output_qubit"], output_qubit=cat.items[ts[0]]["output_qubit"])
    return dict(p=p, se=s, noiseless=nl, overshoot=bool(p > nl + 2 * s), info=info, n=len(ts))


def dr_of(cat, night, job):
    out = {}
    for pos in PROBE_POS:
        q = cat.probe[pos]
        p11t = float(cat.noise.get("p11", {}).get(str(q), 1.0))
        p00t = float(cat.noise.get("p00", {}).get(str(q), 1.0))
        r = rng_for(night, job, f"dr{q}")
        p11, p00 = r.binomial(SHOTS, p11t) / SHOTS, r.binomial(SHOTS, p00t) / SHOTS
        s = math.sqrt(se(p11, SHOTS) ** 2 + se(p00, SHOTS) ** 2)
        d = p00 - p11
        out[str(q)] = dict(p11=p11, p00=p00, gap=d, two_se=2 * s, sig=bool(d > 0 and d >= 2 * s))
    return out


def q_choice_for(cat):
    """R2's offset as gpu/os_loop.py's q_choice: the offset whose last output qubit reads with the smallest gap."""
    def q(key, row, dr):
        L = int(key)
        ch = cat.probe
        cands = [(dr[str(ch[o + 2 * L - 1])]["gap"], o) for o in OFFSETS
                 if o + 2 * L - 1 < len(ch) and str(ch[o + 2 * L - 1]) in dr]
        best = min(cands) if cands else None
        return best[1] if best and best[1] != 0 else None
    return q


def old_night(cat, pick, night, eps, k_max=4):
    stacks = {str(L): [pick[str(L)]] for L in LS}
    rules = [stacks]
    rounds, spent = [], DIAG_S
    qc = q_choice_for(cat)
    for k in range(1, k_max + 1):
        n = 9 + 3 + 4 + sum(0 if stacks[str(L)] == ["P0"] else 3 * len(cat.tags(stacks[str(L)], L)) for L in LS)
        if spent + seconds(n) > BUDGET + 1e-9:
            break
        spent += seconds(n)
        rows = {}
        for L in LS:
            key, st = str(L), stacks[str(L)]
            p0r = read(cat, ["P0"], L, night, k, eps[k])
            row = dict(stack=st, p0=p0r["p"], exact=EXACT[L])
            if st == ["P0"]:
                row.update(verdict="NO PRESCRIPTION")
            else:
                r = read(cat, st, L, night, k, eps[k])
                gain = abs(p0r["p"] - EXACT[L]) - abs(r["p"] - EXACT[L])
                g_se = math.sqrt(p0r["se"] ** 2 + r["se"] ** 2)
                v = "OVERSHOOT" if r["overshoot"] else ("PRESCRIPTION HELPS" if (gain > 0 and gain >= 2 * g_se)
                                                        else "NOT SHOWN")
                row.update(r["info"], p=r["p"], overshoot=r["overshoot"], g=gain, g_se=g_se, verdict=v)
            rows[key] = row
        rounds.append(dict(round=k, device="sim", rows=rows, dr=dr_of(cat, night, k), model_seconds_so_far=spent))
        R = LP.next_stacks(rounds, q_choice=qc, k_max=k_max, budget=BUDGET)
        stacks = R["stacks"]
        rules.append(stacks)
        if R["stop"]:
            break
    return rules, spent, len(rounds)


def paired_night(cat, pick, night, eps, k_max=4, climb=False):
    R = LP.paired_rule1(dict(round=1, device="sim", stacks={str(L): [pick[str(L)]] for L in LS}, why={}),
                        {str(L): [pick[str(L)]] for L in LS}, dict(per_key={}))
    rules = [R["stacks"]]
    rounds, spent = [], DIAG_S
    qc = q_choice_for(cat)
    for k in range(1, k_max + 1):
        if R.get("stop"):
            break
        n = 9 + 3 + 4
        for L in LS:
            c, i = R["candidates"][str(L)], R["stacks"][str(L)]
            if c:
                n += 3 * len(cat.tags(c, L)) + (0 if i == ["P0"] else len(cat.tags(i, L)))
        if spent + seconds(n) > BUDGET + 1e-9:
            break
        spent += seconds(n)
        rows = {}
        for L in LS:
            key = str(L)
            inc, cand = R["stacks"][key], R["candidates"][key]
            p0r = read(cat, ["P0"], L, night, k, eps[k])
            row = dict(stack=inc, candidate=cand, step=R["steps"][key], tried=R["tried"][key], pick=R["pick"][key],
                       exact=EXACT[L], p0=p0r["p"])
            if cand:
                a = p0r if inc == ["P0"] else read(cat, inc, L, night, k, eps[k])
                b = read(cat, cand, L, night, k, eps[k])
                if inc == ["P0"]:
                    a = dict(a, info=dict(output_qubit=cat.items[f"p0_{L}"]["output_qubit"]))
                row.update(inc_p=a["p"], inc_se=a["se"], inc_info=a["info"], cand_p=b["p"], cand_se=b["se"],
                           cand_overshoot=b["overshoot"], cand_info=b["info"])
            rows[key] = row
        rounds.append(dict(round=k, device="sim", rows=rows, dr=dr_of(cat, night, k), model_seconds_so_far=spent))
        R = LP.next_stacks_paired(rounds, q_choice=qc, k_max=k_max, budget=BUDGET, climb_on_kept=climb)
        rules.append(R["stacks"])
    return rules, spent, len(rounds)


def neighbours(st, pick):
    st = list(st)
    out = []
    if st == ["P0"]:
        out.append([pick])
    if "B" not in st:
        out.append(["P2", "B"])
        if st != ["P0"]:
            if "M" not in st:
                out.append(st + ["M"])
            if "F" not in st and st[0] in ("P1", "P2"):
                out.append([{"P1": "P2", "P2": "P1"}[st[0]]] + st[1:] + ["F"])
    elif not any(x.startswith("Q") for x in st):
        out += [st + ["Q2"], st + ["Q4"]]
    return out


def metrics(cat, pick, rules, literal=False):
    wrong = harmful = missed = 0
    dist = []
    start = {str(L): ["P0"] for L in LS}
    seq = [start] + rules
    for L in LS:
        key = str(L)
        for a, b in zip(seq, seq[1:]):
            if list(a[key]) != list(b[key]):
                d = abs(cat.value(a[key], L, literal) - EXACT[L]) - abs(cat.value(b[key], L, literal) - EXACT[L])
                wrong += d <= MARGIN
                harmful += d < -MARGIN
        fin = seq[-1][key]
        df = abs(cat.value(fin, L, literal) - EXACT[L])
        dist.append(df)
        if any(df - abs(cat.value(nb, L, literal) - EXACT[L]) > MARGIN for nb in neighbours(fin, pick[key])):
            missed += 1
    return wrong, harmful, missed, sum(dist) / len(dist)


def calibrate(cat, pick, s):
    """The between-job SD of g (incumbent P0, the pick) that drift s produces, per L (first order in eps)."""
    out = {}
    for L in LS:
        st = [pick[str(L)]]
        h = 0.05

        def g(e):
            p0 = cat.share(f"p0_{L}", e)
            ts = cat.tags(st, L)
            p = sum(cat.share(t, e) for t in ts) / len(ts)
            return abs(p0 - EXACT[L]) - abs(p - EXACT[L])
        slope = (g(h) - g(-h)) / (2 * h)
        out[str(L)] = dict(dg_deps=slope, sd_g=abs(slope) * s)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("catalog")
    ap.add_argument("pick")
    ap.add_argument("--nights", type=int, default=50)
    ap.add_argument("--drift", type=float, default=0.0)
    ap.add_argument("--k-max-paired", type=int, default=4)
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()
    cat = Cat(a.catalog)
    pick = json.loads(a.pick)
    cal = calibrate(cat, pick, a.drift)
    if a.calibrate:
        print(json.dumps(cal, indent=1))
        return
    res = dict(noise=cat.noise, illustrative=True, drift_s=a.drift, between_job_sd_g=cal, pick=pick,
               nights=a.nights, margin=MARGIN, rules={})
    for name, fn, km in (("current (next_stacks, K 4)", old_night, 4),
                         (f"paired (next_stacks_paired, K {a.k_max_paired})", paired_night, a.k_max_paired),
                         (f"paired + climb_on_kept (K {a.k_max_paired})",
                          lambda *x: paired_night(*x, climb=True), a.k_max_paired)):
        rows = []
        for i in range(a.nights):
            r = np.random.default_rng([SEED, i, 999])
            eps = [0.0] + list(r.normal(0.0, a.drift, size=12)) if a.drift else [0.0] * 13
            rules, spent, nr = fn(cat, pick, i, eps, km)
            w, h, m, d = metrics(cat, pick, rules)
            wl, hl, ml, dl = metrics(cat, pick, rules, literal=True)
            rows.append(dict(wrong=w, harmful=h, missed=m, distance=d, wrong_literal=wl, harmful_literal=hl,
                             missed_literal=ml, distance_literal=dl, seconds=spent, rounds=nr,
                             final={k: "+".join(v) for k, v in rules[-1].items()},
                             path=[{k: "+".join(v) for k, v in r.items()} for r in rules]))
        agg = {k: float(np.mean([x[k] for x in rows])) for k in (
            "wrong", "harmful", "missed", "distance", "wrong_literal", "harmful_literal", "missed_literal",
            "distance_literal", "seconds", "rounds")}
        finals = {}
        for x in rows:
            f = json.dumps(x["final"], sort_keys=True)
            finals[f] = finals.get(f, 0) + 1
        res["rules"][name] = dict(mean=agg, finals=dict(sorted(finals.items(), key=lambda kv: -kv[1])[:4]),
                                  nights=rows)
        print(f"{name}: wrong steps {agg['wrong']:.2f} / night (harmful {agg['harmful']:.2f}), missed "
              f"{agg['missed']:.2f} L / night, final distance {agg['distance']:.4f}, seconds {agg['seconds']:.1f}, "
              f"rounds {agg['rounds']:.2f}; literal truth: wrong {agg['wrong_literal']:.2f} (harmful "
              f"{agg['harmful_literal']:.2f}), missed {agg['missed_literal']:.2f}, distance {agg['distance_literal']:.4f}",
              flush=True)
    best = {str(L): min(abs(cat.credible(st, L) - EXACT[L]) for st in [["P0"], [pick[str(L)]]] +
                        [n for n in neighbours([pick[str(L)]], pick[str(L)])]) for L in LS}
    res["reference"] = dict(credible={str(L): {"+".join(st): cat.credible(st, L) for st in
                                                [["P0"], ["P1"], ["P1", "M"], ["P2"], ["P2", "M"], ["P2", "B"],
                                                 ["P2", "B", "M"], ["P2", "F"], ["P2", "M", "F"], ["P1", "F"],
                                                 ["P1", "M", "F"], ["P2", "B", "Q2"], ["P2", "B", "Q4"]]}
                                      for L in LS},
                            p0_distance={str(L): abs(cat.true_p(["P0"], L) - EXACT[L]) for L in LS},
                            true_p={str(L): {"+".join(st): cat.true_p(st, L) for st in
                                             [["P0"], ["P1"], ["P1", "M"], ["P2"], ["P2", "M"], ["P2", "B"],
                                              ["P2", "B", "M"], ["P2", "F"], ["P2", "M", "F"], ["P1", "F"],
                                              ["P1", "M", "F"], ["P2", "B", "Q2"], ["P2", "B", "Q4"]]}
                                    for L in LS}, one_step_best=best)
    if a.out:
        json.dump(res, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
