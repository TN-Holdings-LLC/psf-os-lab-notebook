"""Beside the verdict, never judged: P(last output 1) of the ff and off arms split by neuron 0's try bits.

usage: python results/rus-neuron-2026-11-16/branch.py   (reads job/manifest.json, job/raw_counts.json, build.json here)
Counts keys: classical bit 0 rightmost; neuron j's tries in bits j m .. j m + m - 1, the last output in bit L m."""
import json
import os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
man = json.load(open(os.path.join(HERE, "job", "manifest.json")))
raw = json.load(open(os.path.join(HERE, "job", "raw_counts.json")))
build = json.load(open(os.path.join(HERE, "build.json")))
counts = {row["pub"]: row["counts"] for row in raw["rows"]}
names = [c["name"] for c in man["cells"] for _ in range(c["points"])]
out = {}
for pub, name in enumerate(names):
    if not name.startswith("ff_rus") or name.endswith("_floor"):
        continue
    tag = name.split("_")[1]
    arm = "off" if name.endswith("_off") else "ff"
    rus = build["items"][tag]["rus"]
    m, ob = rus["m"], rus["out_bit"]
    agg = Counter()
    for key, c in counts[pub].items():
        k = key.replace(" ", "")
        b = [int(k[-1 - i]) for i in range(len(k))]
        agg[("".join(str(x) for x in b[:m]), b[ob])] += c
    split = {}
    for p in sorted({p for p, _ in agg}):
        n = agg[(p, 0)] + agg[(p, 1)]
        split[p] = dict(shots=n, p1=agg[(p, 1)] / n)
        print(f"{tag} {arm:3s} neuron 0 tries (first..last) {p}: shots {n:5d}  P(out 1) {agg[(p, 1)] / n:.3f}")
    out.setdefault(tag, {})[arm] = split
json.dump(out, open(os.path.join(HERE, "branch.json"), "w"), indent=1)
