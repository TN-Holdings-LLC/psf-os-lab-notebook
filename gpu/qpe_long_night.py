"""Phase estimation at n = 5, 6 (and 4): does the classical side's cost grow with the number of feedbacks? (draft for a
declaration; workplace Claude, 2026-11-20, home's candidate 6 and added instruction 3 item 4; not declared).
gpu/qpe_repro_night.py (declared 2026-11-19) is read only: its textbook circuit, its dry run and its words.

The 2026-11-19 test at larger n: IPE (one ancilla, one target in |1>, bits read least significant first, the phase
feedback of every bit already read, a conditional-X reset) against its ceiling C(n) (the best fixed decoder of the
off arm's bits, exact), and beside it the textbook circuit (n counting qubits routed on a line, final measurements).
1950 shots per circuit; a job of 32 items is 100 circuits (x 3 arms + the sentinel's 4), 59.2 s by the model; plan
shape's job 1 holds 16 items: 52 circuits, 32.2 s (the workplace VS, 2026-11-20).

Plans (`--plan`, one build per job, `--job k`):
  n5      2 jobs: n = 5 IPE and textbook, phases 0-15 and 16-31 (each job holds both circuits of its phases)
  n5n6    4 jobs: n5's two, and n = 6 IPE alone, phases 0-31 and 32-63
  shape   4 jobs: IPE alone at n = 4 (16 phases), 5 (32), 6 (64): n4 + n5 0-15, n5 16-31, n6 0-31, n6 32-63
          (the drop per added bit at three n on one night, without the textbook circuit)

What n = 5, 6 read (notes/ipe_long_2026-11-20/README.md): on 2026-11-19's slope IPE stays far beyond C(n) (about 0.84
and 0.80 against 0.38 and 0.31); the question is whether the drop per added bit stays flat (a loss per round: the
CZ pair and the read) or grows (a loss per conditional: each added bit adds one more feedback than the last: 2, 5, 9,
14, 20 conditionals at n = 2 .. 6). Measure (proposed [OWNER], revised after the dry runs of 2026-11-20): with IPE at three n on one night
(plan shape), on the log of the share, D_n = ln p(n - 1) - ln p(n), the acceleration a = D_6 - D_5 with SE
sqrt(t4^2 + 4 t5^2 + t6^2), t_n = SE_n / p_n; ACCELERATES when a >= 2 SE, FLAT when |a| < 2 SE, SLOWS when
a <= -2 SE. The same on the share itself beside (it hides a per-conditional loss: noise c reads FLAT there).

  python gpu/qpe_long_night.py ideal
  python gpu/qpe_long_night.py build DEVDIR OUT --plan n5|n5n6|shape --job K [--fence] [--dry-clifford-sentinel]
  python gpu/qpe_long_night.py check OUT
  python gpu/qpe_long_night.py dry OUT NOISE.json [--seed S]         illustrative noise only (qpe_repro_night's dry)
  python gpu/qpe_long_night.py score OUT [OUT ...]                   every job of the plan
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
for d in ("notes/ffapps_2026-11-17", "notes/rus_coherent_2026-11-17", "notes/os2_2026-11-18"):
    sys.path.insert(0, os.path.join(NB, d))
import apps as AP  # noqa: E402
import qpe_repro_night as Q  # noqa: E402  (declared 2026-11-19; read only)

SHOTS = 1950
SEED = 20261121
# job -> [(family, n, first phase, last phase + 1)]
PLANS = {
    "n5": [[("ipe", 5, 0, 16), ("tqpe", 5, 0, 16)], [("ipe", 5, 16, 32), ("tqpe", 5, 16, 32)]],
    "n5n6": [[("ipe", 5, 0, 16), ("tqpe", 5, 0, 16)], [("ipe", 5, 16, 32), ("tqpe", 5, 16, 32)],
             [("ipe", 6, 0, 32)], [("ipe", 6, 32, 64)]],
    "shape": [[("ipe", 4, 0, 16), ("ipe", 5, 0, 16)], [("ipe", 5, 16, 32)], [("ipe", 6, 0, 32)],
              [("ipe", 6, 32, 64)]],
}


def items(plan, job):
    out = []
    for fam, n, j0, j1 in PLANS[plan][job]:
        for j in range(j0, j1):
            if fam == "ipe":
                qc, succ = AP.ipe(n, j, True)
                off, _ = AP.ipe(n, j, False)
                out.append((f"ipe{n}_{j}", qc, dict(success=succ, off_circuit=off, form="blocks")))
            else:
                qc, succ, _ = Q.textbook_logical(n, j)
                out.append((f"tqpe{n}_{j}", qc, dict(success=succ, form="pauli")))
    return out


_IDEAL = {}


def ideal(n):
    if n not in _IDEAL:
        _IDEAL[n] = AP.ipe_ideal(n)
    return _IDEAL[n]


def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None   # dry runs only, never a device
    its = items(a.plan, a.job)
    kw = dict(fence=True, footprint=True) if a.fence else {}       # psf-os after-2026-11-20 (fence: [OWNER])
    rep = FF.build(Device.load(a.devdir), its, a.out, shots=a.shots, max_seconds=70, sentinel_spec=spec, **kw)
    info = dict(part=f"{a.plan}:{a.job}", plan=a.plan, job=a.job, contents=PLANS[a.plan][a.job], shots=a.shots,
                fence=bool(a.fence),
                device=rep["device"],
                circuits=rep["circuits"], qpu_seconds_model=rep["qpu_seconds_model"], versions=Q._versions())
    json.dump(info, open(os.path.join(a.out, "part.json"), "w"), indent=1)
    print(f"{rep['device']}: plan {a.plan} job {a.job} {PLANS[a.plan][a.job]}: {rep['circuits']} circuits, "
          f"{rep['qpu_seconds_model']:.1f} s by the model")
    for fam in ("ipe", "tqpe"):
        v = [x for t, x in rep["items"].items() if t.startswith(fam)]
        if v:
            print(f"  {fam}: {len(v)} items, CZ {min(x['cz'] for x in v)}-{max(x['cz'] for x in v)}, depth "
                  f"{min(x['depth'] for x in v)}-{max(x['depth'] for x in v)}, conditionals "
                  f"{max(x['conditionals'] for x in v)}, chain {v[0]['chain']}")


def check(a):
    """As qpe_repro_night's: noiseless Aer of every arm (ff success 1, IPE off within 0.03 of exact, textbook replicate
    1, floors all zero), with this plan's items."""
    part = json.load(open(os.path.join(a.out, "part.json")))
    spec = {t: sp for t, _, sp in items(part["plan"], part["job"])}
    saved = Q._spec_by_tag
    Q._spec_by_tag = lambda _part: spec
    try:
        ns = argparse.Namespace(out=a.out, verbose=False)
        return Q.check(ns)
    finally:
        Q._spec_by_tag = saved


