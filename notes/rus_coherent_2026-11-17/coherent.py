"""Repeat-until-success without mid-circuit measurements (workplace, 2026-11-17 design; desk only, nothing sent).

The owner's idea (2026-11-16 23:14 JST): no waiting between tries, only an entrance and an exit. Each try r gets its own
fresh ancilla a_r; try r runs coherently only when a_{r-1} is |1> (the previous try failed); every qubit is measured
once, at the end (deferred measurement). The joint distribution of (ancilla bits, last output) equals the
measure-and-feed-forward circuit psf_os.feedforward.rus_chain(L, theta, m) (checked here exactly, by a branching
simulation of the dynamic circuit against the statevector of the coherent one).

Three forms, each a line of L (m + 1) qubits placed by rule C (coupling graph and failed marks only, no search):
  naive    the retry block written as a generic controlled gate (Qiskit .control, the previous output's control kept)
           on the line [a_0 .. a_{m-1}, o] per neuron; two-qubit gates on non-neighbours routed by a fixed rule
           (move the first qubit along the line until it is next to the second; no search);
  zipper   (2b-1) the zipper line a_0, o, a_1, a_2, ... : before try r the output steps one place along the line
           (a SWAP with the fresh ancilla), so every gate of the try is on neighbours; within neuron j a retry is
           controlled by a_{r-1} only (a_{r-1} = 1 implies the previous output was 1, so that control is redundant:
           an identity of this circuit); exact gates (CRY = 2 CZ, SWAP = 3 CZ);
  zipper+  (2b-1 + 2b-2) the same line with gates that use what is known: a fresh ancilla is |0>, so its controlled
           preparation is RY(a) CX RY(-a) (1 CZ, exact on |0>); the ancilla's last controlled rotation is followed only
           by its measurement and its use as a control, so a CRY up to a diagonal phase is enough (1 CZ); the output's
           step onto the fresh |0> is a move of 2 CX, not a SWAP of 3.
usage: PYTHONPATH=<psf-os>:<notebook>:<notebook>/gpu python notes/rus_coherent_2026-11-17/coherent.py DEVDIR
"""
import itertools
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
THETA = 1.1


# ------------------------------------------------------------------------------------------------ exact simulation

def branch_distribution(qc):
    """Exact distribution of the classical register of a dynamic circuit (mid-circuit measurements, if_test on one
    bit, no else), by following every measurement branch with a statevector. Returns {bitstring c[n-1]..c[0]: p}."""
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    nq, nc = qc.num_qubits, qc.num_clbits
    branches = [(1.0, Statevector.from_label("0" * nq), [0] * nc)]

    def apply(branches, circ, qmap, cmap):
        for ins in circ.data:
            op = ins.operation
            qs = [qmap[circ.find_bit(x).index] for x in ins.qubits]
            if op.name == "barrier":
                continue
            if op.name == "measure":
                cb = cmap[circ.find_bit(ins.clbits[0]).index]
                new = []
                for p, sv, bits in branches:
                    probs = sv.probabilities([qs[0]])
                    for v in (0, 1):
                        if probs[v] < 1e-15:
                            continue
                        proj = np.zeros((2, 2))
                        proj[v, v] = 1
                        s2 = sv.evolve(proj, [qs[0]])
                        s2 = Statevector(s2.data / math.sqrt(probs[v]))
                        b2 = list(bits)
                        b2[cb] = v
                        new.append((p * probs[v], s2, b2))
                branches = new
                continue
            if op.name == "if_else":
                bit, val = op.condition
                cb = cmap[circ.find_bit(bit).index]
                body = op.blocks[0]
                inner_q = {j: qs[j] for j in range(len(qs))}
                inner_c = {j: cmap[circ.find_bit(x).index] for j, x in enumerate(ins.clbits)}
                fire = [b for b in branches if b[2][cb] == int(val)]
                rest = [b for b in branches if b[2][cb] != int(val)]
                branches = rest + apply(fire, body, inner_q, inner_c)
                continue
            sub = QuantumCircuit(len(qs))
            sub.append(op, list(range(len(qs))))
            branches = [(p, sv.evolve(sub, qs), bits) for p, sv, bits in branches]
        return branches

    out = {}
    for p, _, bits in apply(branches, qc, {j: j for j in range(nq)}, {j: j for j in range(nc)}):
        key = "".join(str(b) for b in reversed(bits))
        out[key] = out.get(key, 0.0) + p
    return out


