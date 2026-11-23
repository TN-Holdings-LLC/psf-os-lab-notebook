"""Ohm on the wall's light-cone window, twins in one job (home VS, 2026-11-23; home's instruction "オームの窓と双子の
宣言の下書き"; owner 13:4x CET: plan B, about 50 s, the window's M and W judged, W(t)/W(1) beside, no fractional gates).

Circuits: gpu/ohm_answers.py's (N 40 chain, fSim(pi/4, phi) brickwork, arms A0 / A1 / A2), t = 1 and 3 cycles, the
first PAIRS pairs of the 11-12 strings (seed 20261112, K 14, m 0.5: s00..s06 and their complements c00..c06 by
default). Every (arm, t, string) is built twice, as twins in the same job:
  F: the 40-qubit circuit, on the chain chosen as gpu/ohm_build.py chooses it (daily/du91 shapes, then psf-os rule C);
  L: the light-cone circuit: only the qubits and fSim gates of the backward light cone of the window (the 2t - 1 chain
     sites next to the wall, positions 20 .. 20 + 2t - 2), placed on the same physical qubits as F's (the subset at the
     same chain positions; the build refuses if psf-os places it anywhere else).
Floor and mirror (psf-os user entrance) are sent only for the items named by --floors (default: A1, string s00, for
each t and twin); the others are built and checked by psf-os as usual, and their floor and mirror records are moved
to OUT/unsent_runs before the job is assembled. One ring sentinel. psf-os 0.3.3, its park default unchanged (these
circuits have no mid-circuit measurement and no delay: nothing to park; the build checks and records it).

Subcommands:
  answers OUT.json [--pairs 7]                  per-qubit <Z> of every item (A0 F by free fermions, the rest by quimb
                                                 CircuitMPS, chi 2048, cutoff 1e-10), by chain position; sealed: prints
                                                 checks only (the window of L against F; A0 quimb against free fermions)
  pick QUEUE.json                               the device: not ibm_marrakesh; of ibm_fez and ibm_kingston the fewer
                                                 pending, a tie in the queue file's order
  build DEV_DIR OUT ANS_IN ANS_OUT [--shots 1000] [--floors TAG ...]
  check OUT ANS_OUT                             noise-free, on the job's compiled circuits (Aer, statevector up to 12
                                                 qubits, MPS above): per-qubit <Z> within 1e-6 of the answers, mirrors
                                                 all zeros, the twins' windows equal within 1e-6, CZ as intended
  score OUT ANS_OUT                             the declared verdicts (prereg draft ohm_window_night)
Charge estimate: 2.6 s + 0.000269 s x circuits x shots (the project's usual formula), with psf-os's model beside.
usage: PYTHONPATH=<psf-os 0.3.3>:<TOQB> python gpu/ohm_window_night.py SUBCOMMAND ...
"""
import argparse
import ast
import hashlib
import json
import os
import shutil
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import ohm_answers as OA  # noqa: E402

N, K, M_BIAS, SEED = 40, 14, 0.5, 20261112
TS = (1, 3)
ARMS = ("A0", "A1", "A2")
FORMS = ("L", "F")
CZ_PER_FSIM = {"A0": 2, "A1": 3, "A2": 3}
DEFAULT_FLOORS = [f"A1_t{t}_{f}_s00" for t in TS for f in FORMS]
H = N // 2


def charge(circuits, shots):
    """The project's usual charge formula (seconds)."""
    return 2.6 + 0.000269 * circuits * shots


def window(t):
    return list(range(H, H + 2 * t - 1))


def tag(arm, t, form, name):
    return f"{arm}_t{t}_{form}_{name}"


def strings(pairs):
    s = OA.strings(N, K, M_BIAS, SEED)
    keep = {f"s{k:02d}" for k in range(pairs)} | {f"c{k:02d}" for k in range(pairs)}
    return [(n, b) for n, b in s if n in keep]


