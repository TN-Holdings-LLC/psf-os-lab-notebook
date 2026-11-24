#!/usr/bin/env python3
"""Two desk re-readings of results/ohm-window-night-2026-11-23, beside only (workplace Claude, 2026-11-24; the home
VS's suggestions of 2026-11-23, asked for by the owner: "作って"). No verdict, no declaration, no correction of any
recorded value; no noise model is fitted to the device and no calibration number is read.

Inputs: the record's raw counts, sent circuits (measure instructions give the qubit -> clbit map), build.json (the
chain's physical qubits by position) and the sealed answers. Only qiskit and numpy (no psf-os, no notebook scorer).

1. Per-qubit twins. On the window's qubits (positions 20 .. 20 + 2t - 2), the light-cone circuit (L) and the full
   40-qubit circuit (F) have the same exact <Z> and run on the same physical qubits. Per string and window qubit:
   the device <Z> of F minus that of L, against shot noise (chi-square), and the pooled difference of the squared
   errors (F - L) with its SE, over 14 strings x |window| points instead of 14 window sums.

2. Where the bias goes: W or S. Per pair (string s, complement c) and window qubit, the odd part O = (Z_s - Z_c) / 2 and
   the even part E = (Z_s + Z_c) / 2 of the device <Z>, against the same parts of the exact <Z>. W depends on the odd
   parts only, S on the even parts only (exact identities: W = -sum O / 2 + const, S = -sum E + const). Beside:
   - the odd part's shrink, r = sum O_dev O_ex / sum O_ex^2 (a summary of the data, not a noise model), and the share
     of the odd part's squared error left after scaling by r (how much of W's error is a uniform shrink);
   - the even part's mean shift, mean(E_dev - E_ex) (a one-sided shift: decay towards |0> raises Z on both strings);
   - the W excess (device - exact, per pair) split into the shrink term and the rest.
   SEs by bootstrap over the 7 pairs (2000 draws, seed 20261124).

  python ow_beside.py RESULTS/ohm-window-night-2026-11-23 OUT.json
"""
import gzip
import io
import json
import sys

import numpy as np
from qiskit import qpy

R, OUT = sys.argv[1], sys.argv[2]
ARMS, TS, FORMS = ("A0", "A1", "A2"), (1, 3), ("L", "F")
PAIRS = 7
SHOTS = None
RNG = np.random.default_rng(20261124)
NBOOT = 2000


def window(t):
    return list(range(20, 20 + 2 * t - 1))


man = json.load(open(f"{R}/ow/job/manifest.json"))
raw = json.load(open(f"{R}/ow/job/raw_counts.json"))
circs = qpy.load(io.BytesIO(gzip.open(f"{R}/ow/job/circuits.qpy.gz").read()))
cell_name = {c["cell"]: c["name"] for c in man["cells"]}
pub_name = [cell_name[p["cell"]] for p in man["pubs"]]
pi = {n: i for i, n in enumerate(pub_name) if not n.startswith("ksent")}
rows = {r["pub"]: r["counts"] for r in raw["rows"]}
chain = json.load(open(f"{R}/ow/build.json"))["chain"]["labels"]
A = json.load(open(f"{R}/answers/ohm_window_answers.json"))
pos_of = A["meta"]["positions"]
assert A["meta"]["windows"] == {"t1": window(1), "t3": window(3)}


def measured(qc):
    return {qc.find_bit(i.qubits[0]).index: qc.find_bit(i.clbits[0]).index for i in qc.data
            if i.operation.name == "measure"}


def z_and_n(counts, clbits):
    tot = sum(counts.values())
    z = np.zeros(len(clbits))
    for key, c in counts.items():
        s = key.replace(" ", "")
        z += c * np.array([1 - 2 * int(s[-1 - k]) for k in clbits])
    return z / tot, tot


# device and exact <Z> on the window, per (arm, t, form, string)
dev, ex, shots = {}, {}, set()
for a in ARMS:
    for t in TS:
        w = window(t)
        for f in FORMS:
            for k in range(PAIRS):
                for p in "sc":
                    lab = f"{a}_t{t}_{f}_{p}{k:02d}"
                    qc = circs[pi[f"p2d_{lab}"]]
                    m = measured(qc)
                    z, n = z_and_n(rows[pi[f"p2d_{lab}"]], [m[chain[q]] for q in w])
                    shots.add(n)
                    dev[lab] = z
                    apos = pos_of[f"t{t}_{f}"]
                    ex[lab] = np.array([A["z"][lab][apos.index(q)] for q in w])
SHOTS = shots.pop() if len(shots) == 1 else None
out = dict(note="beside only: no verdict, no declaration, no correction; a summary of the record, no noise model",
           record="results/ohm-window-night-2026-11-23", shots=SHOTS, pairs=PAIRS, bootstrap=dict(n=NBOOT,
                                                                                                  seed=20261124))

