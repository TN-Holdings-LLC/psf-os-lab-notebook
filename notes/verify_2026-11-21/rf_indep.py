"""Independent recount of results/rus-fence-night-2026-11-21 (home VS): qiskit / aer / numpy only, no psf-os and no
notebook scorer. RUS items: P of the output bit (named in the record) read as declared (P2 flipped), exact =
sin^2(arctan(tan^2 1.1))^L derived here; g of the fence (F - D) and parking (M - F); M against D beside. Controls:
success bits from the record, right values from noiseless Aer of the recorded circuit. Sent: circuits, shots, copies,
the three forms in one job, M's extra X per qubit against F (compiled), the device rule from queue.json."""
import json
import math
import sys
from collections import Counter, defaultdict

from qiskit import qpy
from qiskit_aer import AerSimulator

R, OUT = sys.argv[1], sys.argv[2]
EX = {L: math.sin(math.atan(math.tan(1.1) ** 2)) ** (2 * L) for L in (1, 2, 3)}
PRESC = {"p0l3": "P0", "nfl3m3": "NF", "p2l3m3": "P2", "p3l3": "P3"}
sim = AerSimulator()
lines = []
say = lambda s: (print(s), lines.append(s))


def bit(k, i):
    return int(k.replace(" ", "")[-1 - i])


def word(d, se):
    return "KEEPS MORE" if d >= 2 * se and d > 0 else "KEEPS LESS" if d <= -2 * se and d < 0 else "SAME WITHIN ERROR"


jd = f"{R}/rf/job0"
man = json.load(open(f"{jd}/job/manifest.json"))
raw = json.load(open(f"{jd}/job/raw_counts.json"))
circs = qpy.load(open(f"{jd}/job/circuits.qpy", "rb"))
cells = {c["cell"]: c for c in man["cells"]}
counts = {r["pub"]: r["counts"] for r in raw["rows"]}
part = json.load(open(f"{jd}/part.json"))
by = {}
roles = Counter()
shots = set()
for i, p in enumerate(man["pubs"]):
    c = cells[p["cell"]]
    roles[c["role"]] += 1
    shots.add(sum(counts[i].values()))
    if c["role"] == "user":
        by[c["name"][3:]] = (i, json.load(open(f"{jd}/runs/{c['name']}.json")))
say(f"sent: {len(man['pubs'])} circuits, roles {dict(roles)}, shots {sorted(shots)}; off/floor cells "
    f"{[c['name'] for c in man['cells'] if c['name'].endswith(('_off', '_floor'))] or 'none'}; psf_os_build "
    f"{man.get('psf_os_build')}")

# ---- RUS items
res = {}
for key, presc in PRESC.items():
    copies = {k: sorted(t for t in by if t[:-1] == key + k) for k in "DFM"}
    n = {k: len(v) for k, v in copies.items()}
    P = {}
    for k in "DFM":
        ok = N = 0
        for t in copies[k]:
            i, rec = by[t]
            ob = rec["rus"]["out_bit"]
            want = 0 if presc == "P2" else 1
            ok += sum(v for kk, v in counts[i].items() if bit(kk, ob) == want)
            N += sum(counts[i].values())
        P[k] = (ok / N, N)
    L = by[copies["D"][0]][1]["rus"]["L"]
    ex = EX[L]

    def g(x, y):
        (px, nx), (py, ny) = P[x], P[y]
        d = abs(py - ex) - abs(px - ex)
        se = math.sqrt(px * (1 - px) / nx + py * (1 - py) / ny)
        return d, se
    fd, fs = g("F", "D")
    pd, ps = g("M", "F")
    md, ms = g("M", "D")
    res[key] = (word(fd, fs), word(pd, ps))
    say(f"{key} copies {n}: P D {P['D'][0]:.4f} F {P['F'][0]:.4f} M {P['M'][0]:.4f} (exact {ex:.4f}); fence F - D "
        f"{fd:+.4f} (2 SE {2 * fs:.4f}) {word(fd, fs)}; park M - F {pd:+.4f} (2 SE {2 * ps:.4f}) {word(pd, ps)}; "
        f"beside M - D {md:+.4f}")
    # M's extra X per physical qubit against F (copy a), compiled; against part.json's list
    def gates(c):
        cnt = defaultdict(Counter)
        for ins in c.data:
            nm = ins.operation.name
            for q in ins.qubits:
                cnt[c.find_bit(q).index][nm] += 1
        return cnt
    gf, gm = gates(circs[by[f"{key}Fa"][0]]), gates(circs[by[f"{key}Ma"][0]])
    chain = by[f"{key}Ma"][1]["chain"]
    extra = {q: gm[q]["x"] - gf[q]["x"] for q in set(gm) | set(gf) if gm[q]["x"] != gf[q]["x"]}
    listed = part["majority"][key]["majority_x"]
    lq = sorted({chain[x["qubit"]] for x in listed})
    say(f"   M's X: extra x per physical qubit {dict(sorted(extra.items()))}; part.json lists {len(listed)} "
        f"qubit-waits on physical {lq}; same qubits {sorted(extra) == lq}; each extra count even "
        f"{all(v % 2 == 0 and v > 0 for v in extra.values())}; at most 2 per listed qubit-wait "
        f"{all(extra.get(q, 0) <= 2 * sum(1 for x in listed if chain[x['qubit']] == q) for q in lq)}")