def dry(a):
    Q.dry(a)


def _pool(cs):
    N = sum(c["ff"]["counted"] for c in cs)
    p = sum(c["ff"]["success"] for c in cs) / N
    return p, (math.sqrt(p * (1 - p) / N) if 0 < p < 1 else 0.0), N


def accel_word(acc, se):              # [OWNER]
    if acc >= 2 * se and acc > 0:
        return "ACCELERATES"
    if acc <= -2 * se and acc < 0:
        return "SLOWS"
    return "FLAT"


def score(a):
    from psf_os import feedforward as FF
    cards = {}
    for out in a.outs:
        cards.update(FF.cards(out))
    res, lines = {}, []
    say = lambda s: (print(s), lines.append(s))
    for n in (4, 5, 6):
        ipe = [cards.get(f"ipe{n}_{j}") for j in range(2 ** n)]
        if not any(ipe):
            continue
        if not all(ipe):
            raise SystemExit(f"n = {n}: some phases missing (give every job of the plan)")
        p, sp, Np = _pool(ipe)
        C = float(ideal(n)["ceiling"])
        r = dict(ipe=p, ipe_2se=2 * sp, N=Np, ceiling=C, margin=p - C, verdict=Q.ceiling_verdict(p, sp, C))
        tb = [cards.get(f"tqpe{n}_{j}") for j in range(2 ** n)]
        if all(tb):
            q, sq, _ = _pool(tb)
            d, sd = p - q, math.sqrt(sp ** 2 + sq ** 2)
            r.update(textbook=q, textbook_2se=2 * sq, per_shot_d=d, per_shot_2se=2 * sd,
                     per_shot_word=Q.per_shot_verdict(d, sd))
        res[n] = r
        say(f"n {n}: IPE {p:.4f} (2 SE {2 * sp:.4f}, {Np} shots) against C {C:.4f} -> {r['verdict']} (margin "
            f"{p - C:+.4f})" + (f"; textbook {r['textbook']:.4f}; IPE - textbook {r['per_shot_d']:+.4f} (2 SE "
                                f"{r['per_shot_2se']:.4f}) -> {r['per_shot_word']}" if "textbook" in r else ""))
    acc = None
    if all(n in res for n in (4, 5, 6)):
        p4, p5, p6 = (res[n]["ipe"] for n in (4, 5, 6))
        s4, s5, s6 = (res[n]["ipe_2se"] / 2 for n in (4, 5, 6))
        # proposed measure (2026-11-20, after the dry runs): on the log of the share. A fixed loss per round gives
        # a fixed log drop per added bit; a fixed loss per conditional gives a log drop that grows by about that loss
        # per added bit (each bit adds one conditional more than the last: 3, 4, 5, 6). On the share itself (beside)
        # the per-conditional shape is hidden by the share's own fall (illustrative noise c: FLAT on the share,
        # ACCELERATES on its log).
        l4, l5, l6 = (math.log(x) for x in (p4, p5, p6))
        t4, t5, t6 = s4 / p4, s5 / p5, s6 / p6
        la = (l5 - l6) - (l4 - l5)
        lse = math.sqrt(t4 ** 2 + 4 * t5 ** 2 + t6 ** 2)
        a_ = (p5 - p6) - (p4 - p5)
        se = math.sqrt(s4 ** 2 + 4 * s5 ** 2 + s6 ** 2)
        acc = dict(log_drop_5=l4 - l5, log_drop_6=l5 - l6, log_acceleration=la, log_two_se=2 * lse,
                   word=accel_word(la, lse),
                   beside=dict(drop_5=p4 - p5, drop_6=p5 - p6, acceleration=a_, two_se=2 * se,
                               word=accel_word(a_, se)))
        say(f"log drop per added bit: n 4 -> 5 {l4 - l5:+.4f}, 5 -> 6 {l5 - l6:+.4f}; acceleration {la:+.4f} (2 SE "
            f"{2 * lse:.4f}) -> {acc['word']} [OWNER]")
        say(f"  beside, on the share: drop {p4 - p5:+.4f}, {p5 - p6:+.4f}; acceleration {a_:+.4f} (2 SE {2 * se:.4f})"
            f" -> {acc['beside']['word']}")
    json.dump(dict(rows={str(k): v for k, v in res.items()}, acceleration=acc),
              open(os.path.join(a.outs[0], "qpe_long_scores.json"), "w"), indent=1)
    open(os.path.join(a.outs[0], "score.txt"), "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ideal")
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    b.add_argument("--plan", choices=sorted(PLANS), required=True)
    b.add_argument("--job", type=int, required=True)
    b.add_argument("--shots", type=int, default=SHOTS)
    b.add_argument("--dry-clifford-sentinel", action="store_true")
    b.add_argument("--fence", action="store_true",
                   help="psf-os after-2026-11-20: a barrier around every wait, so that the target waits in |1> as "
                        "written (without it the compiler merges its rotations across the wait) [OWNER]")
    sub.add_parser("check").add_argument("out")
    d = sub.add_parser("dry")
    d.add_argument("out")
    d.add_argument("noise")
    d.add_argument("--seed", type=int, default=SEED)
    sc = sub.add_parser("score")
    sc.add_argument("outs", nargs="+")
    a = ap.parse_args()
    if a.cmd == "ideal":
        for n in (4, 5, 6):
            r = ideal(n)
            print(f"n {n}: IPE noiseless {float(r['ff']):.4f}, off {float(r['off']):.4f}, ceiling {float(r['ceiling']):.4f}")
        for plan, jobs in PLANS.items():
            print(f"plan {plan}: {len(jobs)} jobs: " + "; ".join(str(j) for j in jobs))
        sys.exit(0)
    r = {"build": build, "check": check, "dry": dry, "score": score}[a.cmd](a)
    sys.exit(0 if r is not False else 1)
