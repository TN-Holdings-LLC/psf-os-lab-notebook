"""Two packing tests for the night of 2026-11-18 (home Claude; prereg/parallel_night_2026-11-18.md). Owner 2026-11-18
10:5x JST: "do the parallel tests too", the two forms below.

The fifth round of 2026-11-17 (results/packing-night-2026-11-17): ten feed-forward items packed in one circuit per arm
kept 0.20 less in the control (ff) arm than the same items alone on the same qubits, while the off arm (no
conditionals) agreed within 0.03. Two jobs tonight, each with its own single references in the SAME job and on the
SAME physical qubits:

P-A "pack the fixed circuits only" (OUT/pa): the ten items of 2026-11-17 (rd1..5 notes/compound_2026-11-17, ea1..5
  notes/early_2026-11-17); per item its ff, off and floor arms alone (psf_os.feedforward.build, each item on the qubits
  bundle_place gives it), plus one bundle (build_bundle, tag "pa") whose sub-items "o<tag>" are the items' off arms
  (the explicit off arm where the item has one, else strip_conditionals of the lowered circuit: no conditional), so the bundle holds the ten off arms in one circuit
  (its "off" arm, the reading used) and again (its "ff" arm, the same circuit, beside as a repeat), and their floor.
  The production form this stands for: the ten ff arms alone + one packed off + one packed floor + the sentinel.

P-B "what makes the loss" (OUT/pb): rd2 (gpu/rus3_night.chain(2, 1.1, 2)) on two segments A and B of one rule-C chain
  (bundle_place of two equal items); three bundles and the item alone on A and on B:
    B1  A: rd2 (conditionals)          B: rd2's off arm (mid-circuit measurements, no conditional)
    B2  A: rd2                         B: rd2
    B3  A: rd2                         B: rd2 preceded by a delay on all its qubits longer than A's whole duration
                                          (ledger, ASAP, decision latency 1 us, x 1.25, rounded up to 16 dt), so that
                                          no decision of B falls inside A
    sa, sb  rd2 alone on A, on B.

  python gpu/parallel_night.py build DEVDIR OUT [--dry-clifford-sentinel]     -> OUT/pa, OUT/pb (one job each)
  python gpu/parallel_night.py check OUT
  python gpu/parallel_night.py score OUT

check (prints PASS or FAIL, exits 1 on FAIL; a FAIL means neither job is submitted):
  1. independence: no instruction or barrier of any bundle arm spans two sub-items (bundle_acceptance);
  2. identity: every packed sub-item, restricted to its qubits and bits, has the same instructions per wire as its
     single reference (P-A: packed off arm against the single off arm; P-B: B1 A / B2 A, B / B3 A against the single
     ff arm, B1 B against sb's off arm, B3 B with its delays removed against sb's ff arm) and the same exact
     distribution (notes/rus_coherent_2026-11-17/coherent.branch_distribution, total variation below 1e-12);
  3. the same physical qubits for a sub-item and its single reference;
  4. the recorded acceptance of every arm; no sx / x in a floor; no conditional in an off arm or in a P-A bundle arm;
     conditionals kept in every single ff arm and in B1 A, B2, B3;
  5. timing (ledger, ASAP, latency 0 and 1 us): in B3 the first operation on B's qubits after its delay starts after
     A's last operation ends; B2's overlap printed beside.

score (verdict words as 2026-11-17's packing test; d positive: packed kept more):
  P-A: per item d_off = |s - v| - |p - v|, s the single off arm, p the packed off arm (the bundle's "off"), v the
       noiseless off value (notes/compound_2026-11-17/ideal.json); the mean over ten items with its 2 SE. Verdict on the
       mean: PACKING KEEPS LESS (mean <= -2 SE) / PACKING KEEPS MORE (mean >= 2 SE) / SAME WITHIN ERROR. Beside: the
       per-item words, the repeat (the bundle's "ff"), CLOSER WITH CONTROL per item with the single and with the packed
       off arm, the floors, the seconds of the production form by the time model.
  P-B: per sub-item with conditionals d = |s - v| - |p - v|, s its single reference's ff, p its ff in the bundle, v the
       noiseless ff value of rd2; per bundle the mean over its sub-items with conditionals (B1: A only; B2, B3: A and
       B) with its 2 SE; the same three words per bundle (PACKED KEEPS LESS / PACKED KEEPS MORE / SAME WITHIN ERROR).
       Beside: B1 B (a fixed circuit packed) against sb's off arm; the share still failing after the second try; the
       floors; the reading table (fixed before the data, in the declaration)."""
