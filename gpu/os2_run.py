"""Run the prescription loop with compounding end to end (prereg/os2_night_2026-11-18.md once declared; draft text
prereg/drafts-2026-11-18/os2_night_2026-11-18_READY.md). Workplace Claude, 2026-11-18 (home instruction "複利の OS を
今夜実機で"). One command runs the night without a person in between: device record, diagnostics, rule, round 1,
score, rule, round 2, ... until a stop.

  python gpu/os2_run.py preflight [--dry] [--out OUT] [--zip ZIPFILE]
  python gpu/os2_run.py go OUT --zip ZIPFILE                 the night on the device (home PC, saved IBM account)
  python gpu/os2_run.py go OUT --dry DEVDIR [--noise NOISE.json] [--k-max K] [--budget S]   noiseless / example noise
  python gpu/os2_run.py resume OUT [--zip ZIPFILE]           continue a stopped night (never sends a job twice)
  python gpu/os2_run.py verify OUT [--resim]                  rebuild, re-score, re-rule from the records: SAME / DIFFERENT
                                                             (--resim, dry runs: re-simulate with the recorded seeds)

Order (each step is skipped when its output already exists, so resume continues where it stopped):
  1. fetch: gpu/daily_fetch.py OUT/fetch_in (queue and device records; the night's device is the first one it
     chooses, in the declared order ibm_marrakesh, ibm_fez, ibm_kingston). Dry: DEVDIR is copied in, queue marked dry.
  2. diagnostics: Dw (gpu/wait_night.py items) and Dc (gpu/ctrl_night.py items): build, check, budget, submit, queue
     after, collect, score.
  3. the rule of 2026-11-17 (gpu/os_night.py rule) -> OUT/os_rule.json; round 1 -> OUT/RULE1.json.
  4. round k: build OUT/r{k} from RULE{k}.json, check, budget (diagnostics + rounds run + this round's model seconds
     <= 240; otherwise the job is moved to job_NOT_SENT and the night stops), submit, queue after, collect, score, the
     rule -> RULE{k+1}.json; stop when the rule says so (fixed point, K_MAX).
  5. compound, job timing, stop.json; the whole OUT zipped (Python zipfile) to ZIPFILE (device runs).
Stops: a check FAIL, a refused build, the budget, K_MAX, a fixed point; a collect that times out (60 min per job)
stops with resumable = true. The reason is written to OUT/stop.json.

Safety: no key is read (the saved IBM account, as gpu/daily_fetch.py); no git network operation; IBM is touched only
by `python -m psf_os submit`, `python -m psf_os collect`, gpu/daily_fetch.py and the queue read after each submission.
A job folder with a submission.json is never submitted again. Dry runs never touch IBM.
"""
import argparse
import contextlib
import datetime as dt
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
import zipfile
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)

PSF_OS_COMMIT = "0f57c76db110ba25857a71a883e1d41574af73ee"
DECLARATION = "prereg/os2_night_2026-11-18.md"
ORDER = ["ibm_marrakesh", "ibm_fez", "ibm_kingston"]
COLLECT_WAIT_MIN = 60
EXPECTED = {"qiskit": "2.5.2", "qiskit_aer": "0.18.0", "qiskit_ibm_runtime": "0.51.0"}   # checked by the workplace VS
DRY_SEED0 = 20261118


def dry_seed(tag):
    """Dry runs only: the simulator's seed per job, fixed here (declared): dw 20261116, dc 20261117, round k
    20261118 + k; recorded in the job's submission.json, and used again by verify --resim."""
    if tag == "dw":
        return DRY_SEED0 - 2
    if tag == "dc":
        return DRY_SEED0 - 1
    return DRY_SEED0 + int(tag[1:])


def now():
    t = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    return f"{t.isoformat()} ({t.astimezone(ZoneInfo('Europe/Zurich')).strftime('%Y-%m-%d %H:%M:%S')} CET)"