def layers(t):
    return [(c, p, [(q, q + 1) for q in range(p, N - 1, 2)]) for c in range(t) for p in (0, 1)]


def cone(t):
    """(chain positions in the window's backward light cone, kept fSim gates as (cycle, parity, q))."""
    s, kept = set(window(t)), []
    for c, p, gates in reversed(layers(t)):
        for a, b in gates:
            if a in s or b in s:
                kept.append((c, p, a))
                s |= {a, b}
    return sorted(s), sorted(kept)


def positions(t, form):
    return cone(t)[0] if form == "L" else list(range(N))


def logical(arm, t, form, bits):
    """The logical circuit on len(positions) qubits (qubit i = chain position positions[i]), no measurement."""
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import UnitaryGate
    phi, Hf = OA.ARMS[arm]
    G = UnitaryGate(OA.fsim(OA.THETA, phi), label=f"fsim_{arm}")
    if form == "F":
        return OA.circuit(N, t, arm, bits)
    qs, kept = cone(t)
    ix, keep = {q: i for i, q in enumerate(qs)}, set(kept)
    qc = QuantumCircuit(len(qs))
    for q in qs:
        if bits[q]:
            qc.x(ix[q])
    for c in range(t):
        for p in (0, 1):
            for q in range(p, N - 1, 2):
                if (c, p, q) in keep:
                    qc.append(G, [ix[q], ix[q + 1]])
        if Hf:
            for q in qs:
                if OA.PATTERN[q % 3]:
                    qc.rz(Hf * OA.PATTERN[q % 3], ix[q])
    return qc


def fsim_count(t, form):
    return len(cone(t)[1]) if form == "L" else t * (N - 1)


def z_cone_quimb(arm, t, bits):
    """Per-qubit <Z> of the light-cone circuit by quimb, by chain position."""
    import quimb.tensor as qtn
    phi, Hf = OA.ARMS[arm]
    qs, kept = cone(t)
    ix, keep = {q: i for i, q in enumerate(qs)}, set(kept)
    c = qtn.CircuitMPS(len(qs), max_bond=2048, cutoff=1e-10)
    X = np.array([[0, 1], [1, 0]])
    for q in qs:
        if bits[q]:
            c.apply_gate_raw(X, (ix[q],))
    G = OA.fsim(OA.THETA, phi)
    for cy in range(t):
        for p in (0, 1):
            for q in range(p, N - 1, 2):
                if (cy, p, q) in keep:
                    c.apply_gate_raw(G, (ix[q], ix[q + 1]))
        if Hf:
            for q in qs:
                h = Hf * OA.PATTERN[q % 3]
                if h:
                    c.apply_gate_raw(np.diag([np.exp(-0.5j * h), np.exp(0.5j * h)]), (ix[q],))
    Z = np.diag([1.0, -1.0])
    return [float(np.real(c.psi.local_expectation(Z, ix[q]))) for q in qs]


# ------------------------------------------------------------------------------------------------------- answers

