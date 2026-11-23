"""How long the Ohm circuits leave a qubit idle while it is probably |1> (home VS, 2026-11-23; desk, no device).

The circuits are the ones sent (results/ohm-2026-11-12, results/ohm-kingston-2026-11-12: runs/p2d_<tag>.qpy.gz, the
compiled circuit on the device's physical qubits). Nothing under results/ is written.

Lengths of time: the night's device record holds no instruction durations, so the durations are those of
qiskit-ibm-runtime's fake backends (FakeFez for fez, FakeKingston for kingston) read by psf_os.device.fetch_fake
(psf-os 0.3.3, durations only). THEY ARE THE FAKE BACKENDS' VALUES, NOT THE DEVICES' RECORDS. No error number is read.

Schedule: the device's own schedule is not in the record. Two are computed: ASAP (every instruction as early as its
qubits allow; each qubit is measured as soon as it is done) and ALAP (every instruction as late as possible; all
measurements at the end). RZ is virtual (no duration, no physical action) and does not end an idle span.

Idle span: on one qubit, a stretch of time in which no physical instruction (x, sx, cz) acts on it, from time 0 to
the start of its measurement. A unitary on other qubits does not change this qubit's reduced state, so its P(|1>) is
constant over the span and equals the value just before the next instruction on it.

P(|1>): noise-free, from a matrix product state along the 40-qubit chain (the circuits act only between chain
neighbours, checked), with the circuit's own gates (rz, sx, x, cz). Truncation: singular values below CUTOFF times the
largest dropped, bond at most CHI; the final per-qubit <Z> is compared with the sealed exact answers (answers/) as the
accuracy check of every circuit.

usage: PYTHONPATH=<psf-os 0.3.3> python notes/ohm_idle_2026-11-23/ohm_idle.py OUT.json [--chi 256] [--cutoff 1e-6]
       [--jobs 10] [--only TAG_PREFIX]
"""
import argparse
import gzip
import io
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

NB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
NIGHTS = {"fez": ("results/ohm-2026-11-12", "ibm_fez", "FakeFez", "answers/ohm_ibm_fez_ans.json"),
          "kingston": ("results/ohm-kingston-2026-11-12", "ibm_kingston", "FakeKingston",
                       "answers/ohm_ibm_kingston_ans.json")}
PHYSICAL = ("x", "sx", "cz")
OVER = 0.5 + 1e-6      # "probably |1>": P(|1>) above one half; many spans sit at exactly 0.5 (fSim(pi/4))
SX = 0.5 * np.array([[1 + 1j, 1 - 1j], [1 - 1j, 1 + 1j]])
X = np.array([[0, 1], [1, 0]], dtype=complex)


def rz(t):
    return np.diag([np.exp(-0.5j * t), np.exp(0.5j * t)])


def load_circuit(dev, tag):
    """(ops, positions, record): ops [(name, (chain positions), param)] in circuit order without measurements."""
    from qiskit import qpy
    base, d, _, _ = NIGHTS[dev]
    runs = os.path.join(NB, base, d, "runs")
    rec = json.load(open(os.path.join(runs, f"p2d_{tag}.json")))
    c = qpy.load(io.BytesIO(gzip.open(os.path.join(runs, f"p2d_{tag}.qpy.gz")).read()))[0]
    chain = json.load(open(os.path.join(NB, base, d, "build.json")))["chain"]["labels"]
    mapping = rec["mapping"] if isinstance(rec["mapping"], dict) else eval(rec["mapping"])  # noqa: S307 (own record)
    phys = [int(mapping[str(lab)]) for lab in chain]
    pos = {p: k for k, p in enumerate(phys)}
    ops, measured = [], []
    for ins in c.data:
        name = ins.operation.name
        qs = tuple(pos[c.find_bit(q).index] for q in ins.qubits)
        if name == "measure":
            measured.append(qs[0])
            continue
        if name == "barrier":
            raise SystemExit(f"{tag}: a barrier in the sent circuit (not expected)")
        if name not in ("rz",) + PHYSICAL:
            raise SystemExit(f"{tag}: instruction {name} not handled")
        if name == "cz" and abs(qs[0] - qs[1]) != 1:
            raise SystemExit(f"{tag}: cz between chain positions {qs} (not neighbours)")
        ops.append((name, qs, float(ins.operation.params[0]) if name == "rz" else None))
    if sorted(measured) != list(range(len(chain))):
        raise SystemExit(f"{tag}: the measured qubits are not the 40 chain qubits")
    return ops, phys, chain, rec


def durations(fake_timing, phys, ops):
    """Duration (dt) of every op from the fake backend's table, by physical qubits; rz 0."""
    D = fake_timing["durations"]
    out = []
    for name, qs, _ in ops:
        if name == "rz":
            out.append(0)
        elif name == "cz":
            out.append(int(D["cz"][f"{phys[qs[0]]},{phys[qs[1]]}"]))
        else:
            out.append(int(D[name][str(phys[qs[0]])]))
    meas = [int(D["measure"][str(p)]) for p in phys]
    return out, meas


