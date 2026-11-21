"""Should psf-os fence the RUS chains, and park their likely-|1> waiting qubits? (draft for a declaration; home VS Claude,
2026-11-21 night; home instruction "RUS の鎖の柵の実機試験の準備" with its additions 1 and 2; desk, no device).

Per RUS item, three forms of one circuit side by side in one job (copies a, b, ...):
  D  psf-os 0.3.0's default (the chains have nothing to park: no fence, no X)
  F  fenced: fence_waits(conditionals=True)
  M  F and, at every wait, an X before and after on each waiting qubit (neither measured there nor inside its
     conditionals) whose noiseless probability of |1>, over the branches with their weights, is above 0.5 ("park the
     likely value"; entangled qubits included). X X = I across a wait the qubit takes no part in: the action is the same.
Two differences, read as the loop reads g (|P - exact|, nearer is better): the fence's, F - D; parking's, M - F.
Beside, in the same night (addition 2, A): a control, IPE n = 4 at 4 phases parked (0.3.0's default) and unparked
(park_skip), +0.035 on both earlier nights; and the repetition code's F10, F6P, F6 at its four errors.

Everything runs on the released psf-os 0.3.0 (v0.3.0): the fence by footprint.fence_waits, the X here in the tool, the
noiseless state by footprint's own branching. The declared tools are imported read only. The device: not marrakesh;
of ibm_fez and ibm_kingston the one with the shorter queue in daily_fetch's queue.json (pick_device).

  python gpu/rus_fence_night.py table OUT.json
  python gpu/rus_fence_night.py pick FETCH_IN                      the device by the rule
  python gpu/rus_fence_night.py build DEVDIR OUT --plan P [--dry-clifford-sentinel]
  python gpu/rus_fence_night.py check OUT
  python gpu/rus_fence_night.py dry OUT NOISE [--seed S]           ILLUSTRATIVE noise only: wait | cond | phase
  python gpu/rus_fence_night.py score OUT
"""
import argparse
import contextlib
import io
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
for d in ("notes/ffapps_2026-11-17", "notes/rus_coherent_2026-11-17", "notes/os2_2026-11-18"):
    sys.path.insert(0, os.path.join(NB, d))

THETA = 1.1
MAX_S = 60.0
SENT = 4
SEED = 20261124
IPE_PHASES = (2, 6, 10, 14)        # n = 4 phases of the paired subset of 2026-11-21 that keep all 8 CZ when compiled
REP_FORMS = ("F10", "F6P", "F6")
# illustrative noises (never fitted): the weekend's two types and a third, a coherent phase while a neighbour is read
NOISES = {"wait": dict(gamma=0.06), "cond": dict(dephase_cond=0.05), "phase": dict(read_phase=0.15)}

# RUS items: key -> (prescription, m, L)
RUS = {"p0l3": ("P0", 3, 3), "p3l3": ("P3", 2, 3), "nfl3m3": ("NF", 3, 3), "nfl3m2": ("NF", 2, 3),
       "p2l3m3": ("P2", 3, 3), "p0l2": ("P0", 3, 2)}

# plans [OWNER]: per job, the shots and its contents; RUS copies per item (notes/rus_fence_2026-11-21: the copies
# follow the desk's expected differences: NF, whose parking difference is large, fewer; P0 and P2, whose fence
# difference is the smaller, more)
PLANS = {
    "alpha-one-job": [dict(shots=1950, rus={"nfl3m3": 2, "p0l3": 5, "p2l3m3": 5}, ipe=True, rep=True)],
    "beta-two-jobs": [dict(shots=4000, rus={"nfl3m3": 2, "p0l3": 5, "p2l3m3": 5, "p3l3": 2}, ipe=False, rep=False),
                      dict(shots=1950, rus={}, ipe=True, rep=True)],
    "gamma-one-job": [dict(shots=1950, rus={"nfl3m3": 3, "p0l3": 7, "p2l3m3": 7, "p3l3": 3}, ipe=True, rep=True)],
}


