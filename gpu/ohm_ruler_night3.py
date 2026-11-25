"""Ohm with rulers inside the circuit, the third night's candidates (workplace Claude, 2026-11-25; not declared).

The declared tool of 2026-11-24, gpu/ohm_ruler_night.py, and gpu/ohm_ruler_night2.py are imported read only and not
changed. This file adds:

  build3  as the declared build, with two options that the declared build does not have:
            --smirrors sc   per cell, string mirrors on s00 and c00: the compiled circuit, a barrier, its inverse, a
                            barrier, X on the physical qubits whose bit is 1, Z readout (ideal: <Z_q> = 1 - 2 b_q);
                            records p2d_<tag>_smirror (kind user2d_smirror). "s": on s00 alone. "none" (default).
            --pairs-t T:K   pairs per t (e.g. 4:9); the answers file must hold the largest K (the same rule's draws)
  check3  the declared check, then every string mirror against its string (1e-6)
  score3  every candidate's words side by side (the declaration chooses which are judged):
            raw M, W (as 11-24); the one-factor test (as 11-24, with its shot-noise SE, NOT READ on a 0 SE);
            rulers (a) total, (b) |0> mirror, (c) |0> mirror on the window, (d) string mirrors' odd part on the window,
            (d1) the s00 string mirror alone on the window;
            candidate 1: (b), (c), (d), (d1) again with the qubits whose mirror value is below --tau left out of the mean
                         (NOT READ when fewer than half are left);
            candidate 3: the direction r - rho_a per cell (the window's own factor against the circuit's total).
          Words: AGREES when |d| < t_{0.975, K-1} SE (prereg rule 4), DIFFERS otherwise, NOT READ when SE = 0 (rule 5);
          the 2 SE word beside. The one-factor test keeps its chi2 (its SE is shot noise, not the pairs' scatter).

The SEs of the one-factor test are shot-noise SEs (var Z = (1 - Z^2) / shots), not bootstrap SEs over pairs: the
declared tool's comment says "bootstrap" where its code uses shot noise (noted by the workplace VS, 2026-11-25).

  PYTHONPATH=<psf-os 0.3.3>:<TOQB> python gpu/ohm_ruler_night3.py build3 DEV OUT ANS_IN ANS_OUT [--smirrors sc]
  python gpu/ohm_ruler_night3.py check3 OUT ANS_BY_LABEL
  python gpu/ohm_ruler_night3.py score3 OUT ANS_BY_LABEL [--tau 0.3]
"""
import argparse
import hashlib
import json
import math
import os
import shutil
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ohm_ruler_night as ORN  # noqa: E402  (read only: the declared tool of 2026-11-24)
import ohm_ruler_night2 as ORN2  # noqa: E402  (read only: t quantile table)

TAU = 0.3            # [OWNER] candidate 1: a qubit whose mirror value is below TAU leaves the ruler's mean
KEEP_FRACTION = 0.5  # [OWNER] candidate 1: fewer than this fraction left -> NOT READ
RULERS = ("a", "b", "c", "d", "d1")


def pairs_by_t(spec, ts, kmax):
    out = {t: kmax for t in ts}
    for s in spec or []:
        t, k = s.split(":")
        out[int(t)] = int(k)
    if max(out.values()) > kmax:
        raise SystemExit(f"STOP: --pairs-t asks for more pairs than the answers hold ({kmax})")
    return out


def word(d, se, K):
    """Rule 4 (t quantile, K - 1 dof) and rule 5 (SE 0: NOT READ); the 2 SE word beside."""
    if not (se > 0) or not math.isfinite(se) or not math.isfinite(d):
        return dict(t="NOT READ", **{"2se": "NOT READ"})
    tq = ORN2.t975(K - 1)
    return {"t": "AGREES" if abs(d) < tq * se else "DIFFERS", "2se": "AGREES" if abs(d) < 2 * se else "DIFFERS"}


