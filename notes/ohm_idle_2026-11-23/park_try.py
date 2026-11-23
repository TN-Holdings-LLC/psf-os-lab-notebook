"""A trial outside psf-os: park the probably-|1> idle spans of the sent Ohm circuits with X, delay, X (home VS,
2026-11-23; desk, no device). Nothing is sent and nothing under results/ is written.

For every idle span (ohm_idle.py, one schedule) with P(|1>) above one half and room for the pair (length at least
2 x + 2 dt, the fake backends' grid minimum delay being 2 dt), the span's instructions on that qubit become
X, delay(length - 2 x), X, placed just before the instruction (or measurement) that ends the span; any rz already in
the span stays before the first X, so the qubit's unitary is unchanged. Lengths are the fake backends' values (FakeFez,
FakeKingston), not the devices' records.

Checks, per circuit:
  * noise-free: the parked circuit's state against the sent one's, by MPS overlap (|<a|b>|; X only acts on sites, so
    the truncations are the same), and the final per-qubit <Z>;
  * the schedule: the parked circuit laid out again has the same length;
  * the added one-qubit gates and the share of the probably-|1> idle weight that the parked spans cover.
On one circuit per cell, the one with the most parked spans (--transpile): qiskit transpile with the fake backend's
target, optimization levels 1-3, the sent and the parked circuit, with and without a fence (a one-qubit barrier on each
side of the X, delay, X): the compiled CZ count, the X and delay counts, and P(|1>) of each delayed qubit during its
delay in the transpiled circuit (noise-free, MPS), i.e. whether the qubit is still parked once the transpiler has
merged the X into its neighbouring one-qubit gates.

usage: PYTHONPATH=<psf-os 0.3.3> python notes/ohm_idle_2026-11-23/park_try.py OUT.json [--schedule alap]
       [--jobs 10] [--transpile 12]
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ohm_idle as O  # noqa: E402


def overlap(a, b):
    """|<a|b>| of two MPS on the same chain."""
    e = np.ones((1, 1), dtype=complex)
    for x, y in zip(a.A, b.A):
        e = np.tensordot(np.tensordot(e, x.conj(), axes=(0, 0)), y, axes=([0, 1], [0, 1]))
    return float(abs(e[0, 0]))


def run(ops, n, chi, cutoff):
    m = O.MPS(n, chi, cutoff)
    for name, qs, p in ops:
        if name == "delay":
            continue
        if name == "cz":
            m.cz(min(qs))
        else:
            m.one(qs[0], O.gate(name, p))
    return m


def parked_ops(ops, spans, p1, x_dt, n):
    """The sent ops with X, delay, X before the op that ends each parkable span; [(q, begin, end, end op)]."""
    before, parked = {}, []
    for q in range(n):
        for b, e, i in spans[q]:
            if p1[(q, i)] > O.OVER and e - b >= 2 * x_dt + 2:
                before.setdefault(i, []).append((q, e - b - 2 * x_dt))
                parked.append((q, b, e, i))
    out = []
    for i, op in enumerate(ops):
        for q, d in before.get(i, ()):
            out += [("x", (q,), None), ("delay", (q,), d), ("x", (q,), None)]
        out.append(op)
    for q, d in before.get(None, ()):
        out += [("x", (q,), None), ("delay", (q,), d), ("x", (q,), None)]
    return out, parked


def durations_with_delay(timing, phys, ops):
    plain = [o for o in ops if o[0] != "delay"]
    dur_plain, meas = O.durations(timing, phys, plain)
    it = iter(dur_plain)
    return [int(o[2]) if o[0] == "delay" else next(it) for o in ops], meas


def study(dev, tag, how, chi, cutoff):
    from psf_os import device as Dv
    timing = Dv.fetch_fake(O.NIGHTS[dev][2]).timing
    ops, phys, chain, _ = O.load_circuit(dev, tag)
    n = len(chain)
    dur, meas = O.durations(timing, phys, ops)
    start, mstart = O.schedule(ops, dur, n, how)
    spans = O.idle_spans(ops, dur, start, mstart, n)
    queries = {(q, sp[2]) for q in range(n) for sp in spans[q]}
    p1, z0, _ = O.simulate(ops, n, queries, chi, cutoff)
    x_dt = int(timing["durations"]["x"][str(phys[0])])
    pops, parked = parked_ops(ops, spans, p1, x_dt, n)
    d2, _ = durations_with_delay(timing, phys, pops)
    s2, m2 = O.schedule(pops, d2, n, how)
    a, b = run(ops, n, chi, cutoff), run(pops, n, chi, cutoff)
    z1 = [1 - 2 * b.p1(q) for q in range(n)]
    hi_w = sum((2 * p1[(q, sp[2])] - 1) * (sp[1] - sp[0]) for q in range(n) for sp in spans[q]
               if p1[(q, sp[2])] > O.OVER)
    park_w = sum((2 * p1[(q, i)] - 1) * (e - bb - 2 * x_dt) for q, bb, e, i in parked)
    return dict(device=dev, tag=tag, schedule=how, parked_spans=len(parked),
                added_one_qubit_gates=2 * len(parked), sent_one_qubit_gates=sum(o[0] in ("x", "sx") for o in ops),
                overlap=overlap(a, b), final_z_change_max=float(np.max(np.abs(np.array(z1) - np.array(z0)))),
                length_dt=int(max(mstart)), parked_length_dt=int(max(m2)),
                gain_share_covered=(park_w / hi_w) if hi_w else None, gain_dt=float(hi_w), parked_gain_dt=float(park_w))


def work(args):
    return study(*args)


def qiskit_parked(dev, tag, how, fence):
    """(sent, parked) as qiskit circuits on the physical qubits."""
    from qiskit import QuantumCircuit, qpy
    from psf_os import device as Dv
    base, d, fake, _ = O.NIGHTS[dev]
    c = qpy.load(io.BytesIO(gzip.open(os.path.join(O.NB, base, d, "runs", f"p2d_{tag}.qpy.gz")).read()))[0]
    timing = Dv.fetch_fake(fake).timing
    ops, phys, chain, _ = O.load_circuit(dev, tag)
    n = len(chain)
    dur, _ = O.durations(timing, phys, ops)
    start, mstart = O.schedule(ops, dur, n, how)
    spans = O.idle_spans(ops, dur, start, mstart, n)
    queries = {(q, sp[2]) for q in range(n) for sp in spans[q]}
    p1, _, _ = O.simulate(ops, n, queries, 256, 1e-6)
    x_dt = int(timing["durations"]["x"][str(phys[0])])
    _, parked = parked_ops(ops, spans, p1, x_dt, n)
    before = {}
    for q, b, e, i in parked:
        before.setdefault(i, []).append((phys[q], e - b - 2 * x_dt))
    new = QuantumCircuit(*c.qregs, *c.cregs)
    k = 0                                         # index into ops (instructions other than measurements)

    def put(pq, dly):
        if fence:
            new.barrier(pq)
        new.x(pq)
        new.delay(dly, pq, unit="dt")
        new.x(pq)
        if fence:
            new.barrier(pq)
    done_end = False
    for ins in c.data:
        if ins.operation.name == "measure":
            if not done_end:
                for pq, dly in before.get(None, ()):
                    put(pq, dly)
                done_end = True
        else:
            for pq, dly in before.get(k, ()):
                put(pq, dly)
            k += 1
        new.append(ins.operation, ins.qubits, ins.clbits)
    return c, new, len(parked)


def p1_at_delays(tq, dev, tag):
    """P(|1>) of each delayed qubit during its delay in a transpiled circuit (noise-free, MPS)."""
    _, phys, chain, _ = O.load_circuit(dev, tag)
    pos = {p: k for k, p in enumerate(phys)}
    ops, marks = [], []
    for ins in tq.data:
        name = ins.operation.name
        if name in ("measure", "barrier"):
            continue
        qs = tuple(pos[tq.find_bit(q).index] for q in ins.qubits)
        if name == "delay":
            marks.append((qs[0], len(ops)))
            continue
        if name not in ("rz", "sx", "x", "cz"):
            raise SystemExit(f"{tag}: transpiled instruction {name} not handled")
        ops.append((name, qs, float(ins.operation.params[0]) if name == "rz" else None))
    got, _, _ = O.simulate(ops, len(chain), set(marks), 256, 1e-6)
    return [got[m] for m in marks]


def transpile_check(dev, tag, how):
    from qiskit import transpile
    from qiskit_ibm_runtime import fake_provider as FP
    be = getattr(FP, O.NIGHTS[dev][2])()
    rows = []
    for fence in (False, True):
        c, p, k = qiskit_parked(dev, tag, how, fence)
        for lvl in (1, 2, 3):
            r = dict(device=dev, tag=tag, fence=fence, level=lvl, parked_spans=k)
            for name, qc in (("sent", c), ("parked", p)):
                t0 = time.time()
                tq = transpile(qc, target=be.target, optimization_level=lvl, layout_method="trivial",
                               routing_method="none", seed_transpiler=1)
                ops = tq.count_ops()
                r[name] = dict(cz=int(ops.get("cz", 0)), x=int(ops.get("x", 0)), sx=int(ops.get("sx", 0)),
                               delay=int(ops.get("delay", 0)), seconds=round(time.time() - t0, 1))
                if name == "parked" and k:
                    pd = p1_at_delays(tq, dev, tag)
                    r["p1_during_delays_max"] = max(pd)  # parked: each qubit should be probably |0> here
            r["cz_same"] = r["sent"]["cz"] == r["parked"]["cz"]
            r["delays_kept"] = r["parked"]["delay"] == k
            rows.append(r)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--schedule", default="alap", choices=["asap", "alap"])
    ap.add_argument("--jobs", type=int, default=10)
    ap.add_argument("--chi", type=int, default=256)
    ap.add_argument("--cutoff", type=float, default=1e-6)
    ap.add_argument("--transpile", type=int, default=12, help="transpile check on this many circuits (one per cell)")
    a = ap.parse_args()
    if os.path.exists(a.out):
        raise SystemExit(f"STOP: {a.out} exists")
    sys.path.insert(0, O.NB)
    todo = O.tags(None)
    t0 = time.time()
    with Pool(a.jobs) as pool:
        res = list(pool.imap_unordered(work, [(d, t, a.schedule, a.chi, a.cutoff) for d, t in todo]))
    res.sort(key=lambda r: (r["device"], r["tag"]))
    print(f"parked {len(res)} circuits ({a.schedule}) in {time.time() - t0:.0f} s; overlap worst "
          f"{min(r['overlap'] for r in res):.12f}; final Z change worst {max(r['final_z_change_max'] for r in res):.1e}; "
          f"length changed in {sum(r['length_dt'] != r['parked_length_dt'] for r in res)}")
    most = {}                                     # per cell, the circuit with the most parked spans
    for r in res:
        k = (r["device"], r["tag"].rsplit("_", 1)[0])
        if k not in most or r["parked_spans"] > most[k][1]:
            most[k] = (r["tag"], r["parked_spans"])
    picks = sorted((k, v[0]) for k, v in most.items())[:a.transpile]
    with Pool(min(a.jobs, len(picks) or 1)) as pool:
        tr = [r for rows in pool.starmap(transpile_check, [(d, t, a.schedule) for (d, _), t in picks]) for r in rows]
    for r in tr:
        print(f"{r['device']:8} {r['tag']:10} fence {str(r['fence']):5} level {r['level']}: CZ {r['sent']['cz']} / "
              f"{r['parked']['cz']}, x {r['sent']['x']} / {r['parked']['x']}, delays {r['parked']['delay']} of "
              f"{r['parked_spans']}, P(|1>) during the delays at most {r.get('p1_during_delays_max', '-')}")
    json.dump(dict(note="trial outside psf-os; fake backends' durations, not the devices' records; noise-free checks",
                   schedule=a.schedule, chi=a.chi, cutoff=a.cutoff, circuits=res, transpile=tr),
              open(a.out, "w"), indent=1)
    print("wrote", a.out, f"{time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
