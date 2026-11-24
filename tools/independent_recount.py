"""A second, independent re-count of a night's raw counts (workplace VS, 2026-11-24; home instruction "研究ノートの道具の
直し", 3). Generalised from the home VS's notes/verify_2026-11-23/ow_independent_check.py. It uses qiskit, numpy and
the night's record files only: no psf-os, no notebook scoring tool, and it does not read the qubit-to-clbit mapping
from build.json: every mapping comes from the measure instructions of the circuits as sent (build.json is only set
beside, to say whether it agrees).

The common part (any night with job folders):
  load_job(job_dir)   circuits.qpy or circuits.qpy.gz (sha256 against manifest["circuits_sha256"]), manifest,
                      raw_counts; per pub: its name (cell name, with "#point" for multi-point cells), its circuit,
                      its counts, its shots, and the measured physical qubit -> clbit map read from the circuit
  z_from_counts       per-qubit <Z> from the counts for given clbits
A night's scoring formula is a small function registered in SCORERS under the night's folder name; the first is
ohm-window-night-2026-11-23 (the same formulas as ow_independent_check.py). Past nights' reproduce.py is not changed.

  python tools/independent_recount.py results/NIGHT [--json OUT.json] [--compare REF.json] [--simulate]
  python tools/independent_recount.py --selftest
Exit code: 0 when every check of the common part holds (and, with --compare, every compared value is equal); 1 if not.
"""
import argparse
import gzip
import hashlib
import io
import json
import os
import sys

import numpy as np


# ------------------------------------------------------------------------------------------------ the common part
def measured(qc):
    """(physical qubit -> clbit) from the measure instructions, the count of gates after a qubit's measurement, the
    count of delays and the set of other operation names."""
    m, after, delays, ops, done = {}, 0, 0, set(), set()
    for ins in qc.data:
        name = ins.operation.name
        qs = [qc.find_bit(q).index for q in ins.qubits]
        if name == "measure":
            m[qs[0]] = qc.find_bit(ins.clbits[0]).index
            done.add(qs[0])
            continue
        if name == "barrier":
            continue
        if name == "delay":
            delays += 1
        if any(q in done for q in qs):
            after += 1
        ops.add(name)
    return m, after, delays, ops


def load_job(job_dir):
    """The job as sent and as returned: dict(manifest, raw, circuits, sha_ok, pubs=[dict(name, circuit, counts, shots,
    meas)])."""
    from qiskit import qpy
    man = json.load(open(os.path.join(job_dir, "manifest.json")))
    raw = json.load(open(os.path.join(job_dir, "raw_counts.json")))
    p = os.path.join(job_dir, "circuits.qpy")
    blob = gzip.open(p + ".gz").read() if os.path.exists(p + ".gz") else open(p, "rb").read()
    sha_ok = hashlib.sha256(blob).hexdigest() == man.get("circuits_sha256")
    circs = qpy.load(io.BytesIO(blob))
    cell_name = {c["cell"]: c["name"] for c in man["cells"]}
    npoints = {}
    for pb in man["pubs"]:
        npoints[pb["cell"]] = npoints.get(pb["cell"], 0) + 1
    rows = {r["pub"]: r["counts"] for r in raw["rows"]}
    pubs = []
    for i, pb in enumerate(man["pubs"]):
        nm = cell_name[pb["cell"]] + (f"#{pb['point']}" if npoints[pb["cell"]] > 1 else "")
        cnt = rows.get(i, {})
        pubs.append(dict(name=nm, circuit=circs[i], counts=cnt, shots=sum(cnt.values()), meas=measured(circs[i])[0]))
    return dict(manifest=man, raw=raw, circuits=circs, sha_ok=sha_ok, pubs=pubs)


def z_from_counts(counts, clbits):
    """<Z> per clbit (in the order given) from counts keyed by bit strings (clbit 0 rightmost; spaces ignored)."""
    tot = sum(counts.values())
    z = np.zeros(len(clbits))
    for key, c in counts.items():
        s = key.replace(" ", "")
        z += c * np.array([1 - 2 * int(s[-1 - k]) for k in clbits])
    return z / tot


