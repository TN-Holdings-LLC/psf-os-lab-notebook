"""Schedule pass (workplace VS Claude, 2026-11-17; the workplace request 17e; desk only, not declared, psf-os unchanged).

For every compiled circuit of a feed-forward job (psf_os.feedforward.build output; the ff and off arms):
  1. the ledger (ledger.py) of four schedules: ASAP / ALAP, with the barriers as built / without them. The barrier-free
     cells are candidates only when the circuit's barriers pin a schedule and nothing else. Barriers between two
     one-qubit gates on one qubit (gate, barriers, gate on that qubit's timeline) stop a compiler from fusing the two;
     in the second and third neuron designs they are the outputs' X before and after each ancilla measurement (held
     flipped during it; partly fused into neighbouring gates once compiled) and keep the X pairs from cancelling in the
     off arm. They belong to the design, so such a circuit keeps its barriers;
  2. the candidate with the smallest wait is chosen (ties: the first of asap, alap, asap_nobar, alap_nobar);
  3. the chosen schedule S is written into the circuit: the instructions in the order of their start times in S, and
     barriers where an executor could move an instruction away from S:
       - before instruction i, when an as-soon-as-possible executor would start it earlier than S: a barrier over i's
         qubits and every qubit whose last instruction ends exactly at i's start in S (the anchor);
       - after instruction i, when an as-late-as-possible executor would end it later than S: a barrier over i's qubits
         and every qubit whose next instruction starts exactly at i's end in S.
     A barrier can only hold an instruction at the time of another instruction's edge. Where S starts (or ends) an
     instruction at a time no other instruction starts or ends at (a sub-gate offset), no barrier can pin it; it is
     counted and reported;
  4. checks: (a) the pinned circuit against the circuit as built, noiselessly, by the exact branching simulation
     (notes/rus_coherent_2026-11-17/coherent.branch_distribution): total variation <= 1e-12, where qubits plus
     measurements <= 24 (larger ones, such as the sequential teleport at distance >= 8, do not fit in memory); and
     always the structural identity: barriers left out, the same operations in the same order on every qubit and
     clbit; (b) the pinned circuit's ledger, recounted under both executors (ASAP and ALAP, barriers kept), against
     the chosen value;
  5. beside: the smallest wait that a pinned circuit guarantees under either executor (every allowed cell, pinned
     exactly or snapped, the larger of its two recounts), with the circuit that gives it.

Lengths are ledger.py's: FakeMarrakesh medians, illustrative, never fitted; no device error number is read. The decision
latency is a parameter (default 0).

  python schedule_pass.py OUTDIR [OUTDIR ...] [--latency-us X] [--json FILE] [--pinned DIR] [--jit]

--jit (the request 17f, after the ledger gained JIT): the schedule is ledger's JIT (prepared just in time, measured
and decided as early as possible; barriers as built, or removed only where they pin a schedule and nothing else and
removing them is smaller). It is pinned by delays: before an instruction that an ASAP executor would start earlier,
a delay on each of its qubits that would be ready earlier, that qubit only. Checks: (a) identity: the exact branching
simulation of the circuit as built, the pinned circuit and the pinned circuit with its delays removed (a delay acts
as the identity there), total variation <= 1e-12, where it fits; the structural identity (barriers and delays left
out) always; (b) the pinned circuit recounted under ASAP (and JIT, ALAP beside), delays counted idle (ledger.py), must
equal the JIT value. Beside: the same schedule pinned by barriers alone (exact, then snapped), and whether that works.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "rus_coherent_2026-11-17"))

import ledger as LG  # noqa: E402

EPS = 1e-15            # seconds: two edges closer than this are the same time (rounding is ~1e-21)
TVD_MAX = 1e-12
CANDS = ("asap", "alap", "asap_nobar", "alap_nobar")


def without_barriers(qc):
    out = qc.copy_empty_like()
    for ins in qc.data:
        if ins.operation.name != "barrier":
            out.append(ins.operation, ins.qubits, ins.clbits)
    return out


def barriers_hold_x_pairs(qc):
    """True when barriers stand between two one-qubit gates on one qubit (that qubit's timeline reads gate,
    barrier(s), gate). Without the barriers a compiler fuses the two; in the second and third neuron designs they are
    the outputs' X before and after a measurement (held flipped during it), partly fused into the neighbouring gates
    when compiled. Such barriers belong to the design, not to a schedule."""
    one = {"x", "sx", "rz", "h", "s", "sdg", "t", "tdg", "z", "y", "p", "ry", "rx", "u"}
    line = {q: [] for q in range(qc.num_qubits)}
    for ins in qc.data:
        for x in ins.qubits:
            line[qc.find_bit(x).index].append(ins.operation.name)
    for seq in line.values():
        for i, nm in enumerate(seq):
            if nm not in one:
                continue
            j = i + 1
            while j < len(seq) and seq[j] == "barrier":
                j += 1
            if j > i + 1 and j < len(seq) and seq[j] in one:
                return True
    return False


def emission_order(ins, start):
    """The instructions by start time, never before an earlier instruction on a shared qubit or clbit (start times
    from ledger's ALAP carry rounding of order 1e-21 s, so a plain sort can swap a zero-length rz with its neighbour).
    At equal start, zero-length instructions first, so that an edge at that time is still ahead to anchor them."""
    import heapq
    n = len(ins)
    preds = [set() for _ in range(n)]
    last = {}
    for i, (qs, cs, *_r) in enumerate(ins):
        for key in [("q", q) for q in qs] + [("c", c) for c in cs]:
            if key in last:
                preds[i].add(last[key])
            last[key] = i
    succ = [[] for _ in range(n)]
    for i in range(n):
        for p in preds[i]:
            succ[p].append(i)
    left = [len(p) for p in preds]
    heap = [(start[i], ins[i][3] > 0, i) for i in range(n) if left[i] == 0]
    heapq.heapify(heap)
    order = []
    while heap:
        _, _, i = heapq.heappop(heap)
        order.append(i)
        for j in succ[i]:
            left[j] -= 1
            if left[j] == 0:
                heapq.heappush(heap, (start[j], ins[j][3] > 0, j))
    assert len(order) == n
    return order


def pin(qc, latency_us, alap, snap=False):
    """(pinned circuit, unpinned counts) for the schedule of qc (its barriers as given) by ledger's ASAP or ALAP.
    snap: an instruction that no edge can hold at its start in S is held at the next edge after it instead (the
    nearest later end of an instruction on another qubit): a later start than S, which no executor can move earlier;
    and an instruction that no edge can hold at its end is held by the nearest later start on another qubit before
    its own successor (it may still drift until then, no further)."""
    ins = LG._instructions(qc, latency_us * LG.US, False)
    nq, nc = qc.num_qubits, qc.num_clbits
    start, T = LG._schedule(ins, nq, nc, alap)
    n = len(ins)
    end = [start[i] + ins[i][3] for i in range(n)]
    order = emission_order(ins, start)
    # next start per qubit / clbit after each emitted position (for the after-barriers)
    nxt_q = [dict() for _ in range(n)]
    nxt_c = [dict() for _ in range(n)]
    later_q, later_c = {}, {}
    for pos in range(n - 1, -1, -1):
        i = order[pos]
        nxt_q[pos], nxt_c[pos] = dict(later_q), dict(later_c)
        for q in ins[i][0]:
            later_q[q] = start[i]
        for c in ins[i][1]:
            later_c[c] = start[i]
    out = qc.copy_empty_like()
    ready_q, ready_c = [0.0] * nq, [0.0] * nc
    miss_asap = miss_alap = 0
    data = qc.data
    for pos, i in enumerate(order):
        qs, cs, kind, d, _, _ = ins[i]
        s, e = start[i], end[i]
        if kind != "barrier" and qs:
            nat = max([ready_q[q] for q in qs] + [ready_c[c] for c in cs] + [0.0])
            if nat < s - EPS:
                anc = [p for p in range(nq) if p not in qs and abs(ready_q[p] - s) <= EPS]
                if not anc and snap:
                    later = [ready_q[p] for p in range(nq) if p not in qs and ready_q[p] > s + EPS]
                    if later:
                        t = min(later)
                        anc = [p for p in range(nq) if p not in qs and abs(ready_q[p] - t) <= EPS]
                if anc:
                    out.barrier(*[out.qubits[q] for q in sorted(set(qs) | set(anc))])
                    t = max(ready_q[p] for p in anc)
                    for q in qs:
                        ready_q[q] = t
                    e = t + d
                else:
                    miss_asap += 1
        out.append(data[i].operation, data[i].qubits, data[i].clbits)
        if kind == "barrier":
            t = max(ready_q[q] for q in qs)
            for q in qs:
                ready_q[q] = t
            continue
        for q in qs:
            ready_q[q] = e
        for c in cs:
            ready_c[c] = e
        if qs:
            nat_end = min([nxt_q[pos].get(q, T) for q in qs] + [nxt_c[pos].get(c, T) for c in cs] + [T])
            if nat_end > e + EPS:
                anc = [p for p in range(nq) if p not in qs and abs(nxt_q[pos].get(p, -1.0) - e) <= EPS]
                if not anc and snap:
                    later = [nxt_q[pos][p] for p in range(nq) if p not in qs and p in nxt_q[pos]
                             and e + EPS < nxt_q[pos][p] < nat_end - EPS]
                    if later:
                        t = min(later)
                        anc = [p for p in range(nq) if p not in qs and abs(nxt_q[pos].get(p, -1.0) - t) <= EPS]
                if anc:
                    out.barrier(*[out.qubits[q] for q in sorted(set(qs) | set(anc))])
                    for p in anc:
                        ready_q[p] = e
                else:
                    miss_alap += 1
    return out, dict(asap_executor=miss_asap, alap_executor=miss_alap)


SIM_MAX = 24          # simulate when qubits + mid-circuit measurements <= this (branches x amplitudes fit)


def same_dag(a, b):
    """True when a and b, barriers and delays left out, hold the same operations in the same order on every qubit and
    every clbit (then they are the same circuit up to idle time: an exact identity, no simulation)."""
    def content(c):
        """A block's instructions by content (name, numeric parameters, block-local qubits and clbits)."""
        return tuple((i.operation.name, tuple(round(float(p), 12) for p in i.operation.params
                                              if isinstance(p, (int, float))),
                      tuple(c.find_bit(x).index for x in i.qubits), tuple(c.find_bit(x).index for x in i.clbits),
                      tuple(content(b) if b is not None else None for b in i.operation.blocks)
                      if i.operation.name == "if_else" else ())
                     for i in c.data if i.operation.name not in ("barrier", "delay"))

    def lines(qc):
        out = {}
        for ins in qc.data:
            if ins.operation.name in ("barrier", "delay"):
                continue
            blk = ()
            if ins.operation.name == "if_else":
                bit, val = ins.operation.condition
                blk = (qc.find_bit(bit).index, int(val),
                       tuple(content(b) if b is not None else None for b in ins.operation.blocks))
            key = (ins.operation.name, tuple(round(float(p), 12) for p in ins.operation.params
                                             if isinstance(p, (int, float))),
                   tuple(qc.find_bit(x).index for x in ins.qubits), tuple(qc.find_bit(x).index for x in ins.clbits),
                   blk)
            for x in ins.qubits:
                out.setdefault(("q", qc.find_bit(x).index), []).append(key)
            for x in ins.clbits:
                out.setdefault(("c", qc.find_bit(x).index), []).append(key)
            if ins.operation.name == "if_else":
                bit, _ = ins.operation.condition
                out.setdefault(("c", qc.find_bit(bit).index), []).append(key)
        return out
    return lines(a) == lines(b)


def identity(cc, p):
    """(total variation by the exact branching simulation or None when too large, same_dag)."""
    from coherent import branch_distribution, tvd
    mids = sum(1 for i in cc.data if i.operation.name == "measure")
    d = tvd(branch_distribution(cc), branch_distribution(p)) if cc.num_qubits + mids <= SIM_MAX else None
    return d, same_dag(cc, p)


def _pinned(cc, latency_us, cand, snap):
    src = without_barriers(cc) if cand.endswith("nobar") else cc
    p, miss = pin(src, latency_us, cand.startswith("alap"), snap)
    re = {ex: LG.ledger(p, latency_us, ex == "alap", False) for ex in ("asap", "alap")}
    added = sum(1 for i in p.data if i.operation.name == "barrier") - sum(1 for i in src.data
                                                                          if i.operation.name == "barrier")
    return p, dict(candidate=cand, snap=snap, recount={ex: re[ex]["wait_qus"] for ex in re},
                   recount_T_us={ex: re[ex]["T_us"] for ex in re}, guaranteed_wait_qus=max(r["wait_qus"]
                                                                                         for r in re.values()),
                   unanchored=miss, barriers_added=added)


def one(cc, latency_us):
    """The request's pass (the smallest ledger cell, pinned) and, beside, the smallest wait that a pinned circuit
    guarantees under either executor (every allowed cell, pinned exactly or snapped)."""
    held = barriers_hold_x_pairs(cc)
    has_bar = any(i.operation.name == "barrier" for i in cc.data)
    cells = {c: LG.ledger(cc, latency_us, c.startswith("alap"), c.endswith("nobar")) for c in CANDS}
    allowed = [c for c in CANDS if not (c.endswith("nobar") and held)]
    best = min(allowed, key=lambda c: (round(cells[c]["wait_qus"], 9), CANDS.index(c)))
    v = cells[best]["wait_qus"]
    pinned, r = _pinned(cc, latency_us, best, False)
    exact = {ex: abs(r["recount"][ex] - v) <= 1e-9 for ex in r["recount"]}
    opts = []
    for c in allowed:
        for sn in (False, True):
            opts.append(_pinned(cc, latency_us, c, sn))
    gp, g = min(opts, key=lambda o: (round(o[1]["guaranteed_wait_qus"], 9), o[1]["snap"], o[1]["barriers_added"]))
    d, sd = identity(cc, pinned)
    dg, sdg = identity(cc, gp)
    return pinned, gp, dict(barriers=has_bar, barriers_belong_to_design=held, cells=cells, allowed=allowed,
                            chosen=best, chosen_wait_qus=v, as_built_asap_wait_qus=cells["asap"]["wait_qus"],
                            as_built_alap_wait_qus=cells["alap"]["wait_qus"], pinned=r, pinned_exact=exact,
                            tvd=d, same_dag=sd, identity=sd and (d is None or d <= TVD_MAX), guaranteed=g,
                            tvd_guaranteed=dg, same_dag_guaranteed=sdg,
                            identity_guaranteed=sdg and (dg is None or dg <= TVD_MAX))


# ---- 17f: the JIT schedule pinned by delays (the default) or by barriers alone -----------------------------------

def without_delays(qc):
    out = qc.copy_empty_like()
    for ins in qc.data:
        if ins.operation.name != "delay":
            out.append(ins.operation, ins.qubits, ins.clbits)
    return out


def pin_delays(qc, latency_us):
    """(pinned circuit, info) for ledger's JIT schedule of qc (its barriers as given): the instructions in the order of
    their JIT start times, and before an instruction that an as-soon-as-possible executor would start earlier than
    JIT, a delay on each of its qubits that would be ready earlier (that qubit only), as long as the difference.
    Delays are whole samples of dt (FakeMarrakesh dt; every length here is a whole number of samples, checked)."""
    from qiskit.circuit import Delay
    dt = LG.lengths()["dt"]
    ins = LG._instructions(qc, latency_us * LG.US, False)
    nq, nc = qc.num_qubits, qc.num_clbits
    start, _ = LG._schedule(ins, nq, nc, "jit")
    order = emission_order(ins, start)
    out = qc.copy_empty_like()
    ready_q, ready_c = [0.0] * nq, [0.0] * nc
    n_delay, off_grid, total = 0, 0.0, 0.0
    for i in order:
        qs, cs, kind, d, _, _ = ins[i]
        s = start[i]
        if kind == "barrier":
            out.append(qc.data[i].operation, qc.data[i].qubits, qc.data[i].clbits)
            t = max(ready_q[q] for q in qs)
            for q in qs:
                ready_q[q] = t
            continue
        nat = max([ready_q[q] for q in qs] + [ready_c[c] for c in cs] + [0.0])
        if nat < s - EPS:
            for q in qs:
                gap = s - ready_q[q]
                if gap > EPS:
                    k = gap / dt
                    off_grid = max(off_grid, abs(k - round(k)))
                    out.append(Delay(int(round(k)), unit="dt"), [out.qubits[q]], [])
                    n_delay += 1
                    total += gap
                    ready_q[q] = s
        out.append(qc.data[i].operation, qc.data[i].qubits, qc.data[i].clbits)
        e = max([ready_q[q] for q in qs] + [ready_c[c] for c in cs] + [0.0]) + d
        for q in qs:
            ready_q[q] = e
        for c in cs:
            ready_c[c] = e
    return out, dict(delays=n_delay, delay_total_us=total / LG.US, off_grid_samples=off_grid)


def recount(p, latency_us):
    """Wait and length of a pinned circuit under three executors (ASAP, ALAP, JIT; barriers kept, delays idle)."""
    re = {ex: LG.ledger(p, latency_us, {"asap": False, "alap": True, "jit": "jit"}[ex], False)
          for ex in ("asap", "alap", "jit")}
    return {ex: r["wait_qus"] for ex, r in re.items()}, {ex: r["T_us"] for ex, r in re.items()}


def one_jit(cc, latency_us):
    """The request 17f: ledger's JIT schedule (barriers as built; without them only where they pin a schedule and
    nothing else, if smaller), pinned by delays; beside, pinned by barriers alone (exact, then snapped)."""
    held = barriers_hold_x_pairs(cc)
    cells = {c: LG.ledger(cc, latency_us, a, nb) for c, a, nb in
             (("asap", False, False), ("alap", True, False), ("jit", "jit", False), ("jit_nobar", "jit", True))}
    cand = "jit"
    if not held and cells["jit_nobar"]["wait_qus"] < cells["jit"]["wait_qus"] - 1e-9:
        cand = "jit_nobar"
    src = without_barriers(cc) if cand == "jit_nobar" else cc
    v = cells[cand]["wait_qus"]
    pd, info = pin_delays(src, latency_us)
    w, T = recount(pd, latency_us)
    mids = sum(1 for i in cc.data if i.operation.name == "measure")
    sim = cc.num_qubits + mids <= SIM_MAX
    tv = tv_strip = None
    if sim:
        from coherent import branch_distribution, tvd
        d0, d1, d2 = branch_distribution(cc), branch_distribution(pd), branch_distribution(without_delays(pd))
        tv, tv_strip = float(tvd(d0, d1)), float(tvd(d1, d2))
    sd = same_dag(cc, pd)
    bar = {}
    for snap in (False, True):
        pb, miss = pin(src, latency_us, "jit", snap)
        wb, Tb = recount(pb, latency_us)
        bar["snapped" if snap else "exact"] = dict(recount=wb, recount_T_us=Tb, unanchored=miss,
                                                   asap_equals_jit=abs(wb["asap"] - v) <= 1e-9,
                                                   same_dag=same_dag(cc, pb))
    return pd, dict(barriers_belong_to_design=held, cells={c: dict(wait_qus=r["wait_qus"], T_us=r["T_us"])
                                                           for c, r in cells.items()},
                    chosen=cand, jit_wait_qus=v, jit_T_us=cells[cand]["T_us"], delays=info, recount=w,
                    recount_T_us=T, asap_equals_jit=abs(w["asap"] - v) <= 1e-9,
                    tvd=tv, tvd_delays_removed=tv_strip, same_dag=sd,
                    identity=sd and (tv is None or (tv <= TVD_MAX and tv_strip <= TVD_MAX)), barrier_only=bar)


def job_jit(out, latency_us, pinned_dir=None):
    from qiskit import qpy
    from psf_os import feedforward as FF
    m = json.load(open(os.path.join(out, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(out, "job", "circuits.qpy"), "rb"))
    res, pins, i = {}, [], 0
    for cell in m["cells"]:
        for _ in range(cell["points"]):
            c = cs[i]
            i += 1
            if cell["role"] not in ("user", "off"):
                continue
            p, r = one_jit(FF.compact(c), latency_us)
            res[cell["name"]] = r
            p.name = cell["name"]
            pins.append(p)
    if pinned_dir:
        os.makedirs(pinned_dir, exist_ok=True)
        with open(os.path.join(pinned_dir, f"{os.path.basename(os.path.normpath(out))}_jit_delays.qpy"), "wb") as f:
            qpy.dump(pins, f)
    return res


def show_jit(name, r):
    w, b = r["recount"], r["barrier_only"]
    bo = ("barriers alone: exact" if b["exact"]["asap_equals_jit"] else
          "barriers alone: snapped" if b["snapped"]["asap_equals_jit"] else
          f"barriers alone: no (ASAP-exec {min(b['exact']['recount']['asap'], b['snapped']['recount']['asap']):.3f})")
    print(f"{name:16s} as built ASAP {r['cells']['asap']['wait_qus']:7.3f} ALAP {r['cells']['alap']['wait_qus']:7.3f}"
          f" -> {r['chosen']:9s} {r['jit_wait_qus']:7.3f} (T {r['jit_T_us']:6.2f}); delays {r['delays']['delays']:3d} "
          f"({r['delays']['delay_total_us']:6.2f} us, off grid {r['delays']['off_grid_samples']:.0e}); recount "
          f"ASAP-exec {w['asap']:7.3f} JIT-exec {w['jit']:7.3f} ALAP-exec {w['alap']:7.3f} "
          f"({'ASAP = JIT' if r['asap_equals_jit'] else 'ASAP != JIT'}); identity "
          f"{'ok' if r['identity'] else 'FAIL'} (TVD {_t(r['tvd'])}, delays removed {_t(r['tvd_delays_removed'])}, "
          f"same DAG {r['same_dag']}) | {bo}")


def job(out, latency_us, pinned_dir=None):
    from qiskit import qpy
    from psf_os import feedforward as FF
    m = json.load(open(os.path.join(out, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(out, "job", "circuits.qpy"), "rb"))
    res, pins, gps, i = {}, [], [], 0
    for cell in m["cells"]:
        for _ in range(cell["points"]):
            c = cs[i]
            i += 1
            if cell["role"] not in ("user", "off"):
                continue
            p, gp, r = one(FF.compact(c), latency_us)
            res[cell["name"]] = r
            p.name = gp.name = cell["name"]
            pins.append(p)
            gps.append(gp)
    if pinned_dir:
        os.makedirs(pinned_dir, exist_ok=True)
        base = os.path.basename(os.path.normpath(out))
        for suffix, cl in (("pinned", pins), ("guaranteed", gps)):
            with open(os.path.join(pinned_dir, f"{base}_{suffix}.qpy"), "wb") as f:
                qpy.dump(cl, f)
    return res


def as_text(v):
    """Floats as text with 4 significant digits (the record is read, not computed on; the full values are in the .txt
    tables to 3 decimals); booleans and integers kept."""
    if isinstance(v, dict):
        return {str(k): as_text(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [as_text(x) for x in v]
    if hasattr(v, "item") and not isinstance(v, (str, bytes)):
        v = v.item()
    if isinstance(v, bool) or v is None or isinstance(v, (int, str)):
        return v
    if isinstance(v, float):
        return "0" if v == 0 else "%.3e" % v      # 4 significant digits: never a 4-decimal string
    return str(v)


def _t(d):
    return "not simulated" if d is None else f"{d:.1e}"


def show(name, r):
    p, g = r["pinned"], r["guaranteed"]
    ok = all(r["pinned_exact"].values())
    print(f"{name:16s} as built ASAP {r['as_built_asap_wait_qus']:7.3f} ALAP {r['as_built_alap_wait_qus']:7.3f} -> "
          f"{r['chosen']:10s} {r['chosen_wait_qus']:7.3f}; pinned recount ASAP-exec {p['recount']['asap']:7.3f} "
          f"ALAP-exec {p['recount']['alap']:7.3f} ({'pinned' if ok else 'NOT pinned'}, unanchored "
          f"{p['unanchored']['asap_executor']}/{p['unanchored']['alap_executor']}, +{p['barriers_added']}) "
          f"identity {'ok' if r['identity'] else 'FAIL'} (TVD {_t(r['tvd'])}, same DAG {r['same_dag']}) | "
          f"guaranteed {g['guaranteed_wait_qus']:7.3f} ({g['candidate']}{' snapped' if g['snap'] else ''}, T "
          f"{max(g['recount_T_us'].values()):6.2f} us, identity {'ok' if r['identity_guaranteed'] else 'FAIL'}, TVD "
          f"{_t(r['tvd_guaranteed'])})"
          + (" | barriers belong to the design" if r["barriers_belong_to_design"] else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outs", nargs="+")
    ap.add_argument("--latency-us", type=float, default=0.0)
    ap.add_argument("--json")
    ap.add_argument("--pinned")
    ap.add_argument("--jit", action="store_true", help="the request 17f: JIT pinned by delays (barriers beside)")
    a = ap.parse_args()
    L = LG.lengths()
    print("lengths (FakeMarrakesh medians, illustrative): " +
          ", ".join(f"{k} {v * 1e9:.0f} ns" for k, v in L.items() if k != "dt") + f"; decision latency {a.latency_us} us")
    allres = {}
    for o in a.outs:
        print(f"== {os.path.basename(os.path.normpath(o))}")
        res = (job_jit if a.jit else job)(o, a.latency_us, a.pinned)
        for nme, r in res.items():
            (show_jit if a.jit else show)(nme, r)
        allres[os.path.basename(os.path.normpath(o))] = res
    if a.json:
        json.dump(as_text(dict(latency_us=a.latency_us, lengths_ns={k: v * 1e9 for k, v in L.items() if k != "dt"},
                               jobs=allres)), open(a.json, "w", newline="\n"), indent=1)


if __name__ == "__main__":
    main()