import argparse
import json
import math
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
for d in ("notes/early_2026-11-17", "notes/compound_2026-11-17", "notes/rus_coherent_2026-11-17",
          "notes/timebudget_2026-11-17"):
    sys.path.insert(0, os.path.join(NB, d))

SHOTS = 4000
MAX_S = 60
THETA, M = 1.1, 2
GRAN = 16                      # delay granularity in dt (as notes/next_2026-11-17/pin_delay.py)
DELAY_FACTOR = 1.25
SPEC_DRY = dict(kind="echo_clifford", D=24)


def ref():
    return {int(k): v for k, v in json.load(open(os.path.join(NB, "notes", "compound_2026-11-17", "ideal.json"))).items()}


def items_a():
    import compound as CP
    import early as EA
    return CP.items() + EA.items()


def rd2():
    import rus3_night as R3
    return R3.chain(2, THETA, m=M)


def offvariant(qc, spec):
    """The item's off arm as a circuit of its own, the same logical circuit build() compiles as the item's off arm:
    the explicit off arm when the spec gives one (the early chain's off arm is the third design's), otherwise the
    conditionals removed from the lowered circuit."""
    from psf_os import feedforward as FF
    off = (spec or {}).get("off_circuit")
    return FF.lower(off) if off is not None else FF.strip_conditionals(FF.lower(qc))


def delayed(qc, n_dt):
    """qc preceded by a delay of n_dt dt on every qubit (top level; accepted by psf-os 871d9e6 and later)."""
    from qiskit.circuit import Delay
    out = qc.copy_empty_like()
    for q in out.qubits:
        out.append(Delay(n_dt, "dt"), [q])
    out.compose(qc, inplace=True)
    return out


def without_delays(qc):
    out = qc.copy_empty_like()
    for ins in qc.data:
        if ins.operation.name != "delay":
            out.append(ins.operation, ins.qubits, ins.clbits)
    return out


def _length(c, latency_us):
    """ASAP length (s) of a compiled circuit by the ledger's gate lengths, barriers kept."""
    import ledger as LG
    ins = LG._instructions(c, latency_us * 1e-6, False)
    _, T = LG._schedule(ins, c.num_qubits, c.num_clbits, False)
    return T


def _merge(dev, parts, runs, job, skip_sentinel):
    """Copy the records of several builds into one runs folder (the sentinel of the first build only) and assemble
    one job."""
    from psf_os import job as J
    os.makedirs(runs)
    for k, p in enumerate(parts):
        for f in sorted(os.listdir(os.path.join(p, "runs"))):
            if k > 0 and skip_sentinel(f):
                continue
            dst = os.path.join(runs, f)
            if os.path.exists(dst):
                raise RuntimeError(f"two records named {f}")
            shutil.copy2(os.path.join(p, "runs", f), dst)
    return J.assemble(dev, runs, job, max_seconds=MAX_S)


def _is_sentinel(f):
    return not f.startswith("ff_")