def string_mirror(c, flips):
    """The compiled |0> mirror c (body, barrier, inverse, measures) with a barrier and X on `flips` (physical qubits)
    inserted before its measurements: ideal readout = the string."""
    from qiskit import QuantumCircuit
    out = QuantumCircuit(*c.qregs, *c.cregs, name=c.name)
    meas = [ins for ins in c.data if ins.operation.name == "measure"]
    for ins in c.data:
        if ins.operation.name != "measure":
            out.append(ins)
    out.barrier()
    for q in flips:
        out.x(q)
    for ins in meas:
        out.append(ins)
    return out


# --------------------------------------------------------------------------------------------------------- build3

def cmd_build3(a):
    sys.path.insert(0, HERE)
    import hub_build as HB
    from qiskit import qpy
    from psf_os import device as Dv
    from psf_os import job as J
    from psf_os import lattice2d as L
    from psf_os import user2d as U
    OW = ORN.OW
    for p in (a.out, a.ans_out):
        if os.path.exists(p):
            raise SystemExit(f"STOP: {p} exists")
    dev = Dv.Device.load(a.dev)
    A = json.load(open(a.ans_in))
    meta = A["meta"]
    ts, forms = tuple(meta["cycles"]), tuple(meta["forms"])
    if forms != ("L",):
        raise SystemExit("STOP: build3 builds the light-cone circuits alone (form L), as plan B")
    strs, _ = ORN.strings(meta["pairs"], ts, forms)
    if {n: "".join(map(str, b)) for n, b in strs} != meta["strings"]:
        raise SystemExit("REFUSED: the strings regenerated from the rule differ from the answers file's")
    kt = pairs_by_t(a.pairs_t, ts, meta["pairs"])
    chain, how = HB.chain_of(dev, ORN.N)
    probe = HB.on_chain(OW.logical("A1", 1, "F", strs[0][1]), chain, dev.num_qubits)
    lab, edges, _ = U.analyse(probe, dev)
    dr, dc, m, reasons = L.place(dev, edges, lab)
    phys_of_pos = [int(m[chain[k]]) for k in range(ORN.N)]
    items, want = [], {}
    for arm in ORN.ARMS:
        for t in ts:
            pos = ORN.positions(t, "L")
            where = [phys_of_pos[k] for k in pos]
            for name, bits in strs:
                if int(name[1:]) >= kt[t]:
                    continue
                tg = ORN.tag(arm, t, "L", name)
                items.append((tg, HB.on_chain(OW.logical(arm, t, "L", bits), where, dev.num_qubits)))
                want[tg] = dict(positions=pos, given_labels=where, physical=[phys_of_pos[k] for k in pos])
    HB._mirror_from_compiled(dev, U)
    OW._pin_light_cone(L, {frozenset(w["given_labels"]) for w in want.values()})
    first = os.path.join(a.out, "unsent_first_build")
    rep = U.build_batch(dev, items, first, shots=a.shots, max_seconds=1e9)
    bad = [tg for tg, w in want.items()
           if [int(rep["items"][tg]["mapping"][str(lb)]) for lb in w["given_labels"]] != w["physical"]]
    if bad:
        raise SystemExit(f"STOPPED: psf-os placed {len(bad)} items off F's physical qubits (e.g. {bad[:3]}).")
    mirrors = {ORN.tag(arm, t, "L", "s00") for arm in ORN.ARMS for t in ts}
    smir = {"none": [], "s": ["s00"], "sc": ["s00", "c00"]}[a.smirrors]
    runs, unsent = os.path.join(a.out, "runs"), os.path.join(a.out, "unsent_runs")
    shutil.copytree(os.path.join(first, "runs"), runs)
    os.makedirs(unsent)
    for tg in want:
        for suf, keep in (("_floor", False), ("_mirror", tg in mirrors)):
            if keep:
                continue
            for ext in (".json", ".qpy"):
                p = os.path.join(runs, f"p2d_{tg}{suf}{ext}")
                if os.path.exists(p):
                    shutil.move(p, os.path.join(unsent, os.path.basename(p)))
    smirrors = []
    for arm in ORN.ARMS:
        for t in ts:
            for nm in smir:
                tg = ORN.tag(arm, t, "L", nm)
                src = os.path.join(first, "runs", f"p2d_{tg}_mirror")
                rec = json.load(open(src + ".json"))
                c = qpy.load(open(src + ".qpy", "rb"))[0]
                bits = meta["strings"][nm]
                flips = [want[tg]["physical"][i] for i, p in enumerate(want[tg]["positions"]) if bits[p] == "1"]
                sm = string_mirror(c, flips)
                labels = rec["labels"]
                mapping = {int(k) if str(k).lstrip("-").isdigit() else k: v for k, v in rec["mapping"].items()}
                U._record(dev, runs, f"p2d_{tg}_smirror", "mirror", "user2d_smirror", [sm],
                          [dict(input="m", setting="z")], labels, mapping,
                          dict(cz=int(sm.count_ops().get("cz", 0)), tag=tg, string=nm, flips=flips), a.shots, True)
                smirrors.append(tg)
    man = J.assemble(dev, runs, os.path.join(a.out, "job"), max_seconds=a.max_seconds)
    n_c = len(man["pubs"])
    cz, depth = {}, {}
    errs = []
    for tg in want:
        c = qpy.load(open(os.path.join(runs, f"p2d_{tg}.qpy"), "rb"))[0]
        cz[tg] = int(c.count_ops().get("cz", 0))
        depth[tg] = int(c.depth(filter_function=lambda i: i.operation.name == "cz"))
        arm, tt, _, _ = tg.split("_")
        t = int(tt[1:])
        if cz[tg] != ORN.CZ_PER_FSIM[arm] * OW.fsim_count(t, "L"):
            errs.append(f"{tg}: CZ {cz[tg]}")
        if c.count_ops().get("delay", 0):
            errs.append(f"{tg}: a delay")
    for tg in smirrors:
        c = qpy.load(open(os.path.join(runs, f"p2d_{tg}_smirror.qpy"), "rb"))[0]
        if int(c.count_ops().get("cz", 0)) != 2 * cz[tg]:
            errs.append(f"{tg} string mirror: CZ {c.count_ops().get('cz', 0)}, intended {2 * cz[tg]}")
    if errs:
        raise SystemExit("REFUSED: " + "; ".join(errs[:6]))
    answers = {tg: {str(lb): v for lb, v in zip(w["given_labels"], A["z"][tg])} for tg, w in want.items()}
    with open(a.ans_out, "w") as f:
        json.dump(dict(meta=meta, z=answers, rulers=A["rulers"]), f, indent=1, sort_keys=True)
    sec = ORN.charge(n_c, a.shots)
    b = dict(device=dev.name, chain=dict(labels=chain, **how), copy_of_F=dict(drow=dr, dcol=dc, passed_over=reasons),
             items=want, cz=cz, cz_depth=depth, mirrors=sorted(mirrors), floors=[], smirrors=sorted(smirrors),
             smirror_strings=smir, pairs_by_t={str(t): k for t, k in kt.items()},
             parking=dict(delays=0, note="no mid-circuit measurement and no delay: nothing to park"),
             shots=a.shots, strings=meta["strings"], pairs=meta["pairs"], cycles=list(ts), forms=["L"],
             circuits=n_c, charge_seconds=round(sec, 1), qpu_seconds_model_psf_os=man["qpu_seconds_model"],
             circuits_sha256=man.get("circuits_sha256"))
    json.dump(b, open(os.path.join(a.out, "build.json"), "w"), indent=1)
    print(f"device {dev.name}; pairs by t {kt}; |0> mirrors {len(mirrors)}; string mirrors {len(smirrors)} "
          f"({'+'.join(smir) or 'none'}); circuits {n_c}; {a.shots} shots; charge {sec:.1f} s "
          f"(2.6 + 0.000269 x circuits x shots); psf-os model {man['qpu_seconds_model']} s")
    print("answers by label sha256", hashlib.sha256(open(a.ans_out, "rb").read()).hexdigest())


