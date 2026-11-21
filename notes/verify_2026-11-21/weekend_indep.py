"""Independent recount of results/weekend-shared-night-2026-11-21 (home VS): qiskit / aer / numpy only, no psf-os and
no notebook scorer. Per item: the success bits named in its record, their right values from noiseless Aer sampling of
the recorded circuit itself; pooled shares, 2 SE, the declared comparisons, the log shape of B, the words. The
ceilings are the declared exact values (A 0.875; C(n) 0.4706, 0.3792, 0.3065); they are not recomputed here."""
import json
import math
import sys
from collections import defaultdict

from qiskit import qpy
from qiskit_aer import AerSimulator

R = sys.argv[1]
OUT = sys.argv[2]
JOBS = {"A": "A/job0", "BC0": "BC/job0", "BC1": "BC/job1"}
CEIL = {"A": 0.875, 4: 0.4706, 5: 0.3792, 6: 0.3065}
sim = AerSimulator()
lines = []
say = lambda s: (print(s), lines.append(s))


def bit(key, i):
    k = key.replace(" ", "")
    return int(k[-1 - i])


def ceiling_word(p, se, C):
    return "BEYOND THE CEILING" if p >= C + 2 * se else "NOT BEYOND"


def pair_word(d, se):
    return "KEEPS MORE" if d >= 2 * se and d > 0 else "KEEPS LESS" if d <= -2 * se and d < 0 else "SAME WITHIN ERROR"


items = {}            # tag -> dict(succ, n, job, cz, qubits)
jobinfo = {}
for jn, jd in JOBS.items():
    man = json.load(open(f"{R}/{jd}/job/manifest.json"))
    raw = json.load(open(f"{R}/{jd}/job/raw_counts.json"))
    circs = qpy.load(open(f"{R}/{jd}/job/circuits.qpy", "rb"))
    cells = {c["cell"]: c for c in man["cells"]}
    counts = {row["pub"]: row["counts"] for row in raw["rows"]}
    roles = defaultdict(int)
    shots = set()
    for i, p in enumerate(man["pubs"]):
        c = cells[p["cell"]]
        roles[c["role"]] += 1
        shots.add(sum(counts[i].values()))
        if c["role"] != "user":
            continue
        name = c["name"]
        assert name.startswith("ff_") and not name.endswith(("_off", "_floor")), name
        tag = name[3:]
        rec = json.load(open(f"{R}/{jd}/runs/{name}.json"))
        sbits = sorted(int(b) for b in rec["success"])
        qc = circs[i]
        ideal = sim.run(qc, shots=20000, seed_simulator=3).result().get_counts()
        right = {}
        for b in sbits:
            p1 = sum(v for k, v in ideal.items() if bit(k, b) == 1) / 20000
            assert p1 in (0.0, 1.0), (tag, b, p1)          # every success bit is deterministic without noise
            right[b] = int(p1)
        assert right == {int(b): v for b, v in rec["success"].items()}, (tag, right, rec["success"])
        ok = sum(v for k, v in counts[i].items() if all(bit(k, b) == right[b] for b in sbits))
        N = sum(counts[i].values())
        used = sorted({qc.find_bit(q).index for ins in qc.data for q in ins.qubits
                       if ins.operation.name not in ("barrier",)})
        cz = sum(1 for ins in qc.data if ins.operation.name == "cz")
        cz += sum(sum(1 for x in blk.data if x.operation.name == "cz") for ins in qc.data
                  if ins.operation.name == "if_else" for blk in ins.operation.blocks)
        items[tag] = dict(ok=ok, N=N, job=jn, cz=cz, qubits=used)
    usage = raw["metrics"]["usage"]
    jobinfo[jn] = dict(circuits=len(man["pubs"]), shots=shots, roles=dict(roles), charged=usage["qpu_charge_time_seconds"],
                       ru=usage["value"], model=man["qpu_seconds_model"])


def pool(tags):
    ok = sum(items[t]["ok"] for t in tags)
    N = sum(items[t]["N"] for t in tags)
    p = ok / N
    return p, math.sqrt(p * (1 - p) / N), N


# ---- A
ERR = ("n", "0", "1", "2")
pa = {}
for f in ("F16", "F10", "F6P", "F6"):
    p, se, N = pool([f"{f.lower()}_{e}" for e in ERR])
    pa[f] = (p, se)
    per = [items[f"{f.lower()}_{e}"]["ok"] / items[f"{f.lower()}_{e}"]["N"] for e in ERR]
    say(f"A {f}: p {p:.4f} (2 SE {2 * se:.4f}, {N} shots) -> {ceiling_word(p, se, 0.875)} (margin {p - 0.875:+.4f}); "
        f"per error n/d0/d1/d2 " + " / ".join(f"{x:.3f}" for x in per))
wa = {}
for name, (x, y) in {"footprint": ("F6P", "F10"), "cz": ("F6", "F6P"), "cz16 (beside)": ("F10", "F16")}.items():
    d = pa[x][0] - pa[y][0]
    se = math.sqrt(pa[x][1] ** 2 + pa[y][1] ** 2)
    wa[name] = pair_word(d, se)
    say(f"A {name} {x} - {y}: {d:+.4f} (2 SE {2 * se:.4f}) -> {wa[name]}")