def cmd_answers(a):
    if os.path.exists(a.out):
        raise SystemExit(f"STOP: {a.out} exists")
    strs = strings(a.pairs)
    z, checks = {}, dict(window_L_vs_F=0.0, A0_quimb_vs_free=0.0, total_z_F=0.0)
    t0 = time.time()
    for arm in ARMS:
        for t in TS:
            for name, bits in strs:
                zf = OA.z_free(N, t, bits) if arm == "A0" else OA.z_quimb(N, t, arm, bits, 2048, 1e-10)[0]
                zl = z_cone_quimb(arm, t, bits)
                qs = positions(t, "L")
                zl_by = dict(zip(qs, zl))
                checks["window_L_vs_F"] = max(checks["window_L_vs_F"],
                                              max(abs(zl_by[q] - zf[q]) for q in window(t)))
                checks["total_z_F"] = max(checks["total_z_F"], abs(float(np.sum(zf)) - float(np.sum(1 - 2 * np.array(bits)))))
                if arm == "A0" and name in ("s00", "c00"):
                    zq = OA.z_quimb(N, t, arm, bits, 2048, 1e-10)[0]
                    checks["A0_quimb_vs_free"] = max(checks["A0_quimb_vs_free"], float(np.abs(zq - zf).max()))
                z[tag(arm, t, "F", name)] = [float(x) for x in zf]
                z[tag(arm, t, "L", name)] = [float(x) for x in zl]
        print(f"{arm}: {time.time() - t0:.0f} s", flush=True)
    meta = dict(N=N, K=K, m=M_BIAS, seed=SEED, pairs=a.pairs, cycles=list(TS), arms=list(ARMS),
                strings={n: "".join(map(str, b)) for n, b in strs},
                positions={f"t{t}_{f}": positions(t, f) for t in TS for f in FORMS},
                windows={f"t{t}": window(t) for t in TS}, checks=checks, theta=OA.THETA,
                note="per-qubit <Z> by chain position (the order of meta.positions)")
    json.dump(dict(meta=meta, z=z), open(a.out, "w"), sort_keys=True)
    print(f"checks: window L against F {checks['window_L_vs_F']:.1e}; A0 quimb against free fermions "
          f"{checks['A0_quimb_vs_free']:.1e}; |total Z - initial| (F) {checks['total_z_F']:.1e}")
    print("answers", a.out, "sha256", hashlib.sha256(open(a.out, "rb").read()).hexdigest())


# ---------------------------------------------------------------------------------------------------------- pick

def cmd_pick(a):
    q = json.load(open(a.queue))                 # gpu fetch's queue.json: {"pending": {device: n}, ...}
    pend = q["pending"]
    cands = [d for d in pend if d in ("ibm_fez", "ibm_kingston")]
    if not cands:
        raise SystemExit("STOP: neither ibm_fez nor ibm_kingston in the queue file")
    pick = min(cands, key=lambda d: (int(pend[d]), cands.index(d)))
    print(f"{pick}  (pending: " + ", ".join(f"{d} {pend[d]}" for d in cands) + "; ibm_marrakesh not used)")


# --------------------------------------------------------------------------------------------------------- build

def _pin_light_cone(L, pinned):
    """psf-os's user entrance places each circuit on the first qualifying copy of its pattern (lattice2d.place), so a
    small light-cone pattern lands wherever it first fits (try-build on the 11-22 fez record: the 4-qubit cone at
    drow -4, dcol -8, away from its 40-qubit twin). For this job only, the light-cone items (handed over on F's
    physical qubits) are offered the single copy at shift (0, 0), i.e. those qubits; psf-os's qualification check of
    that copy still runs and the build refuses if it fails. Every other circuit is placed as psf-os places it. psf-os
    itself is not changed (as gpu/hub_build.py's _mirror_from_compiled overrides the mirror for its job)."""
    orig = L.place

    def place(dev, edges, qubits=None, offsets=None):
        if qubits is not None and offsets is None and frozenset(qubits) in pinned:
            return orig(dev, edges, qubits, offsets=[(0, 0)])
        return orig(dev, edges, qubits, offsets)
    L.place = place

