"""The time a feed-forward decision costs, read by clock qubits on a ruler of delays (workplace Claude, 2026-11-18;
owner "3", the time specification; with the CZ items of home's instruction 18d). Declaration text:
prereg/drafts-2026-11-18/timing_night_2026-11-18_READY.md (declared when moved and pushed at home). No device error
number is read: the ruler is built from our own delays in the same job.

Two "clock" qubits in |+>, with an echo (X) halfway, lose phase while they wait; the longer the wait, the more often
they read 1 after the final H (ideal 0). In each job a ruler R(d) of known delays on an actor (d in dt, per half)
gives each clock's loss against time; every other item's loss read on it gives an equivalent wait. The items differ
only in what the actors do while the clocks wait, per half:
  C(n)   n x (measure the actor, then a conditional X on it that never fires: the actor is |0>)   IBM's fast-path shape
  F(n)   the same with the conditional firing (the actor prepared |1>, the X resets it)               fast-path shape
  D(n)   C(n) on two actors at once                                                                   fast-path shape
  K(n)   n x (measure the actor, then a conditional CZ between the actor and its partner; never fires)  not fast path
  DK(n)  K(n) on two actor / partner pairs at once                                                    not fast path
The off arm of C, K (and of D, DK) is the measurements alone. Per step (weighted least squares of the equivalent wait
against the number of steps): s_M (off arms of C), s_C, s_F, s_D, s_K, s_DK; read:
  decision latency, fast path        s_C - s_M      verdict DECISION LATENCY RESOLVED (>= 2 SE) / NOT RESOLVED
  two actors, fast path              s_D / s_C      DECISIONS WAIT FOR EACH OTHER / IN PARALLEL / NOT SHOWN
  two actors, with a CZ              s_DK / s_K     the same words
  beside: s_K - s_M (the CZ path's latency), s_K - s_C, s_F - s_C, s_M itself.
  WAIT FOR EACH OTHER when ratio - 1 >= 2 SE; IN PARALLEL when |ratio - 1| < 2 SE and ratio - 2 <= -2 SE; otherwise
  NOT SHOWN (SE of a ratio by the delta method, the two slopes taken as independent: conservative, they share a ruler).

Two jobs (each under 60 s by the model; each with its own ruler, so every ratio is read within one job):
  part A: R, C, F, D        part B: R, K, DK
Layout (rule C, one chain of 9 sites): clocks on 0 and 8; actor 1 on 2 with its partner on 3; actor 2 on 5 with its
partner on 6; sites 1, 4, 7 idle, so no clock is next to an actor or a partner. Barriers fence the halves.

dt: the device's dt (dt.json, read at home: a time, not a quality number) sets the ruler's delays in dt so that it
spans 0 .. 32 us per half on any dt (rounded to multiples of 16 dt), and converts dt to us; the same file is given to
build and score (score refuses a different one). Without it 4 ns is assumed and the output says so. Ratios do not
depend on dt.

  python gpu/timing_night.py build DEVDIR OUT --part A|B [--dt-file dt.json] [--dry-clifford-sentinel]
  python gpu/timing_night.py check OUT
  python gpu/timing_night.py score OUT_A OUT_B [--dt-file dt.json]   the verdicts and predictions (both jobs)
  python gpu/timing_night.py planted [--scenario cz-waits|fast-waits]  the estimator on synthetic counts
  python gpu/timing_night.py planted-run OUT [--scenario ...]   dry only: a built job under planted timing
"""
import argparse
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "notes", "packing_2026-11-17"))

DT_NS_ASSUMED = 4.0
RULER_US = (0, 4.032, 8, 16, 24, 32)            # per half; in dt, rounded to multiples of 16 (1008 ... 8000 at 4 ns)


def ruler_dt(dt_ns):
    """The ruler's delays in dt for the device's dt (so the ruler spans the same microseconds on any dt)."""
    return tuple(16 * round(us * 1000.0 / dt_ns / 16) for us in RULER_US)
NS_C = (2, 4, 8)                                 # every item's wait stays inside the ruler's 64 us
NS_F = (4, 8)
NS_D = (2, 4)
NS_K = (2, 4, 8)
NS_DK = (2, 4)
N_SITES = 9
CLOCKS = (0, 8)
PAIRS = ((2, 3), (5, 6))                         # (actor, partner)
SHOTS = 4000
PARTS = {"A": ("R", "C", "F", "D"), "B": ("R", "K", "DK")}


