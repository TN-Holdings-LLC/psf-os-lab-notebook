"""How much the loop's g moves at the same stack: within a job and between jobs (draft
prereg/drafts-2026-11-20/loopvar_DRAFT.md; workplace Claude, 2026-11-20; not declared). Measures only; no rule changes.

The 2026-11-19 loop's round 1 (RULE1 = {1: P1, 2: P1, 3: P1}, every L at offset 0) rebuilt by gpu/os3_night.py's
parts on the night's device record, each L's two items (P0, the control, m = 3; P1, m = 2) TWICE in the job
(copies a and b: the same circuits on the same qubits), without the readout probe (no rule is applied). The job is
built once and copied byte for byte to V1, V2, V3, to be submitted back to back (nothing rebuilt between them).

  python gpu/loopvar_night.py build DEVDIR OUT [--dry-clifford-sentinel]     -> OUT/V1, OUT/V2, OUT/V3 (one build)
  python gpu/loopvar_night.py check OUT
  python gpu/loopvar_night.py score OUT
  python gpu/loopvar_night.py dry OUT NOISE.json [--seed S]   dry runs only: ILLUSTRATIVE noise, never fitted

Device path (home): `python -m psf_os submit OUT/V1`, then V2, then V3, back to back; `collect` each.

check (PASS / FAIL): every circuit's noiseless value against the exact one (as os3_night's check, TOL 0.03); copies a
and b of every item hold the same instructions on the same qubits (the same gate digest, the same chain); V1, V2, V3
hold byte-identical circuits.qpy and manifests but for nothing (the copies are files, not builds); each job within
60 s by the model.

score, per L (g = |P0 - exact| - |P1 - exact| as os2 / os3, SE from the shots of both items):
  g per job and copy, with its SE;
  within a job: g_a - g_b with 2 SE = 2 sqrt(SE_a^2 + SE_b^2), per job;
  between jobs: g_j = (g_a + g_b) / 2 per job (SE_j = sqrt(SE_a^2 + SE_b^2) / 2), the differences V1 - V2, V2 - V3,
    V1 - V3 with 2 SE = 2 sqrt(SE_i^2 + SE_j^2);
  across the three jobs (proposed; the owner fixes the level): the weighted mean gbar = sum w_j g_j / sum w_j
    (w_j = 1 / SE_j^2), chi2 = sum (g_j - gbar)^2 / SE_j^2 with 2 degrees of freedom, p = exp(-chi2 / 2); and the
    excess between-job variance s_b^2 = var(g_j, ddof 1) - mean(SE_j^2) (a moment estimate; negative means none seen);
  pooled over L, beside: chi2 summed over L, 6 degrees of freedom.
  Words [OWNER]: per L and job pair SAME WITHIN ERROR (|d| < 2 SE) / MOVES (|d| >= 2 SE); per L across the three
  jobs SHOT NOISE ONLY (p >= 0.05) / DRIFTS (p < 0.05). Beside: the shares P0 and P1 per job and copy.
"""
import argparse
import hashlib
import json
import math
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
for d in ("notes/rus_coherent_2026-11-17", "notes/compound_2026-11-17", "notes/os2_2026-11-18"):
    sys.path.insert(0, os.path.join(NB, d))
import os2_night as O2  # noqa: E402  (declared; read only)
import os3_night as O3  # noqa: E402  (read only: item, noiseless)

SHOTS = 4000
MAX_S = 60
STACKS = {"1": ["P1"], "2": ["P1"], "3": ["P1"]}
JOBS = ("V1", "V2", "V3")
COPIES = ("a", "b")
LEVEL = 0.05            # [OWNER]


def items():
    """[(tag, circuit, spec)] and {tag: (L, role, presc, m, copy)}."""
    out, meta = [], {}
    for c in COPIES:
        for L in O2.LS:
            out.append((f"p0{L}{c}", *O3.item("P0", L, 3)))
            meta[f"p0{L}{c}"] = (L, "p0", "P0", 3, c)
            out.append((f"x{L}{c}", *O3.item("P1", L, 2)))
            meta[f"x{L}{c}"] = (L, "x", "P1", 2, c)
    return out, meta


