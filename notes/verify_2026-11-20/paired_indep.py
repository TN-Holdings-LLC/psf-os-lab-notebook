"""Independent recount of results/loop-paired-night-2026-11-20 (home VS): qiskit / aer / numpy only, no psf-os and no
notebook scorer. Shares from each job's raw_counts.json and manifest.json; the right value of each output bit and the
noiseless share from noiseless Aer sampling of the recorded circuit itself; exact = sin^2(arctan(tan^2 1.1))^L
(derived here). The paired rule as declared (prereg/loop_paired_night_2026-11-20.md, climb_on_kept on) is written
again below in a few lines and applied to the recounted numbers."""
import json
import math
import sys

from qiskit import qpy
from qiskit_aer import AerSimulator

R = sys.argv[1]
OUT = sys.argv[2]
SHOTS_IDEAL = 400_000
EXACT = {L: math.sin(math.atan(math.tan(1.1) ** 2)) ** (2 * L) for L in (1, 2, 3)}
sim = AerSimulator()


def bit(key, i):
    """Clbit i of a counts key (clbit 0 rightmost)."""
    k = key.replace(" ", "")
    return int(k[-1 - i])


def share(cnt, i, val):
    n = sum(cnt.values())
    return sum(v for k, v in cnt.items() if bit(k, i) == val) / n, n


def diff(p1, n1, p2, n2):
    d = p1 - p2
    return d, 2 * math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)


class Job:
    def __init__(self, name):
        self.dir = f"{R}/{name}"
        man = json.load(open(f"{self.dir}/job/manifest.json"))
        raw = json.load(open(f"{self.dir}/job/raw_counts.json"))
        self.circs = qpy.load(open(f"{self.dir}/job/circuits.qpy", "rb"))
        cells = {c["cell"]: c["name"] for c in man["cells"]}
        self.pub = {cells[p["cell"]]: i for i, p in enumerate(man["pubs"]) if p["point"] == 0}
        self.counts = {row["pub"]: row["counts"] for row in raw["rows"]}
        self.shots = {sum(c.values()) for c in self.counts.values()}
        self.n_circ = len(self.circs)
        self.metrics = raw["metrics"]

    def cnt(self, name):
        return self.counts[self.pub[name]]

    def card(self, name):
        return json.load(open(f"{self.dir}/runs/{name}.json"))

    def ideal(self, name, ob):
        res = sim.run(self.circs[self.pub[name]], shots=SHOTS_IDEAL, seed_simulator=11).result().get_counts()
        p1 = sum(n for k, n in res.items() if bit(k, ob) == 1) / SHOTS_IDEAL
        return (1 if p1 > 0.5 else 0), max(p1, 1 - p1)


out = {}
lines = []

# ---- diagnostics: Dc (late use, neighbours read), Dw (unfired conditionals), Dr (readout gap on the output qubits)
dc, dw = Job("dc"), Job("dw")
diag = {}
for p in "AB":
    # D_late_nb = P(target 1 | now, ff) - P(target 1 | nb, ff); the target is the second-to-last clbit
    cn, cb = dc.cnt(f"ff_{p}now"), dc.cnt(f"ff_{p}nb")
    # each item's own clbit count (the counts key may be wider): target n - 2, control n - 1
    s_now, n_now = share(cn, dc.card(f"ff_{p}now")["clbits"] - 2, 1)
    s_nb, n_nb = share(cb, dc.card(f"ff_{p}nb")["clbits"] - 2, 1)
    dl, tl = diff(s_now, n_now, s_nb, n_nb)
    # D_cond = P(out 1 | wT, off) - P(out 1 | wT, ff); the output is the last clbit
    wo, wf = dw.cnt(f"ff_{p}wT_off"), dw.cnt(f"ff_{p}wT")
    nw = dw.card(f"ff_{p}wT")["clbits"]
    s_off, n_off = share(wo, nw - 1, 1)
    s_ff, n_ff = share(wf, nw - 1, 1)
    dcnd, tc = diff(s_off, n_off, s_ff, n_ff)
    diag[p] = dict(late_nb=(dl, tl, dl > 0 and dl >= tl), cond=(dcnd, tc, dcnd > 0 and dcnd >= tc))
    lines.append(f"Dc {p}: D_late_nb {dl:+.4f} (2 SE {tl:.4f}) loss {dl > 0 and dl >= tl};  "
                 f"Dw {p}: D_cond {dcnd:+.4f} (2 SE {tc:.4f}) loss {dcnd > 0 and dcnd >= tc}")
