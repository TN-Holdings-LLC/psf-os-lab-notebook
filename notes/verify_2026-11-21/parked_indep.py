"""Independent recount of results/qpe-parked-night-2026-11-21 (home VS): qiskit / aer / numpy only, no psf-os and no
notebook scorer. Per item: the success bits named in its record, their right values from noiseless Aer of the recorded
circuit; pooled shares, 2 SE, the paired differences (parked - unparked on the phases holding both), the log shape of
the parked form with SE = sqrt(t4^2 + 4 t5^2 + t6^2), the words and the reading table's row. Beside: the compiled CZ per
phase; the target's state at every wait of the parked n = 4 circuits (branching with qiskit statevectors); the parked
n = 4 circuits against the weekend's C pk circuits. Ceilings: the declared exact values (0.4706, 0.3792, 0.3065)."""
import json
import math
import sys
from collections import defaultdict

import numpy as np
from qiskit import qpy
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

R, WK, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
CEIL = {4: 0.4706, 5: 0.3792, 6: 0.3065}
sim = AerSimulator()
lines = []
say = lambda s: (print(s), lines.append(s))


def bit(key, i):
    return int(key.replace(" ", "")[-1 - i])


def word(d, se):
    return "KEEPS MORE" if d >= 2 * se and d > 0 else "KEEPS LESS" if d <= -2 * se and d < 0 else "SAME WITHIN ERROR"


def load_job(jd):
    man = json.load(open(f"{jd}/job/manifest.json"))
    raw = json.load(open(f"{jd}/job/raw_counts.json"))
    circs = qpy.load(open(f"{jd}/job/circuits.qpy", "rb"))
    cells = {c["cell"]: c for c in man["cells"]}
    return man, raw, circs, cells


items, jobs = {}, {}
for jn in ("job0", "job1"):
    jd = f"{R}/qp/{jn}"
    man, raw, circs, cells = load_job(jd)
    counts = {row["pub"]: row["counts"] for row in raw["rows"]}
    roles, shots = defaultdict(int), set()
    for i, p in enumerate(man["pubs"]):
        c = cells[p["cell"]]
        roles[c["role"]] += 1
        shots.add(sum(counts[i].values()))
        if c["role"] != "user":
            continue
        name = c["name"]
        assert name.startswith("ff_") and not name.endswith(("_off", "_floor")), name
        rec = json.load(open(f"{jd}/runs/{name}.json"))
        sb = sorted(int(b) for b in rec["success"])
        ideal = sim.run(circs[i], shots=20000, seed_simulator=3).result().get_counts()
        right = {}
        for b in sb:
            p1 = sum(v for k, v in ideal.items() if bit(k, b) == 1) / 20000
            assert p1 in (0.0, 1.0), (name, b, p1)
            right[b] = int(p1)
        assert right == {int(b): v for b, v in rec["success"].items()}, name
        ok = sum(v for k, v in counts[i].items() if all(bit(k, b) == right[b] for b in sb))
        cz = sum(1 for ins in circs[i].data if ins.operation.name == "cz")
        cz += sum(sum(1 for x in blk.data if x.operation.name == "cz") for ins in circs[i].data
                  if ins.operation.name == "if_else" for blk in ins.operation.blocks)
        used = sorted({circs[i].find_bit(q).index for ins in circs[i].data for q in ins.qubits
                       if ins.operation.name != "barrier"})
        items[name[3:]] = dict(ok=ok, N=sum(counts[i].values()), job=jn, cz=cz, qubits=used, circ=circs[i])
    u = raw["metrics"]["usage"]
    jobs[jn] = dict(circuits=len(man["pubs"]), roles=dict(roles), shots=shots, build=man.get("psf_os_build"),
                    charged=u["qpu_charge_time_seconds"], ru=u["value"], model=man["qpu_seconds_model"],
                    parked=sum(1 for t, x in items.items() if x["job"] == jn and t.startswith("ipe")),
                    unparked=sum(1 for t, x in items.items() if x["job"] == jn and t.startswith("ipu")),
                    off_floor=[c["name"] for c in man["cells"] if c["name"].endswith(("_off", "_floor"))])


