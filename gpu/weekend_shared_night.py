"""The weekend's three candidates in as few jobs as one night needs (home VS Claude, 2026-11-21; home instruction
"週末の 3 候補を相乗りさせ、秒数を節約する案"; a desk tool, not declared). The candidates' tools are imported read
only and unchanged; their items, checks and scores are theirs:

  A  gpu/repcode4_night.py   the repetition code's four forms (F16 F10 F6P F6 x errors n 0 1 2)
  B  gpu/qpe_long_night.py   IPE at n = 4, 5, 6 (plan shape), or n = 5 (plans n5, n5ipe), n5n6
  C  gpu/ipe_park_night.py   IPE n = 4 sent three ways (pl fe pk)

A night is a selection of their items, one shot count, and a layout. Items are packed in order into the fewest jobs
of at most 60 s by the project's time model (psf_os.job.qpu_seconds: 0.036 s per circuit + 0.00027 s per circuit-shot
+ 3 s per job). psf-os puts one ring sentinel in every job it builds (FF.build); none of A, B, C has a readout probe.
psf-os refuses a job whose records hold different shot counts, so one night has one shot count per job.

Cuts (each optional; none changes a circuit, a ceiling, a word or a threshold of a candidate):
  --a-forms      A's forms (F16 is 2026-11-19's circuit with a barrier; it is read only beside, F10 - F16)
  --b-plan       B's plan: shape | n5 | n5ipe (n = 5, IPE only) | n5n6
  --b-n4-from-c  B's IPE n = 4 items are C's pl items (the same circuit: AP.ipe(4, j) and its off arm; with B
                 --b-fence, C's fe items, fence_waits(conditionals=True) as B's fence). B and C then share their chain.
  --c-forms      C's forms
  --c-shared-fixed  C's fe and pk get their ff arm only: their off arm is the plain off arm, the same circuit as pl's
                 off arm (ipe_park_night: "the same off arm"); their floor is the ff circuit's floor (psf-os ff_only)
  --ff-only      every item's ff arm only (no off, no floor). No candidate's verdict reads off or floor (every
                 verdict pools ff success; every ceiling is exact); off and floor are beside. Needs psf-os with
                 build(ff_only=...) (loop-paired-2026-11-21, a164fc5)
Layout:
  --layout apart (as the home instruction): each group of candidates on its own qubits, at coupler distance >= 3 from
                 the other groups; the first group keeps rule C (the candidates' own placement)
  --layout own   every candidate on its own rule-C placement, as in its single job (the jobs' circuits run one after
                 another; two circuits of one job never run at the same time)

  python gpu/weekend_shared_night.py size  [selection]                     circuits, jobs, seconds (no compile)
  python gpu/weekend_shared_night.py table OUT.json                        the table of cuts (no compile)
  python gpu/weekend_shared_night.py build DEVDIR OUT [selection] [--dry-clifford-sentinel]
  python gpu/weekend_shared_night.py check OUT                             every candidate's own check, per job
  python gpu/weekend_shared_night.py same OUT DEVDIR                       against each candidate's single build
  python gpu/weekend_shared_night.py score OUT                             every candidate's own score
  python gpu/weekend_shared_night.py noiseless OUT                         dry: shared against single, noiseless
"""
import argparse
import contextlib
import io
import json
import math
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import repcode4_night as RC  # noqa: E402  (candidate A; read only)
import qpe_long_night as QL  # noqa: E402  (candidate B; read only)
import ipe_park_night as IP  # noqa: E402  (candidate C; read only)
import qpe_repro_night as Q  # noqa: E402  (declared 2026-11-19; read only: B's and C's check)

MAX_S = 60.0
SENTINEL_CIRCUITS = 4


def qpu_seconds(n_circuits, shots):
    """psf_os.job.qpu_seconds, written again so that `size` needs no psf-os import."""
    return n_circuits * 0.036 + n_circuits * shots * 0.00027 + 3.0


# ------------------------------------------------------------------------------------------------ the selection

def sel_from(a):
    return dict(cands=list(a.cands), shots=a.shots, a_forms=list(a.a_forms), b_plan=a.b_plan,
                b_n4_from_c=bool(a.b_n4_from_c), b_fence=bool(a.b_fence), c_forms=list(a.c_forms),
                c_shared_fixed=bool(a.c_shared_fixed), ff_only=bool(a.ff_only), layout=a.layout)


def b_contents(plan):
    """B's (family, n, j0, j1) over every job of the plan; n5ipe is plan n5 without the textbook circuit."""
    if plan == "n5ipe":
        return [("ipe", 5, 0, 16), ("ipe", 5, 16, 32)]
    return [c for job in QL.PLANS[plan] for c in job]


def b_n_values(sel):
    return sorted({n for fam, n, _, _ in b_contents(sel["b_plan"]) if fam == "ipe"})


