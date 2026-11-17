"""Prototype (workplace, 2026-11-17; owner "プロトタイプ作ってみて"; desk only, not declared): does the advantage of
real-time control compound with the length of the chain?

The idea (owner): a fixed circuit pays "simple interest": its error is read once at the end, and after-the-fact methods
(rescaling, zero-noise extrapolation) can work on that one number. A feed-forward chain pays "compound interest": each
step's real-time decision is the next step's starting point. The part of the answer that only real-time control gives
is measurable: the circuit without control (the off arm) has its own noiseless value, and no after-the-fact method
applied to the off arm can bring it past that value (a perfect correction recovers the off arm's noiseless value, no
more). So:

  ceiling distance  c(L) = |P_off,noiseless - exact|     (the best any correction of the off arm can do)
  device distance   e(L) = |P_ff,device - exact|          (every shot counted)
  margin            g(L) = c(L) - e(L)                     (> 0: the device with control beats any corrected off arm)

Compounding means g(L) grows with L. Items: the third design of 2026-11-16 (`gpu/rus3_night.chain`: m = 2, outputs held
flipped while waiting, the last output read flipped and relabelled), theta 1.1, L = 1 .. 5, each with ff, off and
floor (psf_os.feedforward.build), one ring sentinel.

  python compound.py ideal                       exact, noiseless ff and off (exact branch simulation), c(L)
  python compound.py build DEVDIR OUT [--dry-clifford-sentinel]
  python compound.py check OUT                   noiseless Aer of every arm against `ideal` (0.03)
  python compound.py score OUT                   g(L), its SE, the ceiling verdict per L and the slope of g over L
  python compound.py retro RESULT_DIR ...        the same reading on recorded jobs (exploratory)
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(NB, "gpu"))
sys.path.insert(0, os.path.join(NB, "notes", "rus_coherent_2026-11-17"))

THETA, M = 1.1, 2
LS = (1, 2, 3, 4, 5)
TOL = 0.03


def items(Ls=LS):
    import rus3_night as R3
    return [(f"rd{L}", *R3.chain(L, THETA, m=M)) for L in Ls]


def ideal(Ls=LS):
    """{L: dict(exact, ff, off, ceiling)} with ff and off the noiseless P(last output 1) of the rd circuit and of its
    off arm, read with the declared relabelling, computed exactly (branching simulation, no sampling)."""
    import coherent as CO
    from psf_os import feedforward as FF
    out = {}
    for tag, qc, spec in items(Ls):
        L = spec["L"]
        row = dict(exact=spec["exact"])
        for arm, circ in (("ff", FF.lower(qc)), ("off", FF.strip_conditionals(FF.lower(qc)))):
            dist = CO.branch_distribution(circ)
            n = circ.num_clbits
            p_bit1 = sum(p for k, p in dist.items() if k[n - 1 - spec["out_bit"]] == "1")
            row[arm] = 1 - p_bit1                         # read flipped: P(last output 1) = 1 - P(bit 1)
        row["ceiling"] = abs(row["off"] - row["exact"])
        row["noiseless_margin"] = row["ceiling"] - abs(row["ff"] - row["exact"])
        out[L] = row
    return out


def margin(card, ideal_row):
    """g = c - e and its SE (binomial, from the ff arm only: the ceiling is a noiseless number)."""
    ex = card["exact"]
    p, n = card["ff"]["p1"], card["ff"]["counted"]
    e = abs(p - ex)
    g = ideal_row["ceiling"] - e
    se = math.sqrt(p * (1 - p) / n)
    return dict(p_ff=p, e=e, c=ideal_row["ceiling"], g=g, se=se,
                ceiling_verdict="BEYOND THE CORRECTION CEILING" if g >= 2 * se else "NOT BEYOND")


def slope(Ls, gs, ses):
    """Weighted least-squares slope of g over L and its SE."""
    w = [1 / s ** 2 for s in ses]
    W = sum(w)
    xb = sum(wi * x for wi, x in zip(w, Ls)) / W
    yb = sum(wi * y for wi, y in zip(w, gs)) / W
    sxx = sum(wi * (x - xb) ** 2 for wi, x in zip(w, Ls))
    b = sum(wi * (x - xb) * (y - yb) for wi, x, y in zip(w, Ls, gs)) / sxx
    return b, math.sqrt(1 / sxx)


def read(out, ref):
    import rus3_night as R3
    from psf_os import feedforward as FF
    cards = FF.cards(out)
    rows = {}
    for tag in sorted((t for t in cards if t.startswith("rd")), key=lambda t: int(t[2:])):
        L = int(tag[2:])
        c = R3.relabel(cards[tag])
        rows[L] = dict(margin(c, ref[L]), off=c["off"]["p1"], post=c["post"]["p1"], kept=c["post"]["kept_share"],
                       sentinel=c["sentinel"], floor=c["floor"]["all_zero"])
    Ls = sorted(rows)
    b, sb = slope(Ls, [rows[L]["g"] for L in Ls], [rows[L]["se"] for L in Ls]) if len(Ls) > 1 else (None, None)
    return rows, dict(slope=b, se=sb, verdict=None if b is None else
                      ("COMPOUNDS" if b >= 2 * sb else "NOT SHOWN"))


def show(rows, sl, ref):
    for L, r in rows.items():
        print(f"L {L}: exact {ref[L]['exact']:.3f}  off noiseless {ref[L]['off']:.3f} (ceiling c {r['c']:.3f})  "
              f"ff {r['p_ff']:.3f} (e {r['e']:.3f})  g = c - e {r['g']:+.3f} (2 SE {2 * r['se']:.3f}) -> "
              f"{r['ceiling_verdict']}; off {r['off']:.3f}; post {r['post']:.3f} (kept {r['kept']:.3f})")
    if sl["slope"] is not None:
        print(f"slope of g over L {sl['slope']:+.4f} per step (2 SE {2 * sl['se']:.4f}) -> {sl['verdict']}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ideal")
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    b.add_argument("--dry-clifford-sentinel", action="store_true")
    sub.add_parser("check").add_argument("out")
    sub.add_parser("score").add_argument("out")
    r = sub.add_parser("retro")
    r.add_argument("dirs", nargs="+")
    a = ap.parse_args()
    if a.cmd == "ideal":
        ref = ideal()
        for L, x in ref.items():
            print(f"L {L}: exact {x['exact']:.4f}  ff noiseless {x['ff']:.4f}  off noiseless {x['off']:.4f}  "
                  f"ceiling c {x['ceiling']:.4f}  noiseless margin {x['noiseless_margin']:+.4f}")
        json.dump({str(k): v for k, v in ref.items()}, open(os.path.join(HERE, "ideal.json"), "w"), indent=1)
    elif a.cmd == "build":
        from psf_os import feedforward as FF
        from psf_os.device import Device
        spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None
        rep = FF.build(Device.load(a.devdir), items(), a.out, shots=4000, max_seconds=60, sentinel_spec=spec)
        print(json.dumps({k: rep[k] for k in ("device", "circuits", "qpu_seconds_model")}))
        for t, v in rep["items"].items():
            print(t, "chain", v["chain"], "CZ", v["cz"], "off CZ", v["off_cz"], "mid", v["mid"],
                  "conditionals", v["conditionals"])
    elif a.cmd == "check":
        from qiskit import qpy
        from qiskit_aer import AerSimulator
        from psf_os import feedforward as FF
        ref = {int(k): v for k, v in json.load(open(os.path.join(HERE, "ideal.json"))).items()}
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
                    want = ref[L]["ff" if cell["role"] == "user" else "off"]
                    ok = abs(p - want) <= TOL
                print(f"{cell['name']:14s} {cell['role']:6s} P(out 1, relabelled) {p:.3f} all zero {allz:.3f} "
                      f"{'ok' if ok else 'FAIL'}")
                bad += [] if ok else [cell["name"]]
        print("PASS" if not bad else f"FAIL {bad}")
    elif a.cmd == "score":
        ref = {int(k): v for k, v in json.load(open(os.path.join(HERE, "ideal.json"))).items()}
        rows, sl = read(a.out, ref)
        show(rows, sl, ref)
        json.dump(dict(rows=rows, slope=sl), open(os.path.join(a.out, "compound_scores.json"), "w"), indent=1)
    elif a.cmd == "retro":
        ref = {int(k): v for k, v in json.load(open(os.path.join(HERE, "ideal.json"))).items()}
        res = {}
        for d in a.dirs:
            print(f"== {os.path.basename(os.path.normpath(d))} (recorded; exploratory, after the fact)")
            rows, sl = read(d, ref)
            show(rows, sl, ref)
            res[os.path.basename(os.path.normpath(d))] = dict(rows=rows, slope=sl)
        json.dump(res, open(os.path.join(HERE, "retro.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
