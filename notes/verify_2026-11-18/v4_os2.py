"""4. The compounding OS (results/os2-night-2026-11-18): the declared rules applied by hand to numbers read here from
the raw counts (home VS Claude, 2026-11-18; qiskit and numpy only).

Diagnostics, read from the circuits: in a Dc item the control is the qubit with the first X, the target its CZ partner,
each read from its last measurement; in a Dw item the output is the qubit measured once (its bit), the ancilla the
qubit measured repeatedly. Shares: P(bit = 1) of the ff arm (Dw: wT's off arm = T_mid, wT's ff arm = T_ff).
  rule 1 (prereg/os_night_2026-11-17.md): D_late_nb = now.target - nb.target > 0 and >= 2 SE at A or B -> P1 for every L
  rule 2: per L, the Dr gap P(0|0) - P(1|1) on that L's output qubit > 0 and >= 2 SE -> P2 (Dr: Anow / Bnow control bit,
          Bref's bit; P(1|1) from the ff arm, P(0|0) from the floor arm)
  rule 3: if rule 1 does not hold: D_cond = T_mid - T_ff > 0 and >= 2 SE at A or B -> P3; rule 4: otherwise P0.
Round 1: P(stack) and P0 read as the bit (P1 holds logical 1 as |1> at the read); exact = the ideal chain; the
noiseless value of each circuit by exact branching; g = |P0 - exact| - |P(stack) - exact|, SE of the difference;
OVERSHOOT when P(stack) > noiseless + 2 SE(stack); HELPS when g > 0 and g >= 2 SE.
Round 2 by R1-R4 (prereg/os2_night_2026-11-18.md) and the stop rule.
usage: python notes/verify_2026-11-18/v4_os2.py   (from the notebook root)"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = "results/os2-night-2026-11-18"
LINES = []


def say(s):
    print(s, flush=True)
    LINES.append(s)


def share(counts, bit):
    p, n = V.p_bit(counts, bit)
    return p, n


def diff(a, b):
    (pa, na), (pb, nb) = a, b
    return pa - pb, 2 * math.sqrt(pa * (1 - pa) / na + pb * (1 - pb) / nb)


def loss(d):
    return d[0] > 0 and d[0] >= d[1]


def ctrl_target(qc):
    c, phys = V.compact(qc)
    first_x = next(c.find_bit(i.qubits[0]).index for i in c.data if i.operation.name == "x")
    partner = next((set(c.find_bit(x).index for x in i.qubits) - {first_x}).pop() for i in c.data
                   if i.operation.name == "cz" and first_x in {c.find_bit(x).index for x in i.qubits})
    last = {}
    for b, q, k in V.measured(c):
        last[q] = b
    return dict(control_bit=last[first_x], target_bit=last[partner], control_q=phys[first_x], target_q=phys[partner])


def main():
    dc, _ = V.load_job(os.path.join(ROOT, "dc"))
    dw, _ = V.load_job(os.path.join(ROOT, "dw"))
    late, dr = {}, {}
    for p in ("A", "B"):
        now, nb = ctrl_target(dc[f"ff_{p}now"]["circuit"]), ctrl_target(dc[f"ff_{p}nb"]["circuit"])
        s_now = share(dc[f"ff_{p}now"]["counts"], now["target_bit"])
        s_nb = share(dc[f"ff_{p}nb"]["counts"], nb["target_bit"])
        late[p] = diff(s_now, s_nb)
        say(f"Dc {p}: control q{now['control_q']} (bit {now['control_bit']}), target q{now['target_q']} (bit "
            f"{now['target_bit']}); now target 1 {s_now[0]:.4f}, nb target 1 {s_nb[0]:.4f}; D_late_nb {late[p][0]:+.4f} "
            f"(2 SE {late[p][1]:.4f}) loss {loss(late[p])}")
    cond = {}
    for p in ("A", "B"):
        c, phys = V.compact(dw[f"ff_{p}wT"]["circuit"])
        ob, oq = V.out_bit_general(c)
        t_mid = share(dw[f"ff_{p}wT_off"]["counts"], ob)
        t_ff = share(dw[f"ff_{p}wT"]["counts"], ob)
        cond[p] = diff(t_mid, t_ff)
        say(f"Dw {p}: output q{phys[oq]} (bit {ob}); T_mid {t_mid[0]:.4f}, T_ff {t_ff[0]:.4f}; D_cond {cond[p][0]:+.4f} "
            f"(2 SE {cond[p][1]:.4f}) loss {loss(cond[p])}")
    src = {1: (dc, "Anow", "control"), 2: (dc, "Bnow", "control"), 3: (dw, "Bref", "ref")}
    for L, (job, tag, kind) in src.items():
        c, phys = V.compact(job[f"ff_{tag}"]["circuit"])
        if kind == "control":
            ct = ctrl_target(job[f"ff_{tag}"]["circuit"])
            bit, q = ct["control_bit"], ct["control_q"]
        else:
            ob, oq = V.out_bit_general(c)
            bit, q = ob, phys[oq]
        p11, n1 = share(job[f"ff_{tag}"]["counts"], bit)
        p1f, n0 = share(job[f"ff_{tag}_floor"]["counts"], bit)
        p00 = 1 - p1f
        d = (p00 - p11, 2 * math.sqrt(p00 * (1 - p00) / n0 + p11 * (1 - p11) / n1))
        dr[L] = dict(q=q, p11=p11, p00=p00, gap=d)
        say(f"Dr L {L} (q{q}, {tag} bit {bit}): P(1|1) {p11:.4f}, P(0|0) {p00:.4f}, gap {d[0]:+.4f} (2 SE {d[1]:.4f}) "
            f"loss {loss(d)}")
    if any(loss(v) for v in late.values()):
        pick = {L: "P2" if loss(dr[L]["gap"]) else "P1" for L in (1, 2, 3)}
        why = "rule 1, rule 2 per L"
    elif any(loss(v) for v in cond.values()):
        pick, why = {L: "P3" for L in (1, 2, 3)}, "rule 3"
    else:
        pick, why = {L: "P0" for L in (1, 2, 3)}, "rule 4"
    home_rule = json.load(open(os.path.join(ROOT, "RULE1.json")))
    say(f"pick by hand: {pick} ({why}); recorded RULE1 stacks: {home_rule['stacks']}")
    # round 1
    r1, _ = V.load_job(os.path.join(ROOT, "r1"))
    verdicts = {}
    for L in (1, 2, 3):
        ex, _ = V.ideal_chain(L, 1.1)
        rows = {}
        for nm in (f"p0_{L}", f"x{L}"):
            c, phys = V.compact(r1[f"ff_{nm}"]["circuit"])
            ob, oq = V.out_bit_general(c)
            p, n = V.p_bit(r1[f"ff_{nm}"]["counts"], ob)
            nl = V.p_bit_dist(V.branch_dist(c), ob)
            rec_ob = (r1[f"ff_{nm}"]["record"] or {}).get("rus", {}).get("out_bit")
            rows[nm] = dict(P=p, n=n, noiseless=nl, out_bit=ob, out_bit_record=rec_ob, qubit=phys[oq])
        p0, x = rows[f"p0_{L}"], rows[f"x{L}"]
        g = abs(p0["P"] - ex) - abs(x["P"] - ex)
        se = math.sqrt(p0["P"] * (1 - p0["P"]) / p0["n"] + x["P"] * (1 - x["P"]) / x["n"])
        sx = math.sqrt(x["P"] * (1 - x["P"]) / x["n"])
        over = x["P"] > x["noiseless"] + 2 * sx
        v = "OVERSHOOT" if over else ("PRESCRIPTION HELPS" if g > 0 and g >= 2 * se else "NOT SHOWN")
        verdicts[L] = dict(g=g, two_se=2 * se, P=x["P"], P0=p0["P"], noiseless=x["noiseless"], verdict=v, overshoot=over,
                           out_bits=(p0["out_bit"], x["out_bit"]), out_bits_record=(p0["out_bit_record"], x["out_bit_record"]))
        say(f"L {L} [{pick[L]}]: P {x['P']:.4f} (noiseless {x['noiseless']:.4f}) P0 {p0['P']:.4f} (noiseless "
            f"{p0['noiseless']:.4f}) exact {ex:.4f}  g {g:+.4f} (2 SE {2 * se:.4f}) -> {v};  out bits p0 {p0['out_bit']} "
            f"(record {p0['out_bit_record']}), x {x['out_bit']} (record {x['out_bit_record']}), output qubit {x['qubit']}")
    # round 2 rule
    nxt, notes = {}, {}
    for L in (1, 2, 3):
        stack = [pick[L]]
        v = verdicts[L]["verdict"]
        if v == "OVERSHOOT" and "+B" not in stack:
            nxt[L], notes[L] = ["P2", "+B"], "R1"
        elif "+B" in stack and "+Q" not in stack:
            nxt[L], notes[L] = stack, "R2 (needs the frames; not reached)"
        elif v == "NOT SHOWN" and False:            # R3 needs NOT SHOWN in round k and k - 1: one round only
            nxt[L], notes[L] = stack, "R3"
        else:
            nxt[L], notes[L] = stack, "R4 keep"
    fixed = all(nxt[L] == [pick[L]] for L in (1, 2, 3)) and not any(verdicts[L]["overshoot"] for L in (1, 2, 3)) \
        and not any(verdicts[L]["verdict"] == "NOT SHOWN" for L in (1, 2, 3))
    say(f"round 2 rule by hand: " + "; ".join(f"L {L}: {nxt[L]} ({notes[L]})" for L in (1, 2, 3)) +
        f" -> {'STOP: fixed point after round 1' if fixed else 'continue'}")
    rs = json.load(open(os.path.join(ROOT, "r1", "round_scores.json"))) if os.path.exists(
        os.path.join(ROOT, "r1", "round_scores.json")) else None
    if rs:
        say("recorded round 1 scores: " + json.dumps(rs, default=str)[:700])
    G = [verdicts[L]["g"] for L in (1, 2, 3) if not verdicts[L]["overshoot"]]
    say(f"G_1 = mean g over credited L = {sum(G) / len(G):.4f}")
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    json.dump(dict(late=late, cond=cond, dr=dr, pick=pick, round1=verdicts, round2=nxt, fixed_point=fixed),
              open(os.path.join(HERE, "out", "v4_os2.json"), "w"), indent=1, default=str)
    open(os.path.join(HERE, "out", "v4_os2.txt"), "w").write("\n".join(LINES) + "\n")


if __name__ == "__main__":
    main()