def build(a):
    from psf_os import feedforward as FF
    from psf_os import job as J
    from psf_os.device import Device
    import ledger as LG
    if os.path.exists(a.out):
        print(f"REFUSED: {a.out} exists")
        return False
    dev = Device.load(a.devdir)
    spec = SPEC_DRY if a.dry_clifford_sentinel else None          # dry runs only, never a device
    tmp = tempfile.mkdtemp(prefix="parallel_night_")
    try:
        # ---------------------------------------------------------------- P-A
        its = items_a()
        offs = [(f"o{t}", offvariant(qc, sp), sp) for t, qc, sp in its]
        pa_b = FF.build_bundle(dev, offs, os.path.join(tmp, "pa_bundle"), tag="pa", shots=SHOTS, max_seconds=MAX_S,
                               sentinel_spec=spec)
        chains_a = {t: pa_b["items"][f"o{t}"]["chain"] for t, _, _ in its}
        pa_s = FF.build(dev, its, os.path.join(tmp, "pa_single"), shots=SHOTS, max_seconds=MAX_S, sentinel_spec=spec,
                        chains=chains_a)
        os.makedirs(os.path.join(a.out, "pa"))
        man_a = _merge(dev, [os.path.join(tmp, "pa_single"), os.path.join(tmp, "pa_bundle")],
                       os.path.join(a.out, "pa", "runs"), os.path.join(a.out, "pa", "job"), _is_sentinel)
        n = len(its)
        plan_a = dict(items=[t for t, _, _ in its], chains=chains_a, bundle_chain=pa_b["chain"],
                      bundle_segments=pa_b["segments"], circuits=len(man_a["pubs"]),
                      s_model=man_a["qpu_seconds_model"],
                      production=dict(circuits=n + 2 + 4, s_model=J.qpu_seconds(n + 2 + 4, SHOTS)),
                      all_single=dict(circuits=3 * n + 4, s_model=J.qpu_seconds(3 * n + 4, SHOTS)),
                      build_single=pa_s, build_bundle=pa_b)
        # ---------------------------------------------------------------- P-B
        qc, sp = rd2()
        nq = FF._prepare("rd2", qc, sp)[0]["n"]
        pl = FF.bundle_place(dev, [nq, nq])
        chA = [pl["chain"][k] for k in pl["segments"][0]]
        chB = [pl["chain"][k] for k in pl["segments"][1]]
        pb_s = FF.build(dev, [("sa", qc, sp), ("sb", qc, sp)], os.path.join(tmp, "pb_single"), shots=SHOTS,
                        max_seconds=MAX_S, sentinel_spec=spec, chains={"sa": chA, "sb": chB})
        from qiskit import qpy
        (cA,) = qpy.load(open(os.path.join(tmp, "pb_single", "runs", "ff_sa.qpy"), "rb"))
        T = _length(cA, 1.0)
        dt = LG.lengths()["dt"]
        n_dt = int(math.ceil(DELAY_FACTOR * T / dt / GRAN)) * GRAN
        bundles = {
            "B1": [("b1a", qc, sp), ("b1b", offvariant(qc, sp), sp)],
            "B2": [("b2a", qc, sp), ("b2b", qc, sp)],
            "B3": [("b3a", qc, sp), ("b3b", delayed(qc, n_dt), sp)],
        }
        reps = {}
        for name, subs in bundles.items():
            reps[name] = FF.build_bundle(dev, subs, os.path.join(tmp, f"pb_{name}"), tag=name, shots=SHOTS,
                                         max_seconds=MAX_S, sentinel_spec=spec)
            got = [reps[name]["items"][s]["chain"] for s, _, _ in subs]
            if got != [chA, chB]:
                raise FF.Refused(f"{name}: placed on {got}, the singles on {[chA, chB]}")
        os.makedirs(os.path.join(a.out, "pb"))
        man_b = _merge(dev, [os.path.join(tmp, "pb_single")] + [os.path.join(tmp, f"pb_{k}") for k in bundles],
                       os.path.join(a.out, "pb", "runs"), os.path.join(a.out, "pb", "job"), _is_sentinel)
        plan_b = dict(chain_A=chA, chain_B=chB, bundle_chain=pl["chain"], segments=pl["segments"],
                      delay=dict(n_dt=n_dt, dt_s=dt, seconds=n_dt * dt, A_length_s=T, factor=DELAY_FACTOR, gran=GRAN),
                      circuits=len(man_b["pubs"]), s_model=man_b["qpu_seconds_model"],
                      build_single=pb_s, build_bundles=reps)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    plan = dict(device=dev.name, dry_clifford_sentinel=bool(a.dry_clifford_sentinel), pa=plan_a, pb=plan_b,
                s_model_total=plan_a["s_model"] + plan_b["s_model"])
    json.dump(plan, open(os.path.join(a.out, "plan.json"), "w"), indent=1, default=str)
    print(f"{dev.name}: P-A {plan_a['circuits']} circuits {plan_a['s_model']:.1f} s (production form "
          f"{plan_a['production']['circuits']} circuits {plan_a['production']['s_model']:.1f} s against all single "
          f"{plan_a['all_single']['circuits']} circuits {plan_a['all_single']['s_model']:.1f} s); P-B "
          f"{plan_b['circuits']} circuits {plan_b['s_model']:.1f} s (A {chA}, B {chB}, B3 delay {n_dt} dt = "
          f"{n_dt * dt * 1e6:.2f} us against A's length {T * 1e6:.2f} us); total {plan['s_model_total']:.1f} s")


