"""The prescription loop with more rungs (home VS Claude, 2026-11-18 night; home instruction "試作3点", part B; desk
prototype, not declared). gpu/os2_night.py (declared) is imported read-only and unchanged; this file adds rungs to its
ladder and a rule that can climb them, in a fixed order, from recorded files only (no search, no calibration number).

Why: on 2026-11-18 the compounding OS stopped at a fixed point after round 1: with base P1 and no overshoot, os2's rule
had no rung to climb (R1 needs an overshoot, R2 needs +B). Two proposals, each a ladder (`--ladder A` or `B`):

  ladder A, "+F" frame by readout direction (the instruction's P4): per L, the round's own readout probe Dr on the
    stack's output qubit. The read frame of the base: P1 / NF read logical 1 as |1> (they lose when |1> reads as 0),
    P2 / rd read logical 1 as |0> (they lose when |0> reads as 1). If Dr shows the gap against the current frame
    (P(0|0) - P(1|1) >= 2 SE for a |1> frame; P(1|1) - P(0|0) >= 2 SE for a |0> frame) the base switches frame
    (P1 <-> P2) and the layer "F" is added. 2026-11-17 and 2026-11-18 had the gap on qubit 1 in opposite directions.
  ladder B, "+M" one more try: per L, when round k's verdict is PRESCRIPTION HELPS (no overshoot) and the stack has no
    "M", the base's tries go from m = 2 to m = 3 (the layer "M"): the noiseless value rises toward the exact one
    (L = 1: 0.890 -> 0.922 against 0.937), at the price of one more mid-circuit wait per neuron.

  The rule for round k + 1, per L, first match wins (each threshold: the quantity >= 2 SE of itself):
    R1 overshoot (os2): OVERSHOOT and no +B                       -> P2 + B (layers F / M dropped)
    R2 frames (os2): +B, no +Q, nf keeps less than rd, Dr gap on nf's output -> +Q
    RA (ladder A): no +B, no F, Dr against the base's frame on its output qubit -> switch the base's frame, add F
    RB (ladder B): PRESCRIPTION HELPS, no +B, no M                -> add M
    R3 stop-loss (os2): NOT SHOWN twice with the same stack       -> remove the last layer (F removal switches back)
    R4 keep
  Stops as os2 (a fixed point, K_MAX 4, the budget, a FAIL).

Scores as os2 (g = |P0 - exact| - |P(stack) - exact|; OVERSHOOT / PRESCRIPTION HELPS / NOT SHOWN), with the noiseless
value of every circuit computed exactly (branching) from the circuit itself, since "M" leaves ideal.json's m = 2.

  python gpu/os3_night.py build DEVDIR OUT RULE.json [--dry-clifford-sentinel]
  python gpu/os3_night.py check OUT | score OUT
  python gpu/os3_night.py rule RULE_NEXT.json ROUND_OUT [ROUND_OUT ...] --ladder A|B
  python gpu/os3_night.py dryrule OUT.json            both ladders on the recorded round 1 of 2026-11-18 (desk)
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
for d in ("notes/rus_coherent_2026-11-17", "notes/compound_2026-11-17"):
    sys.path.insert(0, os.path.join(NB, d))

import os2_night as O2  # noqa: E402  (declared; read only)

THETA, LS, K_MAX, BUDGET_S, TOL = O2.THETA, O2.LS, O2.K_MAX, O2.BUDGET_S, O2.TOL
LADDERS = ("A", "B")
_NL = {}


# ------------------------------------------------------------------------------------------------ stacks and items

def base_of(st):
    return st[0]


def tries_of(st, role=None):
    if role == "p0":
        return 3
    return 3 if "M" in st else 2


def frame_reads_one_as_one(presc):
    """True when the base reads logical 1 as |1> (P0, P1, P3, NF); False for P2 / rd (read flipped)."""
    return presc != "P2"


def item(presc, L, m):
    from psf_os import feedforward as FF
    import rus2_night as R2
    import rus3_night as R3
    if presc == "P0":
        return FF.rus_chain(L, THETA, m=3)
    if presc == "P1":
        return R2.flip_chain(L, THETA, m=m)
    if presc == "P2":
        return R3.chain(L, THETA, m=m)
    if presc == "P3":
        return FF.rus_chain(L, THETA, m=2)
    if presc == "NF":
        return R2.flip_chain(L, THETA, m=m, flip=False)
    raise ValueError(presc)


def noiseless(presc, L, m, arm="ff"):
    """P(last output 1) read as declared, exactly (branching over every mid-circuit measurement)."""
    key = (presc, L, m, arm)
    if key not in _NL:
        import coherent as CO
        from psf_os import feedforward as FF
        qc, spec = item(presc, L, m)
        c = FF.lower(qc) if arm == "ff" else FF.strip_conditionals(FF.lower(qc))
        dist = CO.branch_distribution(c)
        n = c.num_clbits
        p1 = sum(p for k, p in dist.items() if k[n - 1 - spec["out_bit"]] == "1")
        _NL[key] = 1 - p1 if presc == "P2" else p1
    return _NL[key]


def items_for(stacks):
    """[(tag, circuit, spec)] and {tag: (L, role, offset, presc, m)}."""
    out, meta = [], {}
    for L in LS:
        out.append((f"p0_{L}", *item("P0", L, 3)))
        meta[f"p0_{L}"] = (L, "p0", 0, "P0", 3)
    for L in LS:
        st = stacks[str(L)]
        if st == ["P0"]:
            continue
        o, m = O2.offset_of(st), tries_of(st)
        if "B" in st:
            out.append((f"xr{L}", *item("P2", L, m)))
            out.append((f"xn{L}", *item("NF", L, m)))
            meta[f"xr{L}"], meta[f"xn{L}"] = (L, "xr", o, "P2", m), (L, "xn", o, "NF", m)
        else:
            out.append((f"x{L}", *item(base_of(st), L, m)))
            meta[f"x{L}"] = (L, "x", o, base_of(st), m)
    out.append(("dr", *O2.probe_item()))
    meta["dr"] = (0, "probe", 0, None, 0)
    return out, meta


# ------------------------------------------------------------------------------------------------ build / check / score

def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    R = json.load(open(a.rule_json))
    if R.get("stop"):
        print(f"STOP: {R.get('stop_reason')}")
        return False
    dev = Device.load(a.devdir)
    if dev.name != R["device"]:
        print(f"REFUSED: the rule was made on {R['device']}, the record is {dev.name}")
        return False
    its, meta = items_for(R["stacks"])
    chains = O2.chains_for(dev, {t: v[:3] for t, v in meta.items()})
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None   # dry runs only, never a device
    rep = FF.build(dev, its, a.out, shots=4000, max_seconds=60, sentinel_spec=spec, chains=chains)
    full = FF.place(dev, O2.PROBE_N + max(O2.OFFSETS))["chain"]
    outq = {t: rep["items"][t]["chain"][2 * v[0] - 1] for t, v in meta.items() if v[1] != "probe"}
    probe_q = [rep["items"]["dr"]["chain"][p] for p in O2.PROBE_POS]
    if probe_q != [full[p] for p in O2.PROBE_POS]:
        os.rename(os.path.join(a.out, "job"), os.path.join(a.out, "job_REFUSED"))
        print("REFUSED: the probe is not on the rule-C chain the offsets are read on (job moved to job_REFUSED)")
        return False
    R2 = dict(R, meta={t: list(v) for t, v in meta.items()}, output_qubit=outq, probe_qubits=probe_q,
              probe_positions=list(O2.PROBE_POS), qpu_seconds_model=rep["qpu_seconds_model"])
    json.dump(R2, open(os.path.join(a.out, "rule.json"), "w"), indent=1)
    print(json.dumps({k: rep[k] for k in ("device", "circuits", "qpu_seconds_model", "shots") if k in rep}))


def check(a):
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    from psf_os import feedforward as FF
    R = json.load(open(os.path.join(a.out, "rule.json")))
    m = json.load(open(os.path.join(a.out, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(a.out, "job", "circuits.qpy"), "rb"))
    i, bad = 0, []
    for cell in m["cells"]:
        for _ in range(cell["points"]):
            c = cs[i]
            i += 1
            if cell["role"] == "sentinel":
                continue
            tag = cell["name"][3:].replace("_floor", "").replace("_off", "")
            L, role, _, presc, mm = R["meta"][tag]
            cc = FF.compact(c)
            n = cc.num_clbits
            cnt = AerSimulator().run(cc, shots=4000, seed_simulator=20261119).result().get_counts()
            tot = sum(cnt.values())
            allz = sum(v for k, v in cnt.items() if set(FF._bits(k, n)) == {0}) / tot
            if cell["role"] == "floor":
                ok, p = allz == 1.0, float("nan")
            elif role == "probe":
                p = sum(v for k, v in cnt.items() if set(FF._bits(k, n)) == {1}) / tot
                ok = p == 1.0
            else:
                p, _ = O2._p_out(n, cnt, L * mm, presc == "P2")
                ok = abs(p - noiseless(presc, L, mm, "ff" if cell["role"] == "user" else "off")) <= TOL
            bad += [] if ok else [cell["name"]]
    print("PASS" if not bad else f"FAIL {bad}")
    return not bad


def score(a, quiet=False):
    import ctrl_night as CN
    R = json.load(open(os.path.join(a.out, "rule.json")))
    ref = O2.refs()
    g = CN._counts(a.out)
    se = O2._se
    rows = {}
    for L in LS:
        st = R["stacks"][str(L)]
        ex = ref["exact"][L]
        p0, n0 = O2._p_out(*g[(f"p0_{L}", "ff")], L * 3, False)
        row = dict(stack=st, p0=p0, p0_n=n0, exact=ex, output_qubit_p0=R["output_qubit"][f"p0_{L}"])
        if st == ["P0"]:
            row.update(verdict="NO PRESCRIPTION")
            rows[str(L)] = row
            continue
        m = tries_of(st)
        if "B" in st:
            nlr, nln = noiseless("P2", L, m), noiseless("NF", L, m)
            nl = (nlr + nln) / 2
            pr, nr = O2._p_out(*g[(f"xr{L}", "ff")], L * m, True)
            pn, nn = O2._p_out(*g[(f"xn{L}", "ff")], L * m, False)
            p = (pr + pn) / 2
            se_p = math.sqrt(se(pr, nr) ** 2 + se(pn, nn) ** 2) / 2
            row.update(rd=pr, nf=pn, rd_share=pr / nlr, nf_share=pn / nln, share_gap=pr / nlr - pn / nln,
                       share_gap_two_se=2 * math.sqrt((se(pr, nr) / nlr) ** 2 + (se(pn, nn) / nln) ** 2),
                       output_qubit_rd=R["output_qubit"][f"xr{L}"], output_qubit_nf=R["output_qubit"][f"xn{L}"])
        else:
            nl = noiseless(base_of(st), L, m)
            p, nx = O2._p_out(*g[(f"x{L}", "ff")], L * m, base_of(st) == "P2")
            se_p = se(p, nx)
            row.update(output_qubit=R["output_qubit"][f"x{L}"])
        gain = abs(p0 - ex) - abs(p - ex)
        se_g = math.sqrt(se(p0, n0) ** 2 + se_p ** 2)
        over = p > nl + 2 * se_p
        v = "OVERSHOOT" if over else ("PRESCRIPTION HELPS" if (gain > 0 and gain >= 2 * se_g) else "NOT SHOWN")
        row.update(p=p, se=se_p, noiseless=nl, overshoot=bool(over), g=gain, g_se=se_g, verdict=v, tries=m)
        rows[str(L)] = row
        if not quiet:
            print(f"L {L} [{'+'.join(st)}]: P {p:.4f} (noiseless {nl:.4f}) P0 {p0:.4f} g {gain:+.4f} "
                  f"(2 SE {2 * se_g:.4f}) -> {v}")
    dr = O2.dr_from_probe(a.out, R)
    out = dict(round=R["round"], device=R["device"], ladder=R.get("ladder"), stacks=R["stacks"], rows=rows, dr=dr,
               probe_qubits=R["probe_qubits"], qpu_seconds_model=R["qpu_seconds_model"],
               model_seconds_so_far=R.get("model_seconds_so_far", 0.0) + R["qpu_seconds_model"])
    json.dump(out, open(os.path.join(a.out, "round_scores.json"), "w"), indent=1)
    return out


# ------------------------------------------------------------------------------------------------ the rule

def _against_frame(presc, d):
    """Dr on the output qubit shows the gap against the base's read frame (>= 2 SE)."""
    if d is None:
        return False
    gap, two = d["gap"], d["two_se"]                 # gap = P(0|0) - P(1|1)
    if frame_reads_one_as_one(presc):
        return gap > 0 and gap >= two                 # |1> reads worse: a |1>-frame loses
    return -gap > 0 and -gap >= two                   # |0> reads worse: a |0>-frame (rd) loses