def cmd_build(a):
    sys.path.insert(0, HERE)
    import hub_build as HB
    from qiskit import qpy
    from psf_os import device as Dv
    from psf_os import job as J
    from psf_os import lattice2d as L
    from psf_os import user2d as U
    for p in (a.out, a.ans_out):
        if os.path.exists(p):
            raise SystemExit(f"STOP: {p} exists")
    dev = Dv.Device.load(a.dev)
    A = json.load(open(a.ans_in))
    meta = A["meta"]
    strs = strings(meta["pairs"])
    if {n: "".join(map(str, b)) for n, b in strs} != meta["strings"]:
        raise SystemExit("REFUSED: the strings regenerated from the seed differ from the answers file's")
    chain, how = HB.chain_of(dev, N)
    # where psf-os places the 40-qubit pattern: the light-cone twins are handed over on those physical qubits
    probe = HB.on_chain(logical("A1", 1, "F", strs[0][1]), chain, dev.num_qubits)
    lab, edges, _ = U.analyse(probe, dev)
    dr, dc, m, reasons = L.place(dev, edges, lab)
    phys_of_pos = [int(m[chain[k]]) for k in range(N)]
    items, want = [], {}
    for arm in ARMS:
        for t in TS:
            for form in FORMS:
                pos = positions(t, form)
                where = [chain[k] for k in pos] if form == "F" else [phys_of_pos[k] for k in pos]
                for name, bits in strs:
                    tg = tag(arm, t, form, name)
                    items.append((tg, HB.on_chain(logical(arm, t, form, bits), where, dev.num_qubits)))
                    want[tg] = dict(positions=pos, given_labels=where, physical=[phys_of_pos[k] for k in pos])
    HB._mirror_from_compiled(dev, U)
    _pin_light_cone(L, {frozenset(w["given_labels"]) for tg, w in want.items() if "_L_" in tg})
    first = os.path.join(a.out, "unsent_first_build")
    rep = U.build_batch(dev, items, first, shots=a.shots, max_seconds=1e9)
    # the twins' placement: every L item on F's physical qubits at the same chain positions
    bad = []
    for tg, w in want.items():
        got = {str(k): int(v) for k, v in rep["items"][tg]["mapping"].items()}
        phys = [got[str(lb)] for lb in w["given_labels"]]
        if phys != w["physical"]:
            bad.append(tg)
    if bad:
        raise SystemExit(f"STOPPED: psf-os placed {len(bad)} items off F's physical qubits (e.g. {bad[:3]}); the twins "
                         "would not share their qubits. Nothing to submit.")
    # floors and mirrors only for the named items
    floors = set(a.floors or DEFAULT_FLOORS)
    unknown = floors - set(want)
    if unknown:
        raise SystemExit(f"STOP: --floors names unknown items {sorted(unknown)}")
    runs = os.path.join(a.out, "runs")
    unsent = os.path.join(a.out, "unsent_runs")
    shutil.copytree(os.path.join(first, "runs"), runs)
    os.makedirs(unsent)
    for tg in want:
        if tg in floors:
            continue
        for suf in ("_floor", "_mirror"):
            for ext in (".json", ".qpy"):
                p = os.path.join(runs, f"p2d_{tg}{suf}{ext}")
                if os.path.exists(p):
                    shutil.move(p, os.path.join(unsent, os.path.basename(p)))
    man = J.assemble(dev, runs, os.path.join(a.out, "job"), max_seconds=a.max_seconds)
    n_c = len(man["pubs"])
    # compiled checks: CZ as intended, A1 = A2, no delay, measurements last (nothing to park)
    cz, depth, park = {}, {}, {}
    for tg in want:
        c = qpy.load(open(os.path.join(runs, f"p2d_{tg}.qpy"), "rb"))[0]
        cz[tg] = int(c.count_ops().get("cz", 0))
        depth[tg] = int(c.depth(filter_function=lambda i: i.operation.name == "cz"))
        seen_measure, late_gate = set(), False
        for ins in c.data:
            qs = [c.find_bit(q).index for q in ins.qubits]
            if ins.operation.name == "measure":
                seen_measure.update(qs)
            elif any(q in seen_measure for q in qs):
                late_gate = True
        park[tg] = dict(delays=int(c.count_ops().get("delay", 0)), gate_after_measure=late_gate)
    errs = []
    for tg in want:
        arm, tt, form, _ = tg.split("_")
        t = int(tt[1:])
        if cz[tg] != CZ_PER_FSIM[arm] * fsim_count(t, form):
            errs.append(f"{tg}: CZ {cz[tg]}, intended {CZ_PER_FSIM[arm] * fsim_count(t, form)}")
        if park[tg]["delays"] or park[tg]["gate_after_measure"]:
            errs.append(f"{tg}: a delay or a gate after a measurement ({park[tg]})")
        if arm == "A1":
            t2 = "A2" + tg[2:]
            if (cz[tg], depth[tg]) != (cz[t2], depth[t2]):
                errs.append(f"{tg[3:]}: A1 / A2 CZ {cz[tg]} / {cz[t2]}, depth {depth[tg]} / {depth[t2]}")
    if errs:
        raise SystemExit("REFUSED: " + "; ".join(errs[:6]))
    # answers by tag and the record's label
    answers = {}
    for tg, w in want.items():
        answers[tg] = {str(lb): v for lb, v in zip(w["given_labels"], A["z"][tg])}
    with open(a.ans_out, "w") as f:
        json.dump(dict(meta=meta, z=answers), f, indent=1, sort_keys=True)
    sec = charge(n_c, a.shots)
    b = dict(device=dev.name, chain=dict(labels=chain, **how), copy_of_F=dict(drow=dr, dcol=dc, passed_over=reasons),
             items=want, cz=cz, cz_depth=depth, parking=dict(
                 park_default_unchanged=True, delays=sum(p["delays"] for p in park.values()),
                 gates_after_a_measurement=sum(p["gate_after_measure"] for p in park.values()),
                 note="no mid-circuit measurement and no delay in any sent circuit: nothing to park"),
             floors=sorted(floors), shots=a.shots, strings=meta["strings"], pairs=meta["pairs"], cycles=list(TS),
             circuits=n_c, charge_seconds=round(sec, 1), qpu_seconds_model_psf_os=man["qpu_seconds_model"],
             circuits_sha256=man.get("circuits_sha256"))
    json.dump(b, open(os.path.join(a.out, "build.json"), "w"), indent=1)
    print(f"device {dev.name}; chain by rule {how['rule']} ({how.get('shape', how.get('start'))}); F copy drow {dr} "
          f"dcol {dc}; every L item on F's physical qubits")
    for arm in ARMS:
        for t in TS:
            for form in FORMS:
                tg = tag(arm, t, form, "s00")
                print(f"{arm} t {t} {form}: {len(want[tg]['positions'])} qubits, CZ {cz[tg]}, CZ layers {depth[tg]}")
    print(f"floors and mirrors sent for {sorted(floors)}; circuits {n_c}; {a.shots} shots; charge {sec:.1f} s "
          f"(2.6 + 0.000269 x circuits x shots); psf-os model {man['qpu_seconds_model']} s; nothing parked")
    print("answers by label sha256", hashlib.sha256(open(a.ans_out, "rb").read()).hexdigest())


