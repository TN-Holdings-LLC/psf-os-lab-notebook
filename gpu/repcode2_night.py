"""The distance-3 repetition code of gpu/repcode_night.py with fewer CZ (draft; workplace Claude, 2026-11-20, home's
added instruction; desk only, not for the night of 2026-11-20). gpu/repcode_night.py (declared for 2026-11-19) is
imported read only; this file swaps in another arrangement of the same code and reuses its build / check / dry /
score / ideal unchanged: the four error items, the T and the readout, the ceiling's definition and the pooling are
the same; only the circuit's arrangement on the line differs.

Where the 2026-11-19 arrangement spends its CZ (every CX is H CZ H; per item, every version and arm):
  line d0 a0 d1 a1 d2 (data at the ends and the middle, ancillas between):
  encode  6  d1 ^= d0 and d2 ^= d1 each go through an ancilla: CX(d, a) CX(a, d') CX(d, a)
  parity  4  each ancilla touches both data of its pair: CX(d0, a0) CX(d1, a0) CX(d1, a1) CX(d2, a1)
  decode  6  the encoding undone
  total  16  (the look-up and the resets add conditional one-qubit gates only, no CZ)

The arrangement here, by formula (no search): the line a0 d1 d0 d2 a1, d0 in the middle with both other data as
its neighbours, each ancilla at an end next to one datum:
  encode  2  CX(d0, d1) CX(d0, d2)
  parity  6  s0 = d0 + d1 into a0: CX(d0, d1) CX(d1, a0) CX(d0, d1); s1 = d0 + d2 into a1 likewise
  decode  2  CX(d0, d2) CX(d0, d1)
  total  10
Why not fewer on heavy-hex: its coupling graph is bipartite (no triangles), so no ancilla can neighbour both data of
an adjacent pair; a parity of two neighbouring data through an ancilla then costs 3, and a parity through an
ancilla between two data (2 CZ) needs the data apart, which makes the encoding cost 3 per link. With the data
adjacent: 2 + 2 x 3 + 2 = 10; with the data apart (2026-11-19): 6 + 4 + 6 = 16; mixed (one pair each way): 2 + 3 +
5 + ... = 12 or more. The line of five fits any rule-C chain; no degree-3 site is needed, so placement is unchanged.

The syndromes are s0 = d0 + d1 and s1 = d0 + d2 (2026-11-19: d0 + d1 and d1 + d2), so the table reads: s == 3 ->
X d0, s == 1 -> X d1, s == 2 -> X d2 (three tests on register s, as before). lut1's single test for no error is the
test of s == 1 (it never fires), as before. Noiselessly every ff shot reads c = 000; the off arm leaves an X on d0
to the T (c[0] right in half the shots) and ends an X on d1 or d2 on c[1] or c[2]: the ceiling stays 0.875.

  python gpu/repcode2_night.py ideal | build DEVDIR OUT [--dry-clifford-sentinel] | check OUT | dry OUT NOISE.json |
                               score OUT          (as gpu/repcode_night.py)
  python gpu/repcode2_night.py same                 per item and arm: the exact distribution of every recorded bit
                                                    against the 2026-11-19 arrangement's
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import repcode_night as RN  # noqa: E402  (declared 2026-11-19; read only)

TABLE3 = ((3, "x", 0), (1, "x", 1), (2, "x", 2))       # (value of s, gate, data index corrected)
ONE = {"n": (1, "x", 1), "0": (3, "x", 0), "1": (1, "x", 1), "2": (2, "x", 2)}
LINE = dict(d=(2, 1, 3), a=(0, 4))                      # q0 a0, q1 d1, q2 d0, q3 d2, q4 a1
CZ_COUNT = dict(encode=2, parity=6, decode=2)


def circuit(error, table, lookup=True):
    """(circuit, success): the code on the line a0 d1 d0 d2 a1 with the given look-up table; lookup=False removes
    the table and keeps the ancilla resets (the off arm), as repcode_night.circuit."""
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
    q = QuantumRegister(5, "q")
    s, c = ClassicalRegister(2, "s"), ClassicalRegister(3, "c")
    qc = QuantumCircuit(q, s, c)
    d, a = LINE["d"], LINE["a"]

    def cx(ctl, tgt):
        qc.h(tgt)
        qc.cz(ctl, tgt)
        qc.h(tgt)

    def parity(k):                       # a[k] ^= d0 + d[k+1], through d[k+1] (its neighbour); d[k+1] restored
        cx(d[0], d[k + 1])
        cx(d[k + 1], a[k])
        cx(d[0], d[k + 1])
    qc.h(d[0])
    qc.tdg(d[0])
    cx(d[0], d[1])                       # encode
    cx(d[0], d[2])
    if error != "n":
        qc.x(d[int(error)])
    parity(0)
    parity(1)
    qc.measure(a[0], s[0])
    qc.measure(a[1], s[1])
    if lookup:
        for value, gate, k in table:
            with qc.if_test((s, value)):
                if gate == "x":
                    qc.x(d[k])
                else:
                    qc.z(a[k])          # the ancilla holds its measured value: a phase only, nothing changes
    for i in (0, 1):
        with qc.if_test((s[i], 1)):
            qc.x(a[i])
    cx(d[0], d[2])                       # decode
    cx(d[0], d[1])
    qc.t(d[0])
    qc.h(d[0])
    for i in range(3):
        qc.measure(d[i], c[i])
    return qc, {RN.C_BIT: 0}


def install():
    """Swap this arrangement into repcode_night's module (its functions read these names at call time)."""
    RN._circuit_2026_11_19, RN._table3_2026_11_19, RN._one_2026_11_19 = RN.circuit, RN.TABLE3, RN.ONE
    RN.circuit, RN.TABLE3, RN.ONE = circuit, TABLE3, ONE


