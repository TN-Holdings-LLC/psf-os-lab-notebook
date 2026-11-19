"""Scenario tests of the loop runner on copies of a finished dry night (workplace VS Claude, 2026-11-19; instruction
"その2" item 1). The runner is driven only through `gpu/os_loop.py go / resume / verify`; the copies are cut back or
damaged here, and the outcome is read from the files.

  python vs_scenarios.py NIGHT_DONE WORK DEVDIR NOISE.json

S1 resume never sends twice: r2 cut back to "submitted, no result" (raw_counts moved away) -> resume stops resumable,
   r2's submission.json unchanged and no new local run of r2; result put back -> resume finishes with every rule,
   score, prediction and stop the same as the uninterrupted night.
S2 check FAIL: r2 cut back to "built, not checked", one ff arm's conditionals removed -> resume stops on the check,
   job_NOT_SENT, no submission, nothing after.
S3 build refused: r2 cut back to "RULE2 written", L1's stack replaced by an unknown layer -> resume stops, no r2 job.
S4 round limit: a new night with --k-max 1 stops after round 1 by "round limit".
S5 budget: a new night with --budget 90 stops before building the round that would pass it; the estimate written
   before each round equals the build's model seconds (in the finished night).
S6 ledger: other calibration time, other device, family disagreeing at one L -> not used, with the reason in RULE1.json.
S7 verify: the finished night SAME; a copy with 50 counts moved in r1 DIFFERENT.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
TOOL = os.path.join(NB, "gpu", "os_loop.py")
RES = []


def report(sec, name, ok, note=""):
    RES.append(dict(section=sec, name=name, ok=bool(ok), note=note))
    print(f"{sec} {'PASS' if ok else 'FAIL'}  {name}" + (f"  ({note})" if note else ""), flush=True)


def run(*args):
    r = subprocess.run([sys.executable, TOOL, *args], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None


def rm(*ps):
    for p in ps:
        if os.path.isdir(p):
            shutil.rmtree(p)
        elif os.path.exists(p):
            os.remove(p)


def copy_night(src, dst):
    rm(dst)
    shutil.copytree(src, dst)
    cfg = json.load(open(os.path.join(dst, "run.json")))
    cfg["ledger"] = None                       # a copy never writes into the original's ledger
    json.dump(cfg, open(os.path.join(dst, "run.json"), "w"), indent=1)
    return dst


def cut_after(night, k):
    """Remove everything from RULE{k+1} on and the finish files (the night as it was when round k was running)."""
    j = k + 1
    while os.path.exists(os.path.join(night, f"RULE{j}.json")) or os.path.isdir(os.path.join(night, f"r{j}")):
        rm(os.path.join(night, f"RULE{j}.json"), os.path.join(night, f"r{j}"), os.path.join(night, f"budget_r{j}.json"),
           os.path.join(night, f"build_r{j}.txt"))
        j += 1
    rm(*[os.path.join(night, f) for f in ("stop.json", "compound.json", "predictions.json", "job_timing.json",
                                          "ledger_written")])


def stop_of(night):
    p = os.path.join(night, "stop.json")
    return json.load(open(p)) if os.path.exists(p) else {}


def records(night):
    """Every rule, round score, prediction and the stop reason, without time stamps."""
    out = {}
    for f in sorted(os.listdir(night)):
        if f.startswith("RULE") or f in ("predictions.json", "compound.json"):
            out[f] = json.load(open(os.path.join(night, f)))
    for d in sorted(os.listdir(night)):
        p = os.path.join(night, d, "round_scores.json")
        if os.path.exists(p):
            out[d] = json.load(open(p))
    out["stop"] = stop_of(night).get("reason")
    return out


def s1(done, work):
    n = copy_night(done, os.path.join(work, "s1"))
    cut_after(n, 2)
    rm(os.path.join(n, "r2", "round_scores.json"), os.path.join(n, "r2", "score.txt"))
    raw = os.path.join(n, "r2", "job", "raw_counts.json")
    shutil.move(raw, raw + ".aside")
    sub0 = sha(os.path.join(n, "r2", "job", "submission.json"))
    runs0 = open(os.path.join(n, "run_log.txt")).read().count("r2: run locally")
    rc, out = run("resume", n)
    st = stop_of(n)
    sub1 = sha(os.path.join(n, "r2", "job", "submission.json"))
    runs1 = open(os.path.join(n, "run_log.txt")).read().count("r2: run locally")
    # resume skips submit() when submission.json exists, so no "already submitted" line is written: the test is the
    # submission file unchanged (and equal to the uninterrupted night's) and no new local run of r2
    sub_done = sha(os.path.join(done, "r2", "job", "submission.json"))
    report("S1", "result missing: resume stops resumable, r2 not sent again", st.get("resumable") and sub0 == sub1
           == sub_done and runs1 == runs0, f"{st.get('reason', '')[:60]}; submission unchanged {sub0 == sub1 == sub_done}, "
           f"r2 local runs {runs0} -> {runs1}")
    shutil.move(raw + ".aside", raw)
    rc, out = run("resume", n)
    a, b = records(done), records(n)
    diff = [k for k in set(a) | set(b) if a.get(k) != b.get(k)]
    runs2 = open(os.path.join(n, "run_log.txt")).read().count("r2: run locally")
    report("S1", "result back: resume finishes the same as the uninterrupted night; r2 run once in all",
           not diff and runs2 == runs0 == 1, f"differ: {diff or '-'}; r2 local runs {runs2}")


def s2(done, work):
    from qiskit import qpy
    n = copy_night(done, os.path.join(work, "s2"))
    cut_after(n, 2)
    r2 = os.path.join(n, "r2")
    rm(os.path.join(r2, "round_scores.json"), os.path.join(r2, "score.txt"), os.path.join(r2, "check_ok"),
       os.path.join(r2, "check.txt"), os.path.join(r2, "job", "submission.json"), os.path.join(r2, "job", "raw_counts.json"))
    p = os.path.join(r2, "job", "circuits.qpy")
    cs = qpy.load(open(p, "rb"))
    m = json.load(open(os.path.join(r2, "job", "manifest.json")))
    names = [c["name"] for c in m["cells"] for _ in range(c["points"])]
    k = next(i for i, nm in enumerate(names) if nm.startswith("ff_") and not nm.endswith(("_off", "_floor"))
             and nm != "ff_dr" and any(ins.operation.name == "if_else" for ins in cs[i].data))
    c = cs[k].copy_empty_like()
    for ins in cs[k].data:
        if ins.operation.name != "if_else":
            c.append(ins.operation, ins.qubits, ins.clbits)
    cs[k] = c
    with open(p, "wb") as f:
        qpy.dump(cs, f)
    rc, out = run("resume", n)
    st = stop_of(n)
    report("S2", f"check FAIL ({names[k]} without its conditionals): stopped, job_NOT_SENT, nothing after",
           "check FAIL" in st.get("reason", "") and os.path.isdir(os.path.join(r2, "job_NOT_SENT"))
           and not os.path.exists(os.path.join(r2, "job_NOT_SENT", "submission.json"))
           and not os.path.exists(os.path.join(n, "RULE3.json")), st.get("reason", "")[:80])


def s3(done, work):
    n = copy_night(done, os.path.join(work, "s3"))
    cut_after(n, 2)
    rm(os.path.join(n, "r2"), os.path.join(n, "budget_r2.json"), os.path.join(n, "build_r2.txt"))
    R = json.load(open(os.path.join(n, "RULE2.json")))
    R["stacks"]["1"] = ["P9"]
    json.dump(R, open(os.path.join(n, "RULE2.json"), "w"), indent=1)
    rc, out = run("resume", n)
    st = stop_of(n)
    report("S3", "build refused (L1 stack P9): stopped, no r2 job", "refused" in st.get("reason", "")
           and not os.path.isdir(os.path.join(n, "r2", "job")), st.get("reason", "")[:90])


def s4(work, dev, noise):
    n = os.path.join(work, "s4")
    rm(n)
    run("go", n, "--dry", dev, "--noise", noise, "--k-max", "1")
    st = stop_of(n)
    report("S4", "--k-max 1: stops after round 1 by the round limit, no r2", "round limit" in st.get("reason", "")
           and not os.path.isdir(os.path.join(n, "r2")), st.get("reason", "")[:80])


def s5(done, work, dev, noise):
    n = os.path.join(work, "s5")
    rm(n)
    run("go", n, "--dry", dev, "--noise", noise, "--budget", "90")
    st = stop_of(n)
    built = sorted(d for d in os.listdir(n) if d.startswith("r") and d[1:].isdigit() and os.path.isdir(os.path.join(n, d, "job")))
    report("S5", "--budget 90: stops before the round that would pass it, nothing built past it",
           st.get("reason", "").startswith("budget") and all(
               json.load(open(os.path.join(n, f"budget_r{d[1:]}.json")))["spent_s"] + json.load(
                   open(os.path.join(n, f"budget_r{d[1:]}.json")))["estimate_s"] <= 90 + 1e-9 for d in built),
           f"{st.get('reason', '')[:90]}; rounds built {built}")
    rows = []
    for f in sorted(os.listdir(done)):
        if f.startswith("budget_r"):
            k = f[len("budget_r"):-5]
            est = json.load(open(os.path.join(done, f)))["estimate_s"]
            real = json.load(open(os.path.join(done, f"r{k}", "build.json")))["qpu_seconds_model"]
            rows.append((k, est, real))
    report("S5", "the estimate before each round equals the round's build", all(abs(e - r) < 1e-9 for _, e, r in rows),
           str(rows))


def s6(done, work, dev, noise):
    led = json.load(open(os.path.join(os.path.dirname(done), "ledger.json")))
    cases = {
        "calibration": dict(calibration_time="2026-11-17 10:40:00+01:00"),
        "device": dict(device="ibm_fez"),
        "family": None,
    }
    for name, change in cases.items():
        e = json.loads(json.dumps(led[-1]))
        if change:
            e.update(change)
        else:
            e["last_stacks"]["2"] = ["P0"]
        lp = os.path.join(work, f"ledger_{name}.json")
        json.dump([e], open(lp, "w"), indent=1)
        n = os.path.join(work, f"s6_{name}")
        rm(n)
        run("go", n, "--dry", dev, "--noise", noise, "--k-max", "1", "--ledger", lp)
        R1 = json.load(open(os.path.join(n, "RULE1.json")))
        L = R1["ledger"]
        if name == "family":
            ok = (L["per_key"].get("2", "").startswith("diagnostics disagree") and R1["stacks"]["2"] == R1["diagnostics_stacks"]["2"]
                  and L["used"])
            note = L["per_key"].get("2", "")[:90]
        else:
            ok = (not L["used"]) and name in L["why"] and R1["stacks"] == R1["diagnostics_stacks"]
            note = L["why"][:90]
        report("S6", f"ledger with another {name}: not used there, reason in RULE1.json", ok, note)


def s7(done, work):
    rc, out = run("verify", done)
    report("S7", "verify on the finished night: SAME", "DIFFERENT" not in out and "SAME" in out,
           out.strip().splitlines()[-1][:90] if out.strip() else "")
    n = copy_night(done, os.path.join(work, "s7"))
    p = os.path.join(n, "r1", "job", "raw_counts.json")
    d = json.load(open(p))
    cnt = d["rows"][3]["counts"]
    ks = sorted(cnt, key=lambda k: -cnt[k])
    cnt[ks[0]] -= 50
    cnt[ks[1]] += 50
    json.dump(d, open(p, "w"))
    rc, out = run("verify", n)
    report("S7", "verify with 50 counts moved in r1: DIFFERENT", "DIFFERENT" in out,
           next((l for l in out.splitlines() if "DIFFERENT" in l), "")[:90])


def main():
    done, work, dev, noise = sys.argv[1:5]
    if len(sys.argv) > 5 and sys.argv[5] == "s1":
        os.makedirs(work, exist_ok=True)
        s1(done, work)
        json.dump(RES, open(os.path.join(work, "vs_scenarios_s1.json"), "w"), indent=1)
        return
    os.makedirs(work, exist_ok=True)
    s1(done, work)
    s2(done, work)
    s3(done, work)
    s4(work, dev, noise)
    s5(done, work, dev, noise)
    s6(done, work, dev, noise)
    s7(done, work)
    print(f"{len(RES)} checks, {sum(not r['ok'] for r in RES)} FAIL")
    json.dump(RES, open(os.path.join(work, "vs_scenarios.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
