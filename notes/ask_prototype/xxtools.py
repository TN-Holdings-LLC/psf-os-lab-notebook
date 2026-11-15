"""Compiler, simulator and estimate for the answerer, XX chain first (owner 2026-11-15 14:01 CET: estimates allowed,
labelled as estimates, with their basis).

compile  : the XX brickwork circuit built by gpu/ffxx91.py (the path of the declared XX runs) on the newest device
           record of that device in the notebook: chain labels, CZ count, CZ depth of the compiled circuit, failed
           elements of the record. Deterministic; about 20 s.
ideal    : the noiseless <Z_i> by free fermions (gpu/ff_xx.py z_exact), exact at any size, no sampling.
estimate : the kept share r this circuit may have on that device, from the recorded XX runs on the same device only:
           every recorded series (date, run, size, angle) whose CZ depths bracket the asked depth gives r at that
           depth by straight-line interpolation of ln r; the estimate is the range over the series, same size first.
           No extrapolation beyond the recorded depths or sizes; the rest (shape error) is not estimated.
backtest : each recorded XX result estimated from the other series only (its own series left out), against what it
           was; prints how often the recorded r fell in the range and how often the side of 0.293 was right.
usage: python notes/ask_prototype/xxtools.py backtest"""
import glob
import json
import math
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "gpu"))
LINE = 1 - 2 ** -0.5
THETA = {"π/4": 0.7853981633974483, "π/2": 1.5707963267948966}


# ---------------------------------------------------------------- device records
def newest_record(device):
    best = None
    for f in glob.glob(os.path.join(ROOT, "results", "**", "device.json"), recursive=True):
        try:
            d = json.load(open(f))
        except (OSError, ValueError):
            continue
        if d.get("name") != device or d.get("fake"):
            continue
        t = d.get("source", {}).get("fetched", "")
        if best is None or t > best[0]:
            best = (t, f, d)
    return best


# ---------------------------------------------------------------- compile
def compile_xx(device, n, angle, steps):
    rec = newest_record(device)
    if rec is None:
        return None, f"{device} の装置記録がノートブックにない"
    fetched, path, d = rec
    import psf_os
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([os.path.dirname(os.path.dirname(psf_os.__file__)), ROOT,
                                                       os.path.join(ROOT, "gpu")]))
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "job")
        r = subprocess.run([sys.executable, os.path.join(ROOT, "gpu", "ffxx91.py"), os.path.dirname(path), out,
                            os.path.join(tmp, "ans.json"), "--n", str(n), "--thetas", repr(THETA[angle]),
                            "--steps", str(steps)], capture_output=True, text=True, env=env, cwd=ROOT)
        if r.returncode != 0:
            last = (r.stderr.strip() or r.stdout.strip()).splitlines()[-1:] or ["?"]
            return None, f"置けなかった（{last[0][:200]}）"
        b = json.load(open(os.path.join(out, "build.json")))
        from qiskit import qpy
        m = json.load(open(os.path.join(out, "job", "manifest.json")))
        cs = qpy.load(open(os.path.join(out, "job", "circuits.qpy"), "rb"))
        user = [k for k, c in enumerate(m["cells"]) if c["role"] == "user"][0]
        start = sum(c["points"] for c in m["cells"][:user])
        circ = cs[start]
        depth = circ.depth(filter_function=lambda x: x.operation.name == "cz")
        labels = b["chains"][str(n)]["labels"]
    return dict(device=device, record=os.path.relpath(path, ROOT), fetched=fetched,
                calibration=d.get("source", {}).get("calibration_time"), failed_qubits=d.get("failed_qubits", []),
                failed_couplers=d.get("failed_couplers", []), labels=labels, cz=sum(b["cz"].values()),
                cz_depth=depth, model_seconds=b.get("qpu_seconds_model")), None


# ---------------------------------------------------------------- ideal values
def ideal_xx(n, angle, steps):
    import ff_xx as F
    z = [float(x) for x in F.z_exact(n, steps, THETA[angle])]
    return dict(z=z, mean_square=sum(x * x for x in z) / n, mean=sum(z) / n)