row = {("KEEPS MORE", "KEEPS MORE"): "both", ("KEEPS MORE", "SAME WITHIN ERROR"): "the footprint",
       ("SAME WITHIN ERROR", "KEEPS MORE"): "the CZ count", ("SAME WITHIN ERROR", "SAME WITHIN ERROR"): "neither"}
say(f"A reading row: {row.get((wa['footprint'], wa['cz']), 'against the expectation')}")

# ---- C
pc = {}
for f in ("pl", "fe", "pk"):
    tags = [f"{f}4_{j}" for j in range(16)]
    p, se, N = pool(tags)
    pc[f] = (p, se)
    say(f"C {f}: p {p:.4f} (2 SE {2 * se:.4f}, {N} shots) -> {ceiling_word(p, se, CEIL[4])}; jobs "
        f"{sorted({items[t]['job'] for t in tags})}")
wc = {}
for name, (x, y) in {"park": ("pk", "pl"), "fence": ("fe", "pl"), "pk - fe (beside)": ("pk", "fe")}.items():
    d = pc[x][0] - pc[y][0]
    se = math.sqrt(pc[x][1] ** 2 + pc[y][1] ** 2)
    wc[name] = pair_word(d, se)
    say(f"C {name} {x} - {y}: {d:+.4f} (2 SE {2 * se:.4f}) -> {wc[name]}")
crow = {("KEEPS MORE", "KEEPS LESS"): "decay", ("KEEPS MORE", "KEEPS MORE"): "dephasing",
        ("KEEPS MORE", "SAME WITHIN ERROR"): "waiting in |0> keeps more; |1> neither",
        ("SAME WITHIN ERROR", "SAME WITHIN ERROR"): "not seen"}
say(f"C reading row: {crow.get((wc['park'], wc['fence']), 'against the expectation')}")

# ---- B (n = 4 from C's pl)
pb = {}
ipe4 = [t for t in items if t.startswith("ipe4_")]
say(f"B: items tagged ipe4 in the jobs: {len(ipe4)} (n = 4 is read from C's pl4: {len([t for t in items if t.startswith('pl4_')])} items)")
for n in (4, 5, 6):
    tags = [f"pl4_{j}" for j in range(16)] if n == 4 else [f"ipe{n}_{j}" for j in range(2 ** n)]
    p, se, N = pool(tags)
    pb[n] = (p, se, N)
    say(f"B n {n}: p {p:.4f} (2 SE {2 * se:.4f}, {N} shots) -> {ceiling_word(p, se, CEIL[n])} (margin {p - CEIL[n]:+.4f}); "
        f"jobs {sorted({items[t]['job'] for t in tags})}")
l = {n: math.log(pb[n][0]) for n in pb}
t = {n: pb[n][1] / pb[n][0] for n in pb}
d5, d6 = l[4] - l[5], l[5] - l[6]
acc = d6 - d5
se = math.sqrt(t[4] ** 2 + 4 * t[5] ** 2 + t[6] ** 2)
word = "ACCELERATES" if acc >= 2 * se and acc > 0 else "SLOWS" if acc <= -2 * se and acc < 0 else "FLAT"
say(f"B log drops {d5:+.4f}, {d6:+.4f}; acceleration {acc:+.4f} (2 SE {2 * se:.4f}) -> {word}")
s5, s6 = pb[4][0] - pb[5][0], pb[5][0] - pb[6][0]
sse = math.sqrt(pb[4][1] ** 2 + 4 * pb[5][1] ** 2 + pb[6][1] ** 2)
say(f"B beside, on the share: drops {s5:+.4f}, {s6:+.4f}; acceleration {s6 - s5:+.4f} (2 SE {2 * sse:.4f})")

# ---- what was sent
for jn, j in jobinfo.items():
    say(f"job {jn}: {j['circuits']} circuits, shots {sorted(j['shots'])}, roles {j['roles']}, charged {j['charged']} s, "
        f"{j['ru']:.4f} RU, model {j['model']}")
say(f"total: charged {sum(j['charged'] for j in jobinfo.values())} s, {sum(j['ru'] for j in jobinfo.values()):.4f} RU, "
    f"model {sum(j['model'] for j in jobinfo.values()):.1f} s")
qa = sorted({q for t_, x in items.items() if x["job"] == "A" for q in x["qubits"]})
qbc = sorted({q for t_, x in items.items() if x["job"] != "A" for q in x["qubits"]})
say(f"qubits touched by the user circuits: A {qa}; BC {qbc}")

# ---- compiled CZ per phase, C's forms
same_cz = True
for j in range(16):
    czs = {f: items[f"{f}4_{j}"]["cz"] for f in ("pl", "fe", "pk")}
    same_cz &= len(set(czs.values())) == 1
say("C compiled CZ per phase (pl/fe/pk): " + "; ".join(f"{j}: {items[f'pl4_{j}']['cz']}/{items[f'fe4_{j}']['cz']}/"
                                                       f"{items[f'pk4_{j}']['cz']}" for j in range(16))
    + f" -> {'the same at every phase' if same_cz else 'DIFFERENT'}")
json.dump(dict(lines=lines), open(OUT, "w"), indent=1)