# --------------------------------------------------------------------------------------------------------- check

def cmd_check(a):
    sys.path.insert(0, HERE)
    import hub_check as HK
    b = json.load(open(os.path.join(a.out, "build.json")))
    ans = json.load(open(a.answers))["z"]
    runs = os.path.join(a.out, "runs")
    res, ok, win = {}, True, {}
    t_all = time.time()
    for tg, w in sorted(b["items"].items()):
        rec = json.load(open(os.path.join(runs, f"p2d_{tg}.json")))
        mp = rec["mapping"] if isinstance(rec["mapping"], dict) else ast.literal_eval(rec["mapping"])
        phys = [int(mp[str(lb)]) for lb in w["given_labels"]]
        t0 = time.time()
        z, method = HK.z_of(HK.reduced(HK.load(os.path.join(runs, f"p2d_{tg}.qpy")), phys))
        e = np.array([ans[tg][str(lb)] for lb in w["given_labels"]])
        r = dict(qubits=len(phys), cz=b["cz"][tg], method=method, worst=float(np.abs(z - e).max()))
        good = r["worst"] < 1e-6
        if tg in b["floors"]:
            zm, _ = HK.z_of(HK.reduced(HK.load(os.path.join(runs, f"p2d_{tg}_mirror.qpy")), phys))
            r["mirror_worst"] = float(np.abs(zm - 1.0).max())
            good &= r["mirror_worst"] < 1e-6
        arm, tt, form, name = tg.split("_")
        t = int(tt[1:])
        win[tg] = {p: float(z[i]) for i, p in enumerate(w["positions"]) if p in window(t)}
        r["ok"], r["seconds"] = bool(good), round(time.time() - t0, 1)
        ok &= good
        res[tg] = r
        print(f"{tg}: {r['qubits']} qubits, CZ {r['cz']}; {method}: worst {r['worst']:.1e}"
              + (f", mirror {r['mirror_worst']:.1e}" if "mirror_worst" in r else "") + f" {'PASS' if good else 'FAIL'}",
              flush=True)
    twins = 0.0
    for tg in win:
        if "_L_" in tg:
            f = tg.replace("_L_", "_F_")
            twins = max(twins, max(abs(win[tg][p] - win[f][p]) for p in win[tg]))
    ok &= twins < 1e-6
    res["twins_window_worst"] = twins
    res["ALL"] = "PASS" if ok else "FAIL"
    res["seconds"] = round(time.time() - t_all, 1)
    json.dump(res, open(os.path.join(a.out, "check.json"), "w"), indent=1)
    print(f"twins' windows (compiled, noise-free): worst {twins:.1e}")
    print("ALL", res["ALL"], f"({res['seconds']} s)")


