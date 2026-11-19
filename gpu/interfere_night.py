"""Interference tests (draft prereg/drafts-2026-11-19/interfere_DRAFT.md; home VS Claude, 2026-11-18 evening; not
declared). Tonight's P-B (results/parallel-night-2026-11-18): next to a fixed item A does not lose (B1); next to a
conditional item the item on qubits 0-3 (A, whose bits come first) loses 0.06 and B does not (B2); delaying B past A's
whole length does not remove it (B3). Three bundles separate "where" (A's qubits), "bit order" (A's bits first) and
"nearness" (one site apart), each against the same item alone on the same qubits, in ONE job:

  E1  A: rd2's off arm (fixed)    B: rd2 (conditional)          gap 1, bits A then B   (B1 reversed)
  E2  A: rd2                      B: rd2                        gap 3 (three sites skipped), bits A then B
  E3  A: rd2                      B: rd2                        gap 1, bits B then A   (only the bit order changed)
  sa, sb, sc  rd2 alone on E1/E3's A qubits, on their B qubits, and on E2's B qubits (E2's A qubits are sa's; checked)

rd2 = gpu/rus3_night.chain(2, 1.1, 2) (the item of P-B). Bundles by psf-os build_bundle (v0.2 prototype:
allow_conditional_neighbours=True, the manifest records it; gap and bit_order as above), singles by build(chains=...).
One job: 3 bundles x 3 arms + 3 singles x 3 arms + the sentinel's 4 = 22 circuits, 27.6 s by the time model.

  python gpu/interfere_night.py build DEVDIR OUT [--dry-clifford-sentinel]
  python gpu/interfere_night.py check OUT
  python gpu/interfere_night.py score OUT

check (PASS / FAIL, exit 1 on FAIL), as P-B's: independence of every bundle arm; per packed sub-item the same
instructions per wire and the same exact distribution as its single reference (E1 A against sa's off arm); the same
physical qubits; the recorded acceptance of every arm, no sx / x in a floor, no conditional in an off arm, conditionals
kept in every single ff and every conditional sub-item; E2's skipped sites >= 3 and no coupler joining A and B within
two steps; E3's bits of A after B's; the manifest records allow_conditional_neighbours.
score: per conditional sub-item d = |s - v| - |p - v| (s its single reference's ff, p its ff packed, v rd2's noiseless
ff, computed here exactly from the single circuit); E1's A (fixed) against sa's off arm beside; per bundle the mean
over its conditional sub-items with 2 SE. Numbers only: the verdict words and the reading table are [OWNER] in the
draft."""
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
import parallel_night as PN  # noqa: E402  (read only: rd2, offvariant)

SHOTS = 4000
MAX_S = 30
GAP_WIDE = 3
SPEC_DRY = dict(kind="echo_clifford", D=24)


def _merge(dev, parts, runs, job, extra):
    from psf_os import job as J
    os.makedirs(runs)
    for k, p in enumerate(parts):
        for f in sorted(os.listdir(os.path.join(p, "runs"))):
            if k > 0 and not f.startswith("ff_"):
                continue
            dst = os.path.join(runs, f)
            if os.path.exists(dst):
                raise RuntimeError(f"two records named {f}")
            shutil.copy2(os.path.join(p, "runs", f), dst)
    return J.assemble(dev, runs, job, max_seconds=MAX_S, extra=extra)


