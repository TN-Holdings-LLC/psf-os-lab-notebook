"""Measuring the time a feed-forward decision costs, with a clock qubit and a ruler of delays (DRAFT tool, workplace
Claude, 2026-11-18; owner "3": the third missing piece, the time specification; prereg/drafts-2026-11-18/timing_DRAFT.md).
Not declared. No device error number is read: the ruler is built from our own delays in the same job.

The device's records keep no decision latency and no measurement length. A time can still be read from counts: a
"clock" qubit in |+>, with an echo (X) halfway, loses its phase while it waits; the longer the wait, the more often it
reads 1 after the final H (ideal 0). In one job:
  ruler  R(d): the clock waits through a delay of d on the actor qubit (both halves), d known (in dt);
  M(n)   the actor is measured n times per half (no conditional): the measurements' time (the off arm of C(n));
  C(n)   each measurement followed by a conditional X on the actor that never fires (the actor is |0>);
  F(n)   the same with the conditional firing every time (the actor prepared |1>, the conditional X resets it);
  C2(n)  two actors, each as C(n), side by side (do decisions on two qubits wait for each other?).
The clock's loss in R(d) against the elapsed time gives the ruler (read piecewise linearly between its points, made
non-decreasing first; no shape of the decay assumed); every other item's loss read on it gives an equivalent wait. Then, per step of a half:
  s_M  the time of one mid-circuit measurement (the off arms of C(n), against n),
  s_C  one measurement and one unfired decision, s_F one fired decision,
  decision latency  = s_C - s_M (what the conditional adds; a measurement's crosstalk on the clock cancels in it),
  fired - unfired   = s_F - s_C,
  two actors        = s_C2 / s_C (1: in parallel; 2: one after the other).
Placement: rule C, one chain of 7 sites, two clocks on sites 0 and 6 (the same wait read on two qubits), actors on
sites 2 and 4 (sites 1, 3, 5 idle, so no actor is a clock's neighbour). The clock is read last; barriers fence the halves so the clock idles while the actor works.

  python gpu/timing_night.py build DEVDIR OUT [--dry-clifford-sentinel]
  python gpu/timing_night.py check OUT
  python gpu/timing_night.py score OUT
  python gpu/timing_night.py planted                 the estimator on synthetic counts with a planted latency
  python gpu/timing_night.py planted-run OUT         dry only: simulate a built job (Clifford sentinel) with planted
                                                     lengths; then `score OUT` should read them back
"""
import argparse
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

DT_NS = 4.0                       # dt assumed 4 ns (the record keeps no dt; home can record backend.dt: a time, not a
                                  # quality number). The ruler is in dt, so only the conversion to us depends on it.
RULER_DT = (0, 1008, 2000, 4000, 6000, 8000)   # per half, multiples of 16 dt: 0, ~4, 8, 16, 24, 32 us (64 in all)
NS_C = (2, 4, 8)                                # steps chosen so every item's wait stays inside the ruler's range
NS_F = (4, 8)
NS_C2 = (2, 4)
N_SITES = 7
CLOCKS, A1, A2 = (0, 6), 2, 4                   # two clocks (more shots on the same wait), never an actor's neighbour
SHOTS = 4000


def _half(qc, kind, n, d, bits, actors):
    """One half's actor work; bits: an iterator of fresh clbit indices."""
    if kind == "R":
        if d:
            qc.delay(d, A1, unit="dt")
        return
    for _ in range(n):
        for a in actors:
            b = next(bits)
            if kind == "F":
                qc.x(a)
            qc.measure(a, b)
            with qc.if_test((qc.clbits[b], 1)):
                qc.x(a)                       # never fires in C (the actor is |0>); fires and resets in F


