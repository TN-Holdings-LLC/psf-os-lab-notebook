"""Fix the JIT schedule of the time-budget ledger into a circuit with delays (desk only, not declared; taken over at home
from the workplace VS request 17f, owner 17:18 JST).

For every top-level instruction of a compiled circuit, in order: the ledger's JIT start time s (prepare as late as
the next operation allows; measurements and decisions as early as possible) against the earliest start an
as-soon-as-possible executor would give it on its qubits; where s is later, a delay on that qubit holds it. Then an
ASAP executor reproduces the JIT schedule (up to the rounding of each delay to a multiple of GRAN dt).

Checks per circuit: (1) structure: with the delays removed, the same instructions in the same order on every qubit and
clbit as the original (so the noiseless distribution is the same: a delay is the identity noiselessly); (2) recount:
the ledger's ASAP wait of the pinned circuit against the JIT wait of the original.

usage: python notes/next_2026-11-17/pin_delay.py OUT [OUT ...] [--latency-us X]   (OUT: a build folder with job/)
Lengths: FakeMarrakesh medians (illustrative). No device error number is used. Not usable on a device as it stands:
psf-os's feed-forward entrance refuses 'delay', and whether IBM's dynamic circuits honour top-level delays between
mid-circuit measurements and conditionals exactly has not been checked here."""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "timebudget_2026-11-17"))
import ledger as LG  # noqa: E402

GRAN = 16                                              # delay granularity in dt (an assumption, stated)


def pin(qc, latency_us=0.0):
    from qiskit import QuantumCircuit
    from qiskit.circuit import Delay
    L = LG.lengths()
    dt = L["dt"]
    ins = LG._instructions(qc, latency_us * 1e-6, False)
    start, _ = LG._schedule(ins, qc.num_qubits, qc.num_clbits, "jit")
    out = qc.copy_empty_like()
    ready_q = [0.0] * qc.num_qubits
    ready_c = [0.0] * qc.num_clbits
    added = 0
    k = 0
    for inst in qc.data:
        qs, cs, kind, d, _, _ = ins[k]
        s = start[k]
        k += 1
        if kind != "barrier":
            for q in qs:
                gap = s - ready_q[q]
                if gap > 1e-12:
                    n = int(math.ceil(gap / dt / GRAN)) * GRAN
                    out.append(Delay(n, "dt"), [out.qubits[q]])
                    ready_q[q] += n * dt
                    added += 1
        out.append(inst.operation, inst.qubits, inst.clbits)
        e = max([ready_q[q] for q in qs] + [ready_c[c] for c in cs] + [0.0])
        if kind == "barrier":
            for q in qs:
                ready_q[q] = e
            continue
        for q in qs:
            ready_q[q] = e + d
        for c in cs:
            ready_c[c] = e + d
    return out, added


def same_structure(a, b):
    def seq(qc):
        per = {}
        for ins in qc.data:
            if ins.operation.name == "delay":
                continue
            key = (ins.operation.name, tuple(qc.find_bit(q).index for q in ins.qubits),
                   tuple(qc.find_bit(c).index for c in ins.clbits), tuple(map(str, getattr(ins.operation, "params", []))))
            for w in key[1]:
                per.setdefault(("q", w), []).append(key)
            for w in key[2]:
                per.setdefault(("c", w), []).append(key)
        return per
    return seq(a) == seq(b)


def main():
    from qiskit import qpy
    ap = argparse.ArgumentParser()
    ap.add_argument("outs", nargs="+")
    ap.add_argument("--latency-us", type=float, default=0.0)
    a = ap.parse_args()
    res = {}
    for out in a.outs:
        m = json.load(open(os.path.join(out, "job", "manifest.json")))
        cs = qpy.load(open(os.path.join(out, "job", "circuits.qpy"), "rb"))
        i = 0
        for cell in m["cells"]:
            for _ in range(cell["points"]):
                c = cs[i]
                i += 1
                if cell["role"] not in ("user", "off"):
                    continue
                p, added = pin(c, a.latency_us)
                asap0 = LG.ledger(c, a.latency_us, False)["wait_qus"]
                jit0 = LG.ledger(c, a.latency_us, "jit")["wait_qus"]
                asap1 = LG.ledger(p, a.latency_us, False)
                ok = same_structure(c, p)
                res[cell["name"]] = dict(asap=asap0, jit=jit0, pinned_asap=asap1["wait_qus"], T_us=asap1["T_us"],
                                         delays=added, structure_same=ok)
                print(f"{cell['name']:16s} wait q.us: ASAP {asap0:7.2f}  JIT {jit0:7.2f}  pinned (ASAP executor) "
                      f"{asap1['wait_qus']:7.2f}  T {asap1['T_us']:6.2f} us  delays {added:3d}  structure "
                      f"{'same' if ok else 'DIFFERENT'}")
    json.dump(res, open(os.path.join(HERE, f"pin_delay_latency{a.latency_us:g}us.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