def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    if os.path.exists(a.out):
        print(f"REFUSED: {a.out} exists")
        return False
    dev = Device.load(a.devdir)
    spec = SPEC_DRY if a.dry_clifford_sentinel else None          # dry runs only, never a device
    qc, sp = PN.rd2()
    off = PN.offvariant(qc, sp)
    n = FF._prepare("rd2", qc, sp)[0]["n"]
    p1 = FF.bundle_place(dev, [n, n])
    p3 = FF.bundle_place(dev, [n, n], gap=GAP_WIDE)
    chA, chB = ([p1["chain"][k] for k in s] for s in p1["segments"])
    chA2, chC = ([p3["chain"][k] for k in s] for s in p3["segments"])
    if chA2 != chA:
        raise FF.Refused(f"E2's A {chA2} is not on sa's qubits {chA}: a fourth single would be needed")
    tmp = tempfile.mkdtemp(prefix="interfere_night_")
    try:
        single = FF.build(dev, [("sa", qc, sp), ("sb", qc, sp), ("sc", qc, sp)], os.path.join(tmp, "single"),
                          shots=SHOTS, max_seconds=60, sentinel_spec=spec, chains={"sa": chA, "sb": chB, "sc": chC})
        bundles = {
            "E1": dict(items=[("e1a", off, sp), ("e1b", qc, sp)], gap=1, bit_order=None),
            "E2": dict(items=[("e2a", qc, sp), ("e2b", qc, sp)], gap=GAP_WIDE, bit_order=None),
            "E3": dict(items=[("e3a", qc, sp), ("e3b", qc, sp)], gap=1, bit_order=["e3b", "e3a"]),
        }
        want = {"E1": [chA, chB], "E2": [chA, chC], "E3": [chA, chB]}
        reps, extra = {}, {}
        for name, b in bundles.items():
            reps[name] = FF.build_bundle(dev, b["items"], os.path.join(tmp, name), tag=name, shots=SHOTS,
                                         max_seconds=60, sentinel_spec=spec, allow_conditional_neighbours=True,
                                         gap=b["gap"], bit_order=b["bit_order"])
            got = [reps[name]["items"][t]["chain"] for t, _, _ in b["items"]]
            if got != want[name]:
                raise FF.Refused(f"{name}: placed on {got}, the singles on {want[name]}")
            m = json.load(open(os.path.join(tmp, name, "job", "manifest.json")))
            extra[name] = {k: m[k] for k in ("conditional_neighbours", "conditionals_per_item", "bundle_gap",
                                             "bit_order") if k in m}
        man = _merge(dev, [os.path.join(tmp, "single")] + [os.path.join(tmp, k) for k in bundles],
                     os.path.join(a.out, "runs"), os.path.join(a.out, "job"), dict(interfere_bundles=extra))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    plan = dict(device=dev.name, dry_clifford_sentinel=bool(a.dry_clifford_sentinel), chain_A=chA, chain_B=chB,
                chain_C=chC, gap_wide=GAP_WIDE, circuits=len(man["pubs"]), s_model=man["qpu_seconds_model"],
                bundles={k: dict(gap=v["gap"], bit_order=v["bit_order"], items=[t for t, _, _ in v["items"]],
                                 chains=want[k]) for k, v in bundles.items()},
                manifest_bundles=extra, build_single=single, build_bundles=reps)
    json.dump(plan, open(os.path.join(a.out, "plan.json"), "w"), indent=1, default=str)
    print(f"{dev.name}: {plan['circuits']} circuits {plan['s_model']:.1f} s by the model; A {chA}, B {chB}, E2's B {chC}")
    return True


def _rec(out, name):
    from qiskit import qpy
    rec = json.load(open(os.path.join(out, "runs", name + ".json")))
    (c,) = qpy.load(open(os.path.join(out, "runs", name + ".qpy"), "rb"))
    return rec, c


