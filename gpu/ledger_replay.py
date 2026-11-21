"""The loop's ledger path checked by replaying recorded nights (home VS Claude, 2026-11-21; home instruction
"台帳の道を記録の再生で確かめる"; no device). The declared tools gpu/os_loop.py and gpu/os_loop_paired.py are imported
read only; psf-os at ledger-replay-2026-11-21 (`start(..., replay_from=RECORD)`): a dry night whose jobs are answered
from the record's raw counts, stopping with "記録にない" when a circuit is not in the record.

  python gpu/ledger_replay.py WORK            every case (a) to (d) into WORK, summary WORK/summary.json and .txt

Cases:
  (a) results/loop-paired-night-2026-11-20 with a hand-made ledger line on its device and calibration time, stacks
      the night's final incumbents (L1 P2+M, L2 P0, L3 P2+M)
  (b) results/loop-night-2026-11-19 (the rule without pairs) with a ledger line of its own calibration time and its
      final stacks
  (c) the ledger not used: another device, another calibration, a broken file, a line without one of the L
  (d) each record replayed with the ledger it read that night (its RULE1's ledger_last): every RULE file and the stop
      reason against the record
"""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)

PAIRED = os.path.join(NB, "results", "loop-paired-night-2026-11-20")
PLAIN = os.path.join(NB, "results", "loop-night-2026-11-19")


def exp_of(record):
    if record == PAIRED:
        import os_loop_paired as OP
        return OP.PairedRusLoop(), True
    import os_loop as OL
    return OL.RusLoop(), False


def devdir_of(record):
    cfg = json.load(open(os.path.join(record, "run.json")))
    return os.path.join(record, "fetch_in", cfg["device"], "dev"), cfg


def calibration_of(devdir):
    d = json.load(open(os.path.join(devdir, "device.json")))
    return (d.get("source") or {}).get("calibration_time")


def night(work, name, record, ledger_lines=None, ledger_text=None):
    """One replayed night. ledger_lines: a list written as the ledger; ledger_text: raw text (a broken file)."""
    from psf_os import loop as LP
    out = os.path.join(work, name)
    if os.path.exists(out):
        os.makedirs(os.path.join(work, "_to_delete"), exist_ok=True)
        shutil.move(out, os.path.join(work, "_to_delete", f"{name}_{len(os.listdir(os.path.join(work, '_to_delete')))}"))
    os.makedirs(os.path.join(work, "ledgers"), exist_ok=True)
    led = None
    if ledger_lines is not None or ledger_text is not None:
        led = os.path.join(work, "ledgers", f"{name}.json")
        open(led, "w").write(ledger_text if ledger_text is not None else json.dumps(ledger_lines, indent=1))
    exp, paired = exp_of(record)
    dev, cfg = devdir_of(record)
    extra = {"climb_on_kept": True} if cfg.get("climb_on_kept") else {}
    n = LP.start(out, exp, dry_devdir=dev, ledger=led, paired=paired, replay_from=record, extra=extra)
    res = n.go()
    return out, res


def summary_of(out, record):
    R1 = json.load(open(os.path.join(out, "RULE1.json"))) if os.path.exists(os.path.join(out, "RULE1.json")) else {}
    led = R1.get("ledger", {})
    st = json.load(open(os.path.join(out, "stop.json")))
    jobs = {}
    for d in sorted(os.listdir(out)):
        p = os.path.join(out, d, "replay.json")
        if os.path.exists(p):
            r = json.load(open(p))
            jobs[d] = dict(primary=r["primary"], test_cells_from=r["test_cells_from"],
                           one_recorded_job=r["one_recorded_job"])
    rules = sorted(f for f in os.listdir(out) if f.startswith("RULE") and f.endswith(".json"))
    return dict(ledger_used=led.get("used"), ledger_why=led.get("why"), per_key=led.get("per_key"),
                round1_stacks=R1.get("stacks"), round1_candidates=R1.get("candidates"), round1_steps=R1.get("steps"),
                diagnostics_stacks=R1.get("diagnostics_stacks"), stop=st["reason"],
                replay_missing=bool(st.get("replay_missing")), jobs=jobs, rules=rules,
                stacks_per_rule={f: json.load(open(os.path.join(out, f))).get("stacks") for f in rules})


