"""Prototypes (workplace, 2026-11-17; owner "試作作って"; desk only, not declared): two computations where the real-time
decision is the computation, each with an exact answer and a ceiling for any after-the-fact processing.

A. Iterative phase estimation (semiclassical, one bit at a time; Kitaev / Griffiths-Niu). Two qubits on a line: an
   ancilla a and a target t in |1>, the eigenstate of the phase gate U = P(2 pi phi). phi = j / 2^n for every
   j = 0 .. 2^n - 1. Round m = n-1 .. 0 (least significant bit first): H(a), controlled U^(2^m) written with CZ,
   then, for every bit already read, a conditional phase on a that removes its share (the feedback), H(a), measure a
   into c[m] (the bit phi_{m+1}), reset a by a conditional X. With feedback every bit is right in every shot.
   The off arm keeps the reset and drops the phase feedback. Ceiling for after-the-fact processing: the best fixed
   decoder from the off arm's recorded bits to phi, averaged over all phi (computed exactly):
       C(n) = 2^-n sum_bits max_phi P_off(bits | phi).
   The decisions compound: bit m's correction depends on all bits read before it.
B. Long-range teleportation in constant depth: a non-Clifford state T^dag|+> on q0 is carried to q_{2k} through k
   Bell pairs made in parallel and k Bell measurements in parallel; the byproduct X^a Z^b on the last qubit (a and b
   parities of the measured bits) is removed by single-bit conditionals (IBM's dynamic circuits test one bit and do no
   arithmetic, so a parity is applied as one conditional per bit); then T and H: every shot ideally reads 0. Without
   the corrections the X byproduct lands before the T: the ceiling is 3/4 (as the teleport test of 2026-11-16). The
   point here is depth: the CZ layers stay constant in k, where the sequential teleport test grows with k.

  python apps.py ideal                     exact values (branching simulation, no sampling) and ceilings
  python apps.py build DEVDIR OUT [--dry-clifford-sentinel] [--n 2 3] [--k 2 4]
  python apps.py score OUT                 success per item, the averages against the ceilings
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(NB, "notes", "rus_coherent_2026-11-17"))


# ------------------------------------------------------------------------------------------------ A: phase estimation

def _cx(qc, c, t):
    qc.h(t)
    qc.cz(c, t)
    qc.h(t)


def _cp(qc, lam, c, t):
    """Controlled phase P(lam) written with CZ: P(lam/2) c, P(lam/2) t, CX, P(-lam/2) t, CX."""
    qc.p(lam / 2, c)
    qc.p(lam / 2, t)
    _cx(qc, c, t)
    qc.p(-lam / 2, t)
    _cx(qc, c, t)


def ipe(n, j, feedback=True):
    """(circuit, success {clbit: value}) for phi = j / 2^n; c[m] holds the bit phi_{m+1}."""
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
    q, c = QuantumRegister(2, "q"), ClassicalRegister(n, "c")
    qc = QuantumCircuit(q, c)
    a, t = 0, 1
    phi = j / 2 ** n
    qc.x(t)
    for m in range(n - 1, -1, -1):
        qc.h(a)
        _cp(qc, 2 * math.pi * phi * 2 ** m, a, t)
        if feedback:
            for d in range(1, n - m):                     # bits phi_{m+1+d}, read in earlier rounds, sit in c[m + d]
                with qc.if_test((c[m + d], 1)):
                    qc.p(-2 * math.pi / 2 ** (d + 1), a)
        qc.h(a)
        qc.measure(a, m)
        if m > 0:
            with qc.if_test((c[m], 1)):
                qc.x(a)                                  # reset the ancilla for the next round
    bits = [(j >> (n - 1 - m)) & 1 for m in range(n)]   # phi_{m+1} for m = 0 .. n-1
    return qc, {m: bits[m] for m in range(n)}


def ipe_ideal(n):
    import coherent as CO
    ff, off = [], []
    P = {}
    for j in range(2 ** n):
        for fb in (True, False):
            qc, succ = ipe(n, j, fb)
            dist = CO.branch_distribution(qc)
            ok = sum(p for k, p in dist.items() if all(k[n - 1 - m] == str(v) for m, v in succ.items()))
            (ff if fb else off).append(ok)
            if not fb:
                P[j] = dist
    keys = set().union(*P.values())
    ceiling = sum(max(P[j].get(k, 0.0) for j in P) for k in keys) / 2 ** n
    return dict(n=n, ff=sum(ff) / len(ff), off=sum(off) / len(off), ceiling=ceiling, ff_min=min(ff))


# ------------------------------------------------------------------------------------------------ B: long range

def longrange(k, feed_forward=True):
    """q0 holds T^dag|+>; Bell pairs (q1, q2), (q3, q4), ..., (q_{2k-1}, q_{2k}) in parallel; Bell measurements on
    (q0, q1), (q2, q3), ..., (q_{2k-2}, q_{2k-1}) in parallel; X on q_{2k} for every Z-type bit, Z for every X-type
    bit; T, H, measure q_{2k}. Bits: c[2i] the X-type (first qubit of the pair after H), c[2i+1] the Z-type, c[2k]
    the final."""
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
    n = 2 * k + 1
    q, c = QuantumRegister(n, "q"), ClassicalRegister(2 * k + 1, "c")
    qc = QuantumCircuit(q, c)
    qc.h(0)
    qc.tdg(0)
    for i in range(k):                                   # Bell pairs (2i+1, 2i+2)
        qc.h(2 * i + 1)
        _cx(qc, 2 * i + 1, 2 * i + 2)
    for i in range(k):                                   # Bell measurements (2i, 2i+1)
        _cx(qc, 2 * i, 2 * i + 1)
        qc.h(2 * i)
        qc.measure(2 * i, 2 * i)
        qc.measure(2 * i + 1, 2 * i + 1)
    last = 2 * k
    if feed_forward:
        for i in range(k):
            with qc.if_test((c[2 * i + 1], 1)):
                qc.x(last)
        for i in range(k):
            with qc.if_test((c[2 * i], 1)):
                qc.z(last)
    qc.t(last)
    qc.h(last)
    qc.measure(last, 2 * k)
    return qc, {2 * k: 0}


def longrange_ideal(k):
    import coherent as CO
    out = {}
    for ff in (True, False):
        qc, succ = longrange(k, ff)
        dist = CO.branch_distribution(qc)
        out["ff" if ff else "off"] = sum(p for key, p in dist.items() if key[0] == "0")
        if not ff:                                        # best fixed rule on the recorded bits (exact)
            by = {}
            for key, p in dist.items():
                by.setdefault(key[1:], [0.0, 0.0])[int(key[0])] += p
            out["ceiling"] = sum(max(v) for v in by.values())
    return dict(k=k, **out)


# ------------------------------------------------------------------------------------------------ job

def items(ns=(2, 3), ks=(2, 4)):
    out = []
    for n in ns:
        for j in range(2 ** n):
            qc, succ = ipe(n, j, True)
            off, _ = ipe(n, j, False)
            out.append((f"ipe{n}_{j}", qc, dict(success=succ, off_circuit=off, form="blocks")))
    for k in ks:
        qc, succ = longrange(k, True)
        out.append((f"lr{k}", qc, dict(success=succ, bound=0.75)))
    return out


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ideal")
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    b.add_argument("--dry-clifford-sentinel", action="store_true")
    b.add_argument("--n", type=int, nargs="+", default=[2, 3])
    b.add_argument("--k", type=int, nargs="+", default=[2, 4])
    sub.add_parser("score").add_argument("out")
    a = ap.parse_args()
    if a.cmd == "ideal":
        res = dict(ipe=[ipe_ideal(n) for n in (1, 2, 3, 4)], longrange=[longrange_ideal(k) for k in (1, 2, 3, 4)])
        for r in res["ipe"]:
            print(f"A n {r['n']}: ff {r['ff']:.4f} (min over phi {r['ff_min']:.4f}); off as read {r['off']:.4f}; "
                  f"ceiling (best decoder of the off bits) {r['ceiling']:.4f}; margin {r['ff'] - r['ceiling']:+.4f}")
        for r in res["longrange"]:
            print(f"B k {r['k']}: ff {r['ff']:.4f}; off {r['off']:.4f}; ceiling (best fixed rule) {r['ceiling']:.4f}")
        json.dump(res, open(os.path.join(HERE, "ideal.json"), "w"), indent=1)
    elif a.cmd == "build":
        from psf_os import feedforward as FF
        from psf_os.device import Device
        spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None
        rep = FF.build(Device.load(a.devdir), items(a.n, a.k), a.out, shots=4000, max_seconds=160, sentinel_spec=spec)
        print(json.dumps({x: rep[x] for x in ("device", "circuits", "qpu_seconds_model")}))
        seen = set()
        for t, v in rep["items"].items():
            key = t.split("_")[0]
            if key in seen:
                continue
            seen.add(key)
            print(key, "chain", v["chain"], "CZ", v["cz"], "off CZ", v["off_cz"], "depth", v["depth"], "mid", v["mid"],
                  "conditionals", v["conditionals"])
    elif a.cmd == "score":
        from psf_os import feedforward as FF
        ideal = json.load(open(os.path.join(HERE, "ideal.json")))
        ceil_a = {r["n"]: r for r in ideal["ipe"]}
        ceil_b = {r["k"]: r for r in ideal["longrange"]}
        cards = FF.cards(a.out)
        groups = {}
        for t, c in cards.items():
            groups.setdefault(t.split("_")[0], []).append(c)
        out = {}
        for g in sorted(groups):
            cs = groups[g]
            N = sum(c["ff"]["counted"] for c in cs)
            p = sum(c["ff"]["success"] for c in cs) / N
            po = sum(c["off"]["success"] for c in cs) / sum(c["off"]["counted"] for c in cs)
            se = math.sqrt(p * (1 - p) / N) if 0 < p < 1 else 0.0
            ceil = ceil_a[int(g[3:])]["ceiling"] if g.startswith("ipe") else ceil_b[int(g[2:])]["ceiling"]
            v = "BEYOND THE CEILING" if p >= ceil + 2 * se else "NOT BEYOND"
            out[g] = dict(ff=p, two_se=2 * se, off_as_read=po, ceiling=ceil, verdict_draft=v, circuits=len(cs),
                          sentinel=cs[0]["sentinel"])
            print(f"{g}: ff {p:.4f} (2 SE {2 * se:.4f}, {len(cs)} circuits, {N} shots) against the ceiling "
                  f"{ceil:.4f} -> {v}; off as read {po:.4f}; sentinel {cs[0]['sentinel']}")
        json.dump(out, open(os.path.join(a.out, "apps_scores.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
