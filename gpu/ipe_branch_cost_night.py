"""The cost of the branch in IPE, cut in two (draft for a declaration; home VS Claude, 2026-11-22 night; home instruction
"IPE の解剖と条件分岐のコストの試験の準備", part B; desk, no device).

Three forms of IPE (apps.ipe's rounds: round 1 reads clbit n-1, round n clbit 0) on the same phases and the same
qubits, side by side in one job:
  F    the form as it is: every phase correction from an earlier bit inside a conditional (if_test on that bit),
       built with psf-os 0.3.1's defaults stated (park=True, park_likely=True);
  S    fixed corrections: the phase j is known, so the correction each earlier bit calls for (when the bit is right)
       is applied without a condition; the run of corrections sits between two full fences, with the target's
       parking pair (X before, X after) where F's parking puts it, so S has F's gates without F's conditional wait;
  SD   S with a delay, inside the same fences, of L for every conditional F holds at that place: L * (round - 1) at
       round r, on every qubit of the circuit (the whole device waits on a conditional).
  R    (beside) F with a spectator qubit, the neighbour of the ancilla, read at every read of the ancilla (into
       clbits n .. 2n - 1, outside the scored bits): what reading a neighbour costs. Never one of the three.
Every form's reset of the ancilla (if_test on the bit just read: X) is kept as in F: the forms differ in the phase
feedback only. Every item has three qubits (spectator, ancilla, target on a line), the spectator idle in F, S and SD,
so that the twin R sits on the same qubits.

  P(SD) - P(F)   what the feedback costs beyond its wait (the branch itself)
  P(S) - P(SD)   what the wait costs
P is the share of shots with all n bits right, pooled over the phases of each n.

L, the length of one conditional's wait, is [OWNER], a whole number of the device's dt: psf-os 0.3.1 has no time per
operation (its model is per job, circuit and shot) and the device records hold neither durations nor dt, so the
compiled F fixes how many waits stand at each place (the conditionals of the round's run, counted in the compiled
circuit by check) and L fixes their length. Delays are written in dt because qiskit 2.5.2's qpy (the job's
circuits.qpy) keeps only dt: a delay in us comes back as the same number of dt, one in s is refused. Plan d runs SD at
L and at 2 L, so that the wait's cost can be read per unit of delay whatever L is.

  python gpu/ipe_branch_cost_night.py table OUT.json
  python gpu/ipe_branch_cost_night.py pick FETCH_IN
  python gpu/ipe_branch_cost_night.py build DEVDIR OUT --plan P [--L-us L] [--dry-clifford-sentinel]
  python gpu/ipe_branch_cost_night.py check OUT
  python gpu/ipe_branch_cost_night.py dry OUT NOISE.json [--seed S]       ILLUSTRATIVE noise only
  python gpu/ipe_branch_cost_night.py score OUT
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
import apps as AP  # noqa: E402  (read only: _cp)
import rus_fence_night as RF  # noqa: E402  (declared 2026-11-21; read only: the device rule)

DECLARED = "0.3.1"
MAX_S = 60.0
SENT = 4
SEED = 20261123
L_DT = 4500                       # [OWNER] one conditional's wait, in the device's dt (a placeholder, not a measurement)
R_TWINS = 4
# the record of 2026-11-22 on ibm_fez (results/qpe-n78-night-2026-11-22), parked, 16 phases: for the sizes only
RECORD = {6: 0.5785, 7: 0.5097, 8: 0.4236}
PLANS = {
    "a": dict(ns=(6, 8), K=8, forms=("F", "S", "SD"), Lx=(1,), R=False, shots=3900),
    "b": dict(ns=(6, 8), K=8, forms=("F", "S", "SD"), Lx=(1,), R=True, shots=3350),
    "c": dict(ns=(6, 8), K=16, forms=("F", "S", "SD"), Lx=(1,), R=False, shots=1950),
    "d": dict(ns=(6, 8), K=8, forms=("F", "S", "SD"), Lx=(1, 2), R=False, shots=2950),
}
S_Q, A_Q, T_Q = 0, 1, 2           # spectator, ancilla, target (a line: the spectator is the ancilla's neighbour)


def a_of(n):
    a = int(round(2 ** n * (math.sqrt(5) - 1) / 2))
    return a + (a % 2 == 0)


def phases(n, K):
    """j_k = k a_n mod 2^n, k = 1 .. K (a_n odd: the trailing zeros of j_k are k's, so half the phases are odd and
    every round of an odd phase carries a non-trivial controlled phase)."""
    return [(k * a_of(n)) % 2 ** n for k in range(1, K + 1)]


def bits_of(n, j):
    return {m: (j >> (n - 1 - m)) & 1 for m in range(n)}


def ipe_form(n, j, form, park=True, delay_dt=0, spectator_read=False):
    """One IPE circuit of the given form: 'F' (conditional corrections), 'S' (fixed corrections), 'SD' (fixed
    corrections and delay_dt per conditional F holds at that place), 'OFF' (no phase feedback: the off arm's shape,
    never run), with the spectator read beside the ancilla when
    spectator_read. Returns (circuit, success {clbit: bit})."""
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
    q, c = QuantumRegister(3, "q"), ClassicalRegister(2 * n if spectator_read else n, "c")
    qc = QuantumCircuit(q, c)
    a, t, s = A_Q, T_Q, S_Q
    succ = bits_of(n, j)
    phi = j / 2 ** n
    qc.x(t)
    for m in range(n - 1, -1, -1):
        qc.h(a)
        AP._cp(qc, 2 * math.pi * phi * 2 ** m, a, t)
        run = list(range(1, n - m))                      # bits phi_{m+1+d}, read earlier, in c[m + d]
        if run and form == "F":
            for d in run:
                with qc.if_test((c[m + d], 1)):
                    qc.p(-2 * math.pi / 2 ** (d + 1), a)
        elif run and form != "OFF":
            if park:
                qc.x(t)                                  # the parking pair F's park_waits puts around its run
            qc.barrier()
            for d in run:
                if succ[m + d]:
                    qc.p(-2 * math.pi / 2 ** (d + 1), a)
            if form == "SD" and delay_dt:
                qc.delay(int(delay_dt) * len(run), list(range(qc.num_qubits)), unit="dt")
            qc.barrier()
            if park:
                qc.x(t)
        qc.h(a)
        if spectator_read:
            qc.measure([a, s], [m, n + m])
        else:
            qc.measure(a, m)
        if m > 0:
            with qc.if_test((c[m], 1)):
                qc.x(a)                                  # reset the ancilla for the next round (every form)
    return qc, succ


def plan_items(plan, L=L_DT):
    """[(tag, n, j, form, delay_dt, spectator_read)]: tags ip<f><n>_<j>, f = f (F), s (S), d (SD at L), e (SD at 2 L),
    r (F with the spectator read)."""
    p = PLANS[plan]
    code = {("F", 1): "f", ("S", 1): "s", ("SD", 1): "d", ("SD", 2): "e"}
    out = []
    for n in p["ns"]:
        for j in phases(n, p["K"]):
            for form in p["forms"]:
                for x in (p["Lx"] if form == "SD" else (1,)):
                    out.append((f"ip{code[(form, x)]}{n}_{j}", n, j, form, L * x if form == "SD" else 0, False))
        if p["R"]:
            for j in phases(n, p["K"])[:R_TWINS]:
                out.append((f"ipr{n}_{j}", n, j, "F", 0, True))
    return out


def qpu_seconds(n_circ, shots):
    return n_circ * 0.036 + n_circ * shots * 0.00027 + 3.0


def size(plan):
    p = PLANS[plan]
    its = plan_items(plan)
    n_c = len(its) + SENT
    s = p["shots"]
    per_n = {}
    for n in p["ns"]:
        P = RECORD[n]
        per_n[n] = round(2 * math.sqrt(2 * P * (1 - P) / (p["K"] * s)), 4)       # a difference of two forms
    pooled = round(0.5 * math.sqrt(sum((v / 2) ** 2 for v in per_n.values())) * 2, 4)
    out = dict(plan=plan, circuits=n_c, shots=s, seconds=round(qpu_seconds(n_c, s), 1), diff_two_se_per_n=per_n,
               diff_two_se_pooled=pooled, forms=list(p["forms"]), Lx=list(p["Lx"]), phases_per_n=p["K"])
    if p["R"]:
        out["twin_two_se_pooled"] = round(0.5 * math.sqrt(sum(2 * RECORD[n] * (1 - RECORD[n]) / (R_TWINS * s)
                                                              for n in p["ns"])) * 2, 4)
    return out


def table(a):
    rows = [size(p) for p in PLANS]
    json.dump(dict(rows=rows, phases={n: phases(n, 16) for n in (6, 8)}, a={n: a_of(n) for n in (6, 8)},
                   record=RECORD, L_dt=L_DT), open(a.out, "w"), indent=1)
    for r in rows:
        print(f"plan {r['plan']}: {r['circuits']} circuits at {r['shots']} shots, {r['seconds']} s; forms "
              f"{'/'.join(r['forms'])} (SD at {r['Lx']} x L), {r['phases_per_n']} phases per n; 2 SE of a difference: "
              + ", ".join(f"n{n} {v}" for n, v in r["diff_two_se_per_n"].items()) + f", pooled {r['diff_two_se_pooled']}"
              + (f"; R twin 2 SE pooled {r['twin_two_se_pooled']}" if "twin_two_se_pooled" in r else ""))


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
    items = []
    for tag, n, j, form, dl, sp in plan_items(a.plan, a.L_dt):
        qc, succ = ipe_form(n, j, form, True, dl, sp)
        off, _ = ipe_form(n, j, "OFF", False, 0, sp)      # declared shape only (ff_only: never run)
        items.append((tag, qc, dict(success=succ, off_circuit=off, form="blocks")))
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None   # dry runs only, never a device
    jd = os.path.join(a.out, "job0")
    os.makedirs(a.out)
    rep = FF.build(dev, items, jd, shots=p["shots"], max_seconds=MAX_S, sentinel_spec=spec,
                   ff_only=[t for t, _, _ in items], park=True, park_likely=True, footprint=True, declared=DECLARED)
    json.dump(dict(part=f"branch:{a.plan}", shots=p["shots"], tags=[t for t, _, _ in items]),
              open(os.path.join(jd, "part.json"), "w"))
    json.dump(dict(plan=a.plan, device=dev.name, devdir=os.path.abspath(a.devdir), psf_os=psf_os.__version__,
                   shots=p["shots"], L_dt=a.L_dt, circuits=rep["circuits"], qpu_seconds_model=rep["qpu_seconds_model"]),
              open(os.path.join(a.out, "plan.json"), "w"), indent=1)
    print(f"{rep['circuits']} circuits at {p['shots']} shots, {rep['qpu_seconds_model']:.1f} s on {dev.name}")


def _job(out):
    from qiskit import qpy
    jd = os.path.join(out, "job0")
    man = json.load(open(os.path.join(jd, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(jd, "job", "circuits.qpy"), "rb"))
    cells = {c["cell"]: c for c in man["cells"]}
    return jd, man, cs, {cells[p["cell"]]["name"][3:]: cs[i] for i, p in enumerate(man["pubs"])
                         if cells[p["cell"]]["role"] == "user"}


def _counts(c, n):
    """Compiled counts: CZ, one-qubit gates (outside and inside conditionals), conditionals, delays (total dt per
    qubit; any other unit is recorded as such), the conditionals of each run (between two reads of scored bits,
    clbits below n: the spectator's reads do not split a run)."""
    from psf_os import feedforward as FF
    one = cond = bars = 0
    xs = {}
    delays = {}
    runs, cur = [], 0
    for x in c.data:
        nm = x.operation.name
        if nm == "if_else":
            cond += 1
            cur += 1
            for blk in x.operation.blocks:
                if blk is not None:
                    one += sum(1 for y in blk.data if len(y.qubits) == 1 and y.operation.name not in ("barrier",))
        elif nm == "measure" and c.find_bit(x.clbits[0]).index < n:
            runs.append(cur)
            cur = 0
        elif nm == "delay":
            q = c.find_bit(x.qubits[0]).index
            key = q if x.operation.unit == "dt" else (q, x.operation.unit)
            delays[key] = delays.get(key, 0) + x.operation.duration
        elif nm == "barrier":
            bars += 1
        elif len(x.qubits) == 1 and nm != "measure":
            one += 1
            if nm in ("x", "sx"):
                key = (c.find_bit(x.qubits[0]).index, nm)
                xs[key] = xs.get(key, 0) + 1
    return dict(cz=FF.cz_count(c), one=one, cond=cond, delays=delays, runs=runs, xs=xs, bars=bars)


def check(a):
    """(1) noiseless: F, S and SD of each phase give the same exact distribution of the scored bits, and every shot
    has all n bits right (the corrections right for the phase); (2) compiled: the same CZ, X and SX per qubit outside
    conditionals, and fences in F, S, SD (one-qubit gate totals reported: F's conditional blocks counted); F's compiled conditionals per run
    (feedback + reset) as built; (3) every SD item keeps its delays after compiling, L * (r - 1) per round on every
    qubit, totals as built; no delay in F or S; (4) psf_os_build 0.3.1 with park and park_likely stated; F parked."""
    from psf_os.footprint import exact_distribution
    info = json.load(open(os.path.join(a.out, "plan.json")))
    jd, man, _cs, by = _job(a.out)
    L = info["L_dt"]
    lines, ok_all = [], True
    its = plan_items(info["plan"], L)
    # (1)
    bad = []
    for tag, n, j, form, dl, sp in its:
        qc, succ = ipe_form(n, j, form, True, 0, sp)         # the delay is an identity in the exact model
        dist = exact_distribution(qc)
        ok = sum(p for k, p in dist.items() if all(k[len(k) - 1 - m] == str(v) for m, v in succ.items()))
        if abs(ok - 1.0) > 1e-9:
            bad.append((tag, round(ok, 6)))
    lines.append(f"(1) noiseless, every item all n bits right with probability 1: "
                 f"{'ok, ' + str(len(its)) + ' items' if not bad else 'NOT ' + str(bad[:4])}")
    ok_all &= not bad
    # (2), (3)
    cz_bad, d_bad, rows = [], [], {}
    for tag, n, j, form, dl, sp in its:
        k = _counts(by[tag], n)
        rows[tag] = k
        exp_runs = [n - 1 - m + (1 if m < n - 1 else 0) for m in range(n - 1, -1, -1)]   # feedback + previous reset
        if form == "F" and k["runs"] != exp_runs:
            d_bad.append((tag, "runs", k["runs"]))
        if form == "SD":
            want = sum(dl * r for r in range(n))
            if set(k["delays"]) != {0, 1, 2} or any(v != want for v in k["delays"].values()):
                d_bad.append((tag, "delays", k["delays"], want))
        elif k["delays"]:
            d_bad.append((tag, "delay in " + form))
    for tag, n, j, form, dl, sp in its:
        if form != "F" or sp:
            continue
        for o in ("s", "d", "e"):
            t2 = tag.replace("ipf", "ip" + o)
            if t2 in rows and any(rows[t2][k] != rows[tag][k] for k in ("cz", "xs", "bars")):
                cz_bad.append((tag, t2, rows[tag]["cz"], rows[t2]["cz"]))
    lines.append(f"(2) compiled CZ, X and SX per qubit outside conditionals, and fences the same in F, S, SD of every "
                 f"phase: {'ok' if not cz_bad else 'NOT ' + str(cz_bad[:4])}")
    ok_all &= not cz_bad
    for n in sorted({x[1] for x in its}):
        for fm in ("f", "s", "d", "e", "r"):
            ts = [t for t in rows if t.startswith(f"ip{fm}{n}_")]
            if ts:
                cz = sum(rows[t]["cz"] for t in ts) / len(ts)
                one = sum(rows[t]["one"] for t in ts) / len(ts)
                cond = sum(rows[t]["cond"] for t in ts) / len(ts)
                lines.append(f"    n {n} {fm}: {len(ts)} items, CZ {cz:.2f}, one-qubit gates {one:.1f} (conditional "
                             f"blocks counted), conditionals {cond:.1f}")
    lines.append(f"(3) F's conditionals per run as built; SD's delays kept after compiling (L {L} dt x (r - 1) per "
                 f"round, on all 3 qubits); none in F or S: {'ok' if not d_bad else 'NOT ' + str(d_bad[:3])}")
    ok_all &= not d_bad
    # (4)
    b = man.get("psf_os_build", {})
    okb = b.get("version") == "0.3.1" and b.get("park") is True and b.get("park_set") == "explicit" and \
        b.get("park_likely") is True and "park_likely_set" not in b and b.get("declared") == DECLARED
    lines.append(f"(4) psf_os_build {b} -> {'ok (park and park_likely stated)' if okb else 'NOT AS DECLARED'}")
    ok_all &= okb
    unparked = []
    for t in by:
        rec = json.load(open(os.path.join(jd, "runs", f"ff_{t}.json")))
        if not rec.get("park", {}).get("arms", {}).get("ff", {}).get("parked"):
            unparked.append(t)
    lines.append(f"    psf-os parked the target in every item: {'ok' if not unparked else 'NOT ' + str(unparked[:4])}")
    ok_all &= not unparked
    lines.append("PASS" if ok_all else "FAIL")
    print("\n".join(lines))
    open(os.path.join(a.out, "check.txt"), "w").write("\n".join(lines) + "\n")
    return ok_all


def noisy(cc, noise, L):
    """ILLUSTRATIVE noise, by hand (never fitted, no calibration number): per conditional (if_else) a dephasing
    'cond' on every qubit (the branch itself); per wait unit (one conditional, or a delay of L) an amplitude damping
    'wait_amp' and a dephasing 'wait_deph' on every qubit waiting (a conditional: every qubit; a delay: its qubit,
    once per L of its length)."""
    from qiskit_aer.noise import amplitude_damping_error, phase_damping_error
    lc, la, lp = (float(noise.get(k, 0.0)) for k in ("cond", "wait_amp", "wait_deph"))
    out = cc.copy_empty_like()

    def wait(qs, k=1):
        for _ in range(k):
            for q in qs:
                if la:
                    out.append(amplitude_damping_error(la).to_instruction(), [q])
                if lp:
                    out.append(phase_damping_error(lp).to_instruction(), [q])
    for ins in cc.data:
        nm = ins.operation.name
        if nm == "delay":
            if ins.operation.unit != "dt":
                raise ValueError("a delay not in dt")
            wait(ins.qubits, int(round(ins.operation.duration / L)))
            continue
        out.append(ins.operation, ins.qubits, ins.clbits)
        if nm == "if_else":
            if lc:
                for q in out.qubits:
                    out.append(phase_damping_error(lc).to_instruction(), [q])
            wait(out.qubits)
    return out


def dry(a):
    """Dry runs only: every circuit under ILLUSTRATIVE noise (noisy, plus depolarizing 'p2' on every CZ); writes the
    job's submission.json and raw_counts.json as psf_os.feedforward.run_local does (local=True, the noise written in)."""
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, depolarizing_error
    from psf_os import feedforward as FF
    from psf_os.ibm import _stamp
    from psf_os.sim import to_clifford_gates
    noise = json.load(open(a.noise))
    info = json.load(open(os.path.join(a.out, "plan.json")))
    job = os.path.join(a.out, "job0", "job")
    sub = os.path.join(job, "submission.json")
    if os.path.exists(sub):
        raise SystemExit(f"{sub} exists: this job was already run")
    man = json.load(open(os.path.join(job, "manifest.json")))
    circs = qpy.load(open(os.path.join(job, "circuits.qpy"), "rb"))
    rows = []
    for k, c in enumerate(circs):
        cc = FF.compact(c)
        seed = a.seed + 10_000 * k
        cl = None if cc.has_control_flow_op() else to_clifford_gates(cc)
        if cl is not None and cc.num_qubits > FF.LOCAL_MAX_QUBITS:
            res = AerSimulator(method="stabilizer").run(cl, shots=man["shots"], seed_simulator=seed).result()
        else:
            nm = NoiseModel()
            if noise.get("p2"):
                nm.add_all_qubit_quantum_error(depolarizing_error(float(noise["p2"]), 2), ["cz"])
            sim = AerSimulator(method="density_matrix", noise_model=nm)
            res = sim.run(noisy(cc, noise, info["L_dt"]), shots=man["shots"], seed_simulator=seed).result()
        rows.append(dict(pub=k, counts={key.replace(" ", ""): v for key, v in res.get_counts(0).items()}))
    t = _stamp()
    jid = f"local-illustrative-noise-{a.seed}"
    json.dump(dict(job_id=jid, submitted=t, local=True, backend=man["fetch"]["backend"],
                   simulator="aer, ILLUSTRATIVE noise (not fitted to any device)", noise=noise, seed=a.seed,
                   circuit_stride=10_000), open(sub, "w"), indent=1)
    json.dump(dict(fetched=t, job_id=jid, status="DONE (local, illustrative noise)", rows=rows),
              open(os.path.join(job, "raw_counts.json"), "w"))
    print(f"dry run written ({len(rows)} circuits, {jid}, noise {noise})")


def word(d, se, what):            # [OWNER]
    if d > 0 and d >= 2 * se:
        return f"{what} COSTS"
    if d < 0 and d <= -2 * se:
        return f"{what} GAINS"
    return f"NO {what} COST SEEN"


READING = {                       # [OWNER]: every pair of words on one row (3 x 3), with what 0.4 would try
    ("FEEDBACK COSTS", "WAIT COSTS"):
        "both the branch and its wait cost: 0.4 tries fewer conditionals (the corrections of a round merged into one "
        "conditional on the earlier bits, a table look-up) and the parked wait kept",
    ("FEEDBACK COSTS", "NO WAIT COST SEEN"):
        "the branch costs beyond its time: 0.4 tries deferring the corrections (applied once, late, from the bits "
        "together) or a classical post-correction where the algorithm allows it",
    ("FEEDBACK COSTS", "WAIT GAINS"):
        "the branch costs and the delay alone helps (a dynamical effect of idling, not a cost of time): 0.4 tries "
        "deferred corrections with a fixed idle, read beside first",
    ("NO FEEDBACK COST SEEN", "WAIT COSTS"):
        "the loss is the time waited, not the branch: 0.4 tries shorter waits (corrections merged into fewer "
        "conditionals), parking every waiting qubit, and placement away from the slow times",
    ("NO FEEDBACK COST SEEN", "NO WAIT COST SEEN"):
        "neither part costs at this n and L: the loss per round lies elsewhere (the controlled phase, the reads); "
        "0.4 tries the angle-dependent loss seen beside (controlled phases near pi) before any control rule",
    ("NO FEEDBACK COST SEEN", "WAIT GAINS"):
        "the delay helps and the branch is neutral: not read for a control rule; 0.4 tries the idle as a "
        "dynamical decoupling question, beside",
    ("FEEDBACK GAINS", "WAIT COSTS"):
        "F keeps more than S plus the delay although the wait costs: the delay overstates F's wait (L too long); "
        "read with plan d's two lengths before any 0.4 step",
    ("FEEDBACK GAINS", "NO WAIT COST SEEN"):
        "F keeps more than the fixed corrections at no wait cost: not expected noiselessly; check the build first, "
        "no 0.4 step",
    ("FEEDBACK GAINS", "WAIT GAINS"):
        "both differences reversed: not read for the mechanism; check the build first, no 0.4 step",
}


def score(a):
    from psf_os import feedforward as FF
    from psf_os import job as J
    info = json.load(open(os.path.join(a.out, "plan.json")))
    p = PLANS[info["plan"]]
    jd = os.path.join(a.out, "job0")
    read = J.read(os.path.join(jd, "job"), os.path.join(jd, "runs"))
    cards = {}
    for _n, (rec, cc) in read.items():
        if rec.get("psfos_job", {}).get("kind", "").startswith(FF.KIND) and rec.get("ff_arm") == "ff":
            cards[rec["tag"]] = FF.success_share(cc[("f", "z")], rec["clbits"],
                                                 {int(b): v for b, v in rec["success"].items()})
    lines, res = [], dict(per_n={})
    say = lambda s: (print(s), lines.append(s))

    def pool(tags):
        ok = sum(cards[t]["success"] for t in tags)
        N = sum(cards[t]["counted"] for t in tags)
        q = ok / N
        return q, math.sqrt(q * (1 - q) / N)
    diffs = {"fb": [], "wait": [], "wait2": [], "read": []}
    for n in p["ns"]:
        P = {fm: pool([t for t in cards if t.startswith(f"ip{fm}{n}_")]) for fm in ("f", "s", "d", "e")
             if any(t.startswith(f"ip{fm}{n}_") for t in cards)}
        r = {fm: dict(p=v[0], two_se=2 * v[1]) for fm, v in P.items()}
        fb = (P["d"][0] - P["f"][0], math.hypot(P["d"][1], P["f"][1]))
        wt = (P["s"][0] - P["d"][0], math.hypot(P["s"][1], P["d"][1]))
        diffs["fb"].append(fb)
        diffs["wait"].append(wt)
        r.update(feedback=dict(d=fb[0], two_se=2 * fb[1]), wait=dict(d=wt[0], two_se=2 * wt[1]))
        if "e" in P:
            w2 = (P["d"][0] - P["e"][0], math.hypot(P["d"][1], P["e"][1]))
            diffs["wait2"].append(w2)
            r["wait_second_L"] = dict(d=w2[0], two_se=2 * w2[1])
        tw = [t for t in cards if t.startswith(f"ipr{n}_")]
        if tw:
            pf, sf = pool([t.replace("ipr", "ipf") for t in tw])
            pr, sr = pool(tw)
            diffs["read"].append((pf - pr, math.hypot(sf, sr)))
            r["neighbour_read"] = dict(d=pf - pr, two_se=2 * math.hypot(sf, sr), phases=len(tw))
        res["per_n"][str(n)] = r
        say(f"n {n}: P F {P['f'][0]:.4f}, S {P['s'][0]:.4f}, SD {P['d'][0]:.4f}" +
            (f", SD(2L) {P['e'][0]:.4f}" if "e" in P else "") +
            f"; SD - F {fb[0]:+.4f} (2 SE {2 * fb[1]:.4f}); S - SD {wt[0]:+.4f} (2 SE {2 * wt[1]:.4f})" +
            (f"; beside F - R {r['neighbour_read']['d']:+.4f} (2 SE {r['neighbour_read']['two_se']:.4f})" if tw else ""))

    def mean(v):
        return sum(x for x, _ in v) / len(v), math.sqrt(sum(s ** 2 for _, s in v)) / len(v)
    fb, wt = mean(diffs["fb"]), mean(diffs["wait"])
    wf, ww = word(fb[0], fb[1], "FEEDBACK"), word(wt[0], wt[1], "WAIT")
    row = READING[(wf, ww)]
    res.update(feedback=dict(d=fb[0], two_se=2 * fb[1], word=wf), wait=dict(d=wt[0], two_se=2 * wt[1], word=ww),
               reading=row)
    say(f"pooled over n (mean of the n): SD - F {fb[0]:+.4f} (2 SE {2 * fb[1]:.4f}) -> {wf}; S - SD {wt[0]:+.4f} "
        f"(2 SE {2 * wt[1]:.4f}) -> {ww}")
    if diffs["wait2"]:
        w2 = mean(diffs["wait2"])
        res["wait_second_L"] = dict(d=w2[0], two_se=2 * w2[1])
        say(f"beside: SD(L) - SD(2L) {w2[0]:+.4f} (2 SE {2 * w2[1]:.4f}), the wait's cost per further L")
    if diffs["read"]:
        rd = mean(diffs["read"])
        res["neighbour_read"] = dict(d=rd[0], two_se=2 * rd[1])
        say(f"beside: F - R (reading the neighbour) {rd[0]:+.4f} (2 SE {2 * rd[1]:.4f})")
    say(f"reading: {row}")
    json.dump(res, open(os.path.join(a.out, "branch_scores.json"), "w"), indent=1)
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
    b.add_argument("--L-dt", type=int, default=L_DT)
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