def schedule(ops, dur, n, how):
    """Start time (dt) of every physical op and the start of every qubit's measurement."""
    start = [None] * len(ops)
    if how == "asap":
        ready = [0] * n
        for i, (name, qs, _) in enumerate(ops):
            if name == "rz":
                continue
            s = max(ready[q] for q in qs)
            start[i] = s
            for q in qs:
                ready[q] = s + dur[i]
        return start, ready[:]
    # alap: lay out backwards from the end, then shift so the earliest op starts at 0
    back = [0] * n
    for i in range(len(ops) - 1, -1, -1):
        name, qs, _ = ops[i]
        if name == "rz":
            continue
        e = max(back[q] for q in qs)           # time from the end to this op's end
        start[i] = -(e + dur[i])
        for q in qs:
            back[q] = e + dur[i]
    t0 = min(s for s in start if s is not None)
    start = [None if s is None else s - t0 for s in start]
    T = -t0
    return start, [T] * n


def idle_spans(ops, dur, start, mstart, n):
    """Per qubit: [(begin, end, index of the op that ends the span or None for the measurement)], length > 0."""
    last = [0] * n
    spans = [[] for _ in range(n)]
    for i, (name, qs, _) in enumerate(ops):
        if name == "rz":
            continue
        for q in qs:
            if start[i] > last[q]:
                spans[q].append((last[q], start[i], i))
            last[q] = start[i] + dur[i]
    for q in range(n):
        if mstart[q] > last[q]:
            spans[q].append((last[q], mstart[q], None))
    return spans


class MPS:
    """Mixed-canonical MPS on a chain of qubits, nearest-neighbour gates, P(|1>) read at the orthogonality centre."""

    def __init__(self, n, chi, cutoff):
        self.A = [np.zeros((1, 2, 1), dtype=complex) for _ in range(n)]
        for a in self.A:
            a[0, 0, 0] = 1
        self.c, self.chi, self.cutoff, self.dropped, self.maxbond = 0, chi, cutoff, 0.0, 1

    def _right(self):
        k, a = self.c, self.A[self.c]
        q, r = np.linalg.qr(a.reshape(-1, a.shape[2]))
        self.A[k] = q.reshape(a.shape[0], 2, -1)
        self.A[k + 1] = np.tensordot(r, self.A[k + 1], axes=(1, 0))
        self.c += 1

    def _left(self):
        k, a = self.c, self.A[self.c]
        q, r = np.linalg.qr(a.reshape(a.shape[0], -1).T)
        self.A[k] = q.T.reshape(-1, 2, a.shape[2])
        self.A[k - 1] = np.tensordot(self.A[k - 1], r.T, axes=(2, 0))
        self.c -= 1

    def centre(self, k):
        while self.c < k:
            self._right()
        while self.c > k:
            self._left()

    def one(self, k, g):
        self.A[k] = np.einsum("ij,ajb->aib", g, self.A[k])

    def cz(self, k):
        """CZ on (k, k + 1); the centre ends on k + 1."""
        self.centre(k)
        a, b = self.A[k], self.A[k + 1]
        th = np.tensordot(a, b, axes=(2, 0))   # (l, 2, 2, r)
        th[:, 1, 1, :] *= -1
        l, r = th.shape[0], th.shape[3]
        u, s, vh = np.linalg.svd(th.reshape(l * 2, 2 * r), full_matrices=False)
        keep = max(1, min(self.chi, int(np.sum(s > self.cutoff * s[0]))))
        self.dropped += float(np.sum(s[keep:] ** 2) / np.sum(s ** 2))
        s = s[:keep] / np.linalg.norm(s[:keep])
        self.A[k] = u[:, :keep].reshape(l, 2, keep)
        self.A[k + 1] = (s[:, None] * vh[:keep]).reshape(keep, 2, r)
        self.c = k + 1
        self.maxbond = max(self.maxbond, keep)

    def p1(self, k):
        self.centre(k)
        a = self.A[k]
        n0, n1 = np.sum(np.abs(a[:, 0, :]) ** 2), np.sum(np.abs(a[:, 1, :]) ** 2)
        return float(n1 / (n0 + n1))


def gate(name, param):
    return rz(param) if name == "rz" else (SX if name == "sx" else X)


def simulate(ops, n, queries, chi, cutoff):
    """P(|1>) of qubit q just before op i for every (q, i) in queries (i None: at the end), and the final <Z>."""
    want = {}
    for q, i in queries:
        want.setdefault(i, []).append(q)
    m, got = MPS(n, chi, cutoff), {}
    for i, (name, qs, p) in enumerate(ops):
        for q in want.get(i, ()):
            got[(q, i)] = m.p1(q)
        if name == "cz":
            m.cz(min(qs))
        else:
            m.one(qs[0], gate(name, p))
    fin = [m.p1(q) for q in range(n)]
    for q in want.get(None, ()):
        got[(q, None)] = fin[q]
    return got, [1 - 2 * x for x in fin], dict(max_bond=m.maxbond, dropped_weight=m.dropped)


