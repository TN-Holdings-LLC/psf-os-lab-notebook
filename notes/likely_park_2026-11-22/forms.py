"""Keeping the likely-value X pairs without the full fence's cost (home VS, 2026-11-22; home instruction "0.3.1 の机上
設計"; desk, no device). On the night of 2026-11-21 (ibm_fez, results/rus-fence-night-2026-11-21), parking the likely
value gained on top of the full fence (NF +0.088), but the full fence cost on P0 and P3 (-0.045, -0.024). Forms of one
RUS item, built on psf-os 0.3.0's footprint (its waits and branching), compiled by psf-os 0.3.0 on a device record:

  D     the default (no fence, no X)
  F     the full fence at every wait (fence_waits(conditionals=True))
  M     F + the likely value parked (X before and after each wait on every waiting qubit with P(|1>) > 0.5): the night's M
  MW    the full fence only at the waits where a qubit is parked, + its X pairs
  MP    at those waits only, a partial fence: a barrier on the parked qubits and the wait's own qubits (measured there or
        inside its conditionals), + the X pairs; every other qubit free as in D
  MQ    at those waits, a barrier on the parked qubits alone, + the X pairs (the pair cannot cancel, but nothing ties it
        to the wait)
  X0    the X pairs alone, no barrier: the compiler folds them into the neighbouring gates (the folding idea)
  Y0    Y pairs alone, no barrier (another pair that is the identity)

Per form: the compiled CZ (must equal D's), the compiled noiseless distribution (must equal D's), the compiled depth,
the number of compiled one-qubit gates that differ from D, whether the compiled circuit is D's own (a cancelled pair),
the excited count while waiting as compiled (footprint, span, conditionals; record only); and the dry runs under the
three ILLUSTRATIVE noises of gpu/rus_fence_night.py on the compiled circuits, g against D.

  python notes/likely_park_2026-11-22/forms.py DEVDIR OUT.json
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(NB, "gpu"))
import rus_fence_night as RF  # noqa: E402  (its items, forms, noises; read only)

ITEMS = ("p0l3", "nfl3m3", "p3l3", "p2l3m3")
SHOTS = 40000


def inserted(low, f):
    """Indices of f's instructions that fence_waits inserted (f is low with barriers added)."""
    j, ins = 0, set()
    ld = list(low.data)
    for i, x in enumerate(f.data):
        # the same instruction (control-flow ops are copied on append, so compared by value)
        if j < len(ld) and x.operation == ld[j].operation and list(x.qubits) == list(ld[j].qubits) and                 list(x.clbits) == list(ld[j].clbits):
            j += 1
        else:
            ins.add(i)
    assert j == len(ld), "fence_waits did more than add barriers"
    return ins


def plan(low):
    """(f, windows with their parked qubits, inserted indices) from psf-os 0.3.0's footprint."""
    from psf_os.footprint import _reduced, _simulate, _windows, fence_waits
    f = fence_waits(low, conditionals=True)
    wins = _windows(f)
    _, sim = _simulate(f, [w["start"] for w in wins])
    act, pos = sim["act"], sim["pos"]
    n = len(act)
    out = []
    for w in wins:
        flip = [q for q in act if q not in w["involved"] and
                sum(p * float(_reduced(sv.data, pos[q], n)[1, 1].real) for p, sv, _ in sim["at"][w["start"]]) > 0.5 + 1e-9]
        out.append(dict(w, flip=flip))
    return f, out, inserted(low, f)


def build_form(low, kind):
    from qiskit.circuit.library import XGate, YGate
    f, wins, ins = plan(low)
    data = list(f.data)
    allq = list(f.qubits)
    parked = [w for w in wins if w["flip"]]
    starts = {w["start"]: w for w in parked}
    ends = {w["end"]: w for w in parked}
    keep_fence = set()
    if kind in ("F", "M"):
        keep_fence = set(ins)
    elif kind == "MW":
        keep_fence = {w["start"] for w in parked} | {w["end"] for w in parked if w["close"]}
    gate = YGate() if kind == "Y0" else XGate()
    out = f.copy_empty_like()

    def bar(qs):
        out.barrier([allq[q] for q in sorted(set(qs))])
    for i, x in enumerate(data):
        w = starts.get(i)
        if w is not None and kind not in ("D", "F"):
            for q in w["flip"]:
                out.append(gate, [allq[q]])
            if kind == "MP":
                bar(w["flip"] + w["involved"])
            elif kind == "MQ":
                bar(w["flip"])
        if i in ins and i not in keep_fence:
            pass                                    # an inserted fence not kept
        else:
            out.append(x.operation, x.qubits, x.clbits)
        w = ends.get(i)
        if w is not None and kind not in ("D", "F"):
            if not w["close"] and kind in ("M", "MW"):
                out.barrier(allq)
            if kind == "MP":
                bar(w["flip"] + w["involved"])
            elif kind == "MQ":
                bar(w["flip"])
            for q in w["flip"]:
                out.append(gate, [allq[q]])
    return out


