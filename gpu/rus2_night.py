"""The repeat-until-success neuron chain, second design (prereg/rus_neuron2_2026-11-16.md): fewer waits (m = 2 tries)
and the outputs held flipped during every mid-circuit measurement, so that the likely value 1 waits as |0>. Build,
pre-run check, score (needs psf-os at the branch feedforward-2026-11-16, commit 32dc3e5 or later, importable).

  python gpu/rus2_night.py build DEVDIR OUT
  python gpu/rus2_night.py check OUT
  python gpu/rus2_night.py score OUT

Items, theta 1.1, L = 1, 2, 3: "flip{L}" (m = 2, outputs flipped around every measurement) and "m2_{L}" (m = 2,
the same circuit without the X pairs, beside). Both carry barriers on the ancilla and the outputs in use around every
ancilla measurement, so that the compiler keeps the X pairs and the two designs wait the same. Each with the ff, off and floor arms of psf_os.feedforward.build.
The flip: before each measurement of neuron j's ancilla, X on the outputs still in use (neuron j's own and neuron
j-1's, the control of neuron j's retries), and X on them again right after it; X X = 1, so the ideal circuit is that
of rus_chain(L, 1.1, m=2) exactly, and the off arm (blocks removed) keeps the X pairs.

The verdict (declared), per L for the flip items, every shot of both arms counted:
  d = |P_off - exact| - |P_ff - exact|, SE_d = sqrt(P_ff (1 - P_ff) / N + P_off (1 - P_off) / N),
  CLOSER WITH CONTROL when d >= 2 SE_d, otherwise NOT CLOSER (gpu/rus_night.verdict)."""
import argparse
import json
import math
import os
import sys

THETA = 1.1
M = 2
LS = (1, 2, 3)
TOL = 0.03


def flip_chain(L, theta, m=M, flip=True):
    """rus_chain(L, theta, m) with barriers on the ancilla and the outputs in use around every ancilla measurement
    (so that the compiler keeps each X pair and the waits are the same in both designs), and with flip=True the outputs
    in use flipped by X before the measurement and back after it."""
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
    from psf_os import feedforward as FF
    q, c = QuantumRegister(2 * L, "q"), ClassicalRegister(L * m + 1, "c")
    qc = QuantumCircuit(q, c)
    for j in range(L):
        a, o, ctrl = 2 * j, 2 * j + 1, (None if j == 0 else 2 * j - 1)
        live = [o] if ctrl is None else [ctrl, o]
        FF._rus_attempt(qc, a, o, theta, ctrl)
        for r in range(m):
            if r > 0:
                qc.barrier(a, *live)                    # keeps the X pairs apart in the off arm (block removed)
                with qc.if_test((c[j * m + r - 1], 1)):
                    qc.ry(math.pi / 2, o)
                    qc.x(a)
                    FF._rus_attempt(qc, a, o, theta, ctrl)
                qc.barrier(a, *live)
            if flip:
                for x in live:
                    qc.x(x)
            qc.barrier(a, *live)
            qc.measure(a, j * m + r)
            qc.barrier(a, *live)
            if flip:
                for x in live:
                    qc.x(x)
    qc.measure(2 * L - 1, L * m)
    spec = dict(kind="rus", L=L, theta=theta, m=m, out_bit=L * m,
                tries=[list(range(j * m, j * m + m)) for j in range(L)], exact=math.sin(FF.rus_q(theta)) ** (2 * L),
                form="blocks")
    return qc, spec


def items():
    out = []
    for L in LS:
        out.append((f"flip{L}", *flip_chain(L, THETA)))
    for L in LS:
        out.append((f"m2_{L}", *flip_chain(L, THETA, flip=False)))
    return out


def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None   # dry runs only, never a device
    rep = FF.build(Device.load(a.devdir), items(), a.out, shots=4000, sentinel_spec=spec)
    print(json.dumps({k: rep[k] for k in ("device", "circuits", "qpu_seconds_model", "shots") if k in rep}))
    print(json.dumps({t: (v["chain"], v["cz"], v["off_cz"], v["depth"]) for t, v in rep["items"].items()}))


def reference():
    """Noiseless P(last output 1) of the ff and off arms of rus_chain(L, 1.1, m=2) (logical circuits, Aer, 200000
    shots, fixed seed): the pre-run check's reference, the same for both designs."""
    from qiskit_aer import AerSimulator
    from psf_os import feedforward as FF
    ref = {}
    for L in LS:
        qc, sp = FF.rus_chain(L, THETA, m=M)
        row = {}
        for arm, circ in (("ff", FF.lower(qc)), ("off", FF.strip_conditionals(FF.lower(qc)))):
            cnt = AerSimulator().run(circ, shots=200000, seed_simulator=7).result().get_counts()
            n = circ.num_clbits
            row[arm] = sum(v for k, v in cnt.items() if FF._bits(k, n)[sp["out_bit"]] == 1) / sum(cnt.values())
        ref[L] = row
    return ref