# Dr per L: (job, item, clbit of the qubit); P(1|1) from the ff arm, P(0|0) from the floor arm
dr0 = {}
for L, (job, tag, b) in {1: (dc, "Anow", 1), 2: (dc, "Bnow", 1), 3: (dw, "Bref", 0)}.items():
    p11, n1 = share(job.cnt(f"ff_{tag}"), b, 1)
    p00, n0 = share(job.cnt(f"ff_{tag}_floor"), b, 0)
    gap, two = diff(p00, n0, p11, n1)
    q = job.card(f"ff_{tag}")["chain"][{1: 1, 2: 3, 3: 5}[L]]
    dr0[L] = dict(q=q, p11=p11, p00=p00, gap=gap, two_se=two, loss=gap > 0 and gap >= two)
    lines.append(f"Dr L {L} (physical qubit {q}): P(1|1) {p11:.4f}, P(0|0) {p00:.4f}, gap {gap:+.4f} "
                 f"(2 SE {two:.4f}) loss {dr0[L]['loss']}")
late_any = any(v["late_nb"][2] for v in diag.values())
cond_any = any(v["cond"][2] for v in diag.values())
if late_any:
    pick = {L: ("P2" if dr0[L]["loss"] else "P1") for L in (1, 2, 3)}
elif cond_any:
    pick = {L: "P3" for L in (1, 2, 3)}
else:
    pick = {L: "P0" for L in (1, 2, 3)}
lines.append(f"pick {pick}")
out["diagnostics"] = dict(diag=diag, dr=dr0, pick=pick)


# ---- rounds
def probe_dr(job):
    """The round's own readout probe: X on chain positions 1, 3, .., 9 read at once; clbit i is probe position i."""
    c1, c0 = job.cnt("ff_dr"), job.cnt("ff_dr_floor")
    qs = json.load(open(f"{job.dir}/rule.json"))["probe_qubits"]
    res = {}
    for i, q in enumerate(qs):
        p11, n1 = share(c1, i, 1)
        p00, n0 = share(c0, i, 0)
        gap, two = diff(p00, n0, p11, n1)
        res[q] = dict(p11=p11, p00=p00, gap=gap, two_se=two)
    return res


def arm(job, name):
    card = job.card(name)
    ob = card["rus"]["out_bit"]
    rv, nl = job.ideal(name, ob)
    p, n = share(job.cnt(name), ob, rv)
    return dict(name=name, p=p, n=n, se=math.sqrt(p * (1 - p) / n), noiseless=nl, right=rv, m=card["rus"]["m"],
                chain=card["chain"])


