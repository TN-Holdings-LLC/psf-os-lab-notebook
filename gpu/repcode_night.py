"""The distance-3 repetition code with a look-up decoder in real time, its result used at once by a non-Clifford gate
(draft for a declaration; workplace Claude, 2026-11-19, home handover 2026-11-19 section 4.2). Not declared; verdict
words, thresholds and predictions are the owner's ([OWNER] in prereg/drafts-2026-11-19/repcode_DRAFT.md). Needs psf-os
with register conditions (branch register-cond-2026-11-18 or v0.2).

The circuit (psf_os.feedforward.rep3_lookup's form, here with the table as a parameter): a line d0 a0 d1 a1 d2; d0
holds T^dag|+>, encoded into d0 d1 d2 through the ancillas (neighbour gates only); an X on data e (none, 0, 1, 2); the
parities a0 = d0 + d1 and a1 = d1 + d2 measured into register s; the look-up corrects; the ancillas are reset by a
conditional X on their own bit; decoded back onto d0; then T and H on d0 and every data qubit read (c[0] = d0 the
logical answer, c[1], c[2] the decoding's check bits). Noiselessly every shot reads c = 000.

Why the T: in a memory test a decoder run afterwards on the recorded syndromes does as well as one in real time (the
Pauli frame). Here the correction must be applied before the T: an X left on d0 before the T leaves c[0] at random,
and no rule on the recorded bits can repair it afterwards.

Items (4000 shots each, ff / off / floor arms, one ring sentinel; one job):
  lut3_e   the full table, three tests on register s (s == 1 -> X d0, s == 3 -> X d1, s == 2 -> X d2)
  lut1_e   one test only, the one that fires for error e (for no error: the test of s == 1, which never fires): a
           decoder told where the error is
  lut5_e   lut3 and two tests of s == 0 with a Z on an ancilla holding its measured value (they change nothing; they
           fire for e = none only, so lut5 - lut3 is also scored per group: added tests never fire / fire)
  for e in none, 0, 1, 2. The off arm (given explicitly): no look-up, the ancilla resets kept (the same for lut1 and
  lut3). Both versions hold the two reset conditionals.

Yardsticks:
  ceiling   C = the best fixed rule on the off arm's recorded bits (s, c[1], c[2]) that flips c[0], noiseless and exact
            per item, averaged over the four errors (the error's place is known to the rule): C = (1 + 1/2 + 1 + 1) / 4
            = 0.875 (an X on d0 before the T leaves c[0] at 1/2 whatever is recorded). Verdict on lut3, the four items
            pooled, success = c[0] right: BEYOND THE CEILING when p >= C + 2 SE, otherwise NOT BEYOND.
  within    d = p(lut3) - p(lut1), the four errors pooled, the same circuits but for two tests that never fire: does an
            item lose with more conditionals inside it (the loss of 2026-11-17 / 18 was between items side by side)?
            Draft words [OWNER]: MORE TESTS KEEP LESS (d <= -2 SE), SAME WITHIN ERROR (|d| < 2 SE), MORE TESTS KEEP MORE.

  python gpu/repcode_night.py ideal
  python gpu/repcode_night.py build DEVDIR OUT [--shots S] [--dry-clifford-sentinel]
  python gpu/repcode_night.py check OUT
  python gpu/repcode_night.py dry OUT NOISE.json [--seed S]    illustrative noise only, never fitted
  python gpu/repcode_night.py score OUT
Placement: rule C (coupling graph and failed marks); no calibration error number is read."""
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

ERRORS = ("n", "0", "1", "2")
TABLE3 = ((1, "x", 0), (3, "x", 1), (2, "x", 2))      # (value of s, gate, data index corrected)
PAD = ((0, "za", 0), (0, "za", 1))            # two tests that change nothing: Z on an ancilla in a basis state
ONE = {"n": (1, "x", 0), "0": (1, "x", 0), "1": (3, "x", 1), "2": (2, "x", 2)}
VERSIONS = ("lut3", "lut1", "lut5")
NCOND = {"lut3": 5, "lut1": 3, "lut5": 7}
SHOTS = 4000
SEED = 20261119
C_BIT = 2                                    # c[0] is clbit 2 (register s holds clbits 0, 1)


