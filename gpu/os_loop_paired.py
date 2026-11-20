"""The paired loop of the RUS chain (home VS Claude, 2026-11-21; home instruction "輪の改造: 比べる 2 つの積み方を同じ
ジョブに入れる"; desk prototype, not declared). psf-os branch loop-paired-2026-11-21 (psf_os.loop.next_stacks_paired,
Night with cfg "paired", feedforward.build ff_only). gpu/os_loop.py, gpu/os3_night.py and gpu/os2_night.py (declared
tools) are imported read only and unchanged; this file adds the paired build, check and score.

One round's job, per L that has a candidate:
  - P0 (three arms; g beside, and the incumbent itself while the incumbent is P0);
  - the incumbent's ff only (feedforward.build ff_only; not when the incumbent is P0: P0's ff is above);
  - the candidate's three arms (ff, off, floor);
  - order inside the job: the circuits are sorted by name, so the tags alternate who comes first by L
    (L odd: incumbent then candidate; L even: candidate then incumbent);
  and the readout probe dr, the ring sentinel. A key with no candidate adds nothing but its P0.
The decision (psf_os.loop.paired_decision) reads the two ff arms of one job: d = |P_inc - exact| - |P_cand - exact|.
g against P0 and the os3 verdict words are kept beside, for the ceiling and the compound rows.

  python gpu/os_loop_paired.py go OUT --dry DEVDIR [--noise N.json] [--k-max K] [--budget S] [--ledger L.json]
                                [--climb-on-kept]
  python gpu/os_loop_paired.py go OUT --zip ZIP --expect-psf-os SHA --declaration PREREG.md [--ledger L.json]
  python gpu/os_loop_paired.py resume OUT [--zip ZIP]
  python gpu/os_loop_paired.py verify OUT [--resim]
  python gpu/os_loop_paired.py size DEVDIR [--stacks JSON]     circuits and model seconds of one paired round
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import os_loop as OL  # noqa: E402  (declared 2026-11-19; read only)

LS = (1, 2, 3)


def _stack_items(st, who):
    """[(suffix, presc, m, os2 role, offset)] of one stack; who 'i' (incumbent) or 'c' (candidate)."""
    import os2_night as O2
    import os3_night as O3
    o, m = O2.offset_of(st), O3.tries_of(st)
    if "B" in st:
        return [(who + "r", "P2", m, "xr", o), (who + "n", "NF", m, "xn", o)]
    return [(who, O3.base_of(st), m, "x", o)]


def items_for_paired(R):
    """([(tag, circuit, spec)], {tag: (L, role, offset, presc, m, who)}, [ff-only tags])."""
    import os2_night as O2
    import os3_night as O3
    out, meta, ff_only = [], {}, []
    for L in LS:
        out.append((f"p0_{L}", *O3.item("P0", L, 3)))
        meta[f"p0_{L}"] = (L, "p0", 0, "P0", 3, "p0")
    for L in LS:
        inc, cand = R["stacks"][str(L)], R["candidates"][str(L)]
        if not cand:
            continue
        order = ("i", "c") if L % 2 else ("c", "i")
        for pos, who in zip("ab", order):
            st = inc if who == "i" else cand
            if who == "i" and list(st) == ["P0"]:
                continue
            for suf, presc, m, role, o in _stack_items(st, who):
                tag = f"y{L}{pos}{suf}"
                out.append((tag, *O3.item(presc, L, m)))
                meta[tag] = (L, role, o, presc, m, who)
                if who == "i":
                    ff_only.append(tag)
    out.append(("dr", *O2.probe_item()))
    meta["dr"] = (0, "probe", 0, None, 0, "probe")
    return out, meta, ff_only


def build(devdir, folder, rule_path, dry):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    import os2_night as O2
    R = json.load(open(rule_path))
    if R.get("stop"):
        print(f"STOP: {R.get('stop_reason')}")
        return False
    if not R.get("paired"):
        print("REFUSED: not a paired rule")
        return False
    dev = Device.load(devdir)
    if dev.name != R["device"]:
        print(f"REFUSED: the rule was made on {R['device']}, the record is {dev.name}")
        return False
    its, meta, ff_only = items_for_paired(R)
    chains = O2.chains_for(dev, {t: v[:3] for t, v in meta.items()})
    spec = dict(kind="echo_clifford", D=24) if dry else None     # dry runs only, never a device
    rep = FF.build(dev, its, folder, shots=4000, max_seconds=60, sentinel_spec=spec, chains=chains, ff_only=ff_only)
    full = FF.place(dev, O2.PROBE_N + max(O2.OFFSETS))["chain"]
    outq = {t: rep["items"][t]["chain"][2 * v[0] - 1] for t, v in meta.items() if v[1] != "probe"}
    probe_q = [rep["items"]["dr"]["chain"][p] for p in O2.PROBE_POS]
    if probe_q != [full[p] for p in O2.PROBE_POS]:
        os.rename(os.path.join(folder, "job"), os.path.join(folder, "job_REFUSED"))
        print("REFUSED: the probe is not on the rule-C chain the offsets are read on (job moved to job_REFUSED)")
        return False
    same_q = {}
    for L in LS:
        i = [rep["items"][t]["chain"] for t, v in meta.items() if v[0] == L and v[5] == "i"]
        c = [rep["items"][t]["chain"] for t, v in meta.items() if v[0] == L and v[5] == "c"]
        if i and c:
            same_q[str(L)] = sorted(map(tuple, i)) == sorted(map(tuple, c))
    R2 = dict(R, meta={t: list(v) for t, v in meta.items()}, ff_only=ff_only, output_qubit=outq,
              probe_qubits=probe_q, probe_positions=list(O2.PROBE_POS), qpu_seconds_model=rep["qpu_seconds_model"],
              incumbent_candidate_same_qubits=same_q)
    json.dump(R2, open(os.path.join(folder, "rule.json"), "w"), indent=1)
    print(json.dumps({k: rep[k] for k in ("device", "circuits", "qpu_seconds_model", "shots") if k in rep}))
    print("incumbents", json.dumps(R["stacks"]), "candidates", json.dumps(R["candidates"]))
    return True


def check(folder):
    """Noiseless (Aer): every ff and off arm at its exact noiseless value (os3's TOL), floors all zero, the probe all
    one; the incumbent and the candidate of an L on the same qubits unless their offsets differ (+Q)."""
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    from psf_os import feedforward as FF
    import os2_night as O2
    import os3_night as O3
    R = json.load(open(os.path.join(folder, "rule.json")))
    m = json.load(open(os.path.join(folder, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(folder, "job", "circuits.qpy"), "rb"))
    i, bad = 0, []
    for cell in m["cells"]:
        for _ in range(cell["points"]):
            c = cs[i]
            i += 1
            if cell["role"] == "sentinel":
                continue
            tag = cell["name"][3:].replace("_floor", "").replace("_off", "")
            L, role, _, presc, mm, _who = R["meta"][tag]
            cc = FF.compact(c)
            n = cc.num_clbits
            cnt = AerSimulator().run(cc, shots=4000, seed_simulator=20261121).result().get_counts()
            tot = sum(cnt.values())
            allz = sum(v for k, v in cnt.items() if set(FF._bits(k, n)) == {0}) / tot
            if cell["role"] == "floor":
                ok, p = allz == 1.0, float("nan")
            elif role == "probe":
                p = sum(v for k, v in cnt.items() if set(FF._bits(k, n)) == {1}) / tot
                ok = p == 1.0
            else:
                p, _ = O2._p_out(n, cnt, L * mm, presc == "P2")
                ok = abs(p - O3.noiseless(presc, L, mm, "ff" if cell["role"] == "user" else "off")) <= O3.TOL
            print(f"{cell['name']:<16} {cell['role']:<6} P {p:.3f} {'ok' if ok else 'FAIL'}")
            bad += [] if ok else [cell["name"]]
    for L, same in R.get("incumbent_candidate_same_qubits", {}).items():
        offs = {v[2] for t, v in R["meta"].items() if v[0] == int(L) and v[5] in ("i", "c")}
        if not same and len(offs) == 1:
            bad.append(f"L {L}: incumbent and candidate on other qubits")
    print("PASS" if not bad else f"FAIL {bad}")
    return not bad


def _read_stack(st, who, L, g, R, p0, n0):
    """P, SE, noiseless, overshoot and the readings for the next step of one stack in this job."""
    import os2_night as O2
    import os3_night as O3
    se = O2._se
    if list(st) == ["P0"]:
        p, s = p0, se(p0, n0)
        nl = O3.noiseless("P0", L, 3)
        return dict(p=p, se=s, noiseless=nl, overshoot=bool(p > nl + 2 * s),
                    info=dict(output_qubit=R["output_qubit"][f"p0_{L}"]))
    mine ={t: v for t, v in R["meta"].items() if v[0] == L and v[5] == who}
    m = O3.tries_of(st)
    if "B" in st:
        tr = next(t for t, v in mine.items() if v[1] == "xr")
        tn = next(t for t, v in mine.items() if v[1] == "xn")
        nlr, nln = O3.noiseless("P2", L, m), O3.noiseless("NF", L, m)
        pr, nr = O2._p_out(*g[(tr, "ff")], L * m, True)
        pn, nn = O2._p_out(*g[(tn, "ff")], L * m, False)
        p, s, nl = (pr + pn) / 2, math.sqrt(se(pr, nr) ** 2 + se(pn, nn) ** 2) / 2, (nlr + nln) / 2
        info = dict(share_gap=pr / nlr - pn / nln,
                    share_gap_two_se=2 * math.sqrt((se(pr, nr) / nlr) ** 2 + (se(pn, nn) / nln) ** 2),
                    output_qubit_rd=R["output_qubit"][tr], output_qubit_nf=R["output_qubit"][tn], rd=pr, nf=pn)
    else:
        t = next(iter(mine))
        nl = O3.noiseless(O3.base_of(st), L, m)
        p, nx = O2._p_out(*g[(t, "ff")], L * m, O3.base_of(st) == "P2")
        s = se(p, nx)
        info = dict(output_qubit=R["output_qubit"][t])
    return dict(p=p, se=s, noiseless=nl, overshoot=bool(p > nl + 2 * s), info=info)


def score(folder, quiet=False):
    import ctrl_night as CN
    import os2_night as O2
    from psf_os import loop as LP
    R = json.load(open(os.path.join(folder, "rule.json")))
    ref = O2.refs()
    g = CN._counts(folder)
    se = O2._se
    rows = {}
    for L in LS:
        key = str(L)
        inc, cand = R["stacks"][key], R["candidates"][key]
        ex = ref["exact"][L]
        p0, n0 = O2._p_out(*g[(f"p0_{L}", "ff")], L * 3, False)
        row = dict(stack=inc, candidate=cand, step=R["steps"][key], tried=R["tried"][key], pick=R["pick"][key],
                   exact=ex, p0=p0, p0_n=n0, output_qubit_p0=R["output_qubit"][f"p0_{L}"])
        if not cand:
            row.update(verdict="NO CANDIDATE")
            rows[key] = row
            continue
        a = _read_stack(inc, "i", L, g, R, p0, n0)
        b = _read_stack(cand, "c", L, g, R, p0, n0)
        row.update(inc_p=a["p"], inc_se=a["se"], inc_noiseless=a["noiseless"], inc_info=a["info"],
                   cand_p=b["p"], cand_se=b["se"], cand_noiseless=b["noiseless"], cand_overshoot=b["overshoot"],
                   cand_info=b["info"])
        dec = LP.paired_decision(row)
        # beside (not the decision): the candidate against P0 as os3 scores a stack, for the ceiling and compound rows
        gain = abs(p0 - ex) - abs(b["p"] - ex)
        g_se = math.sqrt(se(p0, n0) ** 2 + b["se"] ** 2)
        v = "OVERSHOOT" if b["overshoot"] else ("PRESCRIPTION HELPS" if (gain > 0 and gain >= 2 * g_se)
                                                else "NOT SHOWN")
        g_inc = abs(p0 - ex) - abs(a["p"] - ex)
        row.update(d=dec["d"], d_se=dec["se"], decision=dec["word"], adopted=dec["adopted"],
                   p=b["p"], se=b["se"], noiseless=b["noiseless"], overshoot=b["overshoot"], g=gain, g_se=g_se,
                   verdict=v, g_incumbent=g_inc, tries=None)
        rows[key] = row
        if not quiet:
            print(f"L {L}: candidate [{'+'.join(cand)}] P {b['p']:.4f} against incumbent [{'+'.join(inc)}] P "
                  f"{a['p']:.4f} (exact {ex:.4f}): d {dec['d']:+.4f} (2 SE {dec['two_se']:.4f}) -> {dec['word']}; "
                  f"beside: g {gain:+.4f} (2 SE {2 * g_se:.4f}) {v}")
    dr = O2.dr_from_probe(folder, R)
    out = dict(round=R["round"], device=R["device"], paired=True, stacks=R["stacks"], candidates=R["candidates"],
               rows=rows, dr=dr, probe_qubits=R["probe_qubits"], qpu_seconds_model=R["qpu_seconds_model"],
               model_seconds_so_far=R.get("model_seconds_so_far", 0.0) + R["qpu_seconds_model"])
    json.dump(out, open(os.path.join(folder, "round_scores.json"), "w"), indent=1)
    return out


class PairedRusLoop(OL.RusLoop):
    name = "rus-chain loop, paired (incumbent and candidate in one job; os3 rungs +M, +F; ledger)"

    def build(self, devdir, folder, rule_path, dry):
        return build(devdir, folder, rule_path, dry)

    def check(self, folder):
        return check(folder)

    def score(self, folder):
        return score(folder)

    def predictions(self, out):
        """Beside only until a declaration names predictions [OWNER]: the steps adopted, the final incumbents, the
        decisions per round."""
        ds = sorted([d for d in os.listdir(out) if d.startswith("r") and d[1:].isdigit() and
                     os.path.exists(os.path.join(out, d, "round_scores.json"))], key=lambda d: int(d[1:]))
        rs = [json.load(open(os.path.join(out, d, "round_scores.json"))) for d in ds]
        dec = {str(r["round"]): {k: [v.get("step"), v.get("decision")] for k, v in r["rows"].items()} for r in rs}
        last = None
        if rs:
            p = os.path.join(out, f"RULE{rs[-1]['round'] + 1}.json")
            last = json.load(open(p))["stacks"] if os.path.exists(p) else None
        return {"declared predictions": "none yet ([OWNER])", "rounds_run": len(rs), "decisions": dec,
                "final_incumbents": last}


def size(devdir, stacks_json=None):
    """Circuits and model seconds of one paired round on a device record (default: every L incumbent P1, candidate
    P1 + M; the largest ordinary round; and every L incumbent P2 + B, candidate P2 + B + Q2 with B's two circuits)."""
    import shutil
    import tempfile
    from psf_os.device import Device
    dev = Device.load(devdir).name
    cases = json.loads(stacks_json) if stacks_json else {
        "round 1 (incumbent P0, candidate P1)": ({"1": ["P0"], "2": ["P0"], "3": ["P0"]}, {k: ["P1"] for k in "123"}),
        "incumbent P1, candidate P1+M": ({k: ["P1"] for k in "123"}, {k: ["P1", "M"] for k in "123"}),
        "incumbent P2+B, candidate P2+B+Q2": ({k: ["P2", "B"] for k in "123"}, {k: ["P2", "B", "Q2"] for k in "123"}),
    }
    tmp = tempfile.mkdtemp(prefix="paired_size_")
    try:
        for name, (inc, cand) in cases.items():
            R = dict(round=1, device=dev, paired=True, stacks=inc, candidates=cand, steps={k: "M" for k in inc},
                     tried={k: [] for k in inc}, pick={k: "P1" for k in inc})
            rp = os.path.join(tmp, "R.json")
            json.dump(R, open(rp, "w"))
            f = os.path.join(tmp, name.replace(" ", "_").replace("+", "p").replace(",", "").replace("(", "")
                             .replace(")", ""))
            OL._quiet(build, devdir, f, rp, True)
            b = json.load(open(os.path.join(f, "build.json")))
            print(f"{name}: {b['circuits']} circuits, {b['qpu_seconds_model']} s by the model")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    from psf_os import loop as LP
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("go")
    g.add_argument("out")
    g.add_argument("--zip")
    g.add_argument("--dry", metavar="DEVDIR")
    g.add_argument("--noise")
    g.add_argument("--k-max", type=int)
    g.add_argument("--budget", type=float)
    g.add_argument("--ledger")
    g.add_argument("--expect-psf-os")
    g.add_argument("--declaration")
    g.add_argument("--climb-on-kept", action="store_true", help="psf_os.loop.next_stacks_paired's option [OWNER]")
    r = sub.add_parser("resume")
    r.add_argument("out")
    r.add_argument("--zip")
    v = sub.add_parser("verify")
    v.add_argument("out")
    v.add_argument("--resim", action="store_true")
    s = sub.add_parser("size")
    s.add_argument("devdir")
    s.add_argument("--stacks")
    a = ap.parse_args()
    exp = PairedRusLoop()
    if a.cmd == "size":
        size(a.devdir, a.stacks)
        return 0
    if a.cmd == "verify":
        return 0 if LP.verify(a.out, exp, a.resim) else 1
    if a.cmd == "go":
        if not a.dry and not (a.expect_psf_os and a.declaration):
            raise SystemExit("a device run needs --expect-psf-os and --declaration")
        ok, items = OL.preflight(bool(a.dry), out=a.out, zip_path=a.zip, expect_psf_os=a.expect_psf_os,
                                 declaration=a.declaration)
        if not ok:
            raise SystemExit("preflight FAIL: nothing started")
        n = LP.start(a.out, exp, dry_devdir=a.dry, noise=json.load(open(a.noise)) if a.noise else None,
                     k_max=a.k_max, budget=a.budget, ledger=a.ledger, zip_path=a.zip, paired=True,
                     extra=dict(preflight=items, expect_psf_os=a.expect_psf_os, declaration=a.declaration,
                                **({"climb_on_kept": True} if a.climb_on_kept else {})))
    else:
        n = LP.Night(a.out, exp)
        if a.zip:
            n.set_cfg(zip=os.path.abspath(a.zip))
        c = n.cfg()
        if not OL.preflight(c["dry"], expect_psf_os=c.get("expect_psf_os"), declaration=c.get("declaration"))[0]:
            raise SystemExit("preflight FAIL: not resumed")
    print(json.dumps(n.go(), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
