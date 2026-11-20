"""Where should a qubit wait? IPE sent three ways (draft for a declaration; workplace Claude, 2026-11-20, after the
workplace VS's finding that the compiled IPE target waits in a superposition; not declared).

The same iterative phase estimation (notes/ffapps_2026-11-17 apps.ipe, as 2026-11-17 / 2026-11-19) in three forms,
the same action, the same CZ:
  pl  plain, as 2026-11-19: compiled, the target waits in a superposition (one carrier per wait, half excited)
  fe  fenced (psf_os.footprint.fence_waits): a barrier on every qubit around each wait; the target waits in |1>
      (no carrier, fully excited)
  pk  parked (notes/park_2026-11-20/park.py): fenced, with X on the target before the wait and after it; the
      target waits in |0> (no carrier, nothing excited)
Every form's off arm is the plain off arm (the ceiling C(n) is the same). n = 4 by default, every phase, 1950 shots.
Two jobs (phases 0-7 and 8-15, every form in both): 24 items, 76 circuits, 45.8 s by the model each.

  python gpu/ipe_park_night.py build DEVDIR OUT --job 0|1 [--n 4] [--dry-clifford-sentinel]
  python gpu/ipe_park_night.py check OUT                 noiseless Aer (as qpe_repro_night's check)
  python gpu/ipe_park_night.py dry OUT NOISE.json [--seed S]       ILLUSTRATIVE noise only (qpe_repro_night's dry)
  python gpu/ipe_park_night.py score OUT0 OUT1
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
for d in ("notes/ffapps_2026-11-17", "notes/rus_coherent_2026-11-17", "notes/os2_2026-11-18", "notes/park_2026-11-20",
          "notes/ipe_long_2026-11-20"):
    sys.path.insert(0, os.path.join(NB, d))
import apps as AP  # noqa: E402
import qpe_repro_night as Q  # noqa: E402  (declared 2026-11-19; read only)

SHOTS = 1950
SEED = 20261122
FORMS = ("pl", "fe", "pk")
COMPARISONS = {"park": ("pk", "pl"),       # waiting in |0> against waiting as 2026-11-19 sent it
               "fence": ("fe", "pl"),      # waiting in |1> against the same
               "park_vs_fence": ("pk", "fe")}   # |0> against |1>, both without a carrier (beside)


def form(f, qc):
    from psf_os.footprint import fence_waits
    import park as PK
    return {"pl": qc, "fe": fence_waits(qc), "pk": PK.park(qc)}[f]


def items(n, job):
    half = 2 ** n // 2
    out = []
    for j in range(job * half, (job + 1) * half):
        qc, succ = AP.ipe(n, j, True)
        off, _ = AP.ipe(n, j, False)
        for f in FORMS:
            out.append((f"{f}{n}_{j}", form(f, qc), dict(success=succ, off_circuit=off, form="blocks")))
    return out


def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None   # dry runs only, never a device
    rep = FF.build(Device.load(a.devdir), items(a.n, a.job), a.out, shots=a.shots, max_seconds=60,
                   sentinel_spec=spec, footprint=True)
    info = dict(part=f"park:{a.n}:{a.job}", n=a.n, job=a.job, shots=a.shots, device=rep["device"],
                circuits=rep["circuits"], qpu_seconds_model=rep["qpu_seconds_model"], versions=Q._versions())
    json.dump(info, open(os.path.join(a.out, "part.json"), "w"), indent=1)
    print(f"{rep['device']}: n {a.n} job {a.job}: {rep['circuits']} circuits, {rep['qpu_seconds_model']:.1f} s by the "
          "model")
    for f in FORMS:
        v = [x for t, x in rep["items"].items() if t.startswith(f)]
        print(f"  {f}: {len(v)} items, CZ {min(x['cz'] for x in v)}-{max(x['cz'] for x in v)}, depth "
              f"{min(x['depth'] for x in v)}-{max(x['depth'] for x in v)}, footprint as sent max "
              f"{max(x['footprint_max'] for x in v)}, chain {v[0]['chain']}")


def check(a):
    part = json.load(open(os.path.join(a.out, "part.json")))
    spec = {t: sp for t, _, sp in items(part["n"], part["job"])}
    saved = Q._spec_by_tag
    Q._spec_by_tag = lambda _part: spec
    try:
        return Q.check(argparse.Namespace(out=a.out, verbose=False))
    finally:
        Q._spec_by_tag = saved


def dry(a):
    Q.dry(a)


def _pool(cs):
    N = sum(c["ff"]["counted"] for c in cs)
    p = sum(c["ff"]["success"] for c in cs) / N
    return p, (math.sqrt(p * (1 - p) / N) if 0 < p < 1 else 0.0), N


def pair_word(d, se):              # [OWNER]
    if d >= 2 * se and d > 0:
        return "KEEPS MORE"
    if d <= -2 * se and d < 0:
        return "KEEPS LESS"
    return "SAME WITHIN ERROR"


def reading(park, fence):          # [OWNER]: every pair of words on one row (9 outcomes)
    more, same, less = "KEEPS MORE", "SAME WITHIN ERROR", "KEEPS LESS"
    if park == more and fence == less:
        return "decay while waiting: |1> loses, |0> keeps"
    if park == more and fence == more:
        return "dephasing while waiting: any basis state keeps, |0> at least as well"
    if park == more and fence == same:
        return "waiting in |0> keeps more; |1> neither more nor less than the superposition"
    if park == same and fence == same:
        return "where the target waits is not seen at this night's shot noise"
    return "against the expectation (|0> keeps no more, or keeps less): not read for the mechanism"


def score(a):
    from psf_os import feedforward as FF
    cards = {}
    for out in a.outs:
        cards.update(FF.cards(out))
    ns = sorted({int(t[2:].split("_")[0]) for t in cards if t[:2] in FORMS})
    lines = []
    say = lambda s: (print(s), lines.append(s))
    res = {}
    for n in ns:
        C = float(AP.ipe_ideal(n)["ceiling"])
        pr = {}
        for f in FORMS:
            cs = [cards.get(f"{f}{n}_{j}") for j in range(2 ** n)]
            if not all(cs):
                raise SystemExit(f"n = {n}, form {f}: some phases missing (give both jobs)")
            p, s, N = _pool(cs)
            pr[f] = (p, s)
            say(f"n {n} {f}: {p:.4f} (2 SE {2 * s:.4f}, {N} shots) against C {C:.4f} -> {Q.ceiling_verdict(p, s, C)}")
        words = {}
        for name, (x, y) in COMPARISONS.items():
            d = pr[x][0] - pr[y][0]
            se = math.sqrt(pr[x][1] ** 2 + pr[y][1] ** 2)
            words[name] = pair_word(d, se)
            say(f"  {name} ({x} - {y}): {d:+.4f} (2 SE {2 * se:.4f}) -> {words[name]}")
        say(f"  reading [OWNER]: {reading(words['park'], words['fence'])}")
        res[n] = dict(shares={f: pr[f][0] for f in FORMS}, words=words, reading=reading(words["park"], words["fence"]))
    json.dump(res, open(os.path.join(a.outs[0], "park_scores.json"), "w"), indent=1)
    open(os.path.join(a.outs[0], "score.txt"), "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    b.add_argument("--job", type=int, choices=(0, 1), required=True)
    b.add_argument("--n", type=int, default=4)
    b.add_argument("--shots", type=int, default=SHOTS)
    b.add_argument("--dry-clifford-sentinel", action="store_true")
    sub.add_parser("check").add_argument("out")
    d = sub.add_parser("dry")
    d.add_argument("out")
    d.add_argument("noise")
    d.add_argument("--seed", type=int, default=SEED)
    sc = sub.add_parser("score")
    sc.add_argument("outs", nargs="+")
    a = ap.parse_args()
    r = {"build": build, "check": check, "dry": dry, "score": score}[a.cmd](a)
    sys.exit(0 if r is not False else 1)
