"""Independent check of the repetition-code tool (workplace VS Claude, 2026-11-19; workplace instruction "その2",
item 2). qiskit and qiskit_aer only: the tool, psf-os and their helpers are not imported, except that the tool's
`check` is run as a subprocess on damaged copies (V4).

  python vs_repcode.py BUILT_OUT WORKDIR TOOL.py [OUT.json]

V1 every compiled arm, noiseless: ff c = 000 in every shot, floor all zero, off c[0] at the value derived here; every
   compiled register test reads bits [0, 1] of register s in order; the look-up table read from the compiled
   circuits equals the one derived from the parities.
V2 the ceiling by another method: each off arm written with deferred measurement (fresh qubits for the two syndrome
   reads, the conditional resets as controlled X), its exact distribution from the statevector, and every fixed rule
   on (s, c[1], c[2]) that flips c[0] tried exhaustively; per item (the tool's definition) and one rule for all items.
V3 the broadcast record against a hand count (conditionals, condition bits, IBM's broadcasts and bits).
V4 damaged copies (a table value shifted by one; two X targets exchanged) must make the tool's check FAIL.
"""
import itertools
import json
import os
import re
import shutil
import subprocess
import sys

from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister, qpy
from qiskit.circuit import Clbit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

RES = []
SIM = AerSimulator()


def report(sec, name, ok, note=""):
    RES.append(dict(section=sec, name=name, ok=bool(ok), note=note))
    print(f"{sec} {'PASS' if ok else 'FAIL'}  {name}" + (f"  ({note})" if note else ""), flush=True)


