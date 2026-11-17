"""Packing estimate (workplace VS Claude, 2026-11-17; the workplace request 17f; desk only, not declared, psf-os
unchanged).

How many device seconds would be saved if items that do not touch each other ran side by side in one circuit, on
qubits apart? For each feed-forward job (psf_os.feedforward.build output; tonight's three jobs):

  placement   the items in build order. Each item gets a chain by rule C (psf_os.chain.place: the coupling graph and
              the failed marks only, no error number) on the device with every qubit already used in the group, and
              every neighbour of one, marked unusable: so between two items there is at least one qubit, and no
              coupler joins them. The first item of a group gets the chain of the single build. When rule C finds no
              chain, the group is closed and a new one starts.
  circuits    per group three circuits: the ff arms of its items side by side, the off arms, the floor arms. Each
              item keeps one chain for its three arms (as in the single build, where ff, off and floor share the
              qubits). The compiled arms are moved from their single chain to the new one qubit by qubit (chain[k] to
              chain'[k]; both are rule C chains, so every CZ lands on a working coupler of the new chain); each item
              keeps its own classical register. The job's sentinel stays as built (4 circuits).
  seconds     the project's time model (psf_os.job.qpu_seconds: 36 ms per circuit + 0.27 ms per shot + 3 s per job),
              same shots. The model has no term for a circuit's length; the ledger's T is given beside.
  checks      (a) acceptance: every instruction on one item's chain only, every two-qubit gate on a working coupler of
              that chain, no coupler between two items' qubits; (b) identity: each item's part of a packed circuit
              (its qubits and its register) holds the same operations in the same order as its single circuit
              (structural, exact: the items share no qubit and no bit, so the packed distribution is the product of
              the items' distributions); and the exact branching simulation (coherent.branch_distribution) of the
              whole packed circuit, each item's marginal against its single circuit, total variation <= 1e-12, where
              the packed circuit fits (qubits + measurements <= 24), else of its first two items packed alone (a
              sample check of the same construction); (c) the ledger (ledger.py) of each packed circuit
              against its items' single ledgers: T, and the wait as the ledger counts it (any other qubit's
              measurement counts, so another item's measurements count too) beside the sum of the single waits.

Lengths are ledger.py's (FakeMarrakesh medians, illustrative); no error number is read. Running packed on a device
would be a declared condition: single and packed compared on the same night.

  python pack.py DEVDIR OUTDIR [OUTDIR ...] [--latency-us X] [--json FILE]
"""
import argparse
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "rus_coherent_2026-11-17"))

import ledger as LG  # noqa: E402
import schedule_pass as SP  # noqa: E402

TVD_MAX = 1e-12
SIM_MAX = 24
ARMS = (("user", ""), ("off", "_off"), ("floor", "_floor"))


def blocked_device(dev, used):
    """A copy of dev with the used qubits and all their neighbours marked failed (rule C then keeps a gap)."""
    nb = set(used)
    for a, b in dev.working_couplers():
        if a in used:
            nb.add(b)
        if b in used:
            nb.add(a)
    for a, b in (tuple(e) for e in dev.failed_couplers):
        if a in used:
            nb.add(b)
        if b in used:
            nb.add(a)
    d = copy.deepcopy(dev)
    d.failed_qubits = sorted(set(dev.failed_qubits) | nb)
    return d


def groups_of(dev, items):
    """items: [(tag, n)] in build order -> [[(tag, chain)]]."""
    from psf_os import chain as CH
    groups, cur, used = [], [], set()
    for tag, n in items:
        try:
            ch = CH.place(blocked_device(dev, used), n)["chain"]
        except CH.Refused:
            groups.append(cur)
            cur, used = [], set()
            ch = CH.place(dev, n)["chain"]
        cur.append((tag, ch))
        used |= set(ch)
    if cur:
        groups.append(cur)
    return groups


def moved(c, old_chain, new_chain):
    """(compact circuit, list of new physical qubits in the compact order) of a compiled single arm."""
    from psf_os import feedforward as FF
    act = sorted({q for _, qs in FF.walk(c) for q in qs})
    pos = {q: i for i, q in enumerate(old_chain)}
    return FF.compact(c), [new_chain[pos[q]] for q in act]