def study(dev, tag, timing, chi, cutoff, answers, keep_segments=False):
    ops, phys, chain, rec = load_circuit(dev, tag)
    n = len(chain)
    dur, meas = durations(timing, phys, ops)
    sched = {h: schedule(ops, dur, n, h) for h in ("asap", "alap")}
    spans = {h: idle_spans(ops, dur, *sched[h], n) for h in sched}
    queries = {(q, sp[2]) for h in spans for q in range(n) for sp in spans[h][q]}
    t0 = time.time()
    p1, zfin, mps = simulate(ops, n, queries, chi, cutoff)
    exact = [answers[tag][str(lab)] for lab in chain]
    out = dict(tag=tag, device=dev, cz=sum(o[0] == "cz" for o in ops), one_qubit=sum(o[0] in ("x", "sx") for o in ops),
               mps=dict(chi=chi, cutoff=cutoff, seconds=round(time.time() - t0, 2),
                        final_z_vs_exact_max=float(np.max(np.abs(np.array(zfin) - np.array(exact)))), **mps))
    x_dt = int(timing["durations"]["x"][str(phys[0])])
    for h in sched:
        start, mstart = sched[h]
        total = int(sum(mstart))                       # qubit-time from 0 to each qubit's measurement
        idle = hi = w = gain = 0
        segs = []
        for q in range(n):
            for b, e, i in spans[h][q]:
                p = p1[(q, i)]
                L = e - b
                idle += L
                w += p * L
                if p > OVER:
                    hi += L
                    gain += (2 * p - 1) * L
                segs.append((q, b, e, i, round(p, 6)))
        out[h] = dict(length_dt=int(max(mstart)), qubit_time_dt=total, idle_dt=int(idle), idle_p1_over_half_dt=int(hi),
                      idle_p1_weighted_dt=float(w), park_gain_dt=float(gain),
                      spans=len(segs), spans_p1_over_half=sum(s[4] > OVER for s in segs),
                      parkable=sum(s[4] > OVER and s[2] - s[1] >= 2 * x_dt + 2 for s in segs),
                      parkable_dt=int(sum(s[2] - s[1] for s in segs if s[4] > OVER and s[2] - s[1] >= 2 * x_dt + 2)))
        if keep_segments:
            out[h]["segments"] = segs
    return out


def work(args):
    dev, tag, chi, cutoff = args
    from psf_os import device as Dv
    timing = Dv.fetch_fake(NIGHTS[dev][2]).timing
    answers = json.load(open(os.path.join(NB, NIGHTS[dev][0], NIGHTS[dev][3])))["z"]
    return study(dev, tag, timing, chi, cutoff, answers)


def tags(only):
    out = []
    for dev, (base, d, _, _) in NIGHTS.items():
        b = json.load(open(os.path.join(NB, base, d, "build.json")))
        for arm in ("A0", "A1", "A2"):
            for t in b["cycles"]:
                for name in b["strings"]:
                    tg = f"{arm}_t{t}_{name}"
                    if not only or tg.startswith(only) or f"{dev}:{tg}".startswith(only):
                        out.append((dev, tg))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--chi", type=int, default=256)
    ap.add_argument("--cutoff", type=float, default=1e-6)
    ap.add_argument("--jobs", type=int, default=10)
    ap.add_argument("--only", default=None)
    a = ap.parse_args()
    if os.path.exists(a.out):
        raise SystemExit(f"STOP: {a.out} exists")
    sys.path.insert(0, NB)
    todo = tags(a.only)
    # heavy circuits first so the pool ends evenly
    todo.sort(key=lambda x: (-int(x[1].split("_")[1][1:]), x[1][:2] == "A0"))
    t0 = time.time()
    res = []
    with Pool(a.jobs) as pool:
        for k, r in enumerate(pool.imap_unordered(work, [(d, t, a.chi, a.cutoff) for d, t in todo])):
            res.append(r)
            if k % 20 == 0 or k == len(todo) - 1:
                print(f"{k + 1}/{len(todo)} {time.time() - t0:.0f} s  last {r['device']} {r['tag']}: bond "
                      f"{r['mps']['max_bond']}, final Z vs exact {r['mps']['final_z_vs_exact_max']:.1e}", flush=True)
    res.sort(key=lambda r: (r["device"], r["tag"]))
    json.dump(dict(note="durations: fake backends' values (FakeFez, FakeKingston), not the devices' records; "
                        "noise-free P(|1>) by MPS; schedules ASAP and ALAP (the device's own schedule is not recorded)",
                   chi=a.chi, cutoff=a.cutoff, seconds=round(time.time() - t0, 1), circuits=res),
              open(a.out, "w"))
    print("wrote", a.out, f"{time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
