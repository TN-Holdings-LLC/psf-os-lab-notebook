"""Time-budget ledger (workplace prototype, 2026-11-17; owner "プロトタイプ作って"; desk only, not declared, psf-os unchanged).

For every compiled circuit of a feed-forward job (psf_os.feedforward.build output: job/manifest.json, job/circuits.qpy)
the ledger counts what the circuit's shape costs in time, with no device error number:

  mid            mid-circuit measurements (a measurement followed by any other operation on that qubit, or whose bit a
                 later conditional reads)
  meas_depth     sequential mid-circuit measurements on the longest dependency path (waits that cannot overlap)
  dec_depth      conditionals in a row on the longest dependency path (each may cost a decision latency; a parity is
                 one conditional per bit on IBM, so the stack on one qubit counts in full)
  T_us           length of the schedule (microseconds)
  idle_qus       idle time summed over qubits while they carry information (from their first gate to the start of
                 their last measurement), qubit-microseconds
  wait_qus       the part of idle_qus that lies under another qubit's measurement or under a decision latency
                 (the exposure the 2026-11-16 diagnostics point at)

each under three schedules a scheduler can choose: ASAP (every gate as early as possible), ALAP (as late as possible)
and JIT (ASAP, then every gate other than measurements and conditionals pushed as late as the next operation on its
qubits allows: prepared just in time, read as early as possible; added after the early-measurement prototype showed
that ALAP also pushes a qubit's last measurement late); and each for the circuit as built and with its barriers removed
(barriers do not change what the circuit computes; they pin the schedule). The difference between the cells is what a
scheduling pass of the OS could save without changing the circuit.

A delay instruction (written by the schedule pass to pin a schedule) takes its length in the schedule but counts as
idle, not as busy, and does not start a qubit's information-carrying time (2026-11-17f; circuits without delays are
counted exactly as before).

Lengths (illustrative, never fitted): the medians of Qiskit's FakeMarrakesh snapshot (the psf-os device record keeps no
gate lengths): sx / x 36 ns, rz 0, cz 68 ns, measure 2.584 us, reset 2.72 us. The decision latency of a conditional is
a free parameter (--latency-us, default 0; the device's value is not in any record we keep): with 0 the ledger is a
lower bound on the time a decision costs.

  python ledger.py OUTDIR [OUTDIR ...] [--latency-us X] [--json FILE]

Recorded here: ledger_latency0us.json and ledger_latency1us.json for tonight's three jobs (coh_night, compound_night,
apps_night, built on the 11-16 13:11 CET marrakesh record) and seqcmp (the 11-16 sequential teleport test at distance
4-16 beside the constant-depth form k = 2-8, same record).
"""
import argparse
import json
import os
import statistics

US = 1e-6
_LEN = None


def lengths():
    global _LEN
    if _LEN is None:
        from qiskit_ibm_runtime.fake_provider import FakeMarrakesh
        t = FakeMarrakesh().target
        _LEN = {}
        for g in ("sx", "x", "rz", "cz", "measure", "reset"):
            d = [p.duration for p in t[g].values() if p is not None and p.duration is not None]
            _LEN[g] = statistics.median(d)
        _LEN["dt"] = t.dt
    return _LEN


def _dur_simple(op):
    L = lengths()
    if op.name in ("barrier",):
        return 0.0
    if op.name == "delay":
        return op.duration * (L["dt"] if op.unit == "dt" else {"s": 1, "ms": 1e-3, "us": 1e-6, "ns": 1e-9}[op.unit])
    if op.name in L:
        return L[op.name]
    if op.name in ("id",):
        return L["sx"]
    raise ValueError(f"no length for {op.name}")


def _block_busy(block):
    """Per block-qubit busy time of a conditional body (sequential sum of its gates on that qubit)."""
    busy = [0.0] * block.num_qubits
    span = [0.0] * block.num_qubits
    for ins in block.data:
        qs = [block.find_bit(q).index for q in ins.qubits]
        d = _dur_simple(ins.operation)
        s = max(span[q] for q in qs) if qs else 0.0
        for q in qs:
            span[q] = s + d
            busy[q] += d
    return busy, max(span) if span else 0.0


