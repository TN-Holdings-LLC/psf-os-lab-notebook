"""Phase estimation at n = 4, 5, 6 parked (draft for a declaration; home VS Claude, 2026-11-21; home instruction
"psf-os 0.3.0 の追加", part C; desk, no device). Does parking the waiting target in |0> keep more at every n, and does
the loss per added bit stay per round once the target is parked?

The weekend's B (results/weekend-shared-night-2026-11-21) ran IPE n = 4, 5, 6 unparked (as 2026-11-19) and read FLAT;
its C ran n = 4 parked (pk) beside unparked (pl) in one job: +0.0387 (2 SE 0.0045). This tool builds B's circuits
with psf-os 0.3.0 (release-0.3.0): `ipe{n}_{j}` parked (the default, `park=True` said), `ipu{n}_{j}` the same circuit
unparked (`park_skip`), every item its ff arm only (as the weekend), one sentinel per job. The declared tools
(qpe_long_night, ipe_park_night, qpe_repro_night) are read only.

Plans [OWNER] (the comparison inside one job; a comparison across nights is beside only):
  parked   every phase parked (shape and ceiling); the difference from the weekend's unparked B is across nights
  both     every phase parked and unparked, side by side per phase in one job (d_n = parked - unparked per n)
  subset   every phase parked; unparked at 8 phases per n (evenly spaced), each beside its parked twin in one job;
           d_n read on those 8 phases
  formula  both forms at every phase, the shot count from the formula: d = 0.03 seen at 2 SE with about 80 % power
           (z = 2 + 0.84) on the n with the fewest phases (n = 4)

  python gpu/qpe_parked_night.py table OUT.json
  python gpu/qpe_parked_night.py build DEVDIR OUT --plan P [--shots S] [--dry-clifford-sentinel]
  python gpu/qpe_parked_night.py check OUT
  python gpu/qpe_parked_night.py dry OUT NOISE.json [--seed S]       ILLUSTRATIVE noise only
  python gpu/qpe_parked_night.py score OUT
"""
import argparse
import contextlib
import io
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

NS = (4, 5, 6)
SHOTS = 1950
MAX_S = 60.0
SENT = 4
SEED = 20261123
# the weekend's unparked IPE shares (results/weekend-shared-night-2026-11-21, B), for the precision estimates only
WEEKEND = {4: 0.8957, 5: 0.8715, 6: 0.8451}
D_MIN = 0.03
Z = 2 + 0.84


def qpu_seconds(n, shots):
    return n * 0.036 + n * shots * 0.00027 + 3.0


def subset(n):
    step = 2 ** n // 8
    return list(range(0, 2 ** n, step))


def formula_shots():
    """Shots per circuit so that d = D_MIN is seen at 2 SE with about 80 % power at n = 4 (16 phases): the total
    shots per arm N = Z^2 (p1 q1 + p2 q2) / d^2, p2 the weekend's unparked share, p1 = p2 + d; rounded up to 50."""
    p2 = WEEKEND[4]
    p1 = min(p2 + D_MIN, 0.999)
    N = Z ** 2 * (p1 * (1 - p1) + p2 * (1 - p2)) / D_MIN ** 2
    return int(math.ceil(N / 16 / 50.0) * 50)


def plan_items(plan):
    """[(block, tag, n, j, parked)] in packing order (a block, one phase of one n, never split across jobs)."""
    out = []
    for n in NS:
        sub_ = set(subset(n))
        for j in range(2 ** n):
            blk = f"{n}:{j}"
            out.append((blk, f"ipe{n}_{j}", n, j, True))
            if plan in ("both", "formula") or (plan == "subset" and j in sub_):
                out.append((blk, f"ipu{n}_{j}", n, j, False))
    return out


def shots_of(plan, shots=None):
    return shots or (formula_shots() if plan == "formula" else SHOTS)


