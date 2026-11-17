"""A frame-balanced neuron chain (desk tool for a future declaration; prereg/drafts-2026-11-17/balanced_DRAFT.md).

Decay during the waits and on readout moves |1> to |0> only. A design that holds the likely value 1 as |0> (the third
design, rd) turns that one-sided decay into a lift toward success and can overshoot its own noiseless value (N2 at
L = 1, 7 and the OS loop at L = 1, 2026-11-17). Here every L runs in two complementary frames in one job:
  rd{L}  gpu/rus3_night.chain(L, 1.1, 2): outputs in use flipped around every ancilla measurement, last output read
         flipped and relabelled (logical 1 waits and is read as |0>);
  nf{L}  gpu/rus2_night.flip_chain(L, 1.1, flip=False): the same barriers and waits, no flips, read as it is (logical 1
         waits and is read as |1>).
The verdict uses the pooled value P = (P_rd + P_nf) / 2 (4000 shots each): in each frame every logical value spends
the same time as |1>, so one-sided decay acts on the pool like a symmetric flip, which pulls toward 1/2 and cannot lift
P above the noiseless value when that value is above 1/2 (checked under the workplace VS's illustrative decay model:
pooled at or below its noiseless value at every L = 1 .. 5 and gamma 0 .. 0.14, notes/next_2026-11-17/BALANCED.md).

  python gpu/balanced_night.py build DEVDIR OUT [--dry-clifford-sentinel]
  python gpu/balanced_night.py check OUT
  python gpu/balanced_night.py score OUT"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(NB, "notes", "compound_2026-11-17"))
LS = (1, 2, 3, 4, 5)
THETA, M, TOL = 1.1, 2, 0.03


def ref():
    return {int(k): v for k, v in json.load(open(os.path.join(NB, "notes", "next_2026-11-17", "ideal7.json"))).items()}


def items():
    import rus2_night as R2
    import rus3_night as R3
    out = []
    for L in LS:
        out.append((f"rd{L}", *R3.chain(L, THETA, m=M)))
        out.append((f"nf{L}", *R2.flip_chain(L, THETA, flip=False)))
    return out


def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None   # dry runs only, never a device
    rep = FF.build(Device.load(a.devdir), items(), a.out, shots=4000, max_seconds=60, sentinel_spec=spec)
    print(json.dumps({k: rep[k] for k in ("device", "circuits", "qpu_seconds_model", "shots") if k in rep}))


def check(a):
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    from psf_os import feedforward as FF
    R = ref()
    m = json.load(open(os.path.join(a.out, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(a.out, "job", "circuits.qpy"), "rb"))
    i, bad = 0, []
    for cell in m["cells"]:
        for _ in range(cell["points"]):
            c = cs[i]
            i += 1
            if cell["role"] == "sentinel":
                continue
            tag = cell["name"].split("_")[1]
            L = int(tag[2:])
            cc = FF.compact(c)
            n = cc.num_clbits
            cnt = AerSimulator().run(cc, shots=4000, seed_simulator=20261117).result().get_counts()
            tot = sum(cnt.values())
            p = sum(v for k, v in cnt.items() if FF._bits(k, n)[L * M] == 1) / tot
            if tag.startswith("rd"):
                p = 1 - p
            allz = sum(v for k, v in cnt.items() if set(FF._bits(k, n)) == {0}) / tot
            ok = allz == 1.0 if cell["role"] == "floor" else abs(p - R[L]["ff" if cell["role"] == "user" else "off"]) <= TOL
            print(f"{cell['name']:14s} {cell['role']:6s} P(out 1, read as declared) {p:.3f} all zero {allz:.3f} "
                  f"{'ok' if ok else 'FAIL'}")
            bad += [] if ok else [cell["name"]]
    print("PASS" if not bad else f"FAIL {bad}")
    return not bad


def score(a):
    import compound as CP
    import rus3_night as R3
    from psf_os import feedforward as FF
    R = ref()
    cards = FF.cards(a.out)
    rows, over = {}, []
    for L in LS:
        rd, nf = R3.relabel(cards[f"rd{L}"]), cards[f"nf{L}"]
        p3, n3, p1, n1 = rd["ff"]["p1"], rd["ff"]["counted"], nf["ff"]["p1"], nf["ff"]["counted"]
        p = (p3 + p1) / 2
        se = math.sqrt(p3 * (1 - p3) / n3 + p1 * (1 - p1) / n1) / 2
        ex, c = R[L]["exact"], R[L]["ceiling"]
        g = c - abs(p - ex)
        o = p > R[L]["ff"] + 2 * se
        v = "OVERSHOOT" if o else ("BEYOND THE CORRECTION CEILING" if g >= 2 * se else "NOT BEYOND")
        over += [L] if o else []
        rows[L] = dict(p_pooled=p, se=se, g=g, c=c, verdict=v, rd=p3, nf=p1, noiseless=R[L]["ff"])
        print(f"L {L}: rd {p3:.3f}  nf {p1:.3f}  pooled {p:.3f} (noiseless {R[L]['ff']:.3f}, {p - R[L]['ff']:+.3f})  "
              f"g {g:+.3f} (2 SE {2 * se:.3f}) -> {v}")
    b, sb = CP.slope(list(LS), [rows[L]["g"] for L in LS], [rows[L]["se"] for L in LS])
    sv = "COMPOUNDS" if (b >= 2 * sb and not over) else "NOT SHOWN"
    print(f"slope of the pooled g over L {b:+.4f} (2 SE {2 * sb:.4f}) -> {sv}")
    json.dump(dict(rows=rows, slope=dict(slope=b, se=sb, verdict=sv)), open(os.path.join(a.out, "balanced_scores.json"),
                                                                          "w"), indent=1)


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