# --------------------------------------------------------------------------------------------------------- check3

def cmd_check3(a):
    sys.path.insert(0, HERE)
    import hub_check as HK
    ORN.cmd_check(a)                                   # the declared check (items, |0> mirrors, totals, rulers)
    b = json.load(open(os.path.join(a.out, "build.json")))
    base = json.load(open(os.path.join(a.out, "check.json")))
    runs = os.path.join(a.out, "runs")
    res, ok = {}, base["ALL"] == "PASS"
    for tg in b.get("smirrors", []):
        w = b["items"][tg]
        rec = json.load(open(os.path.join(runs, f"p2d_{tg}_smirror.json")))
        phys = [int(rec["mapping"][str(lb)]) for lb in w["given_labels"]]
        z, method = HK.z_of(HK.reduced(HK.load(os.path.join(runs, f"p2d_{tg}_smirror.qpy")), phys))
        nm = tg.split("_")[-1]
        ideal = np.array([1 - 2 * int(b["strings"][nm][p]) for p in w["positions"]], dtype=float)
        worst = float(np.abs(z - ideal).max())
        res[tg] = dict(method=method, worst=worst, ok=worst < 1e-6)
        ok &= worst < 1e-6
        print(f"{tg} string mirror: {method}: worst {worst:.1e} {'PASS' if worst < 1e-6 else 'FAIL'}", flush=True)
    res["ALL"] = "PASS" if ok else "FAIL"
    json.dump(dict(declared=base["ALL"], smirrors=res), open(os.path.join(a.out, "check3.json"), "w"), indent=1)
    print("ALL (declared check and string mirrors)", res["ALL"])


