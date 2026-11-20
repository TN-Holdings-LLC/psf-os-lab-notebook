"""Independent count of the waits in sent IPE circuits (home VS, 2026-11-21): qiskit / numpy only, no psf-os and no
notebook tool. For every wait (a measure or an if_else at the top level) and every other active qubit q:
  - floating ops: ops on q that are neither ancestors nor descendants of the wait (they may run during it);
    fenced = no floating op on any waiting qubit;
  - the state of q during the wait, exactly, in every classical branch: at the cut just before the wait, and after
    each floating op; carrier = q not in a basis state in some branch; excited = expected P(q = 1).
Also the exact distribution of the classical register (branching statevector) for the noiseless comparison.
usage: python waits.py OUT [OUT ...]  -> prints a summary and writes waits.json in the cwd"""
import json
import sys
from collections import defaultdict

import numpy as np
from qiskit import qpy
from qiskit.circuit import Clbit, ClassicalRegister
from qiskit.quantum_info import Operator, Statevector

EPS = 1e-9


def load(out):
    man = json.load(open(f"{out}/job/manifest.json"))
    circs = qpy.load(open(f"{out}/job/circuits.qpy", "rb"))
    cells = {c["cell"]: c["name"] for c in man["cells"]}
    idx = {cells[p["cell"]]: i for i, p in enumerate(man["pubs"]) if p["point"] == 0}
    return {n: circs[i] for n, i in idx.items()}


def flatten(qc):
    """Top-level instructions as (name, op, qubits, clbits) with outer indices."""
    out = []
    for ins in qc.data:
        out.append((ins.operation.name, ins.operation, [qc.find_bit(q).index for q in ins.qubits],
                    [qc.find_bit(c).index for c in ins.clbits]))
    return out


def active_qubits(ops):
    return sorted({q for n, _, qs, _ in ops if n not in ("barrier", "delay") for q in qs})


def cond_true(op, cl, qc_bits):
    c = op.condition
    if isinstance(c, tuple):
        tgt, val = c
        if isinstance(tgt, Clbit):
            return cl[qc_bits(tgt)] == int(val)
        if isinstance(tgt, ClassicalRegister):
            v = sum(cl[qc_bits(b)] << k for k, b in enumerate(tgt))
            return v == int(val)
    raise NotImplementedError(f"condition {c!r}")


class Sim:
    """Branching statevector over the active qubits."""

    def __init__(self, qc, act):
        self.qc, self.act = qc, act
        self.pos = {q: k for k, q in enumerate(act)}
        self.nc = qc.num_clbits

    def start(self):
        return [(1.0, Statevector.from_label("0" * len(self.act)), (0,) * self.nc)]

    def apply(self, branches, item):
        name, op, qs, cs = item
        if name in ("barrier", "delay"):
            return branches
        if name == "measure":
            out = []
            for p, sv, cl in branches:
                k = self.pos[qs[0]]
                pr = sv.probabilities([k])
                for v in (0, 1):
                    if pr[v] < 1e-14:
                        continue
                    proj = np.zeros((2, 2))
                    proj[v, v] = 1
                    nsv = sv.evolve(Operator(proj), [k])
                    nsv = Statevector(nsv.data / np.sqrt(pr[v]))
                    ncl = list(cl)
                    ncl[cs[0]] = v
                    out.append((p * pr[v], nsv, tuple(ncl)))
            return out
        if name == "reset":
            raise NotImplementedError("reset")
        if name == "if_else":
            out = []
            for br in branches:
                p, sv, cl = br
                taken = cond_true(op, cl, lambda b: self.qc.find_bit(b).index)
                body = op.blocks[0] if taken else (op.blocks[1] if len(op.blocks) > 1 else None)
                sub = [br]
                if body is not None:
                    for ins in body.data:
                        bq = [qs[body.find_bit(q).index] for q in ins.qubits]
                        bc = [cs[body.find_bit(c).index] for c in ins.clbits]
                        sub = self.apply(sub, (ins.operation.name, ins.operation, bq, bc))
                out.extend(sub)
            return out
        mat = Operator(op)
        return [(p, sv.evolve(mat, [self.pos[q] for q in qs]), cl) for p, sv, cl in branches]

    def run(self, ops, subset=None):
        br = self.start()
        for i, it in enumerate(ops):
            if subset is None or i in subset:
                br = self.apply(br, it)
        return br