# ---- the reading row and the next step
p0f, nfp = res["p0l3"][0], res["nfl3m3"][1]
ROWS = {("KEEPS LESS", "KEEPS MORE"): 1, ("KEEPS MORE", "SAME WITHIN ERROR"): 2,
        ("SAME WITHIN ERROR", "KEEPS LESS"): 3, ("KEEPS MORE", "KEEPS MORE"): 4, ("KEEPS MORE", "KEEPS LESS"): 5,
        ("SAME WITHIN ERROR", "KEEPS MORE"): 6, ("KEEPS LESS", "SAME WITHIN ERROR"): 7,
        ("KEEPS LESS", "KEEPS LESS"): 8, ("SAME WITHIN ERROR", "SAME WITHIN ERROR"): 9}
say(f"reading row: P0 fence {p0f}, NF parking {nfp} -> row {ROWS[(p0f, nfp)]}")


# ---- controls
def right_share(tags):
    ok = N = 0
    for t in tags:
        i, rec = by[t]
        sb = sorted(int(b) for b in rec["success"])
        ideal = sim.run(circs[i], shots=20000, seed_simulator=3).result().get_counts()
        right = {}
        for b in sb:
            p1 = sum(v for k, v in ideal.items() if bit(k, b) == 1) / 20000
            assert p1 in (0.0, 1.0)
            right[b] = int(p1)
        assert right == {int(b): v for b, v in rec["success"].items()}, t
        ok += sum(v for k, v in counts[i].items() if all(bit(k, b) == right[b] for b in sb))
        N += sum(counts[i].values())
    return ok / N, N


ipk = sorted(t for t in by if t.startswith("ipk4_"))
(pk, nk), (pu, nu) = right_share(ipk), right_share([t.replace("ipk", "ipu") for t in ipk])
se = math.sqrt(pk * (1 - pk) / nk + pu * (1 - pu) / nu)
gate = word(pk - pu, se)
say(f"control IPE {ipk}: parked {pk:.4f} - unparked {pu:.4f} = {pk - pu:+.4f} (2 SE {2 * se:.4f}) {gate}; gate "
    f"{'open' if gate == 'KEEPS MORE' else 'closed: no next step taken'}")
rep = {f: right_share([f"{f.lower()}_{e}" for e in ("n", "0", "1", "2")]) for f in ("F10", "F6P", "F6")}
for name, (x, y) in (("footprint F6P - F10", ("F6P", "F10")), ("CZ F6 - F6P", ("F6", "F6P"))):
    (px, nx), (py, ny) = rep[x], rep[y]
    s = math.sqrt(px * (1 - px) / nx + py * (1 - py) / ny)
    say(f"repetition code {name}: {px - py:+.4f} (2 SE {2 * s:.4f}) {word(px - py, s)}")
p6, n6 = rep["F6"]
s6 = math.sqrt(p6 * (1 - p6) / n6)
say(f"repetition code: F10 {rep['F10'][0]:.4f}, F6P {rep['F6P'][0]:.4f}, F6 {p6:.4f} (2 SE {2 * s6:.4f}) -> "
    f"{'BEYOND THE CEILING' if p6 >= 0.875 + 2 * s6 else 'NOT BEYOND'}")

# ---- the device rule and the charge
q = json.load(open(f"{R}/fetch_in/queue.json"))
cand = [d for d in q["chosen"] if d != "ibm_marrakesh"]
pick = min(cand, key=lambda d: (q["pending"][d], cand.index(d)))
u = raw["metrics"]["usage"]
say(f"device rule: pending {q['pending']}, order {q['chosen']} -> {pick}; the job ran on {man['fetch']['backend']}; "
    f"charged {u['qpu_charge_time_seconds']} s, {u['value']:.4f} RU, model {man['qpu_seconds_model']}")
json.dump(dict(lines=lines), open(OUT, "w"), indent=1)
