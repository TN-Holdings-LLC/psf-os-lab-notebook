"""Independent check of the decoy job (workplace VS, 2026-11-20; author The Architect). qiskit, qiskit-aer and numpy
only: no psf-os, no notebook scorer. Reads the built job (job/circuits.qpy, the per-arm runs/*.qpy only to name the
job's circuits) and the device record's coupling map (no calibration number is read). No device.

  1. which circuit is which: every job circuit matched to one runs/*.qpy by equality
  2. per bundle circuit, the independent parts (qubits joined by multi-qubit gates), their qubits and clbits
     (measured and conditioned on): Z's bits first (0..4) in D1 and last (10..14) in D2; A [0-3], B [5-8], Z [11-14]
  3. per packed part against its single (A and B against sa / sb ff, Z against sz off): the same instructions in the
     same order on relabelled wires (qubits and clbits by rank), conditional blocks compared recursively
  4. coupling distance between the parts' qubits on the device's coupler graph (working and failed couplers)
  5. noiseless value of rd2's ff and off arms by sampling the single circuits (2 000 000 shots, statevector), as the
     share of shots whose output bit reads 0 ("read flipped")

  python decoy_check.py OUT DEVDIR
"""
import collections
import glob
import json
import os
import sys

from qiskit import QuantumCircuit, qpy
from qiskit_aer import AerSimulator


def load(p):
    with open(p, "rb") as f:
        return qpy.load(f)


def parts(qc):
    """Independent parts: union-find over qubits joined by any multi-qubit instruction (blocks included)."""
    par = {q: q for q in range(qc.num_qubits)}

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    def walk(c, qmap):
        for ins in c.data:
            qs = [qmap[c.find_bit(q).index] for q in ins.qubits]
            if ins.operation.name == "barrier":
                continue
            for a in qs[1:]:
                par[find(a)] = find(qs[0])
            for blk in getattr(ins.operation, "blocks", ()):
                walk(blk, {blk.find_bit(bq).index: qs[i] for i, bq in enumerate(blk.qubits)})

    walk(qc, {i: i for i in range(qc.num_qubits)})
    used = set()
    clb = collections.defaultdict(set)

    def touch(c, qmap, cmap):
        for ins in c.data:
            if ins.operation.name == "barrier":
                continue
            qs = [qmap[c.find_bit(q).index] for q in ins.qubits]
            cs = [cmap[c.find_bit(b).index] for b in ins.clbits]
            used.update(qs)
            cond = getattr(ins.operation, "condition", None)
            cbits = []
            if cond is not None:
                tgt = cond[0]
                bits = [tgt] if not hasattr(tgt, "__len__") else list(tgt)
                cbits = [cmap[c.find_bit(b).index] for b in bits]
            root = find(qs[0]) if qs else None
            if root is not None:
                clb[root].update(cs + cbits)
            for blk in getattr(ins.operation, "blocks", ()):
                touch(blk, {blk.find_bit(bq).index: qs[i] for i, bq in enumerate(blk.qubits)},
                      {blk.find_bit(bb).index: cs[i] for i, bb in enumerate(blk.clbits)})

    touch(qc, {i: i for i in range(qc.num_qubits)}, {i: i for i in range(qc.num_clbits)})
    groups = collections.defaultdict(list)
    for q in sorted(used):
        groups[find(q)].append(q)
    return [(sorted(qs), sorted(clb[r])) for r, qs in groups.items()]


def signature(qc, qubits, clbits):
    """The instruction sequence on the given wires, wires relabelled by rank; conditions and blocks included."""
    qr = {q: k for k, q in enumerate(sorted(qubits))}
    cr = {c: k for k, c in enumerate(sorted(clbits))}
    out = []

    def rec(c, qmap, cmap, depth):
        for ins in c.data:
            if ins.operation.name == "barrier":
                continue
            qs = [qmap[c.find_bit(q).index] for q in ins.qubits]
            if not set(qs) & set(qubits):
                continue
            cs = [cmap[c.find_bit(b).index] for b in ins.clbits]
            op = ins.operation
            cond = getattr(op, "condition", None)
            ctext = None
            if cond is not None:
                tgt = cond[0]
                bits = [tgt] if not hasattr(tgt, "__len__") else list(tgt)
                ctext = (tuple(cr[cmap[c.find_bit(b).index]] for b in bits), int(cond[1]))
            params = tuple(round(float(p), 12) for p in op.params if isinstance(p, (int, float)))
            out.append((depth, op.name, tuple(qr[q] for q in qs), tuple(cr[x] for x in cs), params, ctext))
            for bi, blk in enumerate(getattr(op, "blocks", ())):
                out.append((depth + 1, f"block{bi}"))
                rec(blk, {blk.find_bit(bq).index: qs[i] for i, bq in enumerate(blk.qubits)},
                    {blk.find_bit(bb).index: cs[i] for i, bb in enumerate(blk.clbits)}, depth + 1)

    rec(qc, {i: i for i in range(qc.num_qubits)}, {i: i for i in range(qc.num_clbits)}, 0)
    return out


def distance(couplers, A, B):
    adj = collections.defaultdict(set)
    for a, b in couplers:
        adj[a].add(b)
        adj[b].add(a)
    seen = {q: 0 for q in A}
    fr = list(A)
    while fr:
        nf = []
        for q in fr:
            for r in adj[q]:
                if r not in seen:
                    seen[r] = seen[q] + 1
                    nf.append(r)
        fr = nf
    return min(seen.get(b, 10 ** 9) for b in B)


