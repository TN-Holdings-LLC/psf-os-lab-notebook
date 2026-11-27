"""Ohm with rulers inside the circuit, the fifth night's candidates (workplace Claude, 2026-11-27; not declared).

The declared tools gpu/ohm_ruler_night.py (11-24), ohm_ruler_night3.py (11-25) and ohm_ruler_night4.py (11-26) are
imported read only and not changed. This file is ohm_ruler_night4.py with, on the owner's decisions of 2026-11-26:

  build5  build3's job (string mirrors s00 and c00, pairs per t), then 6 readout circuits on the t = 4 light cone's
          physical qubits (22), X alone then measured (no other gate): s00 and c00 at the head of the job and again at
          its tail, s01 and c01 at its tail only. psf-os 0.3.3 orders a job's pubs by its records' file names
          (job.assemble: sorted names), so the head pair is named a_readout_<s>_head (before ksent_ and p2d_) and the
          tail ones z_readout_<s>_tail (after every p2d_). build5 checks the assembled order and stops otherwise.
  check5  check3, then every readout circuit noise-free equal to its string.
  score5  score3 (its scores3.json, unchanged), then scores5.json and qubits.csv:
            e_q  = the mean of the head and tail pairs' odd parts (Z_s00 - Z_c00) / 2 x (1 - 2 b_s00,q); its shot
                   variance (var_head + var_tail) / 4 per qubit, the qubits taken as independent
            (e)   beside: rho_e = mean of e_q over the window (no square root)
            (de)  judged: per window qubit rho_q = sqrt(m_q e_q)
            (a')  judged: the circuit's total over the qubits (b') keeps, over the exact total on the same qubits
            direction with rho_a' (judged) and with rho_a (beside)
            beside: tau 0.2 / 0.3 / 0.4; the tail minus head e_q per qubit with its SE (a change during the job, on
                  the user's qubits); the tail's s01/c01 minus s00/c00 e_q (the neighbours' states); OR5-2
          Words: t quantile with K - 1 dof (rule 4), NOT READ on SE 0 (rule 5), 2 SE beside.
  qubits.csv (beside, never judged): night 4's columns (R_LOW and R_HIGH tested at t >= 3 only, where the window has
          a pooled r; at t = 1 they read False), plus e_head, e_tail and r_over_e (r_q / e_q where both are present
          and e_q > 0: a qubit's shrink on the test against its readout's), values to 3 decimals.

  PYTHONPATH=<psf-os 0.3.3>:<TOQB> python gpu/ohm_ruler_night5.py build5 DEV OUT ANS_IN ANS_OUT --pairs-t 1:7 3:7 4:9
  python gpu/ohm_ruler_night5.py check5 OUT ANS_BY_LABEL
  python gpu/ohm_ruler_night5.py score5 OUT ANS_BY_LABEL --tau 0.3
"""
import argparse
import csv
import json
import math
import os
import shutil
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ohm_ruler_night as ORN  # noqa: E402  (read only: declared 2026-11-24)
import ohm_ruler_night2 as ORN2  # noqa: E402  (read only: the t quantile table)
import ohm_ruler_night3 as ORN3  # noqa: E402  (read only: declared 2026-11-25)
import ohm_ruler_night4 as ORN4  # noqa: E402  (read only: declared 2026-11-26)

TAU = 0.3
TAUS_BESIDE = (0.2, 0.3, 0.4)
# (record name, string, place): the head pair sorts before every other record, the tail ones after every p2d_ record
READOUT = (("a_readout_s00_head", "s00", "head"), ("a_readout_c00_head", "c00", "head"),
           ("z_readout_c00_tail", "c00", "tail"), ("z_readout_c01_tail", "c01", "tail"),
           ("z_readout_s00_tail", "s00", "tail"), ("z_readout_s01_tail", "s01", "tail"))
OR52 = dict(device="ibm_fez", drow=4, physical=(101, 102, 103, 104), t=4)     # owner 2026-11-26

