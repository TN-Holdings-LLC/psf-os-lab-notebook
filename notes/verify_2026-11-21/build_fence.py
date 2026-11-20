"""Build IPE n = 3, 4 (the plain items of gpu/ipe_park_night.py) through psf_os.feedforward.build(fence=True), then
compare every sent ff circuit, instruction by instruction, with the tool's fe form (home VS, 2026-11-21).
usage: PYTHONPATH=PSF_OS:NB:NB/gpu python build_fence.py DEVDIR WORK"""
import json
import os
import sys

from qiskit import qpy

import ipe_park_night as IP
from psf_os import feedforward as FF
from psf_os.device import Device

dev, work = sys.argv[1], sys.argv[2]


def sent(out):
    man = json.load(open(f"{out}/job/manifest.json"))
    circs = qpy.load(open(f"{out}/job/circuits.qpy", "rb"))
    cells = {c["cell"]: c["name"] for c in man["cells"]}
    return {cells[p["cell"]]: circs[i] for i, p in enumerate(man["pubs"]) if p["point"] == 0}


def sig(qc):
    def one(c):
        rows = []
        for ins in c.data:
            op = ins.operation
            q = [c.find_bit(x).index for x in ins.qubits]
            k = [c.find_bit(x).index for x in ins.clbits]
            if op.name == "if_else":
                rows.append(("if_else", str(op.condition[1]), q, k, [one(b) for b in op.blocks]))
            else:
                rows.append((op.name, [round(float(p), 12) for p in op.params], q, k))
        return rows
    return one(qc)


for n in (3, 4):
    for job in (0, 1):
        its = [(t.replace("pl", "bf", 1), qc, meta) for t, qc, meta in IP.items(n, job, True) if t.startswith("pl")]
        out = os.path.join(work, f"bf_n{n}_j{job}")
        FF.build(Device.load(dev), its, out, shots=IP.SHOTS, max_seconds=60, footprint=True, fence=True)
        a, b = sent(out), sent(os.path.join(work, f"aw_n{n}_j{job}"))
        same = diff = 0
        for name, qc in a.items():
            if not name.startswith("ff_bf") or name.endswith(("_off", "_floor")):
                continue
            other = b[name.replace("ff_bf", "ff_fe")]
            if sig(qc) == sig(other):
                same += 1
            else:
                diff += 1
                print("DIFFERENT", name)
        print(f"n {n} job {job}: build(fence=True) ff circuits identical to the tool's fe: {same}, different: {diff}")
