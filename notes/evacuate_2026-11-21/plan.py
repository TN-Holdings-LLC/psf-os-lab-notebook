"""Device plans for the evacuation study, built and checked, never run (home VS, 2026-11-21 night; desk). For the
RUS chains, the three forms of one circuit side by side in one job: the default (psf-os 0.3.0: nothing to park, so
unfenced), fenced (fence_waits(conditionals=True)) and evacuated (psf_os.evacuate: the B1 qubits, fenced). The dry runs
(dry.txt) put the large differences in the fence and only small ones in B1, so each plan reads both: fence = fenced -
default, B1 = evacuated - fenced, g as the loop reads it (|P - exact|). ff arms only, one sentinel per job, copies a, b,
... of every item in the same job.

  python notes/evacuate_2026-11-21/plan.py DEVDIR WORK OUT.json      build every plan, check, size
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, "..", ".."))
for d in ("gpu", "notes/rus_coherent_2026-11-17", "notes/os2_2026-11-18"):
    sys.path.insert(0, os.path.join(NB, d))
from psf_os import feedforward as FF  # noqa: E402
from psf_os.device import Device  # noqa: E402
from psf_os.evacuate import evacuate  # noqa: E402
from psf_os.footprint import exact_distribution, fence_waits  # noqa: E402

SHOTS = 4000
# expected differences from dry.txt (illustrative noise a wait / c cond): (fence, B1)
PLANS = {
    "A (P2 m3 L3, 4 copies)": dict(items=[("P2", 3, 3)], copies=4),
    "B (P2 m3 L2, L3; 2 copies)": dict(items=[("P2", 3, 2), ("P2", 3, 3)], copies=2),
    "C (P2 m3 L3 and P0 L3; 4 copies)": dict(items=[("P2", 3, 3), ("P0", 3, 3)], copies=4),
    "D (P0, P2 m3 at L 1-3; 2 copies)": dict(items=[(p, 3, L) for p in ("P0", "P2") for L in (1, 2, 3)], copies=2),
}


def circuit(presc, m, L):
    import rus2_night as R2  # noqa: F401
    import rus3_night as R3
    if presc == "P0":
        return FF.rus_chain(L, 1.1, m=3)
    return R3.chain(L, 1.1, m=m)


def qpu_seconds(n):
    return n * 0.036 + n * SHOTS * 0.00027 + 3.0


def main():
    dev = Device.load(sys.argv[1])
    work = sys.argv[2]
    os.makedirs(work, exist_ok=True)
    comp = FF.Compiler(dev)
    res = {}
    for name, plan in PLANS.items():
        items, skip, checks = [], [], []
        for presc, m, L in plan["items"]:
            qc, spec = circuit(presc, m, L)
            low = FF.lower(qc)
            forms = {"d": low, "f": fence_waits(low, conditionals=True), "e": evacuate(low, ("L", "K", "B"))[0]}
            d0 = exact_distribution(low)
            chain = FF.place(dev, low.num_qubits)["chain"]
            czs = {k: FF.cz_count(comp.run(FF.on_device(c, chain, dev.num_qubits))) for k, c in forms.items()}
            same = all(all(abs(d0.get(x, 0) - exact_distribution(c).get(x, 0)) < 1e-9 for x in set(d0))
                       for c in forms.values())
            checks.append(dict(item=f"{presc} m{m} L{L}", cz=czs, cz_same=len(set(czs.values())) == 1,
                               distribution_same=same, evacuated_differs=forms["e"] != forms["f"]))
            for k, c in forms.items():
                for cp in "abcd"[:plan["copies"]]:
                    tag = f"{presc.lower()}m{m}l{L}{k}{cp}"
                    items.append((tag, c, spec))
                    if k != "d":
                        skip.append(tag)             # the fenced and evacuated forms built as given (not parked)
        out = os.path.join(work, name.split()[0])
        rep = FF.build(dev, items, out, shots=SHOTS, max_seconds=60, ff_only=[t for t, _, _ in items],
                       park=True, park_skip=skip, sentinel_spec=dict(kind="echo_clifford", D=24))
        n_pairs = len(plan["items"])
        p = 0.8
        se_diff = math.sqrt(2 * p * (1 - p) / (SHOTS * plan["copies"]))
        res[name] = dict(circuits=rep["circuits"], seconds=rep["qpu_seconds_model"], items=plan["items"],
                         copies=plan["copies"], two_se_per_difference=round(2 * se_diff, 4), checks=checks)
        print(f"{name}: {rep['circuits']} circuits, {rep['qpu_seconds_model']:.1f} s; 2 SE per difference "
              f"{2 * se_diff:.4f}; checks " + "; ".join(f"{c['item']} CZ {c['cz']} same {c['cz_same']}, distribution "
                                                       f"same {c['distribution_same']}" for c in checks), flush=True)
    json.dump(res, open(sys.argv[3], "w"), indent=1)


if __name__ == "__main__":
    main()
