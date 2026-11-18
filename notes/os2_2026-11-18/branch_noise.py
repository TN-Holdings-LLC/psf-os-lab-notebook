"""Illustrative noise for dry runs of the compounding OS, to drive every branch of its rule (workplace VS Claude,
2026-11-18; home instruction "VSクロードへの指示_複利OSの点検"; desk only, not declared).

THE NOISE IS AN ILLUSTRATION. It is uniform, written by hand, never fitted to a device, and reads no calibration number.
Its only purpose: noiselessly the rule only ever steps back (R3); these settings make R1, R2, R3 and every stop happen
inside a run, so the tools are exercised on every path before the night.

  noise = dict(gamma=G,                  amplitude damping |1> -> |0> with probability G on every other touched qubit
                                         during each mid-circuit measurement (top level; as RUS_DECAY_DESK)
               p11={"1": 0.83, ...},     P(read 1 | 1) per PHYSICAL qubit (default 1); e.g. one qubit at 0.83, the size
                                         of the 2026-11-17 q1 readout gap, as an example
               p00={...})                P(read 0 | 0) per physical qubit (default 1)

  noisy_run_local(OUT, noise, seed)      the drop-in for psf_os.feedforward.run_local (dry runs only): the same
                                         raw_counts.json and submission.json (local=True, the noise written into it).
                                         A Clifford sentinel runs noiselessly (the stabilizer method has no damping;
                                         the sentinel is not scored by the rule).
  python branch_noise.py run OUT NOISE.json [--seed S]
  python branch_noise.py loop DEVDIR OUT NOISE.json [--budget S] [--k-max K]
                                         the night's order (Dw, Dc, os_night rule, rounds of os2_night) with this noise,
                                         every job through noisy_run_local; stops as gpu/os2_night.py says, with the
                                         budget counted as the home instruction says (diagnostics + rounds run + the
                                         next round's estimate > budget: the next round is not run). Writes
                                         OUT/loop.json. Until gpu/os2_run.py has "go --dry --noise", this is the
                                         stand-in; the branches are re-run through go --dry when it exists.
"""
import argparse
import json
import os
import sys
from types import SimpleNamespace as NS

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(NB, "gpu"))


def noisy_circuit(cc, gamma):
    """A copy of the compact circuit with amplitude damping on every other qubit after each top-level measurement.
    Consecutive measurements (nothing else between them) count as one simultaneous read, as IBM runs measurements on
    disjoint qubits in one block: the damping falls once, after the group, on the qubits not read in it."""
    from qiskit_aer.noise import amplitude_damping_error
    if not gamma:
        return cc
    err = amplitude_damping_error(gamma).to_instruction()
    out = cc.copy_empty_like()
    group = []

    def flush():
        if group:
            for q in out.qubits:
                if q not in group:
                    out.append(err, [q])
            group.clear()
    for ins in cc.data:
        if ins.operation.name != "measure":
            flush()
        out.append(ins.operation, ins.qubits, ins.clbits)
        if ins.operation.name == "measure":
            group.append(ins.qubits[0])
    flush()
    return out


def readout_model(phys, noise):
    from qiskit_aer.noise import NoiseModel, ReadoutError
    nm = NoiseModel()
    p11, p00 = noise.get("p11", {}), noise.get("p00", {})
    for i, q in enumerate(phys):
        a, b = float(p00.get(str(q), 1.0)), float(p11.get(str(q), 1.0))
        if a < 1.0 or b < 1.0:
            nm.add_readout_error(ReadoutError([[a, 1 - a], [1 - b, b]]), [i])
    return nm


def noisy_run_local(out, noise, seed=20261118):
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    from psf_os import feedforward as FF
    from psf_os.sim import to_clifford_gates
    job = os.path.join(out, "job")
    sub = os.path.join(job, "submission.json")
    if os.path.exists(sub):
        raise SystemExit(f"{sub} exists: this job was already run")
    man = json.load(open(os.path.join(job, "manifest.json")))
    circs = qpy.load(open(os.path.join(job, "circuits.qpy"), "rb"))
    rows = []
    for k, c in enumerate(circs):
        phys = sorted({q for _, qs in FF.walk(c) for q in qs})
        cc = FF.compact(c)
        cl = None if cc.has_control_flow_op() else to_clifford_gates(cc)
        if cl is not None and cc.num_qubits > FF.LOCAL_MAX_QUBITS:
            res = AerSimulator(method="stabilizer").run(cl, shots=man["shots"], seed_simulator=seed + k).result()
        else:
            if cc.num_qubits > FF.LOCAL_MAX_QUBITS:
                raise SystemExit(f"circuit {k} ({c.name}) touches {cc.num_qubits} qubits and is not Clifford: build "
                                 "the dry job with the Clifford sentinel")
            sim = AerSimulator(method="density_matrix" if cc.num_qubits <= 10 else "statevector",
                               noise_model=readout_model(phys, noise))
            res = sim.run(noisy_circuit(cc, noise.get("gamma", 0.0)), shots=man["shots"],
                          seed_simulator=seed + k).result()
        rows.append(dict(pub=k, counts={key.replace(" ", ""): v for key, v in res.get_counts(0).items()}))
    from psf_os.ibm import _stamp
    t = _stamp()
    jid = f"local-illustrative-noise-{seed}"
    json.dump(dict(job_id=jid, submitted=t, local=True, backend=man["fetch"]["backend"],
                   simulator="aer, ILLUSTRATIVE noise (not fitted to any device)", noise=noise),
              open(sub, "w"), indent=1)
    json.dump(dict(fetched=t, job_id=jid, status="DONE (local, illustrative noise)", rows=rows),
              open(os.path.join(job, "raw_counts.json"), "w"))
    return jid