def common_checks(job):
    man, pubs = job["manifest"], job["pubs"]
    shots = sorted({p["shots"] for p in pubs})
    return dict(circuits=len(pubs), circuits_match_manifest=len(pubs) == len(man["pubs"]),
                qpy_sha256_matches_manifest=job["sha_ok"], shots_manifest=man.get("shots"), shots_per_pub=shots,
                shots_as_manifest=shots == [man.get("shots")])


# ------------------------------------------------------------------------------------------------ night scorers
def score_ohm_window(night, job, simulate=False):
    """ohm-window-night-2026-11-23: M and W in the window per arm, t and form, their READS words, the twins (F - L),
    the order of the arms at t = 3, W(3)/W(1) beside, floor and mirror; as ow_independent_check.py, with the chain
    positions read from the F circuits' measure instructions (clbit k <-> chain position k)."""
    ARMS, TS, FORMS = ("A0", "A1", "A2"), (1, 3), ("L", "F")
    NAMES = [f"{p}{k:02d}" for k in range(7) for p in "sc"]
    A = json.load(open(os.path.join(night, "answers", "ohm_window_answers.json")))
    strs, pos_of = A["meta"]["strings"], A["meta"]["positions"]
    window = lambda t: list(range(20, 20 + 2 * t - 1))
    cone = lambda t: list(range(18, 22)) if t == 1 else list(range(14, 30))
    pubs = {p["name"]: p for p in job["pubs"]}
    out = {}
    # The chain from the records, not from build.json. The F circuits measure the 40 chain qubits (their clbit order
    # is not the chain order); on the device's working couplers those 40 qubits form one path, which fixes the order
    # up to its direction; the direction is the one under which the answers by chain position equal the answers by
    # physical label (both are record files).
    man = job["manifest"]
    coup = {tuple(sorted(c)) for c in man["device"]["couplers"]}
    bad = {tuple(sorted(c)) for c in man["device"].get("failed_couplers", [])}
    fset = set(pubs["p2d_A0_t1_F_s00"]["meas"])
    every_F_same = all(set(pubs[f"p2d_{a}_t{t}_F_{n}"]["meas"]) == fset for a in ARMS for t in TS for n in NAMES)
    path = _path_through(fset, coup - bad)
    AL = json.load(open(os.path.join(night, "answers", "ohm_window_answers_by_label.json")))
    chain, agree = None, []
    for cand in ([] if path is None else [path, path[::-1]]):
        apos = pos_of["t1_F"]
        ok = all(abs(A["z"][f"A0_t1_F_{n}"][apos.index(p)] - AL["z"][f"A0_t1_F_{n}"][str(cand[p])]) < 1e-9
                 for n in NAMES for p in range(40))
        agree.append(ok)
        if ok and chain is None:
            chain = cand
    bj = os.path.join(night, "ow", "build.json")
    out["chain_from_records"] = dict(every_F_circuit_measures_the_same_40=every_F_same, one_path_on_the_couplers=path
                                     is not None, directions_agreeing_with_the_answers=sum(agree),
                                     build_json_agrees=(json.load(open(bj))["chain"]["labels"] == chain)
                                     if os.path.exists(bj) and chain else None)
    if chain is None:
        raise SystemExit("independent_recount: the chain is not fixed by the records (no single path, or no direction "
                         "agrees with the answers)")
    out["chain_is_device_path"] = all(tuple(sorted(e)) in coup and tuple(sorted(e)) not in bad
                                      for e in zip(chain, chain[1:]))
    dev_z, ex_z, L_ok = {}, {}, True
    names_user = [f"p2d_{a}_t{t}_{f}_{n}" for a in ARMS for t in TS for f in FORMS for n in NAMES]
    for nm in names_user:
        _, a, tt, f, s = nm.split("_")
        t = int(tt[1:])
        pos = list(range(40)) if f == "F" else cone(t)
        phys = [chain[p] for p in pos]
        m = pubs[nm]["meas"]
        if sorted(m) != sorted(phys):
            L_ok = False
            continue
        apos = pos_of[f"t{t}_{f}"]
        ex_z[nm] = dict(zip(pos, [A["z"][nm[4:]][apos.index(p)] for p in pos]))
        dev_z[nm] = dict(zip(pos, z_from_counts(pubs[nm]["counts"], [m[q] for q in phys])))
    out["measured_on_the_declared_positions"] = L_ok
    if simulate:
        out["noise_free_vs_answers_worst"] = _simulate_against_answers(pubs, names_user, chain, cone, ex_z)

    def mw(nm, which):
        t, s = int(nm.split("_")[2][1:]), nm.split("_")[4]
        z = dev_z[nm] if which == "d" else ex_z[nm]
        return sum((1 - z[p]) / 2 for p in window(t)) - sum(int(strs[s][p]) for p in window(t))

    cells, twins, order, beside = {}, {}, {}, {}
    for a in ARMS:
        for t in TS:
            errs = {}
            for f in FORMS:
                tg = [f"p2d_{a}_t{t}_{f}_{n}" for n in NAMES]
                d = np.array([mw(x, "d") for x in tg])
                e = np.array([mw(x, "e") for x in tg])
                wd = np.array([(mw(f"p2d_{a}_t{t}_{f}_s{k:02d}", "d") - mw(f"p2d_{a}_t{t}_{f}_c{k:02d}", "d")) / 2
                               for k in range(7)])
                we = np.array([(mw(f"p2d_{a}_t{t}_{f}_s{k:02d}", "e") - mw(f"p2d_{a}_t{t}_{f}_c{k:02d}", "e")) / 2
                               for k in range(7)])
                rM = float(np.mean((d - e) ** 2) / np.mean(e ** 2))
                rW = float(np.mean((wd - we) ** 2) / np.mean(we ** 2))
                S = float(np.mean([mw(f"p2d_{a}_t{t}_{f}_s{k:02d}", "d") + mw(f"p2d_{a}_t{t}_{f}_c{k:02d}", "d")
                                   for k in range(7)]))
                Se = float(np.mean([mw(f"p2d_{a}_t{t}_{f}_s{k:02d}", "e") + mw(f"p2d_{a}_t{t}_{f}_c{k:02d}", "e")
                                    for k in range(7)]))
                exc = wd - we
                cells[f"{a}_t{t}_{f}"] = dict(
                    M_ratio=round(rM, 4), M="READS" if rM <= 0.5 else "DOES NOT READ",
                    W_ratio=round(rW, 4), W="READS" if rW <= 0.5 else "DOES NOT READ",
                    W_dev=round(float(wd.mean()), 4), W_exact=round(float(we.mean()), 4),
                    W_excess=round(float(exc.mean()), 4), W_excess_2SE=round(float(2 * exc.std(ddof=1) / np.sqrt(7)), 4),
                    W_excess_rel=round(float(wd.mean() / we.mean() - 1), 4),
                    S_dev=round(S, 4), S_exact=round(Se, 4))
                errs[f] = d - e
            dl = errs["F"] ** 2 - errs["L"] ** 2
            mu, se = float(dl.mean()), float(dl.std(ddof=1) / np.sqrt(len(dl)))
            twins[f"{a}_t{t}"] = dict(F_minus_L=round(mu, 5), SE=round(se, 5),
                                      verdict="KEEPS MORE" if mu > 2 * se else "KEEPS LESS" if mu < -2 * se else "SAME")
    for f in FORMS:
        w3 = [cells[f"{a}_t3_{f}"]["W_dev"] for a in ARMS]
        order[f] = "yes" if w3[0] > w3[1] > w3[2] else "no"
        for a in ARMS:
            beside[f"{a}_{f}_W3/W1"] = dict(
                dev=round(cells[f"{a}_t3_{f}"]["W_dev"] / cells[f"{a}_t1_{f}"]["W_dev"], 3),
                exact=round(cells[f"{a}_t3_{f}"]["W_exact"] / cells[f"{a}_t1_{f}"]["W_exact"], 3))
    fm = {}
    for t in TS:
        for f in FORMS:
            for k in ("floor", "mirror"):
                nm = f"p2d_A1_t{t}_{f}_s00_{k}"
                if nm in pubs:
                    m = pubs[nm]["meas"]
                    phys = sorted(m)
                    zd = z_from_counts(pubs[nm]["counts"], [m[q] for q in phys])
                    fm[nm[4:]] = dict(n=len(phys), raw_mean=round(float(zd.mean()), 4))
    out.update(cells=cells, twins=twins, order=order, beside=beside, floor_mirror=fm)
    return out


