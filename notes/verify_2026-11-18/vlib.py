"""Independent reading of the 2026-11-18 records (home VS Claude, 2026-11-18; desk only). qiskit and numpy only: none
of home Claude's scoring code (gpu/*_night.py, psf_os.feedforward) is imported.

  load_job(folder)        {cell name: dict(counts, circuit, record)} from job/manifest.json, job/raw_counts.json and
                          runs/<name>.qpy / .json (manifest pubs[k].cell -> cells[cell].name; counts keys with clbit 0
                          rightmost)
  compact(qc)             the circuit on its touched qubits, in increasing physical order; returns (circuit, qubits)
  branch_dist(qc)         the exact distribution of the classical register of a dynamic circuit (measurements anywhere,
                          if_else on one bit with or without else), following every measurement branch with a state
                          vector (numpy)
  measured(qc)            [(clbit, physical qubit, order)] of every top-level measurement
  out_bit(qc)             the neuron chain's output bit read from the circuit: the bit of the one measurement of a
                          qubit measured exactly once that no conditional reads and that comes last among those
  p_bit(counts, bit)      share of shots with that bit 1, and the number of shots
"""
import json
import math
import os

import numpy as np


def load_job(folder):
    from qiskit import qpy
    job = os.path.join(folder, "job")
    man = json.load(open(os.path.join(job, "manifest.json")))
    raw = json.load(open(os.path.join(job, "raw_counts.json")))
    names = {c["cell"]: c["name"] for c in man["cells"]}
    out = {}
    for row in raw["rows"]:
        pub = man["pubs"][row["pub"]]
        name = names[pub["cell"]]
        rec_f = os.path.join(folder, "runs", name + ".json")
        rec = json.load(open(rec_f)) if os.path.exists(rec_f) else None
        qf = os.path.join(folder, "runs", name + ".qpy")
        circ = qpy.load(open(qf, "rb"))[pub.get("point", 0)] if os.path.exists(qf) else None
        out.setdefault(name, []).append(dict(counts=row["counts"], circuit=circ, record=rec, pub=row["pub"]))
    return {k: (v[0] if len(v) == 1 else v) for k, v in out.items()}, man


def _walk_q(qc):
    qs = set()

    def rec(c, qmap):
        for ins in c.data:
            q = [qmap[c.find_bit(x).index] for x in ins.qubits]
            if ins.operation.name != "barrier":
                qs.update(q)
            if ins.operation.name == "if_else":
                for b in ins.operation.blocks:
                    if b is not None:
                        rec(b, {j: q[j] for j in range(len(q))})
    rec(qc, {j: j for j in range(qc.num_qubits)})
    return qs


def compact(qc):
    from qiskit import QuantumCircuit, QuantumRegister
    act = sorted(_walk_q(qc))
    idx = {q: i for i, q in enumerate(act)}
    out = QuantumCircuit(QuantumRegister(len(act), "q"), *qc.cregs)
    for ins in qc.data:
        qs = [qc.find_bit(x).index for x in ins.qubits]
        if ins.operation.name == "barrier":
            qs = [q for q in qs if q in idx]
            if not qs:
                continue
            from qiskit.circuit import Barrier
            out.append(Barrier(len(qs)), [out.qubits[idx[q]] for q in qs])
            continue
        out.append(ins.operation, [out.qubits[idx[q]] for q in qs], ins.clbits)
    return out, act


def measured(qc):
    res = []
    for k, ins in enumerate(qc.data):
        if ins.operation.name == "measure":
            res.append((qc.find_bit(ins.clbits[0]).index, qc.find_bit(ins.qubits[0]).index, k))
    return res


def condition_bits(qc):
    bits = set()

    def rec(c, cmap):
        for ins in c.data:
            if ins.operation.name == "if_else":
                bits.add(cmap[c.find_bit(ins.operation.condition[0]).index])
                for b in ins.operation.blocks:
                    if b is not None:
                        rec(b, cmap)
    rec(qc, {j: j for j in range(qc.num_clbits)})
    return bits


