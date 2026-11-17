"""Packing tonight's T2 and T4 items into one circuit per arm (home VS Claude, 2026-11-17 evening; desk only, not
declared; psf-os unchanged at feedforward-2026-11-16 / 301ac01).

Items: T2's third design rd1..rd5 (notes/compound_2026-11-17/compound.items) and T4's early chain ea1..ea5
(notes/early_2026-11-17/early.items, off arm = the third design's off arm), in that order.

Placement (the coupling map and the failed marks only, no error number): one rule-C chain (psf_os.chain.place) of N
sites; the items are laid on it in order, each on consecutive sites; after an item one site is skipped, and further
sites are skipped while the next item's first site would be joined by any coupler of the device (working or not) to a
qubit of an earlier item (so no two items touch). N is the smallest length for which every item fits.
The packed logical circuit: the N-site chain, every item on its own sites and its own classical register; ff = the
items' circuits, off = their off arms, floor = psf_os.feedforward.floor_of(ff compiled).

Checks:
  1. entrance: does psf_os.feedforward accept the packed circuit (analyse, form "blocks"; build as one item)?
  2. independence: every instruction (top level and inside conditional blocks) acts on one item's qubits, and every
     classical bit it writes or reads belongs to the same item (then the packed circuit is a product of the items and
     each item's marginal is its own distribution);
  3. per item, the packed compiled circuit restricted to the item equals the item compiled alone (instruction by
     instruction, qubits taken in chain order), and their exact distributions (branching simulation,
     notes/rus_coherent_2026-11-17/coherent.branch_distribution) agree;
  4. ledger (notes/timebudget_2026-11-17/ledger.py, latency 0 and 1 us): per item, the start of its last measurement in
     the packed circuit (ASAP as built and JIT) equals that of the item alone, and its wait is the same; no barrier
     spans two items.
usage: python notes/next_2026-11-17/packing.py DEVDIR [--psf-os PATH]   (writes packing.json, packing.txt here)"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.dirname(os.path.dirname(HERE))
for d in ("notes/early_2026-11-17", "notes/compound_2026-11-17", "notes/rus_coherent_2026-11-17",
          "notes/timebudget_2026-11-17", "gpu"):
    sys.path.insert(0, os.path.join(NB, d))

GAP = 1
LOG = []


def say(s):
    print(s, flush=True)
    LOG.append(s)


def items():
    import compound as CP
    import early as EA
    return CP.items() + EA.items()


def arms_of(tag, qc, spec):
    from psf_os import feedforward as FF
    ff = FF.lower(qc)
    off = FF.lower(spec["off_circuit"]) if spec.get("off_circuit") is not None else FF.strip_conditionals(ff)
    return ff, off


def placement(dev, sizes):
    from psf_os import chain as CH
    adj = {}
    for a, b in dev.all_couplers():
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    N = sum(sizes) + GAP * (len(sizes) - 1)
    while True:
        try:
            pl = CH.place(dev, N)
        except CH.Refused:
            return None
        ch = pl["chain"]
        segs, used, pos, ok = [], set(), 0, True
        for n in sizes:
            while pos + n <= N and any(q in used or adj.get(q, set()) & used for q in ch[pos:pos + n]):
                pos += 1
            if pos + n > N:
                ok = False
                break
            segs.append(list(range(pos, pos + n)))
            used |= set(ch[pos:pos + n])
            pos += n + GAP
        if ok:
            return dict(N=N, chain=list(ch), segments=segs, rule=pl.get("rule"), start=pl.get("start"))
        N += 1


def packed(arms, segs, N, which):
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
    cregs = [ClassicalRegister(arms[i][which].num_clbits, f"c{i}") for i in range(len(arms))]
    out = QuantumCircuit(QuantumRegister(N, "q"), *cregs)
    for i, a in enumerate(arms):
        c = a[which]
        out.compose(c, qubits=segs[i], clbits=list(cregs[i]), inplace=True)
    return out, cregs


def walk_all(qc):
    """(name, [qubit index], [clbit index incl. condition bits]) of every instruction, blocks included."""
    out = []

    def rec(circ, qmap, cmap):
        for ins in circ.data:
            op = ins.operation
            qs = [qmap[circ.find_bit(x).index] for x in ins.qubits]
            cs = [cmap[circ.find_bit(x).index] for x in ins.clbits]
            if op.name == "if_else":
                cb = op.condition[0]
                cs = cs + [cmap[circ.find_bit(cb).index]] if type(cb).__name__ == "Clbit" else cs + ["REG"]
                out.append((op.name, qs, cs))
                for b in op.blocks:
                    if b is not None:
                        rec(b, {b.find_bit(x).index: qs[k] for k, x in enumerate(b.qubits)},
                            {b.find_bit(x).index: cs[k] for k, x in enumerate(b.clbits)} if b.clbits else {})
            else:
                out.append((op.name, qs, cs))
    rec(qc, {i: i for i in range(qc.num_qubits)}, {i: i for i in range(qc.num_clbits)})
    return out


def restrict(qc, qubits, clbits):
    """The compiled circuit's instructions on the given physical qubits (in that order) and clbits (in that order)."""
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
    qi = {q: k for k, q in enumerate(qubits)}
    ci = {c: k for k, c in enumerate(clbits)}
    out = QuantumCircuit(QuantumRegister(len(qubits), "q"), ClassicalRegister(len(clbits), "c"))
    for ins in qc.data:
        qs = [qc.find_bit(x).index for x in ins.qubits]
        if not qs or not set(qs) <= set(qi):
            if qs and set(qs) & set(qi):
                raise ValueError(f"instruction {ins.operation.name} straddles the item")
            continue
        cs = [qc.find_bit(x).index for x in ins.clbits]
        op = ins.operation
        if op.name == "if_else":
            cb = op.condition[0]
            cbit = qc.find_bit(cb).index
            from qiskit.circuit import IfElseOp
            op = IfElseOp((out.clbits[ci[cbit]], op.condition[1]), op.blocks[0].copy(),
                          op.blocks[1] if len(op.blocks) > 1 else None)
            out.append(op, [out.qubits[qi[q]] for q in qs], [out.clbits[ci[c]] for c in cs])
            continue
        out.append(op, [out.qubits[qi[q]] for q in qs], [out.clbits[ci[c]] for c in cs])
    return out


