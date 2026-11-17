"""The repeat-until-success neuron without mid-circuit measurements against the third design (prereg/ff_night_2026-11-17.md,
test T1). Build, pre-run check, score (needs psf-os at the branch feedforward-2026-11-16, commit 301ac01 or later).

  python gpu/coh_night.py build DEVDIR OUT [--dry-clifford-sentinel]
  python gpu/coh_night.py check OUT
  python gpu/coh_night.py score OUT

Items (theta 1.1, L = 1, m = 2, 4000 shots):
  coh1  the workplace's zipper+ line (notes/rus_coherent_2026-11-17/coherent.zipper(1, 1.1, 2, plus=True)): no
        mid-circuit measurement; with two changes from the workplace draft (home, 2026-11-17):
        (1) its off arm (try 0 only) moves the output onto the same line position as the ff arm before it is read
            (2 CX onto the untouched |0>), so both arms read the output on the same physical qubit;
        (2) the output is read flipped (X before its measurement) and the last bit relabelled 1 - bit in both arms,
            as the third design reads its output.
  rd1   the third design of 2026-11-16 (gpu/rus3_night.chain(1, 1.1, 2)), read with its declared relabelling.
Verdict per item (declared): gpu/rus_night.verdict on the relabelled cards (CLOSER WITH CONTROL / NOT CLOSER).
Beside (never judged): |P_ff - noiseless m = 2 value| of each item and the difference with its two SE."""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "notes", "rus_coherent_2026-11-17"))

THETA, L, M = 1.1, 1, 2
SHOTS = 4000
TOL = 0.03


def coherent_item(theta=THETA, m=M):
    """(ff circuit, spec with the explicit off arm) for coh1, L = 1."""
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
    from psf_os import feedforward as FF
    import coherent as CO

    def finish(line, meas, out_pos):
        b = CO.to_basis(line)
        qc = QuantumCircuit(QuantumRegister(b.num_qubits, "q"), ClassicalRegister(m + 1, "c"))
        qc.compose(b, inplace=True)
        qc.x(out_pos)                                   # read the output flipped (relabelled 1 - bit in the score)
        for p, bit in meas:
            qc.measure(p, bit)
        return qc

    ff_line, ff_meas = CO.zipper(1, theta, m, plus=True)
    out_pos = dict((bit, p) for p, bit in ff_meas)[m]
    off_line, _ = CO.zipper(1, theta, m, plus=True, tries=1)
    src = 1                                             # after try 0 the output stands at line position 1
    for dst in range(2, out_pos + 1):                   # step it onto the ff arm's output position (fresh |0>s)
        CO._move(off_line, src, dst)
        src = dst
    ff = finish(ff_line, ff_meas, out_pos)
    off = finish(off_line, ff_meas, out_pos)            # the same measured positions as the ff arm
    spec = dict(kind="rus", L=1, theta=theta, m=m, out_bit=m, tries=[list(range(m))],
                exact=math.sin(FF.rus_q(theta)) ** 2, off_circuit=off)
    return ff, spec


def items():
    import rus3_night as R3
    return [("coh1", *coherent_item()), ("rd1", *R3.chain(L, THETA, m=M))]


def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None   # dry runs only, never a device
    rep = FF.build(Device.load(a.devdir), items(), a.out, shots=SHOTS, sentinel_spec=spec)
    print(json.dumps({k: rep[k] for k in ("device", "circuits", "qpu_seconds_model", "shots") if k in rep}))
    print(json.dumps({t: (v["chain"], v["cz"], v["off_cz"], v["depth"], v["mid"]) for t, v in rep["items"].items()}))


def _p_out(cnt, n, bit):
    from psf_os import feedforward as FF
    tot = sum(cnt.values())
    return 1 - sum(v for k, v in cnt.items() if FF._bits(k, n)[bit] == 1) / tot      # read as declared (1 - bit)