def out_bit(qc):
    ms = measured(qc)
    per_q = {}
    for c, q, k in ms:
        per_q.setdefault(q, []).append((k, c))
    cond = condition_bits(qc)
    cands = [(v[0][0], v[0][1], q) for q, v in per_q.items() if len(v) == 1 and v[0][1] not in cond]
    if not cands:
        raise ValueError("no output bit")
    k, c, q = max(cands)
    return c, q


# ------------------------------------------------------------------------------------------------ exact branching

def _apply1(psi, n, q, U):
    psi = psi.reshape([2] * n)
    ax = n - 1 - q                                       # qubit q is axis n-1-q (little endian as Qiskit)
    psi = np.moveaxis(np.tensordot(U, psi, axes=([1], [ax])), 0, ax)
    return psi.reshape(-1)


def _apply2(psi, n, q0, q1, U):
    psi = psi.reshape([2] * n)
    a0, a1 = n - 1 - q0, n - 1 - q1
    U4 = U.reshape(2, 2, 2, 2)                           # (out q1, out q0, in q1, in q0) in Qiskit's matrix order
    psi = np.tensordot(U4, psi, axes=([2, 3], [a1, a0]))
    psi = np.moveaxis(psi, [0, 1], [a1, a0])
    return psi.reshape(-1)


def branch_dist(qc, tol=1e-15):
    """Exact distribution of the classical register: {bitstring c[n-1]..c[0]: p}."""
    from qiskit.quantum_info import Operator
    n, nc = qc.num_qubits, qc.num_clbits
    psi0 = np.zeros(2 ** n, dtype=complex)
    psi0[0] = 1.0
    branches = [(1.0, psi0, [0] * nc)]
    cache = {}

    def mat(op):
        key = (op.name, tuple(float(p) for p in op.params)) if all(isinstance(p, (int, float)) for p in op.params) \
            else None
        if key is not None and key in cache:
            return cache[key]
        m = Operator(op).data
        if key is not None:
            cache[key] = m
        return m

    def run(branches, circ, qmap, cmap):
        for ins in circ.data:
            op = ins.operation
            qs = [qmap[circ.find_bit(x).index] for x in ins.qubits]
            nm = op.name
            if nm in ("barrier", "delay", "id"):
                continue
            if nm == "measure":
                cb = cmap[circ.find_bit(ins.clbits[0]).index]
                q = qs[0]
                nb = []
                for w, psi, bits in branches:
                    t = psi.reshape([2] * n)
                    ax = n - 1 - q
                    for v in (0, 1):
                        sl = [slice(None)] * n
                        sl[ax] = 1 - v
                        ph = t.copy()
                        ph[tuple(sl)] = 0
                        pr = float(np.vdot(ph, ph).real)
                        if pr * w > tol:
                            b2 = list(bits)
                            b2[cb] = v
                            nb.append((w * pr, (ph / math.sqrt(pr)).reshape(-1), b2))
                branches = nb
                continue
            if nm == "if_else":
                cbit = cmap[circ.find_bit(op.condition[0]).index]
                val = int(op.condition[1])
                tb, fb = op.blocks[0], (op.blocks[1] if len(op.blocks) > 1 else None)
                yes = [b for b in branches if b[2][cbit] == val]
                no = [b for b in branches if b[2][cbit] != val]
                bm = lambda blk: {blk.find_bit(x).index: qs[j] for j, x in enumerate(blk.qubits)}
                bc = lambda blk: {blk.find_bit(x).index: cmap[circ.find_bit(ins.clbits[j]).index]
                                  for j, x in enumerate(blk.clbits)}
                if yes:
                    yes = run(yes, tb, bm(tb), bc(tb))
                if no and fb is not None:
                    no = run(no, fb, bm(fb), bc(fb))
                branches = yes + no
                continue
            U = mat(op)
            if len(qs) == 1:
                branches = [(w, _apply1(psi, n, qs[0], U), b) for w, psi, b in branches]
            elif len(qs) == 2:
                branches = [(w, _apply2(psi, n, qs[0], qs[1], U), b) for w, psi, b in branches]
            else:
                raise ValueError(f"{nm} on {len(qs)} qubits not handled")
        return branches

    branches = run(branches, qc, {j: j for j in range(n)}, {j: j for j in range(nc)})
    dist = {}
    for w, _, bits in branches:
        k = "".join(str(b) for b in bits[::-1])
        dist[k] = dist.get(k, 0.0) + w
    return dist