# [OWNER] reading table C (the readout rulers), word for word as the draft
READ_TABLE_C = {
    ("e", "AGREES"): "the readout's shrink on the window carries the window's shrink",
    ("e", "DIFFERS"): "the readout's shrink on the window does not carry the window's shrink",
    ("e", "NOT READ"): "no scatter (rule 5)",
    ("de", "AGREES"): "the string mirrors with the readout's half put back carry the window's shrink",
    ("de", "DIFFERS"): "the string mirrors with the readout's half put back do not carry the window's shrink",
    ("de", "NOT READ"): "no scatter (rule 5), or a mirror or readout value not positive",
    ("a_prime", "AGREES"): "the circuit's total over the kept qubits carries the window's shrink",
    ("a_prime", "DIFFERS"): "the circuit's total over the kept qubits does not carry the window's shrink",
    ("a_prime", "NOT READ"): "fewer than half of the circuit's qubits kept, or no scatter (rule 5)",
}
# the dry runs' expectation per (ruler, t), from notes/ohm_ruler5_2026-11-27/expect5.py (the fourth night's dry runs;
# tests/test_ohm_ruler_night5.py checks that this table equals that tool's output)
EXPECT = {("de", 1): "EXPECTED TO AGREE", ("de", 3): "EXPECTED TO AGREE", ("de", 4): "EXPECTED TO AGREE",
          ("a_prime", 3): "EXPECTED TO DIFFER", ("a_prime", 4): "MIXED",
          ("e", 1): "EXPECTED TO AGREE", ("e", 3): "EXPECTED TO DIFFER", ("e", 4): "EXPECTED TO DIFFER"}
# [OWNER] reading table D, the word against the dry runs' expectation, word for word as the draft
READ_EXPECTED = {
    ("EXPECTED TO AGREE", "AGREES"): "as the dry runs expect",
    ("EXPECTED TO AGREE", "DIFFERS"): "against the dry runs: the device holds a fault that none of the dry runs' illustrative noises holds",
    ("EXPECTED TO DIFFER", "AGREES"): "against the dry runs: the gates shrank the signal less than the dry runs' gate noise, or not at all",
    ("EXPECTED TO DIFFER", "DIFFERS"): "as the dry runs expect under gate noise or damping",
    ("MIXED", "AGREES"): "within what the dry runs allow",
    ("MIXED", "DIFFERS"): "within what the dry runs allow",
}
# beside, never judged: compared with (d), as the addendum asks (a reading row, not a prediction)
READ_DE_VS_D = {
    "SMALLER": "|d| of (de) below |d| of (d): the readout would explain part of (d)'s gap",
    "NOT SMALLER": "|d| of (de) not below |d| of (d): the readout does not explain (d)'s gap",
}


# ---------------------------------------------------------------------------------------------------------- build5

def cmd_build5(a):
    from psf_os import device as Dv
    from psf_os import job as J
    from psf_os import user2d as U
    a3 = argparse.Namespace(dev=a.dev, out=a.out, ans_in=a.ans_in, ans_out=a.ans_out, shots=a.shots, smirrors="sc",
                            pairs_t=a.pairs_t, max_seconds=1e9)
    ORN3.cmd_build3(a3)
    dev = Dv.Device.load(a.dev)
    b = json.load(open(os.path.join(a.out, "build.json")))
    t4 = max(b["cycles"])
    s00 = ORN.tag("A0", t4, "L", "s00")
    pos, phys = b["items"][s00]["positions"], b["items"][s00]["physical"]
    rec = json.load(open(os.path.join(a.out, "runs", f"p2d_{s00}.json")))
    labels = rec["labels"]
    mapping = {int(k): v for k, v in rec["mapping"].items()}
    runs = os.path.join(a.out, "runs")
    for name, nm, place in READOUT:
        bits = "".join(b["strings"][nm][p] for p in pos)
        qc = ORN4.readout_circuit(dev.num_qubits, phys, bits, [int(mapping[lb]) for lb in labels])
        U._record(dev, runs, name, "readout", "user2d_readout", [qc], [dict(input="r", setting="z")],
                  labels, mapping, dict(tag=name, string=nm, place=place, positions=pos, physical=phys, cz=0),
                  a.shots, True)
    shutil.move(os.path.join(a.out, "job"), os.path.join(a.out, "unsent_job_build3"))
    man = J.assemble(dev, runs, os.path.join(a.out, "job"), max_seconds=a.max_seconds)
    cell_name = {c["cell"]: c["name"] for c in man["cells"]}
    order = [cell_name[pb["cell"]] for pb in man["pubs"]]
    n_c = len(order)
    head = [i for i, o in enumerate(order) if "a_readout_" in o]
    tail = [i for i, o in enumerate(order) if "z_readout_" in o]
    if head != [0, 1] or tail != list(range(n_c - 4, n_c)):
        raise SystemExit(f"STOP: readout pubs not at the head and tail of the job (head {head}, tail {tail}, "
                         f"of {n_c})")
    b.update(circuits=n_c, charge_seconds=round(ORN.charge(n_c, a.shots), 1),
             qpu_seconds_model_psf_os=man["qpu_seconds_model"], circuits_sha256=man.get("circuits_sha256"),
             readout=dict(records=[list(r) for r in READOUT], positions=pos, physical=phys, t=t4,
                          pub_index={order[i]: i for i in head + tail}))
    json.dump(b, open(os.path.join(a.out, "build.json"), "w"), indent=1)
    print(f"build5: + {len(READOUT)} readout circuits on the t = {t4} cone ({len(phys)} qubits): pubs {head} at the "
          f"head, {tail} at the tail; circuits {n_c}; charge {b['charge_seconds']} s (2.6 + 0.000269 x circuits x "
          f"shots); psf-os model {man['qpu_seconds_model']} s")


