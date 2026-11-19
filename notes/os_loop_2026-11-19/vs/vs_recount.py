"""Round 1 of a loop night counted again from its records (workplace VS Claude, 2026-11-19; instruction "その2" item 1):
raw_counts.json, manifest.json and the run records' rus fields (out_bit) only; qiskit and qiskit_aer for the noiseless
value. No tool of the notebook or of psf-os is imported.

Per chain length L: p0 = P(out bit 1) of the circuit as written (item p0_L); p = the prescription's success (item x_L;
P(out bit 1), or P(out bit 0) for the read-flipped base P2); g = |p0 - exact| - |p - exact| with
SE_g = sqrt(SE_p^2 + SE_p0^2); the noiseless value of x_L from Aer (200000 shots, the compiled circuit, no noise);
OVERSHOOT if p > noiseless + 2 SE_p, else PRESCRIPTION HELPS if g >= 2 SE_g, else NOT SHOWN. The probe's Dr: P(1 | |1>)
per probe bit from item dr, P(0 | |0>) from its floor arm.

  python vs_recount.py NIGHT_DIR [ROUND]
"""
import json
import math
import os
import sys

from qiskit import QuantumCircuit, QuantumRegister, qpy
from qiskit_aer import AerSimulator


def load(rd):
    m = json.load(open(os.path.join(rd, "job", "manifest.json")))
    raw = {r["pub"]: {k.replace(" ", ""): v for k, v in r["counts"].items()}
           for r in json.load(open(os.path.join(rd, "job", "raw_counts.json")))["rows"]}
    cs = qpy.load(open(os.path.join(rd, "job", "circuits.qpy"), "rb"))
    names = [c["name"] + (f"#{p}" if c["points"] > 1 else "") for c in m["cells"] for p in range(c["points"])]
    return {n: (raw[i], cs[i]) for i, n in enumerate(names)}


def share(cnt, bit, val):
    tot = sum(cnt.values())
    p = sum(v for k, v in cnt.items() if int(k[-1 - bit]) == val) / tot
    return p, math.sqrt(p * (1 - p) / tot), tot


def compact(c):
    used = sorted({c.find_bit(q).index for ins in c.data for q in ins.qubits})
    pos = {q: i for i, q in enumerate(used)}
    out = QuantumCircuit(QuantumRegister(len(used), "q"), *c.cregs)
    for ins in c.data:
        out.append(ins.operation, [out.qubits[pos[c.find_bit(q).index]] for q in ins.qubits],
                   [out.clbits[c.find_bit(b).index] for b in ins.clbits])
    return out


def main():
    night = sys.argv[1]
    k = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    rd = os.path.join(night, f"r{k}")
    rule = json.load(open(os.path.join(night, f"RULE{k}.json")))
    rec = json.load(open(os.path.join(rd, "round_scores.json")))
    cells = load(rd)
    sim = AerSimulator()
    bad = []
    for L, st in rule["stacks"].items():
        if len(st) != 1:
            print(f"L {L}: stack {'+'.join(st)} has layers; recount covers single-base stacks only")
            continue
        r0 = json.load(open(os.path.join(rd, "runs", f"ff_p0_{L}.json")))["rus"]
        rx = json.load(open(os.path.join(rd, "runs", f"ff_x{L}.json")))["rus"]
        exact = math.sin(math.atan(math.tan(1.1) ** 2)) ** 2 ** 1
        exact = (math.sin(math.atan(math.tan(1.1) ** 2)) ** 2) ** int(L)
        p0, s0, _ = share(cells[f"ff_p0_{L}"][0], r0["out_bit"], 1)
        want = 0 if st[0] == "P2" else 1
        p, sp, _ = share(cells[f"ff_x{L}"][0], rx["out_bit"], want)
        cc = compact(cells[f"ff_x{L}"][1])
        ncnt = {k2.replace(" ", ""): v for k2, v in sim.run(cc, shots=200000, seed_simulator=3).result().get_counts().items()}
        nl, nse, _ = share(ncnt, rx["out_bit"], want)
        g, sg = abs(p0 - exact) - abs(p - exact), math.sqrt(sp ** 2 + s0 ** 2)
        over = p > rec["rows"][L]["noiseless"] + 2 * sp
        verdict = "OVERSHOOT" if over else ("PRESCRIPTION HELPS" if g >= 2 * sg else "NOT SHOWN")
        R = rec["rows"][L]
        same = (abs(R["p"] - p) < 1e-12 and abs(R["p0"] - p0) < 1e-12 and abs(R["g"] - g) < 1e-12
                and abs(R["g_se"] - sg) < 1e-12 and R["verdict"] == verdict and abs(R["exact"] - exact) < 1e-12
                and abs(R["noiseless"] - nl) < 3 * nse + 1e-9)
        bad += [] if same else [L]
        print(f"L {L} [{st[0]}]: p {p:.4f} p0 {p0:.4f} g {g:+.4f} (2 SE {2 * sg:.4f}) -> {verdict}; noiseless recorded "
              f"{R['noiseless']:.4f}, Aer {nl:.4f} (SE {nse:.4f}); record: {R['verdict']} g {R['g']:+.4f} -> "
              f"{'SAME' if same else 'DIFFERENT'}")
    dcnt, dcirc = cells["ff_dr"]
    fcnt, _ = cells["ff_dr_floor"]
    for b, q in enumerate(rec["probe_qubits"]):
        p11, s11, _ = share(dcnt, b, 1)
        p00, s00, _ = share(fcnt, b, 0)
        R = rec["dr"][str(q)]
        same = abs(R["p11"] - p11) < 1e-12 and abs(R["p00"] - p00) < 1e-12
        bad += [] if same else [f"dr{q}"]
        print(f"Dr q{q}: P(1|1) {p11:.4f} P(0|0) {p00:.4f} gap {p00 - p11:+.4f}; record {R['p11']:.4f} / {R['p00']:.4f} "
              f"-> {'SAME' if same else 'DIFFERENT'}")
    print("ALL SAME" if not bad else f"DIFFERENT {bad}")
    return not bad


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