def p_bit_dist(dist, bit):
    return sum(p for k, p in dist.items() if k[len(k) - 1 - bit] == "1")


def p_bit(counts, bit):
    tot = sum(counts.values())
    ones = sum(v for k, v in counts.items() if k.replace(" ", "")[len(k.replace(" ", "")) - 1 - bit] == "1")
    return ones / tot, tot


def wls_slope(xs, ys, ses):
    w = np.array([1 / s ** 2 for s in ses])
    x, y = np.array(xs, float), np.array(ys, float)
    xb, yb = (w * x).sum() / w.sum(), (w * y).sum() / w.sum()
    sxx = (w * (x - xb) ** 2).sum()
    return float((w * (x - xb) * (y - yb)).sum() / sxx), float(math.sqrt(1 / sxx))


def ideal_chain(L, theta):
    """P(last output 1) when every neuron succeeds, from a plain statevector of the ideal chain (output 0 by RY(2q),
    output j by a controlled RY(2q) from output j-1; tan q = tan^2 theta), and the closed form sin(q)^(2L)."""
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    q = math.atan(math.tan(theta) ** 2)
    c = QuantumCircuit(L)
    c.ry(2 * q, 0)
    for j in range(1, L):
        c.cry(2 * q, j - 1, j)
    return float(Statevector(c).probabilities([L - 1])[1]), math.sin(q) ** (2 * L)


# ------------------------------------------------------------------------------------------------ packed circuits

def _walk_qc(qc):
    """(name, qubits, clbits incl. condition bit) of every instruction, blocks included, in top-circuit indices."""
    out = []

    def rec(c, qmap, cmap):
        for ins in c.data:
            op = ins.operation
            qs = [qmap[c.find_bit(x).index] for x in ins.qubits]
            cs = [cmap[c.find_bit(x).index] for x in ins.clbits]
            if op.name == "if_else":
                cs = cs + [cmap[c.find_bit(op.condition[0]).index]]
                out.append((op.name, qs, cs))
                for b in op.blocks:
                    if b is not None:
                        rec(b, {j: qs[j] for j in range(len(qs))},
                            {j: cmap[c.find_bit(x).index] for j, x in enumerate(ins.clbits)})
            else:
                out.append((op.name, qs, cs))
    rec(qc, {j: j for j in range(qc.num_qubits)}, {j: j for j in range(qc.num_clbits)})
    return out