def packed_circuit(width, parts):
    """parts: [(tag, compact circuit, new physical qubits)] -> one width-qubit circuit, one register per item."""
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
    regs = [ClassicalRegister(cc.num_clbits, f"c_{tag}") for tag, cc, _ in parts]
    out = QuantumCircuit(QuantumRegister(width, "q"), *regs)
    for (tag, cc, phys), reg in zip(parts, regs):
        out.compose(cc, qubits=phys, clbits=list(reg), inplace=True)
    return out, regs


def acceptance(dev, packed, chains):
    from psf_os import feedforward as FF
    work = {tuple(sorted(e)) for e in dev.working_couplers()}
    owner = {q: t for t, ch in chains.items() for q in ch}
    links = {t: {tuple(sorted(e)) for e in zip(ch, ch[1:])} for t, ch in chains.items()}
    one_item = on_links = True
    for name, qs in FF.walk(packed):
        if name == "barrier" and not qs:
            continue
        ts = {owner.get(q) for q in qs}
        if len(ts) != 1 or None in ts:
            one_item = False
            continue
        if len(qs) == 2 and name != "barrier":
            t = ts.pop()
            if tuple(sorted(qs)) not in links[t] or tuple(sorted(qs)) not in work:
                on_links = False
    cross = [e for e in work if e[0] in owner and e[1] in owner and owner[e[0]] != owner[e[1]]]
    return dict(one_item_per_instruction=one_item, couplers_on_own_chain=on_links, no_coupler_between_items=not cross,
                qubits_ok=all(dev.qubit_ok(q) for q in owner))


def item_part(packed, phys, reg):
    """The instructions of packed on these qubits and this register, as a compact circuit like the single one."""
    from qiskit import QuantumCircuit, QuantumRegister
    from qiskit.circuit import ClassicalRegister
    qset = {packed.qubits[q] for q in phys}
    qidx = {packed.qubits[q]: i for i, q in enumerate(phys)}
    creg = ClassicalRegister(len(reg), "c")
    cidx = {b: i for i, b in enumerate(reg)}
    out = QuantumCircuit(QuantumRegister(len(phys), "q"), creg)
    for ins in packed.data:
        if not set(ins.qubits) <= qset:
            continue
        op = ins.operation
        if op.name == "if_else":
            bit, val = op.condition
            op = op.replace_blocks(op.blocks)
            op.condition = (creg[cidx[bit]], val)
        out.append(op, [out.qubits[qidx[x]] for x in ins.qubits], [creg[cidx[b]] for b in ins.clbits])
    return out


def marginal(dist, reg_positions):
    """dist keys c[n-1]..c[0] over the packed register order -> keys over the item's bits."""
    out = {}
    for k, p in dist.items():
        bits = k[::-1]
        kk = "".join(bits[i] for i in reg_positions)[::-1]
        out[kk] = out.get(kk, 0.0) + p
    return out