def check(a):
    import coherent as CO
    from psf_os import feedforward as FF
    plan = json.load(open(os.path.join(a.out, "plan.json")))
    man = json.load(open(os.path.join(a.out, "job", "manifest.json")))
    bad, lines = [], []
    say = lambda s: (print(s), lines.append(s))
    single = {t: {arm: _rec(a.out, f"ff_{t}" + ("" if arm == "ff" else f"_{arm}")) for arm in ("ff", "off", "floor")}
              for t in ("sa", "sb", "sc")}
    for name in ("E1", "E2", "E3"):
        arms = {arm: _rec(a.out, f"ff_{name}" + ("" if arm == "ff" else f"_{arm}")) for arm in ("ff", "off", "floor")}
        table = arms["ff"][0]["bundle"]
        tags = list(table)
        qsets = [set(table[t]["qubits"]) for t in tags]
        bsets = [set(range(table[t]["bit_offset"], table[t]["bit_offset"] + table[t]["clbits"])) for t in tags]
        try:
            FF.bundle_acceptance({k: v[1] for k, v in arms.items()}, qsets, bsets)
            ind = "ok"
        except FF.Refused as e:
            ind = f"FAIL {e}"
            bad.append(f"{name} independence")
        refs = {"E1": {"e1a": ("sa", "off"), "e1b": ("sb", "ff")}, "E2": {"e2a": ("sa", "ff"), "e2b": ("sc", "ff")},
                "E3": {"e3a": ("sa", "ff"), "e3b": ("sb", "ff")}}[name]
        parts = []
        for t in tags:
            st, sarm = refs[t]
            info = table[t]
            bits = list(range(info["bit_offset"], info["bit_offset"] + info["clbits"]))
            mine = FF.restrict(arms["ff"][1], info["qubits"], bits)
            ref = FF.restrict(single[st][sarm][1], info["qubits"], list(range(info["clbits"])))
            same = FF.wire_signature(mine) == FF.wire_signature(ref)
            tv = float(CO.tvd(CO.branch_distribution(mine), CO.branch_distribution(ref)))
            q_same = info["qubits"] == single[st][sarm][0]["chain"]
            ok = same and tv < 1e-12 and q_same
            bad += [] if ok else [f"{name} {t} identity"]
            parts.append(f"{t} vs {st} {sarm}: same per wire {same}, TV {tv:.1e}, same qubits {q_same}, bits "
                         f"{bits[0]}..{bits[-1]}")
        # acceptance, floors, offs, conditionals
        acc = all(all(r["checks"].values()) for r, _ in arms.values())
        fl = not ({n for n, _ in FF.walk(arms["floor"][1])} & {"sx", "x"})
        of = "if_else" not in {n for n, _ in FF.walk(arms["off"][1])}
        cond_items = [t for t in tags if table[t]["conditionals"]]
        kept = all(any(nm == "if_else" for nm, qs in FF.walk(arms["ff"][1]) if set(qs) <= set(table[t]["qubits"]))
                   for t in cond_items)
        rec_allow = man["interfere_bundles"][name]["conditional_neighbours"]["allowed"] is True
        extra_ok = True
        if name == "E2":
            ch = arms["ff"][0]["chain"]
            pa, pb = [ch.index(q) for q in table["e2a"]["qubits"]], [ch.index(q) for q in table["e2b"]["qubits"]]
            skipped = min(pb) - max(pa) - 1
            extra_ok = skipped >= 3
            parts.append(f"sites skipped between A and B on the chain: {skipped}")
        if name == "E3":
            extra_ok = table["e3a"]["bit_offset"] > table["e3b"]["bit_offset"]
            parts.append(f"bits: A at {table['e3a']['bit_offset']}.., B at {table['e3b']['bit_offset']}..")
        ok = ind == "ok" and acc and fl and of and kept and rec_allow and extra_ok
        bad += [] if ok else [f"{name} acceptance/extras"]
        say(f"{name}: independence {ind}; acceptance {acc}; floor without sx/x {fl}; off without conditionals {of}; "
            f"conditionals kept {kept}; manifest records allow {rec_allow}; " + "; ".join(parts))
    sfail = [t for t in single for arm in ("ff", "off", "floor") if not all(single[t][arm][0]["checks"].values())]
    sk = all(any(n == "if_else" for n, _ in FF.walk(single[t]["ff"][1])) for t in single)
    say(f"singles: acceptance {'ok' if not sfail else sfail}; conditionals kept {sk}; chains A {plan['chain_A']}, "
        f"B {plan['chain_B']}, E2's B {plan['chain_C']}; {plan['circuits']} circuits {plan['s_model']:.1f} s")
    bad += sfail + ([] if sk else ["single conditionals"])
    if plan["s_model"] > MAX_S:
        bad.append("over 30 s")
    say("PASS" if not bad else f"FAIL {bad}")
    open(os.path.join(a.out, "check.txt"), "w").write("\n".join(lines) + "\n")
    return not bad


def verdict(d, two_se):
    """The words of P-B, as declared for 2026-11-19 (prereg/interfere_night_2026-11-19.md): per sub-item and per
    bundle. Added after the night (the workplace VS: the night's score gave numbers only)."""
    if d <= -two_se:
        return "PACKED KEEPS LESS"
    if d >= two_se:
        return "PACKED KEEPS MORE"
    return "SAME WITHIN ERROR"


