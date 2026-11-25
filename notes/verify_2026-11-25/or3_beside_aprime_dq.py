#!/usr/bin/env python3
# Beside values after the record (never judged), Ohm ruler third night (2026-11-25):
#   (a')  the circuit's total over the qubits that (b') keeps (window qubits always; outside qubits whose |0> mirror
#         <Z> >= tau), divided by the exact total over the same qubits (from the sealed answers), per pair;
#         and the direction r - rho_a' as the declared direction with rho_a' in place of rho_a.
#   (dq)  ruler (d) per window qubit: O_q / sqrt(m_q), m_q the string mirrors' odd part on that qubit.
# qiskit + numpy only; the qubit-to-clbit map from the measure instructions of the circuits as sent.
# Author: The Architect <love.os.architect@proton.me>
import gzip
import io
import json
import math
import os
import sys

import numpy as np
from qiskit import qpy

R, OUT = sys.argv[1], sys.argv[2]
ARMS, TS = ("A0", "A1", "A2"), (1, 3, 4)
KT = {1: 7, 3: 7, 4: 9}
T975 = {6: 2.447, 8: 2.306}
TAU, SHOTS = 0.3, 1000


def window(t):
    return list(range(20, 20 + 2 * t - 1))


def cone(t):
    return {1: list(range(18, 22)), 3: list(range(14, 30)), 4: list(range(12, 34))}[t]


A = json.load(open(f"{R}/answers/ohm_ruler_answers_L9.json"))
B = json.load(open(f"{R}/or3/build.json"))
strs = A["meta"]["strings"]
man = json.load(open(f"{R}/or3/job/manifest.json"))
raw = json.load(open(f"{R}/or3/job/raw_counts.json"))
qp = f"{R}/or3/job/circuits.qpy"
circs = qpy.load(io.BytesIO(open(qp, "rb").read() if os.path.exists(qp) else gzip.open(qp + ".gz").read()))
cell_name = {c["cell"]: c["name"] for c in man["cells"]}
pub_name = [cell_name[p["cell"]] + (f"#{p['point']}" if cell_name[p["cell"]].startswith("ksent") else "")
            for p in man["pubs"]]
pi = {n: i for i, n in enumerate(pub_name)}
rows = {r["pub"]: r["counts"] for r in raw["rows"]}
F = [q + 80 for q in B["chain"]["labels"]]       # copy drow 4, checked in or3_independent_check.py


def meas(nm):
    qc = circs[pi[nm]]
    return {qc.find_bit(i.qubits[0]).index: qc.find_bit(i.clbits[0]).index for i in qc.data
            if i.operation.name == "measure"}


def z_of(nm, phys, weights=None):
    m = meas(nm)
    cl = [m[q] for q in phys]
    w = np.ones(len(cl)) if weights is None else np.asarray(weights, float)
    counts = rows[pi[nm]]
    tot = sum(counts.values())
    z = np.zeros(len(cl))
    per = []
    for key, c in counts.items():
        s = key.replace(" ", "")
        v = np.array([1 - 2 * int(s[-1 - k]) for k in cl])
        z += c * v
        per.append(((w * v).mean(), c))
    z /= tot
    mu = sum(a * c for a, c in per) / tot
    return z, math.sqrt(sum(c * (a - mu) ** 2 for a, c in per) / (tot - 1) / tot)


def words(d, se, K):
    if not se > 0:
        return {"t": "NOT READ", "2se": "NOT READ"}
    return {"t": "AGREES" if abs(d) < T975[K - 1] * se else "DIFFERS", "2se": "AGREES" if abs(d) < 2 * se else "DIFFERS"}