def parts(qc):
    """Independent parts of a circuit read from its instructions alone: [(sorted qubits, sorted clbits)], joined by
    any instruction other than a barrier (blocks and condition bits included); also returns the barriers that would
    join two parts."""
    parent = {}

    def f(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    ins = _walk_qc(qc)
    for name, qs, cs in ins:
        if name == "barrier":
            continue
        ws = [("q", q) for q in qs] + [("c", c) for c in cs]
        for w in ws:
            f(w)
        for w in ws[1:]:
            a, b = f(ws[0]), f(w)
            if a != b:
                parent[a] = b
    groups = {}
    for w in list(parent):
        groups.setdefault(f(w), []).append(w)
    ps = sorted((sorted(i for t, i in g if t == "q"), sorted(i for t, i in g if t == "c")) for g in groups.values())
    owner = {}
    for k, (qs, cs) in enumerate(ps):
        for q in qs:
            owner[q] = k
    spanning = [qs for name, qs, cs in ins if name == "barrier" and len({owner.get(q) for q in qs} - {None}) > 1]
    return ps, spanning


def restrict(qc, qubits, clbits):
    """The instructions of qc on the given qubits / clbits (in that order) as a compact circuit; barriers cut to the
    set; an instruction straddling the set raises."""
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
    from qiskit.circuit import Barrier, IfElseOp
    qi = {q: k for k, q in enumerate(qubits)}
    ci = {c: k for k, c in enumerate(clbits)}
    out = QuantumCircuit(QuantumRegister(len(qubits), "q"), ClassicalRegister(max(len(clbits), 1), "c"))
    for ins in qc.data:
        op = ins.operation
        qs = [qc.find_bit(x).index for x in ins.qubits]
        cs = [qc.find_bit(x).index for x in ins.clbits]
        if op.name == "barrier":
            keep = [q for q in qs if q in qi]
            if keep:
                out.append(Barrier(len(keep)), [out.qubits[qi[q]] for q in keep])
            continue
        cond = qc.find_bit(op.condition[0]).index if op.name == "if_else" else None
        ws_q = [q in qi for q in qs]
        ws_c = [c in ci for c in cs + ([cond] if cond is not None else [])]
        if not any(ws_q) and not any(ws_c):
            continue
        if not all(ws_q) or not all(ws_c):
            raise ValueError(f"{op.name} straddles the set")
        if op.name == "if_else":
            op = IfElseOp((out.clbits[ci[cond]], op.condition[1]), op.blocks[0].copy(),
                          op.blocks[1].copy() if len(op.blocks) > 1 and op.blocks[1] is not None else None)
        out.append(op, [out.qubits[qi[q]] for q in qs], [out.clbits[ci[c]] for c in cs])
    return out


def marginal(counts, clbits):
    """Counts over the given clbits (new bit k = clbits[k])."""
    out = {}
    for key, v in counts.items():
        k = key.replace(" ", "")
        n = len(k)
        sub = "".join(k[n - 1 - b] for b in reversed(clbits))
        out[sub] = out.get(sub, 0) + v
    return out


def out_bit_general(qc):
    """The output bit: among bits of qubits measured exactly once that no conditional reads, the one whose qubit lies
    farthest (two-qubit gate graph, blocks included) from the qubit measured first; returns (clbit, qubit)."""
    ms = measured(qc)
    per_q = {}
    for c, q, k in ms:
        per_q.setdefault(q, []).append((k, c))
    cond = condition_bits(qc)
    cands = [(q, v[0][1]) for q, v in per_q.items() if len(v) == 1 and v[0][1] not in cond]
    if len(cands) == 1:
        return cands[0][1], cands[0][0]
    adj = {}
    for name, qs, cs in _walk_qc(qc):
        if len(qs) == 2 and name != "barrier":
            adj.setdefault(qs[0], set()).add(qs[1])
            adj.setdefault(qs[1], set()).add(qs[0])
    first = min(ms, key=lambda x: x[2])[1]
    dist, front = {first: 0}, [first]
    while front:
        nxt = []
        for q in front:
            for r in adj.get(q, ()):
                if r not in dist:
                    dist[r] = dist[q] + 1
                    nxt.append(r)
        front = nxt
    q, c = max(cands, key=lambda x: dist.get(x[0], -1))
    return c, q


def tries_bits(qc):
    """Per ancilla (a qubit measured more than once), its bits in order: the neuron's tries."""
    per_q = {}
    for c, q, k in measured(qc):
        per_q.setdefault(q, []).append((k, c))
    return [[c for _, c in sorted(v)] for q, v in sorted(per_q.items()) if len(v) > 1]
