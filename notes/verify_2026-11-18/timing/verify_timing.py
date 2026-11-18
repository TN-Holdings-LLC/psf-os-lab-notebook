"""Independent re-scoring of the decision-timing test of 2026-11-18 (results/timing-night-2026-11-18), home VS Claude,
2026-11-18. Only qiskit (to read the recorded circuits) and numpy; home Claude's tools (gpu/timing_night.py score,
psf_os.feedforward.cards, ctrl_night) are NOT used. Definitions re-implemented from prereg/timing_night_2026-11-18.md:
per job, each clock's ruler made non-decreasing (pool adjacent violators), read piecewise linearly on
tau = -ln(1 - 2 (loss - loss0)); the two clocks' equivalent waits averaged with inverse-variance weights; per step,
weighted least squares against the number of steps (2 n steps for n per half).

Everything is read from the record: cell names from job/manifest.json (pubs[k].cell -> cells[cell].name), counts from
job/raw_counts.json (key bit 0 rightmost), the clock bits and the ruler delays from runs/*.qpy (the clocks are the
qubits measured in the ruler circuits R*, which measure nothing else; the ruler's wait is the sum of the delays in the
R circuit, in dt, times dt from dt.json).

Robustness (a reading check, nothing fitted to the device): the same slopes and verdicts with the ruler read in three
other ways: (b) one straight line of tau against time per clock (weighted), (c) a saturating exponential
loss = p0 + A (1 - exp(-t / T)) per clock (least squares, T on a grid), (d) piecewise linear on the raw loss scale.
usage: python verify_timing.py NB OUTDIR"""
import json
import math
import os
import sys

import numpy as np
from qiskit import qpy

NB, OUT = sys.argv[1], sys.argv[2]
TD = os.path.join(NB, "results", "timing-night-2026-11-18")
DT_NS = json.load(open(os.path.join(TD, "dt.json")))["dt"] * 1e9
LOG = []


def say(s=""):
    print(s, flush=True)
    LOG.append(s)


def load_job(folder):
    man = json.load(open(os.path.join(folder, "job", "manifest.json")))
    raw = json.load(open(os.path.join(folder, "job", "raw_counts.json")))
    names = {k: man["cells"][p["cell"]]["name"] for k, p in enumerate(man["pubs"])}
    counts = {names[r["pub"]]: r["counts"] for r in raw["rows"] if r["pub"] in names}
    circ = {}
    for nm in counts:
        f = os.path.join(folder, "runs", nm + ".qpy")
        if nm.startswith("ff_") and os.path.exists(f):
            (c,) = qpy.load(open(f, "rb"))
            circ[nm] = c
    return counts, circ


def measures(c):
    """[(qubit, clbit)] of top-level measurements, in order."""
    return [(c.find_bit(i.qubits[0]).index, c.find_bit(i.clbits[0]).index) for i in c.data if i.operation.name == "measure"]


def delay_dt(c):
    tot = 0
    for i in c.data:
        if i.operation.name == "delay":
            assert i.operation.unit == "dt"
            tot = max(tot, 0) + 0
    per_q = {}
    for i in c.data:
        if i.operation.name == "delay":
            q = c.find_bit(i.qubits[0]).index
            per_q[q] = per_q.get(q, 0) + int(i.operation.duration)
    return max(per_q.values()) if per_q else 0


def share1(cnt, bit):
    tot = sum(cnt.values())
    return sum(v for k, v in cnt.items() if k.replace(" ", "")[-1 - bit] == "1") / tot, tot


def lse(p, n):
    return math.sqrt(max(p * (1 - p), 0.25 / n) / n)


def pava(pts):
    b = [[t, p, n] for t, p, n in pts]
    i = 0
    while i < len(b) - 1:
        if b[i][1] > b[i + 1][1]:
            x, y = b[i], b[i + 1]
            n = x[2] + y[2]
            b[i] = [(x[0] * x[2] + y[0] * y[2]) / n, (x[1] * x[2] + y[1] * y[2]) / n, n]
            del b[i + 1]
            i = max(i - 1, 0)
        else:
            i += 1
    return [tuple(v) for v in b]


def tau(p, p0):
    return -math.log(max(1 - 2 * (p - p0), 1e-6))