def _quiet(fn, *a):
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        r = fn(*a)
    return r, buf.getvalue()


def loop(devdir, out, noise, budget=240.0, k_max=4, seed=20261118):
    """The night's order with the illustrative noise. Returns the loop record (also OUT/loop.json)."""
    import ctrl_night as CN
    import os2_night as O2
    import os_night as ON
    import wait_night as WN
    from psf_os import feedforward as FF
    from psf_os.device import Device
    dev = Device.load(devdir)
    os.makedirs(out, exist_ok=False)
    cliff = dict(kind="echo_clifford", D=24)
    rec = dict(noise=noise, illustrative=True, budget_s=budget, k_max=k_max, rounds=[], log=[])
    spent = 0.0
    for nm, mod in (("dw", WN), ("dc", CN)):
        d = os.path.join(out, nm)
        rep = FF.build(dev, mod.items(), d, shots=4000, sentinel_spec=cliff)
        spent += rep["qpu_seconds_model"]
        noisy_run_local(d, noise, seed)
        _quiet(mod.score, NS(out=d))
        rec["log"].append(f"{nm}: {rep['circuits']} circuits, {rep['qpu_seconds_model']} s")
    rule0 = os.path.join(out, "os_rule.json")
    _quiet(ON.rule, NS(dw=os.path.join(out, "dw"), dc=os.path.join(out, "dc"), rule_json=rule0))
    r0 = json.load(open(rule0))
    rec["os_night_pick"] = r0["pick"]
    rule = os.path.join(out, "RULE1.json")
    _quiet(O2.round1, NS(os_rule=rule0, out_rule=rule, device=None))
    rec["diagnostics_s"] = spent
    rounds = []
    k = 1
    while True:
        R = json.load(open(rule))
        if R.get("stop"):
            rec["stop"] = R["stop_reason"]
            break
        d = os.path.join(out, f"round{k}")
        ok, _ = _quiet(O2.build, NS(devdir=devdir, out=d, rule_json=rule, dry_clifford_sentinel=True))
        if ok is False:
            rec["stop"] = f"round {k}: build refused"
            break
        cost = json.load(open(os.path.join(d, "rule.json")))["qpu_seconds_model"]
        okc, txt = _quiet(O2.check, NS(out=d))
        if not okc:
            rec["stop"] = f"round {k}: check FAIL"
            break
        if spent + cost > budget:
            rec["stop"] = f"budget before round {k}: {spent:.1f} + {cost:.1f} > {budget:.0f} s (not run)"
            break
        noisy_run_local(d, noise, seed + 100 * k)
        spent += cost
        sc, _ = _quiet(O2.score, NS(out=d))
        rounds.append(d)
        rec["rounds"].append(dict(round=k, cost_s=cost, stacks=sc["stacks"],
                                  rows={L: dict(verdict=v.get("verdict"), p=v.get("p"), noiseless=v.get("noiseless"),
                                                g=v.get("g"), g_two_se=2 * v["g_se"] if "g_se" in v else None,
                                                rd_share=v.get("rd_share"), nf_share=v.get("nf_share"))
                                        for L, v in sc["rows"].items()},
                                  dr_sig=[q for q, v in sc["dr"].items() if v["sig"]]))
        nxt = os.path.join(out, f"RULE{k + 1}.json")
        scores = [json.load(open(os.path.join(x, "round_scores.json"))) for x in rounds]
        b = json.load(open(os.path.join(d, "build.json")))
        Rn = O2.next_stacks(scores, O2._probe_chain(b, None), k_max=k_max, budget=budget, next_cost=None)
        json.dump(Rn, open(nxt, "w"), indent=1)
        rec["rounds"][-1]["why_next"] = Rn["why"]
        rec["rounds"][-1]["next_stacks"] = Rn["stacks"]
        rule = nxt
        k += 1
    rec["model_seconds"] = spent
    if len(rounds) >= 1:
        rec["compound"] = O2.compound_rows([json.load(open(os.path.join(x, "round_scores.json"))) for x in rounds])
    json.dump(rec, open(os.path.join(out, "loop.json"), "w"), indent=1, default=str)
    return rec


def show(rec):
    print(f"noise (ILLUSTRATIVE) {json.dumps(rec['noise'])}; os_night pick {rec['os_night_pick']}; diagnostics "
          f"{rec['diagnostics_s']:.1f} s")
    for r in rec["rounds"]:
        print(f" round {r['round']} ({r['cost_s']} s) " + "; ".join(
            f"L{L} [{'+'.join(r['stacks'][L])}] {v['verdict']}" + (f" g {v['g']:+.3f}/{v['g_two_se']:.3f}" if v['g'] is not None else "")
            + (f" sh {v['rd_share']:.3f}/{v['nf_share']:.3f}" if v.get('rd_share') is not None else "")
            for L, v in r["rows"].items()) + f"; Dr sig {r['dr_sig']}")
        print("   next: " + "; ".join(f"L{L} {r['why_next'][L]}" for L in r["why_next"]))
    print(f" STOP: {rec.get('stop')}; model seconds {rec['model_seconds']:.1f}; compound "
          f"{rec.get('compound', {}).get('verdict')}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("out")
    r.add_argument("noise")
    r.add_argument("--seed", type=int, default=20261118)
    lp = sub.add_parser("loop")
    lp.add_argument("devdir")
    lp.add_argument("out")
    lp.add_argument("noise")
    lp.add_argument("--budget", type=float, default=240.0)
    lp.add_argument("--k-max", type=int, default=4)
    a = ap.parse_args()
    if a.cmd == "run":
        print(noisy_run_local(a.out, json.load(open(a.noise)), a.seed))
    else:
        show(loop(a.devdir, a.out, json.load(open(a.noise)), a.budget, a.k_max))


if __name__ == "__main__":
    main()
