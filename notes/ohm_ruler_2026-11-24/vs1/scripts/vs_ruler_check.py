"""Independent re-computation of gpu/ohm_ruler_night.py's rulers from a scored dry run (workplace VS, 2026-11-24,
sono1; author The Architect). qiskit (qpy only) and numpy; no psf-os, no notebook scorer. The qubit -> clbit map is read
from each sent circuit's measure instructions; the items from the manifest's cell names; the strings and labels from
build.json; the exact <Z> from the sealed answers by label. No answer value is printed: only differences against the
tool's scores.json and the counts of words.

Per cell (arm, t, form): the raw W (W = (M_s - M_c) / 2 written as -sum O_window / 2 - (m_s - m_c) / 2), ruler (a)
rho_a = T_device / T0 per pair and W_a, ruler (b) rho_b = sqrt(mean <Z> of the mirror) and W_b with the delta-method SE,
their words (|d| < 2 SE: AGREES), and at t >= 3 the uniformity r per window position, its shot-noise SE, the
weighted pool, chi2 and p (chi-square, n - 1 dof). Also the identity sum_window O_exact over every qubit = T0 (the
conservation the ruler (a) uses), checked on the answers.

  python vs_ruler_check.py RUN_DIR ANSWERS.json
"""
import gzip
import io
import json
import math
import os
import sys

import numpy as np
from qiskit import qpy

ARMS = ("A0", "A1", "A2")


def dmax(w, *ds):
    # a NaN difference (one side NaN, the other not) counts as infinite, so it can never hide
    for d in ds:
        w = max(w, float("inf") if d != d else d)
    return w
UNIFORM_FLOOR = 0.05


