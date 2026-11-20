"""Independent check of the loopvar jobs (workplace VS, 2026-11-20; author The Architect). qiskit and numpy only for
the circuits (no psf-os, no notebook scorer). No device.

  1. V1, V2, V3: sha256 of every file of job/ (circuits.qpy, manifest.json) and of runs/
  2. every independent part of every V1 circuit (qubits, instruction sequence on relabelled wires, see decoy_check):
     each non-sentinel part appears exactly twice (copies a and b; the same qubits), and appears among the parts of
     the 2026-11-19 loop's round 1 job (results/loop-night-2026-11-19/r1/job/circuits.qpy) on the same qubits
  3. the score's arithmetic recomputed from its own per-job / per-copy g and SE (score json): within, between, chi2
     (2 df, p = exp(-chi2 / 2)), the excess variance; and the chi2 sum over L (6 df) with the closed form for even df

  python loopvar_check.py OUT R1_DIR [SCORE_JSON]
"""
import collections
import hashlib
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decoy_check as C   # noqa: E402  (parts, signature: qiskit only)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def tree(d):
    out = {}
    for root, _, files in os.walk(d):
        for f in files:
            p = os.path.join(root, f)
            out[os.path.relpath(p, d).replace("\\", "/")] = sha(p)
    return out


def part_keys(circuits):
    keys = collections.Counter()
    for c in circuits:
        for qs, cs in C.parts(c):
            if len(qs) > 12:
                keys[("sentinel", len(qs))] += 1
                continue
            keys[(tuple(qs), tuple(map(str, C.signature(c, qs, cs))))] += 1
    return keys


def main():
    out, r1 = sys.argv[1], sys.argv[2]
    trees = {v: tree(os.path.join(out, v)) for v in ("V1", "V2", "V3")}
    same = trees["V1"] == trees["V2"] == trees["V3"]
    print(f"1. V1, V2, V3: {len(trees['V1'])} files each; every file byte-identical: {same}; "
          f"job/circuits.qpy {trees['V1']['job/circuits.qpy'][:16]}...")
    lv = C.load(os.path.join(out, "V1", "job", "circuits.qpy"))
    rr = C.load(os.path.join(r1, "job", "circuits.qpy"))
    kl, kr = part_keys(lv), part_keys(rr)
    twice = all(n == 2 for k, n in kl.items() if k[0] != "sentinel")
    in_r1 = [k for k in kl if k[0] != "sentinel" and k not in kr]
    nparts = sum(n for k, n in kl.items() if k[0] != "sentinel")
    print(f"2. V1: {len(lv)} circuits, {nparts} item parts in {len([k for k in kl if k[0] != 'sentinel'])} kinds; "
          f"each kind exactly twice (copies a, b): {twice}; kinds not among r1's parts on the same qubits: {len(in_r1)}")
    print(f"   r1 job: {len(rr)} circuits; its part kinds {len([k for k in kr if k[0] != 'sentinel'])}; "
          f"sentinel parts V1 {[(k, n) for k, n in kl.items() if k[0] == 'sentinel']}, r1 {[(k, n) for k, n in kr.items() if k[0] == 'sentinel']}")
    qs_by = collections.defaultdict(int)
    for k in kl:
        if k[0] != "sentinel":
            qs_by[k[0]] += 1
    print(f"   qubit sets of the item parts (kinds per set): {dict(qs_by)}")
    if len(sys.argv) > 3:
        sc = json.load(open(sys.argv[3]))
        rows = sc["rows"] if "rows" in sc else sc
        worst = 0.0
        chi_all = 0.0
        for L, r in sorted(rows.items()):
            per = r["per_job_copy"]
            for v in ("V1", "V2", "V3"):
                a, b = per[v]["a"], per[v]["b"]
                d, t = a["g"] - b["g"], 2 * math.hypot(a["se"], b["se"])
                worst = max(worst, abs(d - r["within"][v]["d"]), abs(t - r["within"][v]["two_se"]))
            gj = {v: (per[v]["a"]["g"] + per[v]["b"]["g"]) / 2 for v in per}
            sj = {v: math.hypot(per[v]["a"]["se"], per[v]["b"]["se"]) / 2 for v in per}
            for x, y in (("V1", "V2"), ("V2", "V3"), ("V1", "V3")):
                d, t = gj[x] - gj[y], 2 * math.hypot(sj[x], sj[y])
                worst = max(worst, abs(d - r["between"][f"{x}-{y}"]["d"]), abs(t - r["between"][f"{x}-{y}"]["two_se"]))
            w = {v: 1 / sj[v] ** 2 for v in gj}
            gbar = sum(w[v] * gj[v] for v in gj) / sum(w.values())
            chi = sum((gj[v] - gbar) ** 2 / sj[v] ** 2 for v in gj)
            p = math.exp(-chi / 2)
            m = sum(gj.values()) / 3
            sb2 = sum((gj[v] - m) ** 2 for v in gj) / 2 - sum(s ** 2 for s in sj.values()) / 3
            worst = max(worst, abs(chi - r["chi2"]), abs(p - r["p"]), abs(sb2 - r["excess_var"]), abs(gbar - r["gbar"]))
            chi_all += chi
            print(f"3. L {L}: chi2 {chi:.3f} p {p:.3f} (tool {r['chi2']:.3f} / {r['p']:.3f}); s_b^2 {sb2:+.2e} "
                  f"(tool {r['excess_var']:+.2e})")
        p6 = math.exp(-chi_all / 2) * sum((chi_all / 2) ** i / math.factorial(i) for i in range(3))
        print(f"   pooled chi2 {chi_all:.3f}, 6 df, p {p6:.3f}; largest difference from the tool's numbers {worst:.1e}")


if __name__ == "__main__":
    main()