# ---- four ways of reading one clock's ruler: functions (loss, shots) -> (t_eq, se)

def reader_tau_pw(pts, scale="tau"):
    mono = pava(pts)
    p0 = mono[0][1]
    f = (lambda q: tau(q, p0)) if scale == "tau" else (lambda q: q)
    df = (lambda q: 2 / max(1 - 2 * (q - p0), 1e-6)) if scale == "tau" else (lambda q: 1.0)
    R = [(t, f(q), q, m) for t, q, m in mono]

    def read(p, n):
        y = f(p)
        if y <= R[0][1]:
            i = 0
        elif y >= R[-1][1]:
            i = len(R) - 2
        else:
            i = max(j for j in range(len(R) - 1) if R[j][1] <= y)
        (t0, y0, q0, m0), (t1, y1, q1, m1) = R[i], R[i + 1]
        if y1 <= y0:
            return float("nan"), float("inf")
        t = t0 + (y - y0) * (t1 - t0) / (y1 - y0)
        gy = (t1 - t0) / (y1 - y0)
        g0 = (t1 - t0) * (y - y1) / (y1 - y0) ** 2
        g1 = -(t1 - t0) * (y - y0) / (y1 - y0) ** 2
        var = (gy * df(p) * lse(p, n)) ** 2 + (g0 * df(q0) * lse(q0, m0)) ** 2 + (g1 * df(q1) * lse(q1, m1)) ** 2
        return t, math.sqrt(var)
    return read


def reader_tau_line(pts):
    """tau = a + b t fitted (weighted) to every ruler point; t_eq = (tau(p) - a) / b; SE from p and the fit."""
    p0 = pts[0][1]
    ts = np.array([t for t, _, _ in pts])
    ys = np.array([tau(q, p0) for _, q, _ in pts])
    ss = np.array([2 / max(1 - 2 * (q - p0), 1e-6) * lse(q, m) for _, q, m in pts])
    ss[0] = max(ss[0], 1e-4)
    w = 1 / ss ** 2
    X = np.vstack([np.ones_like(ts), ts]).T
    cov = np.linalg.inv(X.T @ (w[:, None] * X))
    a, b = cov @ X.T @ (w * ys)

    def read(p, n):
        y = tau(p, p0)
        t = (y - a) / b
        sy = 2 / max(1 - 2 * (p - p0), 1e-6) * lse(p, n)
        g = np.array([-1 / b, -(y - a) / b ** 2])
        var = (sy / b) ** 2 + g @ cov @ g
        return t, math.sqrt(var)
    return read


def reader_exp(pts):
    """loss = p0 + A (1 - exp(-t / T)), weighted least squares with T on a grid (A, p0 linear given T)."""
    ts = np.array([t for t, _, _ in pts])
    ps = np.array([q for _, q, _ in pts])
    w = np.array([1 / lse(q, m) ** 2 for _, q, m in pts])
    best = None
    for T in np.geomspace(5, 2000, 4000):
        X = np.vstack([np.ones_like(ts), 1 - np.exp(-ts / T)]).T
        cov = np.linalg.inv(X.T @ (w[:, None] * X))
        beta = cov @ X.T @ (w * ps)
        chi = float(np.sum(w * (ps - X @ beta) ** 2))
        if best is None or chi < best[0]:
            best = (chi, T, beta, cov)
    _, T, (p0, A), cov = best

    def read(p, n):
        x = 1 - (p - p0) / A
        if x <= 0:
            return float("nan"), float("inf")
        t = -T * math.log(x)
        dtdp = T / (A * x)
        dtdp0 = T / (A * x)
        dtdA = -T * (p - p0) / (A ** 2 * x)
        g = np.array([dtdp0, dtdA])
        var = (dtdp * lse(p, n)) ** 2 + g @ cov @ g          # T taken as fixed at its best value
        return t, math.sqrt(var)
    return read, T


def wls(xs, ys, ses):
    w = np.array([1 / max(s, 1e-12) ** 2 for s in ses])
    x, y = np.array(xs, float), np.array(ys, float)
    W = w.sum()
    xb, yb = (w * x).sum() / W, (w * y).sum() / W
    sxx = (w * (x - xb) ** 2).sum()
    b = (w * (x - xb) * (y - yb)).sum() / sxx
    return b, math.sqrt(1 / sxx)