def chi2_sf(x, k):
    from math import erfc, exp, sqrt, pi
    if k % 2 == 0:
        s, term = 0.0, 1.0
        for i in range(k // 2):
            if i:
                term *= (x / 2) / i
            s += term
        return exp(-x / 2) * s
    s = erfc(sqrt(x / 2))
    term = sqrt(2 * x / pi) * exp(-x / 2)
    for i in range(1, (k - 1) // 2 + 1):
        s += term
        term *= x / (2 * i + 1)
    return s


def main():
    run, ansf = sys.argv[1:3]
    man = json.load(open(os.path.join(run, "job", "manifest.json")))
    raw = json.load(open(os.path.join(run, "job", "raw_counts.json")))
    p = os.path.join(run, "job", "circuits.qpy")
    blob = gzip.open(p + ".gz").read() if os.path.exists(p + ".gz") else open(p, "rb").read()
    circs = qpy.load(io.BytesIO(blob))
    b = json.load(open(os.path.join(run, "build.json")))
    A = json.load(open(ansf))["z"]
    cell = {c["cell"]: c["name"] for c in man["cells"]}
    rows = {r["pub"]: r["counts"] for r in raw["rows"]}
    shots = man["shots"]
    z, zse = {}, {}
    for i, pb in enumerate(man["pubs"]):
        name = cell[pb["cell"]]
        if not name.startswith("p2d_"):
            continue
        tg = name[4:]
        meas = {}
        for ins in circs[i].data:
            if ins.operation.name == "measure":
                meas[circs[i].find_bit(ins.qubits[0]).index] = circs[i].find_bit(ins.clbits[0]).index
        base = tg.replace("_mirror", "")
        labels = b["items"][base]["given_labels"]
        cnt, tot = rows[i], sum(rows[i].values())
        v_sum = np.zeros(len(labels))
        per_shot = []
        for key, c in cnt.items():
            s = key.replace(" ", "")
            v = np.array([1 - 2 * int(s[-1 - meas[lb]]) for lb in labels])
            v_sum += c * v
            per_shot.append((v.mean(), c))
        zz = v_sum / tot
        mu = sum(m * c for m, c in per_shot) / tot
        se = math.sqrt(sum(c * (m - mu) ** 2 for m, c in per_shot) / (tot - 1) / tot)
        z[tg], zse[tg] = zz, se
    strs = b["strings"]
    ks = sorted({n[1:] for n in strs})
    K = len(ks)
    sc = json.load(open(os.path.join(run, "scores.json")))
    worst, words, conserv = 0.0, {}, 0.0
    for arm in ARMS:
        for t in b["cycles"]:
            for form in b["forms"]:
                key = f"{arm}_t{t}_{form}"
                it = b["items"][f"{key}_s00"]
                pos, labels = it["positions"], it["given_labels"]
                win = list(range(20, 20 + 2 * t - 1))
                wi = [i for i, q in enumerate(pos) if q in win]
                Od = np.array([(z[f"{key}_s{k}"] - z[f"{key}_c{k}"]) / 2 for k in ks])
                Oe = np.array([(np.array([A[f"{key}_s{k}"][str(lb)] for lb in labels]) -
                                np.array([A[f"{key}_c{k}"][str(lb)] for lb in labels])) / 2 for k in ks])
                T0 = np.array([sum(1 - 2 * int(strs["s" + k][q]) for q in pos) for k in ks], dtype=float)
                conserv = max(conserv, float(np.abs(Oe.sum(axis=1) - T0).max()))
                const = np.array([-(sum(int(strs["s" + k][q]) for q in win) - sum(int(strs["c" + k][q]) for q in win)) / 2
                                  for k in ks])
                w_ex = -Oe[:, wi].sum(axis=1) / 2 + const
                w_raw = -Od[:, wi].sum(axis=1) / 2 + const
                sek = lambda x: float(np.std(x, ddof=1) / np.sqrt(K))
                mine = dict(W_device=float(w_raw.mean()), W_excess=float((w_raw - w_ex).mean()),
                            W_excess_2se=2 * sek(w_raw - w_ex))
                if form == "F" or t >= 3:
                    rho_a = Od.sum(axis=1) / T0
                    w_a = -(Od[:, wi].sum(axis=1) / rho_a) / 2 + const
                    d_a = w_a - w_ex
                    mine.update(W_a=float(w_a.mean()), d_a=float(d_a.mean()), d_a_2se=2 * sek(d_a))
                    words[("a", "AGREES" if abs(d_a.mean()) < 2 * sek(d_a) else "DIFFERS")] = \
                        words.get(("a", "AGREES" if abs(d_a.mean()) < 2 * sek(d_a) else "DIFFERS"), 0) + 1
                mt = f"{key}_s00_mirror"
                if mt in z and z[mt].mean() > 0:
                    m = float(z[mt].mean())
                    rb = math.sqrt(m)
                    w_b = -(Od[:, wi].sum(axis=1) / rb) / 2 + const
                    d_b = w_b - w_ex
                    g = float(np.mean(Od[:, wi].sum(axis=1)) / (4 * m ** 1.5))
                    se_b = math.sqrt(sek(d_b) ** 2 + (g * zse[mt]) ** 2)
                    mine.update(rho_b=rb, W_b=float(w_b.mean()), d_b=float(d_b.mean()), d_b_2se=2 * se_b)
                    wb = "AGREES" if abs(d_b.mean()) < 2 * se_b else "DIFFERS"
                    words[("b", wb)] = words.get(("b", wb), 0) + 1
                tc = sc["cells"][key]
                for q, v in mine.items():
                    worst = dmax(worst, 0.0 if (v != v and tc[q] != tc[q]) else abs(v - tc[q]))
                if t >= 3:
                    use = [i for i in wi if np.sum(Oe[:, i] ** 2) >= UNIFORM_FLOOR * K]
                    var = np.array([[(1 - z[f"{key}_{s}{k}"] ** 2) / shots for s in "sc"] for k in ks])
                    r, se = [], []
                    for i in use:
                        den = float(np.sum(Oe[:, i] ** 2))
                        r.append(float(np.sum(Od[:, i] * Oe[:, i]) / den))
                        se.append(math.sqrt(float(np.sum(Oe[:, i] ** 2 * (var[:, 0, i] + var[:, 1, i]) / 4))) / den)
                    r, se = np.array(r), np.array(se)
                    if len(use) >= 2:
                        wt = 1 / se ** 2
                        pool = float(np.sum(wt * r) / wt.sum())
                        chi = float(np.sum(((r - pool) / se) ** 2))
                        pv = chi2_sf(chi, len(use) - 1)
                        u = sc["uniform"][key]
                        worst = dmax(worst, abs(pool - u["r_pool"]), abs(chi - u["chi2"]), abs(pv - u["p"]))
                        wu = "UNIFORM" if pv >= 0.05 else "NOT UNIFORM"
                        words[("u", wu)] = words.get(("u", wu), 0) + 1
    print(f"{os.path.basename(run)}: largest difference from the tool's scores.json {worst:.1e}; "
          f"answers' total odd part against T0 worst {conserv:.1e}; words {dict(sorted(words.items()))}")


if __name__ == "__main__":
    main()
