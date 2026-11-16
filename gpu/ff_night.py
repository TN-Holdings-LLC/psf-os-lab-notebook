"""The feed-forward test of prereg/feedforward_2026-11-16.md: build, pre-run check, score (needs psf-os at the branch
feedforward-2026-11-16, commit 1ab062b or later, importable).

  python gpu/ff_night.py build DEVDIR OUT --k 1 2 4        one job: per k the ff, off and floor arms, one sentinel
  python gpu/ff_night.py check OUT                         noiseless Aer of every arm but the sentinel; PASS / FAIL
  python gpu/ff_night.py score OUT                         answer cards from the job's raw counts and the verdicts
  dry run of the whole chain: build ... --dry-clifford-sentinel, then psf_os.feedforward.run_local(OUT), then score

The verdict (declared): for k = 1 and 2, ABOVE THE BOUND when the success share of the ff arm, every shot counted, is
at least the bound plus two standard errors at the bound: 0.75 + 2 sqrt(0.75 x 0.25 / shots) (0.7637 at 4000 shots).
Otherwise NOT ABOVE. k = 4 is beside, never judged. The bound 0.75 comes from the circuit (any fixed rule on the
recorded bits of a run without real-time control reaches at most 3/4), never from the data."""
import argparse
import json
import math
import os
import sys

BOUND = 0.75
JUDGED = (1, 2)


def threshold(shots):
    return BOUND + 2 * math.sqrt(BOUND * (1 - BOUND) / shots)


def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    dev = Device.load(a.devdir)
    items = [(f"tp{k}", FF.teleport_test(k), dict(success={k: 0}, bound=BOUND)) for k in a.k]
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
            cc = FF.compact(c)
            n = cc.num_clbits
            counts = AerSimulator().run(cc, shots=4000, seed_simulator=20261116).result().get_counts()
            tot = sum(counts.values())
            last0 = sum(v for key, v in counts.items() if key.replace(" ", "")[0] == "0") / tot
            allz = counts.get("0" * n, 0) / tot
            k = n - 1
            if cell["role"] == "user":
                ok = last0 == 1.0
            elif cell["role"] == "off":
                ok = abs(last0 - (0.75 if k == 1 else 0.5)) <= 0.03
            else:
                ok = allz == 1.0
            lines.append(f"{cell['name']:14s} {cell['role']:6s} last bit 0 {last0:.3f}  all zero {allz:.3f}  "
                         f"{'ok' if ok else 'FAIL'}")
            bad += [] if ok else [cell["name"]]
    print("\n".join(lines))
    print("PASS" if not bad else f"FAIL {bad}")
    return not bad


def score(a):
    from psf_os import feedforward as FF
    cards = FF.cards(a.out)
    out = {}
    for tag in sorted(cards, key=lambda t: int(t[2:])):
        c = cards[tag]
        k = int(tag[2:])
        thr = threshold(c["ff"]["shots"])
        verdict = None
        if k in JUDGED:
            verdict = "ABOVE THE BOUND" if c["ff"]["share"] >= thr else "NOT ABOVE"
        c["threshold"] = thr
        c["verdict"] = verdict
        out[tag] = c
        print(f"{tag}: ff {c['ff']['share']:.4f} (2 SE {c['ff']['two_se']:.4f}, threshold {thr:.4f}) -> "
              f"{verdict or 'beside'}; off {c['off']['share']:.4f}; floor all zero {c['floor']['all_zero']:.4f}; "
              f"off best fixed rule after the fact {c.get('off_best_fixed_rule_after_the_fact', float('nan')):.4f}; "
              f"sentinel {c['sentinel']}")
    json.dump(out, open(os.path.join(a.out, "ff_scores.json"), "w"), indent=1)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    b.add_argument("--k", type=int, nargs="+", default=[1, 2, 4])
    b.add_argument("--dry-clifford-sentinel", action="store_true",
                   help="dry runs only (2026-11-16, workplace): the ring sentinel at its Clifford point so that "
                        "psf_os.feedforward.run_local can simulate the whole job; never for the device job")
    c = sub.add_parser("check")
    c.add_argument("out")
    s = sub.add_parser("score")
    s.add_argument("out")
    a = p.parse_args()
    r = {"build": build, "check": check, "score": score}[a.cmd](a)
    sys.exit(0 if r is not False else 1)
