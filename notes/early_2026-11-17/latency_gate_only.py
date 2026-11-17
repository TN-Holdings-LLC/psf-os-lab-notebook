# Extra cases for latency_desk.py (home VS Claude, 2026-11-17 evening; illustrative model, desk only): gate noise only
# (no idle decay, T1 = 1e3 s, latency 0) at CZ 0.3 % and 1 %, 16000 shots, scored by the declared T4 scorer.
# usage (from the notebook root, PYTHONPATH as latency_desk.py): python notes/early_2026-11-17/latency_gate_only.py
import sys, json, os
sys.path.insert(0, "notes/early_2026-11-17")
import latency_desk as D
from concurrent.futures import ProcessPoolExecutor
def task(args):
    tag, k, p2 = args
    D.P2Q = p2
    from qiskit import qpy
    c = qpy.load(open(os.path.join(D.JOBS[tag], "job", "circuits.qpy"), "rb"))[k]
    return tag, k, p2, D.run_circuit(c, 16000, 0.0, 1e3, noise=True, seed=500 + k)
if __name__ == "__main__":
    pubs = {t: D.user_pubs(t) for t in D.JOBS}
    tasks = [(t, k, p2) for p2 in (0.003, 0.01) for t in D.JOBS for k, _ in pubs[t]]
    res = {}
    with ProcessPoolExecutor(10) as ex:
        for t, k, p2, cnt in ex.map(task, tasks):
            res.setdefault(p2, {})[(t, k)] = cnt
    out = {}
    for p2, cells in sorted(res.items()):
        t2, t4, s2, s4 = D.write_and_score("/tmp/latwork_gate", cells, 0.0, 1e3, True)
        out[f"gate only, CZ {p2}"] = dict(T2=t2, T4=t4)
        print(f"== gate only (no idle decay), CZ {p2}"); print(s4)
    json.dump(out, open("notes/early_2026-11-17/latency_gate_only.json", "w"), indent=1, default=str)