rounds = {}
for rk in ("r1", "r2"):
    job = Job(rk)
    rule = json.load(open(f"{job.dir}/rule.json"))
    meta = rule["meta"]
    rows = {}
    for L in (1, 2, 3):
        p0 = arm(job, f"ff_p0_{L}")
        ex = EXACT[L]
        inc_tags = [t for t, v in meta.items() if v[0] == L and v[5] == "i"]
        cand_tags = [t for t, v in meta.items() if v[0] == L and v[5] == "c"]
        assert len(inc_tags) <= 1 and len(cand_tags) <= 1, (rk, L, inc_tags, cand_tags)   # no B stack tonight
        if not cand_tags:
            rows[L] = dict(p0=p0["p"], candidate=None)
            continue
        inc = arm(job, f"ff_{inc_tags[0]}") if inc_tags else p0
        cand = arm(job, f"ff_{cand_tags[0]}")
        # off and floor arms of the candidate must exist; the incumbent's ff only (ff_only)
        assert f"ff_{cand_tags[0]}_off" in job.pub and f"ff_{cand_tags[0]}_floor" in job.pub
        if inc_tags:
            assert f"ff_{inc_tags[0]}_off" not in job.pub
            assert set(inc["chain"]) == set(cand["chain"]), "incumbent and candidate on other qubits"
        d = abs(inc["p"] - ex) - abs(cand["p"] - ex)
        two = 2 * math.sqrt(inc["se"] ** 2 + cand["se"] ** 2)
        over = cand["p"] > cand["noiseless"] + 2 * cand["se"]
        word = ("CANDIDATE OVERSHOOTS" if over else "CANDIDATE ADOPTED" if d >= two else
                "CANDIDATE NOT ADOPTED" if -d >= two else "INCUMBENT KEPT")
        rows[L] = dict(exact=ex, p0=p0["p"], inc=inc, cand=cand, d=d, two_se=two, overshoot=over, word=word,
                       inc_overshoot=inc["p"] > inc["noiseless"] + 2 * inc["se"],
                       desc=(meta[inc_tags[0]][3:5] if inc_tags else ["P0", 3], meta[cand_tags[0]][3:5]))
    rounds[rk] = dict(rows=rows, dr=probe_dr(job), n_circ=job.n_circ, shots=job.shots, metrics=job.metrics)
    for L, r in rows.items():
        if r.get("candidate", 1) is None:
            lines.append(f"{rk} L {L}: no candidate; P0 {r['p0']:.4f}")
            continue
        lines.append(f"{rk} L {L}: inc {r['desc'][0]} P {r['inc']['p']:.4f} (SE {r['inc']['se']:.4f}, noiseless "
                     f"{r['inc']['noiseless']:.4f}); cand {r['desc'][1]} P {r['cand']['p']:.4f} (SE "
                     f"{r['cand']['se']:.4f}, noiseless {r['cand']['noiseless']:.4f}); exact {r['exact']:.4f}; "
                     f"d {r['d']:+.4f} (2 SE {r['two_se']:.4f}) -> {r['word']}; P0 {r['p0']:.4f}")
    lines.append(f"{rk} Dr: " + "; ".join(f"q{q} P(1|1) {v['p11']:.4f} P(0|0) {v['p00']:.4f} gap {v['gap']:+.4f} "
                                          f"(2 SE {v['two_se']:.4f})" for q, v in rounds[rk]["dr"].items()))


# ---- the declared rule, written again: stacks are tuples of layers; base in {P0, P1, P2}; rungs M then F
def frame(base):
    """Read frame of the base: P1 reads logical 1 as |1>, P2 as |0> (os3 ladder A)."""
    return {"P1": 1, "P2": 0}.get(base)


def against(base, d):
    """Dr against the base's frame on its output qubit, >= 2 SE."""
    f = frame(base)
    if f == 1:
        return d["gap"] >= d["two_se"]            # P(0|0) - P(1|1) >= 2 SE
    if f == 0:
        return -d["gap"] >= d["two_se"]           # P(1|1) - P(0|0) >= 2 SE
    return False


def next_step(stack, tried, dr_q, overshoot_b=False):
    """The next untried step on top of `stack`: B after an overshoot; the base on P0; Q on B; M; F."""
    if overshoot_b and "B" not in tried:
        return ("P2", "B"), "B"
    if stack == ("P0",):
        return (None, None) if "base" in tried else ((pick_now,), "base")
    if "B" in stack:
        raise NotImplementedError("no B stack tonight")
    if "M" not in stack and "M" not in tried:
        return stack + ("M",), "M"
    if "F" not in stack and "F" not in tried and against(stack[0], dr_q):
        return ({"P1": "P2", "P2": "P1"}[stack[0]],) + stack[1:] + ("F",), "F"
    return None, None