# ---------------------------------------------------------------------------------------------------------- check5

def cmd_check5(a):
    sys.path.insert(0, HERE)
    import hub_check as HK
    ORN3.cmd_check3(a)
    b = json.load(open(os.path.join(a.out, "build.json")))
    base = json.load(open(os.path.join(a.out, "check3.json")))
    ok = base["smirrors"]["ALL"] == "PASS"
    res = {}
    for name, nm, _place in b["readout"]["records"]:
        z, method = HK.z_of(HK.reduced(HK.load(os.path.join(a.out, "runs", f"{name}.qpy")),
                                       b["readout"]["physical"]))
        ideal = np.array([1 - 2 * int(b["strings"][nm][p]) for p in b["readout"]["positions"]], dtype=float)
        worst = float(np.abs(z - ideal).max())
        res[name] = dict(method=method, worst=worst, ok=worst < 1e-9)
        ok &= worst < 1e-9
        print(f"readout {name}: {method}: worst {worst:.1e} {'PASS' if worst < 1e-9 else 'FAIL'}")
    res["ALL"] = "PASS" if ok else "FAIL"
    json.dump(dict(check3=base["smirrors"]["ALL"], readout=res), open(os.path.join(a.out, "check5.json"), "w"),
              indent=1)
    print("ALL (declared check, string mirrors, readout)", res["ALL"])


# ---------------------------------------------------------------------------------------------------------- score5

def _z(counts, rec_labels, labels, weights, idx):
    return ORN3.counts_mean_se(counts, rec_labels, labels, weights, idx)


def _ruler(w_k, w_ex, K, extra_var=0.0):
    d = w_k - w_ex
    se = math.sqrt(float(np.std(d, ddof=1) / np.sqrt(K)) ** 2 + extra_var)
    return dict(d=float(d.mean()), se=se, t_se=ORN2.t975(K - 1) * se, words=ORN3.word(float(d.mean()), se, K))