def next_stacks(rounds, ladder, chain_full=None, k_max=K_MAX, budget=BUDGET_S, next_cost=None):
    """As os2_night.next_stacks with the rung of `ladder` (A: frame by readout direction, B: one more try)."""
    if ladder not in LADDERS:
        raise ValueError(ladder)
    cur = rounds[-1]
    prev = rounds[-2] if len(rounds) > 1 else None
    dr = cur["dr"]
    stacks, why = {}, {}
    for L in LS:
        sL = str(L)
        row = cur["rows"][sL]
        st = list(row["stack"])
        new, reason = st, "R4 keep"
        if row.get("verdict") == "OVERSHOOT" and "B" not in st:
            new, reason = ["P2", "B"], "R1 overshoot -> P2 + B"
        elif "B" in st and not any(x.startswith("Q") for x in st):
            gap_ok = row["share_gap"] > 0 and row["share_gap"] >= row["share_gap_two_se"]
            qn = str(row["output_qubit_nf"])
            if gap_ok and qn in dr and dr[qn]["sig"] and chain_full is not None:
                cands = [(dr[str(chain_full[o + 2 * L - 1])]["gap"], o) for o in O2.OFFSETS
                         if str(chain_full[o + 2 * L - 1]) in dr]
                best = min(cands) if cands else None
                if best and best[1] != 0:
                    new, reason = st + [f"Q{best[1]}"], f"R2 frames -> +Q{best[1]}"
        elif st != ["P0"] and ladder == "A" and "F" not in st and base_of(st) in ("P1", "P2"):
            q = str(row.get("output_qubit"))
            if _against_frame(base_of(st), dr.get(q)):
                nb = "P2" if base_of(st) == "P1" else "P1"
                new = [nb] + st[1:] + ["F"]
                reason = (f"RA frame: Dr on q{q} gap {dr[q]['gap']:+.4f} (2 SE {dr[q]['two_se']:.4f}) against the "
                          f"{base_of(st)} frame -> {nb} + F")
        elif st != ["P0"] and ladder == "B" and "M" not in st and row.get("verdict") == "PRESCRIPTION HELPS":
            new, reason = st + ["M"], "RB helps -> one more try (m 3) + M"
        if new is st and prev is not None:
            prow = prev["rows"].get(sL, {})
            if (row.get("verdict") == "NOT SHOWN" and prow.get("verdict") == "NOT SHOWN"
                    and list(prow.get("stack", [])) == st):
                if st[-1] == "F":
                    new = ["P2" if base_of(st) == "P1" else "P1"] + st[1:-1]
                else:
                    new = st[:-1] if len(st) > 1 else ["P0"]
                reason = "R3 stop-loss: NOT SHOWN twice with the same stack -> " + "+".join(new)
        stacks[sL], why[sL] = new, reason
    k = cur["round"]
    spent = cur.get("model_seconds_so_far", 0.0)
    unchanged = all(stacks[str(L)] == list(cur["rows"][str(L)]["stack"]) for L in LS)
    any_over = any(cur["rows"][str(L)].get("verdict") == "OVERSHOOT" for L in LS)
    pending = any(cur["rows"][str(L)].get("verdict") == "NOT SHOWN" and not (
        prev is not None and prev["rows"].get(str(L), {}).get("verdict") == "NOT SHOWN") for L in LS)
    stop, sreason = False, None
    if unchanged and not any_over and not pending:
        stop, sreason = True, "fixed point: every L keeps its stack, none overshoots, none NOT SHOWN for the first time"
    elif k >= k_max:
        stop, sreason = True, f"round limit K = {k_max}"
    elif next_cost is not None and spent + next_cost > budget:
        stop, sreason = True, f"budget: {spent:.1f} + {next_cost:.1f} > {budget:.0f} s"
    return dict(round=k + 1, device=cur["device"], ladder=ladder, stacks=stacks, why=why, stop=stop,
                stop_reason=sreason, model_seconds_so_far=spent)


