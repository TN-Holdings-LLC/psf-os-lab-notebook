"""The prescription loop with more rungs (gpu/os3_night.py) and a nightly ledger (home VS Claude, 2026-11-18 night;
home instruction "試作3点", part C; desk prototype, not declared). gpu/os2_run.py (declared) is not changed. This
prototype runs nights locally (dry, with the illustrative noise of notes/os2_2026-11-18/branch_noise.py, never fitted to
a device); the device path ("go" as os2_run.py has it: fetch, submit, collect, zip) is left for the port into psf-os.

The ledger (one JSON file, a list of nights): per night the device, its calibration time (the device record's
source.calibration_time: a time, not an error number), the ladder, and per L the last stack run and its g / verdict.

Round 1 of a night: the diagnostics (Dw, Dc) and gpu/os_night.py's rule give the pick per L, as os2. Then the ledger:
  - used only when its last night is on the SAME device with the SAME calibration time;
  - and only for an L where the night's own diagnostics agree with the ledger's stack: the same family of base (P1 / P2
    = "hold flipped"; P0; P3) as tonight's pick. Where they disagree the diagnostics win (tonight's pick is kept) and
    the ledger is not used for that L;
  - every decision (used / not used, and why) is written into RULE1.json and the night record.
No calibration number is read; only the time stamp, the failed marks and the coupling map (as every tool here).

  python gpu/os3_run.py night DEVDIR OUT --ladder A|B [--noise NOISE.json] [--ledger LEDGER.json] [--seed-base N]
  python gpu/os3_run.py show LEDGER.json
"""
import argparse
import contextlib
import io
import json
import os
import sys
from types import SimpleNamespace as NS

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(NB, "notes", "os2_2026-11-18"))

FAMILY = {"P0": "P0", "P1": "flip", "P2": "flip", "P3": "P3"}


def calibration_time(devdir):
    d = json.load(open(os.path.join(devdir, "device.json")))
    return d["name"], (d.get("source") or {}).get("calibration_time")


def _quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        r = fn(*a, **k)
    return r, buf.getvalue()


def ledger_load(path):
    return json.load(open(path)) if path and os.path.exists(path) else []


def ledger_start(ledger, device, cal_time, pick):
    """Round 1 stacks from tonight's pick and the ledger. Returns (stacks, decision dict)."""
    stacks = {L: [p] for L, p in pick.items()}
    dec = dict(used=False, per_L={}, last_night=None)
    if not ledger:
        dec["why"] = "no ledger"
        return stacks, dec
    last = ledger[-1]
    dec["last_night"] = dict(night=last.get("night"), device=last["device"], calibration_time=last["calibration_time"])
    if last["device"] != device:
        dec["why"] = f"other device ({last['device']} -> {device}): start from tonight's diagnostics"
        return stacks, dec
    if not cal_time or last["calibration_time"] != cal_time:
        dec["why"] = (f"other calibration ({last['calibration_time']} -> {cal_time}): start from tonight's "
                      "diagnostics")
        return stacks, dec
    for L, p in pick.items():
        prev = last["last_stacks"].get(L)
        if prev is None:
            dec["per_L"][L] = "no stack for this L in the ledger"
            continue
        if FAMILY.get(prev[0]) != FAMILY.get(p):
            dec["per_L"][L] = (f"diagnostics disagree (tonight {p}, ledger {'+'.join(prev)}): the diagnostics win, "
                               "ledger not used")
            continue
        stacks[L] = list(prev)
        dec["per_L"][L] = f"ledger used: start from {'+'.join(prev)} (same device and calibration time; family agrees)"
        dec["used"] = True
    dec["why"] = "same device and calibration time"
    return stacks, dec