# the window's exact <Z> is the same in L and F (the declared construction); checked here
worst = max(float(np.abs(ex[f"{a}_t{t}_L_{p}{k:02d}"] - ex[f"{a}_t{t}_F_{p}{k:02d}"]).max())
            for a in ARMS for t in TS for k in range(PAIRS) for p in "sc")
out["window_exact_L_vs_F_worst"] = worst

# ---------------------------------------------------------------------------------------------- 1. per-qubit twins
tw = {}
for a in ARMS:
    for t in TS:
        dz, var, de2 = [], [], []
        for k in range(PAIRS):
            for p in "sc":
                L, F = f"{a}_t{t}_L_{p}{k:02d}", f"{a}_t{t}_F_{p}{k:02d}"
                zl, zf, e = dev[L], dev[F], ex[L]
                dz += list(zf - zl)
                var += list((1 - zl ** 2) / SHOTS + (1 - zf ** 2) / SHOTS)
                de2 += list((zf - e) ** 2 - (zl - e) ** 2)
        dz, var, de2 = np.array(dz), np.array(var), np.array(de2)
        chi2 = float(np.sum(dz ** 2 / var))
        n = len(dz)
        e2 = np.array([ex[f"{a}_t{t}_L_{p}{k:02d}"] ** 2 for k in range(PAIRS) for p in "sc"]).ravel()
        tw[f"{a}_t{t}"] = dict(points=n, exact_Z2_mean=round(float(e2.mean()), 4),
                               dZ_mean=round(float(dz.mean()), 5),
                               dZ_mean_SE_shots=round(float(np.sqrt(var.sum()) / n), 5),
                               chi2_shots=round(chi2, 1), dof=n,
                               chi2_over_dof=round(chi2 / n, 3),
                               sqerr_F_minus_L=round(float(de2.mean()), 5),
                               sqerr_F_minus_L_SE=round(float(de2.std(ddof=1) / np.sqrt(n)), 5))
out["per_qubit_twins"] = tw

# ---------------------------------------------------------------------------------------------- 2. W or S
def parts(lab_s, lab_c, src):
    zs, zc = src[lab_s], src[lab_c]
    return (zs - zc) / 2, (zs + zc) / 2


ws = {}
for a in ARMS:
    for t in TS:
        for f in FORMS:
            Od, Oe, Ed, Ee = [], [], [], []
            for k in range(PAIRS):
                s, c = f"{a}_t{t}_{f}_s{k:02d}", f"{a}_t{t}_{f}_c{k:02d}"
                od, ed = parts(s, c, dev)
                oe, ee = parts(s, c, ex)
                Od.append(od); Oe.append(oe); Ed.append(ed); Ee.append(ee)
            Od, Oe, Ed, Ee = (np.array(x) for x in (Od, Oe, Ed, Ee))       # pairs x window

            def summ(idx):
                od, oe, ed, ee = Od[idx], Oe[idx], Ed[idx], Ee[idx]
                r = float(np.sum(od * oe) / np.sum(oe ** 2))
                err_odd = float(np.mean((od - oe) ** 2))
                left = float(np.mean((od - r * oe) ** 2))
                # W per pair = -sum_window O / 2 + const: its excess and the shrink part of it
                w_exc = float(np.mean(-(od - oe).sum(axis=1) / 2))
                w_shrink = float(np.mean(-((r - 1) * oe).sum(axis=1) / 2))
                e_shift = float(np.mean(ed - ee))
                s_exc = float(np.mean(-(ed - ee).sum(axis=1)))
                return dict(r_odd=r, odd_err_left_after_r=left / err_odd if err_odd > 0 else 0.0,
                            W_excess=w_exc, W_excess_from_shrink=w_shrink, even_shift=e_shift, S_excess=s_exc)

            full = summ(np.arange(PAIRS))
            boots, dropped = [], 0
            for _ in range(NBOOT):
                idx = RNG.integers(0, PAIRS, PAIRS)
                if np.sum(Oe[idx] ** 2) < 1e-3 * np.sum(Oe ** 2):     # a draw with (almost) no odd signal
                    dropped += 1
                    continue
                boots.append(summ(idx))
            ws[f"{a}_t{t}_{f}"] = {k: dict(value=round(v, 4),
                                           SE=round(float(np.std([b[k] for b in boots], ddof=1)), 4))
                                   for k, v in full.items()}
            ws[f"{a}_t{t}_{f}"]["bootstrap_dropped"] = dropped
            ws[f"{a}_t{t}_{f}"]["odd_exact_rms"] = round(float(np.sqrt(np.mean(Oe ** 2))), 4)
out["odd_even"] = ws