def qpu_seconds(n, shots):
    return n * 0.036 + n * shots * 0.00027 + 3.0


# ------------------------------------------------------------------------------------------------ circuits

def rus_circuit(presc, m, L):
    from psf_os import feedforward as FF
    import rus2_night as R2
    import rus3_night as R3
    if presc == "P0":
        return FF.rus_chain(L, THETA, m=3)
    if presc == "P3":
        return FF.rus_chain(L, THETA, m=2)
    if presc == "P1":
        return R2.flip_chain(L, THETA, m=m)
    if presc == "NF":
        return R2.flip_chain(L, THETA, m=m, flip=False)
    if presc == "P2":
        return R3.chain(L, THETA, m=m)
    raise ValueError(presc)


def reads_one(presc):
    return presc != "P2"           # P2 reads its output flipped


def majority(low):
    """(circuit, list): fence_waits(low, conditionals=True) with an X before each wait's fence and after its closing
    fence on every waiting qubit whose probability of |1> (noiseless, over the branches with their weights) is above
    0.5. Built with psf-os 0.3.0's footprint (its waits and branching). The noiseless distribution is checked."""
    from psf_os.footprint import _reduced, _simulate, _windows, exact_distribution, fence_waits
    f = fence_waits(low, conditionals=True)
    wins = _windows(f)
    if not wins:
        return f, []
    _, sim = _simulate(f, [w["start"] for w in wins])
    act, pos = sim["act"], sim["pos"]
    n = len(act)
    plan, chosen = [], []
    for i, w in enumerate(wins):
        flip = []
        for q in act:
            if q in w["involved"]:
                continue
            p1 = sum(p * float(_reduced(sv.data, pos[q], n)[1, 1].real) for p, sv, _ in sim["at"][w["start"]])
            if p1 > 0.5 + 1e-9:
                flip.append(q)
                chosen.append(dict(wait=i, kind=w["kind"], qubit=q, p1=round(p1, 6)))
        plan.append((w, flip))
    before = {w["start"]: fl for w, fl in plan if fl}
    after = {w["end"]: (w, fl) for w, fl in plan if fl}
    out = f.copy_empty_like()
    for i, ins in enumerate(f.data):
        for q in before.get(i, ()):
            out.x(q)
        out.append(ins.operation, ins.qubits, ins.clbits)
        if i in after:
            w, fl = after[i]
            if not w["close"]:
                out.barrier(list(out.qubits))
            for q in fl:
                out.x(q)
    d0, d1 = exact_distribution(low), exact_distribution(out)
    if any(abs(d0.get(k, 0) - d1.get(k, 0)) > 1e-9 for k in set(d0) | set(d1)):
        raise ValueError("the majority X changed the noiseless distribution")
    return out, chosen


def forms(key):
    from psf_os import feedforward as FF
    from psf_os.footprint import fence_waits
    presc, m, L = RUS[key]
    qc, spec = rus_circuit(presc, m, L)
    low = FF.lower(qc)
    mm, chosen = majority(low)
    return dict(D=low, F=fence_waits(low, conditionals=True), M=mm), spec, chosen


def job_items(job):
    """[(tag, circuit, spec, parked)] of one job; parked False means park_skip (built as given)."""
    out, meta = [], {}
    for key, copies in job["rus"].items():
        fm, spec, chosen = forms(key)
        meta[key] = dict(majority_x=chosen)
        for cp in "abcdefgh"[:copies]:
            for k in ("D", "F", "M"):
                out.append((f"{key}{k}{cp}", fm[k], spec, False))
    if job["ipe"]:
        import apps as AP
        for j in IPE_PHASES:
            qc, succ = AP.ipe(4, j, True)
            off, _ = AP.ipe(4, j, False)
            sp = dict(success=succ, off_circuit=off, form="blocks")
            out.append((f"ipk4_{j}", qc, sp, True))
            out.append((f"ipu4_{j}", qc, sp, False))
    if job["rep"]:
        import repcode4_night as RC
        for e in RC.ERRORS:
            for f in REP_FORMS:
                qc, succ = RC.circuit(f, e)
                off, _ = RC.circuit(f, e, lookup=False)
                out.append((f"{f.lower()}_{e}", qc, dict(success=succ, off_circuit=off), False))
    return out, meta


