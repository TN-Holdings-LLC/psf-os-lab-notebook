"""Independent recount of results/likely-park-night-2026-11-22 (home VS): qiskit / aer / numpy only, no psf-os and no
notebook scorer. RUS items: P of the output bit named in the record (read as declared), exact derived here, the
noiseless value of each compiled form by noiseless Aer sampling (400000 shots), L - D as g with 2 SE, OVERSHOOT
(P above noiseless + 2 SE); the rule for the default; the IPE control from noiseless right values. Sent: circuits,
shots, copies, psf_os_build, L's parked waits fenced together with a measured qubit, the device rule; the charge."""
import json
import math
import sys
from collections import Counter

from qiskit import qpy
from qiskit_aer import AerSimulator

R, OUT = sys.argv[1], sys.argv[2]
EX = {L: math.sin(math.atan(math.tan(1.1) ** 2)) ** (2 * L) for L in (1, 2, 3)}
ITEMS = ("nfl3m3", "p0l3", "p3l3")
sim = AerSimulator()
lines = []
say = lambda s: (print(s), lines.append(s))


def bit(k, i):
    return int(k.replace(" ", "")[-1 - i])


def word(d, se):
    return "KEEPS MORE" if d >= 2 * se and d > 0 else "KEEPS LESS" if d <= -2 * se and d < 0 else "SAME WITHIN ERROR"


jd = f"{R}/lp/job0"
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
say(f"sent: {len(man['pubs'])} circuits, roles {dict(roles)}, shots {sorted(shots)}; psf_os_build version "
    f"{b.get('version')}, park {b.get('park')}, park_likely {len(b.get('park_likely') or [])} names, declared "
    f"{b.get('declared')}")
l_items = sorted(t for t in by if t[:-1] in {f"{k}L" for k in ITEMS})
say(f"park_likely names exactly the L items: {sorted(b.get('park_likely') or []) == l_items} ({len(l_items)})")

words, excluded = {}, []
for key in ITEMS:
    tags = {k: sorted(t for t in by if t[:-1] == key + k) for k in "DL"}
    P, NL = {}, {}
    for k in "DL":
        ok = N = 0
        for t in tags[k]:
            i, rec = by[t]
            ob = rec["rus"]["out_bit"]
            ok += sum(v for kk, v in counts[i].items() if bit(kk, ob) == 1)        # NF, P0, P3 read 1 as 1
            N += sum(counts[i].values())
        P[k] = (ok / N, N)
        i, rec = by[tags[k][0]]
        ideal = sim.run(circs[i], shots=400000, seed_simulator=5).result().get_counts()
        NL[k] = sum(v for kk, v in ideal.items() if bit(kk, rec["rus"]["out_bit"]) == 1) / 400000
    ex = EX[by[tags["D"][0]][1]["rus"]["L"]]
    (pd, nd), (pl, nl) = P["D"], P["L"]
    g = abs(pd - ex) - abs(pl - ex)
    se = math.sqrt(pd * (1 - pd) / nd + pl * (1 - pl) / nl)
    words[key] = word(g, se)
    over = {k: P[k][0] > NL[k] + 2 * math.sqrt(P[k][0] * (1 - P[k][0]) / P[k][1]) for k in "DL"}
    if any(over.values()):
        excluded.append(key)
    say(f"{key} copies D {len(tags['D'])} L {len(tags['L'])}: P D {pd:.4f} L {pl:.4f} (exact {ex:.4f}; noiseless "
        f"by Aer D {NL['D']:.4f} L {NL['L']:.4f}); L - D {g:+.4f} (2 SE {2 * se:.4f}) {words[key]}; OVERSHOOT {over}")
    # L's parked waits fenced together with a measured qubit (copy a)
    i, rec = by[f"{key}La"]
    c = circs[i]
    meas = {c.find_bit(x.qubits[0]).index for x in c.data if x.operation.name == "measure"}
    bars = [{c.find_bit(q).index for q in x.qubits} for x in c.data if x.operation.name == "barrier"]
    parked = rec["park_likely"]["arms"]["ff"]["parked"]
    fenced = [sum(1 for s in bars if set(w["physical"]) <= s and (s - set(w["physical"])) & meas) for w in parked]
    say(f"   L's parked waits {len(parked)} on physical {sorted({q for w in parked for q in w['physical']})}; barriers "
        f"holding them with a measured qubit per wait {fenced} (>= 2 each: {all(f >= 2 for f in fenced)})")


def right_share(tags):
    ok = N = 0
    for t in tags:
        i, rec = by[t]
        sb = sorted(int(x) for x in rec["success"])
        ideal = sim.run(circs[i], shots=20000, seed_simulator=3).result().get_counts()
        right = {}
        for x in sb:
            p1 = sum(v for k, v in ideal.items() if bit(k, x) == 1) / 20000
            assert p1 in (0.0, 1.0)
            right[x] = int(p1)
        assert right == {int(x): v for x, v in rec["success"].items()}
        ok += sum(v for k, v in counts[i].items() if all(bit(k, x) == right[x] for x in sb))
        N += sum(counts[i].values())
    return ok / N, N


ipk = sorted(t for t in by if t.startswith("ipk4_"))
(pk, nk), (pu, nu) = right_share(ipk), right_share([t.replace("ipk", "ipu") for t in ipk])
se = math.sqrt(pk * (1 - pk) / nk + pu * (1 - pu) / nu)
gate = word(pk - pu, se)
say(f"IPE control: parked {pk:.4f} - unparked {pu:.4f} = {pk - pu:+.4f} (2 SE {2 * se:.4f}) {gate}")
counted = {k: w for k, w in words.items() if k not in excluded}
if gate != "KEEPS MORE":
    rule = "opt-in (gate closed)"
elif not counted:
    rule = "opt-in (no item counted)"
elif any(w == "KEEPS LESS" for w in counted.values()):
    rule = "opt-in (a counted item KEEPS LESS)"
elif any(w == "KEEPS MORE" for w in counted.values()):
    rule = "park_likely the default in 0.3.1"
else:
    rule = "opt-in (no counted item KEEPS MORE)"
say(f"counted {sorted(counted)}; the rule: {rule}")
q = json.load(open(f"{R}/fetch_in/queue.json"))
cand = [d for d in q["chosen"] if d != "ibm_marrakesh"]
pick = min(cand, key=lambda d: (q["pending"][d], cand.index(d)))
u = raw["metrics"]["usage"]
say(f"device rule: pending {q['pending']} -> {pick}; ran on {man['fetch']['backend']}; charged "
    f"{u['qpu_charge_time_seconds']} s, {u['value']:.4f} RU, model {man['qpu_seconds_model']}")
json.dump(dict(lines=lines), open(OUT, "w"), indent=1)