def same():
    """Per item and arm (ff, off): the exact distribution of the recorded bits c against the 2026-11-19
    arrangement's. c[0] is the same bit; the check bits are decoded against d0 here (c1 = d0 + d1, c2 = d0 + d2) and
    along the line there (c1 = d0 + d1, c2 = d1 + d2), so c2 there is c1 + c2 here: compared after that relabeling
    (the same information; the ceiling's best fixed rule reads either). The syndrome bits differ by definition
    (s1 = d0 + d2 here, d1 + d2 there) and are left out."""
    old_c, old_t, old_o = RN.circuit, RN.TABLE3, RN.ONE
    rows, worst = [], 0.0
    for ver in RN.VERSIONS:
        for e in RN.ERRORS:
            for lookup in (True, False):
                tab_old = {"lut3": old_t, "lut1": (old_o[e],), "lut5": old_t + RN.PAD}[ver]
                tab_new = {"lut3": TABLE3, "lut1": (ONE[e],), "lut5": TABLE3 + RN.PAD}[ver]
                do = RN.exact_dist(old_c(e, tab_old, lookup)[0])
                dn = RN.exact_dist(circuit(e, tab_new, lookup)[0])
                mo, mn = {}, {}
                for k, p in do.items():
                    mo[k[:3]] = mo.get(k[:3], 0.0) + p          # key c[2] c[1] c[0] (s dropped)
                for k, p in dn.items():
                    c2, c1, c0 = (int(x) for x in k[:3])
                    kk = f"{c1 ^ c2}{c1}{c0}"                     # here c1 = d0 + d1, c2 = d0 + d2 after decoding;
                    mn[kk] = mn.get(kk, 0.0) + p                 # 2026-11-19's c2 = d1 + d2 = c1 + c2
                tv = 0.5 * sum(abs(mo.get(k, 0) - mn.get(k, 0)) for k in set(mo) | set(mn))
                worst = max(worst, tv)
                rows.append((ver, e, "ff" if lookup else "off", tv))
                print(f"{ver}_{e} {'ff ' if lookup else 'off'}: total variation of c {tv:.1e}")
    print(f"worst {worst:.1e} over {len(rows)} item arms")
    return worst < 1e-12


def main():
    """repcode_night's command line, with this arrangement swapped in."""
    import argparse
    if sys.argv[1:2] == ["same"]:
        sys.exit(0 if same() else 1)
    install()
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ideal")
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    b.add_argument("--shots", type=int, default=RN.SHOTS)
    b.add_argument("--dry-clifford-sentinel", action="store_true")
    c = sub.add_parser("check")
    c.add_argument("out")
    c.add_argument("--verbose", action="store_true")
    d = sub.add_parser("dry")
    d.add_argument("out")
    d.add_argument("noise")
    d.add_argument("--seed", type=int, default=RN.SEED)
    sub.add_parser("score").add_argument("out")
    a = ap.parse_args()
    if a.cmd == "ideal":
        I = RN.ideal()
        for e, r in I["rows"].items():
            print(f"error {e}: ff c[0] right lut3 {r['ff']['lut3']:.4f} lut1 {r['ff']['lut1']:.4f} lut5 "
                  f"{r['ff']['lut5']:.4f}; off c[0] {r['off_c0']:.4f}; ceiling {r['ceiling']:.4f}")
        print(f"ceiling C = {I['ceiling']:.4f}")
        sys.exit(0)
    r = {"build": RN.build, "check": RN.check, "dry": RN.dry, "score": RN.score}[a.cmd](a)
    sys.exit(0 if r is not False else 1)


if __name__ == "__main__":
    main()