def restrict(qc, qubits, clbits):
    """The part alone as a small circuit (for sampling)."""
    qr = {q: k for k, q in enumerate(sorted(qubits))}
    cr = {c: k for k, c in enumerate(sorted(clbits))}
    small = QuantumCircuit(len(qr), len(cr))

    def rec(c, qmap, cmap, tgt):
        for ins in c.data:
            if ins.operation.name == "barrier":
                continue
            qs = [qmap[c.find_bit(q).index] for q in ins.qubits]
            if not set(qs) <= set(qubits):
                continue
            cs = [cmap[c.find_bit(b).index] for b in ins.clbits]
            op = ins.operation
            if op.name == "if_else":
                cond = op.condition
                bits = [cond[0]] if not hasattr(cond[0], "__len__") else list(cond[0])
                cb = [cr[cmap[c.find_bit(b).index]] for b in bits]
                cond2 = ((tgt.clbits[cb[0]]) if len(cb) == 1 else None, int(cond[1]))
                if cond2[0] is None:
                    raise SystemExit("register conditions are not handled here")
                tb = op.blocks[0]
                with tgt.if_test(cond2) as else_:
                    rec(tb, {tb.find_bit(bq).index: qs[i] for i, bq in enumerate(tb.qubits)},
                        {tb.find_bit(bb).index: cs[i] for i, bb in enumerate(tb.clbits)}, tgt)
                if len(op.blocks) > 1 and op.blocks[1] is not None and len(op.blocks[1].data):
                    eb = op.blocks[1]
                    with else_:
                        rec(eb, {eb.find_bit(bq).index: qs[i] for i, bq in enumerate(eb.qubits)},
                            {eb.find_bit(bb).index: cs[i] for i, bb in enumerate(eb.clbits)}, tgt)
                continue
            tgt.append(op, [tgt.qubits[qr[q]] for q in qs], [tgt.clbits[cr[x]] for x in cs])

    rec(qc, {i: i for i in range(qc.num_qubits)}, {i: i for i in range(qc.num_clbits)}, small)
    return small


def main():
    out, devdir = sys.argv[1], sys.argv[2]
    job = load(os.path.join(out, "job", "circuits.qpy"))
    runs = {os.path.basename(p)[:-4]: load(p)[0] for p in glob.glob(os.path.join(out, "runs", "*.qpy"))}
    name = {}
    for k, c in enumerate(job):
        hit = [n for n, r in runs.items() if r == c]
        name[k] = hit[0] if len(hit) == 1 else f"?{hit}"
    print(f"1. job circuits {len(job)}; named: {sorted(name.values())}")
    by = {v: job[k] for k, v in name.items()}
    dev = json.load(open(os.path.join(devdir, "device.json")))
    allc = dev["couplers"] + dev.get("failed_couplers", [])
    ok = True
    want = {"A": [0, 1, 2, 3], "B": [5, 6, 7, 8], "Z": [11, 12, 13, 14]}
    zbits = {"D0": None, "D1": list(range(0, 5)), "D2": list(range(10, 15))}
    singles = {}
    for s, arm in (("sa", "ff"), ("sb", "ff"), ("sz", "off")):
        c = by[f"ff_{s}" + ("" if arm == "ff" else "_off")]
        (qs, cs), = parts(c)
        singles[s] = (c, qs, cs)
    print("2./3. parts per bundle arm (qubits; clbits) and the same instructions as the single:")
    for b in ("D0", "D1", "D2"):
        for arm in ("", "_off", "_floor"):
            c = by[f"ff_{b}{arm}"]
            ps = parts(c)
            desc = []
            for qs, cs in ps:
                role = next((k for k, v in want.items() if v == qs), "?")
                ref = None
                if arm == "":
                    ref = {"A": "sa", "B": "sb", "Z": "sz"}[role] if role != "?" else None
                same = None
                if ref:
                    rc, rq, rcs = singles[ref]
                    same = signature(c, qs, cs) == signature(rc, rq, rcs)
                    ok &= bool(same)
                desc.append(f"{role} q{qs[0]}-{qs[-1]} bits {cs[0]}..{cs[-1]}" + ("" if same is None else f" same-as-{ref} {same}"))
                if role == "?":
                    ok = False
                if role == "Z" and arm == "" and zbits[b] is not None:
                    zok = cs == zbits[b]
                    ok &= zok
                    desc[-1] += f" (Z bits as declared: {zok})"
            print(f"   {b}{arm or ' ff'}: " + "; ".join(desc))
    dz = distance(allc, want["B"], want["Z"])
    da = distance(allc, want["A"], want["B"])
    print(f"4. coupling distance (working and failed couplers): B-Z {dz}, A-B {da}, A-Z {distance(allc, want['A'], want['Z'])}")
    ok &= dz == 3
    sim = AerSimulator(method="statevector")
    N = 2_000_000
    for s, arm in (("sa", "ff"), ("sz", "off")):
        c, qs, cs = singles[s]
        small = restrict(c, qs, cs)
        cnt = sim.run(small, shots=N, seed_simulator=11).result().get_counts()
        out_bit = len(cs) - 1                       # the item's last clbit is its output (rus out_bit 4 of 5)
        p0 = sum(v for k, v in cnt.items() if k.replace(" ", "")[len(cs) - 1 - out_bit] == "0") / N
        se = (p0 * (1 - p0) / N) ** 0.5
        print(f"5. noiseless rd2 {arm} (single {s}, {N} shots): output bit reads 0 in {p0:.4f} (2 SE {2 * se:.4f})")
    print("ALL OK" if ok else "SOMETHING DIFFERS")


if __name__ == "__main__":
    main()