NS = dict(C=(2, 4, 8), F=(4, 8), D=(2, 4), K=(2, 4, 8), DK=(2, 4))


def job_numbers(folder, label):
    counts, circ = load_job(folder)
    # the clocks: qubits measured in the ruler circuits
    rnames = sorted((n for n in counts if n.startswith("ff_R") and not n.endswith(("_off", "_floor"))),
                    key=lambda s: int(s[4:]))
    clockq = sorted({q for n in rnames for q, _ in measures(circ[n])})
    rec = json.load(open(os.path.join(folder, "runs", rnames[0] + ".json")))
    say(f"job {label}: clocks read from the ruler circuits: physical qubits {clockq}; record chain {rec['chain']} "
        f"(sites 0 and 8 = {rec['chain'][0]}, {rec['chain'][8]})")
    order = [rec["chain"][0], rec["chain"][8]]                 # clock 0 = site 0, clock 1 = site 8 (for comparison)
    assert sorted(order) == clockq
    loss = {0: {}, 1: {}}
    for nm, c in circ.items():
        if nm.endswith("_floor"):
            continue
        ms = measures(c)
        for ci, q in enumerate(order):
            bits = [b for qq, b in ms if qq == q]
            assert len(bits) == 1, (nm, q, bits)
            tag = nm[3:]
            loss[ci][tag] = share1(counts[nm], bits[0])
    ruler = {ci: sorted((2 * 0 + delay_dt(circ[n]) * DT_NS / 1000.0 * 1.0, *loss[ci][n[3:]]) for n in rnames)
             for ci in (0, 1)}
    # delay_dt is the delay on the actor summed over both halves (one delay per half): the ruler's wait
    return loss, ruler, rnames


def slopes(loss, ruler, readers, kinds):
    def teq(tag):
        vals = [readers[ci](*loss[ci][tag]) for ci in (0, 1)]
        vals = [v for v in vals if math.isfinite(v[0]) and math.isfinite(v[1]) and v[1] > 0]
        w = [1 / v[1] ** 2 for v in vals]
        return sum(wi * v[0] for wi, v in zip(w, vals)) / sum(w), math.sqrt(1 / sum(w))
    out = {}
    for name, kind, arm in kinds:
        ns = NS[kind]
        pts = [teq(f"{kind}{n}" + arm) for n in ns]
        b, se = wls([2 * n for n in ns], [p[0] for p in pts], [p[1] for p in pts])
        out[name] = (b, se)
    return out


def verdicts(sA, sB):
    lat = (sA["s_C"][0] - sA["s_M"][0], math.hypot(sA["s_C"][1], sA["s_M"][1]))
    def ratio(a, b):
        r = a[0] / b[0]
        return r, abs(r) * math.hypot(a[1] / a[0], b[1] / b[0])
    def pv(r, se):
        if r - 1 >= 2 * se:
            return "DECISIONS WAIT FOR EACH OTHER"
        if abs(r - 1) < 2 * se and r - 2 <= -2 * se:
            return "IN PARALLEL"
        return "NOT SHOWN"
    rD, rK = ratio(sA["s_D"], sA["s_C"]), ratio(sB["s_DK"], sB["s_K"])
    return dict(T1=dict(us=lat[0], two_se=2 * lat[1], verdict="DECISION LATENCY RESOLVED" if lat[0] >= 2 * lat[1]
                        else "NOT RESOLVED"),
                T2=dict(ratio=rD[0], two_se=2 * rD[1], verdict=pv(*rD)),
                T3=dict(ratio=rK[0], two_se=2 * rK[1], verdict=pv(*rK)))


lA, rA, _ = job_numbers(os.path.join(TD, "tmA"), "A")
lB, rB, _ = job_numbers(os.path.join(TD, "tmB"), "B")
for lab, r in (("A", rA), ("B", rB)):
    for ci in (0, 1):
        say(f"job {lab} ruler, clock {ci} (us, loss): " + ", ".join(f"{t:.1f} {p:.3f}" for t, p, _ in r[ci]))