# --------------------------------------------------------------------------------------------------------- score3

def counts_mean_se(counts, rec_labels, labels, weights, idx):
    """Per-label <Z>, and the shot-noise SE of the per-shot mean of weights[q] Z_q over labels[idx]."""
    k_of = {lb: k for k, lb in enumerate(rec_labels)}
    tot = sum(counts.values())
    z = np.zeros(len(labels))
    per = []
    w = np.asarray(weights, dtype=float)
    for key, c in counts.items():
        s = key.replace(" ", "")
        v = np.array([1 - 2 * int(s[-1 - k_of[lb]]) for lb in labels], dtype=float)
        z += c * v
        per.append((float((w[idx] * v[idx]).mean()) if len(idx) else 0.0, c))
    z /= tot
    mu = sum(m * c for m, c in per) / tot
    var = sum(c * (m - mu) ** 2 for m, c in per) / (tot - 1)
    return z, math.sqrt(var / tot)


def mirror_ruler(Od_w, const, w_ex, m, m_se, K):
    """W through rho = sqrt(m), d against the exact W, its SE (pairs' scatter and the mirror's shot noise)."""
    if not (m > 0):
        return dict(rho=None, d=None, se=None, words=word(float("nan"), 0.0, K), note="mirror mean not positive")
    rho = math.sqrt(m)
    d = (-(Od_w / rho) / 2 + const) - w_ex
    se_pairs = float(np.std(d, ddof=1) / np.sqrt(K))
    dwdm = float(np.mean(Od_w) / (4 * m ** 1.5))
    se = math.sqrt(se_pairs ** 2 + (dwdm * m_se) ** 2)
    return dict(rho=rho, mean=m, d=float(d.mean()), se=se, t_se=ORN2.t975(K - 1) * se, words=word(float(d.mean()), se, K))