class Night:
    def __init__(self, out):
        self.out = os.path.abspath(out)
        self.cfg_file = os.path.join(self.out, "run.json")

    # ---------------------------------------------------------------------------------------------- bookkeeping
    def log(self, msg):
        line = f"[{now()}] {msg}"
        print(line, flush=True)
        with open(os.path.join(self.out, "run_log.txt"), "a") as f:
            f.write(line + "\n")

    def cfg(self):
        return json.load(open(self.cfg_file))

    def stop(self, reason, resumable=False, **extra):
        d = dict(reason=reason, resumable=resumable, written=now(), **extra)
        json.dump(d, open(os.path.join(self.out, "stop.json"), "w"), indent=1)
        self.log(f"STOP: {reason}" + (" (resumable)" if resumable else ""))
        return d

    # ---------------------------------------------------------------------------------------------- IBM or local
    def submit(self, folder):
        job = os.path.join(folder, "job")
        if os.path.exists(os.path.join(job, "submission.json")):
            self.log(f"{os.path.basename(folder)}: already submitted (submission.json), not sent again")
            return True
        if self.cfg()["dry"]:
            seed = dry_seed(os.path.basename(folder))
            simulate(folder, self.cfg().get("noise"), seed)
            self.log(f"{os.path.basename(folder)}: run locally ({'example noise' if self.cfg().get('noise') else 'noiseless'}"
                     f", seed {seed})")
            return True
        r = subprocess.run([sys.executable, "-m", "psf_os", "submit", "--job", job], capture_output=True, text=True)
        self.log(f"{os.path.basename(folder)}: submit -> {r.stdout.strip()} {r.stderr.strip()}")
        if not os.path.exists(os.path.join(job, "submission.json")):
            return False
        self.queue_after(os.path.basename(folder))
        return True

    def queue_after(self, tag):
        """Pending jobs per device right after a submission (the saved account; no key, no quality number)."""
        try:
            from qiskit_ibm_runtime import QiskitRuntimeService
            s = QiskitRuntimeService()
            q = {n: s.backend(n).status().pending_jobs for n in ORDER}
            d = dict(read=dt.datetime.now(dt.timezone.utc).isoformat(), pending=q, after=tag)
        except Exception as exc:  # noqa: BLE001 - a failed read is recorded, never fatal
            d = dict(read=dt.datetime.now(dt.timezone.utc).isoformat(), error=type(exc).__name__, after=tag)
        json.dump(d, open(os.path.join(self.out, f"queue_after_{tag}.json"), "w"), indent=1)
        json.dump(d, open(os.path.join(self.out, tag, "queue_after.json"), "w"), indent=1)

    def collect(self, folder):
        job = os.path.join(folder, "job")
        if os.path.exists(os.path.join(job, "raw_counts.json")):
            return "DONE"
        if self.cfg()["dry"]:
            return "MISSING"
        r = subprocess.run([sys.executable, "-m", "psf_os", "collect", "--job", job, "--wait-min", str(COLLECT_WAIT_MIN)],
                           capture_output=True, text=True)
        self.log(f"{os.path.basename(folder)}: collect -> {r.stdout.strip()} {r.stderr.strip()}")
        if os.path.exists(os.path.join(job, "raw_counts.json")):
            return "DONE"
        return "ERROR" if any(x in r.stdout.upper() for x in ("ERROR", "CANCEL")) else "WAIT"

    # ---------------------------------------------------------------------------------------------- steps
    def device_dir(self):
        c = self.cfg()
        return os.path.join(self.out, "fetch_in", c["device"], "dev")

    def fetch(self):
        base = os.path.join(self.out, "fetch_in")
        c = self.cfg()
        if os.path.exists(os.path.join(base, "queue.json")):
            return True
        if c["dry"]:
            from psf_os.device import Device
            dev = Device.load(c["dry_devdir"])
            os.makedirs(os.path.join(base, dev.name))
            shutil.copytree(c["dry_devdir"], os.path.join(base, dev.name, "dev"))
            json.dump(dict(dry=True, pending=None, chosen=[dev.name], read=None), open(os.path.join(base, "queue.json"),
                                                                                       "w"), indent=1)
        else:
            r = subprocess.run([sys.executable, os.path.join(HERE, "daily_fetch.py"), base], capture_output=True,
                               text=True)
            self.log(f"fetch -> {r.stdout.strip()} {r.stderr.strip()}")
            if r.returncode != 0 or not os.path.exists(os.path.join(base, "queue.json")):
                return False
        q = json.load(open(os.path.join(base, "queue.json")))
        c["device"] = q["chosen"][0]
        json.dump(c, open(self.cfg_file, "w"), indent=1)
        self.log(f"device {c['device']} (queue {q.get('pending')})")
        return True

    def spent(self):
        """Model seconds of every job built and sent (or to be sent) so far: diagnostics and rounds with a job/."""
        tot = 0.0
        for d in sorted(os.listdir(self.out)):
            p = os.path.join(self.out, d)
            if os.path.isdir(os.path.join(p, "job")) and os.path.exists(os.path.join(p, "build.json")):
                tot += json.load(open(os.path.join(p, "build.json")))["qpu_seconds_model"]
        return tot

    def budget_ok(self, folder):
        """True when the night's model seconds (every job folder, this one included) stay within the budget."""
        b = self.cfg()["budget"]
        tot = self.spent()
        if tot > b + 1e-9:
            os.rename(os.path.join(folder, "job"), os.path.join(folder, "job_NOT_SENT"))
            self.stop(f"budget: the night would take {tot:.1f} s by the model with {os.path.basename(folder)}, over "
                      f"{b:.0f} s; {os.path.basename(folder)} not sent (job_NOT_SENT)", budget_s=b, model_s=tot)
            return False
        return True

    def run_job(self, folder, check_fn, score_fn):
        """check -> budget -> submit -> collect -> score, each skipped when its output exists. Returns True when the
        job is scored, or a stop dict."""
        name = os.path.basename(folder)
        sub = os.path.join(folder, "job", "submission.json")
        if not os.path.exists(sub):
            if not os.path.exists(os.path.join(folder, "check_ok")):
                ok = _quiet(check_fn, types.SimpleNamespace(out=folder), os.path.join(folder, "check.txt"))
                if ok is False:
                    os.rename(os.path.join(folder, "job"), os.path.join(folder, "job_NOT_SENT"))
                    return self.stop(f"{name}: check FAIL (check.txt); not sent")
                open(os.path.join(folder, "check_ok"), "w").write(now() + "\n")
                self.log(f"{name}: check PASS")
            if not self.budget_ok(folder):
                return json.load(open(os.path.join(self.out, "stop.json")))
            if not self.submit(folder):
                return self.stop(f"{name}: submission refused or failed (see run_log.txt)")
        st = self.collect(folder)
        if st == "WAIT":
            return self.stop(f"{name}: not finished after {COLLECT_WAIT_MIN} min; run resume", resumable=True)
        if st != "DONE":
            return self.stop(f"{name}: the job ended {st}")
        _quiet(score_fn, types.SimpleNamespace(out=folder), os.path.join(folder, "score.txt"))
        self.log(f"{name}: scored")
        return True

    def diagnostics(self):
        import ctrl_night as CN
        import wait_night as WN
        for tag, mod, scores in (("dw", WN, "wait_scores.json"), ("dc", CN, "ctrl_scores.json")):
            folder = os.path.join(self.out, tag)
            if not os.path.exists(folder):
                try:
                    build_diag(mod, self.device_dir(), folder, self.cfg()["dry"])
                except (Exception, SystemExit) as exc:  # noqa: BLE001
                    self.stop(f"{tag}: build refused ({type(exc).__name__}: {exc})")
                    return False
                self.log(f"{tag}: built ({json.load(open(os.path.join(folder, 'build.json')))['qpu_seconds_model']} s)")
            if not os.path.exists(os.path.join(folder, scores)):
                r = self.run_job(folder, mod.check, mod.score)
                if r is not True:
                    return False
        return True

    def rounds(self):
        import os2_night as O
        import os_night as ON
        c = self.cfg()
        if not os.path.exists(os.path.join(self.out, "os_rule.json")):
            _quiet(ON.rule, types.SimpleNamespace(dw=os.path.join(self.out, "dw"), dc=os.path.join(self.out, "dc"),
                                                  rule_json=os.path.join(self.out, "os_rule.json")),
                   os.path.join(self.out, "os_rule.txt"))
        if not os.path.exists(os.path.join(self.out, "RULE1.json")):
            _quiet(O.round1, types.SimpleNamespace(os_rule=os.path.join(self.out, "os_rule.json"),
                                                   out_rule=os.path.join(self.out, "RULE1.json"), device=None,
                                                   diag=[os.path.join(self.out, "dw"), os.path.join(self.out, "dc")]),
                   os.path.join(self.out, "round1.txt"))
            self.log("RULE1.json: " + json.dumps(json.load(open(os.path.join(self.out, "RULE1.json")))["stacks"]))
        k = 1
        while True:
            rule_k = os.path.join(self.out, f"RULE{k}.json")
            R = json.load(open(rule_k))
            if R.get("stop"):
                return self.stop(f"the rule: {R['stop_reason']} (after round {k - 1})", rounds=k - 1)
            folder = os.path.join(self.out, f"r{k}")
            if not os.path.exists(folder):
                try:
                    ok = _quiet(O.build, types.SimpleNamespace(devdir=self.device_dir(), out=folder, rule_json=rule_k,
                                                               dry_clifford_sentinel=c["dry"]),
                                os.path.join(self.out, f"build_r{k}.txt"))
                except (Exception, SystemExit) as exc:  # noqa: BLE001 - a refusal of any kind stops the night
                    return self.stop(f"r{k}: build refused ({type(exc).__name__}: {exc})", rounds=k - 1)
                if ok is False or not os.path.isdir(os.path.join(folder, "job")):
                    return self.stop(f"r{k}: build refused (build_r{k}.txt)", rounds=k - 1)
                self.log(f"r{k}: built {json.dumps(R['stacks'])} "
                         f"({json.load(open(os.path.join(folder, 'build.json')))['qpu_seconds_model']} s)")
            if not os.path.isdir(os.path.join(folder, "job")):
                return json.load(open(os.path.join(self.out, "stop.json")))
            if not os.path.exists(os.path.join(folder, "round_scores.json")):
                r = self.run_job(folder, O.check, O.score)
                if r is not True:
                    return r
            nxt = os.path.join(self.out, f"RULE{k + 1}.json")
            if not os.path.exists(nxt):
                _quiet(O.rule, types.SimpleNamespace(out_rule=nxt, rounds=[os.path.join(self.out, f"r{j}")
                                                                           for j in range(1, k + 1)],
                                                     k_max=c["k_max"]), os.path.join(self.out, f"rule_r{k + 1}.txt"))
                Rn = json.load(open(nxt))
                self.log(f"RULE{k + 1}.json: {json.dumps(Rn['stacks'])} " + json.dumps(Rn["why"]))
            k += 1

    def finish(self):
        import os2_night as O
        import job_timing as JT
        rounds = sorted([d for d in os.listdir(self.out) if d.startswith("r") and d[1:].isdigit() and
                         os.path.exists(os.path.join(self.out, d, "round_scores.json"))], key=lambda d: int(d[1:]))
        if rounds:
            rs = [json.load(open(os.path.join(self.out, d, "round_scores.json"))) for d in rounds]
            comp = O.compound_rows(rs)
            json.dump(comp, open(os.path.join(self.out, "compound.json"), "w"), indent=1)
            self.log("compound: " + str({k: v for k, v in comp.items() if k in ("verdict", "slope", "se",
                                                                                 "difference", "two_se")}))
        if rounds:
            pr = predictions(self.out)
            json.dump(pr, open(os.path.join(self.out, "predictions.json"), "w"), indent=1)
            self.log("predictions: " + json.dumps(pr))
        rows = {}
        for d in ["dw", "dc"] + rounds:
            p = os.path.join(self.out, d)
            if os.path.isdir(p):
                rows[d] = dict(jobs=JT.jobs(p), queue_after=JT.queue(p, "queue_after.json"))
        rows["queue_before"] = JT.queue(os.path.join(self.out, "fetch_in")) if not self.cfg()["dry"] else None
        json.dump(rows, open(os.path.join(self.out, "job_timing.json"), "w"), indent=1)
        z = self.cfg().get("zip")
        if z:
            with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as f:
                for dp, dn, fn in os.walk(self.out):
                    for n in sorted(fn):
                        p = os.path.join(dp, n)
                        f.write(p, os.path.join(os.path.basename(self.out), os.path.relpath(p, self.out)))
            self.log(f"zipped to {z}")

    def go(self):
        st = os.path.join(self.out, "stop.json")
        if os.path.exists(st):
            s = json.load(open(st))
            if not s.get("resumable"):
                self.log(f"the night has stopped: {s['reason']} (not resumable)")
                return s
            os.rename(st, st.replace(".json", f"_{dt.datetime.now().strftime('%H%M%S')}.json"))
        if not self.fetch():
            return self.stop("fetch failed")
        if not self.diagnostics():
            res = json.load(open(st))
        else:
            res = self.rounds()
        if not res.get("resumable"):
            self.finish()
        return res