def against_record(out, record):
    """Every RULE file of the record, byte for byte and by content; the stop reason."""
    rows = {}
    for f in sorted(os.listdir(record)):
        if f.startswith("RULE") and f.endswith(".json"):
            a = open(os.path.join(record, f), "rb").read()
            p = os.path.join(out, f)
            b = open(p, "rb").read() if os.path.exists(p) else None
            if a == b:
                rows[f] = "bytes SAME"
            elif b is None:
                rows[f] = "missing"
            else:
                # beside: the same file without the ledger's own fields (the ledger read differs by design in (c))
                ja, jb = json.loads(a), json.loads(b)
                for j in (ja, jb):
                    for k in ("ledger", "ledger_last"):
                        j.pop(k, None)
                rows[f] = "DIFFERENT" + (" (the same without the ledger's fields)" if ja == jb else "")
    extra = sorted(set(f for f in os.listdir(out) if f.startswith("RULE")) - set(rows))
    sa = json.load(open(os.path.join(record, "stop.json")))["reason"]
    sb = json.load(open(os.path.join(out, "stop.json")))["reason"]
    rows["stop reason"] = "SAME" if sa == sb else f"DIFFERENT ({sa!r} / {sb!r})"
    if extra:
        rows["RULE files not in the record"] = extra
    return rows


def main(work):
    from psf_os import loop as LP
    os.makedirs(work, exist_ok=True)
    out = {}
    for rec, tag in ((PAIRED, "paired1120"), (PLAIN, "loop1119")):
        dev, cfg = devdir_of(rec)
        cal = calibration_of(dev)
        R1 = json.load(open(os.path.join(rec, "RULE1.json")))
        final = json.load(open(os.path.join(rec, "os-ledger_after.json")))[-1]
        # the final stacks as that night wrote them into its ledger line
        fin = final["last_stacks"]
        line = dict(night=f"hand-made for the replay ({tag})", device=cfg["device"], calibration_time=cal,
                    rungs=list(cfg["rungs"]), last_stacks=fin, **({"paired": True} if cfg.get("paired") else {}))
        # (d) the record itself, with the ledger it read
        o, _ = night(work, f"d_{tag}", rec, [R1["ledger_last"]] if R1.get("ledger_last") else None)
        out[f"(d) {tag}"] = dict(summary_of(o, rec), against_record=against_record(o, rec),
                                 verify=_verify(o, rec))
        # (a) / (b) the ledger used
        o, _ = night(work, f"{'a' if rec == PAIRED else 'b'}_{tag}", rec, [line])
        out[f"({'a' if rec == PAIRED else 'b'}) {tag}"] = dict(summary_of(o, rec), ledger_line=line, verify=_verify(o, rec))
        # (c) the refusals, on the paired record (each one starts from the diagnostics: the record's own night)
        if rec == PAIRED:
            cases = {
                "other device": [dict(line, device="ibm_fez")],
                "other calibration": [dict(line, calibration_time="2026-11-19 10:59:49+01:00")],
                "broken file (not JSON)": "[{\"night\": \"cut off",
                "broken line (last_stacks not a table)": [dict(line, last_stacks=["P2", "M"])],
                "L missing (no L3)": [dict(line, last_stacks={k: v for k, v in fin.items() if k != "3"})],
            }
            for nm, led in cases.items():
                key = "c_" + nm.split(" (")[0].replace(" ", "_")
                o, _ = night(work, key, rec, None if isinstance(led, str) else led,
                             led if isinstance(led, str) else None)
                out[f"(c) {nm}"] = dict(summary_of(o, rec), against_record=against_record(o, rec))
    json.dump(out, open(os.path.join(work, "summary.json"), "w"), indent=1, default=str)
    lines = []
    for k, v in out.items():
        lines.append(f"== {k}")
        for f in ("ledger_used", "ledger_why", "per_key", "diagnostics_stacks", "round1_stacks", "round1_candidates",
                  "round1_steps", "stacks_per_rule", "stop", "replay_missing", "jobs", "against_record", "verify"):
            if f in v:
                lines.append(f"  {f}: {json.dumps(v[f], ensure_ascii=False)}")
    open(os.path.join(work, "summary.txt"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


def _verify(out, record):
    import contextlib
    import io
    from psf_os import loop as LP
    exp, _ = exp_of(record)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ok = LP.verify(out, exp)
    return dict(ok=ok, last=buf.getvalue().strip().splitlines()[-1])


if __name__ == "__main__":
    main(sys.argv[1])