def coherent_distribution(qc, measured):
    """measured: [(qubit, bit)]; the distribution of those bits from the statevector (no mid-circuit measurement)."""
    from qiskit.quantum_info import Statevector
    sv = Statevector(qc.remove_final_measurements(inplace=False))
    qs = [q for q, _ in measured]
    probs = sv.probabilities(qs)          # index bit k <-> qs[k]
    nb = max(b for _, b in measured) + 1
    out = {}
    for idx, p in enumerate(probs):
        if p < 1e-15:
            continue
        bits = [0] * nb
        for k, (_, b) in enumerate(measured):
            bits[b] = (idx >> k) & 1
        key = "".join(str(x) for x in reversed(bits))
        out[key] = out.get(key, 0.0) + p
    return out


def tvd(p, q):
    return 0.5 * sum(abs(p.get(k, 0) - q.get(k, 0)) for k in set(p) | set(q))


# ------------------------------------------------------------------------------------------------ the coherent forms

def _q(theta):
    return math.atan(math.tan(theta) ** 2)


def _cry_exact(qc, phi, c, t):
    qc.cry(phi, c, t)


def _prep_from_zero(qc, phi, c, t):
    """Controlled RY(phi) on a target known to be |0>: RY(a) CX RY(-a) with a = (pi - phi) / 2 (exact on |0>)."""
    a = (math.pi - phi) / 2
    qc.ry(a, t)
    qc.cx(c, t)
    qc.ry(-a, t)


def _cry_up_to_phase(qc, phi, c, t):
    """Controlled RY(phi) up to a Z on the target when the control is 1 (a diagonal phase): RY(a) CX RY(-a) with
    a = (pi + phi) / 2. Allowed only where the target is afterwards measured or used as a control."""
    a = (math.pi + phi) / 2
    qc.ry(a, t)
    qc.cx(c, t)
    qc.ry(-a, t)


def _move(qc, src, dst):
    """The state of src onto dst, which is |0>; src left in |0> (2 CX)."""
    qc.cx(src, dst)
    qc.cx(dst, src)


def zipper(L, theta, m, plus=False, tries=None):
    """(circuit on L (m + 1) line positions, measured [(position, bit)]). Neuron j's block starts at base = j (m + 1):
    a_0 at base, o at base + 1, fresh ancillas after it; o steps one place before each retry. tries: run only the
    first `tries` tries per neuron (the others' ancillas stay |0> and are measured as 0): tries=1 is the arm without
    retries on the same line."""
    tries = m if tries is None else tries
    if tries != m and L > 1:
        raise ValueError("tries < m only for L = 1 (the next neuron's control must stand next to its block)")
    from qiskit import QuantumCircuit
    n = L * (m + 1)
    qc = QuantumCircuit(n)
    measured = []
    prep = _prep_from_zero if plus else _cry_exact
    fin = _cry_up_to_phase if plus else _cry_exact
    for j in range(L):
        base = j * (m + 1)
        ctrl = base - 1 if j > 0 else None            # the previous output ends next to this block
        a, o = base, base + 1
        # try 0
        if ctrl is None:
            qc.ry(2 * theta, a)
        else:
            prep(qc, 2 * theta, ctrl, a)
        qc.cy(a, o)
        qc.sdg(a)
        if ctrl is None:
            qc.ry(-2 * theta, a)
        else:
            fin(qc, -2 * theta, ctrl, a)
        measured.append((a, j * m))
        # retries
        for r in range(1, tries):
            prev, here, nxt = base + r - 1, base + r, base + r + 1      # a_{r-1}, o, fresh |0>
            qc.cry(math.pi / 2, prev, here)                              # undo on the output (exact: o is live)
            if plus:
                _move(qc, here, nxt)
            else:
                qc.swap(here, nxt)
            ar, o = here, nxt
            prep(qc, 2 * theta, prev, ar)
            qc.cy(ar, o)
            qc.sdg(ar)
            fin(qc, -2 * theta, prev, ar)
            measured.append((ar, j * m + r))
        for r in range(tries, m):
            measured.append((base + r + 1, j * m + r))          # untouched fresh ancillas (read 0)
    o_last = (L - 1) * (m + 1) + tries                           # where the last output stands after its tries
    measured.append((o_last, L * m))
    return qc, measured


