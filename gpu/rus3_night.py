"""The repeat-until-success neuron chain, third design (prereg/rus_neuron3_2026-11-16.md): the second design (m = 2,
outputs in use held flipped around every ancilla measurement) with the last output also read flipped: it is not
flipped back before its measurement, and the declared reading of the last bit is relabelled (1 - bit). Build, pre-run
check, score (needs psf-os at the branch feedforward-2026-11-16, commit 32dc3e5 or later, importable).

  python gpu/rus3_night.py build DEVDIR OUT
  python gpu/rus3_night.py check OUT
  python gpu/rus3_night.py score OUT

Items, theta 1.1, L = 1, 2, 3: "rd{L}" (the third design) and "flip{L}" (the second design, read as there, beside).
The verdict (declared), per L for the rd items, as gpu/rus_night.verdict on P = share of shots whose last output is 1
after the relabelling, every shot of ff and off counted."""
import argparse
import json
import math
import os
import sys

THETA = 1.1
M = 2
LS = (1, 2, 3)
TOL = 0.03


def chain(L, theta, m=M, read_flipped=True):
    """gpu/rus2_night.flip_chain(L, theta, m) (written out here so that the declared tool of the second design stays
    unchanged); with read_flipped the last output is measured without being flipped back (X before its measurement,
    which cancels the last flip back)."""
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
                qc.barrier(a, *live)
                with qc.if_test((c[j * m + r - 1], 1)):
                    qc.ry(math.pi / 2, o)
                    qc.x(a)
                    FF._rus_attempt(qc, a, o, theta, ctrl)
                qc.barrier(a, *live)
            for x in live:
                qc.x(x)
            qc.barrier(a, *live)
            qc.measure(a, j * m + r)
            qc.barrier(a, *live)
            for x in live:
                qc.x(x)
    if read_flipped:
        qc.x(2 * L - 1)
    qc.measure(2 * L - 1, L * m)
    spec = dict(kind="rus", L=L, theta=theta, m=m, out_bit=L * m,
                tries=[list(range(j * m, j * m + m)) for j in range(L)], exact=math.sin(FF.rus_q(theta)) ** (2 * L),
                form="blocks")
    return qc, spec


def items():
    return [(f"rd{L}", *chain(L, THETA)) for L in LS] + [(f"flip{L}", *chain(L, THETA, read_flipped=False)) for L in LS]


def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None   # dry runs only, never a device
    rep = FF.build(Device.load(a.devdir), items(), a.out, shots=4000, sentinel_spec=spec)
    print(json.dumps({k: rep[k] for k in ("device", "circuits", "qpu_seconds_model", "shots") if k in rep}))
    print(json.dumps({t: (v["chain"], v["cz"], v["off_cz"], v["depth"]) for t, v in rep["items"].items()}))


def check(a):
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    from psf_os import feedforward as FF
    from rus2_night import reference
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
            if tag.startswith("rd"):
                p1 = 1 - p1                                      # the declared relabelling of the last bit
            allz = sum(v for k, v in cnt.items() if set(FF._bits(k, n)) == {0}) / tot
            if cell["role"] == "floor":
                ok, r = allz == 1.0, "all zero 1"
            else:
                arm = "ff" if cell["role"] == "user" else "off"
                ok, r = abs(p1 - ref[L][arm]) <= TOL, f"ref {ref[L][arm]:.3f}"
            lines.append(f"{cell['name']:16s} {cell['role']:6s} P(out 1, read as declared) {p1:.3f}  all zero "
                         f"{allz:.3f}  ({r}) {'ok' if ok else 'FAIL'}")
            bad += [] if ok else [cell["name"]]
    print("\n".join(lines))
    print("PASS" if not bad else f"FAIL {bad}")
    return not bad


def relabel(card):
    """The rd card read as declared: P(last output 1) = 1 - P(last bit 1) for ff, off and post."""
    for arm in ("ff", "off", "post"):
        d = card[arm]
        d["p1_measured_bit"] = d["p1"]
        d["p1"] = 1 - d["p1"]
        d["minus_exact"] = d["p1"] - card["exact"]
        d["in_se"] = d["minus_exact"] / (d["two_se"] / 2) if d["two_se"] and d["two_se"] > 0 else None
    return card


def score(a):
    from psf_os import feedforward as FF
    from rus_night import verdict
    cards = FF.cards(a.out)
    out = dict(cards={})
    for tag in [f"rd{L}" for L in LS] + [f"flip{L}" for L in LS]:
        c = relabel(cards[tag]) if tag.startswith("rd") else cards[tag]
        d, se, v = verdict(c)
        c.update(d=d, se_d=se, d_in_se=d / se if se > 0 else None, verdict=v if tag.startswith("rd") else f"beside ({v})")
        out["cards"][tag] = c
        print(f"{tag}: exact {c['exact']:.4f}; ff {c['ff']['p1']:.4f} (still failed after {c['m']} "
              f"{c['ff']['still_failed_after_m']:.4f}); off {c['off']['p1']:.4f}; d {d:.4f} (2 SE_d {2 * se:.4f}) -> "
              f"{c['verdict']}; post {c['post']['p1']:.4f} (kept {c['post']['kept_share']:.4f}); floor all zero "
              f"{c['floor']['all_zero']:.4f}; sentinel {c['sentinel']}")
    gain = {}
    for L in LS:
        r, f = out["cards"][f"rd{L}"]["ff"], out["cards"][f"flip{L}"]["ff"]
        ex = out["cards"][f"rd{L}"]["exact"]
        g = abs(f["p1"] - ex) - abs(r["p1"] - ex)
        se = math.sqrt(r["p1"] * (1 - r["p1"]) / r["counted"] + f["p1"] * (1 - f["p1"]) / f["counted"])
        gain[L] = dict(gain=g, two_se=2 * se)
        print(f"L {L}: ff error read back {f['p1'] - ex:+.4f}, read flipped {r['p1'] - ex:+.4f}; gain {g:+.4f} "
              f"(2 SE {2 * se:.4f})")
    out["read_gain"] = gain
    V = {L: out["cards"][f"rd{L}"]["verdict"] for L in LS}
    out["predictions"] = {
        "1 L = 1: read gain positive and >= 2 SE": "held" if gain[1]["gain"] > 0 and gain[1]["gain"] >= gain[1][
            "two_se"] else "failed",
        "2 L = 1, 2, 3 (rd): CLOSER WITH CONTROL": "held" if all(V[L] == "CLOSER WITH CONTROL" for L in LS)
        else "failed",
    }
    print("predictions:", out["predictions"])
    json.dump(out, open(os.path.join(a.out, "rus3_scores.json"), "w"), indent=1)


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