def _path_through(nodes, edges):
    """The single simple path visiting every node of `nodes` along `edges` (pairs), as a list from one end; None when
    the induced graph is not one path."""
    adj = {q: set() for q in nodes}
    for a, b in edges:
        if a in adj and b in adj:
            adj[a].add(b)
            adj[b].add(a)
    ends = [q for q, n in adj.items() if len(n) == 1]
    if len(ends) != 2 or any(len(n) > 2 for n in adj.values()):
        return None
    path, prev = [min(ends)], None
    while len(path) < len(nodes):
        nxt = [q for q in adj[path[-1]] if q != prev]
        if len(nxt) != 1:
            return None
        prev = path[-1]
        path.append(nxt[0])
    return path


def _simulate_against_answers(pubs, names, chain, cone, ex_z):
    """Noise-free <Z> of each user circuit on its measured qubits against the sealed answers (heavy: 40 qubits by
    matrix product states)."""
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import SparsePauliOp, Statevector
    from qiskit_aer import AerSimulator
    aer = AerSimulator(method="matrix_product_state")
    worst = 0.0
    for nm in names:
        if nm not in ex_z:
            continue
        qc = pubs[nm]["circuit"]
        pos = sorted(ex_z[nm])
        phys = [chain[p] for p in pos]
        idx = {q: i for i, q in enumerate(phys)}
        r = QuantumCircuit(len(phys))
        for ins in qc.data:
            if ins.operation.name in ("measure", "barrier"):
                continue
            qs = [qc.find_bit(q).index for q in ins.qubits]
            if all(q in idx for q in qs):
                r.append(ins.operation, [idx[q] for q in qs])
        n = r.num_qubits
        if n <= 16:
            pr = Statevector(r).probabilities()
            bits = (np.arange(len(pr))[:, None] >> np.arange(n)[None, :]) & 1
            zs = 1 - 2 * (pr @ bits)
        else:
            c = r.copy()
            for q in range(n):
                lab = ["I"] * n
                lab[n - 1 - q] = "Z"
                c.save_expectation_value(SparsePauliOp("".join(lab)), list(range(n)), label=f"z{q}")
            res = aer.run(c, shots=1).result().data()
            zs = np.array([res[f"z{q}"] for q in range(n)])
        worst = max(worst, float(np.abs(zs - np.array([ex_z[nm][p] for p in pos])).max()))
    return worst


