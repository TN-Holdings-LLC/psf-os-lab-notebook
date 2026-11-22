"""Should psf-os 0.3.1 park the likely value by default? (draft for a declaration; home VS Claude, 2026-11-22; home
instruction "0.3.1 候補（MP）の実機試験の準備"; desk, no device).

Per RUS item, the twins side by side in one job (copies a, b, ...):
  D  psf-os's default (0.3.0's: the chains have nothing to park)
  L  build(park_likely=...): every waiting qubit with P(|1>) > 0.5 parked by an X pair behind a partial fence (the parked
     qubits and the wait's own qubits, at those waits only): the desk's MP (notes/likely_park_2026-11-22)
Read: L - D as the loop reads g (|P - exact|, nearer is better), per item. An item whose D or L OVERSHOOTS (P above
that form's noiseless value + 2 SE, the loop's rule) is recorded but not counted for the rule for the default. Beside, in the same job: the IPE control
(n = 4 at phases 2, 6, 10, 14, parked and unparked), the gate. Needs psf-os 0.3.1 (likely-park-2026-11-22); the
declared tools are imported read only, gpu/rus_fence_night.py for its items, device rule and noises.

  python gpu/likely_park_night.py table OUT.json
  python gpu/likely_park_night.py pick FETCH_IN
  python gpu/likely_park_night.py build DEVDIR OUT [--plan B] [--dry-clifford-sentinel]
  python gpu/likely_park_night.py check OUT
  python gpu/likely_park_night.py dry OUT NOISE [--seed S]            ILLUSTRATIVE noise only: wait | cond | phase
  python gpu/likely_park_night.py score OUT
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
sys.path.insert(0, os.path.join(NB, "notes", "ffapps_2026-11-17"))
import rus_fence_night as RF  # noqa: E402  (declared 2026-11-21; read only: items, the device rule, the noises)

SHOTS = 1950
MAX_S = 60.0
SEED = 20261125
IPE_PHASES = (2, 6, 10, 14)
ITEMS = ("nfl3m3", "p0l3", "p3l3")
PLANS = {"B": {"nfl3m3": 4, "p0l3": 14, "p3l3": 10}, "A": {"nfl3m3": 3, "p0l3": 8, "p3l3": 5}}   # [OWNER]: B chosen


def qpu_seconds(n, shots=SHOTS):
    return n * 0.036 + n * shots * 0.00027 + 3.0


def size(plan):
    n = 2 * sum(PLANS[plan].values()) + 2 * len(IPE_PHASES) + 4
    p = 0.7
    return dict(plan=plan, copies=PLANS[plan], circuits=n, seconds=round(qpu_seconds(n), 1),
                two_se={k: round(2 * math.sqrt(2 * p * (1 - p) / (SHOTS * c)), 4) for k, c in PLANS[plan].items()})


def table(a):
    rows = [size(p) for p in PLANS]
    json.dump(rows, open(a.out, "w"), indent=1)
    for r in rows:
        print(f"plan {r['plan']}: copies {r['copies']}, {r['circuits']} circuits, {r['seconds']} s, 2 SE {r['two_se']}")


def items_of(plan):
    import apps as AP
    out, likely, skip = [], [], []
    for key, c in PLANS[plan].items():
        presc, m, L = RF.RUS[key]
        qc, spec = RF.rus_circuit(presc, m, L)
        for cp in "abcdefghijklmnop"[:c]:
            out.append((f"{key}D{cp}", qc, spec))
            out.append((f"{key}L{cp}", qc, spec))
            likely.append(f"{key}L{cp}")
    for j in IPE_PHASES:
        qc, succ = AP.ipe(4, j, True)
        off, _ = AP.ipe(4, j, False)
        sp = dict(success=succ, off_circuit=off, form="blocks")
        out += [(f"ipk4_{j}", qc, sp), (f"ipu4_{j}", qc, sp)]
        skip.append(f"ipu4_{j}")
    return out, likely, skip


def build(a):
    import psf_os
    from psf_os import feedforward as FF
    from psf_os.device import Device
    if not FF.parks_by_default(psf_os.__version__) or not hasattr(FF, "park_likely") and \
            "park_likely" not in FF.build.__code__.co_varnames:
        raise SystemExit("needs psf-os 0.3.1 (build(park_likely=...))")
    dev = Device.load(a.devdir)
    if dev.name == "ibm_marrakesh":
        raise SystemExit("REFUSED: the rule runs this test off ibm_marrakesh (pick)")
    if os.path.exists(a.out):
        raise SystemExit(f"{a.out} exists (nothing is overwritten)")
    its, likely, skip = items_of(a.plan)
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None   # dry runs only, never a device
    jd = os.path.join(a.out, "job0")
    os.makedirs(a.out)
    rep = FF.build(dev, its, jd, shots=SHOTS, max_seconds=MAX_S, sentinel_spec=spec, ff_only=[t for t, _, _ in its],
                   park=True, park_skip=skip, park_likely=likely, footprint=True, declared=psf_os.__version__)
    info = dict(plan=a.plan, device=dev.name, psf_os=psf_os.__version__, shots=SHOTS, circuits=rep["circuits"],
                qpu_seconds_model=rep["qpu_seconds_model"], folder="job0")
    json.dump(info, open(os.path.join(a.out, "plan.json"), "w"), indent=1)
    print(f"{rep['circuits']} circuits at {SHOTS} shots, {rep['qpu_seconds_model']:.1f} s on {dev.name} (psf-os "
          f"{psf_os.__version__})")


def _job(out):
    from qiskit import qpy
    jd = os.path.join(out, "job0")
    man = json.load(open(os.path.join(jd, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(jd, "job", "circuits.qpy"), "rb"))
    cells = {c["cell"]: c for c in man["cells"]}
    by = {cells[p["cell"]]["name"][3:]: cs[i] for i, p in enumerate(man["pubs"]) if cells[p["cell"]]["role"] == "user"}
    return jd, man, by


def check(a):
    """Per RUS item (copy a): D and L with equal compiled noiseless distributions and CZ; every parked wait of L's record
    (park_likely, physical qubits) fenced on the device by barriers holding its parked qubits and a qubit of the wait
    (the pair cannot fold and stays in the wait), at least two per parked wait; L with more one-qubit gates on the
    parked qubits than D. The IPE control by qpe_repro_night.check (declared). The manifest: psf_os_build version
    0.3.1, park True, park_likely naming the L items."""
    from psf_os import feedforward as FF
    from psf_os.footprint import exact_distribution
    info = json.load(open(os.path.join(a.out, "plan.json")))
    jd, man, by = _job(a.out)
    lines, ok_all = [], True
    b = man.get("psf_os_build", {})
    want_l = sorted(t for t in by if t[:-1].endswith("L") and t[:-2] in ITEMS)
    okb = b.get("version") == "0.3.1" and b.get("park") is True and sorted(b.get("park_likely") or []) == want_l
    lines.append(f"psf_os_build version {b.get('version')}, park {b.get('park')}, park_likely names {len(b.get('park_likely') or [])} "
                 f"L items -> {'ok' if okb else 'NOT AS DECLARED'}")
    ok_all &= okb
    for key in ITEMS:
        cd, cl = FF.compact(by[f"{key}Da"]), FF.compact(by[f"{key}La"])
        dd, dl = exact_distribution(cd), exact_distribution(cl)
        same = all(abs(dd.get(x, 0) - dl.get(x, 0)) < 1e-9 for x in set(dd) | set(dl))
        rec = json.load(open(os.path.join(jd, "runs", f"ff_{key}La.json")))
        parked = rec["park_likely"]["arms"]["ff"]["parked"]
        full = by[f"{key}La"]
        meas = {full.find_bit(x.qubits[0]).index for x in full.data if x.operation.name == "measure"}
        bars = [{full.find_bit(q).index for q in x.qubits} for x in full.data if x.operation.name == "barrier"]
        pq = sorted({q for w in parked for q in w["physical"]})
        fenced = all(sum(1 for s in bars if set(w["physical"]) <= s and (s - set(w["physical"])) & meas) >= 2
                     for w in parked)
        n1 = lambda c: sum(1 for x in c.data if x.operation.name in ("x", "sx", "rz") and
                           c.find_bit(x.qubits[0]).index in pq)
        more = n1(full) > n1(by[f"{key}Da"])
        ok = same and FF.cz_count(cd) == FF.cz_count(cl) and fenced and more and len(parked) > 0
        ok_all &= ok
        lines.append(f"{key}: distributions equal {same}; CZ D {FF.cz_count(cd)} L {FF.cz_count(cl)}; parked waits "
                     f"{len(parked)} on physical {pq}; each fenced with a qubit of its wait {fenced}; one-qubit gates on "
                     f"them D {n1(by[f'{key}Da'])} L {n1(full)} -> {'ok' if ok else 'FAIL'}")
    ok = _ipe_check(jd, man)
    ok_all &= ok
    lines.append(f"IPE control: qpe_repro_night.check {'PASS' if ok else 'FAIL'}")
    lines.append("PASS" if ok_all else "FAIL")
    print("\n".join(lines))
    open(os.path.join(a.out, "check.txt"), "w").write("\n".join(lines) + "\n")
    return ok_all


def _ipe_check(jd, man):
    return RF._control_check(jd, "ipe")


def dry(a):
    """The job's circuits as compiled, under one illustrative noise (density matrix); the sentinel noiseless."""
    from qiskit import qpy, transpile
    from qiskit_aer import AerSimulator
    from psf_os import feedforward as FF
    from psf_os.sim import to_clifford_gates
    jd = os.path.join(a.out, "job0")
    man = json.load(open(os.path.join(jd, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(jd, "job", "circuits.qpy"), "rb"))
    role = {c["cell"]: c["role"] for c in man["cells"]}
    sim, stab = AerSimulator(method="density_matrix"), AerSimulator(method="stabilizer")
    noise = RF.NOISES[a.noise]
    rows = []
    for i, c in enumerate(cs):
        cc = FF.compact(c)
        if role[man["pubs"][i]["cell"]] == "sentinel":
            cnt = stab.run(to_clifford_gates(cc), shots=man["shots"], seed_simulator=a.seed + i).result().get_counts()
        else:
            t = transpile(cc, basis_gates=["cz", "rz", "sx", "x"], optimization_level=0)
            cnt = sim.run(RF.noisy(t, noise), shots=man["shots"], seed_simulator=a.seed + 1000 * i).result().get_counts()
        rows.append(dict(pub=i, counts=cnt))
    json.dump(dict(job_id=f"local-illustrative-{a.noise}", local=True, backend=man["fetch"]["backend"], noise=noise),
              open(os.path.join(jd, "job", "submission.json"), "w"))
    json.dump(dict(job_id=f"local-illustrative-{a.noise}", status="DONE", rows=rows, noise=noise,
                   note="ILLUSTRATIVE noise, never fitted"), open(os.path.join(jd, "job", "raw_counts.json"), "w"))


def decision(words, gate, excluded=()):
    """The rule for the default (the owner's decision of 2026-11-22, the home's proposal): park_likely becomes 0.3.1's
    default when, among the items counted, none reads KEEPS LESS and at least one reads KEEPS MORE, and the IPE
    control's gate is open; otherwise it stays opt-in. An item whose D or L OVERSHOOTS (P above that form's noiseless
    value + 2 SE: the loop's rule) is recorded but not counted (`excluded`)."""
    counted = {k: w for k, w in words.items() if k not in set(excluded)}
    if gate != "KEEPS MORE":
        return "opt-in (the gate is closed: 0.3.0's default kept)"
    if not counted:
        return "opt-in (no item counted: every item overshoots)"
    if any(w == "KEEPS LESS" for w in counted.values()):
        return "opt-in (a counted item KEEPS LESS)"
    if any(w == "KEEPS MORE" for w in counted.values()):
        return "the default in 0.3.1 (no counted item KEEPS LESS, at least one KEEPS MORE)"
    return "opt-in (no counted item KEEPS MORE)"


def noiseless_p(circ, ob, want):
    """The noiseless P of the output bit read as declared, from the compiled circuit itself (exact, branching)."""
    from psf_os import feedforward as FF
    from psf_os.footprint import exact_distribution
    cc = FF.compact(circ)
    n = cc.num_clbits
    return sum(p for k, p in exact_distribution(cc).items() if k[n - 1 - ob] == want)


def score(a):
    from psf_os import feedforward as FF
    from psf_os import job as J
    jd = os.path.join(a.out, "job0")
    read = J.read(os.path.join(jd, "job"), os.path.join(jd, "runs"))
    cards = {rec["tag"]: (rec, cc[("f", "z")]) for _n, (rec, cc) in read.items()
             if rec.get("psfos_job", {}).get("kind", "").startswith(FF.KIND) and rec.get("ff_arm") == "ff"}
    lines, words, res, excluded = [], {}, {}, []
    say = lambda s: (print(s), lines.append(s))
    _jd, _man, compiled = _job(a.out)
    for key in ITEMS:
        presc = RF.RUS[key][0]
        P = {}
        for k in "DL":
            ok = N = 0
            for t in sorted(x for x in cards if x[:-1] == f"{key}{k}"):
                rec, cnt = cards[t]
                ob = rec["rus"]["out_bit"]
                want = "1" if RF.reads_one(presc) else "0"
                ok += sum(v for kk, v in cnt.items() if kk.replace(" ", "")[-1 - ob] == want)
                N += sum(cnt.values())
            P[k] = (ok / N, N)
        ex = cards[f"{key}Da"][0]["rus"]["exact"]
        (pd, nd), (pl, nl) = P["D"], P["L"]
        g = abs(pd - ex) - abs(pl - ex)
        se = math.sqrt(pd * (1 - pd) / nd + pl * (1 - pl) / nl)
        words[key] = RF.word(g, se)
        ob = cards[f"{key}Da"][0]["rus"]["out_bit"]
        want = "1" if RF.reads_one(presc) else "0"
        over = {}
        for k, (pk_, nk_) in (("D", P["D"]), ("L", P["L"])):
            nl_ = noiseless_p(compiled[f"{key}{k}a"], ob, want)
            over[k] = dict(noiseless=nl_, overshoots=bool(pk_ > nl_ + 2 * math.sqrt(pk_ * (1 - pk_) / nk_)))
        out_ = over["D"]["overshoots"] or over["L"]["overshoots"]
        if out_:
            excluded.append(key)
        res[key] = dict(D=pd, L=pl, exact=ex, g=g, two_se=2 * se, word=words[key], overshoot=over, counted=not out_)
        say(f"{key}: P D {pd:.4f} L {pl:.4f} (exact {ex:.4f}; noiseless D {over['D']['noiseless']:.4f} L "
            f"{over['L']['noiseless']:.4f}); L - D {g:+.4f} (2 SE {2 * se:.4f}) {words[key]}"
            + (f"; OVERSHOOT ({', '.join(k for k in 'DL' if over[k]['overshoots'])}): recorded, not counted for the "
               f"rule" if out_ else ""))

    def pool(ts):
        ok = N = 0
        for t in ts:
            rec, cnt = cards[t]
            s = FF.success_share(cnt, rec["clbits"], {int(b): v for b, v in rec["success"].items()})
            ok += s["success"]
            N += s["counted"]
        return ok / N, N
    ipk = sorted(t for t in cards if t.startswith("ipk4_"))
    (pk, nk), (pu, nu) = pool(ipk), pool([t.replace("ipk", "ipu") for t in ipk])
    se = math.sqrt(pk * (1 - pk) / nk + pu * (1 - pu) / nu)
    gate = RF.word(pk - pu, se)
    say(f"IPE control: parked {pk:.4f} - unparked {pu:.4f} = {pk - pu:+.4f} (2 SE {2 * se:.4f}) {gate} "
        f"(the gate {'open' if gate == 'KEEPS MORE' else 'closed'})")
    d = decision(words, gate, excluded)
    say(f"the rule for the default (counted: {[k for k in ITEMS if k not in excluded] or 'none'}): {d}")
    res.update(control=dict(parked=pk, unparked=pu, d=pk - pu, two_se=2 * se, word=gate), decision=d,
               excluded=excluded)
    json.dump(res, open(os.path.join(a.out, "likely_scores.json"), "w"), indent=1)
    open(os.path.join(a.out, "score.txt"), "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("table").add_argument("out")
    sub.add_parser("pick").add_argument("fetch_in")
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    b.add_argument("--plan", default="B", choices=sorted(PLANS))
    b.add_argument("--dry-clifford-sentinel", action="store_true")
    sub.add_parser("check").add_argument("out")
    d = sub.add_parser("dry")
    d.add_argument("out")
    d.add_argument("noise", choices=sorted(RF.NOISES))
    d.add_argument("--seed", type=int, default=SEED)
    sub.add_parser("score").add_argument("out")
    a = ap.parse_args()
    if a.cmd == "pick":
        print(RF.pick_device(a.fetch_in))
        sys.exit(0)
    r = {"table": table, "build": build, "check": check, "dry": dry, "score": score}[a.cmd](a)
    sys.exit(0 if r is not False else 1)