def circuit(error, table, lookup=True):
    """(circuit, success): the code with the given look-up table; lookup=False removes the table, keeps the resets."""
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
    q = QuantumRegister(5, "q")
    s, c = ClassicalRegister(2, "s"), ClassicalRegister(3, "c")
    qc = QuantumCircuit(q, s, c)
    d, a = (0, 2, 4), (1, 3)

    def cx(ctl, tgt):
        qc.h(tgt)
        qc.cz(ctl, tgt)
        qc.h(tgt)

    def copy(i):
        cx(d[i], a[i])
        cx(a[i], d[i + 1])
        cx(d[i], a[i])
    qc.h(d[0])
    qc.tdg(d[0])
    copy(0)
    copy(1)
    if error != "n":
        qc.x(d[int(error)])
    cx(d[0], a[0])
    cx(d[1], a[0])
    cx(d[1], a[1])
    cx(d[2], a[1])
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
    copy(1)
    copy(0)
    qc.t(d[0])
    qc.h(d[0])
    for i in range(3):
        qc.measure(d[i], c[i])
    return qc, {C_BIT: 0}


def items():
    out = []
    for ver in VERSIONS:
        for e in ERRORS:
            table = table_of(ver, e)
            qc, succ = circuit(e, table)
            off, _ = circuit(e, table, lookup=False)
            out.append((f"{ver}_{e}", qc, dict(success=succ, off_circuit=off)))
    return out


def table_of(ver, e):
    return {"lut3": TABLE3, "lut1": (ONE[e],), "lut5": TABLE3 + PAD}[ver]


def _bits(key, n):
    key = key.replace(" ", "")
    return [int(key[-1 - i]) for i in range(n)]


def exact_dist(qc):
    """The exact distribution of the classical register (key: clbit n-1 .. 0), branching over every mid-circuit
    measurement with Statevector (notes/rus_coherent_2026-11-17's branch_distribution tests one bit only; here a test
    may read a whole register)."""
    import numpy as np
    from qiskit.quantum_info import Statevector
    n, nc = qc.num_qubits, qc.num_clbits
    branches = [(1.0, Statevector.from_label("0" * n), [0] * nc)]

    def run(br, circ, qmap, cmap):
        for ins in circ.data:
            op = ins.operation
            qs = [qmap[circ.find_bit(x).index] for x in ins.qubits]
            if op.name == "barrier":
                continue
            if op.name == "measure":
                cb = cmap[circ.find_bit(ins.clbits[0]).index]
                new = []
                for p, sv, bits in br:
                    probs = sv.probabilities([qs[0]])
                    for v in (0, 1):
                        if probs[v] < 1e-15:
                            continue
                        proj = np.zeros((2, 2))
                        proj[v, v] = 1.0
                        s2 = sv.evolve(proj, [qs[0]])
                        s2 = Statevector(s2.data / np.sqrt(probs[v]))
                        b2 = list(bits)
                        b2[cb] = v
                        new.append((p * probs[v], s2, b2))
                br = new
                continue
            if op.name == "if_else":
                tgt, val = op.condition
                if type(tgt).__name__ == "ClassicalRegister":
                    idx = [cmap[circ.find_bit(x).index] for x in tgt]
                else:
                    idx = [cmap[circ.find_bit(tgt).index]]
                body = op.blocks[0]
                bq = {j: qs[j] for j in range(len(qs))}
                bc = {j: cmap[circ.find_bit(x).index] for j, x in enumerate(ins.clbits)}
                new = []
                for p, sv, bits in br:
                    v = sum(bits[b] << i for i, b in enumerate(idx))
                    new += run([(p, sv, bits)], body, bq, bc) if v == int(val) else [(p, sv, bits)]
                br = new
                continue
            br = [(p, sv.evolve(op, qs), bits) for p, sv, bits in br]
        return br
    out = {}
    for p, _, bits in run(branches, qc, {j: j for j in range(n)}, {j: j for j in range(nc)}):
        k = "".join(str(bits[nc - 1 - i]) for i in range(nc))
        out[k] = out.get(k, 0.0) + p
    return out