def deps(ops):
    """Direct predecessors: the last earlier op sharing a qubit or a clbit."""
    n = len(ops)
    anc = [set() for _ in range(n)]
    last_q, last_c = {}, {}
    for i, (_, _, qs, cs) in enumerate(ops):
        for q in qs:
            if q in last_q:
                anc[i] |= {last_q[q]} | anc[last_q[q]]
            last_q[q] = i
        for c in cs:
            for j in last_c.get(c, []):
                anc[i] |= {j} | anc[j]
            last_c.setdefault(c, []).append(i)
    desc = [set() for _ in range(n)]
    for i in range(n):
        for j in anc[i]:
            desc[j].add(i)
    return anc, desc


def p1_stats(branches, k):
    carrier, exc = False, 0.0
    for p, sv, _ in branches:
        if p < 1e-12:
            continue
        r = sv.probabilities([k])[1]
        if EPS < r < 1 - EPS:
            carrier = True
        exc += p * r
    return carrier, exc


def analyse(qc):
    ops = flatten(qc)
    act = active_qubits(ops)
    sim = Sim(qc, act)
    anc, desc = deps(ops)
    waits = []
    for w, (name, _, qs, _) in enumerate(ops):
        if name not in ("measure", "if_else"):
            continue
        for q in act:
            if q in qs:
                continue
            wire = [i for i, it in enumerate(ops) if q in it[2] and it[0] not in ("barrier", "delay")]
            floating = [i for i in wire if i not in anc[w] and i not in desc[w]]
            br = sim.run(ops, anc[w])
            car0, exc0 = p1_stats(br, sim.pos[q])
            car, exc_max = car0, exc0
            for f in floating:
                br = sim.run(ops, anc[w] | anc[f] | {f})
                c, e = p1_stats(br, sim.pos[q])
                car |= c
                exc_max = max(exc_max, e)
            waits.append(dict(at=w, kind=name, qubit=q, floating=len(floating), carrier_cut=car0, carrier_any=car,
                              excited_cut=exc0, excited_max=exc_max))
    dist = defaultdict(float)
    for p, _, cl in sim.run(ops):
        dist["".join(str(b) for b in reversed(cl))] += p
    return waits, dict(dist), act


def main():
    res = {}
    for out in sys.argv[1:]:
        circs = load(out)
        for name, qc in sorted(circs.items()):
            if not name.startswith("ff_") or name.endswith(("_off", "_floor")):
                continue
            w, dist, act = analyse(qc)
            res[f"{out.rstrip('/').split('/')[-1]}:{name}"] = dict(waits=w, dist=dist, active=act)
    json.dump(res, open("waits.json", "w"), indent=1)
    # summary per build and form
    agg = defaultdict(lambda: dict(items=0, waits=0, floating=0, carriers=0, carriers_cut=0, exc=0.0, exc_max=0.0,
                                   meas=0, cond=0))
    for key, r in res.items():
        b, nm = key.split(":")
        form = nm[3:5]
        a = agg[(b, form)]
        a["items"] += 1
        for x in r["waits"]:
            a["waits"] += 1
            a["meas" if x["kind"] == "measure" else "cond"] += 1
            a["floating"] += x["floating"] > 0
            a["carriers"] += x["carrier_any"]
            a["carriers_cut"] += x["carrier_cut"]
            a["exc"] += x["excited_cut"]
            a["exc_max"] += x["excited_max"]
    for (b, f), a in sorted(agg.items()):
        print(f"{b} {f}: items {a['items']}, waits {a['waits']} (reads {a['meas']}, conditionals {a['cond']}); "
              f"waits with floating ops {a['floating']}; carriers (any point) {a['carriers']}, at the cut "
              f"{a['carriers_cut']}; excited sum at the cut {a['exc']:.3f}, at most {a['exc_max']:.3f}")


if __name__ == "__main__":
    main()