def item(kind, n=0, d=0):
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
    actors = [A1, A2] if kind == "C2" else [A1]
    k = "C" if kind == "C2" else kind
    nmeas = 0 if kind == "R" else 2 * n * len(actors)
    qc = QuantumCircuit(QuantumRegister(N_SITES, "q"), ClassicalRegister(nmeas + len(CLOCKS), "c"))
    bits = iter(range(nmeas))
    for c in CLOCKS:
        qc.h(c)
    qc.barrier()
    _half(qc, k, n, d, bits, actors)
    qc.barrier()
    for c in CLOCKS:
        qc.x(c)                               # the echo
    qc.barrier()
    _half(qc, k, n, d, bits, actors)
    qc.barrier()
    for i, c in enumerate(CLOCKS):
        qc.h(c)
        qc.measure(c, nmeas + i)              # ideal 0 (X leaves |+> as it is: H X H |0> = |0>); the loss is reading 1
    return qc, dict(success={nmeas + i: 0 for i in range(len(CLOCKS))}, bound=None, form="pauli")


def items():
    out = [(f"R{d}", *item("R", d=d)) for d in RULER_DT]
    out += [(f"C{n}", *item("C", n=n)) for n in NS_C]
    out += [(f"F{n}", *item("F", n=n)) for n in NS_F]
    out += [(f"D{n}", *item("C2", n=n)) for n in NS_C2]   # D = two actors (C2)
    return out


def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None   # dry runs only, never a device
    rep = FF.build(Device.load(a.devdir), items(), a.out, shots=SHOTS, max_seconds=60, sentinel_spec=spec)
    print(json.dumps({k: rep[k] for k in ("device", "circuits", "qpu_seconds_model", "shots") if k in rep}))
    print(json.dumps({t: v["chain"] for t, v in list(rep["items"].items())[:1]}))