SCORERS = {"ohm-window-night-2026-11-23": (os.path.join("ow", "job"), score_ohm_window)}


# ------------------------------------------------------------------------------------------------ comparing
def compare(mine, ref, keys=("cells", "twins", "order", "beside", "chain_is_device_path")):
    """[(path, mine, ref)] for every value under the given keys that differs (floats equal to the reference's
    rounding)."""
    diffs = []

    def walk(a, b, p):
        if isinstance(b, dict):
            for k in b:
                if k == "err":
                    continue
                walk(a.get(k) if isinstance(a, dict) else None, b[k], f"{p}/{k}")
        elif isinstance(b, float) and isinstance(a, (int, float)):
            if abs(a - b) > 1e-12:
                diffs.append((p, a, b))
        elif a != b:
            diffs.append((p, a, b))
    for k in keys:
        if k in ref:
            walk(mine.get(k), ref[k], k)
    return diffs


def selftest():
    """A two-circuit job written to a temporary folder: the mapping comes from the measure instructions (qubit 3 on
    clbit 0, qubit 1 on clbit 1), <Z> from the counts, the sha256 and the shots."""
    import tempfile
    from qiskit import QuantumCircuit, qpy
    qc = QuantumCircuit(4, 2)
    qc.x(3)
    qc.measure(3, 0)
    qc.measure(1, 1)
    qc2 = QuantumCircuit(4, 1)
    qc2.measure(0, 0)
    d = tempfile.mkdtemp(prefix="recount_selftest_")
    buf = io.BytesIO()
    qpy.dump([qc, qc2], buf)
    blob = buf.getvalue()
    with gzip.open(os.path.join(d, "circuits.qpy.gz"), "wb") as g:
        g.write(blob)
    json.dump(dict(circuits_sha256=hashlib.sha256(blob).hexdigest(), shots=10,
                   cells=[dict(cell=0, name="a"), dict(cell=1, name="b")], pubs=[dict(cell=0, point=0), dict(cell=1, point=0)]),
              open(os.path.join(d, "manifest.json"), "w"))
    json.dump(dict(rows=[dict(pub=0, counts={"01": 10}), dict(pub=1, counts={"0": 6, "1": 4})]),
              open(os.path.join(d, "raw_counts.json"), "w"))
    job = load_job(d)
    c = common_checks(job)
    m = job["pubs"][0]["meas"]
    z = z_from_counts(job["pubs"][0]["counts"], [m[3], m[1]])
    z2 = z_from_counts(job["pubs"][1]["counts"], [0])
    ok = (c["qpy_sha256_matches_manifest"] and c["shots_as_manifest"] and m == {3: 0, 1: 1}
          and list(z) == [-1.0, 1.0] and abs(z2[0] - 0.2) < 1e-12 and [p["name"] for p in job["pubs"]] == ["a", "b"])
    print(f"independent_recount selftest: {'PASS' if ok else 'FAIL'} (map {m}, <Z> {list(z)}, {list(z2)}, {c})")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("night", nargs="?")
    ap.add_argument("--json")
    ap.add_argument("--compare")
    ap.add_argument("--simulate", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return 0 if selftest() else 1
    if not a.night:
        ap.error("give a night folder (results/NAME)")
    night = a.night.rstrip("/\\")
    name = os.path.basename(night)
    if name in SCORERS:
        jobs = [os.path.join(night, SCORERS[name][0])]
    else:
        jobs = sorted(os.path.dirname(p) for p in __import__("glob").glob(os.path.join(night, "**", "job",
                                                                                         "manifest.json"), recursive=True))
    if not jobs:
        print(f"independent_recount: no job folder under {night}", file=sys.stderr)
        return 1
    out, ok = dict(night=name, jobs={}), True
    for jd in jobs:
        job = load_job(jd)
        cc = common_checks(job)
        ok &= cc["qpy_sha256_matches_manifest"] and cc["circuits_match_manifest"] and cc["shots_as_manifest"]
        out["jobs"][os.path.relpath(jd, night)] = cc
        if name in SCORERS:
            out["score"] = SCORERS[name][1](night, job, a.simulate)
    print(json.dumps(out["jobs"], indent=1))
    if "score" in out:
        for k, c in out["score"]["cells"].items():
            print(k, c)
        print("twins", out["score"]["twins"])
        print("order", out["score"]["order"], "| chain", out["score"]["chain_from_records"],
              "| on the declared positions", out["score"]["measured_on_the_declared_positions"])
    else:
        print(f"(no scoring formula registered for {name}; the common part only)")
    if a.compare:
        ref = json.load(open(a.compare))
        diffs = compare(out.get("score", {}), ref)
        print(f"compared with {a.compare}: {len(diffs)} values differ" + "".join(f"\n   {d}" for d in diffs[:20]))
        ok &= not diffs
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1, default=str)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