def item_list(sel, circuits=True):
    """[(cand, tag, qc, spec, arms)] in packing order. With circuits=False qc and spec are None (sizes only)."""
    out = []
    ff_only_all = sel["ff_only"]
    if "A" in sel["cands"]:
        forms = [f for f in RC.FORMS if f in sel["a_forms"]]
        for e in RC.ERRORS:                               # every form in every job (A's comparisons per job)
            for f in forms:
                tag = f"{f.lower()}_{e}"
                if circuits:
                    qc, succ = RC.circuit(f, e)
                    off, _ = RC.circuit(f, e, lookup=False)
                    out.append(("A", tag, qc, dict(success=succ, off_circuit=off), 1 if ff_only_all else 3))
                else:
                    out.append(("A", tag, None, None, 1 if ff_only_all else 3))
    share4 = sel["b_n4_from_c"] and "B" in sel["cands"] and "C" in sel["cands"]
    if "B" in sel["cands"]:
        for fam, n, j0, j1 in b_contents(sel["b_plan"]):
            for j in range(j0, j1):
                if fam == "ipe" and n == 4 and share4:
                    continue                              # read from C's items of the same circuit
                tag = f"{'ipe' if fam == 'ipe' else 'tqpe'}{n}_{j}"
                qc = spec = None
                if circuits:
                    if fam == "ipe":
                        qc, succ = QL.AP.ipe(n, j, True)
                        off, _ = QL.AP.ipe(n, j, False)
                        spec = dict(success=succ, off_circuit=off, form="blocks")
                        if sel["b_fence"]:
                            from psf_os.footprint import fence_waits
                            qc = fence_waits(qc, conditionals=True)
                    else:
                        qc, succ, _ = QL.Q.textbook_logical(n, j)
                        spec = dict(success=succ, form="pauli")
                out.append(("B", tag, qc, spec, 1 if ff_only_all else 3))
    if "C" in sel["cands"]:
        n = 4
        for job in (0, 1):
            for it in (IP.items(n, job) if circuits else [(f"{f}{n}_{j}", None, None) for j in
                                                         range(job * 8, job * 8 + 8) for f in IP.FORMS]):
                tag = it[0]
                f = tag[:2]
                if f not in sel["c_forms"]:
                    continue
                arms = 1 if (ff_only_all or (sel["c_shared_fixed"] and f != "pl")) else 3
                out.append(("C", tag, it[1], it[2], arms))
    return out


def _block(it):
    """The unit a job boundary never splits: A one error's forms, C one phase's forms, B one item."""
    cand, tag = it[0], it[1]
    if cand == "A":
        return "A:" + tag.split("_")[1]
    if cand == "C":
        return "C:" + tag.split("_")[1]
    return "B:" + tag


def pack(items, shots):
    """Items in order into the fewest jobs of at most MAX_S by the model (each job: its items' arms + the sentinel),
    whole blocks only (_block), filled up to an even share of the circuits."""
    blocks = []
    for it in items:
        if blocks and _block(blocks[-1][-1]) == _block(it):
            blocks[-1].append(it)
        else:
            blocks.append([it])
    size_of = lambda b: sum(x[4] for x in b)

    def fill(cap):
        jobs, cur, n_cur = [], [], 0
        for b in blocks:
            nb = size_of(b)
            if cur and (n_cur + nb > cap or qpu_seconds(n_cur + nb + SENTINEL_CIRCUITS, shots) > MAX_S):
                jobs.append(cur)
                cur, n_cur = [], 0
            cur += b
            n_cur += nb
        if cur:
            jobs.append(cur)
        return jobs

    k = len(fill(10 ** 9))
    cap = math.ceil(sum(size_of(b) for b in blocks) / k)
    while len(fill(cap)) > k:
        cap += 1
    return fill(cap)


def size(sel):
    its = item_list(sel, circuits=False)
    jobs = pack(its, sel["shots"])
    rows = []
    for j in jobs:
        n = sum(x[4] for x in j) + SENTINEL_CIRCUITS
        rows.append(dict(circuits=n, seconds=round(qpu_seconds(n, sel["shots"]), 1),
                         cands={c: sum(1 for x in j if x[0] == c) for c in sel["cands"]}))
    total = sum(r["seconds"] for r in rows)
    shots_per_item = {c: sel["shots"] for c in sel["cands"]}
    return dict(jobs=rows, n_jobs=len(rows), circuits=sum(r["circuits"] for r in rows), seconds=round(total, 1),
                shots_per_item=shots_per_item, b_n=b_n_values(sel) if "B" in sel["cands"] else [])


# ------------------------------------------------------------------------------------------------ layout