def _half(qc, kind, n, d, bits, pairs):
    """One half's actor work; bits: an iterator of fresh clbit indices."""
    if kind == "R":
        if d:
            qc.delay(d, PAIRS[0][0], unit="dt")
        return
    for _ in range(n):
        for a, p in pairs:
            b = next(bits)
            if kind == "F":
                qc.x(a)
            qc.measure(a, b)
            with qc.if_test((qc.clbits[b], 1)):
                if kind == "K":
                    qc.cz(a, p)               # never fires (the actor is |0>): the block's shape is what matters
                else:
                    qc.x(a)                   # never fires in C, D; fires and resets in F


def item(kind, n=0, d=0):
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
    pairs = list(PAIRS) if kind in ("D", "DK") else [PAIRS[0]]
    k = {"D": "C", "DK": "K"}.get(kind, kind)
    nmeas = 0 if kind == "R" else 2 * n * len(pairs)
    qc = QuantumCircuit(QuantumRegister(N_SITES, "q"), ClassicalRegister(nmeas + len(CLOCKS), "c"))
    bits = iter(range(nmeas))
    for c in CLOCKS:
        qc.h(c)
    qc.barrier()
    _half(qc, k, n, d, bits, pairs)
    qc.barrier()
    for c in CLOCKS:
        qc.x(c)                               # the echo
    qc.barrier()
    _half(qc, k, n, d, bits, pairs)
    qc.barrier()
    for i, c in enumerate(CLOCKS):
        qc.h(c)
        qc.measure(c, nmeas + i)              # ideal 0 (X leaves |+> as it is); the loss is reading 1
    return qc, dict(success={nmeas + i: 0 for i in range(len(CLOCKS))}, bound=None,
                    form="blocks" if k == "K" else "pauli")


def items(part, dt_ns=DT_NS_ASSUMED):
    kinds = PARTS[part]
    out = [(f"R{d}", *item("R", d=d)) for d in ruler_dt(dt_ns)]
    if "C" in kinds:
        out += [(f"C{n}", *item("C", n=n)) for n in NS_C]
    if "F" in kinds:
        out += [(f"F{n}", *item("F", n=n)) for n in NS_F]
    if "D" in kinds:
        out += [(f"D{n}", *item("D", n=n)) for n in NS_D]
    if "K" in kinds:
        out += [(f"K{n}", *item("K", n=n)) for n in NS_K]
    if "DK" in kinds:
        out += [(f"DK{n}", *item("DK", n=n)) for n in NS_DK]
    return out


def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None   # dry runs only, never a device
    dt_ns, note = read_dt(a.dt_file)
    rep = FF.build(Device.load(a.devdir), items(a.part, dt_ns), a.out, shots=SHOTS, max_seconds=60, sentinel_spec=spec)
    json.dump(dict(part=a.part, dt_ns=dt_ns, dt_note=note, ruler_dt=list(ruler_dt(dt_ns))),
              open(os.path.join(a.out, "part.json"), "w"), indent=1)
    print(note)
    print(json.dumps({k: rep[k] for k in ("device", "circuits", "qpu_seconds_model", "shots") if k in rep}))
    print("chain", rep["items"]["R0"]["chain"])


def _tag(cell):
    return cell["name"][3:].replace("_floor", "").replace("_off", "")


