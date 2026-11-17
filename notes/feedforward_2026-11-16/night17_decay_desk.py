"""Tonight's T2 and T3-A (prereg/ff_night_2026-11-17.md) under the ILLUSTRATIVE decay model of RUS_DECAY_DESK
(workplace VS Claude, 2026-11-17; desk only; nothing fitted to any device, no calibration or error number read).

Model: rus_decay_desk.noise(gamma) with gamma = 0.05 and 0.1 per mid-circuit wait (and 0 beside): one-qubit gates 3e-4,
CZ 3e-3, recorded bit flipped with 0.015 (mid-circuit and final), and during every mid-circuit measurement every other
live qubit gets amplitude damping gamma and a phase flip of 0.024.

T2  the third design (gpu/rus3_night.chain, m = 2, theta 1.1), L = 1 .. 5, modelled by rus_decay_desk.dynamic_any
    (as compiled on 2026-11-16: the ancilla measured m times on every branch). Per L, as gpu/compound_night.py scores
    it: c = |P_off,noiseless - exact| (notes/compound_2026-11-17/ideal.json), e = |P_ff - exact|, g = c - e,
    SE = sqrt(P_ff (1 - P_ff) / 4000); OVERSHOOT when P_ff > P_ff,noiseless + 2 SE; BEYOND when g >= 2 SE and no
    overshoot; slope of g over L by compound.slope (weighted least squares); COMPOUNDS when slope >= 2 SE and no
    overshoot.
T3-A iterative phase estimation, notes/ffapps_2026-11-17/apps.ipe(n, j, feedback) as written (n = 2, 3; every j),
    walked gate by gate with a density matrix per classical record: h / p / x as one-qubit gates (3e-4 each), cz
    (3e-3), every measurement with the waits on the other qubit and the recorded flip, if_test on the recorded bit.
    Success = all n recorded bits right; per n the share pooled over the phases (4000 shots each) against the
    declared noiseless ceiling C(n) (0.750, 0.588); GROWS when margin(3) - margin(2) >= 2 SE of the difference.

Checks: (1) noiseless T2 ff / off equal compound ideal.json; noiseless T3-A ff = 1, off and the decoder ceiling equal
apps.ipe_ideal (an exact branching simulation by the workplace, a separate engine); (2) T3-A with decay against a
Monte Carlo over Kraus trajectories on the state vector (a separate walk).
usage: python notes/feedforward_2026-11-16/night17_decay_desk.py   (numpy and qiskit; writes night17_decay_desk.txt / .json)
"""
import importlib.util
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


sys.path.insert(0, os.path.join(ROOT, "notes", "rus_coherent_2026-11-17"))
D = _load("rus_decay_desk", os.path.join(HERE, "rus_decay_desk.py"))
CP = _load("compound", os.path.join(ROOT, "notes", "compound_2026-11-17", "compound.py"))
AP = _load("apps", os.path.join(ROOT, "notes", "ffapps_2026-11-17", "apps.py"))

GAMMAS = (0.0, 0.05, 0.1)
LS = (1, 2, 3, 4, 5)
NS = (2, 3)
SHOTS = 4000
H = np.array([[1, 1], [1, -1]], dtype=complex) / math.sqrt(2)


def P(lam):
    return np.diag([1, np.exp(1j * lam)]).astype(complex)


# ------------------------------------------------------------------------------------------------ T2

def t2(gamma, ideal):
    nz = D.noise(gamma)
    rows = {}
    for L in LS:
        p, _ = D.dynamic_any(L, 2, "D3", "ff", nz)
        ref = ideal[str(L)]
        se = math.sqrt(p * (1 - p) / SHOTS)
        e = abs(p - ref["exact"])
        g = ref["ceiling"] - e
        over = p > ref["ff"] + 2 * se
        v = "OVERSHOOT" if over else ("BEYOND THE CORRECTION CEILING" if g >= 2 * se else "NOT BEYOND")
        rows[L] = dict(p_ff=p, ff_noiseless=ref["ff"], exact=ref["exact"], c=ref["ceiling"], e=e, g=g, se=se,
                       loss=p - ref["ff"], verdict=v, kept=g / ref["noiseless_margin"])
    b, sb = CP.slope(list(LS), [rows[L]["g"] for L in LS], [rows[L]["se"] for L in LS])
    over = [L for L in LS if rows[L]["verdict"] == "OVERSHOOT"]
    return rows, dict(slope=b, se=sb, overshoot_at=over,
                      verdict="COMPOUNDS" if (b >= 2 * sb and not over) else "NOT SHOWN")


