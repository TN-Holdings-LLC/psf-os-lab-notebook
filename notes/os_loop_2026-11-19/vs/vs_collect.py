"""collect as values (19c), with IBM replaced by fakes (workplace VS Claude, 2026-11-19; instruction "その3"): nothing
here can reach IBM. psf_os.ibm.job_state on every status form; psf_os.ibm.collect with a fake service (it writes
job/collect_status.json); psf_os.loop.Night.collect and run_job with the collect subprocess replaced, for each value
of collect_status.json, a missing file, and DONE without raw counts: which ones stop, and whether resumably.

  python vs_collect.py WORK
"""
import enum
import json
import os
import shutil
import sys
import types

from psf_os import ibm
from psf_os import loop as LP

RES = []


def report(name, ok, note=""):
    RES.append(dict(name=name, ok=bool(ok), note=note))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({note})" if note else ""), flush=True)


class JS(enum.Enum):
    DONE = 1
    QUEUED = 2
    RUNNING = 3
    ERROR = 4
    CANCELLED = 5
    INITIALIZING = 6
    VALIDATING = 7


def s_job_state():
    cases = [(JS.DONE, "DONE"), ("JobStatus.DONE", "DONE"), ("DONE", "DONE"), ("done", "DONE"),
             (JS.QUEUED, "WAIT"), ("RUNNING", "WAIT"), (JS.INITIALIZING, "WAIT"), (JS.VALIDATING, "WAIT"),
             (JS.ERROR, "FAILED"), ("CANCELLED", "FAILED"), ("CANCELED", "FAILED"), ("JobStatus.FAILED", "FAILED"),
             ("COMPLETED", "UNKNOWN"), ("", "UNKNOWN"), (None, "UNKNOWN"), ("DONE_WITH_ERRORS", "UNKNOWN")]
    bad = [(c, ibm.job_state(c), w) for c, w in cases if ibm.job_state(c) != w]
    report("job_state: 16 status forms map to DONE / WAIT / FAILED / UNKNOWN as written", not bad, str(bad) or "all as expected")


class FakeResult:
    def join_data(self):
        return types.SimpleNamespace(get_counts=lambda: {"00": 3, "11": 1})


class FakeJob:
    def __init__(self, status, result_fails=False):
        self._s, self._f = status, result_fails

    def status(self):
        return self._s

    def result(self):
        if self._f:
            raise RuntimeError("result fetch failed (fake)")
        return [FakeResult()]

    def metrics(self):
        return {"usage": {"quantum_seconds": 1}}


class FakeSvc:
    def __init__(self, job):
        self._j = job

    def job(self, jid):
        return self._j


def jobdir(work, name):
    d = os.path.join(work, name, "job")
    shutil.rmtree(os.path.join(work, name), ignore_errors=True)
    os.makedirs(d)
    json.dump(dict(job_id=f"fake-{name}"), open(os.path.join(d, "submission.json"), "w"))
    return d


def s_ibm_collect(work):
    for st, want, raw in (("DONE", "DONE", True), ("QUEUED", "WAIT", False), ("ERROR", "FAILED", False),
                          ("CANCELLED", "FAILED", False), ("COMPLETED", "UNKNOWN", False)):
        d = jobdir(work, f"ibm_{st}")
        ibm.collect(FakeSvc(FakeJob(st)), d, wait_s=0)
        cs = json.load(open(os.path.join(d, "collect_status.json")))
        has_raw = os.path.exists(os.path.join(d, "raw_counts.json"))
        report(f"ibm.collect, status {st}: collect_status.json state {want}, raw_counts {'written' if raw else 'not written'}",
               cs["state"] == want and has_raw == raw, f"state {cs['state']}, raw {has_raw}")
    d = jobdir(work, "ibm_DONE_result_fails")
    try:
        ibm.collect(FakeSvc(FakeJob("DONE", result_fails=True)), d, wait_s=0)
    except RuntimeError:
        pass
    cs = json.load(open(os.path.join(d, "collect_status.json")))
    report("ibm.collect, DONE but the result fetch fails: collect_status.json says DONE, no raw_counts",
           cs["state"] == "DONE" and not os.path.exists(os.path.join(d, "raw_counts.json")), f"state {cs['state']}")


class Exp:
    name, k_max, budget_s, order = "fake", 4, 240.0, ["dev"]

    def dry_seed(self, tag):
        return 1


def night(work, name, status_json, write_raw=False):
    out = os.path.join(work, name)
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(os.path.join(out, "r1", "job"))
    json.dump(dict(dry=False, k_max=4, budget=240.0, rungs=["M", "F"], device="dev"), open(os.path.join(out, "run.json"), "w"))
    json.dump(dict(job_id="fake"), open(os.path.join(out, "r1", "job", "submission.json"), "w"))
    open(os.path.join(out, "r1", "check_ok"), "w").write("x\n")

    def fake_run(cmd, capture_output=True, text=True):
        assert cmd[1:4] == ["-m", "psf_os", "collect"], cmd           # only collect may be called here
        job = cmd[cmd.index("--job") + 1]
        if status_json is not None:
            json.dump(status_json, open(os.path.join(job, "collect_status.json"), "w"))
        if write_raw:
            json.dump(dict(rows=[]), open(os.path.join(job, "raw_counts.json"), "w"))
        return types.SimpleNamespace(stdout="fake collect", stderr="", returncode=0)
    return LP.Night(out, Exp()), fake_run


def s_night_collect(work):
    cases = [
        ("WAIT", dict(state="WAIT", status="QUEUED"), "WAIT", True),
        ("FAILED", dict(state="FAILED", status="ERROR"), "FAILED (ERROR)", False),
        ("UNKNOWN", dict(state="UNKNOWN", status="COMPLETED"), "UNKNOWN (COMPLETED)", False),
        ("DONE_no_raw", dict(state="DONE", status="DONE"), "UNKNOWN (DONE but no raw_counts.json)", False),
        ("no_status_file", None, "UNKNOWN (no collect_status.json", False),
    ]
    real = LP.subprocess.run
    try:
        for name, sj, want, resumable in cases:
            n, fake = night(work, f"night_{name}", sj)
            LP.subprocess.run = fake
            got = n.collect(os.path.join(n.out, "r1"))
            r = n.run_job(os.path.join(n.out, "r1"), lambda f: True, lambda f: None)
            st = json.load(open(os.path.join(n.out, "stop.json")))
            sent_again = False                        # submit() is never reached: submission.json exists
            report(f"Night.collect {name}: '{got[:40]}', run_job stops {'resumable' if st['resumable'] else 'not resumable'}",
                   got.startswith(want) and st["resumable"] == resumable and not sent_again, st["reason"][:90])
        n, fake = night(work, "night_DONE", dict(state="DONE", status="DONE"), write_raw=True)
        LP.subprocess.run = fake
        got = n.collect(os.path.join(n.out, "r1"))
        report("Night.collect DONE with raw_counts: DONE", got == "DONE", got)
    finally:
        LP.subprocess.run = real


def main():
    work = sys.argv[1]
    os.makedirs(work, exist_ok=True)
    s_job_state()
    s_ibm_collect(work)
    s_night_collect(work)
    print(f"{len(RES)} checks, {sum(not r['ok'] for r in RES)} FAIL")
    json.dump(RES, open(os.path.join(work, "vs_collect.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
