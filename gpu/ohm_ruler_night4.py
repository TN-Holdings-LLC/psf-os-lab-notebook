"""Ohm with rulers inside the circuit, the fourth night's candidates (workplace Claude, 2026-11-26; not declared).

The declared tools gpu/ohm_ruler_night.py (11-24) and gpu/ohm_ruler_night3.py (11-25) are imported read only and not
changed. This file adds, on the owner's decisions of 2026-11-25 and home's addendum (home VS's proposals):

  build4  build3's job (string mirrors s00 and c00, pairs per t), then 4 readout circuits on the t = 4 light cone's
          physical qubits (22): the strings s00, c00, s01, c01 prepared with X alone and measured at once (no other
          gate); records p2d_readout_<s> (kind user2d_readout). The job is assembled again with them.
  check4  check3, then every readout circuit noise-free equal to its string.
  score4  score3 (its scores3.json, unchanged), then scores4.json and qubits.csv:
            (e)   the readout ruler: per qubit e_q = (Z_s00 - Z_c00) / 2 x (1 - 2 b_s00,q) on the readout circuits
                  (ideal 1; the odd part keeps only the shrink 1 - p01 - p10); rho_e = mean of e_q over the window
            (de)  per window qubit rho_q = sqrt(m_q e_q), m_q the string mirrors' odd part: the mirror carries the
                  gates twice and the readout once (m = g^2 e) and the test g e, so sqrt(m e) = g e
            (a')  the circuit's total over the qubits (b') keeps (window qubits always; outside qubits whose |0> mirror
                  <Z> >= tau) over the exact total on the same qubits (the sealed answers), per pair; NOT READ when
                  fewer than half of the circuit's qubits are kept
            direction with rho_a' (judged) and with rho_a (beside)
            beside: (a') and (b') at tau 0.2, 0.3, 0.4 with the qubits left out; the second readout pair's e_q
                  (s01 / c01) and its difference from the first; OR4-2
          Words: t quantile with K - 1 dof (rule 4), NOT READ on SE 0 (rule 5), 2 SE beside.
  qubits.csv (beside, never judged): one row per (arm, t, chain position) with the device, its calibration time
          (the device record's time only), the copy, the physical qubit, the |0> mirror's <Z>, m_q, r_q (outside the
          window too), e_q, left out at tau, MIRROR LOW (|0> mirror below tau) and R LOW (r_q beyond 2 shot-noise SE
          of the window's pooled r) as two separate columns.

  PYTHONPATH=<psf-os 0.3.3>:<TOQB> python gpu/ohm_ruler_night4.py build4 DEV OUT ANS_IN ANS_OUT --pairs-t 1:7 3:7 4:9
  python gpu/ohm_ruler_night4.py check4 OUT ANS_BY_LABEL
  python gpu/ohm_ruler_night4.py score4 OUT ANS_BY_LABEL --tau 0.3
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

TAU = 0.3
TAUS_BESIDE = (0.2, 0.3, 0.4)
READOUT_STRINGS = ("s00", "c00", "s01", "c01")
OR42 = dict(device="ibm_fez", drow=4, physical=(104, 102), t=4)     # owner 2026-11-25 20:18 JST

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
# beside, never judged: compared with (d), as the addendum asks (a reading row, not a prediction)
READ_DE_VS_D = {
    "SMALLER": "|d| of (de) below |d| of (d): the readout would explain part of (d)'s gap",
    "NOT SMALLER": "|d| of (de) not below |d| of (d): the readout does not explain (d)'s gap",
}


def readout_circuit(n_qubits, phys, bits, clbit_order):
    """X on the physical qubits whose bit is 1, then measure clbit_order[k] into clbit k (the user records' order of
    labels, so that the job reader maps clbits to qubits as for every other record): no other gate."""
    from qiskit import QuantumCircuit
    qc = QuantumCircuit(n_qubits, len(phys))
    for q, b in zip(phys, bits):
        if b == "1":
            qc.x(q)
    qc.barrier(phys)
    for k, q in enumerate(clbit_order):
        qc.measure(q, k)
    return qc


# ---------------------------------------------------------------------------------------------------------- build4

def cmd_build4(a):
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
    for nm in READOUT_STRINGS:
        bits = "".join(b["strings"][nm][p] for p in pos)
        qc = readout_circuit(dev.num_qubits, phys, bits, [int(mapping[lb]) for lb in labels])
        U._record(dev, runs, f"p2d_readout_{nm}", "readout", "user2d_readout", [qc], [dict(input="r", setting="z")],
                  labels, mapping, dict(tag=f"readout_{nm}", string=nm, positions=pos, physical=phys, cz=0),
                  a.shots, True)
    shutil.move(os.path.join(a.out, "job"), os.path.join(a.out, "unsent_job_build3"))
    man = J.assemble(dev, runs, os.path.join(a.out, "job"), max_seconds=a.max_seconds)
    n_c = len(man["pubs"])
    b.update(circuits=n_c, charge_seconds=round(ORN.charge(n_c, a.shots), 1),
             qpu_seconds_model_psf_os=man["qpu_seconds_model"], circuits_sha256=man.get("circuits_sha256"),
             readout=dict(strings=list(READOUT_STRINGS), positions=pos, physical=phys, t=t4))
    json.dump(b, open(os.path.join(a.out, "build.json"), "w"), indent=1)
    print(f"build4: + {len(READOUT_STRINGS)} readout circuits on the t = {t4} cone ({len(phys)} qubits); circuits "
          f"{n_c}; charge {b['charge_seconds']} s (2.6 + 0.000269 x circuits x shots); psf-os model "
          f"{man['qpu_seconds_model']} s")


# ---------------------------------------------------------------------------------------------------------- check4

def cmd_check4(a):
    sys.path.insert(0, HERE)
    import hub_check as HK
    ORN3.cmd_check3(a)
    b = json.load(open(os.path.join(a.out, "build.json")))
    base = json.load(open(os.path.join(a.out, "check3.json")))
    ok = base["smirrors"]["ALL"] == "PASS"
    res = {}
    for nm in b["readout"]["strings"]:
        z, method = HK.z_of(HK.reduced(HK.load(os.path.join(a.out, "runs", f"p2d_readout_{nm}.qpy")),
                                       b["readout"]["physical"]))
        ideal = np.array([1 - 2 * int(b["strings"][nm][p]) for p in b["readout"]["positions"]], dtype=float)
        worst = float(np.abs(z - ideal).max())
        res[nm] = dict(method=method, worst=worst, ok=worst < 1e-9)
        ok &= worst < 1e-9
        print(f"readout {nm}: {method}: worst {worst:.1e} {'PASS' if worst < 1e-9 else 'FAIL'}")
    res["ALL"] = "PASS" if ok else "FAIL"
    json.dump(dict(check3=base["smirrors"]["ALL"], readout=res), open(os.path.join(a.out, "check4.json"), "w"),
              indent=1)
    print("ALL (declared check, string mirrors, readout)", res["ALL"])


# ---------------------------------------------------------------------------------------------------------- score4

def _z(counts, rec_labels, labels, weights, idx):
    return ORN3.counts_mean_se(counts, rec_labels, labels, weights, idx)


def _ruler(w_k, w_ex, K, extra_var=0.0):
    d = w_k - w_ex
    se = math.sqrt(float(np.std(d, ddof=1) / np.sqrt(K)) ** 2 + extra_var)
    return dict(d=float(d.mean()), se=se, t_se=ORN2.t975(K - 1) * se, words=ORN3.word(float(d.mean()), se, K))


def cmd_score4(a):
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
            rrec[rec["string"]] = (counts, rec["labels"], b["readout"]["positions"])
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
    e_of, e2_of, var_e = {}, {}, {}
    for pair, (sn, cn) in enumerate((("s00", "c00"), ("s01", "c01"))):
        sig = np.array([1 - 2 * int(strs[sn][p]) for p in rpos], dtype=float)
        zs, _ = _z(rrec[sn][0], rrec[sn][1], ro_labels, sig, [])
        zc, _ = _z(rrec[cn][0], rrec[cn][1], ro_labels, sig, [])
        e = (zs - zc) / 2 * sig
        for i, p in enumerate(rpos):
            (e_of if pair == 0 else e2_of)[p] = float(e[i])
            if pair == 0:
                var_e[p] = float(((1 - zs[i] ** 2) + (1 - zc[i] ** 2)) / shots / 4)
    dev_rec = man.get("device", {})
    calib = (dev_rec.get("source") or {}).get("calibration_time", "") if isinstance(dev_rec.get("source"), dict) else ""
    drow = b["copy_of_F"]["drow"]
    res = dict(device=b["device"], calibration_time=calib, copy_drow=drow, tau=a.tau, cells={}, direction={},
               tau_beside={}, readout_pairs={}, tables={}, or4_2=None)
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
                r_low = (pool is not None and math.isfinite(rq_) and se_ > 0 and abs(rq_ - pool) > 2 * se_)
                rows.append(dict(device=b["device"], calibration_time=calib, copy_drow=drow, arm=arm, t=t,
                                 position=p, physical=phys[i], in_window=p in win, mirror_z=round(float(zm[i]), 4),
                                 m_q=round(float(m[i]), 4), r_q="" if not math.isfinite(rq_) else round(rq_, 4),
                                 e_q="" if p not in e_of else round(e_of[p], 4),
                                 left_out_at_tau=(p not in win and zm[i] < a.tau),
                                 MIRROR_LOW=bool(zm[i] < a.tau), R_LOW=bool(r_low)))
            res["cells"][key] = cell
            if t >= 3:
                res["tables"][key] = {r: READ_TABLE_C[(r, cell[r]["words"]["t"])] for r in ("e", "de", "a_prime")
                                      if r in cell}
    res["readout_pairs"] = {str(p): dict(e_s00c00=e_of[p], e_s01c01=e2_of[p], difference=e2_of[p] - e_of[p])
                            for p in rpos}
    res["or4_2"] = or4_2(b, mirror_by)
    json.dump(res, open(os.path.join(a.out, "scores4.json"), "w"), indent=1)
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
    print(f"OR4-2: {res['or4_2']['word']}")


def _direction(dl, K):
    se = float(np.std(dl, ddof=1) / np.sqrt(K))
    tq = ORN2.t975(K - 1)
    mu = float(dl.mean())
    word = ("NOT READ" if not se > 0 else "WINDOW SHRINKS LESS" if mu > tq * se else
            "WINDOW SHRINKS MORE" if mu < -tq * se else "NOT SEEN")
    return dict(r_minus_rho=mu, se=se, t_se=tq * se, word=word)


def or4_2(b, mirror_by):
    """OR4-2 (declared on the owner's decision): on ibm_fez at copy drow 4, physical 104 and 102 sit below tau 0.3 on
    the t = 4 |0> mirror in all three arms. Another device or copy, or a qubit not on the t = 4 cone: NOT READ."""
    if b["device"] != OR42["device"] or b["copy_of_F"]["drow"] != OR42["drow"] or OR42["t"] not in b["cycles"]:
        return dict(word="NOT READ", why="another device or copy")
    vals = {}
    for arm in ORN.ARMS:
        mz = mirror_by[f"{arm}_t{OR42['t']}_L"]
        if any(q not in mz for q in OR42["physical"]):
            return dict(word="NOT READ", why="a qubit not on the t = 4 cone")
        vals[arm] = {str(q): mz[q] for q in OR42["physical"]}
    held = all(v < TAU for a_ in vals.values() for v in a_.values())
    return dict(word="HELD" if held else "NOT HELD", mirror_z=vals)


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("build4")
    for x in ("dev", "out", "ans_in", "ans_out"):
        p.add_argument(x)
    p.add_argument("--shots", type=int, default=1000)
    p.add_argument("--pairs-t", nargs="*", default=None)
    p.add_argument("--max-seconds", type=float, default=60.0)
    for nm in ("check4", "score4"):
        p = sp.add_parser(nm)
        p.add_argument("out")
        p.add_argument("answers")
        if nm == "score4":
            p.add_argument("--tau", type=float, default=TAU)
    a = ap.parse_args()
    dict(build4=cmd_build4, check4=cmd_check4, score4=cmd_score4)[a.cmd](a)


if __name__ == "__main__":
    main()