def main():
    from qiskit import transpile
    from qiskit_aer import AerSimulator
    from psf_os import feedforward as FF
    from psf_os.device import Device
    from psf_os.footprint import exact_distribution, wait_footprint
    dev = Device.load(sys.argv[1])
    comp = FF.Compiler(dev)
    sim = AerSimulator(method="density_matrix")
    kinds = ("D", "F", "M", "MW", "MP", "MQ", "X0", "Y0")
    res = {}
    for key in ITEMS:
        presc, m, L = RF.RUS[key]
        qc, spec = RF.rus_circuit(presc, m, L)
        low = FF.lower(qc)
        chain = FF.place(dev, low.num_qubits)["chain"]
        ob, ex = spec["out_bit"], spec["exact"]
        want = "1" if RF.reads_one(presc) else "0"
        comp_c, row = {}, dict(item=f"{presc} m{m} L{L}", forms={})
        for k in kinds:
            c = build_form(low, k)
            cc = FF.compact(comp.run(FF.on_device(c, chain, dev.num_qubits)))
            comp_c[k] = cc
        dD = exact_distribution(comp_c["D"])
        oneq = lambda c: [(x.operation.name, tuple(c.find_bit(q).index for q in x.qubits)) for x in c.data
                          if x.operation.name in ("x", "sx", "rz")]
        for k, cc in comp_c.items():
            d = exact_distribution(cc)
            same = all(abs(dD.get(x, 0) - d.get(x, 0)) < 1e-9 for x in set(dD) | set(d))
            a, b = oneq(comp_c["D"]), oneq(cc)
            row["forms"][k] = dict(cz=FF.cz_count(cc), cz_same=FF.cz_count(cc) == FF.cz_count(comp_c["D"]),
                                   distribution_same=same, depth=cc.depth(), equal_to_D=(cc == comp_c["D"]),
                                   one_qubit=len(b), one_qubit_vs_D=len(b) - len(a),
                                   barriers=sum(1 for x in cc.data if x.operation.name == "barrier"),
                                   excited=round(float(wait_footprint(cc, span=True, conditionals=True)["excited_waits"]), 3),
                                   noise={})
        for nz, noise in RF.NOISES.items():
            P = {}
            for k, cc in comp_c.items():
                t = transpile(cc, basis_gates=["cz", "rz", "sx", "x"], optimization_level=0)
                cnt = sim.run(RF.noisy(t, noise), shots=SHOTS, seed_simulator=7).result().get_counts()
                n = cc.num_clbits
                P[k] = sum(v for kk, v in cnt.items() if kk.replace(" ", "")[n - 1 - ob] == want) / SHOTS
            for k in kinds:
                g = abs(P["D"] - ex) - abs(P[k] - ex)
                se = 2 * math.sqrt(P["D"] * (1 - P["D"]) / SHOTS + P[k] * (1 - P[k]) / SHOTS)
                row["forms"][k]["noise"][nz] = dict(P=round(P[k], 4), g_vs_D=round(g, 4), two_se=round(se, 4))
        res[key] = row
        print(f"== {key} ({row['item']})", flush=True)
        for k, v in row["forms"].items():
            print(f"  {k:3s} CZ {v['cz']} same {v['cz_same']} dist same {v['distribution_same']} depth {v['depth']} "
                  f"1q {v['one_qubit']} ({v['one_qubit_vs_D']:+d}) barriers {v['barriers']} equal to D {v['equal_to_D']} "
                  f"excited {v['excited']}; g vs D: " +
                  ", ".join(f"{nz} {x['g_vs_D']:+.4f}" for nz, x in v["noise"].items()), flush=True)
    json.dump(res, open(sys.argv[2], "w"), indent=1)


if __name__ == "__main__":
    main()