def rule(a):
    rounds = [json.load(open(os.path.join(d, "round_scores.json"))) for d in a.rounds]
    b = json.load(open(os.path.join(a.rounds[-1], "build.json")))
    R = next_stacks(rounds, a.ladder, b["items"]["dr"]["chain"], k_max=a.k_max)
    json.dump(R, open(a.out_rule, "w"), indent=1)
    for L in LS:
        print(f"L {L}: {'+'.join(R['stacks'][str(L)])}  ({R['why'][str(L)]})")
    print("STOP:" if R["stop"] else "next round", R["round"], R["stop_reason"] or "")


def dryrule(a):
    """Both ladders applied to the recorded round 1 of 2026-11-18 (results/os2-night-2026-11-18/r1): which rung would
    each pick for round 2. The recorded round_scores.json is os2's; its rows carry everything both rungs read."""
    base = os.path.join(NB, "results", "os2-night-2026-11-18")
    r1 = json.load(open(os.path.join(base, "r1", "round_scores.json")))
    b = json.load(open(os.path.join(base, "r1", "build.json")))
    res = {}
    for lad in LADDERS:
        R = next_stacks([r1], lad, b["items"]["dr"]["chain"])
        res[lad] = R
        print(f"ladder {lad}: " + "; ".join(f"L {L} {'+'.join(R['stacks'][str(L)])} ({R['why'][str(L)]})" for L in LS)
              + (f"; STOP: {R['stop_reason']}" if R["stop"] else "; next round 2"))
    print("round 1 Dr (probe): " + " ".join(f"q{q} gap {v['gap']:+.4f} (2 SE {v['two_se']:.4f})" for q, v in r1["dr"].items()))
    json.dump(dict(round1_dr=r1["dr"], round1_verdicts={L: r1["rows"][L]["verdict"] for L in r1["rows"]}, **res),
              open(a.out_json, "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    b.add_argument("rule_json")
    b.add_argument("--dry-clifford-sentinel", action="store_true", help="dry runs only; never for a device job")
    for nm in ("check", "score"):
        sub.add_parser(nm).add_argument("out")
    r = sub.add_parser("rule")
    r.add_argument("out_rule")
    r.add_argument("rounds", nargs="+")
    r.add_argument("--ladder", choices=LADDERS, required=True)
    r.add_argument("--k-max", type=int, default=K_MAX)
    d = sub.add_parser("dryrule")
    d.add_argument("out_json")
    a = ap.parse_args()
    res = {"build": build, "check": check, "score": score, "rule": rule, "dryrule": dryrule}[a.cmd](a)
    sys.exit(0 if res is not False else 1)
