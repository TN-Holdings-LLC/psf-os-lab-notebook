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
ceilings are the declared values; each value is also looked up in the README's results row) and
ohm-ruler-night-2026-11-24 (the raw words, rulers (a) and (b), the one-factor test, the order and W(t) / W(1), from the
declaration's formulas). sentinel_overlap(job) counts the qubits the ring sentinel shares with the other circuits.
score_ohm_ruler3(out_dir, job, answers_by_label) is the frame for the third night (not declared): rulers (b), (b')
(candidate 1, low qubits outside the window left out), (c) and (d), written from the draft; compare_ruler3 sets it
against score3's scores3.json (--ruler3 OUT ANS_BY_LABEL).
Past nights' reproduce.py is not changed.

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
import math
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


# ------------------------------------------------------------------- the Ohm ruler night (11-24) and the sentinel
def sentinel_overlap(job):
    """The qubits the ring sentinel's circuits touch against those of every other circuit of the job (users, mirrors,
    floors), from the circuits as sent (every operation but barriers); the word NOT ON USER QUBITS when they share
    none."""
    role = {c["cell"]: c.get("role") for c in job["manifest"]["cells"]}
    roles = [role[pb["cell"]] for pb in job["manifest"]["pubs"]]

    def active(qc):
        return {qc.find_bit(q).index for ins in qc.data if ins.operation.name != "barrier" for q in ins.qubits}
    sent, other = set(), set()
    for p, r in zip(job["pubs"], roles):
        (sent if r == "sentinel" else other).update(active(p["circuit"]))
    ov = sorted(sent & other)
    return dict(sentinel_circuits=roles.count("sentinel"), sentinel_qubits=len(sent), other_qubits=len(other),
                overlap=len(ov), overlap_qubits=ov,
                word=("NO SENTINEL" if not sent else "NOT ON USER QUBITS" if not ov else "ON USER QUBITS"))


def _chi2_sf(x, k):
    """Chi-square survival function (closed forms: even k by the Poisson sum, odd k by erfc and its series)."""
    if x <= 0:
        return 1.0
    if k % 2 == 0:
        s, term = 0.0, 1.0
        for i in range(k // 2):
            if i:
                term *= (x / 2) / i
            s += term
        return math.exp(-x / 2) * s
    s = math.erfc(math.sqrt(x / 2))
    term = math.sqrt(2 * x / math.pi) * math.exp(-x / 2)
    for i in range(1, (k - 1) // 2 + 1):
        s += term
        term *= x / (2 * i + 1)
    return s


def score_ohm_ruler(night, job, simulate=False):
    """ohm-ruler-night-2026-11-24, from prereg/ohm_ruler_night_2026-11-24.md's formulas: per cell (arm, t, L) the raw
    M and W words with their ratios, W device / exact / excess (2 SE), S, ruler (a) rho_a = T_device / T0 per pair and
    W_a, ruler (b) rho_b = sqrt(mean <Z> of the mirror) and W_b with the mirror's shot noise through the square root,
    their words (|d| < 2 SE); at t >= 3 the window's r per position (shot-noise SE), the weighted pool, chi2 and p; the
    order of W, W_a, W_b at t = 3, 4; W(t) / W(1) raw, exact and by ruler (b). The qubit -> clbit map comes from the
    sent circuits' measure instructions; build.json gives the strings and each item's chain positions and labels; the
    exact <Z> by label from answers/ohm_ruler_answers_by_label.json. The sentinel's word is psf-os's and is not
    re-counted here (sentinel_overlap is given instead)."""
    arms, K = ("A0", "A1", "A2"), None
    b = json.load(open(os.path.join(night, "or", "build.json")))
    ans = json.load(open(os.path.join(night, "answers", "ohm_ruler_answers_by_label.json")))["z"]
    strs, ts, forms, shots = b["strings"], b["cycles"], b["forms"], job["manifest"]["shots"]
    ks = sorted({n[1:] for n in strs})
    K = len(ks)
    window = lambda t: list(range(20, 20 + 2 * t - 1))
    pubs = {p["name"]: p for p in job["pubs"]}

    def zdev(tg):
        p, labels = pubs["p2d_" + tg], b["items"][tg]["given_labels"]
        return z_from_counts(p["counts"], [p["meas"][q] for q in labels])

    out = dict(cells={}, uniform={}, tables={}, order={}, beside={}, sentinel_overlap=sentinel_overlap(job))
    se_k = lambda x: float(np.std(x, ddof=1) / math.sqrt(K))
    for arm in arms:
        for t in ts:
            for form in forms:
                key = f"{arm}_t{t}_{form}"
                it = b["items"][f"{key}_s00"]
                pos, labels = it["positions"], it["given_labels"]
                wi = [i for i, q in enumerate(pos) if q in window(t)]
                zd = {n: zdev(f"{key}_{n}") for n in (p + k for k in ks for p in "sc")}
                ze = {n: np.array([ans[f"{key}_{n}"][str(lb)] for lb in labels]) for n in zd}
                Od = np.array([(zd["s" + k] - zd["c" + k]) / 2 for k in ks])
                Oe = np.array([(ze["s" + k] - ze["c" + k]) / 2 for k in ks])
                T0 = np.array([sum(1 - 2 * int(strs["s" + k][q]) for q in pos) for k in ks], dtype=float)
                m0 = {n: sum(int(strs[n][q]) for q in window(t)) for n in zd}
                const = np.array([-(m0["s" + k] - m0["c" + k]) / 2 for k in ks])
                w_d = -Od[:, wi].sum(axis=1) / 2 + const
                w_e = -Oe[:, wi].sum(axis=1) / 2 + const
                md = np.array([((1 - zd[n][wi]) / 2).sum() - m0[n] for k in ks for n in ("s" + k, "c" + k)])
                me = np.array([((1 - ze[n][wi]) / 2).sum() - m0[n] for k in ks for n in ("s" + k, "c" + k)])
                rM = float(np.mean((md - me) ** 2) / np.mean(me ** 2))
                rW = float(np.mean((w_d - w_e) ** 2) / np.mean(w_e ** 2))
                c = dict(M_ratio=rM, M="READS" if rM <= 0.5 else "DOES NOT READ", W_ratio=rW,
                         W="READS" if rW <= 0.5 else "DOES NOT READ", W_device=float(w_d.mean()),
                         W_exact=float(w_e.mean()), S_device=float(np.mean(md.reshape(K, 2).sum(axis=1))),
                         W_excess=float((w_d - w_e).mean()), W_excess_2se=2 * se_k(w_d - w_e),
                         errors_M=(md - me).tolist())
                if form == "F" or t >= 3:
                    rho_a = Od.sum(axis=1) / T0
                    da = -(Od[:, wi].sum(axis=1) / rho_a) / 2 + const - w_e
                    c.update(rho_a=rho_a.tolist(), W_a=float((da + w_e).mean()), d_a=float(da.mean()),
                             d_a_2se=2 * se_k(da), ruler_a="AGREES" if abs(da.mean()) < 2 * se_k(da) else "DIFFERS")
                else:
                    c["ruler_a"] = "NOT READ"
                mn = f"p2d_{key}_s00_mirror"
                if mn in pubs:
                    mp = pubs[mn]
                    mq = sorted(mp["meas"])
                    zm = z_from_counts(mp["counts"], [mp["meas"][q] for q in mq])
                    m = float(zm.mean())
                    tot = sum(mp["counts"].values())
                    per = [(np.mean([1 - 2 * int(s.replace(" ", "")[-1 - mp["meas"][q]]) for q in mq]), n)
                           for s, n in mp["counts"].items()]
                    mu = sum(v * n for v, n in per) / tot
                    m_se = math.sqrt(sum(n * (v - mu) ** 2 for v, n in per) / (tot - 1) / tot)
                    c["mirror"] = m
                    if m > 0:
                        rb = math.sqrt(m)
                        db = -(Od[:, wi].sum(axis=1) / rb) / 2 + const - w_e
                        slope = float(np.mean(Od[:, wi].sum(axis=1)) / (4 * m ** 1.5))
                        se_b = math.sqrt(se_k(db) ** 2 + (slope * m_se) ** 2)
                        c.update(rho_b=rb, W_b=float((db + w_e).mean()), d_b=float(db.mean()), d_b_2se=2 * se_b,
                                 ruler_b="AGREES" if abs(db.mean()) < 2 * se_b else "DIFFERS")
                out["cells"][key] = c
                if t >= 3:
                    use = [i for i in wi if np.sum(Oe[:, i] ** 2) >= 0.05 * K]
                    var = np.array([[(1 - zd[p + k] ** 2) / shots for p in "sc"] for k in ks])
                    r, se = [], []
                    for i in use:
                        den = float(np.sum(Oe[:, i] ** 2))
                        r.append(float(np.sum(Od[:, i] * Oe[:, i]) / den))
                        se.append(math.sqrt(float(np.sum(Oe[:, i] ** 2 * (var[:, 0, i] + var[:, 1, i]) / 4))) / den)
                    u = dict(positions=[pos[i] for i in use], r=r, se=se)
                    if len(use) >= 2:
                        w = 1 / np.array(se) ** 2
                        pool = float(np.sum(w * np.array(r)) / w.sum())
                        chi = float(np.sum(((np.array(r) - pool) / np.array(se)) ** 2))
                        p = _chi2_sf(chi, len(use) - 1)
                        u.update(r_pool=pool, chi2=chi, dof=len(use) - 1, p=p, word="UNIFORM" if p >= 0.05 else "NOT UNIFORM")
                    else:
                        u.update(word="NOT READ")
                    out["uniform"][key] = u
                    out["tables"][key] = dict(table1=[u["word"], c["ruler_a"]],
                                              table2=[c["ruler_a"], c.get("ruler_b")])
    for form in forms:
        for t in (x for x in ts if x >= 3):
            for q in ("W_device", "W_a", "W_b"):
                v = [out["cells"][f"{a}_t{t}_{form}"].get(q) for a in arms]
                if None not in v:
                    out["order"][f"{q}_t{t}_{form}"] = "yes" if v[0] > v[1] > v[2] else "no"
        for a in arms:
            c1 = out["cells"][f"{a}_t1_{form}"]
            for t in (x for x in ts if x >= 3):
                ct = out["cells"][f"{a}_t{t}_{form}"]
                g = dict(raw=ct["W_device"] / c1["W_device"], exact=ct["W_exact"] / c1["W_exact"])
                for q in ("W_a", "W_b"):
                    if q in ct and q in c1:
                        g[q] = ct[q] / c1[q]
                out["beside"][f"{a}_{form}_W{t}_over_W1"] = g
    return out


# ------------------------------------------------------------------- the third Ohm ruler night (frame, not declared)
T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228}


def _words(d, se, K):
    """Rule 4 (t quantile, K - 1 degrees of freedom) and rule 5 (NOT READ on a 0 SE); the 2 SE word beside."""
    if not (se > 0):
        return {"t": "NOT READ", "2se": "NOT READ"}
    tq = T975.get(K - 1, 1.96)
    return {"t": "AGREES" if abs(d) < tq * se else "DIFFERS", "2se": "AGREES" if abs(d) < 2 * se else "DIFFERS"}


def _mirror_mean_se(pub, labels, idx, weights):
    """Per-label <Z> of a mirror pub, the mean of weights * <Z> over labels[idx] and its shot-noise SE (per-shot mean)."""
    m, w = pub["meas"], np.asarray(weights, dtype=float)
    tot = sum(pub["counts"].values())
    z, per = np.zeros(len(labels)), []
    for key, c in pub["counts"].items():
        s = key.replace(" ", "")
        v = np.array([1 - 2 * int(s[-1 - m[lb]]) for lb in labels], dtype=float)
        z += c * v
        per.append((float((w[idx] * v[idx]).mean()), c))
    z /= tot
    mu = sum(x * c for x, c in per) / tot
    return z, math.sqrt(sum(c * (x - mu) ** 2 for x, c in per) / (tot - 1) / tot)


def score_ohm_ruler3(out_dir, job, answers_by_label, tau=0.3, keep_fraction=0.5):
    """The third night's mirror rulers, written from prereg/drafts-2026-11-25/ohm_ruler3_night_DRAFT.md ("The rulers"):
    per cell (arm, t, L), over its K pairs (K per t from build.json),
      (b)  rho_b = sqrt(mean over the circuit's qubits of the |0> mirror's <Z>);
      (b') the same with the qubits OUTSIDE the window whose mirror <Z> is below tau left out (window qubits always
           stay); NOT READ when fewer than keep_fraction of the circuit's qubits are left;
      (c)  rho_c = sqrt(mean over the window's qubits of the |0> mirror's <Z>);
      (d)  rho_d = sqrt(mean over the window of m_q = (Z^m_s,q - Z^m_c,q) / 2 x (1 - 2 b_s00,q)) from the s00 and c00
           string mirrors;
    each W_x,k = -sum_window (O_device,kq / rho) / 2 + const_k, d = mean_k (W_x,k - W_exact,k), its SE from the pairs'
    scatter and the mirror's shot noise through the square root, and the words (t quantile, rule 5; 2 SE beside).
    Keys as score3's: b, b_out, c, d. The qubit -> clbit map comes from the sent circuits."""
    b = json.load(open(os.path.join(out_dir, "build.json")))
    ans = json.load(open(answers_by_label))["z"]
    strs = b["strings"]
    pubs = {p["name"]: p for p in job["pubs"]}
    window = lambda t: list(range(20, 20 + 2 * t - 1))
    out = {}
    for arm in ("A0", "A1", "A2"):
        for t in b["cycles"]:
            key = f"{arm}_t{t}_L"
            ks = sorted(n[1:] for n in strs if n.startswith("s") and f"{key}_{n}" in b["items"])
            K = len(ks)
            it = b["items"][f"{key}_s00"]
            pos, labels = it["positions"], it["given_labels"]
            wi = [i for i, q in enumerate(pos) if q in window(t)]
            zd = {}
            for n in (p + k for k in ks for p in "sc"):
                pb = pubs[f"p2d_{key}_{n}"]
                zd[n] = z_from_counts(pb["counts"], [pb["meas"][lb] for lb in labels])
            ze = {n: np.array([ans[f"{key}_{n}"][str(lb)] for lb in labels]) for n in zd}
            Od = np.array([(zd["s" + k] - zd["c" + k]) / 2 for k in ks])
            Oe = np.array([(ze["s" + k] - ze["c" + k]) / 2 for k in ks])
            const = np.array([-(sum(int(strs["s" + k][q]) for q in window(t))
                                - sum(int(strs["c" + k][q]) for q in window(t))) / 2 for k in ks])
            Od_w, w_ex = Od[:, wi].sum(axis=1), -Oe[:, wi].sum(axis=1) / 2 + const

            def ruler(m, m_se):
                if not (m > 0):
                    return dict(rho=None, d=None, se=None, words={"t": "NOT READ", "2se": "NOT READ"})
                rho = math.sqrt(m)
                dk = (-(Od_w / rho) / 2 + const) - w_ex
                se = math.sqrt(float(np.std(dk, ddof=1) / math.sqrt(K)) ** 2
                               + (float(np.mean(Od_w)) / (4 * m ** 1.5) * m_se) ** 2)
                return dict(rho=rho, mean=m, d=float(dk.mean()), se=se, words=_words(float(dk.mean()), se, K))
            R = {}
            mp = pubs.get(f"p2d_{key}_s00_mirror")
            if mp is not None:
                ones = np.ones(len(labels))
                allq = list(range(len(pos)))
                zm, se_all = _mirror_mean_se(mp, labels, allq, ones)
                R["b"] = ruler(float(zm.mean()), se_all)
                keep = [i for i in allq if i in wi or zm[i] >= tau]
                if len(keep) < keep_fraction * len(allq):
                    R["b_out"] = dict(words={"t": "NOT READ", "2se": "NOT READ"}, kept=len(keep), of=len(allq))
                else:
                    R["b_out"] = ruler(float(zm[keep].mean()), _mirror_mean_se(mp, labels, keep, ones)[1])
                    R["b_out"].update(kept=len(keep), of=len(allq), left_out=[pos[i] for i in allq if i not in keep])
                R["c"] = ruler(float(zm[wi].mean()), _mirror_mean_se(mp, labels, wi, ones)[1])
            ms, mc = pubs.get(f"p2d_{key}_s00_smirror"), pubs.get(f"p2d_{key}_c00_smirror")
            if ms is not None and mc is not None:
                sig = np.array([1 - 2 * int(strs["s00"][q]) for q in pos], dtype=float)
                zs, se_s = _mirror_mean_se(ms, labels, wi, sig)
                zc, se_c = _mirror_mean_se(mc, labels, wi, sig)
                mq = (zs - zc) / 2 * sig
                R["d"] = ruler(float(mq[wi].mean()), math.sqrt(se_s ** 2 + se_c ** 2) / 2)
            out[key] = dict(K=K, rulers=R)
    return out


def compare_ruler3(mine, scores3, keys=("rho", "d", "se"), words=("t", "2se")):
    """[(cell, ruler, what, mine, score3's)] for every value and word that differs (floats beyond 1e-12)."""
    diffs = []
    for cell, c in mine.items():
        for r, v in c["rulers"].items():
            ref = scores3["cells"][cell]["rulers"].get(r)
            if ref is None:
                diffs.append((cell, r, "missing in scores3", None, None))
                continue
            for k in keys:
                a, b2 = v.get(k), ref.get(k)
                if (a is None) != (b2 is None) or (a is not None and abs(a - b2) > 1e-12):
                    diffs.append((cell, r, k, a, b2))
            for w in words:
                if v["words"][w] != ref["words"][w]:
                    diffs.append((cell, r, "word " + w, v["words"][w], ref["words"][w]))
    return diffs


# name -> (job folders under the night, the scoring function, the keys --compare reads, per-key tolerances, keys
# --compare skips). A function given one job folder takes (night, job, simulate); given a list,
# (night, [(job_dir, job)], simulate).
SCORERS = {
    "ohm-window-night-2026-11-23": (os.path.join("ow", "job"), score_ohm_window,
                                    ("cells", "twins", "order", "beside", "chain_is_device_path"), {}),
    "qpe-parked-night-2026-11-21": ([os.path.join("qp", "job0", "job"), os.path.join("qp", "job1", "job")],
                                    score_qpe_parked, ("per_n", "shape"), {}),
    # the record JSON holds the exact ceiling; the declaration writes it to 4 decimals
    "qpe-n78-night-2026-11-22": ([os.path.join("qn", "job0", "job")], score_qpe_n78, ("per_n", "shape"),
                                 {"ceiling": 5e-5}),
    # the sentinel's word is psf-os's own (not re-counted); no floors were sent
    "ohm-ruler-night-2026-11-24": (os.path.join("or", "job"), score_ohm_ruler,
                                   ("cells", "uniform", "order", "beside"), {}, ("sentinel", "floor_mean")),
}


# ------------------------------------------------------------------------------------------------ comparing
def compare(mine, ref, keys=("cells", "twins", "order", "beside", "chain_is_device_path"), tol=None, skip=()):
    """[(path, mine, ref)] for every value under the given keys that differs (floats within 1e-12, or within tol[k]
    for a value whose own key is k; lists element by element). Keys named in skip (and "err") are not compared."""
    diffs, tol = [], tol or {}

    def walk(a, b, p):
        if isinstance(b, list) and isinstance(a, list) and len(a) == len(b) and any(isinstance(x, float) for x in b):
            for i, (x, y) in enumerate(zip(a, b)):
                walk(x, y, f"{p}/{i}")
            return
        if isinstance(b, dict):
            for k in b:
                if k == "err" or k in skip:
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
    ap.add_argument("--ruler3", nargs=2, metavar=("OUT", "ANS_BY_LABEL"),
                    help="the third night's frame on a build folder with counts: compared with its scores3.json")
    ap.add_argument("--tau", type=float, default=0.3)
    a = ap.parse_args()
    if a.selftest:
        return 0 if selftest() else 1
    if a.ruler3:
        out_dir, ansf = a.ruler3
        job = load_job(os.path.join(out_dir, "job"))
        mine = score_ohm_ruler3(out_dir, job, ansf, tau=a.tau)
        ref = json.load(open(os.path.join(out_dir, "scores3.json")))
        diffs = compare_ruler3(mine, ref)
        n = sum(len(c["rulers"]) for c in mine.values())
        print(f"third night frame: {len(mine)} cells, {n} rulers (b, b_out, c, d) against scores3.json: "
              f"{len(diffs)} values differ" + "".join(f"\n   {d}" for d in diffs[:20]))
        return 0 if not diffs else 1
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
        for k in ("twins", "order", "chain_from_records", "measured_on_the_declared_positions", "uniform",
                  "sentinel_overlap"):
            if k in out["score"]:
                print(k, out["score"][k])
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
        diffs = compare(out.get("score", {}), ref, *(spec[2:5] if spec else ()))
        print(f"compared with {a.compare}: {len(diffs)} values differ" + "".join(f"\n   {d}" for d in diffs[:20]))
        ok &= not diffs
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1, default=str)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