# ---------------------------------------------------------------- estimate from the records
def xx_series(rows, device):
    """{(date, run, qubits, angle): [(layers, r), ...]} of the recorded XX results on one device."""
    out = {}
    for r in rows:
        if r["family"] != "XX chain" or r["device"] != device or r["r"] is None or r["r"] <= 0:
            continue
        out.setdefault((r["date"], r["run"], r["qubits"], r["angle"]), []).append((r["layers"], r["r"]))
    return {k: sorted(v) for k, v in out.items()}


def at_depth(points, layers):
    """r at `layers` by straight-line interpolation of ln r between the bracketing recorded depths, or None."""
    for (l0, r0), (l1, r1) in zip(points, points[1:]):
        if l0 <= layers <= l1:
            if l0 == l1:
                return r0
            w = (layers - l0) / (l1 - l0)
            return math.exp((1 - w) * math.log(r0) + w * math.log(r1))
    for l0, r0 in points:
        if l0 == layers:
            return r0
    return None


def estimate_xx(rows, device, n, angle, layers, leave_out=None):
    ser = {k: v for k, v in xx_series(rows, device).items() if k != leave_out}
    if not ser:
        return None, f"{device} の XX 鎖の記録がない"
    sizes = sorted({k[2] for k in ser})
    vals = {k: at_depth(v, layers) for k, v in ser.items()}
    vals = {k: x for k, x in vals.items() if x is not None}
    if not vals:
        depths = sorted({l for v in ser.values() for l, _ in v})
        return None, f"記録の深さの外（{device} の XX 鎖の記録は CZ {depths[0]}〜{depths[-1]} 層）"
    same = {k: x for k, x in vals.items() if k[2] == n}
    use, basis = (same, "同じ大きさ") if same else (vals, f"別の大きさ（記録は {'/'.join(map(str, sizes))} 量子ビット）")
    lo, hi = min(use.values()), max(use.values())
    side = "読める側" if lo >= LINE else "読めない側" if hi < LINE else "0.293 をまたぐ"
    return dict(lo=lo, hi=hi, side=side, basis=basis, series=sorted(use), n_series=len(use),
                same_angle=sorted(k for k in use if k[3] == angle),
                beyond_size=(n > max(sizes)) or (n < min(sizes))), None


def backtest(rows):
    xx = [r for r in rows if r["family"] == "XX chain" and r["device"] in ("ibm_fez", "ibm_marrakesh")]
    n_est = in_range = side_ok = no_est = 0
    for r in xx:
        key = (r["date"], r["run"], r["qubits"], r["angle"])
        e, why = estimate_xx(rows, r["device"], r["qubits"], r["angle"], r["layers"], leave_out=key)
        if e is None:
            no_est += 1
            continue
        n_est += 1
        in_range += e["lo"] - 1e-9 <= r["r"] <= e["hi"] + 1e-9
        if e["side"] != "0.293 をまたぐ":
            side_ok += (e["side"] == "読める側") == bool(r["reads"])
    sided = sum(1 for r in xx if (lambda e: e and e["side"] != "0.293 をまたぐ")(
        estimate_xx(rows, r["device"], r["qubits"], r["angle"], r["layers"],
                    leave_out=(r["date"], r["run"], r["qubits"], r["angle"]))[0]))
    return dict(results=len(xx), estimated=n_est, no_estimate=no_est, in_range=in_range, sided=sided,
                side_right=side_ok)


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    os.chdir(ROOT)
    import ask
    if sys.argv[1:] == ["backtest"]:
        b = backtest(ask.build_index())
        print(f"XX results on fez and marrakesh: {b['results']}; estimated from the other series {b['estimated']} "
              f"(no estimate {b['no_estimate']}); recorded r inside the range {b['in_range']}; range on one side of "
              f"0.293 {b['sided']}, side right {b['side_right']}")