def pack(items, shots):
    blocks = []
    for it in items:
        if blocks and blocks[-1][-1][0] == it[0]:
            blocks[-1].append(it)
        else:
            blocks.append([it])

    def fill(cap):
        jobs, cur = [], []
        for b in blocks:
            if cur and (len(cur) + len(b) > cap or qpu_seconds(len(cur) + len(b) + SENT, shots) > MAX_S):
                jobs.append(cur)
                cur = []
            cur += b
        if cur:
            jobs.append(cur)
        return jobs
    k = len(fill(10 ** 9))
    cap = math.ceil(len(items) / k)
    while len(fill(cap)) > k:
        cap += 1
    return fill(cap)


def size(plan, shots=None):
    s = shots_of(plan, shots)
    jobs = pack(plan_items(plan), s)
    per = [round(qpu_seconds(len(j) + SENT, s), 1) for j in jobs]
    items = plan_items(plan)
    # precision estimates (the weekend's unparked shares; parked +0.03)
    est = {}
    for n in NS:
        ph = 2 ** n
        nu = sum(1 for it in items if it[2] == n and not it[4])
        pu, pk = WEEKEND[n], min(WEEKEND[n] + D_MIN, 0.999)
        Nk, Nu = ph * s, nu * s
        se_k = math.sqrt(pk * (1 - pk) / Nk)
        d_se = math.sqrt(pk * (1 - pk) / (nu * s) + pu * (1 - pu) / Nu) if nu else None
        est[n] = dict(parked_2se=round(2 * se_k, 4), diff_2se=round(2 * d_se, 4) if d_se else None,
                      unparked_phases=nu)
    t = {n: est[n]["parked_2se"] / 2 / min(WEEKEND[n] + D_MIN, 0.999) for n in NS}
    acc_2se = 2 * math.sqrt(t[4] ** 2 + 4 * t[5] ** 2 + t[6] ** 2)
    return dict(plan=plan, shots=s, circuits=sum(len(j) for j in jobs) + SENT * len(jobs), jobs=len(jobs),
                seconds=round(sum(per), 1), per_job=per, per_n=est, shape_acc_2se=round(acc_2se, 4),
                unparked_items=sum(1 for it in items if not it[4]))


def table(a):
    rows = [size(p) for p in ("parked", "both", "subset", "formula")]
    rows.append(dict(size("subset", formula_shots()), plan="subset at the formula's shots"))
    a1, f1 = size("parked"), size("formula")
    rows.append(dict(plan="parked (1950) + formula's job (both forms)", shots=f"{a1['shots']} / {f1['shots']}",
                     circuits=a1["circuits"] + f1["circuits"], jobs=a1["jobs"] + f1["jobs"],
                     seconds=round(a1["seconds"] + f1["seconds"], 1), per_job=a1["per_job"] + f1["per_job"],
                     per_n={n: dict(parked_2se=a1["per_n"][n]["parked_2se"], diff_2se=f1["per_n"][n]["diff_2se"],
                                    unparked_phases=f1["per_n"][n]["unparked_phases"]) for n in NS},
                     shape_acc_2se=a1["shape_acc_2se"], unparked_items=f1["unparked_items"]))
    json.dump(dict(rows=rows, formula_shots=formula_shots(), d_min=D_MIN, z=Z, weekend_unparked=WEEKEND),
              open(a.out, "w"), indent=1)
    for r in rows:
        print(f"{r['plan']:44s} shots {str(r['shots']):>10s}  {r['circuits']:4d} circuits  {r['jobs']} jobs  "
              f"{r['seconds']:6.1f} s  d_n 2SE " + ", ".join(f"n{n} {r['per_n'][n]['diff_2se']}" for n in NS)
              + f"  parked shape acc 2SE {r['shape_acc_2se']}")


def items_of(plan):
    out = {}
    for _blk, tag, n, j, parked in plan_items(plan):
        qc, succ = AP.ipe(n, j, True)
        off, _ = AP.ipe(n, j, False)
        out[tag] = (qc, dict(success=succ, off_circuit=off, form="blocks"))
    return out