# --------------------------------------------------------------------------------------------------------- score

def _z_from_counts(counts, rec_labels, labels_in_order):
    k_of = {lb: k for k, lb in enumerate(rec_labels)}
    tot = sum(counts.values())
    z = np.zeros(len(labels_in_order))
    for key, c in counts.items():
        s = key.replace(" ", "")
        z += c * np.array([1 - 2 * int(s[-1 - k_of[lb]]) for lb in labels_in_order])
    return z / tot


def cmd_score(a):
    from psf_os import job as J
    from psf_os import sentinel
    from psf_os import user2d as U
    b = json.load(open(os.path.join(a.out, "build.json")))
    ans = json.load(open(a.answers))["z"]
    runs, jobd = os.path.join(a.out, "runs"), os.path.join(a.out, "job")
    read = J.read(jobd, runs)
    zz, floor, mirror = {}, {}, {}
    for name, (rec, cc) in read.items():
        kind = rec.get("psfos_job", {}).get("kind")
        if kind not in ("user2d", "user2d_floor", "user2d_mirror"):
            continue
        tg = U._tag_of(name, rec)
        w = b["items"][tg]
        z = _z_from_counts(cc[(rec["points"][0]["input"], "z")], rec["labels"],
                           [lb for lb in w["given_labels"]])
        if kind == "user2d":
            zz[tg] = z
        elif kind == "user2d_floor":
            floor[tg] = float(z.mean())
        else:
            mirror[tg] = float(z.mean())
    strs = b["strings"]
    ks = sorted({n[1:] for n in strs})

    def m_w(tg, which):
        w = b["items"][tg]
        t = int(tg.split("_")[1][1:])
        idx = [i for i, p in enumerate(w["positions"]) if p in window(t)]
        v = zz[tg] if which == "device" else np.array([ans[tg][str(lb)] for lb in w["given_labels"]])
        bits = strs[tg.split("_")[3]]
        m0 = sum(int(bits[w["positions"][i]]) for i in idx)
        return float(((1 - v[idx]) / 2).sum() - m0)

    res = dict(device=b["device"], cells={}, twins={}, order={}, beside={})
    for arm in ARMS:
        for t in TS:
            for form in FORMS:
                tags = [tag(arm, t, form, n) for n in sorted(strs)]
                d = np.array([m_w(x, "device") - m_w(x, "exact") for x in tags])
                ex = np.array([m_w(x, "exact") for x in tags])
                wd = np.array([(m_w(tag(arm, t, form, "s" + k), "device") - m_w(tag(arm, t, form, "c" + k), "device")) / 2
                               for k in ks])
                we = np.array([(m_w(tag(arm, t, form, "s" + k), "exact") - m_w(tag(arm, t, form, "c" + k), "exact")) / 2
                               for k in ks])
                rM, rW = float(np.mean(d ** 2) / np.mean(ex ** 2)), float(np.mean((wd - we) ** 2) / np.mean(we ** 2))
                res["cells"][f"{arm}_t{t}_{form}"] = dict(
                    M_ratio=rM, M="READS" if rM <= 0.5 else "DOES NOT READ", W_ratio=rW,
                    W="READS" if rW <= 0.5 else "DOES NOT READ", W_device=float(wd.mean()), W_exact=float(we.mean()),
                    S_device=float(np.mean([m_w(tag(arm, t, form, "s" + k), "device") +
                                            m_w(tag(arm, t, form, "c" + k), "device") for k in ks])),
                    errors=d.tolist())
            eL = np.array(res["cells"][f"{arm}_t{t}_L"]["errors"])
            eF = np.array(res["cells"][f"{arm}_t{t}_F"]["errors"])
            delta = eF ** 2 - eL ** 2
            mean, se = float(delta.mean()), float(delta.std(ddof=1) / np.sqrt(len(delta)))
            res["twins"][f"{arm}_t{t}"] = dict(
                mse_F_minus_mse_L=mean, se=se,
                verdict="KEEPS MORE" if mean > 2 * se else ("KEEPS LESS" if mean < -2 * se else "SAME"))
    for form in FORMS:
        w3 = [res["cells"][f"{arm}_t3_{form}"]["W_device"] for arm in ARMS]
        res["order"][form] = "yes" if w3[0] > w3[1] > w3[2] else "no"
        for arm in ARMS:
            c1, c3 = res["cells"][f"{arm}_t1_{form}"], res["cells"][f"{arm}_t3_{form}"]
            res["beside"][f"{arm}_{form}_W3_over_W1"] = dict(device=c3["W_device"] / c1["W_device"],
                                                            exact=c3["W_exact"] / c1["W_exact"])
    res["beside"]["floor_mean"] = floor
    res["beside"]["mirror_mean"] = mirror
    res["beside"]["sentinel"] = sentinel.verdict(jobd, runs)["status"]
    json.dump(res, open(os.path.join(a.out, "scores.json"), "w"), indent=1)
    for k, c in res["cells"].items():
        print(f"{k}: window M {c['M']} ({c['M_ratio']:.3f}); W {c['W']} ({c['W_ratio']:.3f}); beside W {c['W_device']:.3f} "
              f"(exact {c['W_exact']:.3f}), S {c['S_device']:+.3f}")
    for k, v in res["twins"].items():
        print(f"twins {k}: the light-cone circuit {v['verdict']} (MSE F - MSE L {v['mse_F_minus_mse_L']:+.4f}, "
              f"SE {v['se']:.4f})")
    print(f"order of W at t = 3 (A0 > A1 > A2): L {res['order']['L']}, F {res['order']['F']}")


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("answers")
    p.add_argument("out")
    p.add_argument("--pairs", type=int, default=7)
    p = sp.add_parser("pick")
    p.add_argument("queue")
    p = sp.add_parser("build")
    p.add_argument("dev")
    p.add_argument("out")
    p.add_argument("ans_in")
    p.add_argument("ans_out")
    p.add_argument("--shots", type=int, default=1000)
    p.add_argument("--floors", nargs="*", default=None, help=f"items with floor and mirror (default {DEFAULT_FLOORS})")
    p.add_argument("--max-seconds", type=float, default=60, help="psf-os's own model limit for the assembled job")
    p = sp.add_parser("check")
    p.add_argument("out")
    p.add_argument("answers")
    p = sp.add_parser("score")
    p.add_argument("out")
    p.add_argument("answers")
    a = ap.parse_args()
    dict(answers=cmd_answers, pick=cmd_pick, build=cmd_build, check=cmd_check, score=cmd_score)[a.cmd](a)


if __name__ == "__main__":
    main()
