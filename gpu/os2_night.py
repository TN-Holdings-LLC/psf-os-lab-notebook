"""The prescription loop with compounding (workplace Claude, 2026-11-18; home handover 2026-11-17 night, section 3;
the owner's choices of 2026-11-18 08:5x JST: every threshold 2 SE, K_MAX 4, a budget of 240 s by the model for the
whole night including the diagnostics, the primary verdict the last round, nothing read from an earlier night).
Declaration text: prereg/drafts-2026-11-18/os2_night_2026-11-18_READY.md (declared when pushed at home). The night is
run end to end by gpu/os2_run.py.

gpu/os_night.py (2026-11-17) is "simple interest": one diagnosis, one fixed pick per L, one main job, and the result is
not used again. Here a night runs in rounds k = 1 .. K; each round's main job is scored, and its scores are the next
round's rule input; the picks are *stacks* of prescriptions from a fixed list, built up in a fixed order:

  ladder (the order layers are added in; no search):
    base  P0 the circuit as written (rus_chain m = 3) | P1 hold flipped (rus2_night.flip_chain) | P2 P1 + read flipped
          (rus3_night.chain) | P3 fewer tries (rus_chain m = 2)              -- round 1: gpu/os_night.py's rule, as is
    +B    frame balance: the P2 circuit (rd) and its complementary frame (nf = flip_chain(flip=False)) pooled, P =
          (P_rd + P_nf) / 2 (balanced_night.py); base becomes P2
    +Q    output-qubit choice: the item placed on the rule-C chain shifted by an offset o in {0, 2, 4} (its last output
          then on chain position o + 2L - 1), o the candidate whose readout gap (Dr) is smallest; ties: the smaller o

  the rule for round k + 1, per L, first match wins (each threshold: the quantity >= 2 SE of itself):
    R1 overshoot: round k's pick OVERSHOOT (P > its noiseless value + 2 SE) and no +B  -> stack = P2 + B
    R2 frames:    +B in the stack, no +Q, the nf frame keeps a smaller share of its noiseless value than rd (by
                  >= 2 SE), and the Dr gap on nf's output qubit >= 2 SE                  -> add +Q (offset by Dr)
    R3 stop-loss: NOT SHOWN in round k and in round k - 1 with the same stack             -> remove the last layer
                  (a bare base other than P0 goes to P0)
    R4 otherwise: keep the stack
  stop after round k when (a) every L keeps its stack, none overshoots in round k and none is NOT SHOWN for the first
  time (a fixed point), or (b) k = K_MAX (the rule's own stops, written into RULE{k+1}.json); and, in gpu/os2_run.py,
  (c) when the diagnostics + the rounds run + the next round's model seconds (from its build) would pass BUDGET_S (the
  next round is then not sent), or (d) a check FAILs or a build refuses.

  Dr (readout gap) is measured in every round's own job by a probe item: X on chain positions 1, 3, .., 2 LMAX + 3 and
  read at once (P(1|1) per qubit); P(0|0) from the probe's floor arm. Round 1 has the os_night diagnostics' Dr.

  per round, per L (verdict words as gpu/os_night.py): g = |P_ff(P0) - exact| - |P(pick) - exact| with the
  two-SE of the difference; OVERSHOOT when P(pick) > noiseless(pick) + 2 SE; PRESCRIPTION HELPS when g >= 2 SE;
  otherwise NOT SHOWN. P0 runs again in every round (the same circuits), so drift within the night is in both terms.

  the OS's own compounding (compound): per round G_k = the mean of g over the L credited in every round compared (no
  overshoot in any; SE from the per-L SEs); weighted least-squares slope of G_k over k; OS COMPOUNDS when the slope >= 2 SE and no L
  overshoots in the last round; otherwise NOT SHOWN; NOT JUDGEABLE with fewer than three rounds or no L credited in
  every round.

  python gpu/os2_night.py round1 OS_RULE.json RULE1.json [--diag DW DC]   round 1 stacks from os_night's rule.json
  python gpu/os2_night.py build DEVDIR OUT RULE.json [--dry-clifford-sentinel]
  python gpu/os2_night.py check OUT
  python gpu/os2_night.py score OUT                           -> OUT/round_scores.json
  python gpu/os2_night.py rule RULE_NEXT.json ROUND_OUT [ROUND_OUT ...]   (rounds in order, the last is round k)
  python gpu/os2_night.py compound ROUND_OUT [ROUND_OUT ...]
  python gpu/os2_night.py trial OUT.json                      the rule on the recorded rounds of 2026-11-17 (desk)
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)

THETA = 1.1
LS = (1, 2, 3)
LMAX = max(LS)
OFFSETS = (0, 2, 4)
PROBE_POS = tuple(range(1, 2 * LMAX + 4, 2))          # chain positions 1, 3, .., 2 LMAX + 3 (5 qubits for LMAX 3)
PROBE_N = 2 * LMAX + 4
K_MAX = 4                                              # rounds per night (owner, 2026-11-18)
BUDGET_S = 240.0                                       # model seconds per night: diagnostics + every round (owner)
TOL = 0.03


# ------------------------------------------------------------------------------------------------ references

def refs():
    """Noiseless P(last output 1), read as declared: P0 (m = 3) from rus_night.REF (as os_night); m = 2 (P1, P2, P3,
    rd, nf) from notes/compound_2026-11-17/ideal.json (exact). The exact target from the same file."""
    import rus_night as R1
    m2 = {int(k): v for k, v in json.load(open(os.path.join(NB, "notes", "compound_2026-11-17", "ideal.json"))).items()}
    return dict(P0={L: R1.REF[L] for L in LS}, m2={L: dict(ff=m2[L]["ff"], off=m2[L]["off"]) for L in LS},
                exact={L: m2[L]["exact"] for L in LS})


# ------------------------------------------------------------------------------------------------ stacks and items

def stack_name(st):
    return "+".join(x if not x.startswith("Q") else x for x in st)


def base_item(presc, L):
    from psf_os import feedforward as FF
    import rus2_night as R2
    import rus3_night as R3
    if presc == "P0":
        return FF.rus_chain(L, THETA, m=3)
    if presc == "P1":
        return R2.flip_chain(L, THETA)
    if presc == "P2":
        return R3.chain(L, THETA)
    if presc == "P3":
        return FF.rus_chain(L, THETA, m=2)
    if presc == "NF":
        return R2.flip_chain(L, THETA, flip=False)
    raise ValueError(presc)


def offset_of(st):
    q = [x for x in st if x.startswith("Q")]
    return int(q[0][1:]) if q else 0


def probe_item():
    """X on the probe positions, each read at once into its own bit; success = every bit 1 (not judged)."""
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
    qc = QuantumCircuit(QuantumRegister(PROBE_N, "q"), ClassicalRegister(len(PROBE_POS), "c"))
    for i, p in enumerate(PROBE_POS):
        qc.x(p)
        qc.measure(p, i)
    return qc, dict(success={i: 1 for i in range(len(PROBE_POS))}, bound=None)


def items_for(stacks):
    """[(tag, circuit, spec)] and {tag: (L, role, offset)}; roles: p0, x (one circuit), xr / xn (the two frames)."""
    out, meta = [], {}
    for L in LS:
        out.append((f"p0_{L}", *base_item("P0", L)))
        meta[f"p0_{L}"] = (L, "p0", 0)
    for L in LS:
        st = stacks[str(L)]
        if st == ["P0"]:
            continue
        o = offset_of(st)
        if "B" in st:
            out.append((f"xr{L}", *base_item("P2", L)))
            out.append((f"xn{L}", *base_item("NF", L)))
            meta[f"xr{L}"], meta[f"xn{L}"] = (L, "xr", o), (L, "xn", o)
        else:
            out.append((f"x{L}", *base_item(st[0], L)))
            meta[f"x{L}"] = (L, "x", o)
    out.append(("dr", *probe_item()))
    meta["dr"] = (0, "probe", 0)
    return out, meta


def chains_for(dev, meta):
    """Rule-C chains for the shifted items (+Q). The shift is read on one rule-C chain: refused unless the chain for
    n + o sites starts as the probe's chain (rule C's chain is then the same line, read from position o)."""
    from psf_os import feedforward as FF
    full = FF.place(dev, PROBE_N + max(OFFSETS))["chain"]
    out = {}
    for tag, (L, role, o) in meta.items():
        if role in ("x", "xr", "xn") and o:
            n = 2 * L
            ch = FF.place(dev, n + o)["chain"]
            if ch != full[:n + o]:
                raise SystemExit(f"REFUSED: rule C's chain for {n + o} sites is not a prefix of the probe's chain")
            out[tag] = ch[o:o + n]
    return out


# ------------------------------------------------------------------------------------------------ round 1

def _diag_seconds(dirs):
    """The diagnostics' model seconds (their build.json), counted in the night's budget."""
    return float(sum(json.load(open(os.path.join(d, "build.json")))["qpu_seconds_model"] for d in (dirs or [])))


def round1(a):
    """Round 1 stacks = os_night's pick per L (its rule, unchanged; its Dr carried as round 0's readout)."""
    R = json.load(open(a.os_rule))
    stacks = {str(L): [R["pick"][str(L)]] for L in LS}
    dr = {str(v["physical_qubit"]): dict(p11=v["p_read1_given1"], p00=v["p_read0_given0"], gap=v["gap"]["d"],
                                          two_se=v["gap"]["two_se"], sig=v["gap"]["loss"])
          for v in R["dr"].values()}
    dev = R.get("device") or a.device
    if not dev:
        raise SystemExit("the os_night rule.json names no device (made before that field): give --device")
    out = dict(round=1, device=dev, stacks=stacks, why={str(L): "round 1: gpu/os_night.py rule" for L in LS},
               dr_in=dr, stop=False, stop_reason=None, model_seconds_so_far=_diag_seconds(a.diag))
    json.dump(out, open(a.out_rule, "w"), indent=1)
    print(json.dumps(out["stacks"]))


# ------------------------------------------------------------------------------------------------ build / check

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
    chains = chains_for(dev, meta)
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None   # dry runs only, never a device
    rep = FF.build(dev, its, a.out, shots=4000, max_seconds=60, sentinel_spec=spec, chains=chains)
    full = FF.place(dev, PROBE_N + max(OFFSETS))["chain"]
    outq = {}
    for tag, (L, role, o) in meta.items():
        if role in ("x", "xr", "xn", "p0"):
            outq[tag] = rep["items"][tag]["chain"][2 * L - 1]
    probe_q = [rep["items"]["dr"]["chain"][p] for p in PROBE_POS]
    if probe_q != [full[p] for p in PROBE_POS]:
        os.rename(os.path.join(a.out, "job"), os.path.join(a.out, "job_REFUSED"))
        print("REFUSED: the probe is not on the rule-C chain the offsets are read on (job moved to job_REFUSED)")
        return False
    R2 = dict(R, meta={t: list(v) for t, v in meta.items()}, output_qubit=outq, probe_qubits=probe_q,
              probe_positions=list(PROBE_POS), qpu_seconds_model=rep["qpu_seconds_model"])
    json.dump(R2, open(os.path.join(a.out, "rule.json"), "w"), indent=1)
    print(json.dumps({k: rep[k] for k in ("device", "circuits", "qpu_seconds_model", "shots") if k in rep}))
    print("stacks", json.dumps(R["stacks"]), "output qubits", json.dumps(outq), "probe qubits", probe_q)


def _p_out(n, counts, bit, flipped):
    from psf_os import feedforward as FF
    tot = sum(counts.values())
    p = sum(v for k, v in counts.items() if FF._bits(k, n)[bit] == 1) / tot
    return (1 - p if flipped else p), tot


def _read_spec(tag, L):
    """(out bit, read flipped) for each role: P0 m = 3; m = 2 otherwise; rd (P2) read flipped."""
    return (L * 3, False) if tag.startswith("p0") else (L * 2, None)


def check(a):
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    from psf_os import feedforward as FF
    R = json.load(open(os.path.join(a.out, "rule.json")))
    ref = refs()
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
            L, role, _ = R["meta"][tag]
            cc = FF.compact(c)
            n = cc.num_clbits
            cnt = AerSimulator().run(cc, shots=4000, seed_simulator=20261118).result().get_counts()
            tot = sum(cnt.values())
            allz = sum(v for k, v in cnt.items() if set(FF._bits(k, n)) == {0}) / tot
            if cell["role"] == "floor":
                ok, p = allz == 1.0, float("nan")
            elif role == "probe":
                p = sum(v for k, v in cnt.items() if set(FF._bits(k, n)) == {1}) / tot
                ok = p == 1.0
            else:
                st = R["stacks"][str(L)]
                presc = "P0" if role == "p0" else ("P2" if role == "xr" else ("NF" if role == "xn" else st[0]))
                mm = 3 if presc == "P0" else 2
                p, _ = _p_out(n, cnt, L * mm, presc == "P2")
                arm = "ff" if cell["role"] == "user" else "off"
                want = ref["P0"][L][arm] if presc == "P0" else ref["m2"][L][arm]
                ok = abs(p - want) <= TOL
            print(f"{cell['name']:14s} {role:5s} {cell['role']:6s} P {p:.3f} all zero {allz:.3f} {'ok' if ok else 'FAIL'}")
            bad += [] if ok else [cell["name"]]
    print("PASS" if not bad else f"FAIL {bad}")
    return not bad


# ------------------------------------------------------------------------------------------------ score

def _se(p, n):
    return math.sqrt(max(p * (1 - p), 0.0) / n)


def dr_from_probe(out, R):
    """{physical qubit: dict(p11, p00, gap = p00 - p11, two_se, sig)} from the probe's ff and floor arms."""
    import ctrl_night as CN
    from psf_os import feedforward as FF
    g = CN._counts(out)
    n1, c1 = g[("dr", "ff")]
    n0, c0 = g[("dr", "floor")]
    res = {}
    for i, q in enumerate(R["probe_qubits"]):
        t1, t0 = sum(c1.values()), sum(c0.values())
        p11 = sum(v for k, v in c1.items() if FF._bits(k, n1)[i] == 1) / t1
        p00 = sum(v for k, v in c0.items() if FF._bits(k, n0)[i] == 0) / t0
        se = math.sqrt(_se(p11, t1) ** 2 + _se(p00, t0) ** 2)
        d = p00 - p11
        res[str(q)] = dict(p11=p11, p00=p00, gap=d, two_se=2 * se, sig=bool(d > 0 and d >= 2 * se))
    return res