def _instructions(qc, latency, drop_barriers):
    """[(qubits, clbits, kind, duration, body_busy {qubit: busy}, latency)]"""
    out = []
    for ins in qc.data:
        op = ins.operation
        if op.name == "barrier" and drop_barriers:
            continue
        qs = [qc.find_bit(q).index for q in ins.qubits]
        cs = [qc.find_bit(c).index for c in ins.clbits]
        if op.name == "if_else":
            body = {}
            span = 0.0
            for b in op.blocks:
                if b is None:
                    continue
                busy, sp = _block_busy(b)
                span = max(span, sp)
                for i, q in enumerate(qs):
                    body[q] = max(body.get(q, 0.0), busy[i])
            out.append((qs, cs, "if_else", latency + span, body, latency))
        else:
            out.append((qs, cs, op.name, _dur_simple(op), None, 0.0))
    return out


def _schedule(ins, nq, nc, alap):
    """Start times of every instruction: ASAP (alap False), ALAP by scheduling the reversed list (alap True), or "jit":
    ASAP, then every gate that is not a measurement, a conditional or a barrier pushed as late as the next operation on
    each of its qubits allows (prepared just in time, while measurements and decisions stay as early as possible)."""
    if alap == "jit":
        start, T = _schedule(ins, nq, nc, False)
        nxt = [None] * len(ins)
        seen = {}
        for i in range(len(ins) - 1, -1, -1):
            qs = ins[i][0]
            nxt[i] = [seen.get(q) for q in qs]
            for q in qs:
                seen[q] = i
        for i in range(len(ins) - 1, -1, -1):
            qs, cs, kind, d, _, _ = ins[i]
            if kind in ("measure", "if_else", "barrier", "reset") or cs:
                continue
            lim = [start[j] for j in nxt[i] if j is not None]
            if not lim:
                continue
            s = min(lim) - d
            if s > start[i]:
                start[i] = s
        return start, T
    order = list(range(len(ins)))[::-1] if alap else list(range(len(ins)))
    ready_q, ready_c = [0.0] * nq, [0.0] * nc
    start = [0.0] * len(ins)
    for i in order:
        qs, cs, kind, d, _, _ = ins[i]
        s = max([ready_q[q] for q in qs] + [ready_c[c] for c in cs] + [0.0])
        if kind == "barrier":
            for q in qs:
                ready_q[q] = s
            start[i] = s
            continue
        for q in qs:
            ready_q[q] = s + d
        for c in cs:
            ready_c[c] = s + d
        start[i] = s
    T = max(ready_q + ready_c + [0.0])
    if alap:                                            # map reversed time back to forward time
        start = [T - start[i] - ins[i][3] for i in range(len(ins))]
    return start, T


def _union(iv):
    out = []
    for a, b in sorted(iv):
        if b <= a:
            continue
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def _overlap(segs, cover):
    tot = 0.0
    for a, b in segs:
        for c, d in cover:
            lo, hi = max(a, c), min(b, d)
            if hi > lo:
                tot += hi - lo
    return tot