def check(a):
    """Noiseless Aer of every arm: both clocks read 0 in every shot of ff and off; floors all zero. Shapes: every
    conditional of C, F, D takes IBM's fast-path shape and none of K, DK does (notes/packing_2026-11-17/fastpath.py)."""
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    from psf_os import feedforward as FF
    import fastpath as FP
    m = json.load(open(os.path.join(a.out, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(a.out, "job", "circuits.qpy"), "rb"))
    i, bad = 0, []
    for cell in m["cells"]:
        for _ in range(cell["points"]):
            c = cs[i]
            i += 1
            if cell["role"] == "sentinel":
                continue
            cc = FF.compact(c)
            n = cc.num_clbits
            cnt = AerSimulator().run(cc, shots=SHOTS, seed_simulator=20261118).result().get_counts()
            tot = sum(cnt.values())
            clock0 = sum(v for k, v in cnt.items() if all(FF._bits(k, n)[n - 1 - j] == 0
                                                          for j in range(len(CLOCKS)))) / tot
            allz = sum(v for k, v in cnt.items() if set(FF._bits(k, n)) == {0}) / tot
            ok = allz == 1.0 if cell["role"] == "floor" else clock0 == 1.0
            shape = ""
            if cell["role"] == "user":
                rows = FP.classify(cc)
                tag = _tag(cell)
                nf = sum(FP.fast(r) for _, r in rows)
                want_fast = tag[0] in "CFD" and not tag.startswith("DK")
                if rows:
                    sok = (nf == len(rows)) if want_fast else (nf == 0)
                    shape = f"  conditionals {len(rows)}, fast-path shape {nf} ({'ok' if sok else 'WRONG SHAPE'})"
                    ok = ok and sok
            print(f"{cell['name']:12s} {cell['role']:6s} clocks read 0 {clock0:.3f}  all zero {allz:.3f}{shape} "
                  f"{'ok' if ok else 'FAIL'}")
            bad += [] if ok else [cell["name"]]
    print("PASS" if not bad else f"FAIL {bad}")
    return not bad


# ------------------------------------------------------------------------------------------------ the estimator

def _wls(xs, ys, ses):
    w = [1 / max(s, 1e-12) ** 2 for s in ses]
    W = sum(w)
    xb = sum(wi * x for wi, x in zip(w, xs)) / W
    yb = sum(wi * y for wi, y in zip(w, ys)) / W
    sxx = sum(wi * (x - xb) ** 2 for wi, x in zip(w, xs))
    b = sum(wi * (x - xb) * (y - yb) for wi, x, y in zip(w, xs, ys)) / sxx
    a_ = yb - b * xb
    var_b = 1 / sxx
    var_a = 1 / W + xb ** 2 / sxx
    cov = -xb / sxx
    chi2 = sum(wi * (y - a_ - b * x) ** 2 for wi, x, y in zip(w, xs, ys))
    return dict(a=a_, b=b, var_a=var_a, var_b=var_b, cov=cov, chi2=chi2, dof=len(xs) - 2)


def _loss_se(p, n):
    return math.sqrt(max(p * (1 - p), 0.25 / n) / n)       # floor at a quarter shot: no zero SE


def _pava(ts, ps, ns):
    """Pool adjacent violators: the ruler made non-decreasing in time (its losses pooled where they fall)."""
    blocks = [[t, p, n, [t]] for t, p, n in zip(ts, ps, ns)]
    i = 0
    while i < len(blocks) - 1:
        if blocks[i][1] > blocks[i + 1][1]:
            a_, b_ = blocks[i], blocks[i + 1]
            n = a_[2] + b_[2]
            blocks[i] = [(a_[0] * a_[2] + b_[0] * b_[2]) / n, (a_[1] * a_[2] + b_[1] * b_[2]) / n, n, a_[3] + b_[3]]
            del blocks[i + 1]
            i = max(i - 1, 0)
        else:
            i += 1
    return [(b[0], b[1], b[2]) for b in blocks]


def _tau(p, p0):
    """The loss on a scale closer to linear in time for a decaying echo: -ln(1 - 2 (p - p0)), p0 the ruler's start
    (the read-out offset). Monotone in p, so reading the ruler on it assumes no decay shape; it only makes the pieces
    between ruler points straighter."""
    x = 1 - 2 * (p - p0)
    return -math.log(max(x, 1e-6))


def _clock_teq(ruler_pts, p, n):
    """Equivalent wait (us) and its SE for loss p on one clock's ruler [(t, p, shots)], read piecewise linearly on the
    tau scale between the two ruler points around it (the end pieces extended outside; flagged)."""
    p0 = ruler_pts[0][1]
    R = [(t, _tau(q, p0), q, m) for t, q, m in ruler_pts]
    y = _tau(p, p0)
    if y <= R[0][1]:
        i = 0
    elif y >= R[-1][1]:
        i = len(R) - 2
    else:
        i = max(j for j in range(len(R) - 1) if R[j][1] <= y)
    (t0, y0, q0, m0), (t1, y1, q1, m1) = R[i], R[i + 1]
    if y1 <= y0:
        return float("nan"), float("inf"), True
    t = t0 + (y - y0) * (t1 - t0) / (y1 - y0)
    dtau = lambda q: 2 / max(1 - 2 * (q - p0), 1e-6)            # d tau / d p
    gy = (t1 - t0) / (y1 - y0)
    g0 = (t1 - t0) * (y - y1) / (y1 - y0) ** 2
    g1 = -(t1 - t0) * (y - y0) / (y1 - y0) ** 2
    var = (gy * dtau(p) * _loss_se(p, n)) ** 2 + (g0 * dtau(q0) * _loss_se(q0, m0)) ** 2 + \
          (g1 * dtau(q1) * _loss_se(q1, m1)) ** 2
    return t, math.sqrt(var), bool(y < R[0][1] or y > R[-1][1])


def estimate(losses, dt_ns, kinds, ruler=None):
    """losses: {clock index: {tag: (loss share, shots)}} of ONE job, ff tags as items() and off arms as tag + "_off".
    Per clock the ruler (made non-decreasing) is read piecewise linearly on the tau scale; the clocks' equivalent waits
    for an item are averaged with inverse-variance weights. Returns per-step times (us) with SEs."""
    rulers = {}
    for ci, L in losses.items():
        pts = sorted((2 * d * dt_ns / 1000.0, *L[f"R{d}"]) for d in (ruler or ruler_dt(dt_ns)))
        mono = _pava([t for t, _, _ in pts], [p for _, p, _ in pts], [n for _, _, n in pts])
        if len(mono) >= 2 and mono[-1][1] > mono[0][1]:
            rulers[ci] = dict(points=pts, monotone=mono)
    if not rulers:
        return dict(error="every ruler is flat: no time can be read")

    def t_eq(tag):
        vals = [_clock_teq(rulers[ci]["monotone"], *losses[ci][tag]) for ci in rulers]
        vals = [v for v in vals if math.isfinite(v[0]) and math.isfinite(v[1]) and v[1] > 0]
        w = [1 / v[1] ** 2 for v in vals]
        return sum(wi * v[0] for wi, v in zip(w, vals)) / sum(w), math.sqrt(1 / sum(w)), any(v[2] for v in vals)

    def slope(tags, steps):
        pts_ = [(s_, *t_eq(tg)) for tg, s_ in zip(tags, steps)]
        f = _wls([q[0] for q in pts_], [q[1] for q in pts_], [q[2] for q in pts_])
        return dict(us_per_step=f["b"], se=math.sqrt(f["var_b"]), intercept_us=f["a"],
                    points=[dict(steps=q[0], us=q[1], se=q[2], outside_ruler=q[3]) for q in pts_])

    out = dict(rulers={str(c): r for c, r in rulers.items()}, dt_ns=dt_ns)
    if "C" in kinds:
        out["s_M"] = slope([f"C{n}_off" for n in NS_C], [2 * n for n in NS_C])
        out["s_C"] = slope([f"C{n}" for n in NS_C], [2 * n for n in NS_C])
    if "F" in kinds:
        out["s_F"] = slope([f"F{n}" for n in NS_F], [2 * n for n in NS_F])
    if "D" in kinds:
        out["s_D"] = slope([f"D{n}" for n in NS_D], [2 * n for n in NS_D])
    if "K" in kinds:
        out["s_MK"] = slope([f"K{n}_off" for n in NS_K], [2 * n for n in NS_K])
        out["s_K"] = slope([f"K{n}" for n in NS_K], [2 * n for n in NS_K])
    if "DK" in kinds:
        out["s_DK"] = slope([f"DK{n}" for n in NS_DK], [2 * n for n in NS_DK])
    return out


def difference(a, b):
    return dict(us=a["us_per_step"] - b["us_per_step"], se=math.hypot(a["se"], b["se"]))


def ratio(a, b):
    r = a["us_per_step"] / b["us_per_step"]
    se = abs(r) * math.hypot(a["se"] / a["us_per_step"], b["se"] / b["us_per_step"])
    return dict(ratio=r, se=se)


def latency_verdict(d):
    return "DECISION LATENCY RESOLVED" if d["us"] >= 2 * d["se"] else "NOT RESOLVED"


def pair_verdict(r):
    if r["ratio"] - 1 >= 2 * r["se"]:
        return "DECISIONS WAIT FOR EACH OTHER"
    if abs(r["ratio"] - 1) < 2 * r["se"] and r["ratio"] - 2 <= -2 * r["se"]:
        return "IN PARALLEL"
    return "NOT SHOWN"


def judge(eA, eB):
    """The declared verdicts and predictions from the two jobs' estimates."""
    res = {}
    if "error" not in eA:
        lat = difference(eA["s_C"], eA["s_M"])
        rD = ratio(eA["s_D"], eA["s_C"])
        res.update(fast_latency=dict(lat, verdict=latency_verdict(lat)), fast_pair=dict(rD, verdict=pair_verdict(rD)),
                   beside_fired_minus_unfired=difference(eA["s_F"], eA["s_C"]),
                   beside_measurement_us=eA["s_M"]["us_per_step"])
    if "error" not in eB:
        rK = ratio(eB["s_DK"], eB["s_K"])
        res.update(cz_pair=dict(rK, verdict=pair_verdict(rK)),
                   beside_cz_latency=difference(eB["s_K"], eB["s_MK"]))
    if "error" not in eA and "error" not in eB:
        res["beside_cz_minus_fast_us"] = difference(eB["s_K"], eA["s_C"])   # two jobs: beside only
    res["predictions"] = {
        "T-1 fast-path decision latency (s_C - s_M) RESOLVED":
            ("held" if res["fast_latency"]["verdict"] == "DECISION LATENCY RESOLVED" else "failed")
            if "fast_latency" in res else "failed (no time could be read)",
        "T-2 two fast-path actors (s_D / s_C) IN PARALLEL":
            ("held" if res["fast_pair"]["verdict"] == "IN PARALLEL" else "failed")
            if "fast_pair" in res else "failed (no time could be read)",
        "T-3 two actors with a CZ (s_DK / s_K) WAIT FOR EACH OTHER":
            ("held" if res["cz_pair"]["verdict"] == "DECISIONS WAIT FOR EACH OTHER" else "failed")
            if "cz_pair" in res else "failed (no time could be read)",
    }
    return res


def show(eA, eB, res, dt_note):
    print(dt_note)
    for nm, e in (("A", eA), ("B", eB)):
        if "error" in e:
            print(f"job {nm}: {e['error']}")
            continue
        for c, r in e["rulers"].items():
            print(f"job {nm} ruler, clock {c} (us, loss): " + ", ".join(f"{t:.1f} {p:.3f}" for t, p, _ in r["points"]))
        for k in ("s_M", "s_C", "s_F", "s_D", "s_MK", "s_K", "s_DK"):
            if k in e:
                print(f"  {k:5s} {e[k]['us_per_step']:7.3f} us per step (SE {e[k]['se']:.3f})")
    if "fast_latency" in res:
        x = res["fast_latency"]
        print(f"fast-path decision latency s_C - s_M {x['us']:+.3f} us (2 SE {2 * x['se']:.3f}) -> {x['verdict']}")
        x = res["fast_pair"]
        print(f"two fast-path actors s_D / s_C {x['ratio']:.2f} (2 SE {2 * x['se']:.2f}) -> {x['verdict']}")
    if "cz_pair" in res:
        x = res["cz_pair"]
        print(f"two actors with a CZ s_DK / s_K {x['ratio']:.2f} (2 SE {2 * x['se']:.2f}) -> {x['verdict']}")
        x = res["beside_cz_latency"]
        print(f"beside: CZ-path latency s_K - s_M {x['us']:+.3f} us (2 SE {2 * x['se']:.3f})")
    if "beside_cz_minus_fast_us" in res:
        x = res["beside_cz_minus_fast_us"]
        print(f"beside (two jobs): s_K - s_C {x['us']:+.3f} us (2 SE {2 * x['se']:.3f})")
    print("predictions:", res["predictions"])


def losses_of(out):
    from psf_os import feedforward as FF
    import ctrl_night as CN
    g = CN._counts(out)
    losses = {i: {} for i in range(len(CLOCKS))}
    floor = {}
    for (tag, arm), (n, cnt) in g.items():
        tot = sum(cnt.values())
        for i in range(len(CLOCKS)):
            b = n - len(CLOCKS) + i
            share1 = sum(v for k, v in cnt.items() if FF._bits(k, n)[b] == 1) / tot     # loss: the clock reads 1
            if arm == "floor":
                floor[f"{tag} clock {i}"] = share1
            else:
                losses[i][tag + ("" if arm == "ff" else "_off")] = (share1, tot)
    return losses, floor


def read_dt(path):
    if path:
        d = json.load(open(path))
        return float(d["dt"]) * 1e9, f"dt {float(d['dt']) * 1e9:.4g} ns from {os.path.basename(path)} ({d.get('device')})"
    return DT_NS_ASSUMED, f"dt ASSUMED {DT_NS_ASSUMED} ns (no dt file given): the us values scale with it, the ratios do not"


def score(a):
    dt_ns, note = read_dt(a.dt_file)
    est = {}
    for out in (a.out_a, a.out_b):
        pj = json.load(open(os.path.join(out, "part.json")))
        part = pj["part"]
        if abs(pj["dt_ns"] - dt_ns) > 1e-9:
            raise SystemExit(f"{out} was built with dt {pj['dt_ns']} ns, scored with {dt_ns} ns: give the same dt file")
        losses, floor = losses_of(out)
        e = estimate(losses, dt_ns, PARTS[part], pj["ruler_dt"])
        e.update(losses={str(i): v for i, v in losses.items()}, clock_floor_reads_1=floor)
        est[part] = e
    res = judge(est["A"], est["B"])
    show(est["A"], est["B"], res, note)
    res.update(dt_note=note, estimates=est)
    for out in (a.out_a, a.out_b):
        json.dump(res, open(os.path.join(out, "timing_scores.json"), "w"), indent=1)
    return res


# ------------------------------------------------------------------------------------------------ planted checks

SCENARIOS = {   # planted lengths in us (illustrative, never fitted): measurement, latency fast / CZ path, fired extra,
                # whether two fast-path actors / two CZ actors wait for each other
    "cz-waits": dict(MEAS=2.6, LAT=0.9, LATK=1.6, FIRE=0.3, D_SERIAL=False, DK_SERIAL=True),
    "fast-waits": dict(MEAS=2.6, LAT=0.9, LATK=1.6, FIRE=0.3, D_SERIAL=True, DK_SERIAL=False),
}


def planted_time(tag, arm, P, dt_ns):
    """The elapsed time of one half (us) of an item under the planted lengths."""
    if arm == "floor":
        return 0.0
    if tag.startswith("R"):
        return int(tag[1:]) * dt_ns / 1000.0
    kind = tag.rstrip("0123456789")
    n = int(tag[len(kind):])
    if arm == "off":
        per = P["MEAS"]
        two = kind in ("D", "DK")
        return n * per * (2 if two and (P["D_SERIAL"] if kind == "D" else P["DK_SERIAL"]) else 1)
    per = P["MEAS"] + (P["LATK"] if kind in ("K", "DK") else P["LAT"]) + (P["FIRE"] if kind == "F" else 0.0)
    if kind == "D":
        return n * per * (2 if P["D_SERIAL"] else 1)
    if kind == "DK":
        return n * per * (2 if P["DK_SERIAL"] else 1)
    return n * per


def planted(a):
    """The estimator on synthetic counts (no circuit): each clock's loss 0.5 (1 - exp(-t / T)) + 0.01 with T 100 and
    160 us; six seeds per scenario. It should give the planted numbers and the scenario's verdicts back."""
    P = SCENARIOS[a.scenario]
    Ts = (100.0, 160.0)
    for seed in range(6):
        rng = random.Random(20261118 + seed)

        def draw(t, T):
            p = 0.5 * (1 - math.exp(-t / T)) + 0.01
            return sum(rng.random() < p for _ in range(SHOTS)) / SHOTS, SHOTS
        est = {}
        for part in ("A", "B"):
            L = {i: {} for i in range(len(Ts))}
            for i, T in enumerate(Ts):
                for tag, _, _ in items(part, DT_NS_ASSUMED):
                    L[i][tag] = draw(2 * planted_time(tag, "user", P, DT_NS_ASSUMED), T)
                    L[i][tag + "_off"] = draw(2 * planted_time(tag, "off", P, DT_NS_ASSUMED), T)
            est[part] = estimate(L, DT_NS_ASSUMED, PARTS[part])
        r = judge(est["A"], est["B"])
        print(f"{a.scenario} seed {seed}: s_M {est['A']['s_M']['us_per_step']:.2f} (planted {P['MEAS']}); fast latency "
              f"{r['fast_latency']['us']:+.2f} ({P['LAT']}) {r['fast_latency']['verdict']}; D/C "
              f"{r['fast_pair']['ratio']:.2f} {r['fast_pair']['verdict']}; DK/K {r['cz_pair']['ratio']:.2f} "
              f"{r['cz_pair']['verdict']}; CZ latency {r['beside_cz_latency']['us']:+.2f} ({P['LATK']})")


def planted_run(a):
    """Dry runs only: simulate a built job with PLANTED timing (illustrative, never fitted): per half the clocks
    dephase by exp(-t / T) (T 100 us) for the half's planted elapsed time; writes raw_counts.json and submission.json
    as run_local does. Then `score` should read the planted lengths and verdicts back from the real circuits."""
    from qiskit import QuantumCircuit, qpy
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import phase_damping_error
    from psf_os import feedforward as FF
    from psf_os.ibm import _stamp
    from psf_os.sim import to_clifford_gates
    P, T = SCENARIOS[a.scenario], 100.0
    dt_ns = json.load(open(os.path.join(a.out, "part.json")))["dt_ns"]
    job = os.path.join(a.out, "job")
    man = json.load(open(os.path.join(job, "manifest.json")))
    b = json.load(open(os.path.join(a.out, "build.json")))
    circs = qpy.load(open(os.path.join(job, "circuits.qpy"), "rb"))
    rows = []
    for k, c in enumerate(circs):
        cell = man["cells"][man["pubs"][k]["cell"]]
        cc = FF.compact(c)
        seed = 20261118 + 10000 * k
        if cell["role"] == "sentinel":
            res = AerSimulator(method="stabilizer").run(to_clifford_gates(cc), shots=SHOTS, seed_simulator=seed).result()
            rows.append(dict(pub=k, counts={key.replace(" ", ""): v for key, v in res.get_counts(0).items()}))
            continue
        tag = _tag(cell)
        t = planted_time(tag, cell["role"] if cell["role"] != "user" else "user", P, dt_ns)
        act = sorted({q for _, qs in FF.walk(c) for q in qs})
        chain = b["items"][tag]["chain"]
        clocks = [act.index(chain[p]) for p in CLOCKS if chain[p] in act]
        err = phase_damping_error(1 - math.exp(-2 * t / T)).to_instruction() if t > 0 else None
        w = QuantumCircuit(*cc.qregs, *cc.cregs)
        nbar = 0
        for ins in cc.data:
            w.append(ins.operation, ins.qubits, ins.clbits)
            if ins.operation.name == "barrier":
                nbar += 1
                if err is not None and nbar in (2, 4):     # the end of each half: that half's dephasing
                    for q in clocks:
                        w.append(err, [w.qubits[q]])
        res = AerSimulator(method="density_matrix").run(w, shots=SHOTS, seed_simulator=seed).result()
        rows.append(dict(pub=k, counts={key.replace(" ", ""): v for key, v in res.get_counts(0).items()}))
    t_ = _stamp()
    json.dump(dict(job_id="local-planted-timing", submitted=t_, local=True, backend=man["fetch"]["backend"],
                   simulator=f"aer, PLANTED timing {a.scenario} (dry runs only)"),
              open(os.path.join(job, "submission.json"), "w"))
    json.dump(dict(fetched=t_, job_id="local-planted-timing", status="DONE (local, planted timing)", rows=rows),
              open(os.path.join(job, "raw_counts.json"), "w"))
    print(f"planted {a.scenario}: {P}, T {T} us, dt {dt_ns} ns")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    b.add_argument("--part", choices=sorted(PARTS), required=True)
    b.add_argument("--dt-file", help="dt.json (the device's dt, read at home); without it 4 ns is assumed")
    b.add_argument("--dry-clifford-sentinel", action="store_true")
    sub.add_parser("check").add_argument("out")
    s = sub.add_parser("score")
    s.add_argument("out_a")
    s.add_argument("out_b")
    s.add_argument("--dt-file")
    p = sub.add_parser("planted")
    p.add_argument("--scenario", choices=sorted(SCENARIOS), default="cz-waits")
    pr = sub.add_parser("planted-run")
    pr.add_argument("out")
    pr.add_argument("--scenario", choices=sorted(SCENARIOS), default="cz-waits")
    a = ap.parse_args()
    r = {"build": build, "check": check, "score": score, "planted": planted, "planted-run": planted_run}[a.cmd](a)
    sys.exit(0 if r is not False else 1)