def score(a):
    import ctrl_night as CN
    R = json.load(open(os.path.join(a.out, "rule.json")))
    ref = refs()
    g = CN._counts(a.out)
    rows = {}
    for L in LS:
        st = R["stacks"][str(L)]
        ex = ref["exact"][L]
        p0, n0 = _p_out(*g[(f"p0_{L}", "ff")], L * 3, False)
        row = dict(stack=st, p0=p0, p0_n=n0, exact=ex, output_qubit_p0=R["output_qubit"][f"p0_{L}"])
        if st == ["P0"]:
            row.update(verdict="NO PRESCRIPTION")
            rows[str(L)] = row
            continue
        noiseless = ref["m2"][L]["ff"]
        if "B" in st:
            pr, nr = _p_out(*g[(f"xr{L}", "ff")], L * 2, True)
            pn, nn = _p_out(*g[(f"xn{L}", "ff")], L * 2, False)
            p = (pr + pn) / 2
            se_p = math.sqrt(_se(pr, nr) ** 2 + _se(pn, nn) ** 2) / 2
            row.update(rd=pr, nf=pn, rd_share=pr / noiseless, nf_share=pn / noiseless,
                       share_gap=(pr - pn) / noiseless,
                       share_gap_two_se=2 * math.sqrt(_se(pr, nr) ** 2 + _se(pn, nn) ** 2) / noiseless,
                       output_qubit_rd=R["output_qubit"][f"xr{L}"], output_qubit_nf=R["output_qubit"][f"xn{L}"])
        else:
            p, nx = _p_out(*g[(f"x{L}", "ff")], L * 2, st[0] == "P2")
            se_p = _se(p, nx)
            row.update(output_qubit=R["output_qubit"][f"x{L}"])
        gain = abs(p0 - ex) - abs(p - ex)
        se_g = math.sqrt(_se(p0, n0) ** 2 + se_p ** 2)
        over = p > noiseless + 2 * se_p
        v = "OVERSHOOT" if over else ("PRESCRIPTION HELPS" if (gain > 0 and gain >= 2 * se_g) else "NOT SHOWN")
        row.update(p=p, se=se_p, noiseless=noiseless, overshoot=bool(over), g=gain, g_se=se_g, verdict=v)
        rows[str(L)] = row
        print(f"L {L} [{stack_name(st)}]: P {p:.4f} (noiseless {noiseless:.4f}) P0 {p0:.4f} g {gain:+.4f} "
              f"(2 SE {2 * se_g:.4f}) -> {v}" + (f"; rd {row['rd']:.4f} nf {row['nf']:.4f}" if "B" in st else ""))
    dr = dr_from_probe(a.out, R)
    print("Dr:", " ".join(f"q{q} gap {v['gap']:+.4f} (2 SE {v['two_se']:.4f}){'*' if v['sig'] else ''}"
                          for q, v in dr.items()))
    out = dict(round=R["round"], device=R["device"], stacks=R["stacks"], rows=rows, dr=dr,
               probe_qubits=R["probe_qubits"], qpu_seconds_model=R["qpu_seconds_model"],
               model_seconds_so_far=R.get("model_seconds_so_far", 0.0) + R["qpu_seconds_model"])
    json.dump(out, open(os.path.join(a.out, "round_scores.json"), "w"), indent=1)
    return out