res = {}
for a in ARMS:
    for t in TS:
        K, pos = KT[t], cone(t)
        phys = [F[p] for p in pos]
        wi = [pos.index(p) for p in window(t)]
        Od, Oe, T0, const = [], [], [], []
        for k in range(K):
            s, c = f"p2d_{a}_t{t}_L_s{k:02d}", f"p2d_{a}_t{t}_L_c{k:02d}"
            apos = A["meta"]["positions"][f"t{t}_L"]
            zs, zc = z_of(s, phys)[0], z_of(c, phys)[0]
            es = np.array([A["z"][s[4:]][apos.index(p)] for p in pos])
            ec = np.array([A["z"][c[4:]][apos.index(p)] for p in pos])
            Od.append((zs - zc) / 2)
            Oe.append((es - ec) / 2)
            T0.append(sum(1 - 2 * int(strs[f"s{k:02d}"][p]) for p in pos))
            ms = sum(int(strs[f"s{k:02d}"][p]) for p in window(t))
            mc = sum(int(strs[f"c{k:02d}"][p]) for p in window(t))
            const.append(-(ms - mc) / 2)
        Od, Oe, T0, const = map(np.array, (Od, Oe, T0, const))
        se_k = lambda x: float(np.std(x, ddof=1) / math.sqrt(K))
        sumOw = Od[:, wi].sum(axis=1)
        w_ex = -Oe[:, wi].sum(axis=1) / 2 + const
        cell = dict(K=K)
        # the |0> mirror per qubit and (b')'s kept set
        zm, _ = z_of(f"p2d_{a}_t{t}_L_s00_mirror", phys)
        keep = [i for i, p in enumerate(pos) if p in window(t) or zm[i] >= TAU]
        cell["left_out"] = [pos[i] for i in range(len(pos)) if i not in keep]
        if t >= 3:
            rho_a = Od.sum(axis=1) / T0
            rho_ap = Od[:, keep].sum(axis=1) / Oe[:, keep].sum(axis=1)
            cell["exact_kept_total_over_T0"] = (Oe[:, keep].sum(axis=1) / T0).round(4).tolist()
            for name, rho in (("a", rho_a), ("a_prime", rho_ap)):
                wx = -(sumOw / rho) / 2 + const
                dx = wx - w_ex
                cell[name] = dict(rho_mean=float(rho.mean()), d=float(dx.mean()), se=se_k(dx),
                                  t_se=T975[K - 1] * se_k(dx), words=words(float(dx.mean()), se_k(dx), K))
            use = [i for i in wi if np.sum(Oe[:, i] ** 2) >= 0.05 * K]
            rk = np.array([float(np.sum(Od[k, use] * Oe[k, use]) / np.sum(Oe[k, use] ** 2)) for k in range(K)])
            for name, rho in (("dir_a", rho_a), ("dir_a_prime", rho_ap)):
                dk = rk - rho
                mu, sd = float(dk.mean()), se_k(dk)
                cell[name] = dict(r_minus_rho=mu, t_se=T975[K - 1] * sd,
                                  word="NOT READ" if sd == 0 else "WINDOW SHRINKS LESS" if mu > T975[K - 1] * sd
                                  else "WINDOW SHRINKS MORE" if mu < -T975[K - 1] * sd else "NOT SEEN")
        # ruler (d): the cell mean (as declared) and per window qubit
        sign = np.array([1 - 2 * int(strs["s00"][pos[i]]) for i in wi])
        wphys = [phys[i] for i in wi]
        zsm, ses = z_of(f"p2d_{a}_t{t}_L_s00_smirror", wphys, sign)
        zcm, sec = z_of(f"p2d_{a}_t{t}_L_c00_smirror", wphys, sign)
        mq = (zsm - zcm) / 2 * sign
        var_mq = ((1 - zsm ** 2) + (1 - zcm ** 2)) / SHOTS / 4
        md = float(mq.mean())
        wd = -(sumOw / math.sqrt(md)) / 2 + const
        dd = wd - w_ex
        se_d = math.sqrt(se_k(dd) ** 2 + (float(np.mean(sumOw)) / (4 * md ** 1.5) * math.hypot(ses, sec) / 2) ** 2)
        cell["d"] = dict(rho=math.sqrt(md), d=float(dd.mean()), se=se_d, t_se=T975[K - 1] * se_d,
                         words=words(float(dd.mean()), se_d, K))
        cell["m_q"] = {str(p): round(float(mq[j]), 4) for j, p in enumerate(window(t))}
        if np.all(mq > 0):
            Ow = Od[:, wi] / np.sqrt(mq)[None, :]
            wq = -Ow.sum(axis=1) / 2 + const
            dq = wq - w_ex
            # mirror shot noise per qubit through 1 / sqrt(m_q): dW / dm_q = mean_k O_q / (4 m_q^1.5)
            slope = Od[:, wi].mean(axis=0) / (4 * mq ** 1.5)
            se_q = math.sqrt(se_k(dq) ** 2 + float(np.sum(slope ** 2 * var_mq)))
            cell["dq"] = dict(d=float(dq.mean()), se=se_q, se_pairs=se_k(dq), t_se=T975[K - 1] * se_q,
                              words=words(float(dq.mean()), se_q, K))
        else:
            cell["dq"] = dict(words={"t": "NOT READ", "2se": "NOT READ"}, why="m_q <= 0 on a window qubit")
        res[f"{a}_t{t}"] = cell

json.dump(res, open(OUT, "w"), indent=1)
for k, c in res.items():
    print(f"== {k} (K {c['K']}) left out {c['left_out']}")
    for r_ in ("a", "a_prime", "d", "dq"):
        if r_ in c and "d" in c[r_]:
            v = c[r_]
            print(f"   {r_:8s} d {v['d']:+.4f}  t width {v['t_se']:.4f}  2SE {2 * v['se']:.4f}  {v['words']}"
                  + (f"  rho_mean {v['rho_mean']:.3f}" if "rho_mean" in v else ""))
    for r_ in ("dir_a", "dir_a_prime"):
        if r_ in c:
            print(f"   {r_:12s} {c[r_]['r_minus_rho']:+.4f} (t width {c[r_]['t_se']:.4f}) {c[r_]['word']}")
    print("   m_q", c["m_q"])