# ------------------------------------------------------------------------------------------------ check

def _rec(folder, name):
    from qiskit import qpy
    rec = json.load(open(os.path.join(folder, "runs", name + ".json")))
    (c,) = qpy.load(open(os.path.join(folder, "runs", name + ".qpy"), "rb"))
    return rec, c


def _same(mine, ref_c):
    import coherent as CO
    from psf_os import feedforward as FF
    same = FF.wire_signature(mine) == FF.wire_signature(ref_c)
    tv = float(CO.tvd(CO.branch_distribution(mine), CO.branch_distribution(ref_c)))
    return same, tv


def _ops(c):
    from psf_os import feedforward as FF
    return {nm for nm, _ in FF.walk(c)}


def check(a):
    from psf_os import feedforward as FF
    plan = json.load(open(os.path.join(a.out, "plan.json")))
    bad = []

    def arms(folder, tag):
        return {arm: _rec(folder, f"ff_{tag}" + ("" if arm == "ff" else f"_{arm}")) for arm in ("ff", "off", "floor")}

    def restrict_sub(c, info):
        return FF.restrict(c, info["qubits"], list(range(info["bit_offset"], info["bit_offset"] + info["clbits"])))

    def restrict_single(rec, c):
        return FF.restrict(c, rec["chain"], list(range(rec["clbits"])))

    def acceptance(name, ar, kind):
        f = []
        for arm, (rec, c) in ar.items():
            ops = _ops(c)
            if not all(rec["checks"].values()):
                f.append((name, arm, "acceptance"))
            if arm == "floor" and ops & {"sx", "x"}:
                f.append((name, arm, "sx/x in floor"))
            if arm == "off" and "if_else" in ops:
                f.append((name, arm, "conditional in off"))
            if arm == "ff" and kind == "cond" and "if_else" not in ops:
                f.append((name, arm, "no conditional in ff"))
            if arm == "ff" and kind == "fixed" and "if_else" in ops:
                f.append((name, arm, "conditional in a fixed bundle"))
        return f

    # ---------------------------------------------------------------- P-A
    pa = os.path.join(a.out, "pa")
    pb_ = arms(pa, "pa")
    table = pb_["ff"][0]["bundle"]
    tags = plan["pa"]["items"]
    try:
        FF.bundle_acceptance({k: v[1] for k, v in pb_.items()}, [set(table[f"o{t}"]["qubits"]) for t in tags],
                             [set(range(table[f"o{t}"]["bit_offset"], table[f"o{t}"]["bit_offset"] +
                                        table[f"o{t}"]["clbits"])) for t in tags])
        print("P-A 1. independence: ok")
    except FF.Refused as e:
        print(f"P-A 1. independence: FAIL {e}")
        bad.append("pa independence")
    f4 = acceptance("pa", pb_, "fixed")
    worst = 0.0
    for t in tags:
        s = arms(pa, t)
        f4 += acceptance(t, s, "cond")
        info = table[f"o{t}"]
        if s["ff"][0]["chain"] != info["qubits"]:
            bad.append(f"pa qubits {t}")
        ref_off = restrict_single(*s["off"])
        for arm in ("off", "ff"):
            same, tv = _same(restrict_sub(pb_[arm][1], info), ref_off)
            worst = max(worst, tv)
            if not same or tv > 1e-12:
                bad.append(f"pa identity {t} {arm}")
    print(f"P-A 2. identity, packed off arms (bundle off and its repeat) against the single off arms: "
          f"{'ok' if not [b for b in bad if 'identity' in b] else 'FAIL'} (largest TV {worst:.1e})")
    print(f"P-A 3. the same physical qubits: {'ok' if not [b for b in bad if 'pa qubits' in b] else 'FAIL'}")
    print(f"P-A 4. acceptance and arms: {'ok' if not f4 else 'FAIL ' + str(f4)}")
    bad += [f"pa arms {x}" for x in f4]
    # ---------------------------------------------------------------- P-B
    pbf = os.path.join(a.out, "pb")
    sa, sb = arms(pbf, "sa"), arms(pbf, "sb")
    g4 = acceptance("sa", sa, "cond") + acceptance("sb", sb, "cond")
    if sa["ff"][0]["chain"] != plan["pb"]["chain_A"] or sb["ff"][0]["chain"] != plan["pb"]["chain_B"]:
        bad.append("pb single qubits")
    refs = {"A": {"ff": restrict_single(*sa["ff"])}, "B": {"ff": restrict_single(*sb["ff"]),
                                                           "off": restrict_single(*sb["off"])}}
    worst = 0.0
    timing = {}
    for name, (subA, subB, kindB) in {"B1": ("b1a", "b1b", "off"), "B2": ("b2a", "b2b", "ff"),
                                       "B3": ("b3a", "b3b", "ff_delayed")}.items():
        ar = arms(pbf, name)
        tb = ar["ff"][0]["bundle"]
        try:
            FF.bundle_acceptance({k: v[1] for k, v in ar.items()}, [set(tb[s]["qubits"]) for s in (subA, subB)],
                                 [set(range(tb[s]["bit_offset"], tb[s]["bit_offset"] + tb[s]["clbits"]))
                                  for s in (subA, subB)])
        except FF.Refused as e:
            bad.append(f"pb independence {name}: {e}")
        g4 += acceptance(name, ar, "cond")
        if tb[subA]["qubits"] != plan["pb"]["chain_A"] or tb[subB]["qubits"] != plan["pb"]["chain_B"]:
            bad.append(f"pb qubits {name}")
        same, tv = _same(restrict_sub(ar["ff"][1], tb[subA]), refs["A"]["ff"])
        worst = max(worst, tv)
        if not same or tv > 1e-12:
            bad.append(f"pb identity {name} A")
        mineB = restrict_sub(ar["ff"][1], tb[subB])
        if kindB == "ff_delayed":
            if "delay" not in _ops(mineB):
                bad.append(f"pb {name} B: the delay is not in the compiled circuit")
            mineB = without_delays(mineB)
        same, tv = _same(mineB, refs["B"]["off" if kindB == "off" else "ff"])
        worst = max(worst, tv)
        if not same or tv > 1e-12:
            bad.append(f"pb identity {name} B")
        # timing (ledger, ASAP, barriers kept)
        import ledger as LG
        c = ar["ff"][1]
        qA, qB = set(tb[subA]["qubits"]), set(tb[subB]["qubits"])
        for lat in (0.0, 1.0):
            ins = LG._instructions(c, lat * 1e-6, False)
            st, _ = LG._schedule(ins, c.num_qubits, c.num_clbits, False)
            endA = max(st[k] + x[3] + (x[5] if x[2] == "if_else" else 0.0)
                       for k, x in enumerate(ins) if set(x[0]) & qA and x[2] != "barrier")
            startB = min(st[k] for k, x in enumerate(ins) if set(x[0]) & qB and x[2] not in ("barrier", "delay"))
            timing[f"{name}_lat{lat:g}"] = dict(A_end_us=endA * 1e6, B_first_us=startB * 1e6)
        if name == "B3" and not all(timing[f"B3_lat{l:g}"]["B_first_us"] > timing[f"B3_lat{l:g}"]["A_end_us"]
                                    for l in (0.0, 1.0)):
            bad.append("pb timing B3: B starts before A ends")
    print(f"P-B 1. independence (B1, B2, B3): {'ok' if not [b for b in bad if 'pb independence' in b] else 'FAIL'}")
    print(f"P-B 2. identity against the singles (B3 B without its delay): "
          f"{'ok' if not [b for b in bad if 'pb identity' in b or 'delay is not' in b] else 'FAIL'} "
          f"(largest TV {worst:.1e})")
    print(f"P-B 3. the same physical qubits: {'ok' if not [b for b in bad if 'qubits' in b and 'pb' in b] else 'FAIL'}"
          f" (A {plan['pb']['chain_A']}, B {plan['pb']['chain_B']})")
    print(f"P-B 4. acceptance and arms: {'ok' if not g4 else 'FAIL ' + str(g4)}")
    bad += [f"pb arms {x}" for x in g4]
    for k, v in timing.items():
        print(f"P-B 5. {k}: A ends {v['A_end_us']:.2f} us, B's first operation {v['B_first_us']:.2f} us"
              + ("" if not k.startswith("B3") else (" ok" if v["B_first_us"] > v["A_end_us"] else " FAIL")))
    json.dump(dict(bad=bad, timing=timing), open(os.path.join(a.out, "check.json"), "w"), indent=1)
    print("PASS" if not bad else f"FAIL {bad}")
    return not bad