def job(dev, out, latency_us):
    from qiskit import qpy
    from psf_os import feedforward as FF
    from psf_os import job as J
    from coherent import branch_distribution, tvd
    b = json.load(open(os.path.join(out, "build.json")))
    m = json.load(open(os.path.join(out, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(out, "job", "circuits.qpy"), "rb"))
    circ, i, sentinel = {}, 0, 0
    for cell in m["cells"]:
        for _ in range(cell["points"]):
            circ[cell["name"]] = cs[i]
            i += 1
        if cell["role"] == "sentinel":
            sentinel += cell["points"]
    tags = list(b["items"])
    groups = groups_of(dev, [(t, b["items"][t]["n"]) for t in tags])
    res = dict(items=len(tags), groups=[[dict(tag=t, chain=ch) for t, ch in g] for g in groups],
               circuits_single=b["circuits"], seconds_single=J.qpu_seconds(b["circuits"], b["shots"]),
               circuits_packed=3 * len(groups) + sentinel, sentinel_circuits=sentinel, arms={})
    res["seconds_packed"] = J.qpu_seconds(res["circuits_packed"], b["shots"])
    for gi, g in enumerate(groups):
        chains = dict(g)
        for role, suf in ARMS:
            parts = []
            for t, ch in g:
                cc, phys = moved(circ[f"ff_{t}{suf}"], b["items"][t]["chain"], ch)
                parts.append((t, cc, phys))
            packed, regs = packed_circuit(dev.num_qubits, parts)
            acc = acceptance(dev, packed, chains)
            same = {t: SP.same_dag(cc, item_part(packed, phys, reg)) for (t, cc, phys), reg in zip(parts, regs)}
            pc = FF.compact(packed)

            def fits(c):
                return c.num_qubits + sum(1 for x in c.data if x.operation.name == "measure") <= SIM_MAX

            # the whole packed circuit where it fits; otherwise the first two items packed alone (a sample check of
            # the same construction; the structural identity above covers every item)
            sim, sim_scope = None, None
            for scope, sub in (("whole", parts), ("first two items", parts[:2])):
                if len(sub) < 2:
                    continue
                pk, rg = packed_circuit(dev.num_qubits, sub) if scope != "whole" else (packed, regs)
                pkc = FF.compact(pk)
                if not fits(pkc):
                    continue
                dp = branch_distribution(pkc)
                pos, sim, sim_scope = 0, {}, scope
                for (t, cc, _), reg in zip(sub, rg):
                    sim[t] = float(tvd(branch_distribution(cc), marginal(dp, list(range(pos, pos + len(reg))))))
                    pos += len(reg)
                break
            led, single = {}, {}
            for ex, mode in (("asap", False), ("jit", "jit")):
                lp = LG.ledger(pc, latency_us, mode, False)
                ls = [LG.ledger(cc, latency_us, mode, False) for _, cc, _ in parts]
                led[ex] = dict(T_us=lp["T_us"], wait_qus=lp["wait_qus"])
                single[ex] = dict(T_us_max=max(x["T_us"] for x in ls), wait_qus_sum=sum(x["wait_qus"] for x in ls))
            res["arms"][f"group{gi + 1}_{role}"] = dict(
                items=[t for t, _ in g], qubits=sum(len(ch) for _, ch in g), acceptance=acc, same_dag=same,
                tvd=sim, simulated=sim_scope, identity=all(same.values()) and all(acc.values()) and
                (sim is None or max(sim.values()) <= TVD_MAX), ledger=led, single=single)
    return res


def show(name, r):
    print(f"== {name}: {r['items']} items in {len(r['groups'])} group(s); circuits {r['circuits_single']} -> "
          f"{r['circuits_packed']} (sentinel {r['sentinel_circuits']} kept); model seconds {r['seconds_single']:.1f} "
          f"-> {r['seconds_packed']:.1f}")
    for gi, g in enumerate(r["groups"]):
        print(f"  group {gi + 1}: " + ", ".join(f"{x['tag']} {x['chain'][0]}..{x['chain'][-1]} ({len(x['chain'])})"
                                             for x in g))
    for k, a in r["arms"].items():
        sim = ("not simulated" if a["tvd"] is None else
               f"simulated ({a['simulated']}) max TVD {max(a['tvd'].values()):.1e}")
        print(f"  {k:16s} {a['qubits']:3d} qubits; identity {'ok' if a['identity'] else 'FAIL'} (structural "
              f"{all(a['same_dag'].values())}, {sim}, acceptance {all(a['acceptance'].values())}); "
              + "; ".join(f"{ex}: T {a['ledger'][ex]['T_us']:6.2f} us (single max {a['single'][ex]['T_us_max']:6.2f}),"
                          f" wait {a['ledger'][ex]['wait_qus']:8.3f} (single sum {a['single'][ex]['wait_qus_sum']:7.3f})"
                          for ex in ("asap", "jit")))


def main():
    from psf_os.device import Device
    ap = argparse.ArgumentParser()
    ap.add_argument("devdir")
    ap.add_argument("outs", nargs="+")
    ap.add_argument("--latency-us", type=float, default=0.0)
    ap.add_argument("--json")
    a = ap.parse_args()
    dev = Device.load(a.devdir)
    print(f"device record {dev.name}; lengths FakeMarrakesh medians (illustrative); decision latency {a.latency_us} us")
    allres = {}
    for o in a.outs:
        nm = os.path.basename(os.path.normpath(o))
        allres[nm] = job(dev, o, a.latency_us)
        show(nm, allres[nm])
    if a.json:
        json.dump(SP.as_text(dict(latency_us=a.latency_us, jobs=allres)), open(a.json, "w", newline="\n"), indent=1)


if __name__ == "__main__":
    main()
