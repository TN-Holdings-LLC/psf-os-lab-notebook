"""The loopvar tool's chi2 tail (chi2_sf, gpu/loopvar_night.py at 74f479cc) against scipy.stats.chi2.sf
(workplace VS, 2026-11-20; author The Architect). The two functions are lifted from the tool's source by ast (the tool
is not imported, so nothing else of it runs).

  python chi2_vs_scipy.py NOTEBOOK
"""
import ast
import math
import os
import sys

import numpy as np
from scipy.stats import chi2


def lift(path, names):
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    ns = {"math": math}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            exec(compile(ast.Module(body=[node], type_ignores=[]), path, "exec"), ns)
    return ns


def main():
    ns = lift(os.path.join(sys.argv[1], "gpu", "loopvar_night.py"), {"chi2_sf_even", "chi2_sf"})
    f = ns["chi2_sf"]
    xs = np.concatenate([np.linspace(0.0, 1.0, 21), np.linspace(1.0, 60.0, 237)])
    worst_abs, worst_rel, where = 0.0, 0.0, None
    for k in range(1, 13):
        for x in xs:
            a, b = f(float(x), k), float(chi2.sf(x, k))
            da = abs(a - b)
            dr = da / b if b > 1e-300 else 0.0
            if da > worst_abs:
                worst_abs = da
            if dr > worst_rel:
                worst_rel, where = dr, (k, float(x), a, b)
    print(f"k = 1..12, x in [0, 60] ({len(xs)} points each): largest |difference| {worst_abs:.2e}, "
          f"largest relative {worst_rel:.2e} at k {where[0]}, x {where[1]:.2f}")
    for k, x in ((9, 16.919), (9, 9.0), (9, 2.0), (2, 5.991), (6, 12.592), (1, 3.841), (3, 7.815)):
        print(f"  k {k:2d} x {x:7.3f}: tool {f(x, k):.8f}  scipy {chi2.sf(x, k):.8f}")


if __name__ == "__main__":
    main()