# ------------------------------------------------------------------------------------------------ the rule

def next_stacks(rounds, chain_full=None, k_max=K_MAX, budget=BUDGET_S, next_cost=None):
    """rounds: the round_scores of rounds 1 .. k in order. Returns the next RULE dict (stacks, why per L, stop).
    chain_full: the rule-C chain the offsets are read on (physical qubits; the probe's chain prefix). The rule reads only
    the rounds' own scores and Dr; no calibration number."""
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
            dr_ok = qn in dr and dr[qn]["sig"]
            if gap_ok and dr_ok and chain_full is not None:
                cands = []
                for o in OFFSETS:
                    q = str(chain_full[o + 2 * L - 1])
                    if q in dr:
                        cands.append((dr[q]["gap"], o, q))
                best = min(cands) if cands else None
                if best and best[1] != 0:
                    new, reason = st + [f"Q{best[1]}"], (f"R2 frames (nf share {row['nf_share']:.3f} < rd "
                                                          f"{row['rd_share']:.3f}; Dr gap on q{qn} {dr[qn]['gap']:+.4f}) "
                                                          f"-> +Q{best[1]} (output on q{best[2]}, gap {best[0]:+.4f})")
                else:
                    reason = "R2 conditions met, but no candidate offset has a smaller gap: keep"
        if new is st and prev is not None:
            prow = prev["rows"].get(sL, {})
            if (row.get("verdict") == "NOT SHOWN" and prow.get("verdict") == "NOT SHOWN"
                    and list(prow.get("stack", [])) == st):
                new = st[:-1] if len(st) > 1 else ["P0"]
                reason = "R3 stop-loss: NOT SHOWN twice with the same stack -> " + stack_name(new)
        stacks[sL], why[sL] = new, reason
    k = cur["round"]
    spent = cur.get("model_seconds_so_far", 0.0)
    unchanged = all(stacks[str(L)] == list(cur["rows"][str(L)]["stack"]) for L in LS)
    any_over = any(cur["rows"][str(L)].get("verdict") == "OVERSHOOT" for L in LS)
    # a NOT SHOWN seen once is not settled: one more round lets R3 act on it
    pending = any(cur["rows"][str(L)].get("verdict") == "NOT SHOWN" and not (
        prev is not None and prev["rows"].get(str(L), {}).get("verdict") == "NOT SHOWN") for L in LS)
    stop, reason = False, None
    if unchanged and not any_over and not pending:
        stop, reason = True, "fixed point: every L keeps its stack, none overshoots, none NOT SHOWN for the first time"
    elif k >= k_max:
        stop, reason = True, f"round limit K = {k_max}"
    elif next_cost is not None and spent + next_cost > budget:
        stop, reason = True, f"budget: {spent:.1f} + {next_cost:.1f} > {budget:.0f} s"
    return dict(round=k + 1, device=cur["device"], stacks=stacks, why=why, stop=stop, stop_reason=reason,
                model_seconds_so_far=spent)