def _sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    if os.path.exists(a.out):
        print(f"REFUSED: {a.out} exists")
        return False
    dev = Device.load(a.devdir)
    its, meta = items()
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None   # dry runs only, never a device
    v1 = os.path.join(a.out, "V1")
    rep = FF.build(dev, its, v1, shots=SHOTS, max_seconds=MAX_S, sentinel_spec=spec)
    outq = {t: rep["items"][t]["chain"][2 * v[0] - 1] for t, v in meta.items()}
    plan = dict(device=dev.name, stacks=STACKS, meta={t: list(v) for t, v in meta.items()}, output_qubit=outq,
                chains={t: rep["items"][t]["chain"] for t in meta}, circuits=rep["circuits"],
                s_model_per_job=rep["qpu_seconds_model"], s_model_three_jobs=3 * rep["qpu_seconds_model"],
                dry_clifford_sentinel=bool(a.dry_clifford_sentinel), source="2026-11-19 loop, round 1 (P1 / P1 / P1)")
    json.dump(plan, open(os.path.join(v1, "plan.json"), "w"), indent=1)
    for v in JOBS[1:]:
        shutil.copytree(v1, os.path.join(a.out, v))          # the same files, nothing rebuilt
    json.dump(plan, open(os.path.join(a.out, "plan.json"), "w"), indent=1)
    print(f"{dev.name}: {rep['circuits']} circuits, {rep['qpu_seconds_model']:.1f} s per job by the model, "
          f"{3 * rep['qpu_seconds_model']:.1f} s for V1-V3; chains " +
          ", ".join(f"L{L} P0 {plan['chains'][f'p0{L}a']} P1 {plan['chains'][f'x{L}a']}" for L in O2.LS))
    return True


