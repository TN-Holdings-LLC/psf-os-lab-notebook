"""Next step N2 (after T2 / T4 of 2026-11-17): the early-read neuron chain, whose waits do not depend on how the device
schedules (workplace ledger: the same under ASAP and JIT), over L = 1 .. 7. Taken over at home from the workplace VS's
task "a chain with the least-wait schedule fixed, L = 1 .. 7" (owner 17:18 JST): the early chain needs no pinning to get
its least-wait schedule. Items ea{L} of notes/early_2026-11-17/early.py, L = 1 .. 7; the exact ideal values (ceiling
c(L), noiseless ff and off) in notes/next_2026-11-17/ideal7.json (exact branching; L = 1 .. 5 equal to
notes/compound_2026-11-17/ideal.json). Scored as T4 (ceiling, overshoot guard, slope); the comparison with the third
design is left out (no rd job for L = 6, 7).

  python gpu/early2_night.py build DEVDIR OUT [--dry-clifford-sentinel]
  python gpu/early2_night.py check OUT
  python gpu/early2_night.py score OUT

Noiselessly the early chain equals the third design in the joint distribution of all tries and the last output (exact
branching simulation), so the ceiling c(L) and the noiseless values of the third design hold for it unchanged (here from
notes/next_2026-11-17/ideal7.json)."""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.join(HERE, "..")
for d in ("notes/early_2026-11-17", "notes/compound_2026-11-17", "notes/rus_coherent_2026-11-17",
          "notes/timebudget_2026-11-17"):
    sys.path.insert(0, os.path.join(NB, d))
import compound as CP  # noqa: E402
import early as EA  # noqa: E402

LS = (1, 2, 3, 4, 5, 6, 7)
M = 2
TOL = 0.03


def ref():
    return {int(k): v for k, v in json.load(open(os.path.join(NB, "notes", "next_2026-11-17", "ideal7.json"))).items()}


def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None   # dry runs only, never a device
    rep = FF.build(Device.load(a.devdir), EA.items(LS), a.out, shots=4000, max_seconds=90, sentinel_spec=spec)
    print(json.dumps({k: rep[k] for k in ("device", "circuits", "qpu_seconds_model", "shots") if k in rep}))
    print(json.dumps({t: (v["chain"], v["cz"], v["mid"], v["conditionals"]) for t, v in rep["items"].items()}))


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
            L = int(cell["name"].split("_")[1][2:])
            cc = FF.compact(c)
            n = cc.num_clbits
            cnt = AerSimulator().run(cc, shots=4000, seed_simulator=20261117).result().get_counts()
            tot = sum(cnt.values())
            p = 1 - sum(v for k, v in cnt.items() if FF._bits(k, n)[L * M] == 1) / tot
            allz = sum(v for k, v in cnt.items() if set(FF._bits(k, n)) == {0}) / tot
            if cell["role"] == "floor":
                ok = allz == 1.0
            else:
                ok = abs(p - R[L]["ff" if cell["role"] == "user" else "off"]) <= TOL
            print(f"{cell['name']:14s} {cell['role']:6s} P(out 1, relabelled) {p:.3f} all zero {allz:.3f} "
                  f"{'ok' if ok else 'FAIL'}")
            bad += [] if ok else [cell["name"]]
    print("PASS" if not bad else f"FAIL {bad}")
    return not bad


def score(a):
    import rus3_night as R3
    from psf_os import feedforward as FF
    R = ref()
    cards = FF.cards(a.out)
    rows, over = {}, []
    for L in LS:
        c = R3.relabel(cards[f"ea{L}"])
        r = dict(CP.margin(c, R[L]), off=c["off"]["p1"], post=c["post"]["p1"], kept=c["post"]["kept_share"],
                 sentinel=c["sentinel"], floor=c["floor"]["all_zero"], ff_noiseless=R[L]["ff"])
        r["overshoot"] = r["p_ff"] > R[L]["ff"] + 2 * r["se"]
        r["verdict"] = ("OVERSHOOT" if r["overshoot"] else
                        "BEYOND THE CORRECTION CEILING" if r["g"] >= 2 * r["se"] else "NOT BEYOND")
        over += [L] if r["overshoot"] else []
        rows[L] = r
        print(f"L {L}: exact {R[L]['exact']:.3f}  off noiseless {R[L]['off']:.3f} (c {r['c']:.3f})  ff {r['p_ff']:.3f} "
              f"(noiseless {R[L]['ff']:.3f}; e {r['e']:.3f})  g {r['g']:+.3f} (2 SE {2 * r['se']:.3f}) -> {r['verdict']}; "
              f"off {r['off']:.3f}; post {r['post']:.3f} (kept {r['kept']:.3f}); floor {r['floor']:.3f}; sentinel "
              f"{r['sentinel']}")
    b, sb = CP.slope(list(LS), [rows[L]["g"] for L in LS], [rows[L]["se"] for L in LS])
    sv = "COMPOUNDS" if (b >= 2 * sb and not over) else "NOT SHOWN"
    print(f"slope of g over L {b:+.4f} per step (2 SE {2 * sb:.4f}) -> {sv}" + (f" (overshoot at L {over})" if over
                                                                                    else ""))
    out = dict(rows=rows, slope=dict(slope=b, se=sb, verdict=sv, overshoot_at=over))
    out["predictions"] = {
        "N2-1 BEYOND at every L = 1 .. 7": "held" if all(rows[L]["verdict"] == "BEYOND THE CORRECTION CEILING"
                                                         for L in LS) else "failed",
        "N2-2 COMPOUNDS over L = 1 .. 7": "held" if sv == "COMPOUNDS" else "failed",
    }
    print("predictions:", out["predictions"])
    json.dump(out, open(os.path.join(a.out, "early2_scores.json"), "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    b.add_argument("--dry-clifford-sentinel", action="store_true",
                   help="dry runs only: the ring sentinel at its Clifford point; never for the device job")
    sub.add_parser("check").add_argument("out")
    sub.add_parser("score").add_argument("out")
    a = ap.parse_args()
    r = {"build": build, "check": check, "score": score}[a.cmd](a)
    sys.exit(0 if r is not False else 1)