def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    dev = Device.load(a.devdir)
    s = shots_of(a.plan, a.shots)
    its = items_of(a.plan)
    jobs = pack(plan_items(a.plan), s)
    if os.path.exists(a.out):
        raise SystemExit(f"{a.out} exists (nothing is overwritten)")
    os.makedirs(a.out)
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None   # dry runs only, never a device
    info = dict(plan=a.plan, shots=s, device=dev.name, jobs=[])
    for k, job in enumerate(jobs):
        jd = os.path.join(a.out, f"job{k}")
        tags = [it[1] for it in job]
        skip = [it[1] for it in job if not it[4]]
        rep = FF.build(dev, [(t, *its[t]) for t in tags], jd, shots=s, max_seconds=MAX_S, sentinel_spec=spec,
                       ff_only=tags, park=True, park_skip=skip, footprint=True)
        json.dump(dict(part=f"parked:{a.plan}:{k}", shots=s, tags=tags), open(os.path.join(jd, "part.json"), "w"))
        info["jobs"].append(dict(folder=f"job{k}", circuits=rep["circuits"], qpu_seconds_model=rep["qpu_seconds_model"],
                                 parked=len(tags) - len(skip), unparked=len(skip)))
        print(f"job{k}: {rep['circuits']} circuits, {rep['qpu_seconds_model']:.1f} s; parked {len(tags) - len(skip)}, "
              f"unparked {len(skip)}")
    info["qpu_seconds_model"] = round(sum(j["qpu_seconds_model"] for j in info["jobs"]), 1)
    json.dump(info, open(os.path.join(a.out, "plan.json"), "w"), indent=1)
    print(f"{len(jobs)} jobs, {info['qpu_seconds_model']:.1f} s by the model")


def check(a):
    """qpe_repro_night.check (declared) on every job with this plan's items; and per item, the park record as meant
    (ipe parked at every wait, ipu skipped)."""
    info = json.load(open(os.path.join(a.out, "plan.json")))
    spec = {t: sp for t, (_qc, sp) in items_of(info["plan"]).items()}
    ok_all, lines = True, []
    for j in info["jobs"]:
        jd = os.path.join(a.out, j["folder"])
        saved = Q._spec_by_tag
        Q._spec_by_tag = lambda _p: spec
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                ok = Q.check(argparse.Namespace(out=jd, verbose=False))
        finally:
            Q._spec_by_tag = saved
        bad = []
        for f in os.listdir(os.path.join(jd, "runs")):
            if not (f.startswith("ff_ip") and f.endswith(".json")):
                continue
            r = json.load(open(os.path.join(jd, "runs", f)))
            pk = r.get("park", {})
            if r["tag"].startswith("ipe"):
                arms = pk.get("arms", {}).get("ff", {})
                if not arms.get("parked") or arms.get("parked_waits") != arms.get("waits"):
                    bad.append(r["tag"])
            elif pk != {"park": False, "skipped": "park_skip"}:
                bad.append(r["tag"])
        lines.append(f"{j['folder']}: qpe_repro_night.check: {buf.getvalue().strip().splitlines()[-1]}; park records "
                     f"{'as meant' if not bad else 'NOT as meant ' + str(bad[:5])}")
        ok_all &= bool(ok) and not bad
    lines.append("PASS" if ok_all else "FAIL")
    print("\n".join(lines))
    open(os.path.join(a.out, "check.txt"), "w").write("\n".join(lines) + "\n")
    return ok_all


def dry(a):
    info = json.load(open(os.path.join(a.out, "plan.json")))
    for k, j in enumerate(info["jobs"]):
        with contextlib.redirect_stdout(io.StringIO()):
            Q.dry(argparse.Namespace(out=os.path.join(a.out, j["folder"]), noise=a.noise, seed=a.seed + 5_000_000 * k))


def _cards(jd):
    from psf_os import feedforward as FF
    from psf_os import job as J
    read = J.read(os.path.join(jd, "job"), os.path.join(jd, "runs"))
    out = {}
    for _name, (rec, cc) in read.items():
        if rec.get("psfos_job", {}).get("kind", "").startswith(FF.KIND) and rec.get("ff_arm") == "ff":
            succ = {int(b): v for b, v in rec["success"].items()}
            out[rec["tag"]] = FF.success_share(cc[("f", "z")], rec["clbits"], succ)
    return out


