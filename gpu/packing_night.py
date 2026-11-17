"""The packing test (prereg/drafts-2026-11-17/packing_DRAFT.md; home VS Claude, 2026-11-17 evening; not declared):
single against packed on the same night, each item on the SAME physical qubits in both (owner's change: otherwise the
effect of packing and the quality of the qubits are mixed).

Items: the third design rd1..rd5 (notes/compound_2026-11-17/compound.items) and the early chain ea1..ea5
(notes/early_2026-11-17/early.items, off arm the third design's), theta 1.1, m = 2, read flipped and relabelled.

  python gpu/packing_night.py build DEVDIR OUT [--dry-clifford-sentinel]
  python gpu/packing_night.py check OUT
  python gpu/packing_night.py score OUT

build: the packed job first (psf_os.feedforward.build_bundle: one rule-C chain, the bundle's segment rule, one ff, one
off and one floor circuit for the ten items, one sentinel) in OUT/packed; then the single job(s) in OUT/single1, ...
(psf_os.feedforward.build with chains = each item's packed qubits), split so that every job is within 60 s by the time
model. OUT/plan.json records the jobs, the qubits and the seconds.
check: the draft's checks 1-4 and the same physical qubits per item; prints PASS or FAIL (and exits 1 on FAIL):
  1. independence: no instruction or barrier of a packed arm (blocks included) spans two items (bundle_acceptance);
  2. per item and arm (ff, off), the packed circuit restricted to the item has the same instructions on every qubit
     and bit as the single job's circuit of the item, and the same exact distribution (branching simulation,
     notes/rus_coherent_2026-11-17/coherent.branch_distribution; total variation below 1e-12);
  3. ledger (notes/timebudget_2026-11-17/ledger.py; latency 0 and 1 us; ASAP as built and JIT): per item, the start of
     its last measurement inside the packed ff circuit and its wait equal those of the single ff circuit;
  4. the feed-forward checks of every arm as recorded (acceptance), the conditionals kept in ff, no sx / x in the
     floor, no conditional in the off arm;
  5. per item, the same physical qubits in the single and the packed job.
score: per item s = ff(single), p = ff(packed) (P(last output 1), relabelled), v = the noiseless value
(notes/compound_2026-11-17/ideal.json, the same for rd and ea at the same L); d = |s - v| - |p - v| with 2 SE from the
two binomial errors; the mean of d over the ten items with its 2 SE. Numbers only: the verdict words and thresholds
are the owner's ([OWNER] in the draft) and are added at declaration."""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.join(HERE, "..")
for d in ("notes/early_2026-11-17", "notes/compound_2026-11-17", "notes/rus_coherent_2026-11-17",
          "notes/timebudget_2026-11-17"):
    sys.path.insert(0, os.path.join(NB, d))

MAX_S = 60
SHOTS = 4000
TAG = "pk"


def items():
    import compound as CP
    import early as EA
    return CP.items() + EA.items()


def ref():
    return {int(k): v for k, v in json.load(open(os.path.join(NB, "notes", "compound_2026-11-17", "ideal.json"))).items()}


def L_of(tag):
    return int(tag[2:])


def build(a):
    from psf_os import feedforward as FF
    from psf_os import job as J
    from psf_os.device import Device
    if os.path.exists(a.out):
        print(f"REFUSED: {a.out} exists")
        return False
    dev = Device.load(a.devdir)
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None   # dry runs only, never a device
    its = items()
    os.makedirs(a.out)
    pk = FF.build_bundle(dev, its, os.path.join(a.out, "packed"), tag=TAG, shots=SHOTS, max_seconds=MAX_S,
                         sentinel_spec=spec)
    chains = {t: pk["items"][t]["chain"] for t, _, _ in its}
    # the single jobs: items in order, as many per job as the time model allows within MAX_S (3 arms per item + the
    # sentinel's 4 circuits)
    groups, cur = [], []
    for it in its:
        if cur and J.qpu_seconds(3 * (len(cur) + 1) + 4, SHOTS) > MAX_S:
            groups.append(cur)
            cur = []
        cur.append(it)
    groups.append(cur)
    singles = []
    for g, grp in enumerate(groups, 1):
        out = os.path.join(a.out, f"single{g}")
        rep = FF.build(dev, grp, out, shots=SHOTS, max_seconds=MAX_S, sentinel_spec=spec,
                       chains={t: chains[t] for t, _, _ in grp})
        singles.append(dict(folder=f"single{g}", items=[t for t, _, _ in grp], circuits=rep["circuits"],
                            s_model=rep["qpu_seconds_model"]))
    plan = dict(device=dev.name, dry_clifford_sentinel=bool(a.dry_clifford_sentinel), chains=chains,
                packed=dict(folder="packed", circuits=pk["circuits"], s_model=pk["qpu_seconds_model"],
                            chain_length=len(pk["chain"]), segments=pk["segments"], cz=pk["cz"]),
                singles=singles, s_model_total=pk["qpu_seconds_model"] + sum(s["s_model"] for s in singles))
    json.dump(plan, open(os.path.join(a.out, "plan.json"), "w"), indent=1)
    print(f"{dev.name}: packed {pk['circuits']} circuits {pk['qpu_seconds_model']:.1f} s (chain of {len(pk['chain'])} "
          f"sites); single " + ", ".join(f"{s['folder']} {s['circuits']} circuits {s['s_model']:.1f} s" for s in singles)
          + f"; total {plan['s_model_total']:.1f} s by the model")
    for t, ch in chains.items():
        print(f"  {t}: {ch}")


