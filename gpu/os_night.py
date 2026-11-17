"""The first run of the prescription loop ("the seed of an AI OS"; prereg/os_night_2026-11-17.md): diagnose -> a fixed
rule picks a prescription from a fixed list -> one main job with the picked prescription next to the unchanged circuit.
No search: the list, the order and the thresholds are fixed by the declaration; the night's own diagnostics only choose
among the declared entries. Needs psf-os at the branch feedforward-2026-11-16, 301ac01 or later.

  1. diagnostics (two jobs, the tools of 2026-11-16, unchanged):
       python gpu/wait_night.py build DEVDIR DW && python gpu/wait_night.py check DW
       python gpu/ctrl_night.py build DEVDIR DC && python gpu/ctrl_night.py check DC
     (run, then)  python gpu/wait_night.py score DW && python gpu/ctrl_night.py score DC
  2. the rule:   python gpu/os_night.py rule DW DC RULE.json
  3. main job:   python gpu/os_night.py build DEVDIR OUT RULE.json && python gpu/os_night.py check OUT
  4. verdicts:   python gpu/os_night.py score OUT

The list (theta 1.1, L = 1, 2, 3):
  P0  the circuit as written: psf_os.feedforward.rus_chain(L, 1.1, m=3) (the first design of 2026-11-16)
  P1  hold flipped while waiting: gpu/rus2_night.flip_chain(L, 1.1) (m = 2, outputs in use flipped around every
      ancilla measurement; the second design)
  P2  P1 and read flipped: gpu/rus3_night.chain(L, 1.1) (the last bit relabelled 1 - bit; the third design)
  P3  fewer tries: psf_os.feedforward.rus_chain(L, 1.1, m=2) (fewer conditionals and waits, no flips)
The rule (fixed order, first match wins; every threshold in SE of the diagnostic's own difference):
  1. Dc (control diagnostic) shows a late-use loss D_late_nb > 0 and >= 2 SE at position A or B -> P1 for every L;
  2. if 1 holds, per L: Dr shows that the qubit holding that L's last output reads |1> as 1 less often than |0> as 0,
     by >= 2 SE -> P2 for that L;
  3. if 1 does not hold: Dw (wait diagnostic) shows unfired conditionals cost D_cond > 0 and >= 2 SE at A or B -> P3;
  4. otherwise P0 (no prescription; the main job then holds P0 alone and no HELPS verdict is formed).
Dr, per output qubit: P(read 1 | |1>) from the diagnostic arms that prepare |1> and read it at once (Dc "now" control
bit for chain qubits 1 and 3; Dw "ref" at position B for chain qubit 5); P(read 0 | |0>) from the floor arms of the
same items (the same qubit, every gate removed). The main job must place each L's last output on the qubit Dr used
(checked at build; otherwise the build refuses)."""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

THETA = 1.1
LS = (1, 2, 3)
TOL = 0.03
OUT_CHAIN_QUBIT = {1: 1, 2: 3, 3: 5}                  # chain position of each L's last output (a_j = 2j, o_j = 2j + 1)


def _bits_share(n, counts, bit, val):
    from psf_os import feedforward as FF
    tot = sum(counts.values())
    p = sum(v for k, v in counts.items() if FF._bits(k, n)[bit] == val) / tot
    return p, tot


def _diff_ge_2se(p1, n1, p2, n2):
    d = p1 - p2
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    return dict(d=d, two_se=2 * se, loss=bool(d > 0 and d >= 2 * se))