def ceiling_item(e):
    """Best fixed rule on the off arm's other recorded bits flipping c[0], exact (noiseless)."""
    off, _ = circuit(e, TABLE3, lookup=False)
    dist = exact_dist(off)
    n = off.num_clbits
    by = {}
    for k, p in dist.items():
        b = [int(k[n - 1 - i]) for i in range(n)]
        m = tuple(b[i] for i in range(n) if i != C_BIT)
        by.setdefault(m, [0.0, 0.0])[b[C_BIT]] += p
    return sum(max(v) for v in by.values())


def ideal():
    rows = {}
    for e in ERRORS:
        ff = {}
        for ver in VERSIONS:
            qc, _ = circuit(e, table_of(ver, e))
            dist = exact_dist(qc)
            ff[ver] = sum(p for k, p in dist.items() if k[qc.num_clbits - 1 - C_BIT] == "0")
            ff[ver + "_all_c_zero"] = sum(p for k, p in dist.items() if k[:3] == "000")
        off, _ = circuit(e, TABLE3, lookup=False)
        od = exact_dist(off)
        rows[e] = dict(ff=ff, off_c0=sum(p for k, p in od.items() if k[off.num_clbits - 1 - C_BIT] == "0"),
                       ceiling=ceiling_item(e))
    C = sum(r["ceiling"] for r in rows.values()) / len(rows)
    return dict(rows=rows, ceiling=C)


