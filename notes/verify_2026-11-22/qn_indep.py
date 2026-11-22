"""Independent recount of results/qpe-n78-night-2026-11-22 (home VS): qiskit / aer / numpy only, no psf-os and no
notebook scorer (the IPE circuits for the every-phase CZ mean come from the notebook's apps.ipe, the circuit
definition itself). Per item: the success bits named in its record, right values from noiseless Aer of the recorded
circuit; pooled shares, 2 SE, the twin differences, the log drops and acceleration with the declared SE, the words and
the declared table's row. Sent: circuits, shots, phases against k a mod 2^n, the compiled CZ of the sample against every
phase (qiskit's own level-1 transpile on a 2-qubit line), psf_os_build, the parked waits fenced, the device rule."""
import json
import math
import os
import sys
from collections import Counter

from qiskit import qpy, transpile
from qiskit_aer import AerSimulator

R, NBK, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, os.path.join(NBK, "notes", "ffapps_2026-11-17"))
CEIL = {6: 0.3065, 7: 0.2480, 8: 0.2007}          # the declared exact ceilings (not recomputed here)
sim = AerSimulator()
lines = []
say = lambda s: (print(s), lines.append(s))


def bit(k, i):
    return int(k.replace(" ", "")[-1 - i])


def word(d, se):
    return "KEEPS MORE" if d >= 2 * se and d > 0 else "KEEPS LESS" if d <= -2 * se and d < 0 else "SAME WITHIN ERROR"


def ceil_word(p, se, C):
    return "BEYOND THE CEILING" if p >= C + 2 * se else "NOT BEYOND"


jd = f"{R}/qn/job0"
man = json.load(open(f"{jd}/job/manifest.json"))
raw = json.load(open(f"{jd}/job/raw_counts.json"))
circs = qpy.load(open(f"{jd}/job/circuits.qpy", "rb"))
cells = {c["cell"]: c for c in man["cells"]}
counts = {r["pub"]: r["counts"] for r in raw["rows"]}
by, roles, shots = {}, Counter(), set()
for i, p in enumerate(man["pubs"]):
    c = cells[p["cell"]]
    roles[c["role"]] += 1
    shots.add(sum(counts[i].values()))
    if c["role"] == "user":
        by[c["name"][3:]] = (i, json.load(open(f"{jd}/runs/{c['name']}.json")))
b = man.get("psf_os_build", {})
say(f"sent: {len(man['pubs'])} circuits, roles {dict(roles)}, shots {sorted(shots)}; psf_os_build {b}")