def rule(a):
    from psf_os.device import Device  # noqa: F401  (the chain is read from the last round's build)
    rounds = [json.load(open(os.path.join(d, "round_scores.json"))) for d in a.rounds]
    last_rule = json.load(open(os.path.join(a.rounds[-1], "rule.json")))
    b = json.load(open(os.path.join(a.rounds[-1], "build.json")))
    chain_full = _probe_chain(b, last_rule)
    R = next_stacks(rounds, chain_full, k_max=a.k_max)
    json.dump(R, open(a.out_rule, "w"), indent=1)
    for L in LS:
        print(f"L {L}: {stack_name(R['stacks'][str(L)])}  ({R['why'][str(L)]})")
    print("STOP:" if R["stop"] else "next round", R["round"], R["stop_reason"] or "")


def _probe_chain(build_json, rule_json):
    """The physical qubits of chain positions 0 .. PROBE_N - 1 (the probe item's chain)."""
    return build_json["items"]["dr"]["chain"]


# ------------------------------------------------------------------------------------------------ compounding of the OS

def _slope(xs, ys, ses):
    w = [1 / s ** 2 for s in ses]
    W = sum(w)
    xb = sum(wi * x for wi, x in zip(w, xs)) / W
    yb = sum(wi * y for wi, y in zip(w, ys)) / W
    sxx = sum(wi * (x - xb) ** 2 for wi, x in zip(w, xs))
    return sum(wi * (x - xb) * (y - yb) for wi, x, y in zip(w, xs, ys)) / sxx, math.sqrt(1 / sxx)