KA = [("s_M", "C", "_off"), ("s_C", "C", ""), ("s_F", "F", ""), ("s_D", "D", "")]
KB = [("s_MK", "K", "_off"), ("s_K", "K", ""), ("s_DK", "DK", "")]
home = json.load(open(os.path.join(TD, "tmA", "timing_scores.json")))
hest = home["estimates"]
res = {}
forms = {}
for form in ("declared: piecewise linear on tau", "one straight line of tau", "saturating exponential",
             "piecewise linear on raw loss"):
    def mk(r):
        if form.startswith("declared"):
            return {ci: reader_tau_pw(r[ci]) for ci in (0, 1)}, None
        if form.startswith("one straight"):
            return {ci: reader_tau_line(r[ci]) for ci in (0, 1)}, None
        if form.startswith("saturating"):
            rr = {ci: reader_exp(r[ci]) for ci in (0, 1)}
            return {ci: rr[ci][0] for ci in rr}, {ci: rr[ci][1] for ci in rr}
        return {ci: reader_tau_pw(r[ci], scale="raw") for ci in (0, 1)}, None
    RA, TA = mk(rA)
    RB, TB = mk(rB)
    sA, sB = slopes(lA, rA, RA, KA), slopes(lB, rB, RB, KB)
    v = verdicts(sA, sB)
    forms[form] = dict(slopes={**{k: dict(us=b, se=s) for k, (b, s) in sA.items()},
                               **{k: dict(us=b, se=s) for k, (b, s) in sB.items()}}, verdicts=v,
                       exp_T_us=dict(A=TA, B=TB) if TA else None)
    say(f"\n== {form}" + (f" (decay times, us: job A {TA[0]:.0f} / {TA[1]:.0f}, job B {TB[0]:.0f} / {TB[1]:.0f})"
                         if TA else ""))
    say("  " + "   ".join(f"{k} {b:.3f} (SE {s:.3f})" for k, (b, s) in list(sA.items()) + list(sB.items())))
    say(f"  T-1 s_C - s_M {v['T1']['us']:+.3f} us (2 SE {v['T1']['two_se']:.3f}) -> {v['T1']['verdict']}")
    say(f"  T-2 s_D / s_C {v['T2']['ratio']:.3f} (2 SE {v['T2']['two_se']:.3f}) -> {v['T2']['verdict']}")
    say(f"  T-3 s_DK / s_K {v['T3']['ratio']:.3f} (2 SE {v['T3']['two_se']:.3f}) -> {v['T3']['verdict']}")
# against home's recorded numbers (the declared form)
d = forms["declared: piecewise linear on tau"]
say("\n== against home's tmA/timing_scores.json (declared form)")
worst = 0.0
for k in ("s_M", "s_C", "s_F", "s_D"):
    h = hest["A"][k]
    m = d["slopes"][k]
    worst = max(worst, abs(h["us_per_step"] - m["us"]), abs(h["se"] - m["se"]))
    say(f"  {k}: home {h['us_per_step']:.6f} (SE {h['se']:.6f})  mine {m['us']:.6f} (SE {m['se']:.6f})")
for k in ("s_MK", "s_K", "s_DK"):
    h = hest["B"][k]
    m = d["slopes"][k]
    worst = max(worst, abs(h["us_per_step"] - m["us"]), abs(h["se"] - m["se"]))
    say(f"  {k}: home {h['us_per_step']:.6f} (SE {h['se']:.6f})  mine {m['us']:.6f} (SE {m['se']:.6f})")
hv = dict(T1=home["fast_latency"], T2=home["fast_pair"], T3=home["cz_pair"])
for t in ("T1", "T2", "T3"):
    say(f"  {t}: home {hv[t]['verdict']}  mine {d['verdicts'][t]['verdict']}")
say(f"  largest difference in slopes and SEs: {worst:.2e} us")
same = all(f["verdicts"][t]["verdict"] == d["verdicts"][t]["verdict"] for f in forms.values() for t in ("T1", "T2", "T3"))
say(f"\nverdicts the same in all four reading forms: {same}")
json.dump(dict(forms=forms, worst_vs_home=worst, dt_ns=DT_NS), open(os.path.join(OUT, "verify_timing.json"), "w"),
          indent=1)
open(os.path.join(OUT, "verify_timing.txt"), "w").write("\n".join(LOG) + "\n")