def night(devdir, out, ladder, noise=None, ledger_path=None, seed_base=20261119, k_max=4, budget=240.0, label=None):
    import ctrl_night as CN
    import os_night as ON
    import os3_night as O3
    import wait_night as WN
    import branch_noise as BN
    from psf_os import feedforward as FF
    from psf_os.device import Device
    noise = noise or {}
    dev = Device.load(devdir)
    device, cal = calibration_time(devdir)
    os.makedirs(out, exist_ok=False)
    cliff = dict(kind="echo_clifford", D=24)
    rec = dict(night=label or os.path.basename(out), device=device, calibration_time=cal, ladder=ladder, noise=noise,
               illustrative=True, seed_base=seed_base, rounds=[])
    spent = 0.0
    for i, (nm, mod) in enumerate((("dw", WN), ("dc", CN))):
        d = os.path.join(out, nm)
        rep = FF.build(dev, mod.items(), d, shots=4000, sentinel_spec=cliff)
        spent += rep["qpu_seconds_model"]
        BN.noisy_run_local(d, noise, seed_base + 500_000 * i, BN.WIDE_CIRCUIT)
        _quiet(mod.score, NS(out=d))
    rule0 = os.path.join(out, "os_rule.json")
    _quiet(ON.rule, NS(dw=os.path.join(out, "dw"), dc=os.path.join(out, "dc"), rule_json=rule0))
    pick = {str(L): p for L, p in json.load(open(rule0))["pick"].items()}
    ledger = ledger_load(ledger_path)
    stacks, dec = ledger_start(ledger, device, cal, pick)
    rec.update(diagnostics_pick=pick, ledger=dec, round1_stacks=stacks)
    R = dict(round=1, device=device, ladder=ladder, stacks=stacks, why={L: dec["per_L"].get(L, "round 1: os_night rule")
                                                                         for L in stacks},
             stop=False, stop_reason=None, model_seconds_so_far=spent, ledger=dec)
    rule = os.path.join(out, "RULE1.json")
    json.dump(R, open(rule, "w"), indent=1)
    rounds, k = [], 1
    while True:
        R = json.load(open(rule))
        if R.get("stop"):
            rec["stop"] = R["stop_reason"]
            break
        d = os.path.join(out, f"r{k}")
        ok, txt = _quiet(O3.build, NS(devdir=devdir, out=d, rule_json=rule, dry_clifford_sentinel=True))
        if ok is False:
            rec["stop"] = f"round {k}: build refused ({txt.strip()[-200:]})"
            break
        cost = json.load(open(os.path.join(d, "rule.json")))["qpu_seconds_model"]
        okc, _ = _quiet(O3.check, NS(out=d))
        if not okc:
            rec["stop"] = f"round {k}: check FAIL"
            break
        if spent + cost > budget:
            rec["stop"] = f"budget before round {k}: {spent:.1f} + {cost:.1f} > {budget:.0f} s (not run)"
            break
        BN.noisy_run_local(d, noise, seed_base + 1_000_000 * k, BN.WIDE_CIRCUIT)
        spent += cost
        sc = O3.score(NS(out=d), quiet=True)
        rounds.append(sc)
        b = json.load(open(os.path.join(d, "build.json")))
        Rn = O3.next_stacks(rounds, ladder, b["items"]["dr"]["chain"], k_max=k_max, budget=budget)
        rec["rounds"].append(dict(round=k, cost_s=cost, stacks=sc["stacks"],
                                  rows={L: dict(verdict=v.get("verdict"), p=v.get("p"), noiseless=v.get("noiseless"),
                                                g=v.get("g"), g_two_se=2 * v["g_se"] if "g_se" in v else None)
                                        for L, v in sc["rows"].items()},
                                  next_stacks=Rn["stacks"], why_next=Rn["why"]))
        rule = os.path.join(out, f"RULE{k + 1}.json")
        json.dump(Rn, open(rule, "w"), indent=1)
        k += 1
    rec["rounds_run"] = len(rounds)
    rec["model_seconds"] = spent
    if rounds:
        import os2_night as O2
        rec["compound"] = O2.compound_rows(rounds)
        last = rounds[-1]
        rec["last_stacks"] = {L: last["rows"][L]["stack"] for L in last["rows"]}
        rec["last_g"] = {L: last["rows"][L].get("g") for L in last["rows"]}
        rec["last_verdict"] = {L: last["rows"][L].get("verdict") for L in last["rows"]}
    else:
        rec["last_stacks"] = stacks
    json.dump(rec, open(os.path.join(out, "night.json"), "w"), indent=1, default=str)
    if ledger_path:
        entry = {k2: rec[k2] for k2 in ("night", "device", "calibration_time", "ladder", "last_stacks", "rounds_run")}
        entry.update(last_g=rec.get("last_g"), last_verdict=rec.get("last_verdict"), ledger_used=dec["used"],
                     ledger_why=dec["why"])
        json.dump(ledger + [entry], open(ledger_path, "w"), indent=1, default=str)
    return rec


def show(rec):
    print(f"night {rec['night']}: {rec['device']} calibration {rec['calibration_time']} ladder {rec['ladder']} noise "
          f"(ILLUSTRATIVE) {json.dumps(rec['noise'])}")
    print(f"  diagnostics pick {rec['diagnostics_pick']}; ledger: used {rec['ledger']['used']} ({rec['ledger']['why']}) "
          f"{rec['ledger']['per_L']}; round 1 stacks {rec['round1_stacks']}")
    for r in rec["rounds"]:
        print(f"  round {r['round']}: " + "; ".join(
            f"L{L} [{'+'.join(r['stacks'][L])}] {v['verdict']}" + (f" g {v['g']:+.4f} ({v['g_two_se']:.4f})"
                                                                   if v['g'] is not None else "")
            for L, v in r["rows"].items()))
        print("     next: " + "; ".join(f"L{L} {r['why_next'][L]}" for L in r["why_next"]))
    c = rec.get("compound", {})
    print(f"  STOP: {rec.get('stop')}; rounds {rec['rounds_run']}; model seconds {rec['model_seconds']:.1f}; G per round "
          f"{[round(x['G'], 4) for x in c.get('per_round', [])]}; slope {c.get('slope')}; {c.get('verdict')}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("night")
    n.add_argument("devdir")
    n.add_argument("out")
    n.add_argument("--ladder", choices=("A", "B"), required=True)
    n.add_argument("--noise", default=None)
    n.add_argument("--ledger", default=None)
    n.add_argument("--seed-base", type=int, default=20261119)
    s = sub.add_parser("show")
    s.add_argument("ledger")
    a = ap.parse_args()
    if a.cmd == "night":
        show(night(a.devdir, a.out, a.ladder, json.load(open(a.noise)) if a.noise else None, a.ledger, a.seed_base))
    else:
        for e in ledger_load(a.ledger):
            print(json.dumps(e))


if __name__ == "__main__":
    main()
