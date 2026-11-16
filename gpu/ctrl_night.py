"""Does a control qubit keep its |1> until a late use, and is the loss from time or from reading its neighbours?
(prereg/ctrl_diag_2026-11-16.md). Build, pre-run check, score (needs psf-os at the branch feedforward-2026-11-16,
commit 32dc3e5 or later, importable).

  python gpu/ctrl_night.py build DEVDIR OUT
  python gpu/ctrl_night.py check OUT        noiseless Aer of every arm but the sentinel; PASS / FAIL
  python gpu/ctrl_night.py score OUT

One 6-qubit chain placed by rule C (the neuron chain's qubits at L = 3). Two positions: A = control on chain qubit 1
(neuron 0's output, the control of neuron 1's retries), target chain qubit 2, neighbours read: chain qubits 0 and 2,
far qubit: chain qubit 5; B = control chain qubit 3, target 4, neighbours 2 and 4, far qubit 0. Per position:
  now     X on the control; CX(control, target) at once; measure target and control;
  far     X on the control; five measurements of the far qubit (barriers hold the control and the target idle meanwhile); CX;
          measure target and control;
  nb      X on the control; three measurements of the first neighbour and two of the target (as neuron j's and
          neuron j+1's tries); CX; measure target and control.
Ideal: target and control read 1 in every shot. The target reads the control's |1> at the moment of the CX, through
the target's readout, not the control's. CX is written H CZ H."""
import argparse
import json
import math
import os
import sys

N = 6
POS = dict(A=dict(c=1, t=2, nb=0, far=5), B=dict(c=3, t=4, nb=2, far=0))
KINDS = ("now", "far", "nb")


def item(kind, p):
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
    c, t, nb, far = p["c"], p["t"], p["nb"], p["far"]
    mids = 0 if kind == "now" else 5
    qc = QuantumCircuit(QuantumRegister(N, "q"), ClassicalRegister(mids + 2, "m"))
    qc.x(c)
    if kind == "far":
        qc.barrier(c, t, far)
        for r in range(5):
            qc.measure(far, r)
            qc.barrier(c, t, far)
    elif kind == "nb":
        qc.barrier(c, t, nb)
        for r in range(3):
            qc.measure(nb, r)
            qc.barrier(c, t, nb)
        for r in range(3, 5):
            qc.measure(t, r)
            qc.barrier(c, t, nb)
    qc.h(t)
    qc.cz(min(c, t), max(c, t))
    qc.h(t)
    qc.measure(t, mids)
    qc.measure(c, mids + 1)
    return qc, dict(success={mids: 1}, bound=None, form="pauli")


def items():
    return [(f"{p}{k}", *item(k, POS[p])) for p in POS for k in KINDS]


def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    rep = FF.build(Device.load(a.devdir), items(), a.out, shots=4000)
    print(json.dumps({k: rep[k] for k in ("device", "circuits", "qpu_seconds_model", "shots") if k in rep}))
    print(json.dumps({t: v["chain"] for t, v in rep["items"].items()}))


def _counts(out):
    """{(tag, arm): counts} from the job's raw counts."""
    from psf_os import job as J
    read = J.read(os.path.join(out, "job"), os.path.join(out, "runs"))
    got = {}
    for name, (rec, cc) in read.items():
        if rec.get("psfos_job", {}).get("kind", "").startswith("feedforward"):
            got[(rec["tag"], rec["ff_arm"])] = (rec["clbits"], cc[("f", "z")])
    return got


def share(n, counts, bit):
    from psf_os import feedforward as FF
    tot = sum(counts.values())
    p = sum(v for k, v in counts.items() if FF._bits(k, n)[bit] == 1) / tot
    return dict(share=p, counted=tot, two_se=2 * math.sqrt(p * (1 - p) / tot))


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
            cnt = AerSimulator().run(cc, shots=4000, seed_simulator=20261116).result().get_counts()
            pt, pc = share(n, cnt, n - 2)["share"], share(n, cnt, n - 1)["share"]
            allz = sum(v for k, v in cnt.items() if set(FF._bits(k, n)) == {0}) / sum(cnt.values())
            ok = allz == 1.0 if cell["role"] == "floor" else (pt == 1.0 and pc == 1.0)
            lines.append(f"{cell['name']:14s} {cell['role']:6s} target 1 {pt:.3f}  control 1 {pc:.3f}  "
                         f"all zero {allz:.3f}  {'ok' if ok else 'FAIL'}")
            bad += [] if ok else [cell["name"]]
    print("\n".join(lines))
    print("PASS" if not bad else f"FAIL {bad}")
    return not bad


def diff(x, y):
    d = x["share"] - y["share"]
    se = math.sqrt(x["share"] * (1 - x["share"]) / x["counted"] + y["share"] * (1 - y["share"]) / y["counted"])
    return dict(d=d, two_se=2 * se, beyond_2se=abs(d) >= 2 * se)


def loss(dd):
    """A loss beyond two SE: the difference is positive and at least two SE of it."""
    return dd["d"] > 0 and dd["d"] >= dd["two_se"]


def score(a):
    from psf_os import feedforward as FF
    got = _counts(a.out)
    sent = FF.cards(a.out)
    out = dict(positions={}, sentinel=next(iter(sent.values()))["sentinel"], floor={})
    for (tag, arm), (n, cnt) in sorted(got.items()):
        if arm == "floor":
            out["floor"][tag] = sum(v for k, v in cnt.items() if set(FF._bits(k, n)) == {0}) / sum(cnt.values())
    for p in POS:
        sh = {}
        for k in KINDS:
            for arm, lab in (("ff", ""), ("off", "_repeat")):
                n, cnt = got[(f"{p}{k}", arm)]
                sh[f"{k}{lab}"] = dict(target=share(n, cnt, n - 2), control=share(n, cnt, n - 1))
        d = dict(late_far=diff(sh["now"]["target"], sh["far"]["target"]),
                 late_nb=diff(sh["now"]["target"], sh["nb"]["target"]),
                 nb_beyond_time=diff(sh["far"]["target"], sh["nb"]["target"]))
        out["positions"][p] = dict(shares=sh, differences=d)
        print(f"position {p} (control chain qubit {POS[p]['c']}):")
        for k, v in sh.items():
            print(f"  {k:11s} target 1 {v['target']['share']:.4f} (2 SE {v['target']['two_se']:.4f})  "
                  f"control 1 {v['control']['share']:.4f}")
        for k, v in d.items():
            print(f"  D_{k} {v['d']:+.4f} (2 SE {v['two_se']:.4f})")
        dn, df = d["nb_beyond_time"], d["late_far"]
        out["positions"][p]["reading"] = ("reading the neighbours" if loss(dn) else "time" if loss(df) else
                                          "neither beyond 2 SE")
    A = out["positions"]["A"]["differences"]
    out["predictions"] = {"1 position A: D_late_nb >= 2 SE": "held" if loss(A["late_nb"]) else "failed"}
    print("predictions:", out["predictions"])
    print("reading (declared rule):", {p: out["positions"][p]["reading"] for p in POS})
    print("floor all zero:", {k: round(v, 4) for k, v in out["floor"].items()}, "sentinel", out["sentinel"])
    json.dump(out, open(os.path.join(a.out, "ctrl_scores.json"), "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    for nm in ("check", "score"):
        sub.add_parser(nm).add_argument("out")
    a = ap.parse_args()
    r = {"build": build, "check": check, "score": score}[a.cmd](a)
    sys.exit(0 if r is not False else 1)