def score(a):
    import coherent as CO
    import rus3_night as R3
    from psf_os import feedforward as FF
    cards = FF.cards(a.out)
    (_, csa) = _rec(a.out, "ff_sa")
    out_bit = cards["sa"]["ff"] and json.load(open(os.path.join(a.out, "runs", "ff_sa.json")))["rus"]["out_bit"]
    dist = CO.branch_distribution(FF.restrict(csa, json.load(open(os.path.join(a.out, "runs", "ff_sa.json")))["chain"],
                                              list(range(csa.num_clbits))))
    v = 1 - sum(p for k, p in dist.items() if k[len(k) - 1 - out_bit] == "1")       # read flipped (rd)
    rows, lines = {}, []
    say = lambda s: (print(s), lines.append(s))
    c = {t: R3.relabel(cards[t]) for t in cards}
    se_ = lambda x, y: math.sqrt(x["p1"] * (1 - x["p1"]) / x["counted"] + y["p1"] * (1 - y["p1"]) / y["counted"])
    plan = {"E1": [("e1b", "sb")], "E2": [("e2a", "sa"), ("e2b", "sc")], "E3": [("e3a", "sa"), ("e3b", "sb")]}
    say(f"noiseless ff of rd2 (exact, read flipped): {v:.4f}; singles sa {c['sa']['ff']['p1']:.4f}, sb "
        f"{c['sb']['ff']['p1']:.4f}, sc {c['sc']['ff']['p1']:.4f}")
    for name, subs in plan.items():
        ds, ses = [], []
        for t, st in subs:
            s, p = c[st]["ff"], c[t]["ff"]
            d = abs(s["p1"] - v) - abs(p["p1"] - v)
            se = se_(s, p)
            rows[t] = dict(single=s["p1"], packed=p["p1"], d=d, two_se=2 * se, ref=st,
                           still_single=s.get("still_failed_after_m"), still_packed=p.get("still_failed_after_m"))
            ds.append(d)
            ses.append(se)
            rows[t]["verdict"] = verdict(d, 2 * se)
            say(f"  {t} against {st}: alone {s['p1']:.4f}  packed {p['p1']:.4f}  d {d:+.4f} (2 SE {2 * se:.4f}) -> "
                f"{rows[t]['verdict']}")
        m, ms = sum(ds) / len(ds), 2 * math.sqrt(sum(x * x for x in ses)) / len(ses)
        rows[name] = dict(mean=m, two_se=ms, verdict=verdict(m, ms))
        say(f"{name}: mean d over its conditional sub-items {m:+.4f} (2 SE {ms:.4f}) -> {rows[name]['verdict']}")
    # E1's fixed A against sa's off arm (beside)
    sa_off = c["sa"]["off"]
    e1a = c["e1a"]["ff"]          # the bundle's ff arm holds A's off circuit (fixed) as its sub-item
    dist_off = CO.branch_distribution(FF.restrict(_rec(a.out, "ff_sa_off")[1],
                                                  json.load(open(os.path.join(a.out, "runs", "ff_sa.json")))["chain"],
                                                  list(range(csa.num_clbits))))
    v_off = 1 - sum(p for k, p in dist_off.items() if k[len(k) - 1 - out_bit] == "1")
    d = abs(sa_off["p1"] - v_off) - abs(e1a["p1"] - v_off)
    rows["e1a_fixed"] = dict(single_off=sa_off["p1"], packed=e1a["p1"], noiseless_off=v_off, d=d,
                             two_se=2 * se_(sa_off, e1a))
    say(f"beside: E1's A (fixed, rd2's off arm) packed {e1a['p1']:.4f} against sa's off arm {sa_off['p1']:.4f} "
        f"(noiseless {v_off:.4f}): d {d:+.4f} (2 SE {2 * se_(sa_off, e1a):.4f})")
    say("the words as declared in prereg/interfere_night_2026-11-19.md (per sub-item and per bundle); the reading table "
        "is read by hand from them")
    json.dump(dict(rows=rows, noiseless=v, noiseless_off=v_off), open(os.path.join(a.out, "interfere_scores.json"), "w"),
              indent=1)
    open(os.path.join(a.out, "score.txt"), "w").write("\n".join(lines) + "\n")


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