def check(a):
    """Noiseless Aer of every arm but the sentinel, read as declared, against the noiseless m = 2 values."""
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    from psf_os import feedforward as FF
    from rus2_night import reference
    ref = reference()[1]
    m = json.load(open(os.path.join(a.out, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(a.out, "job", "circuits.qpy"), "rb"))
    b = json.load(open(os.path.join(a.out, "build.json")))
    i, bad, lines = 0, [], []
    for cell in m["cells"]:
        for _ in range(cell["points"]):
            c = cs[i]
            i += 1
            if cell["role"] == "sentinel":
                continue
            cc = FF.compact(c)
            n = cc.num_clbits
            cnt = AerSimulator().run(cc, shots=SHOTS, seed_simulator=20261117).result().get_counts()
            p1 = _p_out(cnt, n, M)
            allz = sum(v for k, v in cnt.items() if set(FF._bits(k, n)) == {0}) / sum(cnt.values())
            if cell["role"] == "floor":
                ok, r = allz == 1.0, "all zero 1"
            else:
                arm = "ff" if cell["role"] == "user" else "off"
                ok, r = abs(p1 - ref[arm]) <= TOL, f"ref {ref[arm]:.3f}"
            lines.append(f"{cell['name']:14s} {cell['role']:6s} P(out 1, read as declared) {p1:.3f}  all zero "
                         f"{allz:.3f}  ({r}) {'ok' if ok else 'FAIL'}")
            bad += [] if ok else [cell["name"]]
    # both arms of coh1 read the output on the same physical qubit
    q = {}
    i = 0
    for cell in m["cells"]:
        for _ in range(cell["points"]):
            c = cs[i]
            i += 1
            if cell["name"] in ("ff_coh1", "ff_coh1_off"):
                q[cell["name"]] = [c.find_bit(x.qubits[0]).index for x in c.data
                                   if x.operation.name == "measure" and c.find_bit(x.clbits[0]).index == M]
    same = q.get("ff_coh1") == q.get("ff_coh1_off") and q.get("ff_coh1")
    lines.append(f"coh1 output read on physical qubit: ff {q.get('ff_coh1')}, off {q.get('ff_coh1_off')} "
                 f"{'ok' if same else 'FAIL'}")
    bad += [] if same else ["coh1 readout qubit"]
    print("\n".join(lines))
    print("PASS" if not bad else f"FAIL {bad}")
    return not bad


def score(a):
    from psf_os import feedforward as FF
    import rus3_night as R3
    from rus_night import verdict
    from rus2_night import reference
    ref = reference()[1]
    cards = FF.cards(a.out)
    out = dict(cards={}, beside={})
    for tag in ("coh1", "rd1"):
        c = R3.relabel(cards[tag])
        d, se, v = verdict(c)
        c.update(d=d, se_d=se, d_in_se=d / se if se > 0 else None, verdict=v,
                 loss_vs_noiseless=c["ff"]["p1"] - ref["ff"])
        out["cards"][tag] = c
        print(f"{tag}: exact {c['exact']:.4f}; ff {c['ff']['p1']:.4f} (noiseless m = 2 {ref['ff']:.4f}, loss "
              f"{c['ff']['p1'] - ref['ff']:+.4f}); off {c['off']['p1']:.4f}; d {d:.4f} (2 SE_d {2 * se:.4f}) -> {v}; "
              f"post {c['post']['p1']:.4f} (kept {c['post']['kept_share']:.4f}); floor all zero "
              f"{c['floor']['all_zero']:.4f}; sentinel {c['sentinel']}")
    f, r = out["cards"]["coh1"]["ff"], out["cards"]["rd1"]["ff"]
    gap = abs(r["p1"] - ref["ff"]) - abs(f["p1"] - ref["ff"])
    se = math.sqrt(f["p1"] * (1 - f["p1"]) / f["counted"] + r["p1"] * (1 - r["p1"]) / r["counted"])
    out["beside"] = dict(coh_closer_to_noiseless_by=gap, two_se=2 * se)
    print(f"beside: |rd1 - noiseless| - |coh1 - noiseless| = {gap:+.4f} (2 SE {2 * se:.4f})")
    V = {t: out["cards"][t]["verdict"] for t in ("coh1", "rd1")}
    out["predictions"] = {"T1-1 coh1 CLOSER WITH CONTROL": "held" if V["coh1"] == "CLOSER WITH CONTROL" else "failed",
                          "T1-2 rd1 CLOSER WITH CONTROL": "held" if V["rd1"] == "CLOSER WITH CONTROL" else "failed"}
    print("predictions:", out["predictions"])
    json.dump(out, open(os.path.join(a.out, "coh_scores.json"), "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    b.add_argument("--dry-clifford-sentinel", action="store_true",
                   help="dry runs only: the ring sentinel at its Clifford point; never for the device job")
    for nm in ("check", "score"):
        sub.add_parser(nm).add_argument("out")
    a = ap.parse_args()
    r = {"build": build, "check": check, "score": score}[a.cmd](a)
    sys.exit(0 if r is not False else 1)
