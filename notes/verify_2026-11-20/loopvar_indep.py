"""Independent recount of results/loopvar-night-2026-11-20 (home VS): qiskit / aer / numpy only, no psf-os and no
notebook scorer. exact = sin^2(arctan(tan^2 1.1))^L (derived here); the right value of each output bit from noiseless
Aer sampling of the circuit itself; g = |P0 - exact| - |P - exact|; definitions of the pooled tests as declared."""
import json
import math
import sys

import numpy as np
from qiskit import qpy
from qiskit_aer import AerSimulator

R = sys.argv[1]
JOBS = ("V1", "V2", "V3")
EXACT = {L: math.sin(math.atan(math.tan(1.1) ** 2)) ** (2 * L) for L in (1, 2, 3)}


def chi2_sf(x, k):
    """Survival function of the chi-square law with k degrees of freedom (series, no scipy)."""
    if k % 2 == 0:
        return math.exp(-x / 2) * sum((x / 2) ** i / math.factorial(i) for i in range(k // 2))
    # odd k: P(k/2, x/2) by the lower incomplete gamma series
    a, z = k / 2, x / 2
    term = s = 1 / a
    n = 1
    while term > 1e-17 * s:
        term *= z / (a + n)
        s += term
        n += 1
    return 1 - math.exp(-z + a * math.log(z) - math.lgamma(a)) * s


sim = AerSimulator()
right_of = {}
data = {}
for job in JOBS:
    man = json.load(open(f"{R}/{job}/job/manifest.json"))
    raw = json.load(open(f"{R}/{job}/job/raw_counts.json"))
    circs = qpy.load(open(f"{R}/{job}/job/circuits.qpy", "rb"))
    cells = {c["cell"]: c["name"] for c in man["cells"]}
    pub_of = {cells[p["cell"]]: i for i, p in enumerate(man["pubs"]) if p["point"] == 0}
    counts = {row["pub"]: row["counts"] for row in raw["rows"]}
    tot = {sum(c.values()) for c in counts.values()}
    print(job, "circuits", len(circs), "rows", len(counts), "shots per row", tot, "manifest shots", man["shots"])
    for L in (1, 2, 3):
        for cp in "ab":
            for kind in ("p0", "x"):
                name = f"ff_{kind}{L}{cp}"
                card = json.load(open(f"{R}/{job}/runs/{name}.json"))
                ob = card["rus"]["out_bit"]
                if name not in right_of:
                    res = sim.run(circs[pub_of[name]], shots=200_000, seed_simulator=5).result().get_counts()
                    p1 = sum(n for k, n in res.items() if k[::-1][ob] == "1") / 200_000
                    right_of[name] = (1 if p1 > 0.5 else 0, max(p1, 1 - p1), card["rus"]["m"], card["chain"])
                rv = right_of[name][0]
                cnt = counts[pub_of[name]]
                N = sum(cnt.values())
                data[(job, L, cp, kind)] = (sum(n for k, n in cnt.items() if int(k[::-1][ob]) == rv) / N, N)
print("right value / noiseless / m / qubits:", {k: (v[0], round(v[1], 4), v[2], v[3]) for k, v in right_of.items()
                                               if k.endswith("a")})

out = {}
chi_copies = 0.0
chi_jobs_total = 0.0
for L in (1, 2, 3):
    ex = EXACT[L]
    g, se = {}, {}
    for job in JOBS:
        for cp in "ab":
            (p0, n0), (p, n) = data[(job, L, cp, "p0")], data[(job, L, cp, "x")]
            g[(job, cp)] = abs(p0 - ex) - abs(p - ex)
            se[(job, cp)] = math.sqrt(p0 * (1 - p0) / n0 + p * (1 - p) / n)
    gj = {j: (g[(j, "a")] + g[(j, "b")]) / 2 for j in JOBS}
    sej = {j: math.sqrt(se[(j, "a")] ** 2 + se[(j, "b")] ** 2) / 2 for j in JOBS}
    lines = [f"L {L} (exact {ex:.6f}): g per job " + ", ".join(f"{j} {gj[j]:+.4f} (SE {sej[j]:.4f})" for j in JOBS)]
    within = []
    for j in JOBS:
        d = g[(j, "a")] - g[(j, "b")]
        s = math.sqrt(se[(j, "a")] ** 2 + se[(j, "b")] ** 2)
        chi_copies += (d / s) ** 2
        within.append(f"{j} {d:+.4f} (2 SE {2*s:.4f}) {'MOVES' if abs(d) >= 2*s else 'SAME WITHIN ERROR'}")
    between = []
    for x, y in (("V1", "V2"), ("V2", "V3"), ("V1", "V3")):
        d = gj[x] - gj[y]
        s = math.sqrt(sej[x] ** 2 + sej[y] ** 2)
        between.append(f"{x}-{y} {d:+.4f} (2 SE {2*s:.4f}) {'MOVES' if abs(d) >= 2*s else 'SAME WITHIN ERROR'}")
    w = {j: 1 / sej[j] ** 2 for j in JOBS}
    gbar = sum(w[j] * gj[j] for j in JOBS) / sum(w.values())
    chi = sum((gj[j] - gbar) ** 2 / sej[j] ** 2 for j in JOBS)
    chi_jobs_total += chi
    p = math.exp(-chi / 2)
    sb2 = float(np.var([gj[j] for j in JOBS], ddof=1)) - float(np.mean([sej[j] ** 2 for j in JOBS]))
    lines.append("   within: " + "; ".join(within))
    lines.append("   between: " + "; ".join(between))
    lines.append(f"   three jobs: chi2 {chi:.2f} (2 df), p {p:.3f} -> {'DRIFTS' if p < 0.05 else 'SHOT NOISE ONLY'}; "
                 f"excess SD {math.sqrt(sb2) if sb2 > 0 else 0:.4f} (variance {sb2:+.6f})")
    lines.append("   shares P0 / P1: " + "; ".join(f"{j}{cp} {data[(j, L, cp, 'p0')][0]:.4f} / "
                                                   f"{data[(j, L, cp, 'x')][0]:.4f}" for j in JOBS for cp in "ab"))
    print("\n".join(lines))
    out[L] = dict(gj=gj, sej=sej, chi2=chi, p=p, sb2=sb2)
x = chi_jobs_total
print(f"between jobs pooled over L: chi2 {x:.2f} (6 df), p {chi2_sf(x, 6):.3f} "
      f"(declared closed form {math.exp(-x/2)*(1+x/2+x*x/8):.3f})")
pc = chi2_sf(chi_copies, 9)
print(f"copies pooled (LV-1): chi2 {chi_copies:.2f} (9 df), p {pc:.3f} -> {'MOVES' if pc < 0.05 else 'SAME WITHIN ERROR'}")
json.dump(dict(per_L={str(k): v for k, v in out.items()}, chi_copies=chi_copies, p_copies=pc, chi_jobs=x),
          open(sys.argv[2], "w"), indent=1)