# ------------------------------------------------------------------------------------------------ helpers

def _quiet(fn, ns, log_file):
    """Run a tool's function with its printout captured into log_file; returns its return value."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        r = fn(ns)
    with open(log_file, "a") as f:
        f.write(buf.getvalue())
    return r


def build_diag(mod, devdir, folder, dry):
    """Dw / Dc built as their tools build them (FF.build(dev, items(), out, shots=4000)); with dry the sentinel at its
    Clifford point (never a device job)."""
    from psf_os import feedforward as FF
    from psf_os.device import Device
    spec = dict(kind="echo_clifford", D=24) if dry else None
    FF.build(Device.load(devdir), mod.items(), folder, shots=4000, sentinel_spec=spec)


def simulate(folder, noise, seed):
    """Dry runs only: noiseless (psf_os.feedforward.run_local) or under an EXAMPLE noise: this file's run_noisy for
    noise with `wait_gamma` / `readout`, the workplace VS's notes/os2_2026-11-18/branch_noise.noisy_run_local for noise
    with `gamma` / `p11` / `p00` (the same model written independently)."""
    from psf_os import feedforward as FF
    if not noise:
        FF.run_local(folder, seed=seed)
    elif any(k in noise for k in ("gamma", "p11", "p00")):
        sys.path.insert(0, os.path.join(NB, "notes", "os2_2026-11-18"))
        import branch_noise as BN
        BN.noisy_run_local(folder, noise, seed=seed)
    else:
        run_noisy(folder, noise, seed=seed)


def run_noisy(folder, noise, seed=20261118):
    """Dry runs only: Aer with an EXAMPLE noise (never fitted to a device): `wait_gamma`, amplitude damping on every
    touched qubit not measured in a layer of top-level measurements, once per layer that is followed by more gates (the
    waits); `readout`, {physical qubit: P(read 0 | |1>)}.
    The sentinel runs noiselessly (it is beside, and too large for a noisy simulation). Writes raw_counts.json and
    submission.json as FF.run_local does."""
    from qiskit import QuantumCircuit, qpy
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, ReadoutError, amplitude_damping_error
    from psf_os import feedforward as FF
    from psf_os.ibm import _stamp
    from psf_os.sim import to_clifford_gates
    job = os.path.join(folder, "job")
    sub = os.path.join(job, "submission.json")
    if os.path.exists(sub):
        raise SystemExit(f"{sub} exists")
    man = json.load(open(os.path.join(job, "manifest.json")))
    circs = qpy.load(open(os.path.join(job, "circuits.qpy"), "rb"))
    roles = [man["cells"][p["cell"]]["role"] for p in man["pubs"]]
    gamma = float(noise.get("wait_gamma", 0.0))
    ro = {int(k): float(v) for k, v in noise.get("readout", {}).items()}
    rows = []
    for k, c in enumerate(circs):
        act = sorted({q for _, qs in FF.walk(c) for q in qs})
        cc = FF.compact(c)
        if roles[k] == "sentinel":
            cl = None if cc.has_control_flow_op() else to_clifford_gates(cc)
            res = AerSimulator(method="stabilizer" if cl is not None else "statevector").run(
                cl if cl is not None else cc, shots=man["shots"], seed_simulator=seed + k).result()
            rows.append(dict(pub=k, counts={key.replace(" ", ""): v for key, v in res.get_counts(0).items()}))
            continue
        nm = NoiseModel()
        if gamma > 0:
            nm.add_all_qubit_quantum_error(amplitude_damping_error(gamma), ["id"])
        for i, q in enumerate(act):
            if q in ro:
                p = ro[q]
                nm.add_readout_error(ReadoutError([[1.0, 0.0], [p, 1 - p]]), [i])
        if gamma > 0:
            # one wait per layer of measurements: after the last of consecutive top-level measurements (barriers in
            # between do not split a layer), if anything but measurements and barriers follows; every qubit not
            # measured in that layer decays
            w = QuantumCircuit(*cc.qregs, *cc.cregs)
            data = list(cc.data)
            layer = set()
            for j, ins in enumerate(data):
                w.append(ins.operation, ins.qubits, ins.clbits)
                if ins.operation.name == "measure":
                    layer.add(cc.find_bit(ins.qubits[0]).index)
                if not layer or ins.operation.name not in ("measure", "barrier"):
                    continue
                rest = [x.operation.name for x in data[j + 1:]]
                nxt = next((x for x in rest if x != "barrier"), None)
                if nxt == "measure":
                    continue
                if any(x not in ("measure", "barrier") for x in rest):
                    for i in range(cc.num_qubits):
                        if i not in layer:
                            w.id(i)
                layer = set()
            cc = w
        sim = AerSimulator(method="density_matrix" if cc.num_qubits <= 10 else "statevector", noise_model=nm)
        res = sim.run(cc, shots=man["shots"], seed_simulator=seed + k, basis_gates=None).result()
        rows.append(dict(pub=k, counts={key.replace(" ", ""): v for key, v in res.get_counts(0).items()}))
    t = _stamp()
    json.dump(dict(job_id=f"local-example-noise-{seed}", submitted=t, local=True, backend=man["fetch"]["backend"],
                   simulator="aer, EXAMPLE noise (dry runs only)", noise=noise), open(sub, "w"), indent=1)
    json.dump(dict(fetched=t, job_id=f"local-example-noise-{seed}", status="DONE (local, example noise)", rows=rows),
              open(os.path.join(job, "raw_counts.json"), "w"))


def predictions(out):
    """The declared predictions, read from the records only (prereg: OS2-1, OS2-2; the OS compounding beside)."""
    import os2_night as O
    rounds = sorted([d for d in os.listdir(out) if d.startswith("r") and d[1:].isdigit() and
                     os.path.exists(os.path.join(out, d, "round_scores.json"))], key=lambda d: int(d[1:]))
    rs = [json.load(open(os.path.join(out, d, "round_scores.json"))) for d in rounds]
    r1 = json.load(open(os.path.join(out, "RULE1.json")))["stacks"]
    p2 = os.path.join(out, "RULE2.json")
    r2 = json.load(open(p2))["stacks"] if os.path.exists(p2) else None
    ran2 = os.path.exists(os.path.join(out, "r2", "round_scores.json"))
    changed = bool(r2 is not None and ran2 and any(r1[str(L)] != r2[str(L)] for L in O.LS))
    last = rs[-1] if rs else None
    over = [L for L, v in last["rows"].items() if v.get("overshoot")] if last else None
    comp = O.compound_rows(rs) if rs else dict(verdict="NOT JUDGEABLE", why="no round")
    return {
        "OS2-1 the rule changes at least one stack between round 1 and round 2":
            "held" if changed else "failed",
        "OS2-2 no L overshoots in the last round run":
            ("held" if not over else "failed") if last else "failed (no round ran)",
        "last_round": last["round"] if last else None, "overshoot_in_last_round": over,
        "beside_os_compounding (not a prediction)": {k: v for k, v in comp.items() if k != "per_L"},
    }


# ------------------------------------------------------------------------------------------------ preflight

def preflight(dry=False, out=None, zip_path=None):
    items = []

    def add(name, ok, detail=""):
        items.append(dict(item=name, ok=bool(ok), detail=str(detail)))

    warnings = []
    for mod in ("qiskit", "qiskit_aer", "qiskit_ibm_runtime", "psf_os"):
        try:
            m = __import__(mod)
            ver = getattr(m, "__version__", "")
            add(f"import {mod}", True, ver)
            if mod in EXPECTED and ver != EXPECTED[mod]:
                warnings.append(f"{mod} {ver}, not the version checked at the workplace ({EXPECTED[mod]}); not a stop")
        except Exception as exc:  # noqa: BLE001
            add(f"import {mod}", False, type(exc).__name__ + (
                '; install it (VPN OFF) with:  python -m pip install "qiskit-aer==0.18.0"' if mod == "qiskit_aer" else ""))
    try:
        import psf_os
        root = os.path.dirname(os.path.dirname(os.path.abspath(psf_os.__file__)))
        head = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", root, "status", "--porcelain", "--untracked-files=no", "--", "psf_os"],
                               capture_output=True, text=True).stdout.strip()
        add("psf_os at 0f57c76", head == PSF_OS_COMMIT, head)
        add("psf_os/ unchanged in its checkout", dirty == "", dirty or "clean")
    except Exception as exc:  # noqa: BLE001
        add("psf_os at 0f57c76", False, type(exc).__name__)
    head = subprocess.run(["git", "-C", NB, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    decl = subprocess.run(["git", "-C", NB, "log", "-1", "--format=%H", "--", DECLARATION], capture_output=True,
                          text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", NB, "status", "--porcelain", "--untracked-files=no"], capture_output=True,
                           text=True).stdout.strip()
    if dry:
        add("notebook HEAD is the declaration's commit", True, f"skipped (dry); HEAD {head[:8]}")
    else:
        add("notebook HEAD is the declaration's commit", bool(decl) and head == decl,
            f"HEAD {head[:8]}, {DECLARATION} last changed in {decl[:8] or 'no commit'}")
        add("notebook checkout unchanged", dirty == "", dirty or "clean")
    for f in ("daily_fetch.py", "wait_night.py", "ctrl_night.py", "os_night.py", "os2_night.py", "job_timing.py"):
        add(f"gpu/{f}", os.path.exists(os.path.join(HERE, f)))
    add("Python >= 3.11", sys.version_info >= (3, 11), sys.version.split()[0])
    if not dry:
        # the saved account: its file is looked for, never opened (qiskit-ibm-runtime's default place)
        acct = os.path.join(os.path.expanduser("~"), ".qiskit", "qiskit-ibm.json")
        add("a saved IBM account exists (the file only, not read)", os.path.exists(acct), "")
    if out is not None:
        add("OUT does not exist yet", not os.path.exists(out), "")
    if zip_path is not None:
        zd = os.path.dirname(os.path.abspath(zip_path))
        add("the zip's folder is writable", os.path.isdir(zd) and os.access(zd, os.W_OK), "")
        add("the zip does not exist yet", not os.path.exists(zip_path), "")
    ok = all(x["ok"] for x in items)
    for x in items:
        print(f"{'ok  ' if x['ok'] else 'FAIL'} {x['item']}: {x['detail']}")
    for w in warnings:
        print(f"NOTE {w}")
        items.append(dict(item="version", ok=True, detail=w))
    print("PREFLIGHT PASS" if ok else "PREFLIGHT FAIL")
    return ok, items


# ------------------------------------------------------------------------------------------------ verify

def _first_difference(a, b, path=""):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                return f"{path}/{k} missing on one side"
            d = _first_difference(a[k], b[k], f"{path}/{k}")
            if d:
                return d
        return None
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return f"{path} length {len(a)} != {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            d = _first_difference(x, y, f"{path}[{i}]")
            if d:
                return d
        return None
    if isinstance(a, float) or isinstance(b, float):
        try:
            return None if abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b)) else f"{path}: {a} != {b}"
        except TypeError:
            pass
    return None if a == b else f"{path}: {a!r} != {b!r}"


def _same_job(rec, new):
    """circuits.qpy byte for byte; manifest.json equal but for its 'written' time."""
    a, b = os.path.join(rec, "job"), os.path.join(new, "job")
    if open(os.path.join(a, "circuits.qpy"), "rb").read() != open(os.path.join(b, "circuits.qpy"), "rb").read():
        return "circuits.qpy differs"
    ma, mb = (json.load(open(os.path.join(x, "manifest.json"))) for x in (a, b))
    ma.pop("written", None)
    mb.pop("written", None)
    return _first_difference(ma, mb)


def _rescore(rec, fn, scores, tmp, extra=()):
    d = os.path.join(tmp, os.path.basename(rec) + "_rescore")
    shutil.copytree(os.path.join(rec, "job"), os.path.join(d, "job"))
    shutil.copytree(os.path.join(rec, "runs"), os.path.join(d, "runs"))
    for f in ("build.json",) + tuple(extra):
        shutil.copy2(os.path.join(rec, f), os.path.join(d, f))
    _quiet(fn, types.SimpleNamespace(out=d), os.path.join(tmp, "rescore.txt"))
    return _first_difference(json.load(open(os.path.join(rec, scores))), json.load(open(os.path.join(d, scores))))


def verify(out, resim=False):
    import ctrl_night as CN
    import os2_night as O
    import os_night as ON
    import wait_night as WN
    out = os.path.abspath(out)
    cfg = json.load(open(os.path.join(out, "run.json")))
    devdir = os.path.join(out, "fetch_in", cfg["device"], "dev")
    lines, bad = [], []

    def note(what, diff):
        lines.append(f"{'SAME     ' if diff is None else 'DIFFERENT'} {what}" + ("" if diff is None else f": {diff}"))
        if diff is not None:
            bad.append(what)

    tmp = tempfile.mkdtemp(prefix="os2_verify_")
    try:
        for tag, mod, scores in (("dw", WN, "wait_scores.json"), ("dc", CN, "ctrl_scores.json")):
            rec = os.path.join(out, tag)
            if not os.path.isdir(rec):
                continue
            new = os.path.join(tmp, tag)
            build_diag(mod, devdir, new, cfg["dry"])
            note(f"{tag} job rebuilt", _same_job(rec, new) if os.path.isdir(os.path.join(rec, "job")) else
                 "no job/ recorded")
            if os.path.exists(os.path.join(rec, scores)):
                note(f"{tag} re-scored", _rescore(rec, mod.score, scores, tmp))
        if os.path.exists(os.path.join(out, "os_rule.json")):
            r = os.path.join(tmp, "os_rule.json")
            _quiet(ON.rule, types.SimpleNamespace(dw=os.path.join(out, "dw"), dc=os.path.join(out, "dc"), rule_json=r),
                   os.path.join(tmp, "x.txt"))
            note("os_rule.json re-ruled", _first_difference(json.load(open(os.path.join(out, "os_rule.json"))),
                                                            json.load(open(r))))
            r1 = os.path.join(tmp, "RULE1.json")
            _quiet(O.round1, types.SimpleNamespace(os_rule=os.path.join(out, "os_rule.json"), out_rule=r1, device=None,
                                                   diag=[os.path.join(out, "dw"), os.path.join(out, "dc")]),
                   os.path.join(tmp, "x.txt"))
            note("RULE1.json", _first_difference(json.load(open(os.path.join(out, "RULE1.json"))), json.load(open(r1))))
        k = 1
        while os.path.exists(os.path.join(out, f"RULE{k}.json")):
            rec = os.path.join(out, f"r{k}")
            if not os.path.isdir(rec):
                break
            new = os.path.join(tmp, f"r{k}")
            _quiet(O.build, types.SimpleNamespace(devdir=devdir, out=new, rule_json=os.path.join(out, f"RULE{k}.json"),
                                                  dry_clifford_sentinel=cfg["dry"]), os.path.join(tmp, "x.txt"))
            if os.path.isdir(os.path.join(rec, "job")):
                note(f"r{k} job rebuilt", _same_job(rec, new))
            else:
                note(f"r{k} job rebuilt (not sent)", _same_job(dict_path(rec), new))
            if os.path.exists(os.path.join(rec, "round_scores.json")):
                note(f"r{k} re-scored", _rescore(rec, O.score, "round_scores.json", tmp, extra=("rule.json",)))
                nxt = os.path.join(out, f"RULE{k + 1}.json")
                if os.path.exists(nxt):
                    rn = os.path.join(tmp, f"RULE{k + 1}.json")
                    _quiet(O.rule, types.SimpleNamespace(out_rule=rn, rounds=[os.path.join(out, f"r{j}")
                                                                              for j in range(1, k + 1)],
                                                         k_max=cfg["k_max"]), os.path.join(tmp, "x.txt"))
                    note(f"RULE{k + 1}.json re-ruled", _first_difference(json.load(open(nxt)), json.load(open(rn))))
            k += 1
        if resim and cfg["dry"]:
            for d in sorted(os.listdir(out)):
                rec = os.path.join(out, d)
                if not os.path.exists(os.path.join(rec, "job", "raw_counts.json")):
                    continue
                cp = os.path.join(tmp, d + "_resim")
                shutil.copytree(os.path.join(rec, "job"), os.path.join(cp, "job"),
                                ignore=shutil.ignore_patterns("raw_counts.json", "submission.json"))
                shutil.copytree(os.path.join(rec, "runs"), os.path.join(cp, "runs"))
                simulate(cp, cfg.get("noise"), dry_seed(d))
                a_ = json.load(open(os.path.join(rec, "job", "raw_counts.json")))["rows"]
                b_ = json.load(open(os.path.join(cp, "job", "raw_counts.json")))["rows"]
                note(f"{d} re-simulated (dry, seed {dry_seed(d)})", _first_difference(a_, b_))
        pp = os.path.join(out, "predictions.json")
        if os.path.exists(pp):
            note("predictions re-read", _first_difference(json.load(open(pp)), predictions(out)))
        sp = os.path.join(out, "stop.json")
        if os.path.exists(sp):
            note("stop reason", _first_difference(_stop_reason(out, cfg), json.load(open(sp))["reason"]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n".join(lines))
    print("SAME" if not bad else f"DIFFERENT ({len(bad)}: {', '.join(bad)})")
    return not bad


def dict_path(rec):
    """A round folder whose job was not sent keeps it as job_NOT_SENT: compare that one."""
    tmp = tempfile.mkdtemp(prefix="os2_ns_")
    os.symlink(os.path.join(rec, "job_NOT_SENT"), os.path.join(tmp, "job"))
    return tmp


def _stop_reason(out, cfg):
    """The stop reason recomputed from the records (the same text the run writes)."""
    k = 1
    while os.path.exists(os.path.join(out, f"RULE{k + 1}.json")):
        k += 1
    R = json.load(open(os.path.join(out, f"RULE{k}.json")))
    if R.get("stop"):
        return f"the rule: {R['stop_reason']} (after round {k - 1})"
    rec = os.path.join(out, f"r{k}")
    if os.path.isdir(os.path.join(rec, "job_NOT_SENT")):
        if os.path.exists(os.path.join(rec, "check_ok")):
            tot = 0.0
            for d in sorted(os.listdir(out)):
                p = os.path.join(out, d)
                if os.path.exists(os.path.join(p, "build.json")):
                    tot += json.load(open(os.path.join(p, "build.json")))["qpu_seconds_model"]
            return (f"budget: the night would take {tot:.1f} s by the model with r{k}, over {cfg['budget']:.0f} s; r{k} "
                    "not sent (job_NOT_SENT)")
        return f"r{k}: check FAIL (check.txt); not sent"
    return json.load(open(os.path.join(out, "stop.json")))["reason"]


# ------------------------------------------------------------------------------------------------ main

def main():
    import os2_night as O
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("preflight")
    p.add_argument("--dry", action="store_true")
    p.add_argument("--out", help="the night's OUT, to check it does not exist yet")
    p.add_argument("--zip", help="the zip file, to check its folder is writable")
    g = sub.add_parser("go")
    g.add_argument("out")
    g.add_argument("--zip", help="the zip file the night's OUT is written to (device runs; required there)")
    g.add_argument("--dry", metavar="DEVDIR", help="a dry run on this device record: local simulation, no IBM")
    g.add_argument("--noise", help="dry only: an EXAMPLE noise JSON (wait_gamma, readout {physical qubit: P(0|1)})")
    g.add_argument("--k-max", type=int, help="dry only")
    g.add_argument("--budget", type=float, help="dry only")
    r = sub.add_parser("resume")
    r.add_argument("out")
    r.add_argument("--zip")
    v = sub.add_parser("verify")
    v.add_argument("out")
    v.add_argument("--resim", action="store_true", help="dry runs: also re-simulate every job with its recorded seed")
    a = ap.parse_args()
    if a.cmd == "preflight":
        ok, _ = preflight(a.dry, out=a.out, zip_path=a.zip)
        return 0 if ok else 1
    if a.cmd == "verify":
        return 0 if verify(a.out, a.resim) else 1
    if a.cmd == "go":
        if not a.dry and (a.noise or a.k_max or a.budget):
            raise SystemExit("--noise, --k-max and --budget are for dry runs only")
        if not a.dry and not a.zip:
            raise SystemExit("--zip is required for a device run")
        if os.path.exists(a.out):
            raise SystemExit(f"{a.out} exists: use resume")
        ok, items = preflight(bool(a.dry), out=a.out, zip_path=a.zip)
        if not ok:
            raise SystemExit("preflight FAIL: nothing started")
        os.makedirs(a.out)
        cfg = dict(dry=bool(a.dry), dry_devdir=os.path.abspath(a.dry) if a.dry else None,
                   noise=json.load(open(a.noise)) if a.noise else None, k_max=a.k_max or O.K_MAX,
                   budget=a.budget or O.BUDGET_S, zip=os.path.abspath(a.zip) if a.zip else None, started=now(),
                   preflight=items, psf_os=PSF_OS_COMMIT, device=None)
        json.dump(cfg, open(os.path.join(a.out, "run.json"), "w"), indent=1)
        n = Night(a.out)
    else:
        n = Night(a.out)
        c = n.cfg()
        if a.zip:
            c["zip"] = os.path.abspath(a.zip)
            json.dump(c, open(n.cfg_file, "w"), indent=1)
        ok, _ = preflight(c["dry"])
        if not ok:
            raise SystemExit("preflight FAIL: not resumed")
    res = n.go()
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
