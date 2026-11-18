"""V3: the phase-estimation score, written without the workplace code (workplace VS Claude, 2026-11-18). It reads only
job/manifest.json and job/raw_counts.json. The tool's score, its pool and psf-os are not imported. The expected bits
come from the cell names (vs_bits.expected_key), and the ceiling from vs_ceiling.

Per part and n:
  - IPE ff and textbook ff: pooled over every j, the share of shots with all n bits right, and 2 SE (binomial on the
    pooled shots);
  - ceiling verdict: BEYOND THE CEILING if IPE >= C(n) + 2 SE, else NOT BEYOND;
  - per shot: d = IPE - textbook, SE_d = sqrt(SE_ipe^2 + SE_tb^2); IPE RIGHT MORE OFTEN if d > 0 and d >= 2 SE_d,
    TEXTBOOK RIGHT MORE OFTEN if d < 0 and d <= -2 SE_d, else NOT SEPARATED (the draft's words);
  - beside: the IPE off arm as read, and the textbook replicate arm.

  python vs_score.py OUT [OUT ...] [--compare DRY.txt] [--json OUT.json]
"""
import json
import math
import os
import re
import sys

import vs_bits as VB
import vs_ceiling as VC


def read(out):
    m = json.load(open(os.path.join(out, "job", "manifest.json")))
    raw = json.load(open(os.path.join(out, "job", "raw_counts.json")))
    names = [cell["name"] + (f"#{p}" if cell["points"] > 1 else "") for cell in m["cells"] for p in range(cell["points"])]
    by_pub = {r["pub"]: r["counts"] for r in raw["rows"]}
    assert sorted(by_pub) == list(range(len(names))), "raw_counts does not cover every pub once"
    tally = {}                                   # (fam, n, arm) -> [right, shots]
    for i, name in enumerate(names):
        mt = re.fullmatch(r"ff_(ipe|tqpe)(\d)_(\d+)(_off|_floor)?", name)
        if not mt:
            continue
        fam, n, j, arm = mt.group(1), int(mt.group(2)), int(mt.group(3)), (mt.group(4) or "_ff")[1:]
        if arm == "floor":
            continue
        want = VB.expected_key(fam, n, j)
        cnt = by_pub[i]
        t = tally.setdefault((fam, n, arm), [0, 0])
        t[0] += sum(v for k, v in cnt.items() if k.replace(" ", "")[-n:] == want)
        t[1] += sum(cnt.values())
    return tally


def share(t):
    p = t[0] / t[1]
    return p, math.sqrt(p * (1 - p) / t[1]), t[1]


def score(outs):
    tally = {}
    for o in outs:
        tally.update(read(o))
    res = {}
    for n in sorted({k[1] for k in tally}):
        C = VC.ceiling(VC.analytic(n), n)
        p, sp, N = share(tally[("ipe", n, "ff")])
        q, sq, _ = share(tally[("tqpe", n, "ff")])
        po, _, _ = share(tally[("ipe", n, "off")])
        qr, _, _ = share(tally[("tqpe", n, "off")])
        d, sd = p - q, math.sqrt(sp ** 2 + sq ** 2)
        cv = "BEYOND THE CEILING" if p >= C + 2 * sp else "NOT BEYOND"
        pv = ("IPE RIGHT MORE OFTEN" if d > 0 and d >= 2 * sd else
              "TEXTBOOK RIGHT MORE OFTEN" if d < 0 and d <= -2 * sd else "NOT SEPARATED")
        res[n] = dict(ipe=p, ipe_2se=2 * sp, shots=N, ceiling=C, margin=p - C, ceiling_verdict=cv, off_as_read=po,
                      textbook=q, textbook_2se=2 * sq, d=d, d_2se=2 * sd, per_shot_verdict=pv, replicate=qr)
        print(f"n {n}: IPE {p:.4f} (2 SE {2 * sp:.4f}, {N} shots) vs C {C:.4f} -> {cv} (margin {p - C:+.4f}); "
              f"off as read {po:.4f}; textbook {q:.4f} (2 SE {2 * sq:.4f}); d {d:+.4f} (2 SE {2 * sd:.4f}) -> {pv}; "
              f"replicate {qr:.4f}")
    return res


def compare(res, path):
    """Every number and word of the tool's printed score (dry_*.txt) against ours, at its 4 decimals."""
    txt = open(path, encoding="utf-8").read()
    bad = []
    for n, r in res.items():
        a = re.search(rf"n {n}: IPE ([\d.]+) \(2 SE ([\d.]+), (\d+) shots\) against the ceiling ([\d.]+) -> "
                      rf"(BEYOND THE CEILING|NOT BEYOND) \(margin ([-+\d.]+)\); off as read ([\d.]+)\n\s+textbook "
                      rf"([\d.]+) \(2 SE ([\d.]+)\); IPE - textbook ([-+\d.]+) \(2 SE ([\d.]+)\) -> ([A-Z ]+); beside: "
                      rf"replicate arm ([\d.]+)", txt)
        if not a:
            bad.append(f"n {n}: line not found")
            continue
        theirs = a.groups()
        ours = [f"{r['ipe']:.4f}", f"{r['ipe_2se']:.4f}", str(r["shots"]), f"{r['ceiling']:.4f}", r["ceiling_verdict"],
                f"{r['margin']:+.4f}", f"{r['off_as_read']:.4f}", f"{r['textbook']:.4f}", f"{r['textbook_2se']:.4f}",
                f"{r['d']:+.4f}", f"{r['d_2se']:.4f}", r["per_shot_verdict"], f"{r['replicate']:.4f}"]
        bad += [f"n {n} field {k}: tool {t} / VS {o}" for k, (t, o) in enumerate(zip(theirs, ours)) if t != o]
    print(f"compare with {os.path.basename(path)}: " + ("all 13 fields x n agree" if not bad else f"DIFFER {bad}"))
    return not bad


if __name__ == "__main__":
    args = sys.argv[1:]
    cmp_path = js = None
    if "--compare" in args:
        k = args.index("--compare"); cmp_path = args[k + 1]; del args[k:k + 2]
    if "--json" in args:
        k = args.index("--json"); js = args[k + 1]; del args[k:k + 2]
    res = score(args)
    ok = compare(res, cmp_path) if cmp_path else True
    if js:
        json.dump({n: {k: (f"{v:.3e}" if isinstance(v, float) else v) for k, v in r.items()} for n, r in res.items()},
                  open(js, "w"), indent=1)
    sys.exit(0 if ok else 1)