# ------------------------------------------------------------------------------------------------ T3-A

def _gate_matrix(name, params):
    if name == "h":
        return H
    if name == "x":
        return D.X
    if name == "p":
        return P(float(params[0]))
    raise ValueError(name)


def _walk(qc, nz):
    """Exact: {recorded bits (tuple, index = clbit): LazyRho}; the if_test reads the recorded bit."""
    nq, nc = qc.num_qubits, qc.num_clbits
    r0 = D.LazyRho()
    for q in range(nq):
        r0._ax(q)
    states = {(0,) * nc: r0}

    def apply(st, inst, qidx):
        name = inst.operation.name
        if name == "cz":
            st.cz(*qidx)
            st.depol(list(qidx), nz["p2"])
        else:
            st.kraus1(qidx[0], _gate_matrix(name, inst.operation.params))
            st.depol([qidx[0]], nz["p1"])

    for inst in qc.data:
        name = inst.operation.name
        qidx = [qc.find_bit(q).index for q in inst.qubits]
        if name == "measure":
            c = qc.find_bit(inst.clbits[0]).index
            new = {}
            for rec, st in states.items():
                for v, x in D.measure_split(st, qidx[0], nz).items():
                    key = rec[:c] + (v,) + rec[c + 1:]
                    if key in new:
                        new[key].m = new[key].m + x.m
                    else:
                        new[key] = x
            states = new
        elif name == "if_else":
            (bit, val) = inst.operation.condition
            c = qc.find_bit(bit).index
            body = inst.operation.blocks[0]
            for rec, st in states.items():
                if rec[c] == val:
                    for sub in body.data:
                        apply(st, sub, [qidx[body.find_bit(q).index] for q in sub.qubits])
        else:
            for st in states.values():
                apply(st, inst, qidx)
    return {k: v.tr() for k, v in states.items()}


def _mc(qc, nz, shots, seed):
    """Monte Carlo over Kraus trajectories on the state vector: depolarising as a random Pauli, damping and phase flip
    as sampled Kraus operators, the outcome sampled, the recorded flip sampled. Returns {recorded bits: share}."""
    rng = np.random.default_rng(seed)
    nq, nc = qc.num_qubits, qc.num_clbits
    paulis = [np.eye(2, dtype=complex), D.X, np.array([[0, -1j], [1j, 0]]), np.diag([1, -1]).astype(complex)]

    def ap1(psi, q, K):
        t = np.moveaxis(np.tensordot(K, psi, axes=([1], [q])), 0, q)
        return t

    def kr(psi, q, Ks):
        cands = [ap1(psi, q, K) for K in Ks]
        w = np.array([np.vdot(c, c).real for c in cands])
        i = rng.choice(len(Ks), p=w / w.sum())
        return cands[i] / math.sqrt(w[i])

    def depol(psi, qs, p):
        if rng.random() < p:
            while True:
                idx = [rng.integers(4) for _ in qs]
                if any(idx):
                    break
            for q, i in zip(qs, idx):
                psi = ap1(psi, q, paulis[i])
        return psi

    def apply(psi, inst, qidx):
        name = inst.operation.name
        if name == "cz":
            a, b = qidx
            psi = psi.copy()
            sl = [slice(None)] * nq
            sl[a], sl[b] = 1, 1
            psi[tuple(sl)] *= -1
            return depol(psi, qidx, nz["p2"])
        psi = ap1(psi, qidx[0], _gate_matrix(name, inst.operation.params))
        return depol(psi, qidx, nz["p1"])

    zf = [np.sqrt(1 - nz["pz"]) * np.eye(2, dtype=complex), np.sqrt(nz["pz"]) * np.diag([1, -1]).astype(complex)]
    counts = {}
    for _ in range(shots):
        psi = np.zeros((2,) * nq, dtype=complex)
        psi[(0,) * nq] = 1
        rec = [0] * nc
        for inst in qc.data:
            name = inst.operation.name
            qidx = [qc.find_bit(q).index for q in inst.qubits]
            if name == "measure":
                q, c = qidx[0], qc.find_bit(inst.clbits[0]).index
                for k in range(nq):
                    if k != q:
                        if nz["gamma"]:
                            psi = kr(psi, k, D.kraus_ad(nz["gamma"]))
                        if nz["pz"]:
                            psi = kr(psi, k, zf)
                p1 = float(np.sum(np.abs(np.take(psi, 1, axis=q)) ** 2))
                v = int(rng.random() < p1)
                proj = np.zeros((2, 2), dtype=complex)
                proj[v, v] = 1
                psi = ap1(psi, q, proj)
                psi = psi / math.sqrt(np.vdot(psi, psi).real)
                rec[c] = v ^ int(rng.random() < nz["e"])
            elif name == "if_else":
                (bit, val) = inst.operation.condition
                if rec[qc.find_bit(bit).index] == val:
                    body = inst.operation.blocks[0]
                    for sub in body.data:
                        psi = apply(psi, sub, [qidx[body.find_bit(q).index] for q in sub.qubits])
            else:
                psi = apply(psi, inst, qidx)
        k = tuple(rec)
        counts[k] = counts.get(k, 0) + 1
    return {k: v / shots for k, v in counts.items()}


