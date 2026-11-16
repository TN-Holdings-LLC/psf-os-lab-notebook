"""Beside the verdict, never judged: the success share split by the pattern of mid-circuit bits, ff and off arms.

usage: python results/feedforward-2026-11-16/branch.py   (reads job/manifest.json and job/raw_counts.json here)
Key layout of the counts: the leftmost character is the last (output) bit, the others are the mid-circuit bits with
mid bit 0 rightmost. Success: the output bit is 0."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
man = json.load(open(os.path.join(HERE, "job", "manifest.json")))
raw = json.load(open(os.path.join(HERE, "job", "raw_counts.json")))
counts = {row["pub"]: row["counts"] for row in raw["rows"]}
names = [c["name"] for c in man["cells"] for _ in range(c["points"])]
out = {}
for pub, name in enumerate(names):
    if not name.startswith("ff_tp") or name.endswith("_floor"):
        continue
    arm = "off" if name.endswith("_off") else "ff"
    tag = name.split("_")[1]
    split = {}
    for key, c in counts[pub].items():
        key = key.replace(" ", "")
        mid = key[1:]
        s = split.setdefault(mid, [0, 0])
        s[0] += c * (key[0] == "0")
        s[1] += c
    out.setdefault(tag, {})[arm] = {m: dict(success=v[0], shots=v[1], share=v[0] / v[1]) for m, v in sorted(split.items())}
    for m, v in sorted(split.items()):
        print(f"{tag} {arm:3s} mid bits {m}: success {v[0] / v[1]:.3f} of {v[1]}")
json.dump(out, open(os.path.join(HERE, "branch.json"), "w"), indent=1)
