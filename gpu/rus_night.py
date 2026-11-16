"""The repeat-until-success neuron test of prereg/rus_neuron_2026-11-16.md: build, pre-run check, score (needs psf-os at
the branch feedforward-2026-11-16, commit 32dc3e5 or later, importable).

  python gpu/rus_night.py build DEVDIR OUT                 one job: per L = 1, 2, 3 the ff, off and floor arms, one sentinel
  python gpu/rus_night.py check OUT                        noiseless Aer of every arm but the sentinel; PASS / FAIL
  python gpu/rus_night.py score OUT                        answer cards from the job's raw counts and the verdicts
  dry run of the whole chain: build ... --dry-clifford-sentinel, then psf_os.feedforward.run_local(OUT), then score

The verdict (declared), per L in {1, 2, 3}, theta 1.1, m = 3 tries, every shot of both arms counted:
  d = |P_off - exact| - |P_ff - exact|, SE_d = sqrt(P_ff (1 - P_ff) / N_ff + P_off (1 - P_off) / N_off),
  CLOSER WITH CONTROL when d >= 2 SE_d, otherwise NOT CLOSER.
P is the share of shots with the last output bit 1; exact = (sin^2 q)^L, tan q = tan^2 theta (from the circuit). The
post view (the off arm's counts kept only where every neuron's first try succeeded) is beside, never judged."""
import argparse
import json
import math
import os
import sys

THETA = 1.1
M = 3
LS = (1, 2, 3)
# noiseless references for the pre-run check (notebook notes/feedforward_2026-11-16/rus_neuron_desk.txt, Aer, 20000
# shots, theta 1.1, m = 3): P(last output 1) of the ff and off arms
REF = {1: dict(ff=0.919, off=0.793), 2: dict(ff=0.849, off=0.634), 3: dict(ff=0.781, off=0.502)}
TOL = 0.03


def verdict(card):
    ex = card["exact"]
    ff, off = card["ff"], card["off"]
    d = abs(off["p1"] - ex) - abs(ff["p1"] - ex)
    se = math.sqrt(ff["p1"] * (1 - ff["p1"]) / ff["counted"] + off["p1"] * (1 - off["p1"]) / off["counted"])
    return d, se, ("CLOSER WITH CONTROL" if d >= 2 * se else "NOT CLOSER")


def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    dev = Device.load(a.devdir)
    items = []
    for L in LS:
        qc, spec = FF.rus_chain(L, THETA, m=M)
        items.append((f"rus{L}", qc, spec))
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None   # dry runs only, never a device
    rep = FF.build(dev, items, a.out, shots=4000, sentinel_spec=spec)
    print(json.dumps({k: rep[k] for k in ("device", "circuits", "qpu_seconds_model", "shots") if k in rep}))


def check(a):
    """Noiseless Aer of the ff, off and floor arms (the sentinel is the job's own and scored as always)."""
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
            L = int(cell["name"].split("_")[1][3:])
            cc = FF.compact(c)
            n = cc.num_clbits
            counts = AerSimulator().run(cc, shots=4000, seed_simulator=20261116).result().get_counts()
            tot = sum(counts.values())
            p1 = sum(v for key, v in counts.items() if FF._bits(key, n)[L * M] == 1) / tot
            allz = sum(v for key, v in counts.items() if set(FF._bits(key, n)) == {0}) / tot
            if cell["role"] == "floor":
                ok, ref = allz == 1.0, "all zero 1"
            else:
                arm = "ff" if cell["role"] == "user" else "off"
                ok, ref = abs(p1 - REF[L][arm]) <= TOL, f"ref {REF[L][arm]:.3f}"
            lines.append(f"{cell['name']:16s} {cell['role']:6s} P(out 1) {p1:.3f}  all zero {allz:.3f}  ({ref}) "
                         f"{'ok' if ok else 'FAIL'}")
            bad += [] if ok else [cell["name"]]
    print("\n".join(lines))
    print("PASS" if not bad else f"FAIL {bad}")
    return not bad


def score(a):
    from psf_os import feedforward as FF
    cards = FF.cards(a.out)
    out = {}
    for tag in sorted(cards, key=lambda t: int(t[3:])):
        c = cards[tag]
        d, se, v = verdict(c)
        c.update(d=d, se_d=se, d_in_se=d / se if se > 0 else None, verdict=v)
        out[tag] = c
        print(f"{tag}: exact {c['exact']:.4f}; ff {c['ff']['p1']:.4f} (still failed after {c['m']} "
              f"{c['ff']['still_failed_after_m']:.4f}); off {c['off']['p1']:.4f}; d {d:.4f} (2 SE_d {2 * se:.4f}) -> "
              f"{v}; post {c['post']['p1']:.4f} (kept {c['post']['kept_share']:.4f}, discarded "
              f"{c['post']['discarded']}); floor all zero {c['floor']['all_zero']:.4f}; sentinel {c['sentinel']}")
    json.dump(out, open(os.path.join(a.out, "rus_scores.json"), "w"), indent=1)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    b.add_argument("--dry-clifford-sentinel", action="store_true",
                   help="dry runs only: the ring sentinel at its Clifford point so that psf_os.feedforward.run_local "
                        "can simulate the whole job; never for the device job")
    c = sub.add_parser("check")
    c.add_argument("out")
    s = sub.add_parser("score")
    s.add_argument("out")
    a = p.parse_args()
    r = {"build": build, "check": check, "score": score}[a.cmd](a)
    sys.exit(0 if r is not False else 1)