def naive(L, theta, m):
    """Logical circuit (not yet on a line): per neuron qubits [a_0 .. a_{m-1}, o]; retry r = the generic controlled
    version (on a_{r-1}) of [RY(pi/2) on o, the attempt with the previous output's control], as written."""
    from qiskit import QuantumCircuit
    n = L * (m + 1)
    qc = QuantumCircuit(n)
    measured = []

    def attempt(c, a, o, ctrl):
        if ctrl is None:
            c.ry(2 * theta, a)
        else:
            c.cry(2 * theta, ctrl, a)
        c.cy(a, o)
        c.sdg(a)
        if ctrl is None:
            c.ry(-2 * theta, a)
        else:
            c.cry(-2 * theta, ctrl, a)
    for j in range(L):
        base = j * (m + 1)
        o = base + m
        ctrl = base - 1 if j > 0 else None
        attempt(qc, base, o, ctrl)
        measured.append((base, j * m))
        for r in range(1, m):
            qs = [o, base + r] + ([ctrl] if ctrl is not None else [])
            blk = QuantumCircuit(len(qs))
            blk.ry(math.pi / 2, 0)
            attempt(blk, 1, 0, 2 if ctrl is not None else None)
            g = blk.to_gate(label="retry").control(1)
            qc.append(g, [base + r - 1] + qs)
            measured.append((base + r, j * m + r))
    measured.append((L * (m + 1) - 1, L * m))
    return qc, measured


def route_line(qc):
    """Fixed-rule routing on a line (no search): before each two-qubit gate on non-neighbours, move its first qubit
    along the line by SWAPs until it is next to the second. Input: a circuit of one- and two-qubit gates. Returns
    (routed circuit on line positions, final {logical: position}, swaps)."""
    from qiskit import QuantumCircuit
    n = qc.num_qubits
    pos = {q: q for q in range(n)}
    at = {q: q for q in range(n)}
    out = QuantumCircuit(n)
    swaps = 0
    for ins in qc.data:
        qs = [qc.find_bit(x).index for x in ins.qubits]
        if ins.operation.name == "barrier":
            continue
        if len(qs) == 2:
            a, b = qs
            while abs(pos[a] - pos[b]) > 1:
                p = pos[a]
                p2 = p + (1 if pos[b] > p else -1)
                other = at[p2]
                out.swap(p, p2)
                swaps += 1
                pos[a], pos[other] = p2, p
                at[p], at[p2] = other, a
        out.append(ins.operation, [out.qubits[pos[q]] for q in qs])
    return out, pos, swaps


def to_basis(qc):
    from qiskit import transpile
    return transpile(qc, basis_gates=["cz", "rz", "sx", "x"], optimization_level=1, seed_transpiler=0)


def on_device(dev, line_circ, measured_pos):
    """Place the line circuit on the rule-C chain and compile with psf-os's map-free pass manager (no routing)."""
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
    from psf_os import chain as CH
    from psf_os import feedforward as FF
    pl = CH.place(dev, line_circ.num_qubits)
    chain = pl["chain"]
    nb = max(b for _, b in measured_pos) + 1
    full = QuantumCircuit(QuantumRegister(dev.num_qubits, "q"), ClassicalRegister(nb, "c"))
    full.compose(line_circ, qubits=chain, inplace=True)
    for p, b in measured_pos:
        full.measure(chain[p], b)
    comp = FF.Compiler(dev)
    c = comp.run(full)
    return c, chain


