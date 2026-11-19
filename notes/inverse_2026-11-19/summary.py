"""Table of inverse_desk.py's output, with the shot count the inverse would need at one shot per sampled circuit
(the efficient split): var per shot = gamma_total^2 / (1 - 2 q)^2 - <Z>^2, shots = var * (2 / 0.02)^2.

  python summary.py inverse_n8.json > summary_n8.md
"""
import json
import sys

d = json.load(open(sys.argv[1]))
q = d["config"]["q"]
print("| L | cz | truth | exact | raw (2 SE) | mirror rescale (2 SE) | inverse (2 SE) | gamma^2 | shots for 2 SE 0.02, "
      "one shot per circuit |")
print("|---|---|---|---|---|---|---|---|---|")
for r in d["rows"]:
    w, m, i = r["raw"], r["mirror"], r["inverse"]

    def f(x):
        if x.get("est") is None:
            return "n/a"
        flag = "" if abs(x["err"]) <= x["two_se"] else " **off**"
        return f"{x['est']:+.3f} ({x['two_se']:.3f}){flag}"
    var = i["overhead"] / (1 - 2 * q) ** 2 - r["exact"] ** 2
    print(f"| {r['L']} | {r['cz']} | {r['truth']} | {r['exact']:+.3f} | {f(w)} | {f(m)} | {f(i)} | "
          f"{i['overhead']:.1f} | {var * 1e4:.1e} |")
print()
print("**off**: the estimate misses the exact value by more than its 2 SE.")