def cmd_score5(a):
    from psf_os import job as J
    from psf_os import user2d as U
    import io
    import contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        ORN3.cmd_score3(argparse.Namespace(out=a.out, answers=a.answers, tau=a.tau))
    s3 = json.load(open(os.path.join(a.out, "scores3.json")))
    b = json.load(open(os.path.join(a.out, "build.json")))
    ans = json.load(open(a.answers))["z"]
    strs, shots = b["strings"], b["shots"]
    runs, jobd = os.path.join(a.out, "runs"), os.path.join(a.out, "job")
    man = json.load(open(os.path.join(jobd, "manifest.json")))
    zz, mrec, rrec = {}, {}, {}
    for name, (rec, cc) in J.read(jobd, runs).items():
        kind = rec.get("psfos_job", {}).get("kind")
        if kind not in ("user2d", "user2d_mirror", "user2d_smirror", "user2d_readout"):
            continue
        counts = cc[(rec["points"][0]["input"], "z")]
        if kind == "user2d_readout":
            rrec[(rec["string"], rec["place"])] = (counts, rec["labels"])
            continue
        if kind not in ("user2d", "user2d_mirror", "user2d_smirror"):
            continue
        tg = U._tag_of(name, rec)
        labels = b["items"][tg]["given_labels"]
        if kind == "user2d":
            zz[tg], _ = _z(counts, rec["labels"], labels, np.ones(len(labels)), [])
        else:
            mrec[(tg, kind)] = (counts, rec["labels"], labels)
    # the readout: e_q per chain position of the t = 4 cone (labels are the physical qubits, in position order)
    rpos = b["readout"]["positions"]
    ro_labels = b["readout"]["physical"]

    def odd(sn, cn, place):
        sig = np.array([1 - 2 * int(strs[sn][p]) for p in rpos], dtype=float)
        zs, _ = _z(rrec[(sn, place)][0], rrec[(sn, place)][1], ro_labels, sig, [])
        zc, _ = _z(rrec[(cn, place)][0], rrec[(cn, place)][1], ro_labels, sig, [])
        return (zs - zc) / 2 * sig, ((1 - zs ** 2) + (1 - zc ** 2)) / shots / 4
    e_h, v_h = odd("s00", "c00", "head")
    e_t, v_t = odd("s00", "c00", "tail")
    e_n, _ = odd("s01", "c01", "tail")
    e_of = {p: float((e_h[i] + e_t[i]) / 2) for i, p in enumerate(rpos)}
    var_e = {p: float((v_h[i] + v_t[i]) / 4) for i, p in enumerate(rpos)}
    eh_of = {p: float(e_h[i]) for i, p in enumerate(rpos)}
    et_of = {p: float(e_t[i]) for i, p in enumerate(rpos)}
    dev_rec = man.get("device", {})
    calib = (dev_rec.get("source") or {}).get("calibration_time", "") if isinstance(dev_rec.get("source"), dict) else ""
    drow = b["copy_of_F"]["drow"]
    res = dict(device=b["device"], calibration_time=calib, copy_drow=drow, tau=a.tau, cells={}, direction={},
               tau_beside={}, readout_beside={}, tables={}, or5_2=None)
    rows = []
    mirror_by = {}
    for arm in ORN.ARMS:
        for t in b["cycles"]:
            key = f"{arm}_t{t}_L"
            s00 = ORN.tag(arm, t, "L", "s00")
            pos = b["items"][s00]["positions"]
            phys = b["items"][s00]["physical"]
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
            cell = dict(K=K)
            # the |0> mirror per qubit, the string mirrors' m_q per qubit
            cnt, rl, lb = mrec[(s00, "user2d_mirror")]
            zm, _ = _z(cnt, rl, lb, np.ones(len(lb)), [])
            mirror_by[key] = dict(zip(phys, zm.tolist()))
            sig = np.array([1 - 2 * int(strs["s00"][p]) for p in pos], dtype=float)
            cs, rls, lbs = mrec[(s00, "user2d_smirror")]
            cc_, rlc, lbc = mrec[(ORN.tag(arm, t, "L", "c00"), "user2d_smirror")]
            zsm, _ = _z(cs, rls, lbs, sig, [])
            zcm, _ = _z(cc_, rlc, lbc, sig, [])
            m = (zsm - zcm) / 2 * sig
            var_m = ((1 - zsm ** 2) + (1 - zcm ** 2)) / shots / 4
            e = np.array([e_of.get(p, float("nan")) for p in pos])
            ve = np.array([var_e.get(p, float("nan")) for p in pos])
            # (e): the readout on the window, once (no square root)
            ew = float(np.mean(e[wi]))
            if ew > 0:
                w_e = -(Od_w / ew) / 2 + const
                dwde = float(np.mean(Od_w) / (2 * ew ** 2))
                cell["e"] = dict(rho=ew, **_ruler(w_e, w_ex, K, (dwde ** 2) * float(np.sum(ve[wi])) / len(wi) ** 2))
            else:
                cell["e"] = dict(words=ORN3.word(float("nan"), 0.0, K), note="readout mean not positive")
            # (de): per window qubit sqrt(m_q e_q)
            me = m[wi] * e[wi]
            if np.all(me > 0):
                rq = np.sqrt(me)
                w_de = -(Od[:, wi] / rq).sum(axis=1) / 2 + const
                O_mean = Od[:, wi].mean(axis=0)
                gm = O_mean * e[wi] / (4 * rq ** 3)
                ge = O_mean * m[wi] / (4 * rq ** 3)
                xv = float(np.sum(gm ** 2 * var_m[wi]) + np.sum(ge ** 2 * ve[wi]))
                cell["de"] = dict(rho_q=rq.tolist(), **_ruler(w_de, w_ex, K, xv))
            else:
                cell["de"] = dict(words=ORN3.word(float("nan"), 0.0, K), note="m_q e_q not positive on the window")
            # (a') at each tau (0.3 judged, the others beside), with its direction
            if ORN.ruler_a_read(t, "L"):
                rho_a = Od.sum(axis=1) / T0
                use = [i for i in wi if np.sum(Oe[:, i] ** 2) >= ORN.UNIFORM_FLOOR * K]
                r_k = np.sum(Od[:, use] * Oe[:, use], axis=1) / np.sum(Oe[:, use] ** 2, axis=1)
                for tau in sorted(set(TAUS_BESIDE) | {a.tau}):
                    keep = [i for i in range(len(pos)) if i in wi or zm[i] >= tau]
                    out = dict(kept=len(keep), of=len(pos), left_out=[pos[i] for i in range(len(pos)) if i not in keep])
                    if len(keep) < ORN3.KEEP_FRACTION * len(pos) or np.any(Oe[:, keep].sum(axis=1) == 0):
                        out.update(words=dict(t="NOT READ", **{"2se": "NOT READ"}))
                    else:
                        rho_ap = Od[:, keep].sum(axis=1) / Oe[:, keep].sum(axis=1)
                        out.update(rho_mean=float(rho_ap.mean()), **_ruler(-(Od_w / rho_ap) / 2 + const, w_ex, K))
                        dl = r_k - rho_ap
                        out["direction"] = _direction(dl, K)
                    # (b') at this tau, from the |0> mirror over the kept qubits
                    mb = float(np.mean(zm[keep]))
                    _, se_b = _z(cnt, rl, lb, np.ones(len(lb)), keep)
                    out["b_prime"] = ORN3.mirror_ruler(Od_w, const, w_ex, mb, se_b, K) if mb > 0 else None
                    if tau == a.tau:
                        cell["a_prime"] = {k: v for k, v in out.items() if k != "b_prime"}
                        res["direction"][key] = dict(judged_a_prime=out.get("direction"),
                                                     beside_a=_direction(r_k - rho_a, K))
                    res["tau_beside"].setdefault(key, {})[str(tau)] = dict(
                        a_prime=out.get("words"), b_prime=(out["b_prime"] or {}).get("words"),
                        left_out=out["left_out"])
            # (de) against (d): beside reading row
            d3 = s3["cells"][key]["rulers"].get("d", {})
            if cell["de"].get("d") is not None and d3.get("d") is not None:
                cell["de_vs_d"] = "SMALLER" if abs(cell["de"]["d"]) < abs(d3["d"]) else "NOT SMALLER"
            # r per position (outside the window too) for qubits.csv
            uni = s3["uniform"].get(key, {})
            pool = uni.get("r_pool")
            VarZ = np.array([[(1 - zz[ORN.tag(arm, t, "L", pp + k)] ** 2) / shots for pp in "sc"] for k in ks])
            for i, p in enumerate(pos):
                den = float(np.sum(Oe[:, i] ** 2))
                rq_, se_ = (float("nan"), float("nan"))
                if den >= ORN.UNIFORM_FLOOR * K:
                    rq_ = float(np.sum(Od[:, i] * Oe[:, i]) / den)
                    se_ = math.sqrt(float(np.sum(Oe[:, i] ** 2 * (VarZ[:, 0, i] + VarZ[:, 1, i]) / 4))) / den
                # R LOW: r_q below the window's pooled r by more than 2 shot-noise SE (the lower side only; score3's
                # outlying positions, two-sided, stay in scores3.json)
                r_low = (pool is not None and math.isfinite(rq_) and se_ > 0 and rq_ - pool < -2 * se_)
                # R HIGH: the upper side, the same test (owner, 2026-11-26)
                r_high = (pool is not None and math.isfinite(rq_) and se_ > 0 and rq_ - pool > 2 * se_)
                rows.append(dict(device=b["device"], calibration_time=calib, copy_drow=drow, arm=arm, t=t,
                                 position=p, physical=phys[i], in_window=p in win, mirror_z=round(float(zm[i]), 3),
                                 m_q=round(float(m[i]), 3), r_q="" if not math.isfinite(rq_) else round(rq_, 3),
                                 e_q="" if p not in e_of else round(e_of[p], 3),
                                 e_head="" if p not in eh_of else round(eh_of[p], 3),
                                 e_tail="" if p not in et_of else round(et_of[p], 3),
                                 r_over_e=("" if not (math.isfinite(rq_) and p in e_of and e_of[p] > 0)
                                           else round(rq_ / e_of[p], 3)),
                                 left_out_at_tau=(p not in win and zm[i] < a.tau),
                                 MIRROR_LOW=bool(zm[i] < a.tau), R_LOW=bool(r_low), R_HIGH=bool(r_high)))
            res["cells"][key] = cell
            for r in ("e", "de", "a_prime"):
                w = cell.get(r, {}).get("words", {}).get("t")
                if (r, t) in EXPECT and w in ("AGREES", "DIFFERS"):
                    cell[r]["expected"] = EXPECT[(r, t)]
                    cell[r]["against_expectation"] = READ_EXPECTED[(EXPECT[(r, t)], w)]
            if t >= 3:
                res["tables"][key] = {r: READ_TABLE_C[(r, cell[r]["words"]["t"])] for r in ("e", "de", "a_prime")
                                      if r in cell}
    res["readout_beside"] = {str(p): dict(e_head=float(e_h[i]), e_tail=float(e_t[i]),
                                          tail_minus_head=float(e_t[i] - e_h[i]),
                                          tail_minus_head_se=float(math.sqrt(v_h[i] + v_t[i])),
                                          e_s01c01_tail=float(e_n[i]), s01_minus_s00_tail=float(e_n[i] - e_t[i]))
                             for i, p in enumerate(rpos)}
    res["or5_2"] = or5_2(b, mirror_by)
    json.dump(res, open(os.path.join(a.out, "scores5.json"), "w"), indent=1)
    with open(os.path.join(a.out, "qubits.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for k, c in res["cells"].items():
        print(f"{k}: K {c['K']}; " + "; ".join(
            f"({r}) " + (f"d {c[r]['d']:+.3f} tSE {c[r]['t_se']:.3f} " if c[r].get("d") is not None else "")
            + c[r]["words"]["t"] for r in ("e", "de", "a_prime") if r in c)
            + (f"; (de) against (d): {c['de_vs_d']}" if "de_vs_d" in c else ""))
    for k, v in res["direction"].items():
        print(f"direction {k}: with rho_a' {(v['judged_a_prime'] or {}).get('word')}; with rho_a (beside) "
              f"{v['beside_a']['word']}")
    print(f"OR5-2: {res['or5_2']['word']}")


def _direction(dl, K):
    se = float(np.std(dl, ddof=1) / np.sqrt(K))
    tq = ORN2.t975(K - 1)
    mu = float(dl.mean())
    word = ("NOT READ" if not se > 0 else "WINDOW SHRINKS LESS" if mu > tq * se else
            "WINDOW SHRINKS MORE" if mu < -tq * se else "NOT SEEN")
    return dict(r_minus_rho=mu, se=se, t_se=tq * se, word=word)


def or5_2(b, mirror_by):
    """OR5-2 (the owner's decision of 2026-11-26): on ibm_fez at copy drow 4, physical 101, 102, 103 and 104 sit below
    tau 0.3 on the t = 4 |0> mirror in all three arms. Another device or copy, or a qubit not on the t = 4 cone:
    NOT READ."""
    if b["device"] != OR52["device"] or b["copy_of_F"]["drow"] != OR52["drow"] or OR52["t"] not in b["cycles"]:
        return dict(word="NOT READ", why="another device or copy")
    vals = {}
    for arm in ORN.ARMS:
        mz = mirror_by[f"{arm}_t{OR52['t']}_L"]
        if any(q not in mz for q in OR52["physical"]):
            return dict(word="NOT READ", why="a qubit not on the t = 4 cone")
        vals[arm] = {str(q): mz[q] for q in OR52["physical"]}
    held = all(v < TAU for a_ in vals.values() for v in a_.values())
    return dict(word="HELD" if held else "NOT HELD", mirror_z=vals)


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("build5")
    for x in ("dev", "out", "ans_in", "ans_out"):
        p.add_argument(x)
    p.add_argument("--shots", type=int, default=1000)
    p.add_argument("--pairs-t", nargs="*", default=None)
    p.add_argument("--max-seconds", type=float, default=60.0)
    for nm in ("check5", "score5"):
        p = sp.add_parser(nm)
        p.add_argument("out")
        p.add_argument("answers")
        if nm == "score5":
            p.add_argument("--tau", type=float, default=TAU)
    a = ap.parse_args()
    dict(build5=cmd_build5, check5=cmd_check5, score5=cmd_score5)[a.cmd](a)


if __name__ == "__main__":
    main()