def ledger(qc, latency_us=0.0, alap=False, drop_barriers=False):
    ins = _instructions(qc, latency_us * US, drop_barriers)
    nq, nc = qc.num_qubits, qc.num_clbits
    start, T = _schedule(ins, nq, nc, alap)
    last = {}
    read_later = set()                                  # (instruction, clbit) pairs whose bit a later conditional reads
    for i, (qs, cs, kind, _, _, _) in enumerate(ins):
        for q in qs:
            if kind != "barrier":
                last[q] = i
    writer = {}
    for i, (qs, cs, kind, _, _, _) in enumerate(ins):
        if kind == "if_else":
            for c in cs:
                if c in writer:
                    read_later.add(writer[c])
        if kind == "measure":
            for c in cs:
                writer[c] = i
    # dependency depths
    mq, mc, dq, dc = [0] * nq, [0] * nc, [0] * nq, [0] * nc
    mid = 0
    busy = {q: [] for q in range(nq)}                  # (start, end) of gates on each qubit
    meas = {q: [] for q in range(nq)}                  # measurement intervals per qubit
    lat = []                                            # decision-latency intervals (qubits, (a, b))
    first, last_meas_start = {}, {}
    for i, (qs, cs, kind, d, body, lt) in enumerate(ins):
        if kind == "barrier":
            continue
        s = start[i]
        m = max([mq[q] for q in qs] + [mc[c] for c in cs] + [0])
        k = max([dq[q] for q in qs] + [dc[c] for c in cs] + [0])
        if kind == "measure":
            q = qs[0]
            if last[q] != i or i in read_later:
                mid += 1
                m += 1
            meas[q].append((s, s + d))
            last_meas_start[q] = s
        if kind == "if_else":
            k += 1
            lat.append((qs, (s, s + lt)))
        for q in qs:
            mq[q], dq[q] = m, k
        for c in cs:
            mc[c], dc[c] = m, k
        for q in qs:
            if kind == "if_else":
                b = body.get(q, 0.0)
                busy[q].append((s + d - b, s + d))     # body at the end of the conditional's interval
            elif d > 0 and kind != "delay":            # a delay is idle time, not work (schedule pass, 17f)
                busy[q].append((s, s + d))
            if d > 0 and kind not in ("rz", "delay") and q not in first:
                first[q] = s
    idle = wait = 0.0
    by_q = {}
    for q in range(nq):
        if q not in first:
            continue
        end = last_meas_start.get(q, max((b for _, b in busy[q]), default=first[q]))
        if end <= first[q]:
            continue
        bz = _union([(max(a, first[q]), min(b, end)) for a, b in busy[q]])
        segs, t = [], first[q]
        for a, b in bz:
            if a > t:
                segs.append((t, a))
            t = max(t, b)
        if end > t:
            segs.append((t, end))
        idle += sum(b - a for a, b in segs)
        cover = _union([iv for p in range(nq) if p != q for iv in meas[p]] +
                       [iv for qs, iv in lat if q in qs])
        w = _overlap(segs, cover)
        wait += w
        by_q[q] = round(w / US, 4)
    return dict(mid=mid, meas_depth=max(mq + mc + [0]), dec_depth=max(dq + dc + [0]), T_us=T / US,
                idle_qus=idle / US, wait_qus=wait / US, wait_by_qubit_qus=by_q)


def job_ledgers(out, latency_us=0.0, roles=("user", "off")):
    from qiskit import qpy
    from psf_os import feedforward as FF
    m = json.load(open(os.path.join(out, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(out, "job", "circuits.qpy"), "rb"))
    res, i = {}, 0
    for cell in m["cells"]:
        for _ in range(cell["points"]):
            c = cs[i]
            i += 1
            if cell["role"] not in roles:
                continue
            cc = FF.compact(c)
            res[cell["name"]] = {f"{'alap' if al else 'asap'}{'_nobar' if nb else ''}":
                                 ledger(cc, latency_us, al, nb) for al in (False, True) for nb in (False, True)}
            for nb in (False, True):
                res[cell["name"]]["jit" + ("_nobar" if nb else "")] = ledger(cc, latency_us, "jit", nb)
    return res


def show(name, r):
    a, b, c, d = r["asap"], r["alap"], r["asap_nobar"], r["alap_nobar"]
    print(f"{name:18s} mid {a['mid']:2d}  meas depth {a['meas_depth']:2d}  dec depth {a['dec_depth']:2d}  "
          f"T {a['T_us']:6.2f} us | wait q.us: as built ASAP {a['wait_qus']:6.2f} ALAP {b['wait_qus']:6.2f}; "
          f"no barriers ASAP {c['wait_qus']:6.2f} ALAP {d['wait_qus']:6.2f}; JIT {r['jit']['wait_qus']:6.2f} "
          f"JIT no barriers {r['jit_nobar']['wait_qus']:6.2f} | idle ASAP {a['idle_qus']:6.2f} "
          f"ALAP no barriers {d['idle_qus']:6.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outs", nargs="+")
    ap.add_argument("--latency-us", type=float, default=0.0)
    ap.add_argument("--json")
    a = ap.parse_args()
    L = lengths()
    print("lengths (FakeMarrakesh medians, illustrative): " +
          ", ".join(f"{k} {v * 1e9:.0f} ns" for k, v in L.items() if k != "dt") + f"; decision latency {a.latency_us} us")
    allres = {}
    for o in a.outs:
        print(f"== {os.path.basename(os.path.normpath(o))}")
        res = job_ledgers(o, a.latency_us)
        for n, r in res.items():
            show(n, r)
        allres[os.path.basename(os.path.normpath(o))] = res
    if a.json:
        json.dump(dict(latency_us=a.latency_us, lengths_ns={k: v * 1e9 for k, v in L.items() if k != "dt"},
                       jobs=allres), open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