def check(a):
    """Noiseless Aer of every arm: both clocks read 0 in every shot (their loss 0) in ff and off; floors all zero."""
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    from psf_os import feedforward as FF
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
            clock0 = sum(v for k, v in cnt.items() if all(FF._bits(k, n)[n - 1 - i] == 0 for i in range(len(CLOCKS)))) / tot
            allz = sum(v for k, v in cnt.items() if set(FF._bits(k, n)) == {0}) / tot
            ok = allz == 1.0 if cell["role"] == "floor" else clock0 == 1.0
            print(f"{cell['name']:12s} {cell['role']:6s} clocks read 0 {clock0:.3f}  all zero {allz:.3f} "
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


def estimate(losses):
    """losses: {clock index: {tag: (loss share, shots)}} with ff tags as items() and off arms as tag + "_off". Per
    clock the ruler (made non-decreasing) is read piecewise linearly on the tau scale; the clocks' equivalent waits for
    an item are averaged with inverse-variance weights. Per-step times in us with SEs (delta method)."""
    rulers = {}
    for ci, L in losses.items():
        pts = sorted((2 * d * DT_NS / 1000.0, *L[f"R{d}"]) for d in RULER_DT)
        mono = _pava([t for t, _, _ in pts], [p for _, p, _ in pts], [n for _, _, n in pts])
        if len(mono) >= 2 and mono[-1][1] > mono[0][1]:
            rulers[ci] = dict(points=pts, monotone=mono)
    if not rulers:
        return dict(ruler={str(c): None for c in losses}, error="every ruler is flat: no time can be read")

    def t_eq(tag):
        vals = [_clock_teq(rulers[ci]["monotone"], *losses[ci][tag]) for ci in rulers]
        vals = [v for v in vals if math.isfinite(v[0]) and math.isfinite(v[1]) and v[1] > 0]
        w = [1 / v[1] ** 2 for v in vals]
        t = sum(wi * v[0] for wi, v in zip(w, vals)) / sum(w)
        return t, math.sqrt(1 / sum(w)), any(v[2] for v in vals)

    def slope(tags, steps):
        pts_ = [(s_, *t_eq(tg)) for tg, s_ in zip(tags, steps)]
        f = _wls([q[0] for q in pts_], [q[1] for q in pts_], [q[2] for q in pts_])
        return dict(us_per_step=f["b"], se=math.sqrt(f["var_b"]), intercept_us=f["a"],
                    points=[dict(steps=q[0], us=q[1], se=q[2], outside_ruler=q[3]) for q in pts_])

    steps_c = [2 * n for n in NS_C]                   # measurement + decision steps per circuit (two halves)
    sM = slope([f"C{n}_off" for n in NS_C], steps_c)
    sC = slope([f"C{n}" for n in NS_C], steps_c)
    sF = slope([f"F{n}" for n in NS_F], [2 * n for n in NS_F])
    sD = slope([f"D{n}" for n in NS_C2], [2 * n for n in NS_C2])
    lat = sC["us_per_step"] - sM["us_per_step"]
    lat_se = math.hypot(sC["se"], sM["se"])            # the two slopes share the ruler: conservative
    fire = sF["us_per_step"] - sC["us_per_step"]
    fire_se = math.hypot(sF["se"], sC["se"])
    ratio = sD["us_per_step"] / sC["us_per_step"] if sC["us_per_step"] > 0 else None
    return dict(rulers={str(c): r for c, r in rulers.items()}, measurement=sM, measure_and_decide=sC, fired=sF,
                two_actors=sD, decision_latency_us=lat, decision_latency_se=lat_se, fired_minus_unfired_us=fire,
                fired_minus_unfired_se=fire_se, two_actors_ratio=ratio, dt_ns_assumed=DT_NS)


def show(e):
    if "error" in e:
        print("ruler:", e["error"])
        return
    for c, r in e["rulers"].items():
        print(f"ruler of clock {c} (us, loss): " + ", ".join(f"{t:.0f} {p:.3f}" for t, p, _ in r["points"]))
    for k, nm in (("measurement", "one mid-circuit measurement"), ("measure_and_decide", "measurement + unfired decision"),
                  ("fired", "measurement + fired decision"), ("two_actors", "two actors side by side")):
        print(f"  {nm:34s} {e[k]['us_per_step']:.3f} us (SE {e[k]['se']:.3f})")
    print(f"decision latency (unfired) {e['decision_latency_us']:+.3f} us (2 SE {2 * e['decision_latency_se']:.3f}); "
          f"fired - unfired {e['fired_minus_unfired_us']:+.3f} us (2 SE {2 * e['fired_minus_unfired_se']:.3f}); two "
          f"actors / one {e['two_actors_ratio']:.2f}" if e["two_actors_ratio"] is not None else "")


def score(a):
    from psf_os import feedforward as FF
    import ctrl_night as CN
    g = CN._counts(a.out)
    losses = {i: {} for i in range(len(CLOCKS))}
    floor = {}
    for (tag, arm), (n, cnt) in g.items():
        tot = sum(cnt.values())
        for i in range(len(CLOCKS)):
            b = n - len(CLOCKS) + i
            if arm == "floor":
                floor[f"{tag} clock {i}"] = sum(v for k, v in cnt.items() if FF._bits(k, n)[b] == 1) / tot
            else:
                p0 = sum(v for k, v in cnt.items() if FF._bits(k, n)[b] == 1) / tot     # loss: the clock reads 1
                losses[i][tag + ("" if arm == "ff" else "_off")] = (p0, tot)
    e = estimate(losses)
    e["losses"] = {str(i): v for i, v in losses.items()}
    e["clock_floor_reads_1"] = floor
    show(e)
    json.dump(e, open(os.path.join(a.out, "timing_scores.json"), "w"), indent=1)
    return e


def planted(a):
    """The estimator on synthetic counts (no circuit): each clock's loss 0.5 (1 - exp(-t / T)) + r with T 100 and
    160 us and r 0.01 (illustrative), elapsed times from planted lengths: measurement 2.6 us, decision latency 0.9 us, a fired
    conditional 0.3 us more, two actors waiting for each other (factor 2); binomial counts, 4000 shots, fixed seeds.
    The estimator should give the planted numbers back within its errors."""
    Ts, r, MEAS, LAT, FIRE = (100.0, 160.0), 0.01, 2.6, 0.9, 0.3
    res = []
    for seed in range(6):
        rng = random.Random(20261118 + seed)

        def draw(t, T):
            p = 0.5 * (1 - math.exp(-t / T)) + r
            return sum(rng.random() < p for _ in range(SHOTS)) / SHOTS, SHOTS
        L = {i: {} for i in range(len(Ts))}
        for i, T in enumerate(Ts):
            for d in RULER_DT:
                L[i][f"R{d}"] = draw(2 * d * DT_NS / 1000.0, T)
            for n in NS_C:
                L[i][f"C{n}"] = draw(2 * n * (MEAS + LAT), T)
                L[i][f"C{n}_off"] = draw(2 * n * MEAS, T)
            for n in NS_F:
                L[i][f"F{n}"] = draw(2 * n * (MEAS + LAT + FIRE), T)
            for n in NS_C2:
                L[i][f"D{n}"] = draw(2 * n * 2 * (MEAS + LAT), T)
        e = estimate(L)
        res.append(e)
        print(f"seed {seed}: measurement {e['measurement']['us_per_step']:.2f} (planted {MEAS}); latency "
              f"{e['decision_latency_us']:+.2f} (2 SE {2 * e['decision_latency_se']:.2f}; planted {LAT}); fired - "
              f"unfired {e['fired_minus_unfired_us']:+.2f} (2 SE {2 * e['fired_minus_unfired_se']:.2f}; planted {FIRE}); "
              f"two actors / one {e['two_actors_ratio']:.2f} (planted 2.0)")
    return res


def planted_run(a):
    """Dry runs only: simulate the built job with a PLANTED timing (illustrative, never fitted): each half the clocks
    dephase by exp(-t / T) for the half's elapsed time t (T 100 us), t from planted lengths (a delay d dt; a measurement
    2.6 us; an unfired decision 0.9 us more, a fired one 0.3 us more again; two actors one after the other); writes
    raw_counts.json and submission.json as run_local does. Then `score` should read the planted lengths back from the
    real circuits: a check of the circuits, the bits and the arms, not of any device."""
    from qiskit import QuantumCircuit, qpy
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import phase_damping_error
    from psf_os import feedforward as FF
    from psf_os.ibm import _stamp
    from psf_os.sim import to_clifford_gates
    T, MEAS, LAT, FIRE = 100.0, 2.6, 0.9, 0.3
    job = os.path.join(a.out, "job")
    man = json.load(open(os.path.join(job, "manifest.json")))
    b = json.load(open(os.path.join(a.out, "build.json")))
    circs = qpy.load(open(os.path.join(job, "circuits.qpy"), "rb"))
    rows = []
    for k, c in enumerate(circs):
        cell = man["cells"][man["pubs"][k]["cell"]]
        cc = FF.compact(c)
        if cell["role"] == "sentinel":
            cl = to_clifford_gates(cc)
            res = AerSimulator(method="stabilizer").run(cl, shots=SHOTS, seed_simulator=20261118 + 10000 * k).result()
            rows.append(dict(pub=k, counts={key.replace(" ", ""): v for key, v in res.get_counts(0).items()}))
            continue
        tag = cell["name"][3:].replace("_floor", "").replace("_off", "")
        arm = cell["role"]
        if arm == "floor":
            t = 0.0
        elif tag.startswith("R"):
            t = int(tag[1:]) * DT_NS / 1000.0
        else:
            n = int(tag[1:])
            per = MEAS + (0.0 if arm == "off" else LAT + (FIRE if tag.startswith("F") else 0.0))
            t = n * per * (2 if tag.startswith("D") else 1)
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
        res = AerSimulator(method="density_matrix").run(w, shots=SHOTS, seed_simulator=20261118 + 10000 * k).result()
        rows.append(dict(pub=k, counts={key.replace(" ", ""): v for key, v in res.get_counts(0).items()}))
    t_ = _stamp()
    json.dump(dict(job_id="local-planted-timing", submitted=t_, local=True, backend=man["fetch"]["backend"],
                   simulator="aer, PLANTED timing (dry runs only)"), open(os.path.join(job, "submission.json"), "w"))
    json.dump(dict(fetched=t_, job_id="local-planted-timing", status="DONE (local, planted timing)", rows=rows),
              open(os.path.join(job, "raw_counts.json"), "w"))
    print(f"planted: T {T} us, measurement {MEAS}, decision {LAT}, fired +{FIRE}, two actors in series")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    b.add_argument("--dry-clifford-sentinel", action="store_true")
    for nm in ("check", "score"):
        sub.add_parser(nm).add_argument("out")
    sub.add_parser("planted")
    sub.add_parser("planted-run").add_argument("out")
    a = ap.parse_args()
    r = {"build": build, "check": check, "score": score, "planted": planted, "planted-run": planted_run}[a.cmd](a)
    sys.exit(0 if r is not False else 1)
