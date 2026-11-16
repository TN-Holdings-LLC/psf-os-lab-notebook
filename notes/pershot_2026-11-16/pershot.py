"""Shot by shot on circuits whose ideal output is one bitstring (desk, exploratory, 2026-11-16; owner "進めて" on the
stage-2 proposal: verdicts no correction can reach, because they count the device's own shots).

For the XX chain at theta = pi/2 every <Z> is +-1: the ideal output is one bitstring (the permuted Neel state). The
mirror (circuit then its inverse) and the floor (the circuit without its non-diagonal single-qubit gates) of every
circuit have the all-zero string as ideal output. Per circuit, from the raw counts of the job (bit k = label k, as
psf-os reads them):
  P_exact  share of shots equal to the ideal string;
  MODE     whether the ideal string is the most frequent string of the shots;
  hamming  mean number of wrong bits per shot (this one is linear in the <Z_k>, so a scale can reach it: beside only);
  pass_k   share of shots with at most k wrong bits (k = 1, 2).
Records: the XX size test and the light-cone repeat of 2026-11-14 (ibm_fez, ibm_marrakesh; 33 and 81 qubits).
usage: python notes/pershot_2026-11-16/pershot.py   (from the repository root, psf-os importable)"""
import collections
import glob
import json
import os

import numpy as np
from psf_os import job as J


def per_shot(counts, n, ideal):
    tot = sum(counts.values())
    want = "".join(str(b) for b in ideal)                       # label order 0..n-1
    hist = collections.Counter()
    exact = 0
    ham = 0.0
    top = max(counts.items(), key=lambda kv: kv[1])[0].replace(" ", "")
    top_bits = "".join(top[-1 - k] for k in range(n))
    for key, c in counts.items():
        b = key.replace(" ", "")
        bits = "".join(b[-1 - k] for k in range(n))
        h = sum(x != y for x, y in zip(bits, want))
        hist[h] += c
        exact += c * (h == 0)
        ham += c * h
    return dict(P_exact=exact / tot, MODE=top_bits == want, hamming=ham / tot,
                pass1=(hist[0] + hist[1]) / tot, pass2=(hist[0] + hist[1] + hist[2]) / tot)


rows = []
for d in sorted(glob.glob("results/xxsize-2026-11-14-*/ibm_*_n*")) + sorted(glob.glob("results/xxcone-2026-11-14/ibm_*_n*")):
    sc = json.load(open(os.path.join(d, "scores.json")))["circuits"]
    run = "repeat" if "xxcone" in d else "first"
    dev = os.path.basename(d).rsplit("_n", 1)[0]
    for name, (rec, cc) in J.read(os.path.join(d, "job"), os.path.join(d, "runs")).items():
        kind = rec.get("psfos_job", {}).get("kind")
        if kind not in ("user2d", "user2d_floor", "user2d_mirror"):
            continue
        tag = rec["tag"] if "tag" in rec else name[4:].replace("_floor", "").replace("_mirror", "")
        n = len(rec["labels"])
        p = rec["points"][0]
        counts = cc[(p["input"], "z")]
        if kind == "user2d":
            if "_th1571_" not in tag:
                continue
            ex = sc[tag]["exact"]                               # chain order; map to label order
            chain = json.load(open(os.path.join(d, "build.json")))["chains"][str(n)]["labels"]
            pos = {lab: i for i, lab in enumerate(chain)}
            ideal = [0 if ex[pos[lab]] > 0 else 1 for lab in rec["labels"]]
            role = "pi/2 circuit"
        else:
            ideal = [0] * n
            role = "floor" if kind == "user2d_floor" else "mirror"
        res = per_shot(counts, n, ideal)
        layers = 4 * int(tag.split("_s")[-1])
        rows.append(dict(run=run, device=dev, n=n, tag=tag, role=role, layers=layers,
                         r=sc[tag]["amplitude_ratio"], **res))

json.dump(rows, open("notes/pershot_2026-11-16/pershot.json", "w"), indent=1)
for role in ("pi/2 circuit", "mirror", "floor"):
    print(f"\n{role}: run device n layers | P_exact MODE pass1 pass2 hamming | r of the circuit")
    for r in rows:
        if r["role"] != role or (role != "pi/2 circuit" and "_th0785_" in r["tag"]):
            continue
        print(f"  {r['run']:6s} {r['device']:13s} {r['n']:2d} {r['layers']:2d} | {r['P_exact']:.4f} "
              f"{'yes' if r['MODE'] else 'no ':3s} {r['pass1']:.3f} {r['pass2']:.3f} {r['hamming']:5.2f} | {r['r']:.3f}")