def _arms(folder, name):
    from qiskit import qpy
    runs = os.path.join(folder, "runs")
    out = {}
    for arm in ("ff", "off", "floor"):
        f = f"ff_{name}" + ("" if arm == "ff" else f"_{arm}")
        rec = json.load(open(os.path.join(runs, f + ".json")))
        (c,) = qpy.load(open(os.path.join(runs, f + ".qpy"), "rb"))
        out[arm] = (rec, c)
    return out


def check(a):
    import coherent as CO
    import ledger as LG
    from psf_os import feedforward as FF
    plan = json.load(open(os.path.join(a.out, "plan.json")))
    bad = []
    pk = _arms(os.path.join(a.out, "packed"), TAG)
    table = pk["ff"][0]["bundle"]
    tags = list(table)
    qsets = [set(table[t]["qubits"]) for t in tags]
    bsets = [set(range(table[t]["bit_offset"], table[t]["bit_offset"] + table[t]["clbits"])) for t in tags]
    # 1. independence
    try:
        FF.bundle_acceptance({arm: pk[arm][1] for arm in pk}, qsets, bsets)
        print("1. independence: no instruction or barrier spans two items (ff, off, floor): ok")
    except FF.Refused as e:
        print(f"1. independence: FAIL {e}")
        bad.append("independence")
    # single arms
    where = {t: s["folder"] for s in plan["singles"] for t in s["items"]}
    single = {t: _arms(os.path.join(a.out, where[t]), t) for t in tags}
    # 4. feed-forward checks as recorded
    f4 = []
    for name, arms in [(TAG, pk)] + [(t, single[t]) for t in tags]:
        for arm, (rec, c) in arms.items():
            if not all(rec["checks"].values()):
                f4.append((name, arm, "acceptance"))
            ops = {n for n, _ in FF.walk(c)}
            if arm == "floor" and ops & {"sx", "x"}:
                f4.append((name, arm, "sx/x in floor"))
            if arm == "off" and "if_else" in ops:
                f4.append((name, arm, "conditional in off"))
            if arm == "ff" and "if_else" not in ops:
                f4.append((name, arm, "no conditional in ff"))
    print(f"4. feed-forward checks (acceptance, conditionals kept, floor without sx/x, off without conditionals): "
          f"{'ok' if not f4 else 'FAIL ' + str(f4)}")
    bad += ["ffchecks"] if f4 else []
    # 5. the same physical qubits
    f5 = [t for t in tags if single[t]["ff"][0]["chain"] != table[t]["qubits"] or plan["chains"][t] != table[t]["qubits"]]
    print(f"5. the same physical qubits single and packed: {'ok' if not f5 else 'FAIL ' + str(f5)}")
    bad += ["qubits"] if f5 else []
    # 2 and 3 per item
    rows = {}
    full = {}
    for lat in (0.0, 1.0):
        for mode, alap in (("asap", False), ("jit", "jit")):
            ins = LG._instructions(pk["ff"][1], lat * 1e-6, False)
            st, T = LG._schedule(ins, pk["ff"][1].num_qubits, pk["ff"][1].num_clbits, alap)
            full[(lat, mode)] = (ins, st, T)
    for t, qs, bs in zip(tags, qsets, bsets):
        phys = table[t]["qubits"]
        bits = sorted(bs)
        r = {}
        for arm in ("ff", "off"):
            mine = FF.restrict(pk[arm][1], phys, bits)
            alone = FF.restrict(single[t][arm][1], phys, list(range(table[t]["clbits"])))
            same = FF.wire_signature(mine) == FF.wire_signature(alone)
            tv = float(CO.tvd(CO.branch_distribution(mine), CO.branch_distribution(alone)))
            r[arm] = dict(same=same, tvd=tv)
            if not same or tv > 1e-12:
                bad.append(f"identity {t} {arm}")
        mine = FF.restrict(pk["ff"][1], phys, bits)
        alone = single[t]["ff"][1]
        for (lat, mode), (ins, st, T) in full.items():
            alap = False if mode == "asap" else "jit"
            last_p = max(st[k] for k, x in enumerate(ins) if x[2] == "measure" and set(x[0]) <= qs)
            ia = LG._instructions(alone, lat * 1e-6, False)
            sa, _ = LG._schedule(ia, alone.num_qubits, alone.num_clbits, alap)
            last_a = max(sa[k] for k, x in enumerate(ia) if x[2] == "measure")
            wp = LG.ledger(mine, latency_us=lat, alap=alap)["wait_qus"]
            wa = LG.ledger(alone, latency_us=lat, alap=alap)["wait_qus"]
            r[f"{mode}_lat{lat}"] = dict(last_packed_us=last_p * 1e6, last_single_us=last_a * 1e6, wait_packed=wp,
                                         wait_single=wa)
            if abs(last_p - last_a) > 1e-12 or abs(wp - wa) > 1e-9:
                bad.append(f"ledger {t} {mode} {lat}")
        rows[t] = r
    print("2. per item, packed restricted against single (ff / off): same instructions per wire, exact distribution TV")
    print("3. ledger: last measurement start and wait, packed against single (ASAP and JIT, latency 0 and 1 us)")
    for t, r in rows.items():
        lw = all(abs(v["wait_packed"] - v["wait_single"]) < 1e-9 and abs(v["last_packed_us"] - v["last_single_us"])
                 < 1e-6 for k, v in r.items() if "lat" in k)
        print(f"   {t}: {r['ff']['same']} / {r['off']['same']}; TV {r['ff']['tvd']:.1e} / {r['off']['tvd']:.1e}; "
              f"ledger {lw} (JIT lat 0: last measurement {r['jit_lat0.0']['last_packed_us']:.2f} us, wait "
              f"{r['jit_lat0.0']['wait_packed']:.2f} q.us)")
    print(f"   packed ff length: " + ", ".join(f"{m} lat {l:g} us {T * 1e6:.1f} us" for (l, m), (_, _, T) in full.items()))
    json.dump(dict(rows=rows, bad=bad), open(os.path.join(a.out, "check.json"), "w"), indent=1)
    print("PASS" if not bad else f"FAIL {bad}")
    return not bad