def pool(tags):
    ok = sum(items[t]["ok"] for t in tags)
    N = sum(items[t]["N"] for t in tags)
    p = ok / N
    return p, math.sqrt(p * (1 - p) / N), N


res = {}
words = {}
for n in (4, 5, 6):
    p, se, N = pool([f"ipe{n}_{j}" for j in range(2 ** n)])
    verdict = "BEYOND THE CEILING" if p >= CEIL[n] + 2 * se else "NOT BEYOND"
    pairs = sorted(j for j in range(2 ** n) if f"ipu{n}_{j}" in items)
    step = 2 ** n // 8
    same_job = all(items[f"ipu{n}_{j}"]["job"] == items[f"ipe{n}_{j}"]["job"] for j in pairs)
    pk, sk, _ = pool([f"ipe{n}_{j}" for j in pairs])
    pu, su, _ = pool([f"ipu{n}_{j}" for j in pairs])
    d, sd = pk - pu, math.sqrt(sk ** 2 + su ** 2)
    words[n] = word(d, sd)
    res[n] = (p, se)
    cz_pair = np.mean([items[f"ipe{n}_{j}"]["cz"] for j in pairs])
    cz_rest = np.mean([items[f"ipe{n}_{j}"]["cz"] for j in range(2 ** n) if j not in pairs])
    cz_twin = all(items[f"ipe{n}_{j}"]["cz"] == items[f"ipu{n}_{j}"]["cz"] for j in pairs)
    say(f"n {n}: parked {p:.4f} (2 SE {2 * se:.4f}, {N} shots) -> {verdict} (margin {p - CEIL[n]:+.4f}); paired phases "
        f"{pairs} (= 0, {step}, 2*{step}, ...: {pairs == list(range(0, 2 ** n, step))}; same job {same_job}); "
        f"{pk:.4f} - {pu:.4f} = {d:+.4f} (2 SE {2 * sd:.4f}) -> {words[n]}")
    rest = [j for j in range(2 ** n) if j not in pairs]
    pr, sr, _ = pool([f"ipe{n}_{j}" for j in rest])
    say(f"   beside: parked on the other phases {pr:.4f}; compiled CZ mean, paired {cz_pair:.2f} / other {cz_rest:.2f}; "
        f"per paired phase " + ", ".join(f"{j}:{items[f'ipe{n}_{j}']['cz']}" for j in pairs)
        + f"; twin CZ equal {cz_twin}")
l = {n: math.log(res[n][0]) for n in res}
t = {n: res[n][1] / res[n][0] for n in res}
acc = (l[5] - l[6]) - (l[4] - l[5])
se = math.sqrt(t[4] ** 2 + 4 * t[5] ** 2 + t[6] ** 2)
shape = "ACCELERATES" if acc >= 2 * se and acc > 0 else "SLOWS" if acc <= -2 * se and acc < 0 else "FLAT"
say(f"parked shape: log drops {l[4] - l[5]:+.4f}, {l[5] - l[6]:+.4f}; acceleration {acc:+.4f} (2 SE {2 * se:.4f}) -> {shape}")
ws = [words[n] for n in (4, 5, 6)]
if any(w == "KEEPS LESS" for w in ws):
    row = 5
elif shape == "SLOWS":
    row = 6
elif all(w == "KEEPS MORE" for w in ws):
    row = 1 if shape == "FLAT" else 2
elif all(w == "SAME WITHIN ERROR" for w in ws):
    row = 4
else:
    row = 3
say(f"reading table row (rows in the declared order): {row}")

for jn, j in jobs.items():
    say(f"{jn}: {j['circuits']} circuits, roles {j['roles']}, shots {sorted(j['shots'])}, parked {j['parked']} / "
        f"unparked {j['unparked']}, off/floor cells {j['off_floor'] or 'none'}, psf_os_build {j['build']}, charged "
        f"{j['charged']} s, {j['ru']:.4f} RU, model {j['model']}")
say(f"total charged {sum(j['charged'] for j in jobs.values())} s, {sum(j['ru'] for j in jobs.values()):.4f} RU, model "
    f"{sum(j['model'] for j in jobs.values()):.1f} s; qubits {sorted({q for x in items.values() for q in x['qubits']})}")