def _success(dist, succ):
    return sum(p for k, p in dist.items() if all(k[m] == v for m, v in succ.items()))


def t3a(n, nz):
    ff, off, offd = [], [], {}
    for j in range(2 ** n):
        for fb in (True, False):
            qc, succ = AP.ipe(n, j, fb)
            dist = _walk(qc, nz)
            (ff if fb else off).append(_success(dist, succ))
            if not fb:
                offd[j] = dist
    keys = set().union(*offd.values())
    dec = sum(max(offd[j].get(k, 0.0) for j in offd) for k in keys) / 2 ** n
    return dict(ff=sum(ff) / len(ff), ff_min=min(ff), off=sum(off) / len(off), decoder_of_off=dec, per_phase=ff)


# ------------------------------------------------------------------------------------------------ main

def main():
    f = D.as_text
    ideal = json.load(open(os.path.join(ROOT, "notes", "compound_2026-11-17", "ideal.json")))
    out = dict(model=dict(gammas=GAMMAS, p1=f(D.P1), p2=f(D.P2), readout=f(D.E_RO), pz=f(D.PZ), illustrative=True,
                          fitted_to_device=False), checks={}, T2={}, T3A={})
    T = ["Tonight's T2 and T3-A under the ILLUSTRATIVE decay model of RUS_DECAY_DESK (not fitted to any device; no "
         "calibration or error number read). Exact density matrices; SE for 4000 shots per circuit.", ""]

    # check 1 (noiseless)
    nz0 = D.noise(0, off=True)
    w = 0.0
    for L in LS:
        for arm in ("ff", "off"):
            w = max(w, abs(D.dynamic_any(L, 2, "D3", arm, nz0)[0] - ideal[str(L)][arm]))
    wa = 0.0
    ref = {n: AP.ipe_ideal(n) for n in NS}
    for n in NS:
        r = t3a(n, nz0)
        wa = max(wa, abs(r["ff"] - 1), abs(r["ff_min"] - 1), abs(r["off"] - ref[n]["off"]),
                 abs(r["decoder_of_off"] - ref[n]["ceiling"]))
    ok1 = w < 1e-9 and wa < 1e-9
    T.append(f"Check 1, noiseless: T2 ff / off against compound ideal.json (L 1-5) largest difference {w:.1e}; T3-A ff, "
             f"off and the decoder ceiling against apps.ipe_ideal (n 2, 3) largest difference {wa:.1e}: "
             f"{'PASS' if ok1 else 'FAIL'}")
    out["checks"]["noiseless"] = dict(t2=f(w), t3a=f(wa), passed=ok1)

    # check 2 (decay; separate walk)
    rows, worst = [], 0.0
    for n, j, g, shots, seed in ((2, 1, 0.1, 20000, 11), (3, 5, 0.1, 20000, 12), (3, 3, 0.05, 20000, 13)):
        qc, succ = AP.ipe(n, j, True)
        ex = _success(_walk(qc, D.noise(g)), succ)
        mc = _success(_mc(qc, D.noise(g), shots, seed), succ)
        z = (mc - ex) / math.sqrt(ex * (1 - ex) / shots)
        worst = max(worst, abs(z))
        rows.append(f"  ipe n {n} j {j} gamma {g}: exact {ex:.3f}, MC {mc:.3f} ({z:+.1f} SE, {shots} shots)")
    ok2 = worst < 4
    T.append(f"Check 2, T3-A with decay against a Monte Carlo over Kraus trajectories: {'PASS' if ok2 else 'FAIL'} "
             f"(largest {worst:.1f} SE)")
    T += rows + [""]
    out["checks"]["monte_carlo_t3a"] = dict(largest_se=f(worst), passed=ok2)

    # T2
    T.append("T2 (third design, m 2): per L exact, noiseless ff, ceiling c, model ff, loss (ff - noiseless ff), "
             "g = c - |ff - exact|, 2 SE, verdict, share of the noiseless margin kept")
    for g in GAMMAS:
        rows, sl = t2(g, ideal)
        T.append(f" gamma {g}:")
        for L in LS:
            r = rows[L]
            T.append(f"  L {L}: exact {r['exact']:.3f}  ff0 {r['ff_noiseless']:.3f}  c {r['c']:.3f}  ff {r['p_ff']:.3f}"
                     f"  loss {r['loss']:+.3f}  g {r['g']:+.3f} (2 SE {2 * r['se']:.3f})  {r['verdict']}  kept "
                     f"{r['kept']:.2f}")
        T.append(f"  slope of g {sl['slope']:+.3f} per step (2 SE {2 * sl['se']:.3f}) -> {sl['verdict']}"
                 + (f" (overshoot at L {sl['overshoot_at']})" if sl["overshoot_at"] else ""))
        out["T2"][str(g)] = dict(rows={str(L): {k: (f(v) if isinstance(v, float) else v) for k, v in r.items()}
                                       for L, r in rows.items()},
                                 slope={k: (f(v) if isinstance(v, float) else v) for k, v in sl.items()})
    T.append("")

    # T3-A
    T.append("T3-A (iterative phase estimation): per n the ff success pooled over the phases (4000 shots each) against "
             "the declared noiseless ceiling; off as read and the best decoder of the modelled off bits beside")
    for g in GAMMAS:
        nz = D.noise(g)
        res = {n: t3a(n, nz) for n in NS}
        T.append(f" gamma {g}:")
        marg = {}
        for n in NS:
            r = res[n]
            N = SHOTS * 2 ** n
            se = math.sqrt(r["ff"] * (1 - r["ff"]) / N)
            c = ref[n]["ceiling"]
            marg[n] = (r["ff"] - c, se)
            v = "BEYOND THE CEILING" if r["ff"] >= c + 2 * se else "NOT BEYOND"
            T.append(f"  n {n}: ff {r['ff']:.3f} (lowest phase {r['ff_min']:.3f}; 2 SE {2 * se:.3f}) ceiling {c:.3f} "
                     f"margin {r['ff'] - c:+.3f} -> {v}; off as read {r['off']:.3f}; best decoder of the modelled off "
                     f"bits {r['decoder_of_off']:.3f}")
            out["T3A"].setdefault(str(g), {})[str(n)] = dict(
                ff=f(r["ff"]), ff_min=f(r["ff_min"]), se=f(se), ceiling=f(c), margin=f(r["ff"] - c), verdict=v,
                off_as_read=f(r["off"]), decoder_of_off=f(r["decoder_of_off"]),
                per_phase=[f(x) for x in r["per_phase"]])
        d = marg[3][0] - marg[2][0]
        sd = math.hypot(marg[2][1], marg[3][1])
        gv = "GROWS" if d >= 2 * sd else "NOT SHOWN"
        T.append(f"  margin(3) - margin(2) {d:+.3f} (2 SE {2 * sd:.3f}) -> {gv}")
        out["T3A"][str(g)]["growth"] = dict(diff=f(d), se=f(sd), verdict=gv)
    open(os.path.join(HERE, "night17_decay_desk.txt"), "w", newline="\n").write("\n".join(T) + "\n")
    json.dump(out, open(os.path.join(HERE, "night17_decay_desk.json"), "w", newline="\n"), indent=1)
    print("\n".join(T))


if __name__ == "__main__":
    main()
