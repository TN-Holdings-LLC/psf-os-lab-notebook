"""How firm is MODE on the 2026-11-14 pi/2 records? (workplace VS Claude, 2026-11-16; desk, for the declaration
draft DRAFT_paper10_mode.md; reads the same records and ideal strings as pershot.py).

pershot.py takes the most frequent string with max(), which on a tie returns whichever string comes first in the
counts dict. A declaration has to fix ties. Here, per pi/2 circuit: the count of the ideal string, the largest count
of any other string, how many other strings reach that count, and MODE under the strict rule (the ideal string's count
is larger than every other string's).
For the 81-qubit circuits also the same on the first 33 sites of the chain (the substring of each shot on those
labels, judged against the 81-qubit circuit's own ideal values there): the shot-by-shot form of paper 10's comparison
on the shared qubits; and for the 33-qubit circuits whether their chain is the first 33 sites of the 81-qubit chain.
usage: python notes/pershot_2026-11-16/mode_margin.py   (from the repository root, psf-os importable;
       writes mode_margin.txt)"""
import glob
import json
import os

from psf_os import job as J

OUT = os.path.join("notes", "pershot_2026-11-16", "mode_margin.txt")


def margin(counts, n, ideal, keep=None):
    """keep: positions (label order) to judge; None = all n."""
    keep = list(range(n)) if keep is None else keep
    want = "".join(str(ideal[k]) for k in keep)
    by = {}
    for key, c in counts.items():
        b = key.replace(" ", "")
        bits = "".join(b[-1 - k] for k in keep)
        by[bits] = by.get(bits, 0) + c
    tot = sum(by.values())
    mine = by.get(want, 0)
    others = [c for s, c in by.items() if s != want]
    top = max(others) if others else 0
    return dict(shots=tot, ideal=mine, other_top=top, other_at_top=sum(1 for c in others if c == top),
                distinct=len(by), strict_mode=mine > top, tie=mine == top and mine > 0)


rows = []
chains = {}
for d in sorted(glob.glob("results/xxsize-2026-11-14-*/ibm_*_n*")) + sorted(glob.glob("results/xxcone-2026-11-14/ibm_*_n*")):
    sc = json.load(open(os.path.join(d, "scores.json")))["circuits"]
    run = "repeat" if "xxcone" in d else "first"
    dev = os.path.basename(d).rsplit("_n", 1)[0]
    for name, (rec, cc) in J.read(os.path.join(d, "job"), os.path.join(d, "runs")).items():
        if rec.get("psfos_job", {}).get("kind") != "user2d":
            continue
        tag = rec["tag"] if "tag" in rec else name[4:]
        if "_th1571_" not in tag:
            continue
        n = len(rec["labels"])
        ex = sc[tag]["exact"]
        chain = json.load(open(os.path.join(d, "build.json")))["chains"][str(n)]["labels"]
        pos = {lab: i for i, lab in enumerate(chain)}
        ideal = [0 if ex[pos[lab]] > 0 else 1 for lab in rec["labels"]]
        counts = cc[(rec["points"][0]["input"], "z")]
        m = margin(counts, n, ideal)
        lay = 4 * int(tag.split("_s")[-1])
        rows.append(dict(run=run, device=dev, n=n, layers=lay, part="whole", **m))
        chains[(run, dev, n)] = chain
        if n == 81:
            first = set(chain[:33])
            keep = [k for k, lab in enumerate(rec["labels"]) if lab in first]
            rows.append(dict(run=run, device=dev, n=n, layers=lay, part="first 33", **margin(counts, n, ideal, keep)))

same = {f"{run} {dev}": chains[(run, dev, 33)] == chains[(run, dev, 81)][:33]
        for (run, dev, n) in chains if n == 33 and (run, dev, 81) in chains}
L = ["33-qubit chain equal to the first 33 sites of the 81-qubit chain: "
     + ", ".join(f"{k} {'yes' if v else 'no'}" for k, v in sorted(same.items())), "",
     "pi/2 circuits of 2026-11-14: run device n layers | shots, ideal count, largest other count (strings at it), "
     "distinct strings | MODE strict (ideal count > every other)"]
for r in sorted(rows, key=lambda r: (r["run"], r["device"], r["n"], r["part"], r["layers"])):
    L.append(f"  {r['run']:6s} {r['device']:13s} {r['n']:2d} {r['part']:8s} {r['layers']:2d} | {r['shots']} {r['ideal']:4d} "
             f"{r['other_top']:3d} ({r['other_at_top']}) {r['distinct']:4d} | "
             f"{'yes' if r['strict_mode'] else ('tie' if r['tie'] else 'no')}")
open(OUT, "w", encoding="utf-8").write("\n".join(L) + "\n")
print("\n".join(L))
