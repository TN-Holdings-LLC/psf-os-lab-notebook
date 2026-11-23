"""Compare two rebuild folders of recheck_nights.py (psf-os 0.3.2 and 0.3.3rc1) byte for byte; a manifest without its time, build environment, psf_os_build and compiled keys. usage: python bytecmp.py OUT_0.3.2 OUT_0.3.3rc1"""
import json, os, sys
a, b = sys.argv[1], sys.argv[2]
rows = []
for night in sorted(os.listdir(a)):
    pa = os.path.join(a, night)
    if not os.path.isdir(pa):
        continue
    same, diff, n = [], [], 0
    for root, _, files in os.walk(pa):
        for f in files:
            fa = os.path.join(root, f)
            rel = os.path.relpath(fa, a)
            fb = os.path.join(b, rel)
            if f == "manifest.json":
                ma, mb = json.load(open(fa)), json.load(open(fb))
                for m in (ma, mb):
                    for k in ("written", "env", "psf_os_build", "compiled"):
                        m.pop(k, None)
                (same if ma == mb else diff).append(rel + " (without written, env, psf_os_build, compiled)")
                continue
            if not os.path.exists(fb):
                diff.append(rel + " missing"); continue
            n += 1
            (same if open(fa, "rb").read() == open(fb, "rb").read() else diff).append(rel)
    rows.append((night, len(same), diff))
    print(f"{night:36} files the same: {len(same)}; different: {len(diff)}" + (f" {diff[:5]}" if diff else ""))
