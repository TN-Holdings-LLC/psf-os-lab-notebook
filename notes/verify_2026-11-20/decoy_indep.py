"""Independent recount of results/decoy-night-2026-11-20 (home VS): qiskit / aer / numpy only, no psf-os and no
notebook scorer. The right output value and the reference v come from noiseless Aer sampling of the singles themselves
(4,000,000 shots); the device numbers from job/raw_counts.json; the reading table rows as declared, in their order."""
import json
import math
import sys

from qiskit import qpy
from qiskit_aer import AerSimulator

R = sys.argv[1]
man = json.load(open(f"{R}/job/manifest.json"))
raw = json.load(open(f"{R}/job/raw_counts.json"))
circs = qpy.load(open(f"{R}/job/circuits.qpy", "rb"))
N = man["shots"]
cells = {c["cell"]: c["name"] for c in man["cells"]}
pub_of = {cells[p["cell"]]: i for i, p in enumerate(man["pubs"]) if p["point"] == 0}
counts = {row["pub"]: row["counts"] for row in raw["rows"]}
print("circuits", len(circs), "pubs", len(man["pubs"]), "rows", len(raw["rows"]), "shots", N,
      "row totals", sorted({sum(c.values()) for c in counts.values()}))


def share(cnt, bit, val):
    tot = sum(cnt.values())
    return sum(n for k, n in cnt.items() if int(k[::-1][bit]) == val) / tot


def noiseless_p0(name):
    res = AerSimulator().run(circs[pub_of[name]], shots=4_000_000, seed_simulator=11).result().get_counts()
    return share(res, 4, 0)


v = noiseless_p0("ff_sa")
voff = noiseless_p0("ff_sz_off")
right = 0 if v > 0.5 else 1
assert right == 0 and voff > 0.5
print(f"noiseless (read flipped, right value 0): rd2 ff {v:.4f}, off {voff:.4f}")


def measured(name):
    qc = circs[pub_of[name]]
    return sorted({qc.find_bit(q).index for i in qc.data if i.operation.name == "measure" for q in i.qubits})


single = {s: share(counts[pub_of[f"ff_{s}"]], 4, 0) for s in ("sa", "sb", "sz")}
sz_off = share(counts[pub_of["ff_sz_off"]], 4, 0)
print("singles", {k: round(x, 4) for k, x in single.items()}, "sz off", round(sz_off, 4))


def word(d, se2):
    return "PACKED KEEPS LESS" if d <= -se2 else ("PACKED KEEPS MORE" if d >= se2 else "SAME WITHIN ERROR")


ref_of_qubits = {(0, 1, 2, 3): "sa", (5, 6, 7, 8): "sb", (11, 12, 13, 14): "sz"}
out, words = {}, {}
for bun in ("D0", "D1", "D2"):
    card = json.load(open(f"{R}/runs/ff_{bun}.json"))
    ds = []
    for it, c in sorted(card["bundle"].items()):
        ref = ref_of_qubits[tuple(c["qubits"])]
        p = share(counts[pub_of[f"ff_{bun}"]], c["bit_offset"] + 4, 0)
        if c["conditionals"] == 0:            # the fixed Z against sz's off arm, beside
            s, vv = sz_off, voff
        else:
            s, vv = single[ref], v
        d = abs(s - vv) - abs(p - vv)
        se = math.sqrt(s * (1 - s) / N + p * (1 - p) / N)
        w = word(d, 2 * se) if c["conditionals"] else "beside"
        words[it] = w
        if c["conditionals"]:
            ds.append((d, se))
        out[it] = dict(qubits=c["qubits"], bits=[c["bit_offset"], c["bit_offset"] + 4], alone=s, packed=p, d=d,
                       two_se=2 * se, word=w)
        print(f"  {it} [{'fixed' if not c['conditionals'] else 'cond'}] qubits {c['qubits']} bits "
              f"{c['bit_offset']}-{c['bit_offset']+4}: alone {s:.4f} packed {p:.4f} d {d:+.4f} (2 SE {2*se:.4f}) {w}")
    md = sum(d for d, _ in ds) / len(ds)
    mse = math.sqrt(sum(se * se for _, se in ds)) / len(ds)
    out[bun] = dict(mean_d=md, two_se=2 * mse, word=word(md, 2 * mse))
    print(f"{bun}: mean d {md:+.4f} (2 SE {2*mse:.4f}) {out[bun]['word']}")

loses = {k: words[k] == "PACKED KEEPS LESS" for k in ("d0a", "d0b", "d1a", "d1b", "d2a")}
if not loses["d0a"] or loses["d0b"]:
    row = 4
elif loses["d1a"] and loses["d2a"]:
    row = 2
elif loses["d1a"] and not loses["d2a"]:
    row = 6
elif not loses["d1a"] and loses["d1b"]:
    row = 3
elif loses["d2a"]:
    row = 1
else:
    row = 5
print("reading table row", row)
print("measured qubits:", {n: measured(n) for n in ("ff_D0", "ff_D1", "ff_D2", "ff_sa", "ff_sb", "ff_sz")})
json.dump(dict(items=out, row=row), open(sys.argv[2], "w"), indent=1)