def rule(a):
    import ctrl_night as CN
    w = json.load(open(os.path.join(a.dw, "wait_scores.json")))
    c = json.load(open(os.path.join(a.dc, "ctrl_scores.json")))
    gw, gc = CN._counts(a.dw), CN._counts(a.dc)
    bw = json.load(open(os.path.join(a.dw, "build.json")))
    bc = json.load(open(os.path.join(a.dc, "build.json")))
    ev = {}
    late = {p: c["positions"][p]["differences"]["late_nb"] for p in ("A", "B")}
    late_loss = {p: bool(v["d"] > 0 and v["d"] >= v["two_se"]) for p, v in late.items()}
    cond = {p: w["positions"][p]["differences"]["cond"] for p in ("A", "B")}
    cond_loss = {p: bool(v["d"] > 0 and v["d"] >= v["two_se"]) for p, v in cond.items()}
    # Dr per output chain qubit: (item tag, job counts, clbit of the qubit in that item, build, chain index)
    import wait_night as WN
    if bw["device"] != bc["device"]:
        raise SystemExit(f"REFUSED: the diagnostics ran on different devices ({bw['device']}, {bc['device']})")
    # the bit and chain positions read below must be the diagnostic tools' own (ctrl_night.POS, wait_night.POS)
    assert CN.POS["A"]["c"] == OUT_CHAIN_QUBIT[1] and CN.POS["B"]["c"] == OUT_CHAIN_QUBIT[2]
    assert WN.POS["B"][2] == OUT_CHAIN_QUBIT[3]
    src = {1: ("Anow", gc, 1, bc), 2: ("Bnow", gc, 1, bc), 3: ("Bref", gw, 0, bw)}
    dr = {}
    for L, (tag, g, bit, b) in src.items():
        n1, c1 = g[(tag, "ff")]
        n0, c0 = g[(tag, "floor")]
        p11, t1 = _bits_share(n1, c1, bit, 1)
        p00, t0 = _bits_share(n0, c0, bit, 0)
        gap = _diff_ge_2se(p00, t0, p11, t1)
        chain = b["items"][tag]["chain"]
        dr[L] = dict(item=tag, p_read1_given1=p11, p_read0_given0=p00, gap=gap,
                     physical_qubit=chain[OUT_CHAIN_QUBIT[L]])
    pick = {}
    if any(late_loss.values()):
        for L in LS:
            pick[L] = "P2" if dr[L]["gap"]["loss"] else "P1"
        why = "rule 1 (Dc late-use loss)" + "; rule 2 per L (Dr)"
    elif any(cond_loss.values()):
        pick = {L: "P3" for L in LS}
        why = "rule 3 (Dw unfired conditionals cost)"
    else:
        pick = {L: "P0" for L in LS}
        why = "rule 4 (no prescription)"
    out = dict(pick=pick, why=why, device=bc["device"], late_nb=late, late_loss=late_loss, cond=cond,
               cond_loss=cond_loss, dr=dr)
    json.dump(out, open(a.rule_json, "w"), indent=1)
    for p in ("A", "B"):
        print(f"Dc {p}: D_late_nb {late[p]['d']:+.4f} (2 SE {late[p]['two_se']:.4f}) loss {late_loss[p]};  "
              f"Dw {p}: D_cond {cond[p]['d']:+.4f} (2 SE {cond[p]['two_se']:.4f}) loss {cond_loss[p]}")
    for L in LS:
        r = dr[L]
        print(f"Dr L {L} (physical qubit {r['physical_qubit']}): P(1|1) {r['p_read1_given1']:.4f}, P(0|0) "
              f"{r['p_read0_given0']:.4f}, gap {r['gap']['d']:+.4f} (2 SE {r['gap']['two_se']:.4f}) loss {r['gap']['loss']}")
    print(f"pick: {pick}  ({why})")


def item(presc, L):
    from psf_os import feedforward as FF
    import rus2_night as R2
    import rus3_night as R3
    if presc == "P0":
        return FF.rus_chain(L, THETA, m=3)
    if presc == "P1":
        return R2.flip_chain(L, THETA)
    if presc == "P2":
        return R3.chain(L, THETA)
    if presc == "P3":
        return FF.rus_chain(L, THETA, m=2)
    raise ValueError(presc)


def items(pick):
    out = [(f"p0_{L}", *item("P0", L)) for L in LS]
    for L in LS:
        if pick[str(L)] != "P0":
            out.append((f"x{L}", *item(pick[str(L)], L)))
    return out


def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    R = json.load(open(a.rule_json))
    dev = Device.load(a.devdir)
    if dev.name != R["device"]:
        print(f"REFUSED: the rule was made from diagnostics on {R['device']}, the record is {dev.name}")
        return False
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None   # dry runs only, never a device
    rep = FF.build(dev, items(R["pick"]), a.out, shots=4000, sentinel_spec=spec)
    bad = []
    for t, v in rep["items"].items():
        L = int(t[-1])
        q = v["chain"][OUT_CHAIN_QUBIT[L]]
        if q != R["dr"][str(L)]["physical_qubit"]:
            bad.append((t, q, R["dr"][str(L)]["physical_qubit"]))
    json.dump(R, open(os.path.join(a.out, "rule.json"), "w"), indent=1)
    print(json.dumps({k: rep[k] for k in ("device", "circuits", "qpu_seconds_model", "shots") if k in rep}))
    print(json.dumps({t: (v["chain"], v["cz"], v["mid"]) for t, v in rep["items"].items()}))
    if bad:
        os.rename(os.path.join(a.out, "job"), os.path.join(a.out, "job_REFUSED"))   # nothing left to submit
        print(f"REFUSED: the last output is not on the qubit Dr measured: {bad} (job moved to job_REFUSED)")
        return False


def _ref():
    import rus2_night as R2
    import rus_night as R1
    m2 = R2.reference()
    return {"P0": {L: R1.REF[L] for L in LS}, "m2": m2}