# the target's state at every wait (n = 4, parked and unparked), by branching with statevectors
def target_at_waits(qc, target=1, anc=0):
    """[(kind, P(target in |1>) averaged over branches, max over branches)] at every measurement (read) and every
    if_else (conditional) that is not on the target, on the compacted 2-qubit circuit."""
    act = sorted({qc.find_bit(q).index for ins in qc.data for q in ins.qubits if ins.operation.name != "barrier"})
    pos = {q: i for i, q in enumerate(act)}
    n = len(act)
    br = [(1.0, Statevector.from_label("0" * n), {})]
    out = []
    data = list(qc.data)
    for k, ins in enumerate(data):
        name = ins.operation.name
        if name in ("barrier", "delay"):
            continue
        qs = [pos[qc.find_bit(q).index] for q in ins.qubits]
        if name in ("measure", "if_else") and pos[act[target]] not in qs:
            p1 = [sv.probabilities([target])[1] for _, sv, _ in br]
            ws = [w for w, _, _ in br]
            later = any(x.operation.name not in ("measure", "barrier") for x in data[k + 1:])
            if later:
                out.append((name, float(np.dot(ws, p1)), float(max(p1))))
        if name == "measure":
            cb = qc.find_bit(ins.clbits[0]).index
            new = []
            for w, sv, bits in br:
                pr = sv.probabilities([qs[0]])
                for v in (0, 1):
                    if pr[v] < 1e-12:
                        continue
                    proj = np.diag([1.0, 0.0]) if v == 0 else np.diag([0.0, 1.0])
                    s2 = Statevector(sv.evolve(proj, [qs[0]]).data / math.sqrt(pr[v]))
                    b2 = dict(bits)
                    b2[cb] = v
                    new.append((w * pr[v], s2, b2))
            br = new
        elif name == "if_else":
            cond, val = ins.operation.condition
            idx = [qc.find_bit(cond).index]
            new = []
            for w, sv, bits in br:
                if sum(bits.get(b, 0) << i for i, b in enumerate(idx)) == int(val):
                    blk = ins.operation.blocks[0]
                    for bi in blk.data:
                        if bi.operation.name in ("barrier", "delay"):
                            continue
                        sv = sv.evolve(bi.operation, [qs[blk.find_bit(q).index] for q in bi.qubits])
                new.append((w, sv, bits))
            br = new
        else:
            br = [(w, sv.evolve(ins.operation, qs), b) for w, sv, b in br]
    return out


worst_parked, worst_unparked = 0.0, 0.0
for j in range(16):
    tw = target_at_waits(items[f"ipe4_{j}"]["circ"])
    worst_parked = max([worst_parked] + [m for _, _, m in tw])
    if f"ipu4_{j}" in items:
        tu = target_at_waits(items[f"ipu4_{j}"]["circ"])
        worst_unparked = max([worst_unparked] + [m for _, _, m in tu])
say(f"target at the waits (n = 4): parked circuits, largest P(|1>) in any branch at any wait {worst_parked:.2e}; "
    f"unparked twins {worst_unparked:.3f}")

# the parked n = 4 circuits against the weekend's C pk circuits (BC1)
man, raw, circs, cells = load_job(f"{WK}/BC/job1")
pk = {cells[p["cell"]]["name"][3:]: circs[i] for i, p in enumerate(man["pubs"]) if cells[p["cell"]]["role"] == "user"}
eq = sum(1 for j in range(16) if items[f"ipe4_{j}"]["circ"] == pk[f"pk4_{j}"])
ops_eq = sum(1 for j in range(16) if [(x.operation.name, tuple(items[f"ipe4_{j}"]["circ"].find_bit(q).index
                                                               for q in x.qubits))
                                      for x in items[f"ipe4_{j}"]["circ"].data] ==
             [(x.operation.name, tuple(pk[f"pk4_{j}"].find_bit(q).index for q in x.qubits)) for x in pk[f"pk4_{j}"].data])
say(f"parked n = 4 against the weekend's C pk (BC1): {eq} of 16 equal circuits; {ops_eq} of 16 with the same "
    f"instruction sequence (names and qubits)")
json.dump(dict(lines=lines), open(OUT, "w"), indent=1)