# ------------------------------------------------------------------------------------------------ sizes and copies

def size(plan):
    rows = []
    for job in PLANS[plan]:
        n = 3 * sum(job["rus"].values()) + (8 if job["ipe"] else 0) + (12 if job["rep"] else 0) + SENT
        rows.append(dict(shots=job["shots"], circuits=n, seconds=round(qpu_seconds(n, job["shots"]), 1),
                         rus=job["rus"], ipe=job["ipe"], rep=job["rep"]))
    return dict(plan=plan, jobs=rows, seconds=round(sum(r["seconds"] for r in rows), 1),
                circuits=sum(r["circuits"] for r in rows))


def two_se(p, shots, copies):
    """2 SE of a difference of two forms' shares, each pooled over `copies` circuits."""
    return 2 * math.sqrt(2 * p * (1 - p) / (shots * copies))


def copies_for(d, p, shots, z=2 + 0.84):
    """Copies per form so that a difference d is seen at 2 SE with about 80 % power."""
    return max(1, math.ceil(2 * z * z * p * (1 - p) / (shots * d * d)))


# ------------------------------------------------------------------------------------------------ build, check

def pick_device(fetch_in):
    """The rule (addition 2, B): not ibm_marrakesh; of the others in queue.json, the one with the fewest pending jobs
    (ties: the first in queue.json's 'chosen' order) whose record fetch_in/<device>/dev exists."""
    q = json.load(open(os.path.join(fetch_in, "queue.json")))
    pend = q["pending"]
    order = [d for d in q.get("chosen", list(pend)) if d != "ibm_marrakesh" and d in pend
             and os.path.isdir(os.path.join(fetch_in, d, "dev"))]
    if not order:
        raise SystemExit("no device other than ibm_marrakesh with a record in " + fetch_in)
    return min(order, key=lambda d: (pend[d], order.index(d)))


def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    dev = Device.load(a.devdir)
    if dev.name == "ibm_marrakesh":
        raise SystemExit("REFUSED: the rule runs this test off ibm_marrakesh (pick_device)")
    if os.path.exists(a.out):
        raise SystemExit(f"{a.out} exists (nothing is overwritten)")
    os.makedirs(a.out)
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None   # dry runs only, never a device
    info = dict(plan=a.plan, device=dev.name, jobs=[])
    for k, job in enumerate(PLANS[a.plan]):
        its, meta = job_items(job)
        jd = os.path.join(a.out, f"job{k}")
        tags = [t for t, *_ in its]
        skip = [t for t, _c, _s, parked in its if not parked]
        rep = FF.build(dev, [(t, c, s) for t, c, s, _ in its], jd, shots=job["shots"], max_seconds=MAX_S,
                       sentinel_spec=spec, ff_only=tags, park=True, park_skip=skip, footprint=True)
        json.dump(dict(part=f"rusfence:{a.plan}:{k}", shots=job["shots"], tags=tags, majority=meta),
                  open(os.path.join(jd, "part.json"), "w"), indent=1)
        info["jobs"].append(dict(folder=f"job{k}", shots=job["shots"], circuits=rep["circuits"],
                                 qpu_seconds_model=rep["qpu_seconds_model"], majority=meta))
        print(f"job{k}: {rep['circuits']} circuits at {job['shots']} shots, {rep['qpu_seconds_model']:.1f} s")
    info["qpu_seconds_model"] = round(sum(j["qpu_seconds_model"] for j in info["jobs"]), 1)
    json.dump(info, open(os.path.join(a.out, "plan.json"), "w"), indent=1)
    print(f"{len(info['jobs'])} jobs, {info['qpu_seconds_model']:.1f} s by the model on {dev.name}")