def score(a):
    import rus3_night as R3
    from psf_os import feedforward as FF
    plan = json.load(open(os.path.join(a.out, "plan.json")))
    R = ref()
    pc = FF.cards(os.path.join(a.out, "packed"))
    sc = {}
    for s in plan["singles"]:
        sc.update(FF.cards(os.path.join(a.out, s["folder"])))
    rows, ds, ses = {}, [], []
    for t in plan["chains"]:
        L = L_of(t)
        s_c, p_c = R3.relabel(sc[t]), R3.relabel(pc[t])
        s, p, v = s_c["ff"]["p1"], p_c["ff"]["p1"], R[L]["ff"]
        ns, npk = s_c["ff"]["counted"], p_c["ff"]["counted"]
        d = abs(s - v) - abs(p - v)
        se = math.sqrt(s * (1 - s) / ns + p * (1 - p) / npk)
        rows[t] = dict(L=L, single=s, packed=p, noiseless=v, d=d, two_se=2 * se, floor_single=s_c["floor"]["all_zero"],
                       floor_packed=p_c["floor"]["all_zero"], sentinel_single=s_c["sentinel"],
                       sentinel_packed=p_c["sentinel"])
        ds.append(d)
        ses.append(se)
        print(f"{t}: single {s:.4f}  packed {p:.4f}  noiseless {v:.4f}  d {d:+.4f} (2 SE {2 * se:.4f});  floor "
              f"{rows[t]['floor_single']:.3f} / {rows[t]['floor_packed']:.3f}")
    m = sum(ds) / len(ds)
    mse_mean = math.sqrt(sum(x * x for x in ses)) / len(ses)
    out = dict(rows=rows, mean_d=m, mean_two_se=2 * mse_mean, sentinels=dict(
        packed=next(iter(pc.values()))["sentinel"], single={s["folder"]: sc[s["items"][0]]["sentinel"]
                                                            for s in plan["singles"]}),
        s_model=dict(packed=plan["packed"]["s_model"], single=[s["s_model"] for s in plan["singles"]]),
        note="numbers only; the verdict words and thresholds are the owner's ([OWNER] in the draft)")
    print(f"mean d over {len(ds)} items {m:+.4f} (2 SE {2 * mse_mean:.4f}); sentinels {out['sentinels']}; seconds by the "
          f"model packed {plan['packed']['s_model']:.1f}, single {[round(x, 1) for x in out['s_model']['single']]}")
    json.dump(out, open(os.path.join(a.out, "packing_scores.json"), "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    b.add_argument("--dry-clifford-sentinel", action="store_true",
                   help="a Clifford echo sentinel instead of the ring (dry runs only; never for a device)")
    sub.add_parser("check").add_argument("out")
    sub.add_parser("score").add_argument("out")
    a = ap.parse_args()
    res = {"build": build, "check": check, "score": score}[a.cmd](a)
    sys.exit(0 if res is not False else 1)
