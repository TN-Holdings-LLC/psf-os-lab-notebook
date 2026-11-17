"""The neuron chain with finished outputs read early into classical bits (prereg/ff_night_2026-11-17_T4.md): the
workplace prototype (notes/early_2026-11-17/early.py: items ea{L}, L = 1 .. 5, off arm = the third design's off arm)
scored as test T2 is (the correction ceiling, the overshoot guard, the slope), with the third design of the same night
(test T2's job) beside or compared.

  python gpu/early_night.py build DEVDIR OUT [--dry-clifford-sentinel]
  python gpu/early_night.py check OUT
  python gpu/early_night.py score OUT [--rd T2_OUT]

Noiselessly the early chain equals the third design in the joint distribution of all tries and the last output (exact
branching simulation), so the ceiling c(L) and the noiseless values of notes/compound_2026-11-17/ideal.json hold for it
unchanged."""
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

LS = (1, 2, 3, 4, 5)
M = 2
TOL = 0.03


def ref():
    return {int(k): v for k, v in json.load(open(os.path.join(NB, "notes", "compound_2026-11-17", "ideal.json"))).items()}


def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None   # dry runs only, never a device
    rep = FF.build(Device.load(a.devdir), EA.items(LS), a.out, shots=4000, max_seconds=60, sentinel_spec=spec)
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
    out = dict(rows=rows, slope=dict(slope=b, se=sb, verdict=sv, overshoot_at=over), comparison=None)
    comp = None
    if a.rd:
        rd = {}
        rc = FF.cards(a.rd)
        for L in LS:
            c = R3.relabel(rc[f"rd{L}"])
            rd[L] = c["ff"]
        comp = {}
        for L in LS:
            e_, r_ = rows[L], rd[L]
            d = abs(r_["p1"] - R[L]["ff"]) - abs(e_["p_ff"] - R[L]["ff"])
            se = math.sqrt(e_["se"] ** 2 + r_["p1"] * (1 - r_["p1"]) / r_["counted"])
            rd_over = r_["p1"] > R[L]["ff"] + 2 * math.sqrt(r_["p1"] * (1 - r_["p1"]) / r_["counted"])
            ok = d > 0 and d >= 2 * se and not rd_over and not e_["overshoot"]
            comp[L] = dict(rd_ff=r_["p1"], early_ff=e_["p_ff"], d=d, two_se=2 * se, rd_overshoot=rd_over,
                           verdict="EARLY KEEPS MORE" if ok else
                           ("OVERSHOOT" if (rd_over or e_["overshoot"]) else "NOT SHOWN"))
            print(f"L {L}: |rd - noiseless| - |early - noiseless| = {d:+.4f} (2 SE {2 * se:.4f}) -> {comp[L]['verdict']}"
                  f"  (rd {r_['p1']:.3f}, early {e_['p_ff']:.3f}, noiseless {R[L]['ff']:.3f})")
        out["comparison"] = comp
    out["predictions"] = {
        "T4-1 BEYOND at every L = 1 .. 5": "held" if all(rows[L]["verdict"] == "BEYOND THE CORRECTION CEILING"
                                                         for L in LS) else "failed",
        "T4-2 COMPOUNDS": "held" if sv == "COMPOUNDS" else "failed",
        "T4-3 EARLY KEEPS MORE at L = 4 and 5": (None if comp is None else
                                                 "held" if all(comp[L]["verdict"] == "EARLY KEEPS MORE" for L in (4, 5))
                                                 else "failed"),
    }
    print("predictions:", out["predictions"])
    json.dump(out, open(os.path.join(a.out, "early_scores.json"), "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    b.add_argument("--dry-clifford-sentinel", action="store_true",
                   help="dry runs only: the ring sentinel at its Clifford point; never for the device job")
    sub.add_parser("check").add_argument("out")
    s = sub.add_parser("score")
    s.add_argument("out")
    s.add_argument("--rd", help="test T2's output folder (the third design of the same night), for T4-3")
    a = ap.parse_args()
    r = {"build": build, "check": check, "score": score}[a.cmd](a)
    sys.exit(0 if r is not False else 1)