def stats(c):
    from psf_os import feedforward as FF
    names = [n for n, _ in FF.walk(c)]
    return dict(cz=names.count("cz"), cz_layers=c.depth(lambda i: i.operation.name == "cz"), depth=c.depth(),
                measure=names.count("measure"), mid=names.count("measure") - 1 if "if_else" in names else 0,
                conditionals=names.count("if_else"))


DUR = dict(cz=68e-9, sx=36e-9, x=36e-9, rz=0.0, measure=2.584e-6, barrier=0.0, delay=0.0)


def duration(c, latency=0.0):
    """Longest path with fixed per-instruction durations (illustrative, see README), a conditional block counted as
    its body plus `latency`. Returns seconds."""
    t = {}

    def run(circ, qmap, start):
        for ins in circ.data:
            qs = [qmap[circ.find_bit(x).index] for x in ins.qubits]
            name = ins.operation.name
            t0 = max([start.get(q, 0.0) for q in qs] or [0.0])
            if name == "if_else":
                inner = {q: t0 + latency for q in qs}
                run(ins.operation.blocks[0], {j: qs[j] for j in range(len(qs))}, inner)
                for q in qs:
                    start[q] = inner[q]
                continue
            d = DUR.get(name, 0.0)
            for q in qs:
                start[q] = t0 + d
    run(c, {j: j for j in range(c.num_qubits)}, t)
    return max(t.values()) if t else 0.0


def main(devdir):
    from psf_os import device as Dv
    from psf_os import feedforward as FF
    sys.path.insert(0, os.path.join(HERE, "..", "..", "gpu"))
    import rus3_night as R3
    dev = Dv.Device.load(devdir)
    res = dict(device=dev.name, record=dev.source, theta=THETA, rows=[], checks=[])
    for L in (1, 2, 3):
        for m in (2, 3):
            ref = branch_distribution(FF.rus_chain(L, THETA, m)[0])
            row = dict(L=L, m=m)
            for form in ("naive", "zipper", "zipper+"):
                if form == "naive":
                    lq, meas = naive(L, THETA, m)
                    base = to_basis(lq)
                    line, pos, swaps = route_line(base)
                    mp = [(pos[q], b) for q, b in meas]
                    dist = coherent_distribution(lq, meas)
                    row["naive_all_to_all_cz"] = base.count_ops().get("cz", 0)
                else:
                    line, mp = zipper(L, THETA, m, plus=(form == "zipper+"))
                    swaps = (m - 1) * L
                    dist = coherent_distribution(line, mp)
                    line = to_basis(line)
                d = tvd(ref, dist)
                res["checks"].append(dict(L=L, m=m, form=form, tvd_to_rus_chain=d))
                c, chain = on_device(dev, line, mp)
                st = stats(c)
                st.update(steps_of_the_output=swaps, chain=chain, seconds_illustrative=duration(c))
                row[form] = st
            # tonight's third design (mid-circuit measurements), m as given
            qc, spec = R3.chain(L, THETA, m=m)
            pl = FF.place(dev, 2 * L)
            c = FF.Compiler(dev).run(FF.on_device(FF.lower(qc), pl["chain"], dev.num_qubits))
            st = stats(c)
            st["mid"] = L * m
            st["seconds_illustrative_no_latency"] = duration(c)
            row["rd_mid_circuit"] = st
            res["rows"].append(row)
            print(f"L {L} m {m}: " + "; ".join(
                f"{f} CZ {row[f]['cz']} layers {row[f]['cz_layers']} depth {row[f]['depth']}"
                for f in ("naive", "zipper", "zipper+", "rd_mid_circuit"))
                + f" | naive all-to-all CZ {row['naive_all_to_all_cz']} | rd mid {row['rd_mid_circuit']['mid']}",
                flush=True)
    worst = max(x["tvd_to_rus_chain"] for x in res["checks"])
    print(f"distribution against rus_chain: worst total variation {worst:.2e} over {len(res['checks'])} cases")
    json.dump(res, open(os.path.join(HERE, "coherent.json"), "w"), indent=1, default=str)


if __name__ == "__main__":
    main(sys.argv[1])