# ------------------------------------------------------------------------------------------------ score

def word(d, two_se, overall=False):
    pre = "PACKING" if overall else "PACKED"
    if d <= -two_se:
        return f"{pre} KEEPS LESS"
    if d >= two_se:
        return f"{pre} KEEPS MORE"
    return "SAME WITHIN ERROR"


def charged(folder):
    f = os.path.join(folder, "job", "raw_counts.json")
    if not os.path.exists(f):
        return None
    return json.load(open(f)).get("metrics", {}).get("usage", {}).get("qpu_charge_time_seconds")


def _se(p, n):
    return math.sqrt(p * (1 - p) / n)


def score(a):
    import rus3_night as R3
    from psf_os import feedforward as FF
    plan = json.load(open(os.path.join(a.out, "plan.json")))
    R = ref()
    out = {}
    # ---------------------------------------------------------------- P-A
    pa = os.path.join(a.out, "pa")
    c = {k: R3.relabel(v) for k, v in FF.cards(pa).items()}
    rows, ds, ses = {}, [], []
    print("P-A: the off arm packed (ten in one circuit) against alone, the same job and qubits")
    for t in plan["pa"]["items"]:
        L = int(t[2:])
        s_c, p_c = c[t], c[f"o{t}"]
        s, ns = s_c["off"]["p1"], s_c["off"]["counted"]
        p, npk = p_c["off"]["p1"], p_c["off"]["counted"]
        rep = p_c["ff"]["p1"]
        v, ex = R[L]["off"], s_c["exact"]
        d = abs(s - v) - abs(p - v)
        se = math.sqrt(_se(s, ns) ** 2 + _se(p, npk) ** 2)
        f, nf = s_c["ff"]["p1"], s_c["ff"]["counted"]
        closer = {}
        for which, o, no in (("single off", s, ns), ("packed off", p, npk)):
            dc = abs(o - ex) - abs(f - ex)
            sc = math.sqrt(_se(f, nf) ** 2 + _se(o, no) ** 2)
            closer[which] = dict(d=dc, two_se=2 * sc,
                                 verdict="CLOSER WITH CONTROL" if dc > 0 and dc >= 2 * sc else "NOT CLOSER")
        rows[t] = dict(L=L, single_off=s, packed_off=p, packed_repeat=rep, noiseless_off=v, d=d, two_se=2 * se,
                       beside=word(d, 2 * se), ff_single=f, closer=closer, floor_single=s_c["floor"]["all_zero"],
                       floor_packed=p_c["floor"]["all_zero"])
        ds.append(d)
        ses.append(se)
        print(f"  {t}: off alone {s:.4f}  packed {p:.4f} (repeat {rep:.4f})  noiseless {v:.4f}  d {d:+.4f} (2 SE "
              f"{2 * se:.4f}) -> beside: {rows[t]['beside']};  CLOSER with the single / packed off: "
              f"{closer['single off']['verdict']} / {closer['packed off']['verdict']}")
    m = sum(ds) / len(ds)
    msd = math.sqrt(sum(x * x for x in ses)) / len(ses)
    out["pa"] = dict(rows=rows, mean_d=m, mean_two_se=2 * msd, verdict=word(m, 2 * msd, overall=True),
                     production=plan["pa"]["production"], all_single=plan["pa"]["all_single"],
                     sentinel=next(iter(c.values()))["sentinel"], charged=charged(pa))
    print(f"  mean d over {len(ds)} items {m:+.4f} (2 SE {2 * msd:.4f}) -> {out['pa']['verdict']}")
    print(f"  production form by the model: {plan['pa']['production']['circuits']} circuits "
          f"{plan['pa']['production']['s_model']:.1f} s against all single {plan['pa']['all_single']['circuits']} "
          f"circuits {plan['pa']['all_single']['s_model']:.1f} s; sentinel {out['pa']['sentinel']}; charged "
          f"{out['pa']['charged']}")
    # ---------------------------------------------------------------- P-B
    pbf = os.path.join(a.out, "pb")
    c = {k: R3.relabel(v) for k, v in FF.cards(pbf).items()}
    v = R[2]["ff"]
    print(f"P-B: rd2 packed with one neighbour against alone, the same job and qubits (noiseless ff {v:.4f})")
    sub = {}
    for name, ref_tag in (("b1a", "sa"), ("b2a", "sa"), ("b2b", "sb"), ("b3a", "sa"), ("b3b", "sb")):
        s, ns = c[ref_tag]["ff"]["p1"], c[ref_tag]["ff"]["counted"]
        p, npk = c[name]["ff"]["p1"], c[name]["ff"]["counted"]
        d = abs(s - v) - abs(p - v)
        se = math.sqrt(_se(s, ns) ** 2 + _se(p, npk) ** 2)
        sub[name] = dict(single=s, packed=p, d=d, se=se, still_failed_packed=c[name]["ff"].get("still_failed_after_m"),
                         still_failed_single=c[ref_tag]["ff"].get("still_failed_after_m"),
                         off_packed=c[name]["off"]["p1"], off_single=c[ref_tag]["off"]["p1"],
                         floor_packed=c[name]["floor"]["all_zero"], floor_single=c[ref_tag]["floor"]["all_zero"])
        print(f"  {name} against {ref_tag}: alone {s:.4f}  packed {p:.4f}  d {d:+.4f} (2 SE {2 * se:.4f}); still "
              f"failing after the second try {sub[name]['still_failed_single']:.3f} / {sub[name]['still_failed_packed']:.3f}")
    bundles = {}
    for name, members in (("B1", ["b1a"]), ("B2", ["b2a", "b2b"]), ("B3", ["b3a", "b3b"])):
        dm = sum(sub[x]["d"] for x in members) / len(members)
        sm = math.sqrt(sum(sub[x]["se"] ** 2 for x in members)) / len(members)
        bundles[name] = dict(members=members, mean_d=dm, two_se=2 * sm, verdict=word(dm, 2 * sm))
        print(f"  {name}: mean d {dm:+.4f} (2 SE {2 * sm:.4f}) -> {bundles[name]['verdict']}")
    s, ns = c["sb"]["off"]["p1"], c["sb"]["off"]["counted"]
    p, npk = c["b1b"]["ff"]["p1"], c["b1b"]["ff"]["counted"]
    vo = R[2]["off"]
    dfix = abs(s - vo) - abs(p - vo)
    sfix = math.sqrt(_se(s, ns) ** 2 + _se(p, npk) ** 2)
    print(f"  beside: B1 B (rd2's off arm packed beside a conditional item) {p:.4f} against sb's off arm {s:.4f}: d "
          f"{dfix:+.4f} (2 SE {2 * sfix:.4f})")
    out["pb"] = dict(sub=sub, bundles=bundles, fixed_beside=dict(single_off=s, packed=p, d=dfix, two_se=2 * sfix),
                     delay=plan["pb"]["delay"], sentinel=c["sa"]["sentinel"], charged=charged(pbf))
    print(f"  sentinel {out['pb']['sentinel']}; charged {out['pb']['charged']}")
    json.dump(out, open(os.path.join(a.out, "parallel_scores.json"), "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    b = sp.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    b.add_argument("--dry-clifford-sentinel", action="store_true",
                   help="a Clifford echo sentinel instead of the ring (dry runs only; never for a device)")
    sp.add_parser("check").add_argument("out")
    sp.add_parser("score").add_argument("out")
    a = ap.parse_args()
    res = {"build": build, "check": check, "score": score}[a.cmd](a)
    sys.exit(0 if res is not False else 1)
