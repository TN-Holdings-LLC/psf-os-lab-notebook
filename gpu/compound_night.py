"""Does real-time control keep the neuron chain beyond the correction ceiling of its off arm, and does the margin grow
with the chain? (prereg/ff_night_2026-11-17.md, test T2). The workplace prototype
(notes/compound_2026-11-17/compound.py: items, exact ideal, margin, slope) with one home guard against decay bias.

  python gpu/compound_night.py build DEVDIR OUT [--dry-clifford-sentinel]
  python gpu/compound_night.py check OUT           (the prototype's check: noiseless Aer against ideal.json, 0.03)
  python gpu/compound_night.py score OUT

Items: the third design of 2026-11-16, L = 1 .. 5, m = 2, theta 1.1, read flipped and relabelled; ff, off, floor arms;
one ring sentinel; 19 circuits, 24.2 s by the model, 4000 shots.

Per L (declared): c = |P_off,noiseless - exact| (the ceiling: no after-the-fact method applied to this off circuit
recovers more than its noiseless value), e = |P_ff,device - exact|, g = c - e, SE from the ff arm (binomial).
BEYOND THE CORRECTION CEILING when g >= 2 SE and the ff arm does not overshoot its own noiseless value
(P_ff,device <= P_ff,noiseless + 2 SE); OVERSHOOT when it does (decay toward |0> read flipped lifts it: the
workplace VS desk, 2026-11-17); otherwise NOT BEYOND. Slope of g over L (weighted least squares): COMPOUNDS when the
slope is at least 2 SE and no L overshoots; otherwise NOT SHOWN."""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.join(HERE, "..", "notes", "compound_2026-11-17")
sys.path.insert(0, PROTO)
sys.path.insert(0, os.path.join(HERE, "..", "notes", "rus_coherent_2026-11-17"))
import compound as CP  # noqa: E402


def ref():
    return {int(k): v for k, v in json.load(open(os.path.join(PROTO, "ideal.json"))).items()}


def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None   # dry runs only, never a device
    rep = FF.build(Device.load(a.devdir), CP.items(), a.out, shots=4000, max_seconds=60, sentinel_spec=spec)
    print(json.dumps({k: rep[k] for k in ("device", "circuits", "qpu_seconds_model", "shots") if k in rep}))
    print(json.dumps({t: (v["chain"], v["cz"], v["mid"]) for t, v in rep["items"].items()}))


def check(a):
    sys.argv = ["compound.py", "check", a.out]
    CP.main()


def score(a):
    R = ref()
    rows, _ = CP.read(a.out, R)
    over = []
    for L, r in rows.items():
        ff0 = R[L]["ff"]
        r["ff_noiseless"] = ff0
        r["overshoot"] = r["p_ff"] > ff0 + 2 * r["se"]
        r["retained_of_noiseless_margin"] = r["g"] / R[L]["noiseless_margin"] if R[L]["noiseless_margin"] else None
        if r["overshoot"]:
            r["verdict"] = "OVERSHOOT"
            over.append(L)
        else:
            r["verdict"] = "BEYOND THE CORRECTION CEILING" if r["g"] >= 2 * r["se"] else "NOT BEYOND"
        print(f"L {L}: exact {R[L]['exact']:.3f}  off noiseless {R[L]['off']:.3f} (c {r['c']:.3f})  ff {r['p_ff']:.3f} "
              f"(noiseless {ff0:.3f}; e {r['e']:.3f})  g {r['g']:+.3f} (2 SE {2 * r['se']:.3f}) -> {r['verdict']}; "
              f"retained {r['retained_of_noiseless_margin']:.2f} of the noiseless margin; off {r['off']:.3f}; post "
              f"{r['post']:.3f} (kept {r['kept']:.3f}); floor {r['floor']:.3f}; sentinel {r['sentinel']}")
    Ls = sorted(rows)
    b, sb = CP.slope(Ls, [rows[L]["g"] for L in Ls], [rows[L]["se"] for L in Ls])
    sv = "COMPOUNDS" if (b >= 2 * sb and not over) else "NOT SHOWN"
    print(f"slope of g over L {b:+.4f} per step (2 SE {2 * sb:.4f}) -> {sv}" + (f" (overshoot at L {over})" if over
                                                                                    else ""))
    out = dict(rows=rows, slope=dict(slope=b, se=sb, verdict=sv, overshoot_at=over))
    out["predictions"] = {
        "T2-1 BEYOND at every L = 1 .. 5": "held" if all(rows[L]["verdict"] == "BEYOND THE CORRECTION CEILING"
                                                         for L in Ls) else "failed",
        "T2-2 COMPOUNDS": "held" if sv == "COMPOUNDS" else "failed",
    }
    print("predictions:", out["predictions"])
    json.dump(out, open(os.path.join(a.out, "compound_scores.json"), "w"), indent=1)


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
    {"build": build, "check": check, "score": score}[a.cmd](a)