def _dist_from(dev, sources):
    adj = {}
    for a, b in dev.working_couplers():
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    # distance over every coupler of the record (failed ones too: a failed coupler is still a physical neighbour)
    for a, b in dev.couplers if hasattr(dev, "couplers") else []:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    dist = {q: 0 for q in sources}
    front = list(sources)
    while front:
        nxt = []
        for q in front:
            for r in adj.get(q, ()):
                if r not in dist:
                    dist[r] = dist[q] + 1
                    nxt.append(r)
        front = nxt
    return dist


def free_chain(dev, width, used, min_dist=3):
    """The first chain of `width` usable qubits joined by working couplers whose every qubit is at coupler distance
    >= min_dist from `used`; starts in ascending qubit order, neighbours in ascending order (no error number read)."""
    work = {tuple(sorted(e)) for e in dev.working_couplers()}
    adj = {}
    for a, b in work:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    dist = _dist_from(dev, used) if used else {}
    ok = lambda q: dev.qubit_ok(q) and dist.get(q, 10 ** 6) >= min_dist

    def dfs(path):
        if len(path) == width:
            return list(path)
        for r in sorted(adj.get(path[-1], ())):
            if r not in path and ok(r):
                got = dfs(path + [r])
                if got:
                    return got
        return None

    for s in range(dev.num_qubits):
        if ok(s):
            got = dfs([s])
            if got:
                return got
    raise SystemExit(f"no free chain of {width} qubits at distance >= {min_dist}")


def groups(sel):
    g = [[c] for c in sel["cands"]]
    if sel["b_n4_from_c"] and "B" in sel["cands"] and "C" in sel["cands"]:
        g = [x for x in g if x[0] not in ("B", "C")]
        first = min(sel["cands"].index("B"), sel["cands"].index("C"))
        g.insert(sum(1 for c in sel["cands"][:first] if c not in ("B", "C")), ["B", "C"])
    return g


def chains_for(dev, sel, items):
    """{tag: chain} for layout apart (the first group keeps rule C: no chain given); {} for layout own."""
    from psf_os import feedforward as FF
    if sel["layout"] == "own":
        return {}, {}
    used, chains, region = set(), {}, {}
    for k, grp in enumerate(groups(sel)):
        its = [x for x in items if x[0] in grp]
        width = max(x[2].num_qubits for x in its)
        if k == 0:
            reg = FF.place(dev, width)["chain"]
        else:
            reg = free_chain(dev, width, used)
            for x in its:
                chains[x[1]] = reg[:x[2].num_qubits]
        region["+".join(grp)] = reg
        used |= set(reg)
    return chains, region


# ------------------------------------------------------------------------------------------------ build

def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    sel = sel_from(a)
    dev = Device.load(a.devdir)
    its = item_list(sel)
    chains, region = chains_for(dev, sel, its)
    jobs = pack(its, sel["shots"])
    if os.path.exists(a.out):
        raise SystemExit(f"{a.out} exists (nothing is overwritten)")
    os.makedirs(a.out)
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None   # dry runs only, never a device
    info = dict(selection=sel, devdir=os.path.abspath(a.devdir), device=dev.name, region=region, jobs=[],
                dry_clifford_sentinel=bool(a.dry_clifford_sentinel))
    for k, job in enumerate(jobs):
        jd = os.path.join(a.out, f"job{k}")
        ff_only = [x[1] for x in job if x[4] == 1]
        kw = dict(ff_only=ff_only) if ff_only else {}
        ch = {x[1]: chains[x[1]] for x in job if x[1] in chains}
        rep = FF.build(dev, [(x[1], x[2], x[3]) for x in job], jd, shots=sel["shots"], max_seconds=MAX_S,
                       sentinel_spec=spec, chains=ch or None, footprint=True, **kw)
        info["jobs"].append(dict(folder=f"job{k}", circuits=rep["circuits"], qpu_seconds_model=rep["qpu_seconds_model"],
                                 items={c: [x[1] for x in job if x[0] == c] for c in sel["cands"]}, ff_only=ff_only))
        print(f"job{k}: {rep['circuits']} circuits, {rep['qpu_seconds_model']:.1f} s by the model; " +
              ", ".join(f"{c} {sum(1 for x in job if x[0] == c)} items" for c in sel["cands"]))
    info["qpu_seconds_model"] = round(sum(j["qpu_seconds_model"] for j in info["jobs"]), 1)
    json.dump(info, open(os.path.join(a.out, "shared.json"), "w"), indent=1)
    print(f"{len(jobs)} jobs, {info['qpu_seconds_model']:.1f} s by the model; regions {region}")
    return info


# ------------------------------------------------------------------------------------------------ views and checks