def compound_rows(rounds):
    """G_k = mean of g over the L credited in every round compared (no overshoot in any of them), so that each round's
    mean is over the same L; SE from the per-L SEs. Per-L g beside."""
    common = [str(L) for L in LS if all("g" in r["rows"][str(L)] and not r["rows"][str(L)].get("overshoot")
                                         for r in rounds)]
    per_L = {str(L): [(r["round"], r["rows"][str(L)].get("g"), r["rows"][str(L)].get("verdict")) for r in rounds]
             for L in LS}
    res = dict(common_L=common, per_L=per_L)
    if not common:
        res.update(verdict="NOT JUDGEABLE", why="no L credited in every round")
        return res
    G = []
    for r in rounds:
        gs = [(r["rows"][L]["g"], r["rows"][L]["g_se"]) for L in common]
        G.append(dict(round=r["round"], G=sum(x for x, _ in gs) / len(gs),
                      se=math.sqrt(sum(s_ ** 2 for _, s_ in gs)) / len(gs)))
    res["per_round"] = G
    if len(G) >= 3:
        b, sb = _slope([x["round"] for x in G], [x["G"] for x in G], [x["se"] for x in G])
        last_over = any(v.get("overshoot") for v in rounds[-1]["rows"].values())
        res.update(slope=b, se=sb, verdict="OS COMPOUNDS" if (b >= 2 * sb and not last_over) else "NOT SHOWN")
    else:
        res.update(verdict="NOT JUDGEABLE", why=f"{len(G)} round(s): a slope needs three")
        if len(G) == 2:
            d = G[1]["G"] - G[0]["G"]
            sd = math.sqrt(G[0]["se"] ** 2 + G[1]["se"] ** 2)
            res.update(difference_beside=d, two_se_beside=2 * sd)
    return res


