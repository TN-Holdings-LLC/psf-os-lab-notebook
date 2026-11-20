"""Compare two builds of the same tool byte for byte (home VS, 2026-11-21): job/, runs/ and build.json; for
job/manifest.json, the keys that differ. Used for the default (no fence) builds of repcode_night, rus_night and
qpe_repro_night part A with psf-os 61869bb against d4fb614 on the 2026-11-19 marrakesh record.
usage: python compare_default.py DIR_A DIR_B [NAME ...]   (each NAME a build folder under both)"""
import filecmp
import hashlib
import json
import os
import sys


def files(root):
    return sorted(os.path.relpath(os.path.join(d, f), root) for d, _, fs in os.walk(root) for f in fs)


a, b, names = sys.argv[1], sys.argv[2], sys.argv[3:]
for n in names:
    A, B = os.path.join(a, n), os.path.join(b, n)
    fa, fb = files(A), files(B)
    print(f"== {n}: files {len(fa)} / {len(fb)}; only in A {sorted(set(fa) - set(fb))}, only in B "
          f"{sorted(set(fb) - set(fa))}")
    for part in ("job", "runs", "build.json"):
        sub = [f for f in fa if f == part or f.startswith(part + "/")]
        diff = [f for f in sub if f in fb and not filecmp.cmp(os.path.join(A, f), os.path.join(B, f), shallow=False)]
        print(f"  {part}: {len(sub)} files, byte-identical {len(sub) - len(diff)}, different {diff}")
    ma = json.load(open(os.path.join(A, "job/manifest.json")))
    mb = json.load(open(os.path.join(B, "job/manifest.json")))
    print(f"  manifest keys that differ: {[k for k in sorted(set(ma) | set(mb)) if ma.get(k) != mb.get(k)]}")
    print(f"  circuits.qpy sha256 {hashlib.sha256(open(os.path.join(A, 'job/circuits.qpy'), 'rb').read()).hexdigest()}")