def _ins_sig(qc, ins):
    op = ins.operation
    qs = tuple(qc.find_bit(x).index for x in ins.qubits)
    cs = tuple(qc.find_bit(x).index for x in ins.clbits)
    if op.name == "if_else":
        cond = (qc.find_bit(op.condition[0]).index, int(op.condition[1]))
        return ("if_else", qs, cs, cond, tuple(signature(b) if b is not None else None for b in op.blocks))
    return (op.name, qs, cs, tuple(round(float(p), 12) for p in op.params))


def signature(qc):
    """Per wire (every qubit and every clbit, condition bits included), the instructions on it in order. Two circuits
    with the same signature are the same circuit up to the order in which independent instructions are listed (the
    serialisation of a DAG depends on the physical labels)."""
    wires = {}
    for ins in qc.data:
        s = _ins_sig(qc, ins)
        ws = [("q", i) for i in s[1]] + [("c", i) for i in s[2]]
        if s[0] == "if_else":
            ws.append(("c", s[3][0]))
        for w in ws:
            wires.setdefault(w, []).append(s)
    return tuple(sorted((w, tuple(v)) for w, v in wires.items()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("devdir")
    a = ap.parse_args()
    import coherent as CO
    import ledger as LG
    from psf_os import feedforward as FF
    from psf_os.device import Device
    dev = Device.load(a.devdir)
    its = items()
    arms = [dict(zip(("ff", "off"), arms_of(*it))) for it in its]
    sizes = [ar["ff"].num_qubits for ar in arms]
    pl = placement(dev, sizes)
    N, chain, segs = pl["N"], pl["chain"], pl["segments"]
    say(f"device {dev.name}; items {[t for t, _, _ in its]}; sizes {sizes}; rule-C chain of N = {N} sites from start "
        f"{pl['start']}; segments (chain positions) {[(s[0], s[-1]) for s in segs]}")
    say("physical qubits per item: " + "; ".join(f"{its[i][0]} {[chain[k] for k in s]}" for i, s in enumerate(segs)))
    res = dict(device=dev.name, N=N, chain=chain, segments=segs, items=[t for t, _, _ in its], sizes=sizes, checks={})
    # 1. entrance
    ffp, cregs = packed(arms, segs, N, "ff")
    offp, _ = packed(arms, segs, N, "off")
    try:
        an = FF.analyse(ffp, form="blocks")
        say(f"1. entrance: analyse (form blocks) ACCEPTS the packed circuit: n {an['n']}, clbits {an['clbits']}, "
            f"conditionals {an['conditionals']}, mid {an['mid']}, CZ {an['cz']}")
        ent = dict(analyse="accepted", n=an["n"], clbits=an["clbits"], conditionals=an["conditionals"])
    except FF.Refused as e:
        say(f"1. entrance: analyse REFUSES: {e}")
        ent = dict(analyse=f"refused: {e}")
    try:
        tmp = "/tmp/packing_build"
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
        out0 = cregs[0].size
        rep = FF.build(dev, [("pk", ffp, dict(form="blocks", success={0: 1}, off_circuit=offp))], tmp,
                       sentinel_spec=dict(kind="echo_clifford", D=24))
        say(f"   build as one item: ACCEPTED ({rep['circuits']} circuits, {rep['qpu_seconds_model']} s by the model); "
            f"placed on rule-C chain {rep['items']['pk']['chain'] == chain}; but one item has one success spec / one "
            f"card, so the ten items cannot be scored apart through the entrance as it is")
        ent["build_as_one_item"] = dict(accepted=True, circuits=rep["circuits"], s_model=rep["qpu_seconds_model"],
                                        same_chain=rep["items"]["pk"]["chain"] == chain)
    except FF.Refused as e:
        say(f"   build as one item: REFUSED: {e}")
        ent["build_as_one_item"] = dict(accepted=False, why=str(e))
    # the same packed circuit with one classical register (each item's bits at an offset)
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
    one = {}
    for which in ("ff", "off"):
        nb = sum(ar[which].num_clbits for ar in arms)
        c1 = QuantumCircuit(QuantumRegister(N, "q"), ClassicalRegister(nb, "c"))
        o = 0
        for i, ar in enumerate(arms):
            c = ar[which]
            c1.compose(c, qubits=segs[i], clbits=list(range(o, o + c.num_clbits)), inplace=True)
            o += c.num_clbits
        one[which] = c1
    try:
        an1 = FF.analyse(one["ff"], form="blocks")
        tmp1 = "/tmp/packing_build1"
        import shutil
        shutil.rmtree(tmp1, ignore_errors=True)
        rep1 = FF.build(dev, [("pk", one["ff"], dict(form="blocks", success={0: 1}, off_circuit=one["off"]))], tmp1,
                        sentinel_spec=dict(kind="echo_clifford", D=24))
        say(f"   with one classical register: analyse ACCEPTS (n {an1['n']}, clbits {an1['clbits']}, conditionals "
            f"{an1['conditionals']}); build as one item ACCEPTED ({rep1['circuits']} circuits, "
            f"{rep1['qpu_seconds_model']} s by the model, chain = the packing chain: {rep1['items']['pk']['chain'] == chain})"
            f"; but its card reads one success spec, so the ten items are not scored apart")
        ent["one_register"] = dict(analyse="accepted", build_as_one_item="accepted", circuits=rep1["circuits"],
                                   s_model=rep1["qpu_seconds_model"], same_chain=rep1["items"]["pk"]["chain"] == chain)
    except FF.Refused as e:
        say(f"   with one classical register: REFUSED: {e}")
        ent["one_register"] = dict(refused=str(e))
    res["checks"]["entrance"] = ent
    # compile the packed arms as the entrance does
    comp = FF.Compiler(dev)
    ffc = comp.run(FF.on_device(ffp, chain, dev.num_qubits))
    offc = comp.run(FF.on_device(offp, chain, dev.num_qubits))
    floc = FF.floor_of(ffc)
    acc = {nm: FF.checks(dev, c, chain) for nm, c in (("ff", ffc), ("off", offc), ("floor", floc))}
    say(f"   compiled packed arms: acceptance {acc}; CZ ff {FF.cz_count(ffc)}, off {FF.cz_count(offc)}, floor "
        f"{FF.cz_count(floc)}")
    # 2. independence
    item_q = [set(chain[k] for k in s) for s in segs]
    off_c = [0]
    for cr in cregs:
        off_c.append(off_c[-1] + cr.size)
    item_c = [set(range(off_c[i], off_c[i + 1])) for i in range(len(segs))]
    bad = []
    for nm, c in (("ff", ffc), ("off", offc), ("floor", floc)):
        for name, qs, cs in walk_all(c):
            owners = {i for i in range(len(segs)) if set(qs) & item_q[i]} | \
                     {i for i in range(len(segs)) if set(x for x in cs if x != "REG") & item_c[i]}
            if len(owners) > 1 or "REG" in cs:
                bad.append((nm, name, qs, cs))
    say(f"2. independence: instructions touching more than one item (qubits or bits, blocks included): {len(bad)}"
        + (f" {bad[:5]}" if bad else ""))
    res["checks"]["independence_violations"] = len(bad)
    # 3. per item against the item compiled alone
    rows = []
    for i, (tag, qc, spec) in enumerate(its):
        q_order = [chain[k] for k in segs[i]]
        c_order = sorted(item_c[i])
        alone_pl = FF.place(dev, sizes[i])
        r = dict(tag=tag)
        for nm, pc, logical in (("ff", ffc, arms[i]["ff"]), ("off", offc, arms[i]["off"])):
            sub = restrict(pc, q_order, c_order)
            alone = comp.run(FF.on_device(logical, alone_pl["chain"], dev.num_qubits))
            al = restrict(alone, list(alone_pl["chain"]), list(range(logical.num_clbits)))
            same = signature(sub) == signature(al)
            dp = CO.branch_distribution(sub)
            da = CO.branch_distribution(al)
            r[nm] = dict(same_instructions=same, tvd=float(CO.tvd(dp, da)))
            if nm == "ff":
                sub_ff, al_ff = sub, al
        # 4. ledger
        for lat in (0.0, 1.0):
            for mode, alap in (("asap", False), ("jit", "jit")):
                lp = LG.ledger(sub_ff, latency_us=lat, alap=alap)
                la = LG.ledger(al_ff, latency_us=lat, alap=alap)
                r[f"ledger_{mode}_lat{lat}"] = dict(packed_wait=lp["wait_qus"], alone_wait=la["wait_qus"],
                                                    packed_T=lp["T_us"], alone_T=la["T_us"])
        rows.append(r)
    # last measurement start of each item inside the full packed schedule against the item alone
    for lat in (0.0, 1.0):
        for mode, alap in (("asap", False), ("jit", "jit")):
            ins = LG._instructions(ffc, lat * 1e-6, False)
            st, T = LG._schedule(ins, ffc.num_qubits, ffc.num_clbits, alap)
            for i, r in enumerate(rows):
                last = max((st[k] for k, x in enumerate(ins) if x[2] == "measure" and set(x[0]) <= item_q[i]),
                           default=None)
                sub = restrict(ffc, [chain[k] for k in segs[i]], sorted(item_c[i]))
                ins_a = LG._instructions(sub, lat * 1e-6, False)
                st_a, _ = LG._schedule(ins_a, sub.num_qubits, sub.num_clbits, alap)
                last_a = max(st_a[k] for k, x in enumerate(ins_a) if x[2] == "measure")
                r[f"last_meas_{mode}_lat{lat}"] = dict(packed_us=last * 1e6, alone_us=last_a * 1e6)
            res.setdefault("packed_T_us", {})[f"{mode}_lat{lat}"] = T * 1e6
    span_barriers = sum(1 for name, qs, cs in walk_all(ffc) if name == "barrier" and
                        len({i for i in range(len(segs)) if set(qs) & item_q[i]}) > 1)
    say(f"   barriers spanning two items in the packed ff arm: {span_barriers}")
    res["checks"]["spanning_barriers"] = span_barriers
    say("3-4. per item: same instructions as alone (ff / off), exact distribution total variation (ff / off), ledger "
        "wait packed = alone (ASAP / JIT, latency 0 and 1 us), last measurement start packed = alone")
    allok = True
    for r in rows:
        lw = all(abs(r[k]["packed_wait"] - r[k]["alone_wait"]) < 1e-9 for k in r if k.startswith("ledger_"))
        lm = all(abs(r[k]["packed_us"] - r[k]["alone_us"]) < 1e-6 for k in r if k.startswith("last_meas_"))
        ok = r["ff"]["same_instructions"] and r["off"]["same_instructions"] and r["ff"]["tvd"] < 1e-12 and \
            r["off"]["tvd"] < 1e-12 and lw and lm
        allok &= ok
        say(f"   {r['tag']}: {r['ff']['same_instructions']} / {r['off']['same_instructions']}; tvd {r['ff']['tvd']:.1e} / "
            f"{r['off']['tvd']:.1e}; wait {lw} (JIT lat 0: {r['ledger_jit_lat0.0']['packed_wait']:.2f} q.us, lat 1: "
            f"{r['ledger_jit_lat1.0']['packed_wait']:.2f}); last measurement {lm} (ASAP lat 0 at "
            f"{r['last_meas_asap_lat0.0']['packed_us']:.2f} us) -> {'ok' if ok else 'DIFFERS'}")
    say(f"   packed circuit length (ff, us): " + ", ".join(f"{k} {v:.1f}" for k, v in res["packed_T_us"].items()))
    res["rows"] = rows
    res["all_ok"] = bool(allok and not bad and not span_barriers)
    # time model
    from psf_os import job as J
    per = lambda circuits, jobs: circuits * (0.036 + 0.00027 * 4000) + 3 * jobs
    res["time_model"] = dict(single=dict(circuits=38, jobs=2, s=per(38, 2)), packed=dict(circuits=7, jobs=1, s=per(7, 1)))
    say(f"time model (0.036 s per circuit + 0.00027 s per shot at 4000 shots + 3 s per job): T2 + T4 now 38 circuits in "
        f"2 jobs {per(38, 2):.1f} s; packed 3 arms + 4 sentinel circuits in 1 job {per(7, 1):.1f} s")
    say(f"ALL CHECKS {'PASS' if res['all_ok'] else 'FAIL'}")
    json.dump(res, open(os.path.join(HERE, "packing.json"), "w"), indent=1, default=str)
    open(os.path.join(HERE, "packing.txt"), "w").write("\n".join(LOG) + "\n")


if __name__ == "__main__":
    main()
