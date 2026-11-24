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
A night's scoring formula is a small function registered in SCORERS under the night's folder name:
ohm-window-night-2026-11-23 (the same formulas as ow_independent_check.py), qpe-parked-night-2026-11-21 and
qpe-n78-night-2026-11-22 (the hit shares, 2 SE, the ceiling words and margins, parking's difference with 2 SE; the
ceilings are the declared values; each value is also looked up in the README's results row). Past nights'
reproduce.py is not changed.

  python tools/independent_recount.py results/NIGHT [--json OUT.json] [--compare REF.json] [--simulate]
  python tools/independent_recount.py --selftest
Exit code: 0 when every check of the common part holds (and, with --compare, every compared value is equal; for the
phase estimation nights, every value is found in the README's results rows); 1 if not.
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


# ------------------------------------------------------------------- phase estimation nights (11-21 parked, 11-22 n78)
# The ceilings C(n) as written in a declaration (not recomputed). C(5) is written in no declaration: the value is the
# 11-21 record's README (set apart in the output as "ceiling_source").
CEILINGS = {4: (0.4706, "prereg/qpe_repro_night_2026-11-19.md"),
            5: (0.3792, "results/qpe-parked-night-2026-11-21/README.md (no declaration states C(5))"),
            6: (0.3065, "prereg/qpe_n78_night_2026-11-22.md"),
            7: (0.2480, "prereg/qpe_n78_night_2026-11-22.md"),
            8: (0.2007, "prereg/qpe_n78_night_2026-11-22.md")}


def _bit(key, k):
    return int(key.replace(" ", "")[-1 - k])


def _ipe_items(night, jobs, simulate=False):
    """{tag: dict(ok, N, job)} for every user item of the jobs: the success clbits and their right values are the
    item's runs/ff_TAG.json record ("success"); a shot is a hit when every success clbit reads its right value. With
    simulate, the right values are checked against noiseless Aer of the circuit as sent (each clbit 0 or 1 always)."""
    items, checked = {}, 0
    sim = None
    if simulate:
        from qiskit_aer import AerSimulator
        sim = AerSimulator()
    for jd, job in jobs:
        runs = os.path.join(os.path.dirname(jd), "runs")
        for p in job["pubs"]:
            rec_f = os.path.join(runs, p["name"] + ".json")
            if not p["name"].startswith("ff_") or not os.path.exists(rec_f):
                continue
            right = {int(k): int(v) for k, v in json.load(open(rec_f))["success"].items()}
            if sim is not None:
                ideal = sim.run(p["circuit"], shots=2000, seed_simulator=11).result().get_counts()
                for k, v in right.items():
                    p1 = sum(c for key, c in ideal.items() if _bit(key, k) == 1) / 2000
                    if p1 != float(v):
                        raise SystemExit(f"{p['name']}: clbit {k} noiseless {p1}, record says {v}")
                checked += 1
            ok = sum(c for key, c in p["counts"].items() if all(_bit(key, k) == v for k, v in right.items()))
            items[p["name"][3:]] = dict(ok=ok, N=p["shots"], job=os.path.relpath(jd, night))
    return items, checked


def _pool(items, tags):
    ok = sum(items[t]["ok"] for t in tags)
    N = sum(items[t]["N"] for t in tags)
    p = ok / N
    return p, float(np.sqrt(p * (1 - p) / N)), N


def _keep_word(d, se):
    return "KEEPS MORE" if d >= 2 * se and d > 0 else "KEEPS LESS" if d <= -2 * se and d < 0 else "SAME WITHIN ERROR"


def _ceiling_word(p, se, c):
    return "BEYOND THE CEILING" if p >= c + 2 * se else "NOT BEYOND"


def _shape(res, ns):
    """Acceleration of the log share over three n and its SE sqrt(t1^2 + 4 t2^2 + t3^2), t = SE / p."""
    lg = {n: float(np.log(res[n][0])) for n in ns}
    t = {n: res[n][1] / res[n][0] for n in ns}
    a, b, c = ns
    acc = (lg[b] - lg[c]) - (lg[a] - lg[b])
    se = float(np.sqrt(t[a] ** 2 + 4 * t[b] ** 2 + t[c] ** 2))
    word = "ACCELERATES" if acc >= 2 * se and acc > 0 else "SLOWS" if acc <= -2 * se and acc < 0 else "FLAT"
    return dict(drops=[lg[a] - lg[b], lg[b] - lg[c]], acc=acc, two_se=2 * se, word=word)


def _tagnum(t):
    return int(t.split("_")[1])


def score_qpe_parked(night, jobs, simulate=False):
    """qpe-parked-night-2026-11-21: per n = 4, 5, 6 the parked share over every phase (ipe{n}_j) with 2 SE, its
    ceiling word and the distance from C(n); on the phases holding an unparked twin (ipu{n}_j, same job) the parked
    and unparked shares, their difference d with 2 SE and the word; the parked shape over n (beside, as recorded)."""
    items, checked = _ipe_items(night, jobs, simulate)
    per_n, res = {}, {}
    for n in (4, 5, 6):
        pk = [t for t in items if t.startswith(f"ipe{n}_")]
        p, se, N = _pool(items, pk)
        res[n] = (p, se)
        c, src = CEILINGS[n]
        pairs = sorted(_tagnum(t) for t in items if t.startswith(f"ipu{n}_"))
        split = [j for j in pairs if items[f"ipu{n}_{j}"]["job"] != items[f"ipe{n}_{j}"]["job"]]
        a, sa, _ = _pool(items, [f"ipe{n}_{j}" for j in pairs])
        b, sb, _ = _pool(items, [f"ipu{n}_{j}" for j in pairs])
        d, sd = a - b, float(np.sqrt(sa ** 2 + sb ** 2))
        per_n[str(n)] = dict(parked=p, parked_2se=2 * se, N=N, verdict=_ceiling_word(p, se, c), phases_paired=len(pairs),
                             parked_on_pairs=a, unparked_on_pairs=b, d=d, d_2se=2 * sd, word=_keep_word(d, sd),
                             ceiling=c, ceiling_source=src, beyond_ceiling_by=p - c, phases=len(pk),
                             paired_phases=pairs, pairs_split_across_jobs=split)
    return dict(per_n=per_n, shape=_shape(res, (4, 5, 6)), items=len(items), right_values_simulated=checked)


def score_qpe_n78(night, jobs, simulate=False):
    """qpe-n78-night-2026-11-22: per n = 6, 7, 8 the parked share over its 16 phases (ipk{n}_j) with 2 SE, the
    ceiling word and the margin beyond C(n); on the twin phases (ipu{n}_j) the parked and unparked shares, the gain of
    parking d with 2 SE and the word; the shape over n (beside, as recorded)."""
    items, checked = _ipe_items(night, jobs, simulate)
    per_n, res = {}, {}
    for n in (6, 7, 8):
        pk = [t for t in items if t.startswith(f"ipk{n}_")]
        p, se, N = _pool(items, pk)
        res[n] = (p, se)
        c, src = CEILINGS[n]
        tw = sorted(_tagnum(t) for t in items if t.startswith(f"ipu{n}_"))
        a, sa, _ = _pool(items, [f"ipk{n}_{j}" for j in tw])
        b, sb, _ = _pool(items, [f"ipu{n}_{j}" for j in tw])
        d, sd = a - b, float(np.sqrt(sa ** 2 + sb ** 2))
        per_n[str(n)] = dict(p=p, two_se=2 * se, N=N, ceiling=c, ceiling_source=src, verdict=_ceiling_word(p, se, c),
                             margin=p - c, twin_parked=a, twin_unparked=b, d=d, d_two_se=2 * sd,
                             park_word=_keep_word(d, sd), phases=len(pk), twin_phases=tw)
    return dict(per_n=per_n, shape=_shape(res, (6, 7, 8)), items=len(items), right_values_simulated=checked)


def readme_rows(night, score):
    """[(n, [strings], [missing])]: the record README's results row for each n must hold this re-count's values
    as the README writes them (4 decimals; the distance from the ceiling to 3; the words)."""
    text = open(os.path.join(night, "README.md"), encoding="utf-8").read()
    out = []
    for n, c in score["per_n"].items():
        row = next((ln for ln in text.splitlines() if ln.startswith(f"| {n} |")), "")
        if "parked" in c:      # 11-21
            want = [f"{c['parked']:.4f} ({c['parked_2se']:.4f})", f"{c['ceiling']:.4f}", c["verdict"],
                    f"({c['beyond_ceiling_by']:+.3f})",
                    f"{c['parked_on_pairs']:.4f} - {c['unparked_on_pairs']:.4f} = {c['d']:+.4f} ({c['d_2se']:.4f})",
                    c["word"]]
        else:                  # 11-22
            want = [f"{c['p']:.4f} ({c['two_se']:.4f})", f"{c['ceiling']:.4f}", c["verdict"], f"({c['margin']:+.3f})",
                    f"{c['d']:+.4f} ({c['d_two_se']:.4f})", c["park_word"]]
        out.append((n, want, [w for w in want if w not in row]))
    sh = score["shape"]
    acc = f"{sh['acc']:+.4f} (2 SE {sh['two_se']:.4f})"
    out.append(("shape", [acc, sh["word"]], [w for w in (acc, sh["word"]) if w not in text]))
    return out


# name -> (job folders under the night, the scoring function, the keys --compare reads, per-key tolerances).
# A function given one job folder takes (night, job, simulate); given a list, (night, [(job_dir, job)], simulate).
SCORERS = {
    "ohm-window-night-2026-11-23": (os.path.join("ow", "job"), score_ohm_window,
                                    ("cells", "twins", "order", "beside", "chain_is_device_path"), {}),
    "qpe-parked-night-2026-11-21": ([os.path.join("qp", "job0", "job"), os.path.join("qp", "job1", "job")],
                                    score_qpe_parked, ("per_n", "shape"), {}),
    # the record JSON holds the exact ceiling; the declaration writes it to 4 decimals
    "qpe-n78-night-2026-11-22": ([os.path.join("qn", "job0", "job")], score_qpe_n78, ("per_n", "shape"),
                                 {"ceiling": 5e-5}),
}


# ------------------------------------------------------------------------------------------------ comparing
def compare(mine, ref, keys=("cells", "twins", "order", "beside", "chain_is_device_path"), tol=None):
    """[(path, mine, ref)] for every value under the given keys that differs (floats within 1e-12, or within tol[k]
    for a value whose own key is k)."""
    diffs, tol = [], tol or {}

    def walk(a, b, p):
        if isinstance(b, dict):
            for k in b:
                if k == "err":
                    continue
                walk(a.get(k) if isinstance(a, dict) else None, b[k], f"{p}/{k}")
        elif isinstance(b, float) and isinstance(a, (int, float)):
            # NaN on one side is a difference (abs(a - b) > tol is False for NaN, so test it first); NaN on both
            # sides is equal
            if (a != a) or (b != b):
                if not ((a != a) and (b != b)):
                    diffs.append((p, a, b))
            elif abs(a - b) > tol.get(p.rsplit("/", 1)[-1], 1e-12):
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
    spec = SCORERS.get(name)
    if spec:
        jobs = [os.path.join(night, j) for j in ([spec[0]] if isinstance(spec[0], str) else spec[0])]
    else:
        jobs = sorted(os.path.dirname(p) for p in __import__("glob").glob(os.path.join(night, "**", "job",
                                                                                         "manifest.json"), recursive=True))
    if not jobs:
        print(f"independent_recount: no job folder under {night}", file=sys.stderr)
        return 1
    out, ok, loaded = dict(night=name, jobs={}), True, []
    for jd in jobs:
        job = load_job(jd)
        cc = common_checks(job)
        ok &= cc["qpy_sha256_matches_manifest"] and cc["circuits_match_manifest"] and cc["shots_as_manifest"]
        out["jobs"][os.path.relpath(jd, night)] = cc
        loaded.append((jd, job))
    if spec:
        out["score"] = spec[1](night, loaded[0][1] if isinstance(spec[0], str) else loaded, a.simulate)
    print(json.dumps(out["jobs"], indent=1))
    if "score" in out and "cells" in out["score"]:
        for k, c in out["score"]["cells"].items():
            print(k, c)
        print("twins", out["score"]["twins"])
        print("order", out["score"]["order"], "| chain", out["score"]["chain_from_records"],
              "| on the declared positions", out["score"]["measured_on_the_declared_positions"])
    elif "score" in out:
        for n, c in out["score"]["per_n"].items():
            print(f"n {n}:", {k: (round(v, 6) if isinstance(v, float) else v) for k, v in c.items()})
        print("shape (beside):", {k: (round(v, 6) if isinstance(v, float) else v) if not isinstance(v, list) else
                                  [round(x, 6) for x in v] for k, v in out["score"]["shape"].items()})
        rows = readme_rows(night, out["score"])
        miss = sum(len(m) for _, _, m in rows)
        print(f"against the README's results rows: {sum(len(w) for _, w, _ in rows)} values, {miss} not found"
              + "".join(f"\n   n {n}: missing {m}" for n, _, m in rows if m))
        ok &= not miss
    else:
        print(f"(no scoring formula registered for {name}; the common part only)")
    if a.compare:
        ref = json.load(open(a.compare))
        diffs = compare(out.get("score", {}), ref, *(spec[2:4] if spec else ()))
        print(f"compared with {a.compare}: {len(diffs)} values differ" + "".join(f"\n   {d}" for d in diffs[:20]))
        ok &= not diffs
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1, default=str)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