def make_view(jd, cand, tags, part, vd):
    """A folder holding only `tags`' cells (and the sentinel) of job folder jd, with the candidate's part.json, for
    the candidate's own check. The records are copied; job/ holds the subset manifest and circuits (and counts)."""
    from qiskit import qpy
    from psf_os import job as J
    man = json.load(open(os.path.join(jd, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(jd, "job", "circuits.qpy"), "rb"))
    rows = None
    rc = os.path.join(jd, "job", "raw_counts.json")
    if os.path.exists(rc):
        rows = json.load(open(rc))
    keep = set()
    for c in man["cells"]:
        base = c["name"][3:].replace("_floor", "").replace("_off", "") if c["name"].startswith("ff_") else None
        if c["role"] == "sentinel" or base in tags:
            keep.add(c["cell"])
    os.makedirs(os.path.join(vd, "job"))
    os.makedirs(os.path.join(vd, "runs"))
    cells, pubs, circs, newrows, idx = [], [], [], [], {}
    for c in man["cells"]:
        if c["cell"] in keep:
            idx[c["cell"]] = len(cells)
            cells.append(dict(c, cell=len(cells)))
            r = os.path.join(jd, "runs", c["name"] + ".json")
            shutil.copy(r, os.path.join(vd, "runs"))
            qf = json.load(open(r))["export"]["qpy"]
            shutil.copy(os.path.join(jd, "runs", qf), os.path.join(vd, "runs"))
    for k, p in enumerate(man["pubs"]):
        if p["cell"] in keep:
            pubs.append(dict(cell=idx[p["cell"]], point=p["point"]))
            circs.append(cs[k])
            if rows is not None:
                newrows.append(dict(rows["rows"][k], pub=len(newrows)))
    with open(os.path.join(vd, "job", "circuits.qpy"), "wb") as f:
        qpy.dump(circs, f)
    m2 = dict(man, cells=cells, pubs=pubs, roles={c["name"]: c["role"] for c in cells},
              user_pubs=[k for k, p in enumerate(pubs) if cells[p["cell"]]["role"] == "user"],
              circuits_sha256=J.sha256_file(os.path.join(vd, "job", "circuits.qpy")),
              qpy_sha256=J.sha256_file(os.path.join(vd, "job", "circuits.qpy")),
              view_of=dict(job=os.path.abspath(jd), candidate=cand))
    m2.pop("broadcast", None)
    json.dump(m2, open(os.path.join(vd, "job", "manifest.json"), "w"), indent=1)
    if rows is not None:
        json.dump(dict(rows, rows=newrows), open(os.path.join(vd, "job", "raw_counts.json"), "w"), indent=1)
        sub = os.path.join(jd, "job", "submission.json")
        if os.path.exists(sub):
            shutil.copy(sub, os.path.join(vd, "job"))
    json.dump(part, open(os.path.join(vd, "part.json"), "w"), indent=1)


def _spec_of(sel):
    return {x[1]: x[3] for x in item_list(sel)}


def check(a):
    """Every candidate's own check on its view of every job: A repcode4_night.check; B and C qpe_repro_night.check
    (as qpe_long_night.check and ipe_park_night.check call it, with this night's items)."""
    info = json.load(open(os.path.join(a.out, "shared.json")))
    sel = info["selection"]
    spec = _spec_of(sel)
    ok_all, lines = True, []
    for j in info["jobs"]:
        jd = os.path.join(a.out, j["folder"])
        for cand, tags in j["items"].items():
            if not tags:
                continue
            vd = os.path.join(jd, "views", f"check_{cand}")
            if os.path.exists(vd):
                shutil.move(vd, os.path.join(jd, "views", f"_old_check_{cand}"))
            part = dict(part="shared", shots=sel["shots"], qpu_seconds_model=j["qpu_seconds_model"])
            make_view(jd, cand, set(tags), part, vd)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                if cand == "A":
                    ok = RC.check(argparse.Namespace(out=vd))
                else:
                    saved = Q._spec_by_tag
                    Q._spec_by_tag = lambda _p: spec
                    try:
                        ok = Q.check(argparse.Namespace(out=vd, verbose=False))
                    finally:
                        Q._spec_by_tag = saved
            tail = [s for s in buf.getvalue().splitlines() if s.strip()][-1]
            lines.append(f"{j['folder']} {cand}: {len(tags)} items; {cand}'s own check: {tail}")
            ok_all &= bool(ok)
    lines.append("PASS" if ok_all else "FAIL")
    print("\n".join(lines))
    open(os.path.join(a.out, "check.txt"), "w").write("\n".join(lines) + "\n")
    return ok_all


# ------------------------------------------------------------------------------------------------ same as single

def single_builds(devdir, sel, out):
    """Each candidate's single build with its own tool and arguments, on the same device record (A: part all at
    this night's shots; B: every job of the plan; C: jobs 0 and 1)."""
    spec_s = []
    if "A" in sel["cands"]:
        d = os.path.join(out, "A")
        RC.build(argparse.Namespace(devdir=devdir, out=d, part="all", shots=sel["shots"], dry_clifford_sentinel=True))
        spec_s.append(d)
    if "B" in sel["cands"]:
        plan = "n5" if sel["b_plan"] == "n5ipe" else sel["b_plan"]
        for k in range(len(QL.PLANS[plan])):
            d = os.path.join(out, f"B{k}")
            QL.build(argparse.Namespace(devdir=devdir, out=d, plan=plan, job=k, fence=sel["b_fence"],
                                        shots=sel["shots"], dry_clifford_sentinel=True))
            spec_s.append(d)
    if "C" in sel["cands"]:
        for k in (0, 1):
            d = os.path.join(out, f"C{k}")
            IP.build(argparse.Namespace(devdir=devdir, out=d, n=4, job=k, reads_only=False, shots=sel["shots"],
                                        dry_clifford_sentinel=True))
            spec_s.append(d)
    return spec_s


def _arms(folder):
    """{(tag, arm): (record, compiled circuit)} of a build folder."""
    from qiskit import qpy
    out = {}
    for f in os.listdir(os.path.join(folder, "runs")):
        if f.endswith(".json") and f.startswith("ff_"):
            r = json.load(open(os.path.join(folder, "runs", f)))
            if r.get("psfos_role") == "sentinel" or "tag" not in r:
                continue
            c = qpy.load(open(os.path.join(folder, "runs", r["export"]["qpy"]), "rb"))[0]
            out[(r["tag"], r.get("ff_arm"))] = (r, c)
    return out


def same(a):
    """Per item and arm of the shared night against the candidates' single builds: the compiled circuit (equal as a
    circuit with layout own; with layout apart: the CZ, the depth and the footprint as sent), the chain."""
    info = json.load(open(os.path.join(a.out, "shared.json")))
    sel = info["selection"]
    sd = os.path.join(a.out, "single")
    if not os.path.exists(sd):
        with contextlib.redirect_stdout(io.StringIO()):
            single_builds(a.devdir, sel, sd)
    single = {}
    for f in sorted(os.listdir(sd)):
        single.update(_arms(os.path.join(sd, f)))
    shared = {}
    for j in info["jobs"]:
        shared.update(_arms(os.path.join(a.out, j["folder"])))
    share4 = sel["b_n4_from_c"] and "B" in sel["cands"] and "C" in sel["cands"]
    alias = {}
    if share4:
        src = "fe" if sel["b_fence"] else "pl"
        alias = {f"ipe4_{j}": f"{src}4_{j}" for j in range(16)}
    rows, bad = [], []
    for (tag, arm), (r1, c1) in sorted(single.items()):
        key = (alias.get(tag, tag), arm)
        if key not in shared:
            ff_only = any(t == key[0] for t, _ in shared) and arm in ("off", "floor")
            rows.append((tag, arm, "not in the shared night" + (" (ff only)" if ff_only else "")))
            continue
        r2, c2 = shared[key]
        cz1 = sum(1 for ins in c1.data if ins.operation.name == "cz")
        cz2 = sum(1 for ins in c2.data if ins.operation.name == "cz")
        fp1 = ((r1.get("wait_footprint") or {}).get("sent") or {}).get(arm, {}).get("max")    # as sent, this arm
        fp2 = ((r2.get("wait_footprint") or {}).get("sent") or {}).get(arm, {}).get("max")
        eq = c1 == c2
        same_chain = r1["chain"] == r2["chain"]
        ok = (eq if sel["layout"] == "own" else True) and cz1 == cz2 and r1.get("cz") == r2.get("cz") and \
            c1.depth() == c2.depth() and (fp1 is None or fp2 is None or fp1 == fp2)
        rows.append((tag, arm, f"{'circuit equal' if eq else 'circuit differs'}; chain "
                               f"{'same' if same_chain else str(r1['chain']) + ' -> ' + str(r2['chain'])}; CZ {cz1}/{cz2}; "
                               f"depth {c1.depth()}/{c2.depth()}; footprint {fp1}/{fp2} {'ok' if ok else 'DIFFERS'}"))
        if not ok:
            bad.append((tag, arm))
    lines = [f"{t:12s} {arm:5s} {s}" for t, arm, s in rows]
    n_eq = sum(1 for _, _, s in rows if s.startswith("circuit equal"))
    lines.append(f"{len(rows)} arms of the single builds; {n_eq} with the same compiled circuit; "
                 f"{sum(1 for _, _, s in rows if s.startswith('not in'))} not in the shared night; "
                 + ("SAME (CZ, depth, footprint" + (", circuits" if sel["layout"] == "own" else "") + ")"
                    if not bad else f"DIFFERS {bad[:10]}"))
    print("\n".join(lines[-3:]))
    open(os.path.join(a.out, "same.txt"), "w").write("\n".join(lines) + "\n")
    return not bad


# ------------------------------------------------------------------------------------------------ score

def cards_of(folder):
    """{tag: card} of a finished job folder: FF.cards' card when the item has all three arms; for an item with its ff
    arm only, the card's ff share alone (psf-os success_share on the item's success bits)."""
    from psf_os import feedforward as FF
    from psf_os import job as J
    read = J.read(os.path.join(folder, "job"), os.path.join(folder, "runs"))
    got = {}
    for name, (rec, cc) in read.items():
        if rec.get("psfos_job", {}).get("kind", "").startswith(FF.KIND):
            got.setdefault(rec["tag"], {})[rec["ff_arm"]] = (rec, cc[("f", "z")])
    res = {}
    for tag, arms in got.items():
        rec, cnt = arms["ff"]
        if "off" in arms and "floor" in arms:
            res[tag] = FF._single_card(tag, rec, cnt, arms["off"][1], arms["floor"][1], "not scored here")
        else:
            succ = {int(b): v for b, v in rec["success"].items()}
            res[tag] = dict(tag=tag, chain=rec["chain"], ff=FF.success_share(cnt, rec["clbits"], succ),
                            ff_only=True)
    return res


def score(a):
    """Every candidate's own score function on its items' cards from every job (psf_os.feedforward.cards is
    replaced, for the call, by the cards read here; the candidates' code is unchanged)."""
    from psf_os import feedforward as FF
    info = json.load(open(os.path.join(a.out, "shared.json")))
    sel = info["selection"]
    cards = {}
    for j in info["jobs"]:
        cards.update(cards_of(os.path.join(a.out, j["folder"])))
    if sel["b_n4_from_c"] and "B" in sel["cands"] and "C" in sel["cands"]:
        src = "fe" if sel["b_fence"] else "pl"
        for j in range(16):
            cards[f"ipe4_{j}"] = cards[f"{src}4_{j}"]
    res = {}
    saved = FF.cards
    FF.cards = lambda _out: cards
    try:
        for cand in sel["cands"]:
            sd = os.path.join(a.out, "scores", cand)
            os.makedirs(sd, exist_ok=True)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                if cand == "A":
                    if set(sel["a_forms"]) != set(RC.FORMS):
                        # A's score pools every form; without F16 its beside comparison F10 - F16 cannot be formed
                        _score_a_without(cards, sel["a_forms"], sd)
                    else:
                        RC.score(argparse.Namespace(out=sd, out2=None))
                elif cand == "B":
                    QL.score(argparse.Namespace(outs=[sd]))
                else:
                    IP.score(argparse.Namespace(outs=[sd]))
            res[cand] = buf.getvalue()
    finally:
        FF.cards = saved
    text = "\n".join(f"== {c}\n{t}" for c, t in res.items())
    print(text)
    open(os.path.join(a.out, "score.txt"), "w").write(text)
    return res


def _score_a_without(cards, forms, sd):
    """A's score with a subset of its forms: A's own pooling, ceilings and words; the comparisons whose two forms are
    both run (footprint F6P - F10, CZ F6 - F6P), the beside one only when F16 is run."""
    I = RC.ideal()
    res = {}
    for form in [f for f in RC.FORMS if f in forms]:
        cs = [cards[f"{form.lower()}_{e}"] for e in RC.ERRORS]
        p, se, N = RC._pool(cs)
        C = I[form]["ceiling"]
        res[form] = dict(p=p, se=se, verdict=RC.RN.ceiling_verdict(p, se, C))
        print(f"{form}: {p:.4f} (2 SE {2 * se:.4f}) against C {C:.4f} -> {res[form]['verdict']}")
    words = {}
    for name, (x, y) in RC.COMPARISONS.items():
        if x in res and y in res:
            d = res[x]["p"] - res[y]["p"]
            se = math.sqrt(res[x]["se"] ** 2 + res[y]["se"] ** 2)
            words[name] = RC.pair_word(d, se)
            print(f"{name}: {d:+.4f} (2 SE {2 * se:.4f}) -> {words[name]}")
        else:
            print(f"{name}: not formed ({x} or {y} not run)")
    print(f"reading [OWNER]: {RC.reading(words['footprint'], words['cz'])}")


def noiseless(a):
    """Dry runs only: noiseless Aer (psf_os.feedforward.run_local) on every shared job and on every single build of
    `same`, then every candidate's own score on both; the per-candidate lines (shares, ceilings, verdicts) must be
    the same."""
    from psf_os import feedforward as FF
    info = json.load(open(os.path.join(a.out, "shared.json")))
    if not info.get("dry_clifford_sentinel"):
        raise SystemExit("noiseless runs need a build with --dry-clifford-sentinel (dry runs only)")
    sel = info["selection"]
    for j in info["jobs"]:
        jd = os.path.join(a.out, j["folder"])
        if not os.path.exists(os.path.join(jd, "job", "raw_counts.json")):
            FF.run_local(jd)
    sd = os.path.join(a.out, "single")
    if not os.path.exists(sd):
        raise SystemExit("run `same` first (it builds the single jobs)")
    for f in sorted(os.listdir(sd)):
        if not os.path.exists(os.path.join(sd, f, "job", "raw_counts.json")):
            FF.run_local(os.path.join(sd, f))
    with contextlib.redirect_stdout(io.StringIO()):
        shared = score(a)
    single = {}
    for cand in sel["cands"]:
        outs = [os.path.join(sd, f) for f in sorted(os.listdir(sd)) if f.startswith(cand)]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            if cand == "A":
                if set(sel["a_forms"]) != set(RC.FORMS):
                    saved = FF.cards
                    cards = {}
                    for o in outs:
                        cards.update(saved(o))
                    _score_a_without(cards, sel["a_forms"], outs[0])
                else:
                    RC.score(argparse.Namespace(out=outs[0], out2=outs[1] if len(outs) > 1 else None))
            elif cand == "B":
                QL.score(argparse.Namespace(outs=outs))
            else:
                IP.score(argparse.Namespace(outs=outs))
        single[cand] = buf.getvalue()
    lines, ok = [], True
    for cand in sel["cands"]:
        s1 = [x for x in single[cand].splitlines() if x.strip()]
        s2 = [x for x in shared[cand].splitlines() if x.strip()]
        if cand == "B" and sel["b_plan"] == "n5ipe":
            s1 = [x.split("; textbook")[0] for x in s1 if x.startswith("n 5")]
            s2 = [x.split("; textbook")[0] for x in s2 if x.startswith("n 5")]
        same_ = s1 == s2
        ok &= same_
        lines.append(f"{cand}: {'SAME' if same_ else 'DIFFERENT'} ({len(s1)} lines of {cand}'s own score)")
        for x, y in zip(s1, s2):
            lines.append(f"   single: {x}")
            if x != y:
                lines.append(f"   shared: {y}")
    lines.append("SAME" if ok else "DIFFERENT")
    print("\n".join(lines))
    open(os.path.join(a.out, "noiseless.txt"), "w").write("\n".join(lines) + "\n")
    return ok


# ------------------------------------------------------------------------------------------------ the table

BASE = dict(cands=["A", "B", "C"], shots=1950, a_forms=list(RC.FORMS), b_plan="shape", b_n4_from_c=False,
            b_fence=False, c_forms=list(IP.FORMS), c_shared_fixed=False, ff_only=False, layout="apart")


def separate_nights():
    """Each candidate alone as its draft sizes it (A one job at 4000 shots; B its plan at 1950; C two jobs at 1950)."""
    out = {}
    for cand, sel in (("A", dict(BASE, cands=["A"], shots=4000)), ("B", dict(BASE, cands=["B"])),
                      ("C", dict(BASE, cands=["C"]))):
        out[cand] = size(sel)
    return out


def se_factor(sel, ref_shots):
    """2 SE of each candidate's comparisons relative to its draft (shots per item; the same items pooled)."""
    f = {}
    for c in sel["cands"]:
        f[c] = round(math.sqrt(ref_shots[c] / sel["shots"]), 2)
    return f


def table(a):
    ref = {"A": 4000, "B": 1950, "C": 1950}
    rows = []

    def row(name, sels, lost):
        sels = sels if isinstance(sels, list) else [sels]
        ss = [size(s) for s in sels]
        f = {}
        for s in sels:
            f.update(se_factor(s, ref))
        rows.append(dict(name=name, selection=sels, circuits=sum(s["circuits"] for s in ss),
                         jobs=sum(s["n_jobs"] for s in ss), seconds=round(sum(s["seconds"] for s in ss), 1),
                         per_job=[j["seconds"] for s in ss for j in s["jobs"]], two_se_factor=f, lost=lost))

    sep = separate_nights()
    rows.append(dict(name="0 each alone (drafts)", circuits=sum(v["circuits"] for v in sep.values()),
                     jobs=sum(v["n_jobs"] for v in sep.values()), seconds=round(sum(v["seconds"] for v in sep.values()), 1),
                     per_job={k: [j["seconds"] for j in v["jobs"]] for k, v in sep.items()},
                     two_se_factor={"A": 1.0, "B": 1.0, "C": 1.0}, lost="-"))
    A4 = dict(BASE, cands=["A"], shots=4000)
    A2 = dict(BASE, cands=["A"], shots=2000)
    F3 = ["F10", "F6P", "F6"]
    row("1 all three in one night's jobs, nothing cut (all 1950 shots)", dict(BASE),
        "A at 1950 shots (psf-os: one shot count per job)")
    row("1b as 1, A in its own jobs at 4000", [A4, dict(BASE, cands=["B", "C"])], "nothing")
    row("2 A at 2000 shots (alone)", A2, "A: 2 SE x1.41")
    row("3 A without F16 (alone, 4000)", dict(A4, a_forms=F3), "A: beside F10 - F16; 2026-11-19's circuit")
    row("4 B shape with n = 4 from C's pl, + C", dict(BASE, cands=["B", "C"], b_n4_from_c=True),
        "nothing (B's n = 4 and C's pl are the same circuits on the same qubits)")
    row("5 C alone, fe and pk without off/floor", dict(BASE, cands=["C"], c_shared_fixed=True),
        "fe's and pk's floors (beside); their off arm is pl's (the same circuit)")
    row("6a A alone, ff only (4000)", dict(A4, ff_only=True), "off, floor (beside)")
    row("6b B shape alone, ff only", dict(BASE, cands=["B"], ff_only=True), "off, floor (beside)")
    row("6c C alone, ff only", dict(BASE, cands=["C"], ff_only=True), "off, floor (beside)")
    row("7 B n5 (IPE + textbook) alone", dict(BASE, cands=["B"], b_plan="n5"), "B's shape (needs three n)")
    row("7b B n5, IPE only, alone", dict(BASE, cands=["B"], b_plan="n5ipe"), "B's shape; IPE - textbook")
    row("8 A + B shape (A 4000 own jobs)", [A4, dict(BASE, cands=["B"])], "C")
    row("8b A + C (A 4000 own jobs)", [A4, dict(BASE, cands=["C"])], "B")
    row("8c B shape + C (n4 shared)", dict(BASE, cands=["B", "C"], b_n4_from_c=True), "A")
    row("9 all three, nothing cut but n4 shared (A 4000 own jobs)", [A4, dict(BASE, cands=["B", "C"], b_n4_from_c=True)],
        "nothing")
    row("10 all three, ff only, n4 shared (A 4000 own job)",
        [dict(A4, ff_only=True), dict(BASE, cands=["B", "C"], b_n4_from_c=True, ff_only=True)], "off, floor (beside)")
    row("10b as 10, A at 1950 in the shared jobs", dict(BASE, b_n4_from_c=True, ff_only=True),
        "off, floor; A 2 SE x1.43")
    row("10c as 10, A without F16", [dict(A4, ff_only=True, a_forms=F3),
                                      dict(BASE, cands=["B", "C"], b_n4_from_c=True, ff_only=True)],
        "off, floor; A's F10 - F16")
    row("11 A + C, ff only (A 4000 own job)", [dict(A4, ff_only=True), dict(BASE, cands=["C"], ff_only=True)],
        "B; off, floor")
    row("11b A + B shape, ff only (A 4000 own job)", [dict(A4, ff_only=True), dict(BASE, cands=["B"], ff_only=True)],
        "C; off, floor")
    row("11c B shape + C, ff only, n4 shared", dict(BASE, cands=["B", "C"], b_n4_from_c=True, ff_only=True),
        "A; off, floor")
    row("12 all three, ff only, B n5ipe (A 4000 own job)",
        [dict(A4, ff_only=True), dict(BASE, cands=["B", "C"], b_plan="n5ipe", ff_only=True)],
        "B's shape and textbook; off, floor")
    json.dump(rows, open(a.out, "w"), indent=1)
    for r in rows:
        print(f"{r['name']:48s} {r['circuits']:4d} circuits {r['jobs']} jobs {r['seconds']:6.1f} s  "
              f"2SE x{r['two_se_factor']}  lost: {r['lost']}")


# ------------------------------------------------------------------------------------------------ CLI

def add_sel(p):
    p.add_argument("--cands", default="ABC", type=lambda s: [c for c in s if c in "ABC"])
    p.add_argument("--shots", type=int, default=1950)
    p.add_argument("--a-forms", default="F16,F10,F6P,F6", type=lambda s: s.split(","))
    p.add_argument("--b-plan", default="shape", choices=("shape", "n5", "n5ipe", "n5n6"))
    p.add_argument("--b-n4-from-c", action="store_true")
    p.add_argument("--b-fence", action="store_true")
    p.add_argument("--c-forms", default="pl,fe,pk", type=lambda s: s.split(","))
    p.add_argument("--c-shared-fixed", action="store_true")
    p.add_argument("--ff-only", action="store_true")
    p.add_argument("--layout", default="apart", choices=("apart", "own"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("size")
    add_sel(s)
    t = sub.add_parser("table")
    t.add_argument("out")
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    add_sel(b)
    b.add_argument("--dry-clifford-sentinel", action="store_true")
    sub.add_parser("check").add_argument("out")
    m = sub.add_parser("same")
    m.add_argument("out")
    m.add_argument("devdir")
    sub.add_parser("score").add_argument("out")
    sub.add_parser("noiseless").add_argument("out")
    a = ap.parse_args()
    if a.cmd == "size":
        print(json.dumps(size(sel_from(a)), indent=1))
        sys.exit(0)
    r = {"table": table, "build": build, "check": check, "same": same, "score": score,
         "noiseless": noiseless}[a.cmd](a)
    sys.exit(0 if r is not False else 1)