def pair_word(d, se):              # [OWNER] (the words of C)
    if d >= 2 * se and d > 0:
        return "KEEPS MORE"
    if d <= -2 * se and d < 0:
        return "KEEPS LESS"
    return "SAME WITHIN ERROR"


def score(a):
    info = json.load(open(os.path.join(a.out, "plan.json")))
    cards, job_of = {}, {}
    for j in info["jobs"]:
        c = _cards(os.path.join(a.out, j["folder"]))
        cards.update(c)
        job_of.update({t: j["folder"] for t in c})
    lines, res = [], {}
    say = lambda s: (print(s), lines.append(s))

    def pool(tags):
        ok = sum(cards[t]["success"] for t in tags)
        N = sum(cards[t]["counted"] for t in tags)
        p = ok / N
        return p, math.sqrt(p * (1 - p) / N), N
    for n in NS:
        C = float(AP.ipe_ideal(n)["ceiling"])
        p, se, N = pool([f"ipe{n}_{j}" for j in range(2 ** n)])
        r = dict(parked=p, parked_2se=2 * se, N=N, verdict=Q.ceiling_verdict(p, se, C))
        both = [j for j in range(2 ** n) if f"ipu{n}_{j}" in cards]
        assert all(job_of[f"ipu{n}_{j}"] == job_of[f"ipe{n}_{j}"] for j in both), "a pair split across jobs"
        if both:
            pk, sk, _ = pool([f"ipe{n}_{j}" for j in both])
            pu, su, _ = pool([f"ipu{n}_{j}" for j in both])
            d, sd = pk - pu, math.sqrt(sk ** 2 + su ** 2)
            r.update(phases_paired=len(both), parked_on_pairs=pk, unparked_on_pairs=pu, d=d, d_2se=2 * sd,
                     word=pair_word(d, sd))
        res[n] = r
        say(f"n {n}: parked {p:.4f} (2 SE {2 * se:.4f}) -> {r['verdict']}"
            + (f"; on {len(both)} paired phases parked {r['parked_on_pairs']:.4f} - unparked "
               f"{r['unparked_on_pairs']:.4f} = {r['d']:+.4f} (2 SE {r['d_2se']:.4f}) -> {r['word']}" if both else ""))
    l = {n: math.log(res[n]["parked"]) for n in NS}
    t = {n: res[n]["parked_2se"] / 2 / res[n]["parked"] for n in NS}
    acc = (l[5] - l[6]) - (l[4] - l[5])
    se = math.sqrt(t[4] ** 2 + 4 * t[5] ** 2 + t[6] ** 2)
    word = "ACCELERATES" if acc >= 2 * se and acc > 0 else "SLOWS" if acc <= -2 * se and acc < 0 else "FLAT"
    say(f"parked shape: log drops {l[4] - l[5]:+.4f}, {l[5] - l[6]:+.4f}; acceleration {acc:+.4f} (2 SE {2 * se:.4f}) "
        f"-> {word}")
    json.dump(dict(per_n={str(k): v for k, v in res.items()}, shape=dict(acc=acc, two_se=2 * se, word=word)),
              open(os.path.join(a.out, "parked_scores.json"), "w"), indent=1)
    open(os.path.join(a.out, "score.txt"), "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("table").add_argument("out")
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    b.add_argument("--plan", required=True, choices=("parked", "both", "subset", "formula"))
    b.add_argument("--shots", type=int)
    b.add_argument("--dry-clifford-sentinel", action="store_true")
    sub.add_parser("check").add_argument("out")
    d = sub.add_parser("dry")
    d.add_argument("out")
    d.add_argument("noise")
    d.add_argument("--seed", type=int, default=SEED)
    sub.add_parser("score").add_argument("out")
    a = ap.parse_args()
    r = {"table": table, "build": build, "check": check, "dry": dry, "score": score}[a.cmd](a)
    sys.exit(0 if r is not False else 1)
