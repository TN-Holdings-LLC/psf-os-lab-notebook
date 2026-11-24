#!/usr/bin/env python3
# Beside values after the record (never judged): per light-cone position of the Ohm ruler night (2026-11-24),
# the factor r, the square root of the same qubit's mirror <Z>, and the CZ layers each qubit waits.
# qiskit + numpy only; the qubit-to-clbit map is read from the measure instructions of the circuits as sent.
# Author: The Architect <love.os.architect@proton.me>
import gzip
import io
import json
import math
import sys

import numpy as np
from qiskit import qpy

R, OUT = sys.argv[1], sys.argv[2]
ARMS, K, SHOTS = ("A0", "A1", "A2"), 7, 1000


def window(t):
    return list(range(20, 20 + 2 * t - 1))


def cone(t):
    return {1: list(range(18, 22)), 3: list(range(14, 30)), 4: list(range(12, 34))}[t]


A = json.load(open(f"{R}/answers/ohm_ruler_answers.json"))
B = json.load(open(f"{R}/or/build.json"))
man = json.load(open(f"{R}/or/job/manifest.json"))
raw = json.load(open(f"{R}/or/job/raw_counts.json"))
circs = qpy.load(io.BytesIO(gzip.open(f"{R}/or/job/circuits.qpy.gz").read()))
cell_name = {c["cell"]: c["name"] for c in man["cells"]}
pub_name = [cell_name[p["cell"]] + (f"#{p['point']}" if cell_name[p["cell"]].startswith("ksent") else "")
            for p in man["pubs"]]
pi = {n: i for i, n in enumerate(pub_name)}
rows = {r["pub"]: r["counts"] for r in raw["rows"]}


def meas_map(qc):
    return {qc.find_bit(i.qubits[0]).index: qc.find_bit(i.clbits[0]).index for i in qc.data
            if i.operation.name == "measure"}


def z_counts(counts, clbits):
    tot = sum(counts.values())
    z = np.zeros(len(clbits))
    for key, c in counts.items():
        s = key.replace(" ", "")
        z += c * np.array([1 - 2 * int(s[-1 - k]) for k in clbits])
    return z / tot


def cz_layers(qc, reverse=False):
    """ASAP layering of the CZ gates only; returns (depth, {qubit: last CZ layer}). With reverse=True the circuit is
    read backwards, which gives the ALAP picture: depth - last = the layers a qubit waits before its first CZ."""
    ins = [i for i in qc.data if i.operation.name == "cz"]
    if reverse:
        ins = ins[::-1]
    last = {}
    for i in ins:
        a, b = (qc.find_bit(q).index for q in i.qubits)
        lay = max(last.get(a, 0), last.get(b, 0)) + 1
        last[a] = last[b] = lay
    return max(last.values()), last


def phys_of(tag):
    it = B["items"][tag]
    return dict(zip(it["positions"], it["physical"]))


res = {}
for t in (1, 3, 4):
    pos = cone(t)
    for a in ARMS:
        ph = phys_of(f"{a}_t{t}_L_s00")
        Od, Oe, Vd = [], [], []
        for k in range(K):
            zz = {}
            for p_ in "sc":
                nm = f"p2d_{a}_t{t}_L_{p_}{k:02d}"
                qc = circs[pi[nm]]
                m = meas_map(qc)
                tg = nm[4:]
                assert phys_of(tg) == ph
                zd = z_counts(rows[pi[nm]], [m[ph[p]] for p in pos])
                apos = A["meta"]["positions"][f"t{t}_L"]
                ze = np.array([A["z"][tg][apos.index(p)] for p in pos])
                zz[p_] = (zd, ze)
            Od.append((zz["s"][0] - zz["c"][0]) / 2)
            Oe.append((zz["s"][1] - zz["c"][1]) / 2)
            Vd.append(((1 - zz["s"][0] ** 2) + (1 - zz["c"][0] ** 2)) / SHOTS / 4)
        Od, Oe, Vd = map(np.array, (Od, Oe, Vd))
        # the cell's mirror, per qubit
        mq = circs[pi[f"p2d_{a}_t{t}_L_s00_mirror"]]
        mm = meas_map(mq)
        zm = z_counts(rows[pi[f"p2d_{a}_t{t}_L_s00_mirror"]], [mm[ph[p]] for p in pos])
        # CZ layers waited, from the compiled circuit of s00 (all strings share the gates but the X preparation)
        qc0 = circs[pi[f"p2d_{a}_t{t}_L_s00"]]
        D, last = cz_layers(qc0)
        Dr, lastr = cz_layers(qc0, reverse=True)
        per = []
        for i, p in enumerate(pos):
            den = float(np.sum(Oe[:, i] ** 2))
            r = float(np.sum(Od[:, i] * Oe[:, i]) / den) if den > 0 else float("nan")
            se = math.sqrt(float(np.sum(Oe[:, i] ** 2 * Vd[:, i]))) / den if den > 0 else float("nan")
            per.append(dict(pos=p, phys=ph[p], window=p in window(t), sumOe2_over_K=den / K, used=den >= 0.05 * K,
                            r=r, se=se, mirror=float(zm[i]), sqrt_mirror=math.sqrt(zm[i]) if zm[i] > 0 else float("nan"),
                            wait_end_asap=D - last.get(ph[p], 0), wait_start_alap=Dr - lastr.get(ph[p], 0)))

        def pool(sel):
            sel = [x for x in sel if x["used"]]
            if not sel:
                return None
            w = np.array([1 / x["se"] ** 2 for x in sel])
            r = np.array([x["r"] for x in sel])
            return dict(n=len(sel), r=float(np.sum(w * r) / np.sum(w)), se=float(1 / math.sqrt(np.sum(w))))

        win = pool([x for x in per if x["window"]])
        outs = pool([x for x in per if not x["window"]])
        cmp_ = None
        if win and outs:
            d = outs["r"] - win["r"]
            cmp_ = dict(outside_minus_window=d, two_se=2 * math.hypot(win["se"], outs["se"]))
        used = [x for x in per if x["used"]]
        corr = None
        if len(used) >= 3 and len({x["wait_end_asap"] for x in used}) > 1:
            corr = float(np.corrcoef([x["r"] for x in used], [x["wait_end_asap"] for x in used])[0, 1])
        res[f"{a}_t{t}"] = dict(cz_depth=D, positions=per, window_pool=win, outside_pool=outs, compare=cmp_,
                                corr_r_vs_wait_end=corr)

json.dump(res, open(OUT, "w"), indent=1)
for k, v in res.items():
    print(f"== {k}  (CZ layers {v['cz_depth']})")
    print(" pos phys win  sumOe2/K   r      SE     sqrt(mirror)  wait_end(ASAP) wait_start(ALAP)")
    for x in v["positions"]:
        print(f" {x['pos']:3d} {x['phys']:4d} {'W' if x['window'] else ' '}   {x['sumOe2_over_K']:6.3f}{' ' if x['used'] else '*'}"
              f"  {x['r']:6.3f} {x['se']:6.3f}   {x['sqrt_mirror']:6.3f}      {x['wait_end_asap']:3d}            {x['wait_start_alap']:3d}")
    print(" window pool", v["window_pool"], " outside pool", v["outside_pool"], " compare", v["compare"],
          " corr(r, wait_end)", v["corr_r_vs_wait_end"])