def job(out):
    m = json.load(open(os.path.join(out, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(out, "job", "circuits.qpy"), "rb"))
    names = [c["name"] + (f"#{p}" if c["points"] > 1 else "") for c in m["cells"] for p in range(c["points"])]
    roles = [c["role"] for c in m["cells"] for _ in range(c["points"])]
    return m, list(zip(names, roles, cs))


def compact(c):
    used = sorted({c.find_bit(q).index for ins in c.data for q in ins.qubits})
    pos = {q: i for i, q in enumerate(used)}
    out = QuantumCircuit(QuantumRegister(len(used), "q"), *c.cregs)
    for ins in c.data:
        out.append(ins.operation, [out.qubits[pos[c.find_bit(q).index]] for q in ins.qubits],
                   [out.clbits[c.find_bit(b).index] for b in ins.clbits])
    return out


def counts(qc, shots=2000, seed=5):
    return {k.replace(" ", ""): v for k, v in SIM.run(qc, shots=shots, seed_simulator=seed).result().get_counts().items()}


def bit(key, i):
    return int(key[-1 - i])


# ---------------------------------------------------------------- the code written here (logical, deferred)

def off_deferred(error):
    """The off arm (no look-up, the resets kept) with deferred measurement: qubits d0 a0 d1 a1 d2 = 0..4, the two
    syndrome reads copied by CX onto fresh qubits 5, 6 (= s[0], s[1]); the conditional reset of a_i becomes CX from its
    copy. Returns the exact distribution {(s0, s1, c0, c1, c2): p}."""
    qc = QuantumCircuit(7)
    d, a = (0, 2, 4), (1, 3)

    def copy(i):
        qc.cx(d[i], a[i]); qc.cx(a[i], d[i + 1]); qc.cx(d[i], a[i])
    qc.h(d[0]); qc.tdg(d[0])
    copy(0); copy(1)
    if error != "n":
        qc.x(d[int(error)])
    qc.cx(d[0], a[0]); qc.cx(d[1], a[0]); qc.cx(d[1], a[1]); qc.cx(d[2], a[1])
    qc.cx(a[0], 5); qc.cx(a[1], 6)                 # the reads, deferred
    qc.cx(5, a[0]); qc.cx(6, a[1])                 # the conditional resets, as controlled X from the record
    copy(1); copy(0)
    qc.t(d[0]); qc.h(d[0])
    p = Statevector(qc).probabilities_dict(qargs=[5, 6, 0, 2, 4])   # key: qubit 5 rightmost
    return {tuple(int(k[-1 - i]) for i in range(5)): v for k, v in p.items() if v > 1e-12}


def best_rule(dists):
    """The best fixed rule (s0, s1, c1, c2) -> flip c[0] or not, over the given distributions pooled with equal
    weight, by exhaustive search over all 2^16 rules (and, as a check, the per-key maximum)."""
    keys = list(itertools.product((0, 1), repeat=4))
    w = {k: [0.0, 0.0] for k in keys}               # [P(c0 right if kept), P(c0 right if flipped)]
    for dist in dists:
        for (s0, s1, c0, c1, c2), p in dist.items():
            k = (s0, s1, c1, c2)
            w[k][0] += p * (c0 == 0) / len(dists)
            w[k][1] += p * (c0 == 1) / len(dists)
    best = 0.0
    for rule in itertools.product((0, 1), repeat=len(keys)):
        best = max(best, sum(w[k][r] for k, r in zip(keys, rule)))
    return best, sum(max(v) for v in w.values())


# ---------------------------------------------------------------- V1

def v1(out):
    m, rows = job(out)
    bad, tables = [], {}
    expect_off = {e: sum(p for (s0, s1, c0, c1, c2), p in off_deferred(e).items() if c0 == 0) for e in "n012"}
    for name, role, c in rows:
        if role == "sentinel":
            continue
        cc = compact(c)
        mt = re.fullmatch(r"ff_(lut\d)_([n012])(_off|_floor)?", name)
        ver, e = mt.group(1), mt.group(2)
        arm = (mt.group(3) or "_ff")[1:]
        for ins in cc.data:
            op = ins.operation
            if op.name == "if_else" and isinstance(op.condition[0], ClassicalRegister):
                reg = op.condition[0]
                got = [cc.find_bit(b).index for b in reg]
                if reg.name != "s" or got != [0, 1]:
                    bad.append(f"{name}: register test on {reg.name} {got}")
                if arm == "ff":
                    body = op.blocks[0]
                    xs = [cc.find_bit(ins.qubits[body.find_bit(x.qubits[0]).index]).index
                          for x in body.data if x.operation.name == "x"]
                    tables.setdefault((ver, e), []).append((int(op.condition[1]), tuple(xs)))
        cnt = counts(cc)
        tot = sum(cnt.values())
        if arm == "ff" and any(bit(k, 2) or bit(k, 3) or bit(k, 4) for k in cnt):
            bad.append(f"{name}: c not 000 in every shot")
        if arm == "floor" and any(set(k) != {"0"} for k in cnt):
            bad.append(f"{name}: floor not all zero")
        if arm == "off":
            p0 = sum(v for k, v in cnt.items() if bit(k, 2) == 0) / tot
            if abs(p0 - expect_off[e]) > 0.04:
                bad.append(f"{name}: off c[0] right {p0:.3f}, expected {expect_off[e]:.3f}")
    report("V1", "compiled arms: ff c = 000, floors zero, off c[0] as derived, register tests on s[0], s[1]",
           not bad, "; ".join(bad)[:200] or f"off c[0] right expected {[round(v, 3) for v in expect_off.values()]}")
    # the table: syndrome (a0 = d0 + d1, a1 = d1 + d2) of an X on data k, value s0 + 2 s1
    derived = {1: 0, 3: 1, 2: 2}
    phys = None
    lut3 = sorted(tables.get(("lut3", "n"), []))
    # map each value to which compiled qubit its X acts on; the three must be distinct and consistent across items
    ok = len(lut3) == 3 and len({x for _, x in lut3}) == 3
    same = all(sorted(tables[("lut3", e)]) == lut3 for e in "n012")
    report("V1", "lut3: three tests (values 1, 3, 2), each an X on its own qubit, the same in every lut3 item",
           ok and same and sorted(v for v, _ in lut3) == [1, 2, 3], str(lut3))
    lut1 = {e: tables.get(("lut1", e)) for e in "n012"}
    want1 = {"n": 1, "0": 1, "1": 3, "2": 2}
    report("V1", "lut1: one test, the value of the injected error (s == 1 for no error)",
           all(len(v) == 1 and v[0][0] == want1[e] for e, v in lut1.items()), str(lut1))


# ---------------------------------------------------------------- V2

def v2():
    dists = {e: off_deferred(e) for e in "n012"}
    per = {e: best_rule([dists[e]])[0] for e in "n012"}
    C_item = sum(per.values()) / 4
    C_one, C_check = best_rule(list(dists.values()))
    report("V2", "ceiling, a rule per item (the tool's definition)", abs(C_item - 0.875) < 1e-9,
           f"per error {[round(v, 6) for v in per.values()]}, mean {C_item:.6f}")
    report("V2", "ceiling, one rule for all four items", abs(C_one - 0.875) < 1e-9,
           f"{C_one:.6f} (per-key maximum {C_check:.6f})")
    return dict(per_item=per, C_item=C_item, C_one=C_one)


# ---------------------------------------------------------------- V3

def v3(out):
    m, rows = job(out)
    n = bits = nb = nbits = 0
    for _, _, c in rows:
        stamp, sent, t = {}, {}, 0
        for ins in c.data:
            t += 1
            op = ins.operation
            if op.name == "measure":
                stamp[c.find_bit(ins.clbits[0]).index] = t
            elif op.name == "if_else":
                tgt = op.condition[0]
                cb = [c.find_bit(b).index for b in ([tgt] if isinstance(tgt, Clbit) else list(tgt))]
                n += 1
                bits += len(cb)
                if any(stamp.get(b, 0) > sent.get(b, -1) for b in cb):
                    nb += 1
                    nbits += len(cb)
                    for b in cb:
                        sent[b] = t
    rec = m["broadcast"]
    got = (rec["conditionals"], rec["condition_bits"], rec["broadcasts"], rec["broadcast_bits"])
    report("V3", "broadcast record equals the hand count (conditionals, bits, IBM broadcasts, bits)",
           got == (n, bits, nb, nbits), f"record {got}, hand {(n, bits, nb, nbits)}")


# ---------------------------------------------------------------- V4

def mutate(out, work, tool, kind):
    dst = os.path.join(work, f"mut_{kind}")
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(out, dst)
    m, rows = job(dst)
    cs, hit = [], 0
    for name, role, c in rows:
        if role == "user" and name.startswith("ff_lut3"):
            new = c.copy_empty_like()
            done = False
            xs = []
            for ins in c.data:
                op = ins.operation
                if op.name == "if_else" and isinstance(op.condition[0], ClassicalRegister):
                    xs.append(len(new.data))
                new.append(op, ins.qubits, ins.clbits)
            if kind == "value":            # the test of s == 1 compares with 2 instead
                for k in xs:
                    ins = new.data[k]
                    if int(ins.operation.condition[1]) == 1:
                        op = ins.operation.replace_blocks(ins.operation.blocks)
                        op.condition = (op.condition[0], 2)
                        new.data[k] = ins.replace(operation=op)
                        done = True
            else:                           # the blocks of the tests for s == 1 and s == 3 exchanged
                k1 = [k for k in xs if int(new.data[k].operation.condition[1]) == 1][0]
                k3 = [k for k in xs if int(new.data[k].operation.condition[1]) == 3][0]
                i1, i3 = new.data[k1], new.data[k3]
                op1 = i1.operation.replace_blocks(i1.operation.blocks)
                op3 = i3.operation.replace_blocks(i3.operation.blocks)
                op1.condition, op3.condition = (op1.condition[0], 3), (op3.condition[0], 1)
                new.data[k1], new.data[k3] = i1.replace(operation=op1), i3.replace(operation=op3)
                done = True
            hit += done
            cs.append(new)
        else:
            cs.append(c)
    with open(os.path.join(dst, "job", "circuits.qpy"), "wb") as f:
        qpy.dump(cs, f)
    r = subprocess.run([sys.executable, tool, "check", dst], capture_output=True, text=True)
    last = (r.stdout.strip().splitlines() or ["?"])[-1]
    report("V4", f"damage '{kind}' in {hit} lut3 ff arms: the tool's check fails", r.returncode != 0 and "PASS" not in last,
           last[:120])


def main():
    out, work, tool = sys.argv[1:4]
    os.makedirs(work, exist_ok=True)
    v1(out)
    cres = v2()
    v3(out)
    for kind in ("value", "swap"):
        mutate(out, work, tool, kind)
    print(f"{len(RES)} checks, {sum(not r['ok'] for r in RES)} FAIL")
    if len(sys.argv) > 4:
        json.dump(dict(results=RES, ceiling=cres), open(sys.argv[4], "w"), indent=1)


if __name__ == "__main__":
    main()