inc = {L: ("P0",) for L in (1, 2, 3)}
cand = {L: (pick[L],) for L in (1, 2, 3)}
tried = {L: [] for L in (1, 2, 3)}
step_of = {L: "base" for L in (1, 2, 3)}
stopped = {L: False for L in (1, 2, 3)}
rule_seq = []
for k, rk in enumerate(("r1", "r2"), start=1):
    rows, dr = rounds[rk]["rows"], rounds[rk]["dr"]
    nxt_inc, nxt_cand = {}, {}
    for L in (1, 2, 3):
        if stopped[L] or cand[L] is None:
            nxt_inc[L], nxt_cand[L] = inc[L], None
            stopped[L] = True
            continue
        r = rows[L]
        pick_now = pick[L]
        tried[L].append(step_of[L])
        word = r["word"]
        dq = dr[json.load(open(f"{R}/{rk}/rule.json"))["output_qubit"][f"p0_{L}"]]
        if word == "CANDIDATE ADOPTED":
            new_inc = cand[L]
            base_for_next = new_inc
        elif word == "INCUMBENT KEPT":
            new_inc = inc[L]
            base_for_next = cand[L]                   # climb_on_kept: build on the kept candidate
        else:
            new_inc = inc[L]
            base_for_next = inc[L]
        c, s = next_step(base_for_next, tried[L], dq, overshoot_b=(word == "CANDIDATE OVERSHOOTS"))
        nxt_inc[L], nxt_cand[L], step_of[L] = new_inc, c, s
        if c is None:
            stopped[L] = True
    inc, cand = nxt_inc, nxt_cand
    rule_seq.append(dict(after=rk, incumbents={L: list(v) for L, v in inc.items()},
                         candidates={L: (list(v) if v else None) for L, v in cand.items()},
                         tried={L: list(v) for L, v in tried.items()}))
    lines.append(f"RULE{k + 1} (re-written rule): incumbents {inc}; candidates {cand}; tried {tried}")
stop_all = all(c is None for c in cand.values())
lines.append(f"stop after round 2: every key out of steps: {stop_all}")


def norm(x):
    return {int(k): (tuple(v) if v else None) for k, v in x.items()}


cmp = []
for k, rs in zip((2, 3), rule_seq):
    rec = json.load(open(f"{R}/RULE{k}.json"))
    same = (norm(rec["stacks"]) == {L: tuple(v) for L, v in rs["incumbents"].items()} and
            norm(rec["candidates"]) == {L: (tuple(v) if v else None) for L, v in rs["candidates"].items()})
    cmp.append((k, same, rec.get("stop"), rec.get("stop_reason")))
    lines.append(f"RULE{k}.json recorded: stacks {rec['stacks']} candidates {rec['candidates']} stop {rec.get('stop')} "
                 f"reason {rec.get('stop_reason')} -> {'SAME' if same else 'DIFFERENT'}")

# ---- overshoots, LP-2
overs = [(rk, L) for rk, d in rounds.items() for L, r in d["rows"].items() if r.get("overshoot")]
lines.append(f"candidate overshoots in any round: {overs or 'none'}")
lp2 = []
for (ra, rb) in (("r1", "r2"),):
    for L, r in rounds[ra]["rows"].items():
        if r.get("word") == "CANDIDATE ADOPTED":
            nb = rounds[rb]["rows"].get(L, {})
            if "inc" in nb:
                lp2.append((ra, L, r["desc"][1], nb["inc"]["p"], nb["inc"]["noiseless"], nb["inc"]["se"],
                            nb["inc_overshoot"]))
adopted_last = [(L, r["desc"][1]) for L, r in rounds["r2"]["rows"].items() if r.get("word") == "CANDIDATE ADOPTED"]
lines.append(f"LP-2 rows: {lp2}; adopted in the last round (no next round, not counted): {adopted_last}; "
             f"LP-2 {'held' if lp2 and not any(x[-1] for x in lp2) else 'failed' if lp2 else 'not testable'}")

# ---- time and charge
tot_s = sum(Job(j).metrics["usage"]["qpu_charge_time_seconds"] for j in ("dw", "dc", "r1", "r2"))
tot_ru = sum(Job(j).metrics["usage"]["value"] for j in ("dw", "dc", "r1", "r2"))
lines.append(f"charged {tot_s} s, {tot_ru:.4f} RU; circuits " +
             ", ".join(f"{j} {Job(j).n_circ}" for j in ("dw", "dc", "r1", "r2")) +
             f"; shots {set().union(*(Job(j).shots for j in ('dw', 'dc', 'r1', 'r2')))}")
print("\n".join(lines))
json.dump(dict(lines=lines), open(OUT, "w"), indent=1, default=str)
