"""Phase estimation parked, stretched to n = 7 and 8 (draft for a declaration; home VS Claude, 2026-11-22 night; home
instruction "置いた形の位相推定を n = 7・8 に伸ばす試験の準備"; desk, no device).

IPE (notes/ffapps_2026-11-17 apps.ipe) at n = 6, 7, 8, built with psf-os 0.3.1's defaults stated explicitly
(park=True, park_likely=True): the target waits parked in |0>. n = 7 and 8 have 128 and 256 phases, too many for one
night, so each n is run at 16 phases chosen by a formula:
  j_k = k * a_n mod 2^n, k = 1 .. 16, a_n the odd integer nearest 2^n (sqrt(5) - 1) / 2
a_n odd keeps the number of trailing zero bits of j_k equal to k's, so the 16 phases carry the same distribution of
trailing zeros as all 2^n phases (8 odd, 4 with one zero, ...). That number decides how many CZ the compiler keeps
(more trailing zeros, fewer CZ kept), so the sample's compiled CZ matches every phase's mean (notes/qpe_n78_2026-11-22,
checked by `check`). Equal spacing from 0 would hold only phases with many trailing zeros (8 CZ at every
n); equal spacing with an odd offset only odd ones (the maximum).

Plans [OWNER]:
  a       parked only, n = 6, 7, 8 at 16 phases each (n = 6 to join the earlier nights' shape)
  a64     as a with n = 6 at every phase (64), as the night of 2026-11-21 ran it
  b       a, and unparked twins (park_skip) at 4 phases per n (k = 1 .. 4), side by side in the job: parking per n
  c       b at the shots of a formula (parking's +0.035 seen at 2 SE with about 80 % power on 4 phases)

  python gpu/qpe_long_parked_night.py table OUT.json
  python gpu/qpe_long_parked_night.py pick FETCH_IN
  python gpu/qpe_long_parked_night.py build DEVDIR OUT --plan P [--dry-clifford-sentinel]
  python gpu/qpe_long_parked_night.py check OUT
  python gpu/qpe_long_parked_night.py dry OUT NOISE.json [--seed S]       ILLUSTRATIVE noise only
  python gpu/qpe_long_parked_night.py score OUT
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
import qpe_repro_night as Q  # noqa: E402  (declared 2026-11-19; read only: check, dry, words)
import rus_fence_night as RF  # noqa: E402  (declared 2026-11-21; read only: the device rule)

NS = (6, 7, 8)
K = 16
TWINS = 4
MAX_S = 60.0
SENT = 4
SEED = 20261126
DECLARED = "0.3.1"
CEIL = {}                        # filled by ceiling(n): apps.ipe_ideal, exact
PLANS = {"a": dict(shots=1950, full6=False, twins=False), "a64": dict(shots=1950, full6=True, twins=False),
         "b": dict(shots=1950, full6=False, twins=True), "c": dict(shots=650, full6=False, twins=True)}
# the night of 2026-11-21 on marrakesh (results/qpe-parked-night-2026-11-21): parked, every phase
RECORD = {4: 0.8742, 5: 0.8391, 6: 0.8006}


def a_of(n):
    a = int(round(2 ** n * (math.sqrt(5) - 1) / 2))
    return a + (a % 2 == 0)


def phases(n, full=False):
    if full:
        return list(range(2 ** n))
    return [(k * a_of(n)) % 2 ** n for k in range(1, K + 1)]


def twin_phases(n):
    return phases(n)[:TWINS]


def ceiling(n):
    if n not in CEIL:
        CEIL[n] = float(AP.ipe_ideal(n)["ceiling"])
    return CEIL[n]


def qpu_seconds(n, shots):
    return n * 0.036 + n * shots * 0.00027 + 3.0


def plan_items(plan):
    p = PLANS[plan]
    out = []
    for n in NS:
        for j in phases(n, full=(n == 6 and p["full6"])):
            out.append((f"ipk{n}_{j}", n, j, True))
        if p["twins"]:
            for j in twin_phases(n):
                out.append((f"ipu{n}_{j}", n, j, False))
    return out


def extrapolate():
    """From the record (parked, every phase, marrakesh 2026-11-21): log drops D5, D6; (i) a constant drop (their mean),
    (ii) a drop growing by D6 - D5 per added bit. An extrapolation, not a measurement."""
    l = {n: math.log(p) for n, p in RECORD.items()}
    d5, d6 = l[4] - l[5], l[5] - l[6]
    out = {}
    for name, drops in (("constant", lambda k: (d5 + d6) / 2), ("growing", lambda k: d6 + (d6 - d5) * (k - 6))):
        P = {6: RECORD[6]}
        for n in (7, 8):
            P[n] = P[n - 1] * math.exp(-drops(n))
        out[name] = {n: round(P[n], 4) for n in (7, 8)}
    return dict(d5=round(d5, 4), d6=round(d6, 4), **out)


def size(plan):
    p = PLANS[plan]
    its = plan_items(plan)
    n_c = len(its) + SENT
    s = p["shots"]
    est = {}
    ex = extrapolate()["growing"]
    Pn = {6: RECORD[6], 7: ex[7], 8: ex[8]}
    for n in NS:
        m = sum(1 for it in its if it[1] == n and it[3])
        est[n] = dict(phases=m, two_se=round(2 * math.sqrt(Pn[n] * (1 - Pn[n]) / (m * s)), 4))
    t = {n: est[n]["two_se"] / 2 / Pn[n] for n in NS}
    acc = 2 * math.sqrt(t[6] ** 2 + 4 * t[7] ** 2 + t[8] ** 2)
    out = dict(plan=plan, shots=s, circuits=n_c, seconds=round(qpu_seconds(n_c, s), 1), per_n=est,
               log_drop_two_se=round(2 * math.sqrt(t[6] ** 2 + t[7] ** 2), 4), accel_two_se=round(acc, 4))
    if p["twins"]:
        out["twin_two_se"] = {n: round(2 * math.sqrt(2 * Pn[n] * (1 - Pn[n]) / (TWINS * s)), 4) for n in NS}
    return out


def table(a):
    rows = [size(p) for p in PLANS]
    ex = extrapolate()
    info = dict(rows=rows, ceilings={n: ceiling(n) for n in (6, 7, 8)}, extrapolation=ex,
                phases={n: phases(n) for n in NS}, a={n: a_of(n) for n in NS})
    json.dump(info, open(a.out, "w"), indent=1)
    for r in rows:
        print(f"plan {r['plan']}: {r['circuits']} circuits at {r['shots']} shots, {r['seconds']} s; P 2 SE " +
              ", ".join(f"n{n} {v['two_se']}" for n, v in r["per_n"].items()) +
              f"; acceleration 2 SE {r['accel_two_se']}" + (f"; twins 2 SE {r['twin_two_se']}" if "twin_two_se" in r else ""))
    print(f"ceilings: " + ", ".join(f"C({n}) {ceiling(n):.4f}" for n in (6, 7, 8)))
    print(f"extrapolation (record d5 {ex['d5']}, d6 {ex['d6']}): constant drop {ex['constant']}, growing drop {ex['growing']}")


def build(a):
    import psf_os
    from psf_os import feedforward as FF
    from psf_os.device import Device
    if psf_os.__version__ != "0.3.1" or not hasattr(FF, "PARK_LIKELY_DEFAULT"):
        raise SystemExit("needs psf-os 0.3.1 as released (v0.3.1)")
    dev = Device.load(a.devdir)
    if dev.name == "ibm_marrakesh":
        raise SystemExit("REFUSED: the rule runs this test off ibm_marrakesh (pick)")
    if os.path.exists(a.out):
        raise SystemExit(f"{a.out} exists (nothing is overwritten)")
    p = PLANS[a.plan]
    its = plan_items(a.plan)
    items, skip = [], []
    for tag, n, j, parked in its:
        qc, succ = AP.ipe(n, j, True)
        off, _ = AP.ipe(n, j, False)
        items.append((tag, qc, dict(success=succ, off_circuit=off, form="blocks")))
        if not parked:
            skip.append(tag)
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None   # dry runs only, never a device
    jd = os.path.join(a.out, "job0")
    os.makedirs(a.out)
    rep = FF.build(dev, items, jd, shots=p["shots"], max_seconds=MAX_S, sentinel_spec=spec,
                   ff_only=[t for t, _, _ in items], park=True, park_likely=True, park_skip=skip, footprint=True,
                   declared=DECLARED)
    json.dump(dict(part=f"qpe78:{a.plan}", shots=p["shots"], tags=[t for t, _, _ in items]),
              open(os.path.join(jd, "part.json"), "w"))
    json.dump(dict(plan=a.plan, device=dev.name, devdir=os.path.abspath(a.devdir), psf_os=psf_os.__version__,
                   shots=p["shots"], circuits=rep["circuits"],
                   qpu_seconds_model=rep["qpu_seconds_model"]), open(os.path.join(a.out, "plan.json"), "w"), indent=1)
    print(f"{rep['circuits']} circuits at {p['shots']} shots, {rep['qpu_seconds_model']:.1f} s on {dev.name}")


def _job(out):
    from qiskit import qpy
    jd = os.path.join(out, "job0")
    man = json.load(open(os.path.join(jd, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(jd, "job", "circuits.qpy"), "rb"))
    cells = {c["cell"]: c for c in man["cells"]}
    return jd, man, {cells[p["cell"]]["name"][3:]: cs[i] for i, p in enumerate(man["pubs"])
                     if cells[p["cell"]]["role"] == "user"}


def check(a):
    """qpe_repro_night.check (declared: noiseless, every ff arm all n bits right); the ceilings C(n) exact; the compiled
    CZ of the sample against every phase of each n compiled the same way (mean within 0.5); every parked item's target parked at its waits
    behind fences holding the target and the ancilla; every twin unparked; psf_os_build 0.3.1 with park and
    park_likely stated (explicit)."""
    from psf_os import feedforward as FF
    from psf_os.device import Device
    info = json.load(open(os.path.join(a.out, "plan.json")))
    jd, man, by = _job(a.out)
    lines, ok_all = [], True
    spec = {}
    for tag, n, j, _p in plan_items(info["plan"]):
        qc, succ = AP.ipe(n, j, True)
        off, _ = AP.ipe(n, j, False)
        spec[tag] = dict(success=succ, off_circuit=off, form="blocks")
    saved = Q._spec_by_tag
    Q._spec_by_tag = lambda _p: spec
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            ok = Q.check(argparse.Namespace(out=jd, verbose=False))
    finally:
        Q._spec_by_tag = saved
    lines.append(f"qpe_repro_night.check: {buf.getvalue().strip().splitlines()[-1]}")
    ok_all &= bool(ok)
    b = man.get("psf_os_build", {})
    okb = b.get("version") == "0.3.1" and b.get("park") is True and b.get("park_set") == "explicit" and \
        b.get("park_likely") is True and "park_likely_set" not in b and b.get("declared") == DECLARED
    lines.append(f"psf_os_build {b} -> {'ok (park and park_likely stated)' if okb else 'NOT AS DECLARED'}")
    ok_all &= okb
    lines.append("ceilings (exact): " + ", ".join(f"C({n}) {ceiling(n):.4f}" for n in NS))
    dev = Device.load(info["devdir"])
    comp = FF.Compiler(dev)
    for n in NS:
        tags = [t for t in by if t.startswith(f"ipk{n}_")]
        cz_s = [FF.cz_count(by[t]) for t in tags]
        cz_all = []
        for j in range(2 ** n):                    # every phase, compiled as built (parked), on the same record
            qc, _s = AP.ipe(n, j, True)
            low = FF.lower(qc)
            from psf_os.footprint import park_waits, park_likely
            low = park_likely(park_waits(low)[0])[0]
            ch = FF.place(dev, low.num_qubits)["chain"]
            cz_all.append(FF.cz_count(comp.run(FF.on_device(low, ch, dev.num_qubits))))
        ok_cz = abs(sum(cz_s) / len(cz_s) - sum(cz_all) / len(cz_all)) <= 0.5
        lines.append(f"n {n}: {len(tags)} parked phases, compiled CZ mean {sum(cz_s) / len(cz_s):.2f} against every "
                     f"phase {sum(cz_all) / len(cz_all):.2f} (compiled the same way) -> {'ok' if ok_cz else 'BIASED'}")
        ok_all &= ok_cz
    bad = []
    for t, c in by.items():
        rec = json.load(open(os.path.join(jd, "runs", f"ff_{t}.json")))
        pk = rec.get("park", {})
        if t.startswith("ipk"):
            parked = pk.get("arms", {}).get("ff", {}).get("parked", [])
            tgt = rec["chain"][1]
            anc = rec["chain"][0]
            bars = [{c.find_bit(q).index for q in x.qubits} for x in c.data if x.operation.name == "barrier"]
            if not parked or not all(any({tgt, anc} <= s for s in bars) for _ in parked):
                bad.append(t)
        elif pk != {"park": False, "skipped": "park_skip"}:
            bad.append(t)
    lines.append(f"park records: {'every parked item fenced with its target and ancilla; every twin unparked' if not bad else 'NOT AS MEANT ' + str(bad[:5])}")
    ok_all &= not bad
    lines.append("PASS" if ok_all else "FAIL")
    print("\n".join(lines))
    open(os.path.join(a.out, "check.txt"), "w").write("\n".join(lines) + "\n")
    return ok_all


def _tz(j, n):
    if j == 0:
        return n
    t = 0
    while j % 2 == 0:
        j //= 2
        t += 1
    return t


def dry(a):
    with contextlib.redirect_stdout(io.StringIO()):
        Q.dry(argparse.Namespace(out=os.path.join(a.out, "job0"), noise=a.noise, seed=a.seed))


def word_pair(d, se):              # the words of C [OWNER]
    if d >= 2 * se and d > 0:
        return "KEEPS MORE"
    if d <= -2 * se and d < 0:
        return "KEEPS LESS"
    return "SAME WITHIN ERROR"


def reading(ceil8, shape):         # [OWNER]: every pair on one row (2 x 3)
    if shape == "SLOWS":
        return "the parked loss per added bit shrinks: not read for the mechanism"
    if ceil8 == "BEYOND THE CEILING":
        return ("parked IPE beyond its ceiling to n = 8, the loss per added bit per round" if shape == "FLAT" else
                "parked IPE beyond its ceiling to n = 8, the loss per added bit growing (a cost per conditional)")
    return ("the ceiling is not passed at n = 8 with a loss per round: the range ends before n = 8" if shape == "FLAT"
            else "the ceiling is not passed at n = 8 and the loss per added bit grows")


def score(a):
    from psf_os import feedforward as FF
    from psf_os import job as J
    jd = os.path.join(a.out, "job0")
    read = J.read(os.path.join(jd, "job"), os.path.join(jd, "runs"))
    cards = {}
    for _n, (rec, cc) in read.items():
        if rec.get("psfos_job", {}).get("kind", "").startswith(FF.KIND) and rec.get("ff_arm") == "ff":
            cards[rec["tag"]] = FF.success_share(cc[("f", "z")], rec["clbits"],
                                                 {int(b): v for b, v in rec["success"].items()})
    lines, res = [], {}
    say = lambda s: (print(s), lines.append(s))

    def pool(tags):
        ok = sum(cards[t]["success"] for t in tags)
        N = sum(cards[t]["counted"] for t in tags)
        p = ok / N
        return p, math.sqrt(p * (1 - p) / N), N
    for n in NS:
        tags = [t for t in cards if t.startswith(f"ipk{n}_")]
        p, se, N = pool(tags)
        C = ceiling(n)
        r = dict(p=p, two_se=2 * se, N=N, ceiling=C, verdict=Q.ceiling_verdict(p, se, C))
        tw = [t for t in cards if t.startswith(f"ipu{n}_")]
        if tw:
            pk, sk, _ = pool([t.replace("ipu", "ipk") for t in tw])
            pu, su, _ = pool(tw)
            d, sd = pk - pu, math.sqrt(sk ** 2 + su ** 2)
            r.update(twin_parked=pk, twin_unparked=pu, d=d, d_two_se=2 * sd, park_word=word_pair(d, sd))
        res[n] = r
        say(f"n {n}: parked {p:.4f} (2 SE {2 * se:.4f}, {N} shots) against C {C:.4f} -> {r['verdict']} (margin "
            f"{p - C:+.4f})" + (f"; on {len(tw)} twin phases parked - unparked {r['d']:+.4f} (2 SE {r['d_two_se']:.4f}) "
                                f"{r['park_word']}" if tw else ""))
    l = {n: math.log(res[n]["p"]) for n in NS}
    t = {n: res[n]["two_se"] / 2 / res[n]["p"] for n in NS}
    acc = (l[7] - l[8]) - (l[6] - l[7])
    se = math.sqrt(t[6] ** 2 + 4 * t[7] ** 2 + t[8] ** 2)
    shape = "ACCELERATES" if acc >= 2 * se and acc > 0 else "SLOWS" if acc <= -2 * se and acc < 0 else "FLAT"
    row = reading(res[8]["verdict"], shape)
    say(f"log drops {l[6] - l[7]:+.4f} (6 -> 7), {l[7] - l[8]:+.4f} (7 -> 8); acceleration {acc:+.4f} (2 SE {2 * se:.4f}) "
        f"-> {shape}")
    say(f"reading: {row}")
    json.dump(dict(per_n={str(k): v for k, v in res.items()}, shape=dict(acc=acc, two_se=2 * se, word=shape),
                   reading=row), open(os.path.join(a.out, "qpe78_scores.json"), "w"), indent=1)
    open(os.path.join(a.out, "score.txt"), "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("table").add_argument("out")
    sub.add_parser("pick").add_argument("fetch_in")
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    b.add_argument("--plan", required=True, choices=sorted(PLANS))
    b.add_argument("--dry-clifford-sentinel", action="store_true")
    sub.add_parser("check").add_argument("out")
    d = sub.add_parser("dry")
    d.add_argument("out")
    d.add_argument("noise")
    d.add_argument("--seed", type=int, default=SEED)
    sub.add_parser("score").add_argument("out")
    a = ap.parse_args()
    if a.cmd == "pick":
        print(RF.pick_device(a.fetch_in))
        sys.exit(0)
    r = {"table": table, "build": build, "check": check, "dry": dry, "score": score}[a.cmd](a)
    sys.exit(0 if r is not False else 1)