res = {}
for n in (6, 7, 8):
    a = int(round(2 ** n * (math.sqrt(5) - 1) / 2))
    a += (a % 2 == 0)
    want = [(k * a) % 2 ** n for k in range(1, 17)]
    pk_tags = sorted((t for t in by if t.startswith(f"ipk{n}_")), key=lambda t: int(t.split("_")[1]))
    pu_tags = sorted((t for t in by if t.startswith(f"ipu{n}_")), key=lambda t: int(t.split("_")[1]))
    got = sorted(int(t.split("_")[1]) for t in pk_tags)
    tw = sorted(int(t.split("_")[1]) for t in pu_tags)
    say(f"n {n}: a {a}; parked phases equal k a mod 2^n (k = 1..16): {got == sorted(want)}; twins at k = 1..4 "
        f"{tw == sorted(want[:4])} ({tw})")

    def share(tags):
        ok = N = 0
        for t in tags:
            i, rec = by[t]
            sb = sorted(int(x) for x in rec["success"])
            ideal = sim.run(circs[i], shots=4000, seed_simulator=3).result().get_counts()
            right = {}
            for x in sb:
                p1 = sum(v for k, v in ideal.items() if bit(k, x) == 1) / 4000
                assert p1 in (0.0, 1.0)
                right[x] = int(p1)
            assert right == {int(x): v for x, v in rec["success"].items()}
            ok += sum(v for k, v in counts[i].items() if all(bit(k, x) == right[x] for x in sb))
            N += sum(counts[i].values())
        p = ok / N
        return p, math.sqrt(p * (1 - p) / N), N
    p, se, N = share(pk_tags)
    pk4, sk4, _ = share([t.replace("ipu", "ipk") for t in pu_tags])
    pu4, su4, _ = share(pu_tags)
    d, sd = pk4 - pu4, math.sqrt(sk4 ** 2 + su4 ** 2)
    res[n] = dict(p=p, se=se, verdict=ceil_word(p, se, CEIL[n]), d=d, sd=sd, word=word(d, sd))
    say(f"   parked {p:.4f} (2 SE {2 * se:.4f}, {N} shots) against C {CEIL[n]} -> {res[n]['verdict']} (margin "
        f"{p - CEIL[n]:+.4f}); twins parked {pk4:.4f} - unparked {pu4:.4f} = {d:+.4f} (2 SE {2 * sd:.4f}) {res[n]['word']}")
    # compiled CZ: the job's sample against every phase (qiskit level 1 on a 2-qubit line)
    import apps as AP

    def cz_of(j):
        qc, _ = AP.ipe(n, j, True)
        t = transpile(qc, basis_gates=["cz", "rz", "sx", "x", "if_else"], coupling_map=[[0, 1], [1, 0]],
                      optimization_level=1, seed_transpiler=0)
        cnt = 0
        for ins in t.data:
            if ins.operation.name == "cz":
                cnt += 1
            elif ins.operation.name == "if_else":
                cnt += sum(1 for blk in ins.operation.blocks for x in blk.data if x.operation.name == "cz")
        return cnt
    every = [cz_of(j) for j in range(2 ** n)]
    samp_q = [cz_of(j) for j in got]
    samp_job = [sum(1 for x in circs[by[t][0]].data if x.operation.name == "cz") for t in pk_tags]
    say(f"   compiled CZ mean (qiskit): every phase {sum(every) / len(every):.2f}, the 16 phases {sum(samp_q) / 16:.2f}; "
        f"in the job (as sent) {sum(samp_job) / 16:.2f}")
    # parked waits fenced with target and ancilla (copy of the record's chain)
    bad = []
    for t in pk_tags:
        i, rec = by[t]
        c = circs[i]
        tgt, anc = rec["chain"][1], rec["chain"][0]
        parked = rec["park"]["arms"]["ff"]["parked"]
        bars = [{c.find_bit(q).index for q in x.qubits} for x in c.data if x.operation.name == "barrier"]
        if not parked or not any({tgt, anc} <= s for s in bars):
            bad.append(t)
    say(f"   parked items fenced with target and ancilla: {not bad}; twins unparked: "
        f"{all(by[t][1]['park'] == {'park': False, 'skipped': 'park_skip'} for t in pu_tags)}")

l = {n: math.log(res[n]["p"]) for n in res}
t = {n: res[n]["se"] / res[n]["p"] for n in res}
acc = (l[7] - l[8]) - (l[6] - l[7])
sea = math.sqrt(t[6] ** 2 + 4 * t[7] ** 2 + t[8] ** 2)
shape = "ACCELERATES" if acc >= 2 * sea and acc > 0 else "SLOWS" if acc <= -2 * sea and acc < 0 else "FLAT"
say(f"log drops {l[6] - l[7]:+.4f} (6 -> 7), {l[7] - l[8]:+.4f} (7 -> 8); acceleration {acc:+.4f} (2 SE {2 * sea:.4f}) "
    f"-> {shape} (beside)")
c8, c7, p8 = res[8]["verdict"], res[7]["verdict"], res[8]["word"]
if c8.startswith("BEYOND") and c7.startswith("BEYOND"):
    row = {"KEEPS MORE": "reaches n = 8, parking keeps more there", "SAME WITHIN ERROR":
           "reaches n = 8; parking's gain not seen at n = 8", "KEEPS LESS": "reaches n = 8, parking costs at n = 8"}[p8]
elif c8.startswith("BEYOND"):
    row = "not read (n = 8 beyond, n = 7 not)"
elif c7.startswith("BEYOND"):
    row = "the range ends between n = 7 and 8"
else:
    row = "the range ends before n = 7"
say(f"the declared table's row: {row}")
q = json.load(open(f"{R}/fetch_in/queue.json"))
cand = [d for d in q["chosen"] if d != "ibm_marrakesh"]
pick = min(cand, key=lambda d: (q["pending"][d], cand.index(d)))
u = raw["metrics"]["usage"]
say(f"device rule: pending {q['pending']}, order {q['chosen']} -> {pick}; ran on {man['fetch']['backend']}; charged "
    f"{u['qpu_charge_time_seconds']} s, {u['value']:.4f} RU, model {man['qpu_seconds_model']}")
json.dump(dict(lines=lines), open(OUT, "w"), indent=1)