def check(a):
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    from psf_os import feedforward as FF
    ref = reference()
    m = json.load(open(os.path.join(a.out, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(a.out, "job", "circuits.qpy"), "rb"))
    i, bad, lines = 0, [], []
    for cell in m["cells"]:
        for _ in range(cell["points"]):
            c = cs[i]
            i += 1
            if cell["role"] == "sentinel":
                continue
            tag = cell["name"].split("_", 1)[1].replace("_floor", "").replace("_off", "")
            L = int(tag[-1])
            cc = FF.compact(c)
            n = cc.num_clbits
            cnt = AerSimulator().run(cc, shots=4000, seed_simulator=20261116).result().get_counts()
            tot = sum(cnt.values())
            p1 = sum(v for k, v in cnt.items() if FF._bits(k, n)[L * M] == 1) / tot
            allz = sum(v for k, v in cnt.items() if set(FF._bits(k, n)) == {0}) / tot
            if cell["role"] == "floor":
                ok, r = allz == 1.0, "all zero 1"
            else:
                arm = "ff" if cell["role"] == "user" else "off"
                ok, r = abs(p1 - ref[L][arm]) <= TOL, f"ref {ref[L][arm]:.3f}"
            lines.append(f"{cell['name']:16s} {cell['role']:6s} P(out 1) {p1:.3f}  all zero {allz:.3f}  ({r}) "
                         f"{'ok' if ok else 'FAIL'}")
            bad += [] if ok else [cell["name"]]
    print("\n".join(lines))
    print("PASS" if not bad else f"FAIL {bad}")
    return not bad


def score(a):
    from psf_os import feedforward as FF
    from rus_night import verdict
    cards = FF.cards(a.out)
    out = dict(cards={}, predictions={})
    for tag in [f"flip{L}" for L in LS] + [f"m2_{L}" for L in LS]:
        c = cards[tag]
        d, se, v = verdict(c)
        c.update(d=d, se_d=se, d_in_se=d / se if se > 0 else None,
                 verdict=v if tag.startswith("flip") else f"beside ({v})")
        out["cards"][tag] = c
        print(f"{tag}: exact {c['exact']:.4f}; ff {c['ff']['p1']:.4f} (still failed after {c['m']} "
              f"{c['ff']['still_failed_after_m']:.4f}); off {c['off']['p1']:.4f}; d {d:.4f} (2 SE_d {2 * se:.4f}) -> "
              f"{c['verdict']}; post {c['post']['p1']:.4f} (kept {c['post']['kept_share']:.4f}); floor all zero "
              f"{c['floor']['all_zero']:.4f}; sentinel {c['sentinel']}")
    flip_gain = {}
    for L in LS:
        f, g = out["cards"][f"flip{L}"]["ff"], out["cards"][f"m2_{L}"]["ff"]
        ex = out["cards"][f"flip{L}"]["exact"]
        gain = abs(g["p1"] - ex) - abs(f["p1"] - ex)
        se = math.sqrt(f["p1"] * (1 - f["p1"]) / f["counted"] + g["p1"] * (1 - g["p1"]) / g["counted"])
        flip_gain[L] = dict(gain=gain, two_se=2 * se)
        print(f"L {L}: ff error without flip {g['p1'] - ex:+.4f}, with flip {f['p1'] - ex:+.4f}; gain {gain:+.4f} "
              f"(2 SE {2 * se:.4f})")
    out["flip_gain"] = flip_gain
    V = {L: out["cards"][f"flip{L}"]["verdict"] for L in LS}
    out["predictions"] = {
        "1 L = 2: CLOSER WITH CONTROL": "held" if V[2] == "CLOSER WITH CONTROL" else "failed",
        "2 L = 3: CLOSER WITH CONTROL": "held" if V[3] == "CLOSER WITH CONTROL" else "failed",
        "3 flip gain positive and >= 2 SE at L = 2 and L = 3": "held" if all(
            flip_gain[L]["gain"] > 0 and flip_gain[L]["gain"] >= flip_gain[L]["two_se"] for L in (2, 3)) else "failed",
    }
    print("predictions:", out["predictions"])
    json.dump(out, open(os.path.join(a.out, "rus2_scores.json"), "w"), indent=1)


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