def _compiled(jd):
    """{tag: compiled ff circuit} of a built job."""
    from qiskit import qpy
    man = json.load(open(os.path.join(jd, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(jd, "job", "circuits.qpy"), "rb"))
    cells = {c["cell"]: c for c in man["cells"]}
    return {cells[p["cell"]]["name"][3:]: cs[i] for i, p in enumerate(man["pubs"])
            if cells[p["cell"]]["role"] == "user"}, man


def check(a):
    """Per RUS item: the three forms' noiseless distributions equal (as written and as compiled, the compiled one
    branching over the active qubits), compiled CZ equal, the fence kept in F and M (barriers on every active qubit at
    every wait), M's X kept by the compiler (X or its one-qubit equivalent on the chosen qubits: counted as one-qubit
    gates more than F); the controls by their declared checks (qpe_repro_night.check, repcode4_night.check); the
    manifest's psf_os_build (version 0.3.0, park True, explicit)."""
    from psf_os import feedforward as FF
    from psf_os.footprint import exact_distribution
    info = json.load(open(os.path.join(a.out, "plan.json")))
    lines, ok_all = [], True
    for j in info["jobs"]:
        jd = os.path.join(a.out, j["folder"])
        comp, man = _compiled(jd)
        b = man.get("psf_os_build", {})
        okb = b.get("version") == "0.3.0" and b.get("park") is True and b.get("park_set") == "explicit"
        lines.append(f"{j['folder']}: psf_os_build {b} {'ok' if okb else 'NOT AS DECLARED'}")
        ok_all &= okb
        keys = sorted({t[:-2] for t in comp if t[-2] in "DFM" and t[:-2] in RUS})
        for key in keys:
            cp = "a"
            cs = {k: comp[f"{key}{k}{cp}"] for k in "DFM"}
            act = sorted({cs["D"].find_bit(q).index for ins in cs["D"].data for q in ins.qubits
                          if ins.operation.name != "barrier"})
            dist = {k: exact_distribution(FF.compact(c)) for k, c in cs.items()}
            same = all(all(abs(dist["D"].get(x, 0) - dist[k].get(x, 0)) < 1e-9 for x in set(dist["D"]) | set(dist[k]))
                       for k in "FM")
            czs = {k: FF.cz_count(c) for k, c in cs.items()}
            bars = {k: sum(1 for ins in c.data if ins.operation.name == "barrier" and
                           len({c.find_bit(q).index for q in ins.qubits} & set(act)) == len(act)) for k, c in cs.items()}
            one_q = {k: sum(1 for nm, _ in FF.walk(c) if nm in ("x", "sx", "rz")) for k, c in cs.items()}
            n_x = len(j["majority"][key]["majority_x"])
            ok = same and len(set(czs.values())) == 1 and bars["F"] > 0 and bars["M"] >= bars["F"] and \
                (n_x == 0 or one_q["M"] > one_q["F"])
            ok_all &= ok
            lines.append(f"  {key}: compiled distributions equal {same}; CZ {czs}; full fences {bars}; one-qubit "
                         f"gates {one_q}; majority X {2 * n_x} -> {'ok' if ok else 'FAIL'}")
        for chk in ("ipe", "rep"):
            if not any(t.startswith("ipk" if chk == "ipe" else "f6_") for t in comp):
                continue
            ok = _control_check(jd, chk)
            ok_all &= ok
            lines.append(f"  control {chk}: its declared check {'PASS' if ok else 'FAIL'}")
    lines.append("PASS" if ok_all else "FAIL")
    print("\n".join(lines))
    open(os.path.join(a.out, "check.txt"), "w").write("\n".join(lines) + "\n")
    return ok_all


def _control_check(jd, which):
    """The control's declared check on a view of the job that holds only its cells (and the sentinel)."""
    import shutil
    from qiskit import qpy
    from psf_os import job as J
    man = json.load(open(os.path.join(jd, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(jd, "job", "circuits.qpy"), "rb"))
    pre = ("ipk4_", "ipu4_") if which == "ipe" else tuple(f"{f.lower()}_" for f in REP_FORMS)
    keep = {c["cell"] for c in man["cells"] if c["role"] == "sentinel" or c["name"][3:].startswith(pre)}
    vd = os.path.join(jd, "views", which)
    if os.path.exists(vd):
        shutil.move(vd, vd + "_old")
    os.makedirs(os.path.join(vd, "job"))
    os.makedirs(os.path.join(vd, "runs"))
    cells, pubs, circs, idx = [], [], [], {}
    for c in man["cells"]:
        if c["cell"] in keep:
            idx[c["cell"]] = len(cells)
            cells.append(dict(c, cell=len(cells)))
            r = os.path.join(jd, "runs", c["name"] + ".json")
            shutil.copy(r, os.path.join(vd, "runs"))
            shutil.copy(os.path.join(jd, "runs", json.load(open(r))["export"]["qpy"]), os.path.join(vd, "runs"))
    for k, p in enumerate(man["pubs"]):
        if p["cell"] in keep:
            pubs.append(dict(cell=idx[p["cell"]], point=p["point"]))
            circs.append(cs[k])
    with open(os.path.join(vd, "job", "circuits.qpy"), "wb") as f:
        qpy.dump(circs, f)
    json.dump(dict(man, cells=cells, pubs=pubs, roles={c["name"]: c["role"] for c in cells},
                   circuits_sha256=J.sha256_file(os.path.join(vd, "job", "circuits.qpy"))),
              open(os.path.join(vd, "job", "manifest.json"), "w"), indent=1)
    shots = man["shots"]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        if which == "rep":
            import repcode4_night as RC
            json.dump(dict(shots=shots, qpu_seconds_model=man["qpu_seconds_model"]),
                      open(os.path.join(vd, "part.json"), "w"))
            # repcode4_night.check walks the four forms' ideals; F16 is not sent here, its cells simply absent
            return bool(RC.check(argparse.Namespace(out=vd)))
        import apps as AP
        import qpe_repro_night as Q
        spec = {}
        for j in IPE_PHASES:
            qc, succ = AP.ipe(4, j, True)
            off, _ = AP.ipe(4, j, False)
            spec[f"ipk4_{j}"] = spec[f"ipu4_{j}"] = dict(success=succ, off_circuit=off, form="blocks")
        json.dump(dict(part="rusfence-ipe", shots=shots), open(os.path.join(vd, "part.json"), "w"))
        saved = Q._spec_by_tag
        Q._spec_by_tag = lambda _p: spec
        try:
            return bool(Q.check(argparse.Namespace(out=vd, verbose=False)))
        finally:
            Q._spec_by_tag = saved


# ------------------------------------------------------------------------------------------------ dry, score

def noisy(cc, noise):
    """The illustrative noises on a compiled-for-simulation circuit: damping after each read group on the other
    qubits (branch_noise), dephasing after each conditional (cond_noise), or a coherent RZ(read_phase) after each read
    group on the other qubits (a phase picked up while a neighbour is read: written here, never fitted)."""
    import branch_noise as BN
    import cond_noise as CN
    out = BN.noisy_circuit(cc, float(noise.get("gamma", 0.0)))
    out = CN.dephase_conditionals(out, float(noise.get("dephase_cond", 0.0)))
    phi = float(noise.get("read_phase", 0.0))
    if not phi:
        return out
    res = out.copy_empty_like()
    group = []

    def flush():
        if group:
            for q in res.qubits:
                if q not in group:
                    res.rz(phi, q)
            group.clear()
    for ins in out.data:
        if ins.operation.name != "measure":
            flush()
        res.append(ins.operation, ins.qubits, ins.clbits)
        if ins.operation.name == "measure":
            group.append(ins.qubits[0])
    flush()
    return res


def dry(a):
    """Every job's circuits under one illustrative noise (density matrix), written as raw counts (local, marked)."""
    from qiskit import qpy, transpile
    from qiskit_aer import AerSimulator
    from psf_os import feedforward as FF
    info = json.load(open(os.path.join(a.out, "plan.json")))
    noise = NOISES[a.noise]
    sim = AerSimulator(method="density_matrix")
    for k, j in enumerate(info["jobs"]):
        jd = os.path.join(a.out, j["folder"])
        man = json.load(open(os.path.join(jd, "job", "manifest.json")))
        cs = qpy.load(open(os.path.join(jd, "job", "circuits.qpy"), "rb"))
        role = {c["cell"]: c["role"] for c in man["cells"]}
        stab = AerSimulator(method="stabilizer")
        rows = []
        for i, c in enumerate(cs):
            cc = FF.compact(c)
            if role[man["pubs"][i]["cell"]] == "sentinel":
                # the dry Clifford sentinel (40 qubits): noiseless, by the stabilizer method; never judged here
                from psf_os.sim import to_clifford_gates
                cnt = stab.run(to_clifford_gates(cc), shots=man["shots"], seed_simulator=a.seed + i).result().get_counts()
                rows.append(dict(pub=i, counts=cnt))
                continue
            t = transpile(cc, basis_gates=["cz", "rz", "sx", "x"], optimization_level=0, seed_transpiler=0)
            cnt = sim.run(noisy(t, noise), shots=man["shots"], seed_simulator=a.seed + 1000 * i + 10 ** 6 * k
                          ).result().get_counts()
            rows.append(dict(pub=i, counts=cnt))
        json.dump(dict(job_id=f"local-illustrative-{a.noise}", local=True, backend=man["fetch"]["backend"],
                       noise=noise), open(os.path.join(jd, "job", "submission.json"), "w"))
        json.dump(dict(job_id=f"local-illustrative-{a.noise}", status="DONE", rows=rows, noise=noise,
                       note="ILLUSTRATIVE noise, never fitted"), open(os.path.join(jd, "job", "raw_counts.json"), "w"))


def word(d, se):                    # [OWNER] (the words of C)
    if d >= 2 * se and d > 0:
        return "KEEPS MORE"
    if d <= -2 * se and d < 0:
        return "KEEPS LESS"
    return "SAME WITHIN ERROR"


def score(a):
    from psf_os import feedforward as FF
    from psf_os import job as J
    info = json.load(open(os.path.join(a.out, "plan.json")))
    cards, jobs_of = {}, {}
    for j in info["jobs"]:
        jd = os.path.join(a.out, j["folder"])
        read = J.read(os.path.join(jd, "job"), os.path.join(jd, "runs"))
        for _n, (rec, cc) in read.items():
            if rec.get("psfos_job", {}).get("kind", "").startswith(FF.KIND) and rec.get("ff_arm") == "ff":
                cards[rec["tag"]] = (rec, cc[("f", "z")])
                jobs_of[rec["tag"]] = j["folder"]
    lines, res = [], {}
    say = lambda s: (print(s), lines.append(s))
    for key in RUS:
        tags = {k: sorted(t for t in cards if t[:-1] == f"{key}{k}") for k in "DFM"}
        if not tags["D"]:
            continue
        assert len({jobs_of[t] for k in "DFM" for t in tags[k]}) == 1, f"{key}: forms split across jobs"
        presc = RUS[key][0]
        P = {}
        for k in "DFM":
            ok = N = 0
            for t in tags[k]:
                rec, cnt = cards[t]
                ob, n = rec["rus"]["out_bit"], rec["clbits"]
                want = "1" if reads_one(presc) else "0"
                ok += sum(v for kk, v in cnt.items() if kk.replace(" ", "")[-1 - ob] == want)
                N += sum(cnt.values())
            P[k] = (ok / N, N)
        ex = cards[tags["D"][0]][0]["rus"]["exact"]
        out = {}
        for name, (x, y) in (("fence F - D", ("F", "D")), ("park M - F", ("M", "F"))):
            (px, nx), (py, ny) = P[x], P[y]
            g = abs(py - ex) - abs(px - ex)
            se = math.sqrt(px * (1 - px) / nx + py * (1 - py) / ny)
            out[name] = dict(g=g, two_se=2 * se, word=word(g, se))
        res[key] = dict(P={k: v[0] for k, v in P.items()}, exact=ex, **out)
        say(f"{key}: P D {P['D'][0]:.4f} F {P['F'][0]:.4f} M {P['M'][0]:.4f} (exact {ex:.4f}); "
            + "; ".join(f"{n} {v['g']:+.4f} (2 SE {v['two_se']:.4f}) {v['word']}" for n, v in out.items()))
    # the controls
    ipk = [t for t in cards if t.startswith("ipk4_")]
    if ipk:
        def pool(ts):
            ok = N = 0
            for t in ts:
                rec, cnt = cards[t]
                succ = {int(b): v for b, v in rec["success"].items()}
                s = FF.success_share(cnt, rec["clbits"], succ)
                ok += s["success"]
                N += s["counted"]
            return ok / N, N
        (pk, nk), (pu, nu) = pool(ipk), pool([t.replace("ipk", "ipu") for t in ipk])
        se = math.sqrt(pk * (1 - pk) / nk + pu * (1 - pu) / nu)
        res["control_ipe"] = dict(parked=pk, unparked=pu, d=pk - pu, two_se=2 * se, word=word(pk - pu, se))
        say(f"control IPE n = 4 at {sorted(int(t[5:]) for t in ipk)}: parked {pk:.4f} - unparked {pu:.4f} = "
            f"{pk - pu:+.4f} (2 SE {2 * se:.4f}) {word(pk - pu, se)}")
        rep = {}
        import repcode4_night as RC
        for f in REP_FORMS:
            rep[f] = pool([f"{f.lower()}_{e}" for e in RC.ERRORS])
        for name, (x, y) in (("footprint F6P - F10", ("F6P", "F10")), ("CZ F6 - F6P", ("F6", "F6P"))):
            (px, nx), (py, ny) = rep[x], rep[y]
            se = math.sqrt(px * (1 - px) / nx + py * (1 - py) / ny)
            say(f"repetition code {name}: {px - py:+.4f} (2 SE {2 * se:.4f}) {word(px - py, se)}")
        p6, n6 = rep["F6"]
        s6 = math.sqrt(p6 * (1 - p6) / n6)
        say(f"repetition code F6 {p6:.4f} (2 SE {2 * s6:.4f}) -> "
            f"{'BEYOND THE CEILING' if p6 >= 0.875 + 2 * s6 else 'NOT BEYOND'}")
    json.dump(res, open(os.path.join(a.out, "rusfence_scores.json"), "w"), indent=1)
    open(os.path.join(a.out, "score.txt"), "w").write("\n".join(lines) + "\n")


def table(a):
    rows = [size(p) for p in PLANS]
    json.dump(rows, open(a.out, "w"), indent=1)
    for r in rows:
        print(f"{r['plan']:14s} {r['circuits']:4d} circuits {r['seconds']:6.1f} s: " +
              "; ".join(f"{j['circuits']} circuits at {j['shots']} ({j['seconds']} s)" for j in r["jobs"]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("table").add_argument("out")
    sub.add_parser("pick").add_argument("fetch_in")
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    b.add_argument("--plan", required=True, choices=sorted(PLANS))
    b.add_argument("--dry-clifford-sentinel", action="store_true")
    sub.add_parser("check").add_argument("out")
    d = sub.add_parser("dry")
    d.add_argument("out")
    d.add_argument("noise", choices=sorted(NOISES))
    d.add_argument("--seed", type=int, default=SEED)
    sub.add_parser("score").add_argument("out")
    a = ap.parse_args()
    if a.cmd == "pick":
        print(pick_device(a.fetch_in))
        sys.exit(0)
    r = {"table": table, "build": build, "check": check, "dry": dry, "score": score}[a.cmd](a)
    sys.exit(0 if r is not False else 1)
