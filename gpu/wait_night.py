"""Where the repeat-until-success neuron lost its value: the cost of mid-circuit measurements and of conditionals on a
neighbouring qubit that holds a state (prereg/wait_diag_2026-11-16.md). Build, pre-run check, score (needs psf-os at
the branch feedforward-2026-11-16, commit 32dc3e5 or later, importable).

  python gpu/wait_night.py build DEVDIR OUT
  python gpu/wait_night.py check OUT        noiseless Aer of every arm but the sentinel; PASS / FAIL
  python gpu/wait_night.py score OUT        shares, the declared differences, the predictions

Two positions of the neuron chain of 2026-11-16 (placement by rule C, as there): A = ancilla q_chain[0], output
q_chain[1] (neuron 0's pair); B = ancilla q_chain[4], output q_chain[5] (neuron 2's pair at L = 3). Per position:
  ref   X on the output, measure it at once (no mid-circuit measurement);
  wT    X on the output; three measurements of the ancilla, each followed (ff arm) by a conditional X on the ancilla
        that ideally never fires; the output measured last. The off arm (no conditionals) is the same with the
        measurements only;
  wP    as wT, but the output is turned by RY(-pi/2) before the waits and again by RY(-pi/2) after them (it holds
        a superposition through the waits, as after a failed neuron attempt).
Ideal: the output reads 1 in every shot of every ff and off arm (a conditional that fires on a misread ancilla acts on
the ancilla only). Barriers on both qubits keep the output's gates on their side of the waits."""
import argparse
import json
import math
import os
import sys

POS = dict(A=(2, 0, 1), B=(6, 4, 5))       # position: (qubits in the item, ancilla, output)
MIDS = 3


def item(kind, n, a, o):
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
    if kind == "ref":
        qc = QuantumCircuit(QuantumRegister(n, "q"), ClassicalRegister(1, "c"))
        qc.x(o)
        qc.measure(o, 0)
        return qc, dict(success={0: 1}, bound=None, form="pauli")
    qc = QuantumCircuit(QuantumRegister(n, "q"), ClassicalRegister(MIDS + 1, "c"))
    c = qc.cregs[0]
    if kind == "wT":
        qc.x(o)
    else:
        qc.ry(-math.pi / 2, o)
    qc.barrier(a, o)
    for r in range(MIDS):
        qc.measure(a, r)
        if r < MIDS - 1:
            with qc.if_test((c[r], 1)):
                qc.x(a)
        qc.barrier(a, o)
    if kind == "wP":
        qc.ry(-math.pi / 2, o)
    qc.measure(o, MIDS)
    return qc, dict(success={MIDS: 1}, bound=None, form="pauli")


def items():
    out = []
    for p, (n, a, o) in POS.items():
        for kind in ("ref", "wT", "wP"):
            qc, spec = item(kind, n, a, o)
            out.append((f"{p}{kind}", qc, spec))
    return out


def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    dev = Device.load(a.devdir)
    rep = FF.build(dev, items(), a.out, shots=4000)
    print(json.dumps({k: rep[k] for k in ("device", "circuits", "qpu_seconds_model", "shots") if k in rep}))
    print(json.dumps({t: v["chain"] for t, v in rep["items"].items()}))


def check(a):
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    from psf_os import feedforward as FF
    m = json.load(open(os.path.join(a.out, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(a.out, "job", "circuits.qpy"), "rb"))
    i, bad, lines = 0, [], []
    for cell in m["cells"]:
        for _ in range(cell["points"]):
            c = cs[i]
            i += 1
            if cell["role"] == "sentinel":
                continue
            cc = FF.compact(c)
            n = cc.num_clbits
            counts = AerSimulator().run(cc, shots=4000, seed_simulator=20261116).result().get_counts()
            tot = sum(counts.values())
            p1 = sum(v for k, v in counts.items() if FF._bits(k, n)[n - 1] == 1) / tot
            allz = sum(v for k, v in counts.items() if set(FF._bits(k, n)) == {0}) / tot
            ok = allz == 1.0 if cell["role"] == "floor" else p1 == 1.0
            lines.append(f"{cell['name']:14s} {cell['role']:6s} P(out 1) {p1:.3f}  all zero {allz:.3f}  "
                         f"{'ok' if ok else 'FAIL'}")
            bad += [] if ok else [cell["name"]]
    print("\n".join(lines))
    print("PASS" if not bad else f"FAIL {bad}")
    return not bad


def diff(x, y):
    """x - y for two shares with their counts, and two SE of the difference."""
    d = x["share"] - y["share"]
    se = math.sqrt(x["share"] * (1 - x["share"]) / x["counted"] + y["share"] * (1 - y["share"]) / y["counted"])
    return dict(d=d, two_se=2 * se, beyond_2se=abs(d) >= 2 * se)


def score(a):
    from psf_os import feedforward as FF
    cards = FF.cards(a.out)
    out = dict(cards=cards, positions={})
    for p in POS:
        ref, wT, wP = cards[f"{p}ref"]["ff"], cards[f"{p}wT"], cards[f"{p}wP"]
        sh = dict(ref=ref, T_mid=wT["off"], T_ff=wT["ff"], P_mid=wP["off"], P_ff=wP["ff"])
        d = dict(meas=diff(sh["ref"], sh["T_mid"]), cond=diff(sh["T_mid"], sh["T_ff"]),
                 phase_mid=diff(sh["T_mid"], sh["P_mid"]), phase_ff=diff(sh["T_ff"], sh["P_ff"]))
        out["positions"][p] = dict(shares={k: v["share"] for k, v in sh.items()}, differences=d,
                                   output_qubit=cards[f"{p}wT"]["chain"][POS[p][2]])
        print(f"position {p} (output on q{out['positions'][p]['output_qubit']}): "
              + "; ".join(f"{k} {v['share']:.4f}" for k, v in sh.items()))
        for k, v in d.items():
            print(f"  D_{k} {v['d']:+.4f} (2 SE {v['two_se']:.4f})")
    A, B = out["positions"]["A"], out["positions"]["B"]
    pred = {
        "1 position A: D_cond >= 2 SE": A["differences"]["cond"]["d"] >= A["differences"]["cond"]["two_se"],
        "2 ref at A below ref at B by >= 2 SE": (B["shares"]["ref"] - A["shares"]["ref"]) >= diff(
            cards["Bref"]["ff"], cards["Aref"]["ff"])["two_se"],
    }
    out["predictions"] = {k: ("held" if v else "failed") for k, v in pred.items()}
    for p in POS:
        dc, dp = out["positions"][p]["differences"]["cond"], out["positions"][p]["differences"]["phase_ff"]
        out["positions"][p]["reading"] = ("waits" if dc["d"] >= dp["d"] else "phase")
    print("predictions:", out["predictions"])
    print("reading (declared rule: the larger of D_cond and D_phase_ff):",
          {p: out["positions"][p]["reading"] for p in POS})
    json.dump(out, open(os.path.join(a.out, "wait_scores.json"), "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    for nm in ("check", "score"):
        s = sub.add_parser(nm)
        s.add_argument("out")
    a = ap.parse_args()
    r = {"build": build, "check": check, "score": score}[a.cmd](a)
    sys.exit(0 if r is not False else 1)