# 3. rulers for the shrink inside the job (beside): the mirror (the circuit and its inverse, ideal all |0>) on A1 s00,
# whose mean <Z> is a shrink over twice the layers; and the conserved total <Z> (fSim keeps the number of 1s: the
# exact total equals the initial one), measured on every F circuit
mir = {}
for t in TS:
    for f in FORMS:
        nm = f"p2d_A1_t{t}_{f}_s00_mirror"
        if nm not in pi:
            continue
        qc = circs[pi[nm]]
        m = measured(qc)
        z, _ = z_and_n(rows[pi[nm]], list(m.values()))
        mir[f"A1_t{t}_{f}"] = dict(mirror_mean_Z=round(float(z.mean()), 4), sqrt_mirror=round(float(np.sqrt(z.mean())), 4),
                                   r_odd=ws[f"A1_t{t}_{f}"]["r_odd"]["value"])
out["mirror_ruler"] = mir
tot = {}
strs = A["meta"]["strings"]
for a in ARMS:
    for t in TS:
        rr = []
        for k in range(PAIRS):
            for p in "sc":
                lab = f"{a}_t{t}_F_{p}{k:02d}"
                qc = circs[pi[f"p2d_{lab}"]]
                m = measured(qc)
                z, _ = z_and_n(rows[pi[f"p2d_{lab}"]], [m[chain[q]] for q in range(40)])
                z0 = sum(1 - 2 * int(b) for b in strs[f"{p}{k:02d}"])
                rr.append((float(z.sum()), z0))
        # the odd combination per pair, (T_s - T_c) / (T0_s - T0_c): a one-sided shift cancels in it
        odd = [(rr[2 * i][0] - rr[2 * i + 1][0]) / (rr[2 * i][1] - rr[2 * i + 1][1]) for i in range(PAIRS)]
        tot[f"{a}_t{t}_F"] = dict(initial_totals=sorted({abs(z0) for _, z0 in rr}),
                                  device_over_initial=[round(zt / z0, 3) for zt, z0 in rr],
                                  odd_ratio_per_pair=[round(x, 3) for x in odd],
                                  odd_ratio_mean=round(float(np.mean(odd)), 3),
                                  odd_ratio_SE=round(float(np.std(odd, ddof=1) / np.sqrt(PAIRS)), 3),
                                  r_odd_window=ws[f"{a}_t{t}_F"]["r_odd"]["value"])
out["total_ruler"] = tot

# the shrink by twin, side by side (L 16 or 4 qubits measured, F 40; the same layers)
out["r_odd_L_vs_F"] = {f"{a}_t{t}": dict(L=ws[f"{a}_t{t}_L"]["r_odd"], F=ws[f"{a}_t{t}_F"]["r_odd"])
                       for a in ARMS for t in TS}
json.dump(out, open(OUT, "w"), indent=1)

print(f"window exact L vs F, worst {worst:.1e}; shots {SHOTS}")
print("1. per-qubit twins (F - L on the window's qubits)")
for k, v in tw.items():
    print(f"  {k}: {v['points']} points; dZ mean {v['dZ_mean']:+.4f} (shot SE {v['dZ_mean_SE_shots']:.4f}); "
          f"chi2/dof against shot noise {v['chi2_over_dof']:.2f}; squared error F - L {v['sqerr_F_minus_L']:+.5f} "
          f"(SE {v['sqerr_F_minus_L_SE']:.5f})")
print("   (scale: mean exact Z^2 on the window, per cell:", {k: v["exact_Z2_mean"] for k, v in tw.items()}, ")")
print("2. odd part (W) and even part (S) of the window's <Z>, per cell (bootstrap SE over 7 pairs)")
for k, v in ws.items():
    g = lambda x: f"{v[x]['value']:+.4f} ({v[x]['SE']:.4f})"
    print(f"  {k}: r_odd {v['r_odd']['value']:.3f} ({v['r_odd']['SE']:.3f}); odd error left after r "
          f"{v['odd_err_left_after_r']['value']:.2f}; W excess {g('W_excess')}, of it from the shrink "
          f"{g('W_excess_from_shrink')}; even shift {g('even_shift')}; S excess {g('S_excess')}")
print("3. rulers inside the job")
for k, v in mir.items():
    print(f"  mirror {k}: mean Z {v['mirror_mean_Z']:.3f}, its square root {v['sqrt_mirror']:.3f}; r_odd {v['r_odd']:.3f}")
for k, v in tot.items():
    print(f"  total Z {k}: initial |total| {v['initial_totals']}; odd ratio per pair {v['odd_ratio_per_pair']}, "
          f"mean {v['odd_ratio_mean']:.3f} (SE {v['odd_ratio_SE']:.3f}); r_odd on the window {v['r_odd_window']:.3f}")