def check(a):
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    from psf_os import feedforward as FF
    plan = json.load(open(os.path.join(a.out, "plan.json")))
    bad, lines = [], []
    say = lambda s: (print(s), lines.append(s))
    v1 = os.path.join(a.out, "V1")
    m = json.load(open(os.path.join(v1, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(v1, "job", "circuits.qpy"), "rb"))
    i = 0
    for cell in m["cells"]:
        for _ in range(cell["points"]):
            c = cs[i]
            i += 1
            if cell["role"] == "sentinel":
                continue
            tag = cell["name"][3:].replace("_floor", "").replace("_off", "")
            L, role, presc, mm, _ = plan["meta"][tag]
            cc = FF.compact(c)
            n = cc.num_clbits
            cnt = AerSimulator().run(cc, shots=4000, seed_simulator=20261120).result().get_counts()
            tot = sum(cnt.values())
            allz = sum(v for k, v in cnt.items() if set(FF._bits(k, n)) == {0}) / tot
            if cell["role"] == "floor":
                ok, p = allz == 1.0, float("nan")
            else:
                p, _ = O2._p_out(n, cnt, L * mm, False)
                ok = abs(p - O3.noiseless(presc, L, mm, "ff" if cell["role"] == "user" else "off")) <= O2.TOL
            bad += [] if ok else [cell["name"]]
            lines.append(f"{cell['name']:14s} {cell['role']:6s} P {p:.3f} all zero {allz:.3f} {'ok' if ok else 'FAIL'}")
    # copies a and b: the same gates on the same qubits, arm by arm
    for t in plan["meta"]:
        if not t.endswith("a"):
            continue
        tb = t[:-1] + "b"
        same_q = plan["chains"][t] == plan["chains"][tb]
        same_g = all(_digest(v1, t, arm) == _digest(v1, tb, arm) for arm in ("", "_off", "_floor"))
        ok = same_q and same_g
        bad += [] if ok else [f"copies {t}/{tb}"]
        say(f"copies {t} / {tb}: same qubits {same_q}, same gates (ff, off, floor) {same_g}")
    shas = {v: (_sha(os.path.join(a.out, v, "job", "circuits.qpy")),
                _sha(os.path.join(a.out, v, "job", "manifest.json"))) for v in JOBS}
    same_jobs = len(set(shas.values())) == 1
    say(f"V1, V2, V3: circuits.qpy and manifest byte-identical {same_jobs} (circuits.qpy sha256 "
        f"{shas['V1'][0][:16]}...)")
    bad += [] if same_jobs else ["V1-V3 differ"]
    subs = [v for v in JOBS if os.path.exists(os.path.join(a.out, v, "job", "submission.json"))]
    s = plan["s_model_per_job"]
    say(f"{plan['circuits']} circuits, {s:.1f} s per job by the model (limit {MAX_S}), {3 * s:.1f} s for three jobs; "
        f"submitted already: {subs or 'none'}")
    bad += [] if s <= MAX_S else [f"over {MAX_S} s"]
    say("PASS" if not bad else f"FAIL {bad}")
    open(os.path.join(a.out, "check.txt"), "w").write("\n".join(lines) + "\n")
    return not bad


def _digest(v, tag, arm):
    """The gate digest of one record (psf_os.gatehash: blocks opened, RZ wrapped, parameters to 1e-10)."""
    from psf_os import gatehash as GH
    return GH.qpy_digest(os.path.join(v, "runs", f"ff_{tag}{arm}.qpy"))


def chi2_sf_even(x, k):
    """P(chi2_k >= x) for even k: exp(-x/2) sum_{i < k/2} (x/2)^i / i!."""
    h = x / 2
    return math.exp(-h) * sum(h ** i / math.factorial(i) for i in range(k // 2))


def pair_word(d, two_se):           # [OWNER]
    return "MOVES" if abs(d) >= two_se else "SAME WITHIN ERROR"


def jobs_word(p):                   # [OWNER]
    return "SHOT NOISE ONLY" if p >= LEVEL else "DRIFTS"


def _g(out, plan, L, c):
    """g, its SE and the two shares for copy c of L in one job folder."""
    import ctrl_night as CN
    g = CN._counts(out)
    ex = O2.refs()["exact"][L]
    p0, n0 = O2._p_out(*g[(f"p0{L}{c}", "ff")], L * 3, False)
    p1, n1 = O2._p_out(*g[(f"x{L}{c}", "ff")], L * 2, False)
    gain = abs(p0 - ex) - abs(p1 - ex)
    se = math.sqrt(O2._se(p0, n0) ** 2 + O2._se(p1, n1) ** 2)
    return dict(g=gain, se=se, p0=p0, p1=p1, exact=ex)


def score(a):
    plan = json.load(open(os.path.join(a.out, "plan.json")))
    rows, lines = {}, []
    say = lambda s: (print(s), lines.append(s))
    chi_all, df_all = 0.0, 0
    for L in O2.LS:
        per = {v: {c: _g(os.path.join(a.out, v), plan, L, c) for c in COPIES} for v in JOBS}
        within = {}
        for v in JOBS:
            ga, gb = per[v]["a"], per[v]["b"]
            d, t = ga["g"] - gb["g"], 2 * math.sqrt(ga["se"] ** 2 + gb["se"] ** 2)
            within[v] = dict(d=d, two_se=t, word=pair_word(d, t))
        gj = {v: (per[v]["a"]["g"] + per[v]["b"]["g"]) / 2 for v in JOBS}
        sj = {v: math.sqrt(per[v]["a"]["se"] ** 2 + per[v]["b"]["se"] ** 2) / 2 for v in JOBS}
        between = {}
        for x, y in (("V1", "V2"), ("V2", "V3"), ("V1", "V3")):
            d, t = gj[x] - gj[y], 2 * math.sqrt(sj[x] ** 2 + sj[y] ** 2)
            between[f"{x}-{y}"] = dict(d=d, two_se=t, word=pair_word(d, t))
        w = {v: 1 / sj[v] ** 2 for v in JOBS}
        gbar = sum(w[v] * gj[v] for v in JOBS) / sum(w.values())
        chi = sum((gj[v] - gbar) ** 2 / sj[v] ** 2 for v in JOBS)
        p = chi2_sf_even(chi, 2)
        mean = sum(gj.values()) / 3
        var = sum((gj[v] - mean) ** 2 for v in JOBS) / 2
        sb2 = var - sum(sj[v] ** 2 for v in JOBS) / 3
        chi_all, df_all = chi_all + chi, df_all + 2
        rows[str(L)] = dict(per_job_copy=per, within=within, g_job=gj, se_job=sj, between=between, gbar=gbar, chi2=chi,
                            df=2, p=p, word=jobs_word(p), excess_var=sb2,
                            excess_sd=math.sqrt(sb2) if sb2 > 0 else 0.0)
        say(f"L {L}: g per job " + ", ".join(f"{v} {gj[v]:+.4f} (SE {sj[v]:.4f})" for v in JOBS))
        say("   within (a - b): " + ", ".join(f"{v} {within[v]['d']:+.4f} (2 SE {within[v]['two_se']:.4f}) "
                                             f"{within[v]['word']}" for v in JOBS))
        say("   between: " + ", ".join(f"{k} {b['d']:+.4f} (2 SE {b['two_se']:.4f}) {b['word']}"
                                      for k, b in between.items()))
        say(f"   three jobs: chi2 {chi:.2f} (2 df), p {p:.3f} -> {jobs_word(p)}; excess between-job SD "
            f"{rows[str(L)]['excess_sd']:.4f} (variance {sb2:+.6f})")
        say("   beside, shares P0 / P1: " + "; ".join(f"{v}{c} {per[v][c]['p0']:.4f} / {per[v][c]['p1']:.4f}"
                                                   for v in JOBS for c in COPIES))
    p_all = chi2_sf_even(chi_all, df_all)
    say(f"beside, pooled over L: chi2 {chi_all:.2f} ({df_all} df), p {p_all:.3f}")
    say(f"words [OWNER]: pairs MOVES at |d| >= 2 SE; three jobs DRIFTS at p < {LEVEL}")
    json.dump(dict(rows=rows, pooled=dict(chi2=chi_all, df=df_all, p=p_all), level=LEVEL),
              open(os.path.join(a.out, "loopvar_scores.json"), "w"), indent=1)
    open(os.path.join(a.out, "score.txt"), "w").write("\n".join(lines) + "\n")


def dry(a):
    """Dry runs only, ILLUSTRATIVE noise written by hand, never fitted: per job V1-V3 a depolarizing p2 on every cz
    (key "p2_by_job", one value per job: unequal values are an illustrative drift between jobs), a damping gamma at
    each mid-circuit read (branch_noise; "gamma", or "gamma_by_job" one per job), a symmetric readout flip q. Each job gets its own seed."""
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error
    from psf_os import feedforward as FF
    from psf_os.ibm import _stamp
    from psf_os.sim import to_clifford_gates
    import branch_noise as BN
    noise = json.load(open(a.noise))
    for j, v in enumerate(JOBS):
        job = os.path.join(a.out, v, "job")
        if os.path.exists(os.path.join(job, "submission.json")):
            raise SystemExit(f"{v} was already run")
        man = json.load(open(os.path.join(job, "manifest.json")))
        p2 = float(noise.get("p2_by_job", [0.0] * 3)[j])
        nm = NoiseModel()
        if p2:
            nm.add_all_qubit_quantum_error(depolarizing_error(p2, 2), ["cz"])
        q = float(noise.get("q", 0.0))
        if q:
            nm.add_all_qubit_readout_error(ReadoutError([[1 - q, q], [q, 1 - q]]))
        rows = []
        for k, c in enumerate(qpy.load(open(os.path.join(job, "circuits.qpy"), "rb"))):
            cc = FF.compact(c)
            seed = a.seed + 10 ** 7 * j + 10 ** 5 * k     # strides above the shots: Aer seeds shot by shot from it
            cl = None if cc.has_control_flow_op() else to_clifford_gates(cc)
            if cl is not None and cc.num_qubits > 12:
                res = AerSimulator(method="stabilizer").run(cl, shots=man["shots"], seed_simulator=seed).result()
            else:
                nc = BN.noisy_circuit(cc, float(noise.get("gamma_by_job", [noise.get("gamma", 0.0)] * 3)[j]))
                res = AerSimulator(method="density_matrix", noise_model=nm).run(nc, shots=man["shots"],
                                                                                  seed_simulator=seed).result()
            rows.append(dict(pub=k, counts={key.replace(" ", ""): n for key, n in res.get_counts(0).items()}))
        t = _stamp()
        jid = f"local-illustrative-noise-{v}-{a.seed}"
        json.dump(dict(job_id=jid, submitted=t, local=True, backend=man["fetch"]["backend"], noise=noise, seed=a.seed,
                       simulator="aer, ILLUSTRATIVE noise (not fitted to any device)"),
                  open(os.path.join(job, "submission.json"), "w"), indent=1)
        json.dump(dict(fetched=t, job_id=jid, status="DONE (local, illustrative noise)", rows=rows),
                  open(os.path.join(job, "raw_counts.json"), "w"))
    print("dry runs written (V1, V2, V3)")


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
    d = sub.add_parser("dry")
    d.add_argument("out")
    d.add_argument("noise")
    d.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    res = {"build": build, "check": check, "score": score, "dry": dry}[a.cmd](a)
    sys.exit(0 if res is not False else 1)