def check(a):
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    from psf_os import feedforward as FF
    R = json.load(open(os.path.join(a.out, "rule.json")))
    ref = _ref()
    m = json.load(open(os.path.join(a.out, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(a.out, "job", "circuits.qpy"), "rb"))
    i, bad = 0, []
    for cell in m["cells"]:
        for _ in range(cell["points"]):
            c = cs[i]
            i += 1
            if cell["role"] == "sentinel":
                continue
            tag = cell["name"][3:].replace("_floor", "").replace("_off", "")
            L = int(tag[-1])
            presc = "P0" if tag.startswith("p0") else R["pick"][str(L)]
            mm = 3 if presc == "P0" else 2
            cc = FF.compact(c)
            n = cc.num_clbits
            cnt = AerSimulator().run(cc, shots=4000, seed_simulator=20261117).result().get_counts()
            p, _ = _bits_share(n, cnt, L * mm, 1)
            if presc == "P2":
                p = 1 - p
            allz = sum(v for k, v in cnt.items() if set(FF._bits(k, n)) == {0}) / sum(cnt.values())
            if cell["role"] == "floor":
                ok = allz == 1.0
            else:
                arm = "ff" if cell["role"] == "user" else "off"
                want = ref["P0"][L][arm] if presc == "P0" else ref["m2"][L][arm]
                ok = abs(p - want) <= TOL
            print(f"{cell['name']:14s} {presc} {cell['role']:6s} P(out 1, read as declared) {p:.3f} all zero {allz:.3f} "
                  f"{'ok' if ok else 'FAIL'}")
            bad += [] if ok else [cell["name"]]
    print("PASS" if not bad else f"FAIL {bad}")
    return not bad


def score(a):
    from psf_os import feedforward as FF
    import rus3_night as R3
    from rus_night import verdict
    R = json.load(open(os.path.join(a.out, "rule.json")))
    ref = _ref()
    cards = FF.cards(a.out)
    out = dict(pick=R["pick"], cards={}, helps={})
    for tag in sorted(cards):
        L = int(tag[-1])
        presc = "P0" if tag.startswith("p0") else R["pick"][str(L)]
        c = R3.relabel(cards[tag]) if presc == "P2" else cards[tag]
        d, se, v = verdict(c)
        c.update(prescription=presc, d=d, se_d=se, verdict=v)
        out["cards"][tag] = c
        print(f"{tag} ({presc}): exact {c['exact']:.4f}; ff {c['ff']['p1']:.4f}; off {c['off']['p1']:.4f}; d {d:.4f} "
              f"(2 SE_d {2 * se:.4f}) -> {v}; floor all zero {c['floor']['all_zero']:.4f}; sentinel {c['sentinel']}")
    for L in LS:
        if f"x{L}" not in out["cards"]:
            out["helps"][L] = dict(verdict="NO PRESCRIPTION")
            continue
        x, p0 = out["cards"][f"x{L}"], out["cards"][f"p0_{L}"]
        ex = x["exact"]
        g = abs(p0["ff"]["p1"] - ex) - abs(x["ff"]["p1"] - ex)
        se = math.sqrt(x["ff"]["p1"] * (1 - x["ff"]["p1"]) / x["ff"]["counted"] +
                       p0["ff"]["p1"] * (1 - p0["ff"]["p1"]) / p0["ff"]["counted"])
        noiseless = ref["m2"][L]["ff"]
        sx = math.sqrt(x["ff"]["p1"] * (1 - x["ff"]["p1"]) / x["ff"]["counted"])
        over = x["ff"]["p1"] > noiseless + 2 * sx
        v = "OVERSHOOT" if over else ("PRESCRIPTION HELPS" if (g > 0 and g >= 2 * se) else "NOT SHOWN")
        out["helps"][L] = dict(gain=g, two_se=2 * se, x_ff=x["ff"]["p1"], p0_ff=p0["ff"]["p1"], x_noiseless=noiseless,
                               overshoot=over, verdict=v)
        print(f"L {L}: |P0 - exact| - |{x['prescription']} - exact| = {g:+.4f} (2 SE {2 * se:.4f}) -> {v}  "
              f"({x['prescription']} ff {x['ff']['p1']:.4f}, noiseless {noiseless:.4f}; P0 ff {p0['ff']['p1']:.4f})")
    H = out["helps"]
    out["predictions"] = {
        "OS-1 the rule picks a prescription (not P0) for every L": "held" if all(R["pick"][str(L)] != "P0" for L in LS)
        else "failed",
        "OS-2 PRESCRIPTION HELPS at L = 1, 2, 3": "held" if all(H[L]["verdict"] == "PRESCRIPTION HELPS" for L in LS)
        else "failed",
    }
    print("predictions:", out["predictions"])
    json.dump(out, open(os.path.join(a.out, "os_scores.json"), "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("rule")
    r.add_argument("dw")
    r.add_argument("dc")
    r.add_argument("rule_json")
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    b.add_argument("rule_json")
    b.add_argument("--dry-clifford-sentinel", action="store_true",
                   help="dry runs only: the ring sentinel at its Clifford point; never for the device job")
    for nm in ("check", "score"):
        sub.add_parser(nm).add_argument("out")
    a = ap.parse_args()
    res = {"rule": rule, "build": build, "check": check, "score": score}[a.cmd](a)
    sys.exit(0 if res is not False else 1)