def compound(a):
    rounds = [json.load(open(os.path.join(d, "round_scores.json"))) for d in a.rounds]
    res = compound_rows(rounds)
    print(json.dumps(res, indent=1))
    return res


# ------------------------------------------------------------------------------------------------ trial on 2026-11-17

def trial(a):
    """The rule applied to the recorded rounds of 2026-11-17 on ibm_marrakesh (one device record, calibration
    2026-11-13 18:22 CET), desk only. Round 1 = the prescription loop's main job (P2 at L = 1, 2, 3, with P0). Round 2
    'as if' = the frame-balanced job an hour later, which holds exactly what the rule picks for round 2 (L = 1: P2 + B
    as rd1 + nf1; L = 2, 3: P2 as rd2, rd3) but no P0: g is read against round 1's P0 (another job, flagged). Dr: the
    loop's diagnostics (qubits 1, 3, 5; the balanced job has no probe). Chain: physical qubits 0 .. 9 (the record's
    rule-C chain, as both jobs used)."""
    import rus3_night as R3  # noqa: F401
    ref = refs()
    base = os.path.join(NB, "results")
    osr = json.load(open(os.path.join(base, "os-night-2026-11-17", "main", "os_scores.json")))
    rl = json.load(open(os.path.join(base, "os-night-2026-11-17", "rule.json")))
    bal = json.load(open(os.path.join(base, "balanced-night-2026-11-17", "balanced_scores.json")))
    bb = json.load(open(os.path.join(base, "balanced-night-2026-11-17", "build.json")))
    ob = json.load(open(os.path.join(base, "os-night-2026-11-17", "main", "build.json")))
    dr = {str(v["physical_qubit"]): dict(p11=v["p_read1_given1"], p00=v["p_read0_given0"], gap=v["gap"]["d"],
                                          two_se=v["gap"]["two_se"], sig=bool(v["gap"]["loss"]))
          for v in rl["dr"].values()}
    chain_full = list(range(PROBE_N))
    assert ob["items"]["x1"]["chain"] == chain_full[:2] and bb["items"]["nf1"]["chain"] == chain_full[:2]
    # round 1
    rows1 = {}
    for L in LS:
        c, p0 = osr["cards"][f"x{L}"], osr["cards"][f"p0_{L}"]
        h = osr["helps"][str(L)]
        sx = _se(c["ff"]["p1"], c["ff"]["counted"])
        rows1[str(L)] = dict(stack=["P2"], p=c["ff"]["p1"], se=sx, noiseless=h["x_noiseless"], p0=p0["ff"]["p1"],
                             g=h["gain"], g_se=h["two_se"] / 2, overshoot=bool(h["overshoot"]), verdict=h["verdict"],
                             output_qubit=ob["items"][f"x{L}"]["chain"][2 * L - 1])
    r1 = dict(round=1, device="ibm_marrakesh", stacks={str(L): ["P2"] for L in LS}, rows=rows1, dr=dr,
              model_seconds_so_far=27.6)
    nx2 = next_stacks([r1], chain_full)
    # round 2 as if: the balanced job
    rows2 = {}
    for L in LS:
        st = nx2["stacks"][str(L)]
        b = bal["rows"][str(L)]
        p0 = rows1[str(L)]["p0"]
        ex = ref["exact"][L]
        noiseless = ref["m2"][L]["ff"]
        if "B" in st:
            p, se = b["p_pooled"], b["se"]
            pr, pn = b["rd"], b["nf"]
            n = 4000
            extra = dict(rd=pr, nf=pn, rd_share=pr / noiseless, nf_share=pn / noiseless, share_gap=(pr - pn) / noiseless,
                         share_gap_two_se=2 * math.sqrt(_se(pr, n) ** 2 + _se(pn, n) ** 2) / noiseless,
                         output_qubit_rd=bb["items"][f"rd{L}"]["chain"][2 * L - 1],
                         output_qubit_nf=bb["items"][f"nf{L}"]["chain"][2 * L - 1])
        else:
            p, se = b["rd"], _se(b["rd"], 4000)
            extra = dict(output_qubit=bb["items"][f"rd{L}"]["chain"][2 * L - 1])
        gain = abs(p0 - ex) - abs(p - ex)
        se_g = math.sqrt(_se(p0, 4000) ** 2 + se ** 2)
        over = p > noiseless + 2 * se
        v = "OVERSHOOT" if over else ("PRESCRIPTION HELPS" if (gain > 0 and gain >= 2 * se_g) else "NOT SHOWN")
        rows2[str(L)] = dict(stack=st, p=p, se=se, noiseless=noiseless, p0=p0, g=gain, g_se=se_g, overshoot=bool(over),
                             verdict=v, p0_from="round 1 (another job, an hour earlier)", **extra)
    r2 = dict(round=2, device="ibm_marrakesh", stacks=nx2["stacks"], rows=rows2, dr=dr, model_seconds_so_far=27.6 + 40.9)
    nx3 = next_stacks([r1, r2], chain_full)
    comp = compound_rows([r1, r2])
    res = dict(round1=r1, rule_for_round2=nx2, round2_as_if=r2, rule_for_round3=nx3, os_compounding=comp)
    json.dump(res, open(a.out_json, "w"), indent=1)
    print("round 1 (os-night main, recorded):")
    for L in LS:
        r = rows1[str(L)]
        print(f"  L {L} [P2]: P {r['p']:.4f} (noiseless {r['noiseless']:.4f}) P0 {r['p0']:.4f} g {r['g']:+.4f} "
              f"(2 SE {2 * r['g_se']:.4f}) -> {r['verdict']}")
    print("rule -> round 2:", {L: (stack_name(nx2['stacks'][str(L)]), nx2['why'][str(L)]) for L in LS},
          "stop" if nx2["stop"] else "")
    print("round 2 as if (balanced job; P0 from round 1):")
    for L in LS:
        r = rows2[str(L)]
        print(f"  L {L} [{stack_name(r['stack'])}]: P {r['p']:.4f} (noiseless {r['noiseless']:.4f}) g {r['g']:+.4f} "
              f"(2 SE {2 * r['g_se']:.4f}) -> {r['verdict']}" +
              (f"; rd {r['rd']:.4f} nf {r['nf']:.4f} (shares {r['rd_share']:.3f} / {r['nf_share']:.3f})" if "rd" in r else ""))
    print("rule -> round 3:", {L: (stack_name(nx3['stacks'][str(L)]), nx3['why'][str(L)]) for L in LS},
          ("STOP: " + nx3["stop_reason"]) if nx3["stop"] else "")
    print("OS compounding (G per round):", comp)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r1 = sub.add_parser("round1")
    r1.add_argument("os_rule")
    r1.add_argument("out_rule")
    r1.add_argument("--device", help="only for an os_night rule.json written before it recorded the device")
    r1.add_argument("--diag", nargs="*", default=[], help="the diagnostic job folders (Dw, Dc): their model seconds "
                    "start the night's budget")
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    b.add_argument("rule_json")
    b.add_argument("--dry-clifford-sentinel", action="store_true",
                   help="dry runs only: the ring sentinel at its Clifford point; never for the device job")
    for nm in ("check", "score"):
        sub.add_parser(nm).add_argument("out")
    r = sub.add_parser("rule")
    r.add_argument("out_rule")
    r.add_argument("rounds", nargs="+")
    r.add_argument("--k-max", type=int, default=K_MAX, help="dry runs only (gpu/os2_run.py refuses it on a device)")
    c = sub.add_parser("compound")
    c.add_argument("rounds", nargs="+")
    t = sub.add_parser("trial")
    t.add_argument("out_json")
    a = ap.parse_args()
    res = {"round1": round1, "build": build, "check": check, "score": score, "rule": rule, "compound": compound,
           "trial": trial}[a.cmd](a)
    sys.exit(0 if res is not False else 1)
