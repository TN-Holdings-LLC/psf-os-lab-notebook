"""Expected differences and the excited count, per RUS item and form (home VS, 2026-11-21 night; desk, no device).
For each item of gpu/rus_fence_night.py: P of D, F, M under the three ILLUSTRATIVE noises (density matrix, 40000
shots, the same seed for every form), g of the fence (F - D) and of parking (M - F); and, compiled on a device record
(rule C), the excited count while waiting (footprint.wait_footprint, span, conditionals: the expected waiting qubits in
|1> summed over the waits, as sent) per form. Record only; never a verdict.

  python notes/rus_fence_2026-11-21/expect.py DEVDIR OUT.json
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(NB, "gpu"))
import rus_fence_night as RF  # noqa: E402

SHOTS = 40000


def main():
    from qiskit import transpile
    from qiskit_aer import AerSimulator
    from psf_os import feedforward as FF
    from psf_os.device import Device
    from psf_os.footprint import wait_footprint
    dev = Device.load(sys.argv[1])
    comp = FF.Compiler(dev)
    sim = AerSimulator(method="density_matrix")
    res = {}
    for key, (presc, m, L) in RF.RUS.items():
        fm, spec, chosen = RF.forms(key)
        ob, ex = spec["out_bit"], spec["exact"]
        want = "1" if RF.reads_one(presc) else "0"
        row = dict(item=f"{presc} m{m} L{L}", exact=ex, majority_x=len(chosen), excited={}, noise={})
        chain = FF.place(dev, fm["D"].num_qubits)["chain"]
        for k, c in fm.items():
            cc = comp.run(FF.on_device(c, chain, dev.num_qubits))
            row["excited"][k] = round(float(wait_footprint(FF.compact(cc), span=True, conditionals=True)
                                            ["excited_waits"]), 3)
        for nz, noise in RF.NOISES.items():
            P = {}
            for k, c in fm.items():
                t = transpile(c, basis_gates=["cz", "rz", "sx", "x"], optimization_level=1, seed_transpiler=0)
                cnt = sim.run(RF.noisy(t, noise), shots=SHOTS, seed_simulator=7).result().get_counts()
                n = c.num_clbits
                P[k] = sum(v for kk, v in cnt.items() if kk.replace(" ", "")[n - 1 - ob] == want) / SHOTS
            se = lambda x, y: 2 * math.sqrt(P[x] * (1 - P[x]) / SHOTS + P[y] * (1 - P[y]) / SHOTS)
            row["noise"][nz] = dict(P=P, fence=abs(P["D"] - ex) - abs(P["F"] - ex),
                                    park=abs(P["F"] - ex) - abs(P["M"] - ex), two_se=se("F", "D"))
        res[key] = row
        print(f"{key} ({row['item']}): majority X at {len(chosen)} qubit-waits; excited while waiting (compiled) "
              f"D {row['excited']['D']} F {row['excited']['F']} M {row['excited']['M']}; " +
              "; ".join(f"{nz}: fence {v['fence']:+.4f} park {v['park']:+.4f} (2 SE {v['two_se']:.4f})"
                        for nz, v in row["noise"].items()), flush=True)
    json.dump(res, open(sys.argv[2], "w"), indent=1)


if __name__ == "__main__":
    main()