def cmd_score3(a):
    from psf_os import job as J
    from psf_os import sentinel
    from psf_os import user2d as U
    b = json.load(open(os.path.join(a.out, "build.json")))
    ans = json.load(open(a.answers))["z"]
    runs, jobd = os.path.join(a.out, "runs"), os.path.join(a.out, "job")
    zz, mrec = {}, {}
    for name, (rec, cc) in J.read(jobd, runs).items():
        kind = rec.get("psfos_job", {}).get("kind")
        if kind not in ("user2d", "user2d_mirror", "user2d_smirror"):
            continue
        tg = U._tag_of(name, rec)
        labels = b["items"][tg]["given_labels"]
        counts = cc[(rec["points"][0]["input"], "z")]
        if kind == "user2d":
            zz[tg], _ = counts_mean_se(counts, rec["labels"], labels, np.ones(len(labels)), [])
        else:
            mrec[(tg, kind)] = (counts, rec["labels"], labels)
    strs = b["strings"]
    shots = b["shots"]
    tau = a.tau
    res = dict(device=b["device"], tau=tau, keep_fraction=KEEP_FRACTION, cells={}, uniform={}, direction={}, beside={})
    for arm in ORN.ARMS:
        for t in b["cycles"]:
            s00 = ORN.tag(arm, t, "L", "s00")
            pos = b["items"][s00]["positions"]
            win = ORN.window(t)
            wi = [i for i, p in enumerate(pos) if p in win]
            ks = sorted(n[1:] for n in strs if n.startswith("s") and ORN.tag(arm, t, "L", n) in b["items"])
            K = len(ks)
            zex = lambda tg: np.array([ans[tg][str(lb)] for lb in b["items"][tg]["given_labels"]])
            Od = np.array([(zz[ORN.tag(arm, t, "L", "s" + k)] - zz[ORN.tag(arm, t, "L", "c" + k)]) / 2 for k in ks])
            Oe = np.array([(zex(ORN.tag(arm, t, "L", "s" + k)) - zex(ORN.tag(arm, t, "L", "c" + k))) / 2 for k in ks])
            T0 = np.array([sum(1 - 2 * int(strs["s" + k][p]) for p in pos) for k in ks], dtype=float)
            const = np.array([-(sum(int(strs["s" + k][p]) for p in win) - sum(int(strs["c" + k][p]) for p in win)) / 2
                              for k in ks])
            w_ex = -Oe[:, wi].sum(axis=1) / 2 + const
            Od_w = Od[:, wi].sum(axis=1)
            w_raw = -Od_w / 2 + const
            d_raw = w_raw - w_ex
            # raw M and W as 11-23 / 11-24
            m_dev, m_ex = [], []
            for k in ks:
                for nm in ("s" + k, "c" + k):
                    tg = ORN.tag(arm, t, "L", nm)
                    m0 = sum(int(strs[nm][p]) for p in win)
                    m_dev.append(float(((1 - zz[tg][wi]) / 2).sum() - m0))
                    m_ex.append(float(((1 - zex(tg)[wi]) / 2).sum() - m0))
            m_dev, m_ex = np.array(m_dev), np.array(m_ex)
            rM = float(np.mean((m_dev - m_ex) ** 2) / np.mean(m_ex ** 2)) if np.any(m_ex) else float("nan")
            rW = float(np.mean(d_raw ** 2) / np.mean(w_ex ** 2)) if np.any(w_ex) else float("nan")
            se_raw = float(np.std(d_raw, ddof=1) / np.sqrt(K))
            cell = dict(K=K, t975=ORN2.t975(K - 1), M_ratio=rM, M="READS" if rM <= 0.5 else "DOES NOT READ",
                        W_ratio=rW, W="READS" if rW <= 0.5 else "DOES NOT READ", W_device=float(w_raw.mean()),
                        W_exact=float(w_ex.mean()), W_excess=float(d_raw.mean()), W_excess_se=se_raw, rulers={})
            R = cell["rulers"]
            # (a) the circuit's total (t >= 3)
            rho_a = None
            if ORN.ruler_a_read(t, "L"):
                rho_a = Od.sum(axis=1) / T0
                d_a = (-(Od_w / rho_a) / 2 + const) - w_ex
                se_a = float(np.std(d_a, ddof=1) / np.sqrt(K))
                R["a"] = dict(d=float(d_a.mean()), se=se_a, t_se=ORN2.t975(K - 1) * se_a,
                              words=word(float(d_a.mean()), se_a, K), rho_mean=float(rho_a.mean()))
            # the mirrors: per-qubit values and the averaging sets
            sets = {}
            if (s00, "user2d_mirror") in mrec:
                cnt, rl, lb = mrec[(s00, "user2d_mirror")]
                zm, _ = counts_mean_se(cnt, rl, lb, np.ones(len(lb)), [])
                sets["b"] = (zm, list(range(len(pos))), ("plain", cnt, rl, lb))
                sets["c"] = (zm, wi, ("plain", cnt, rl, lb))
            sig = np.array([1 - 2 * int(strs["s00"][p]) for p in pos], dtype=float)
            if (s00, "user2d_smirror") in mrec:
                cs, rls, lbs = mrec[(s00, "user2d_smirror")]
                zs, _ = counts_mean_se(cs, rls, lbs, sig, [])
                sets["d1"] = (zs * sig, wi, ("s", cs, rls, lbs))
                c00 = ORN.tag(arm, t, "L", "c00")
                if (c00, "user2d_smirror") in mrec:
                    cc_, rlc, lbc = mrec[(c00, "user2d_smirror")]
                    zc, _ = counts_mean_se(cc_, rlc, lbc, sig, [])
                    sets["d"] = ((zs - zc) / 2 * sig, wi, ("sc", (cs, rls, lbs), (cc_, rlc, lbc)))
            for r, (val, idx, src) in sets.items():
                for variant, use in (("", list(idx)), ("_tau", [i for i in idx if val[i] >= tau])):
                    key = r + variant
                    if variant and len(use) < KEEP_FRACTION * len(idx):
                        R[key] = dict(words=dict(t="NOT READ", **{"2se": "NOT READ"}), kept=len(use), of=len(idx),
                                      left_out=[pos[i] for i in idx if i not in use], note="too few qubits left")
                        continue
                    m = float(np.mean(val[use]))
                    if src[0] == "plain":
                        _, se = counts_mean_se(src[1], src[2], src[3], np.ones(len(pos)), use)
                    elif src[0] == "s":
                        _, se = counts_mean_se(src[1], src[2], src[3], sig, use)
                    else:
                        _, se_s = counts_mean_se(*src[1], sig, use)
                        _, se_c = counts_mean_se(*src[2], sig, use)
                        se = math.sqrt(se_s ** 2 + se_c ** 2) / 2
                    R[key] = mirror_ruler(Od_w, const, w_ex, m, se, K)
                    if variant:
                        R[key].update(kept=len(use), of=len(idx), left_out=[pos[i] for i in idx if i not in use])
            res["cells"][f"{arm}_t{t}_L"] = cell
            if t >= 3:
                # the one-factor test (as 11-24; shot-noise SEs) and the direction (candidate 3)
                use = [i for i in wi if np.sum(Oe[:, i] ** 2) >= ORN.UNIFORM_FLOOR * K]
                VarZ = np.array([[(1 - zz[ORN.tag(arm, t, "L", p + k)] ** 2) / shots for p in "sc"] for k in ks])
                r_pos, se_pos = [], []
                for i in use:
                    den = float(np.sum(Oe[:, i] ** 2))
                    r_pos.append(float(np.sum(Od[:, i] * Oe[:, i]) / den))
                    var_o = (VarZ[:, 0, i] + VarZ[:, 1, i]) / 4
                    se_pos.append(math.sqrt(float(np.sum(Oe[:, i] ** 2 * var_o))) / den)
                r_pos, se_pos = np.array(r_pos), np.array(se_pos)
                if len(use) < 2 or np.any(se_pos <= 0):
                    u = dict(word="NOT READ", positions=[pos[i] for i in use], r=r_pos.tolist(), se=se_pos.tolist())
                else:
                    wts = 1 / se_pos ** 2
                    pool = float(np.sum(wts * r_pos) / np.sum(wts))
                    chi2 = float(np.sum(((r_pos - pool) / se_pos) ** 2))
                    p = ORN.chi2_sf(chi2, len(use) - 1)
                    u = dict(word="UNIFORM" if p >= ORN.LEVEL else "NOT UNIFORM", positions=[pos[i] for i in use],
                             r=r_pos.tolist(), se=se_pos.tolist(), r_pool=pool, chi2=chi2, dof=len(use) - 1, p=p)
                res["uniform"][f"{arm}_t{t}_L"] = u
                if rho_a is not None and use:
                    r_k = np.sum(Od[:, use] * Oe[:, use], axis=1) / np.sum(Oe[:, use] ** 2, axis=1)
                    dl = r_k - rho_a
                    se_dl = float(np.std(dl, ddof=1) / np.sqrt(K))
                    tq = ORN2.t975(K - 1)
                    if not (se_dl > 0):
                        wd = "NOT READ"
                    elif dl.mean() > tq * se_dl:
                        wd = "WINDOW SHRINKS LESS"
                    elif dl.mean() < -tq * se_dl:
                        wd = "WINDOW SHRINKS MORE"
                    else:
                        wd = "NOT SEEN"
                    res["direction"][f"{arm}_t{t}_L"] = dict(r_minus_rho_a=float(dl.mean()), se=se_dl, t_se=tq * se_dl,
                                                             word=wd, ruler_a=R["a"]["words"]["t"])
    try:
        res["beside"]["sentinel"] = sentinel.verdict(jobd, runs)["status"]
    except Exception as e:                                # beside only: never stops the scores
        res["beside"]["sentinel"] = f"not read ({type(e).__name__})"
    json.dump(res, open(os.path.join(a.out, "scores3.json"), "w"), indent=1)
    for k, c in res["cells"].items():
        line = (f"{k}: K {c['K']}; raw W {c['W']} ({c['W_ratio']:.3f}), excess {c['W_excess']:+.3f}; " + "; ".join(
            f"({r}) " + (f"d {v['d']:+.3f} tSE {v['t_se']:.3f} " if v.get("d") is not None else "")
            + f"{v['words']['t']}" + (f" [left out {v['left_out']}]" if v.get("left_out") else "")
            for r, v in c["rulers"].items()))
        print(line)
    for k, v in res["direction"].items():
        print(f"direction {k}: r - rho_a {v['r_minus_rho_a']:+.3f} (t SE {v['t_se']:.3f}) {v['word']}; ruler (a) "
              f"{v['ruler_a']}")
    for k, u in res["uniform"].items():
        print(f"uniform {k}: {u['word']}" + (f" (p {u['p']:.3f})" if "p" in u else ""))


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("build3")
    for x in ("dev", "out", "ans_in", "ans_out"):
        p.add_argument(x)
    p.add_argument("--shots", type=int, default=1000)
    p.add_argument("--smirrors", choices=("none", "s", "sc"), default="none")
    p.add_argument("--pairs-t", nargs="*", default=None, help="pairs per t, e.g. 4:9")
    p.add_argument("--max-seconds", type=float, default=60.0)
    p = sp.add_parser("check3")
    p.add_argument("out")
    p.add_argument("answers")
    p = sp.add_parser("score3")
    p.add_argument("out")
    p.add_argument("answers")
    p.add_argument("--tau", type=float, default=TAU)
    a = ap.parse_args()
    dict(build3=cmd_build3, check3=cmd_check3, score3=cmd_score3)[a.cmd](a)


if __name__ == "__main__":
    main()
