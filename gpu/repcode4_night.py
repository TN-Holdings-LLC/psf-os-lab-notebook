"""Does the repetition code lose to its CZ count or to what waits during the conditional? Four arrangements of the
same test in one job (draft for a declaration; workplace Claude, 2026-11-20, after the workplace VS's six-CZ form;
not declared, not for the night of 2026-11-20). gpu/repcode_night.py (declared 2026-11-19) and gpu/repcode2_night.py
are read only.

The test of 2026-11-19 (four error items: none, d0, d1, d2; T and H on d0 then every data qubit read; c[0] judged;
the ceiling C = the best fixed rule on the off arm's other recorded bits flipping c[0], noiseless and exact, averaged
over the four items), lut3 only (the full look-up on register s, three tests, and two single-bit ancilla resets: five
conditionals in every form), in four arrangements:

  form  line            CZ  carriers during the wait   what it is
  F16   d0 a0 d1 a1 d2  16  3 (d0 d1 d2)              2026-11-19's circuit (repcode_night.circuit)
  F10   a0 d1 d0 d2 a1  10  3 (d1 d0 d2)              repcode2_night.circuit (d0 next to both data)
  F6P   a0 d1 d0 d2 a1  10  1 (d0)                    F6 with two CZ pairs that cancel (a barrier inside each pair):
                                                       one on d0-d1 before the read, one on d0-d2 after the look-up,
                                                       where F10 has its extra CZ (6 before the read and 2 after,
                                                       against F6's 4 and 0): F10's CZ count, F6's carriers
  F6    a0 d1 d0 d2 a1   6  1 (d0)                    the workplace VS's form: encode, (error), undo the encoding,
                                                       copy the syndrome from d1, d2 to the ancillas (repcode6_vs.py)

"carriers during the wait": psf_os.footprint (psf-os after-2026-11-20), the qubits not in a computational basis state
while the ancillas are read. F10 against F6P: the same CZ count, carriers 3 against 1. F6P against F6: the same
carriers, CZ 10 against 6. F16 against F10: the same carriers, CZ 16 against 10.

A barrier after the error (every form) stops the compiler from cancelling a CX pair with no error between them (on
2026-11-19 the items other than error 0 compiled to 14 CZ instead of 16; F6's no-error item would compile to 2):
check refuses any item whose compiled CZ differs from its form's count.

Whether F6 and F6P (the code undone before the look-up; the correction acts on d0 alone) are "the same test" is the
owner's; the ceiling is 0.875 in every form (computed per form, exactly).

  python gpu/repcode4_night.py ideal
  python gpu/repcode4_night.py build DEVDIR OUT [--shots S] [--dry-clifford-sentinel]
  python gpu/repcode4_night.py check OUT
  python gpu/repcode4_night.py dry OUT NOISE.json [--seed S]       illustrative noise only (repcode_night's dry)
  python gpu/repcode4_night.py score OUT
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(NB, "notes", "rus_coherent_2026-11-17"))
sys.path.insert(0, os.path.join(NB, "notes", "os2_2026-11-18"))
import repcode_night as RN  # noqa: E402  (declared 2026-11-19; read only)
import repcode2_night as R2  # noqa: E402  (read only)

FORMS = ("F16", "F10", "F6P", "F6")
CZ = {"F16": 16, "F10": 10, "F6P": 10, "F6": 6}
CARRIERS = {"F16": 3, "F10": 3, "F6P": 1, "F6": 1}
ERRORS = RN.ERRORS
SHOTS = 4000
PARTS = {"all": ERRORS, "1": ("n", "0"), "2": ("1", "2")}     # one job of 52 circuits (61.0 s at 4000 shots), or two
                                                              # of 28 (34.2 s each): every form in both, so every
                                                              # comparison is read inside each job and pooled
SEED = 20261120
C_BIT = RN.C_BIT
T16 = RN.TABLE3                                   # 2026-11-19's table (s0 = d0 + d1, s1 = d1 + d2)
T10 = R2.TABLE3                                   # s0 = d0 + d1, s1 = d0 + d2
T6 = ((3, "x3", 0), (1, "x", 1), (2, "x", 2))     # as T10; s == 3 also returns d1, d2 to 0 (the check bits)


def circuit(form, error, table=None, lookup=True):
    """(circuit, success) of one form; a barrier on every qubit after the error position (before syndrome
    extraction) keeps every CX pair from cancelling."""
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
    q = QuantumRegister(5, "q")
    s, c = ClassicalRegister(2, "s"), ClassicalRegister(3, "c")
    qc = QuantumCircuit(q, s, c)

    def cx(ctl, tgt):
        qc.h(tgt)
        qc.cz(ctl, tgt)
        qc.h(tgt)

    def err(d):
        if error != "n":
            qc.x(d[int(error)])
        qc.barrier()

    def lookup_and_resets(d, a, tab):
        qc.measure(a[0], s[0])
        qc.measure(a[1], s[1])
        if lookup:
            for value, gate, k in tab:
                with qc.if_test((s, value)):
                    if gate == "x3":
                        qc.x(d[0])
                        qc.x(d[1])
                        qc.x(d[2])
                    elif gate == "x":
                        qc.x(d[k])
                    else:
                        qc.z(a[k])
        for i in (0, 1):
            with qc.if_test((s[i], 1)):
                qc.x(a[i])

    def finish(d):
        qc.t(d[0])
        qc.h(d[0])
        for i in range(3):
            qc.measure(d[i], c[i])

    if form == "F16":
        d, a = (0, 2, 4), (1, 3)

        def copy(i):
            cx(d[i], a[i])
            cx(a[i], d[i + 1])
            cx(d[i], a[i])
        qc.h(d[0])
        qc.tdg(d[0])
        copy(0)
        copy(1)
        err(d)
        cx(d[0], a[0])
        cx(d[1], a[0])
        cx(d[1], a[1])
        cx(d[2], a[1])
        lookup_and_resets(d, a, table or T16)
        qc.barrier()
        copy(1)
        copy(0)
        finish(d)
    elif form == "F10":
        d, a = R2.LINE["d"], R2.LINE["a"]

        def parity(k):
            cx(d[0], d[k + 1])
            cx(d[k + 1], a[k])
            cx(d[0], d[k + 1])
        qc.h(d[0])
        qc.tdg(d[0])
        cx(d[0], d[1])
        cx(d[0], d[2])
        err(d)
        parity(0)
        parity(1)
        lookup_and_resets(d, a, table or T10)
        qc.barrier()
        cx(d[0], d[2])
        cx(d[0], d[1])
        finish(d)
    elif form in ("F6", "F6P"):
        d, a = R2.LINE["d"], R2.LINE["a"]
        qc.h(d[0])
        qc.tdg(d[0])
        cx(d[0], d[1])
        cx(d[0], d[2])
        err(d)
        cx(d[0], d[2])                      # undo the encoding: d1 = d0 + d1, d2 = d0 + d2 (the syndrome)
        cx(d[0], d[1])
        if form == "F6P":                   # F10 puts 6 CZ between the error and the read, 2 after the look-up;
            qc.cz(d[0], d[1])               # F6 puts 4 and 0: one pair that cancels before the read (on d0-d1, as
            qc.barrier()                    # F10's parity) and one after the look-up (on d0-d2, as F10's decoding
            qc.cz(d[0], d[1])               # starts), each kept by a barrier inside it
        cx(d[1], a[0])                      # copy it to the ancillas
        cx(d[2], a[1])
        lookup_and_resets(d, a, table or T6)
        qc.barrier()                        # as F16 / F10: every form syncs once after the look-up
        if form == "F6P":
            qc.cz(d[0], d[2])
            qc.barrier()
            qc.cz(d[0], d[2])
        finish(d)
    else:
        raise ValueError(form)
    return qc, {C_BIT: 0}


def items(part="all"):
    out = []
    for form in FORMS:
        for e in PARTS[part]:
            qc, succ = circuit(form, e)
            off, _ = circuit(form, e, lookup=False)
            out.append((f"{form.lower()}_{e}", qc, dict(success=succ, off_circuit=off)))
    return out


def ceiling_item(form, e):
    off, _ = circuit(form, e, lookup=False)
    dist = RN.exact_dist(_no_barrier(off))
    n = off.num_clbits
    by = {}
    for k, p in dist.items():
        b = [int(k[n - 1 - i]) for i in range(n)]
        m = tuple(b[i] for i in range(n) if i != C_BIT)
        by.setdefault(m, [0.0, 0.0])[b[C_BIT]] += p
    return sum(max(v) for v in by.values())


def _no_barrier(qc):
    out = qc.copy_empty_like()
    for ins in qc.data:
        if ins.operation.name != "barrier":
            out.append(ins.operation, ins.qubits, ins.clbits)
    return out


def ideal():
    from psf_os.footprint import wait_footprint
    rows = {}
    for form in FORMS:
        r = {}
        for e in ERRORS:
            qc, _ = circuit(form, e)
            dist = RN.exact_dist(_no_barrier(qc))
            ff = sum(p for k, p in dist.items() if k[qc.num_clbits - 1 - C_BIT] == "0")
            allc = sum(p for k, p in dist.items() if k[:3] == "000")
            fp = wait_footprint(qc)
            cz = sum(1 for ins in qc.data if ins.operation.name == "cz")
            r[e] = dict(ff=ff, all_c_zero=allc, ceiling=ceiling_item(form, e), carriers=fp["max"], cz=cz)
        rows[form] = dict(items=r, ceiling=sum(x["ceiling"] for x in r.values()) / len(r))
    return rows


def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None   # dry runs only, never a device
    rep = FF.build(Device.load(a.devdir), items(a.part), a.out, shots=a.shots, max_seconds=70, sentinel_spec=spec)
    info = dict(part=a.part, errors=list(PARTS[a.part]), shots=a.shots, device=rep["device"], circuits=rep["circuits"], qpu_seconds_model=rep["qpu_seconds_model"],
                per_item={t: dict(cz=x["cz"], logical_cz=x.get("logical_cz"), depth=x["depth"],
                                  conditionals=x["conditionals"], chain=x["chain"]) for t, x in rep["items"].items()})
    json.dump(info, open(os.path.join(a.out, "part.json"), "w"), indent=1)
    print(f"{rep['device']}: {rep['circuits']} circuits, {rep['qpu_seconds_model']:.1f} s by the model, {a.shots} shots")
    for form in FORMS:
        v = [x for t, x in rep["items"].items() if t.startswith(form.lower() + "_")]
        print(f"  {form}: CZ {sorted({x['cz'] for x in v})}, depth {min(x['depth'] for x in v)}-"
              f"{max(x['depth'] for x in v)}, conditionals {sorted({x['conditionals'] for x in v})}, chain "
              f"{v[0]['chain']}")


def check(a):
    """Noiseless Aer of every compiled arm (ff c = 000; off c[0] within 0.03 of exact; floor all zero); every arm's
    compiled CZ equal to its form's count (no cancellation); the footprint of every form as designed; the ceiling
    0.875 in every form; one job within 60 s by the model if a limit is set [OWNER]."""
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    from psf_os import feedforward as FF
    part = json.load(open(os.path.join(a.out, "part.json")))
    m = json.load(open(os.path.join(a.out, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(a.out, "job", "circuits.qpy"), "rb"))
    I = ideal()
    bad, lines = [], []
    say = lambda s: (print(s), lines.append(s))
    i = 0
    for cell in m["cells"]:
        for _ in range(cell["points"]):
            c = cs[i]
            i += 1
            if cell["role"] == "sentinel":
                continue
            tag = cell["name"][3:].replace("_floor", "").replace("_off", "")
            form, e = tag.split("_")
            form = form.upper()
            cc = FF.compact(c)
            n = cc.num_clbits
            cnt = AerSimulator().run(cc, shots=part["shots"], seed_simulator=SEED + i).result().get_counts()
            tot = sum(cnt.values())
            allz = sum(v for k, v in cnt.items() if set(RN._bits(k, n)) == {0}) / tot
            c_zero = sum(v for k, v in cnt.items() if RN._bits(k, n)[2:] == [0, 0, 0]) / tot
            c0 = sum(v for k, v in cnt.items() if RN._bits(k, n)[C_BIT] == 0) / tot
            cz = sum(1 for nm, _ in FF.walk(c) if nm == "cz")
            want_cz = CZ[form]
            if cell["role"] == "floor":
                ok = allz == 1.0
            elif cell["role"] == "user":
                ok = c_zero == 1.0
            else:
                off, _ = circuit(form, e, lookup=False)
                d = RN.exact_dist(_no_barrier(off))
                want = sum(p for k, p in d.items() if k[off.num_clbits - 1 - C_BIT] == "0")
                ok = abs(c0 - want) <= 0.03
            ok_cz = cz == want_cz
            if not (ok and ok_cz):
                bad.append(cell["name"])
            lines.append(f"{cell['name']:16s} {cell['role']:6s} c0 {c0:.3f} c=000 {c_zero:.3f} all0 {allz:.3f} CZ {cz} "
                         f"(want {want_cz}) {'ok' if ok and ok_cz else 'FAIL'}")
    for form in FORMS:
        C = I[form]["ceiling"]
        car = {r["carriers"] for r in I[form]["items"].values()}
        okf = abs(C - 0.875) < 1e-9 and car == {CARRIERS[form]} and all(
            abs(r["ff"] - 1) < 1e-12 for r in I[form]["items"].values())
        bad += [] if okf else [f"{form} ideal / footprint"]
        say(f"{form}: ceiling {C:.4f}, carriers during the wait {sorted(car)} (designed {CARRIERS[form]}), noiseless ff "
            f"1 in every item: {all(abs(r['ff'] - 1) < 1e-12 for r in I[form]['items'].values())}")
    s = part["qpu_seconds_model"]
    say(f"{i} circuits, {s:.1f} s by the model ({part['shots']} shots)")
    say("PASS" if not bad else f"FAIL {bad}")
    open(os.path.join(a.out, "check.txt"), "w").write("\n".join(lines) + "\n")
    return not bad


def dry(a):
    RN.dry(a)


def _pool(cards):
    N = sum(c["ff"]["counted"] for c in cards)
    p = sum(c["ff"]["success"] for c in cards) / N
    return p, (math.sqrt(p * (1 - p) / N) if 0 < p < 1 else 0.0), N


def pair_word(d, se):              # [OWNER]
    if d >= 2 * se and d > 0:
        return "KEEPS MORE"
    if d <= -2 * se and d < 0:
        return "KEEPS LESS"
    return "SAME WITHIN ERROR"


def score(a):
    """Pools every form over the four errors from one job (part all) or two (parts 1 and 2)."""
    from psf_os import feedforward as FF
    cards = {}
    for out in [a.out] + ([a.out2] if getattr(a, "out2", None) else []):
        cards.update(FF.cards(out))
    missing = [f"{f.lower()}_{e}" for f in FORMS for e in ERRORS if f"{f.lower()}_{e}" not in cards]
    if missing:
        raise SystemExit(f"items missing: {missing} (give both parts' folders)")
    I = ideal()
    res, lines = {}, []
    say = lambda s: (print(s), lines.append(s))
    for form in FORMS:
        cs = [cards[f"{form.lower()}_{e}"] for e in ERRORS]
        p, se, N = _pool(cs)
        C = I[form]["ceiling"]
        res[form] = dict(p=p, se=se, N=N, ceiling=C, margin=p - C, verdict=RN.ceiling_verdict(p, se, C),
                         per_error={e: cards[f"{form.lower()}_{e}"]["ff"]["share"] for e in ERRORS},
                         cz=CZ[form], carriers=CARRIERS[form])
        say(f"{form} (CZ {CZ[form]}, carriers {CARRIERS[form]}): lut3 c[0] right {p:.4f} (2 SE {2 * se:.4f}) against "
            f"C {C:.4f} -> {res[form]['verdict']} (margin {p - C:+.4f}); per error " +
            ", ".join(f"{e} {v:.3f}" for e, v in res[form]['per_error'].items()))
    out = {}
    for name, (x, y) in COMPARISONS.items():
        d = res[x]["p"] - res[y]["p"]
        se = math.sqrt(res[x]["se"] ** 2 + res[y]["se"] ** 2)
        out[name] = dict(d=d, two_se=2 * se, word=pair_word(d, se))
        say(f"{name}: {d:+.4f} (2 SE {2 * se:.4f}) -> {out[name]['word']}")
    row = reading(out["footprint"]["word"], out["cz"]["word"])
    say(f"reading [OWNER]: {row}")
    say("beside: CZ at equal carriers (F10 - F16) " + out["cz16"]["word"])
    json.dump(dict(forms=res, comparisons=out, reading=row), open(os.path.join(a.out, "repcode4_scores.json"), "w"),
              indent=1)
    open(os.path.join(a.out, "score.txt"), "w").write("\n".join(lines) + "\n")


COMPARISONS = {"footprint": ("F6P", "F10"),      # carriers 1 against 3 at 10 CZ each
               "cz": ("F6", "F6P"),              # 6 against 10 CZ at carriers 1 each
               "cz16": ("F10", "F16")}           # 10 against 16 CZ at carriers 3 each (beside)


def reading(fp, cz):
    """The reading table [OWNER]: every pair of words falls on one row (3 x 3 = 9 outcomes)."""
    more, same = "KEEPS MORE", "SAME WITHIN ERROR"
    if fp == more and cz == more:
        return "both: fewer carriers and fewer CZ each keep more"
    if fp == more and cz == same:
        return "the footprint: fewer carriers during the wait keep more, at equal CZ; fewer CZ add nothing seen"
    if fp == same and cz == more:
        return "the CZ count: fewer CZ keep more; the footprint adds nothing seen"
    if fp == same and cz == same:
        return "neither seen at this night's shot noise"
    return "against the expectation (fewer carriers or fewer CZ keep LESS): not read for the mechanism"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ideal")
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    b.add_argument("--shots", type=int, default=SHOTS)
    b.add_argument("--part", choices=sorted(PARTS), default="all")
    b.add_argument("--dry-clifford-sentinel", action="store_true")
    sub.add_parser("check").add_argument("out")
    d = sub.add_parser("dry")
    d.add_argument("out")
    d.add_argument("noise")
    d.add_argument("--seed", type=int, default=SEED)
    sc = sub.add_parser("score")
    sc.add_argument("out")
    sc.add_argument("out2", nargs="?")
    a = ap.parse_args()
    if a.cmd == "ideal":
        for form, r in ideal().items():
            print(f"{form}: ceiling {r['ceiling']:.4f}; " + "; ".join(
                f"{e}: ff {x['ff']:.4f} c=000 {x['all_c_zero']:.4f} ceiling {x['ceiling']:.4f} carriers {x['carriers']} "
                f"CZ {x['cz']}" for e, x in r["items"].items()))
        sys.exit(0)
    r = {"build": build, "check": check, "dry": dry, "score": score}[a.cmd](a)
    sys.exit(0 if r is not False else 1)