def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None   # dry runs only, never a device
    rep = FF.build(Device.load(a.devdir), items(), a.out, shots=a.shots, max_seconds=60, sentinel_spec=spec)
    man = json.load(open(os.path.join(a.out, "job", "manifest.json")))
    info = dict(shots=a.shots, device=rep["device"], circuits=rep["circuits"], qpu_seconds_model=rep["qpu_seconds_model"],
                broadcast={k: man["broadcast"][k] for k in ("conditionals", "condition_bits", "broadcasts",
                                                             "broadcast_bits", "max_conditionals_per_circuit")},
                build_env=man.get("build_env"))
    json.dump(info, open(os.path.join(a.out, "part.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in info.items() if k != "build_env"}))
    v = rep["items"]
    print(f"per item: CZ {min(x['cz'] for x in v.values())}-{max(x['cz'] for x in v.values())}, depth "
          f"{min(x['depth'] for x in v.values())}-{max(x['depth'] for x in v.values())}, mid 2, conditionals "
          f"lut3 {v['lut3_0']['conditionals']} / lut1 {v['lut1_0']['conditionals']}, chain {v['lut3_0']['chain']}")


def check(a):
    """Noiseless Aer of every compiled arm: ff c = 000 in every shot; off c[0] within 0.03 of its exact value; floor all
    zero; the compiled ff arm keeps its register tests (3 or 1, register s over clbits 0, 1); the manifest's broadcast
    record equals the hand count (lut3 ff and floor: 5 conditionals / 8 bits, 1 broadcast / 2 bits; lut1: 3 / 4, 1 / 2;
    off: 2 / 2, 2 / 2)."""
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    from psf_os import feedforward as FF
    part = json.load(open(os.path.join(a.out, "part.json")))
    m = json.load(open(os.path.join(a.out, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(a.out, "job", "circuits.qpy"), "rb"))
    ref = ideal()["rows"]
    want = {("lut3", "user"): (5, 8, 1, 2), ("lut3", "floor"): (5, 8, 1, 2), ("lut1", "user"): (3, 4, 1, 2),
            ("lut1", "floor"): (3, 4, 1, 2), ("lut5", "user"): (7, 12, 1, 2), ("lut5", "floor"): (7, 12, 1, 2),
            ("lut3", "off"): (2, 2, 2, 2), ("lut1", "off"): (2, 2, 2, 2), ("lut5", "off"): (2, 2, 2, 2)}
    i, bad = 0, []
    for cell in m["cells"]:
        for _ in range(cell["points"]):
            c = cs[i]
            b = m["broadcast"]["per_circuit"][i]
            i += 1
            if cell["role"] == "sentinel":
                ok = b["conditionals"] == 0
                bad += [] if ok else [cell["name"] + " (broadcast)"]
                continue
            tag = cell["name"][3:].replace("_floor", "").replace("_off", "")
            ver, e = tag.split("_")
            cc = FF.compact(c)
            n = cc.num_clbits
            cnt = AerSimulator().run(cc, shots=part["shots"], seed_simulator=SEED).result().get_counts()
            tot = sum(cnt.values())
            allz = sum(v for k, v in cnt.items() if set(_bits(k, n)) == {0}) / tot
            c_zero = sum(v for k, v in cnt.items() if _bits(k, n)[2:] == [0, 0, 0]) / tot
            c0 = sum(v for k, v in cnt.items() if _bits(k, n)[C_BIT] == 0) / tot
            if cell["role"] == "floor":
                ok = allz == 1.0
            elif cell["role"] == "user":
                regs = [ins.operation for ins in c.data if ins.operation.name == "if_else"
                        and type(ins.operation.condition[0]).__name__ == "ClassicalRegister"]
                ok = c_zero == 1.0 and len(regs) == NCOND[ver] - 2 and all(
                    [c.find_bit(x).index for x in op.condition[0]] == [0, 1] for op in regs)
            else:
                ok = abs(c0 - ref[e]["off_c0"]) <= 0.03
            ok = ok and (b["conditionals"], b["condition_bits"], b["broadcasts"], b["broadcast_bits"]) == \
                want[(ver, cell["role"])]
            if not ok or getattr(a, "verbose", False):
                print(f"{cell['name']:16s} {cell['role']:6s} c0 {c0:.3f} c=000 {c_zero:.3f} all0 {allz:.3f} "
                      f"broadcast {b} {'ok' if ok else 'FAIL'}")
            bad += [] if ok else [cell["name"]]
    print(f"{i} circuits; " + ("PASS" if not bad else f"FAIL {bad}"))
    return not bad


def dry(a):
    """Dry runs only, ILLUSTRATIVE noise written by hand: depolarizing p2 on every CZ, damping gamma at each
    mid-circuit read (branch_noise.noisy_circuit), dephasing dephase_cond after every conditional or
    dephase_fired inside a conditional only when it fires (gpu/cond_noise.py), readout p00 / p11."""
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import depolarizing_error
    from psf_os import feedforward as FF
    from psf_os.ibm import _stamp
    from psf_os.sim import to_clifford_gates
    import branch_noise as BN
    import cond_noise as CN
    noise = json.load(open(a.noise))
    job = os.path.join(a.out, "job")
    if os.path.exists(os.path.join(job, "submission.json")):
        raise SystemExit("this job was already run")
    man = json.load(open(os.path.join(job, "manifest.json")))
    rows = []
    for k, c in enumerate(qpy.load(open(os.path.join(job, "circuits.qpy"), "rb"))):
        phys = sorted({q for _, qs in FF.walk(c) for q in qs})
        cc = FF.compact(c)
        seed = a.seed + BN.WIDE_CIRCUIT * k
        cl = None if cc.has_control_flow_op() else to_clifford_gates(cc)
        if cl is not None and cc.num_qubits > FF.LOCAL_MAX_QUBITS:
            res = AerSimulator(method="stabilizer").run(cl, shots=man["shots"], seed_simulator=seed).result()
        else:
            nm = BN.readout_model(phys, noise)
            if noise.get("p2"):
                nm.add_all_qubit_quantum_error(depolarizing_error(float(noise["p2"]), 2), ["cz"])
            nc = CN.dephase_conditionals(BN.noisy_circuit(cc, noise.get("gamma", 0.0)), noise.get("dephase_cond", 0.0),
                                        noise.get("dephase_fired", 0.0))
            res = AerSimulator(method="density_matrix", noise_model=nm).run(nc, shots=man["shots"],
                                                                              seed_simulator=seed).result()
        rows.append(dict(pub=k, counts={key.replace(" ", ""): v for key, v in res.get_counts(0).items()}))
    t = _stamp()
    jid = f"local-illustrative-noise-{a.seed}"
    json.dump(dict(job_id=jid, submitted=t, local=True, backend=man["fetch"]["backend"], noise=noise, seed=a.seed,
                   simulator="aer, ILLUSTRATIVE noise (not fitted to any device)", circuit_stride=BN.WIDE_CIRCUIT),
              open(os.path.join(job, "submission.json"), "w"), indent=1)
    json.dump(dict(fetched=t, job_id=jid, status="DONE (local, illustrative noise)", rows=rows),
              open(os.path.join(job, "raw_counts.json"), "w"))
    print(f"dry run written ({len(rows)} circuits)")


def _pool(cards, arm):
    N = sum(c[arm]["counted"] for c in cards)
    p = sum(c[arm]["success"] for c in cards) / N
    return p, (math.sqrt(p * (1 - p) / N) if 0 < p < 1 else 0.0), N


def ceiling_verdict(p, se, C):
    return "BEYOND THE CEILING" if p >= C + 2 * se else "NOT BEYOND"


def within_verdict(d, se):                         # draft words [OWNER]
    if d < 0 and d <= -2 * se:
        return "MORE TESTS KEEP LESS"
    if d > 0 and d >= 2 * se:
        return "MORE TESTS KEEP MORE"
    return "SAME WITHIN ERROR"


def score(a):
    from psf_os import feedforward as FF
    I = ideal()
    cards = FF.cards(a.out)
    l3 = [cards[f"lut3_{e}"] for e in ERRORS]
    l1 = [cards[f"lut1_{e}"] for e in ERRORS]
    l5 = [cards[f"lut5_{e}"] for e in ERRORS]
    p3, s3, N3 = _pool(l3, "ff")
    p1, s1, N1 = _pool(l1, "ff")
    p5, s5, N5 = _pool(l5, "ff")
    d5, sd5 = p5 - p3, math.sqrt(s5 ** 2 + s3 ** 2)

    def group(es):
        a5, b5, _ = _pool([cards[f"lut5_{e}"] for e in es], "ff")
        a3, b3, _ = _pool([cards[f"lut3_{e}"] for e in es], "ff")
        dd, ss = a5 - a3, math.sqrt(b5 ** 2 + b3 ** 2)
        return dict(errors=list(es), lut5=a5, lut3=a3, d=dd, two_se=2 * ss, verdict=within_verdict(dd, ss))
    # 2026-11-19, after the workplace VS's check: lut5's two added tests (s == 0) fire noiselessly for e = none only,
    # never for e = d0, d1, d2; the two groups are scored apart, beside the pooled d
    groups = dict(added_tests_never_fire=group(("0", "1", "2")), added_tests_fire=group(("n",)))
    groups["added_tests_never_fire"]["label"] = "(b0)"     # the declaration's names (labels added after 2026-11-19)
    groups["added_tests_fire"]["label"] = "(b1)"
    po, so, _ = _pool(l3, "off")
    d, sd = p3 - p1, math.sqrt(s3 ** 2 + s1 ** 2)
    per = {}
    for e in ERRORS:
        c3, c1, c5 = cards[f"lut3_{e}"], cards[f"lut1_{e}"], cards[f"lut5_{e}"]
        per[e] = dict(lut3=c3["ff"]["share"], lut1=c1["ff"]["share"], lut5=c5["ff"]["share"], off=c3["off"]["share"],
                      off_best_rule_after_the_fact=c3.get("off_best_fixed_rule_after_the_fact"),
                      ceiling=I["rows"][e]["ceiling"], floor_all_zero=c3["floor"]["all_zero"])
    out = dict(ceiling=dict(p=p3, two_se=2 * s3, N=N3, C=I["ceiling"], margin=p3 - I["ceiling"],
                            verdict=ceiling_verdict(p3, s3, I["ceiling"])),
               within=dict(lut3=p3, lut1=p1, d=d, two_se=2 * sd, verdict=within_verdict(d, sd)),
               padded=dict(lut5=p5, lut3=p3, d=d5, two_se=2 * sd5, verdict=within_verdict(d5, sd5), groups=groups),
               beside=dict(off_c0=po, per_error=per, sentinel=l3[0]["sentinel"]))
    json.dump(out, open(os.path.join(a.out, "repcode_scores.json"), "w"), indent=1)
    print(f"ceiling: lut3 c[0] right {p3:.4f} (2 SE {2 * s3:.4f}, {N3} shots) against C {I['ceiling']:.4f} -> "
          f"{out['ceiling']['verdict']} (margin {p3 - I['ceiling']:+.4f}); off as read {po:.4f}")
    for nm, g in groups.items():
        print(f"{g['label']} {nm} (e = {', '.join(g['errors'])}): lut5 - lut3 {g['d']:+.4f} (2 SE {g['two_se']:.4f}) -> "
              f"{g['verdict']}" + ("  [judged: RC-2]" if g["label"] == "(b0)" else "  [judged; no direction declared]"))
    print(f"beside, not judged: (a) lut3 {p3:.4f} - lut1 {p1:.4f} = {d:+.4f} (2 SE {2 * sd:.4f}) -> "
          f"{out['within']['verdict']}")
    print(f"beside, not judged: (b) pooled lut5 {p5:.4f} - lut3 {p3:.4f} = {d5:+.4f} (2 SE {2 * sd5:.4f}) -> "
          f"{out['padded']['verdict']}")
    print("per error: " + "; ".join(f"{e}: lut3 {v['lut3']:.3f} lut1 {v['lut1']:.3f} lut5 {v['lut5']:.3f} off {v['off']:.3f}"
                                    for e, v in per.items()) + f"; sentinel {l3[0]['sentinel']}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ideal")
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    b.add_argument("--shots", type=int, default=SHOTS)
    b.add_argument("--dry-clifford-sentinel", action="store_true")
    c = sub.add_parser("check")
    c.add_argument("out")
    c.add_argument("--verbose", action="store_true")
    d = sub.add_parser("dry")
    d.add_argument("out")
    d.add_argument("noise")
    d.add_argument("--seed", type=int, default=SEED)
    sub.add_parser("score").add_argument("out")
    a = ap.parse_args()
    if a.cmd == "ideal":
        I = ideal()
        for e, r in I["rows"].items():
            print(f"error {e}: ff c[0] right lut3 {r['ff']['lut3']:.4f} lut1 {r['ff']['lut1']:.4f} lut5 {r['ff']['lut5']:.4f}"
                  f" (c = 000: {r['ff']['lut3_all_c_zero']:.4f} / {r['ff']['lut1_all_c_zero']:.4f} / "
                  f"{r['ff']['lut5_all_c_zero']:.4f}); off c[0] {r['off_c0']:.4f}; "
                  f"ceiling {r['ceiling']:.4f}")
        print(f"ceiling C = {I['ceiling']:.4f}")
        sys.exit(0)
    r = {"build": build, "check": check, "dry": dry, "score": score}[a.cmd](a)
    sys.exit(0 if r is not False else 1)
