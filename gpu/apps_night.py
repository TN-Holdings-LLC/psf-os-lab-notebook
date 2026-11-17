"""Two computations whose real-time decisions are the computation (prereg/ff_night_2026-11-17.md, test T3): iterative
phase estimation (A) and constant-depth long-range teleport (B), from the workplace prototype
(notes/ffapps_2026-11-17/apps.py), with one home change to B: the last qubit gets an X before its measurement, so that
success is the last bit 1 (decay toward |0> then works against success, never for it: the lesson of the 2026-11-16
teleport test, where the arm without control rose above 3/4). The ceiling 3/4 is recomputed exactly for this form.

  python gpu/apps_night.py build DEVDIR OUT [--dry-clifford-sentinel]
  python gpu/apps_night.py check OUT
  python gpu/apps_night.py score OUT

Items: A ipe{n}_{j} for n = 2, 3 and every j (phi = j / 2^n), success = all n bits right; off arm = the feedback removed
(the ancilla reset kept), given explicitly. B lr{k} for k = 2, 4 (distance 2k), success = last bit 1. ff, off, floor
arms; one ring sentinel; 4000 shots per circuit.

Verdicts (declared): per group (A: n = 2, 3 over all its phases pooled; B: k = 2, 4), BEYOND THE CEILING when the ff
success share (every shot counted) is at least the ceiling + 2 SE; otherwise NOT BEYOND. Ceilings are exact and
noiseless: A, the best decoder of the off arm's recorded bits averaged over phi (Bayes-optimal: no processing of those
bits does better); B, the best fixed rule on the recorded bits (3/4)."""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.join(HERE, "..", "notes", "ffapps_2026-11-17")
sys.path.insert(0, PROTO)
sys.path.insert(0, os.path.join(HERE, "..", "notes", "rus_coherent_2026-11-17"))
import apps as AP  # noqa: E402

NS, KS = (2, 3), (2, 4)
SHOTS = 4000
TOL = 0.03


def longrange1(k, feed_forward=True):
    """apps.longrange(k) with an X on the last qubit before its measurement: ideal last bit 1."""
    qc, _ = AP.longrange(k, feed_forward)
    last = 2 * k
    meas = qc.data.pop()                                # the last instruction is the measurement of the last qubit
    assert meas.operation.name == "measure"
    qc.x(last)
    qc.append(meas.operation, meas.qubits, meas.clbits)
    return qc, {2 * k: 1}


def lr_ideal(k):
    import coherent as CO
    out = {}
    for ff in (True, False):
        qc, _ = longrange1(k, ff)
        dist = CO.branch_distribution(qc)
        out["ff" if ff else "off"] = sum(p for key, p in dist.items() if key[0] == "1")
        if not ff:
            by = {}
            for key, p in dist.items():
                by.setdefault(key[1:], [0.0, 0.0])[int(key[0])] += p
            out["ceiling"] = sum(max(v) for v in by.values())
    return dict(k=k, **out)


def ideal():
    ref = dict(A={n: AP.ipe_ideal(n) for n in NS}, B={k: lr_ideal(k) for k in KS})
    return ref


def items():
    out = []
    for n in NS:
        for j in range(2 ** n):
            qc, succ = AP.ipe(n, j, True)
            off, _ = AP.ipe(n, j, False)
            out.append((f"ipe{n}_{j}", qc, dict(success=succ, off_circuit=off, form="blocks")))
    for k in KS:
        qc, succ = longrange1(k, True)
        out.append((f"lr{k}", qc, dict(success=succ, bound=0.75)))
    return out


def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None   # dry runs only, never a device
    rep = FF.build(Device.load(a.devdir), items(), a.out, shots=SHOTS, max_seconds=160, sentinel_spec=spec)
    print(json.dumps({k: rep[k] for k in ("device", "circuits", "qpu_seconds_model", "shots") if k in rep}))


def check(a):
    """Noiseless Aer of every ff and off arm: success share against the exact ideal (ff 1, off within 0.03 of its exact
    value per circuit); floor arms all zero."""
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    from psf_os import feedforward as FF
    import coherent as CO
    m = json.load(open(os.path.join(a.out, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(a.out, "job", "circuits.qpy"), "rb"))
    succ = {t: s for t, _, s in [(t, q, sp["success"]) for t, q, sp in items()]}
    offc = {t: (sp.get("off_circuit") if sp.get("off_circuit") is not None else None) for t, _, sp in items()}
    i, bad = 0, []
    for cell in m["cells"]:
        for _ in range(cell["points"]):
            c = cs[i]
            i += 1
            if cell["role"] == "sentinel":
                continue
            tag = cell["name"][3:].replace("_floor", "").replace("_off", "")
            cc = FF.compact(c)
            n = cc.num_clbits
            cnt = AerSimulator().run(cc, shots=SHOTS, seed_simulator=20261117).result().get_counts()
            tot = sum(cnt.values())
            ok_sh = sum(v for k, v in cnt.items() if all(FF._bits(k, n)[b] == val for b, val in succ[tag].items())) / tot
            allz = sum(v for k, v in cnt.items() if set(FF._bits(k, n)) == {0}) / tot
            if cell["role"] == "floor":
                ok = allz == 1.0
            elif cell["role"] == "user":
                ok = ok_sh == 1.0
            else:
                if tag.startswith("ipe"):
                    nn, j = map(int, tag[3:].split("_"))
                    dist = CO.branch_distribution(offc[tag])
                    want = sum(p for k, p in dist.items() if all(k[nn - 1 - b] == str(v) for b, v in succ[tag].items()))
                else:
                    want = lr_ideal(int(tag[2:]))["off"]
                ok = abs(ok_sh - want) <= TOL
            print(f"{cell['name']:16s} {cell['role']:6s} success {ok_sh:.3f}  all zero {allz:.3f}  {'ok' if ok else 'FAIL'}")
            bad += [] if ok else [cell["name"]]
    print("PASS" if not bad else f"FAIL {bad}")
    return not bad


def score(a):
    from psf_os import feedforward as FF
    R = ideal()
    cards = FF.cards(a.out)
    groups = {}
    for t, c in cards.items():
        groups.setdefault(t.split("_")[0], []).append(c)
    out = dict(groups={})
    for g in sorted(groups):
        cs = groups[g]
        N = sum(c["ff"]["counted"] for c in cs)
        p = sum(c["ff"]["success"] for c in cs) / N
        po = sum(c["off"]["success"] for c in cs) / sum(c["off"]["counted"] for c in cs)
        se = math.sqrt(p * (1 - p) / N) if 0 < p < 1 else 0.0
        ceil = R["A"][int(g[3:])]["ceiling"] if g.startswith("ipe") else R["B"][int(g[2:])]["ceiling"]
        v = "BEYOND THE CEILING" if p >= ceil + 2 * se else "NOT BEYOND"
        out["groups"][g] = dict(ff=p, se=se, two_se=2 * se, N=N, off_as_read=po, ceiling=ceil, margin=p - ceil,
                                verdict=v, circuits=len(cs), sentinel=cs[0]["sentinel"])
        print(f"{g}: ff {p:.4f} (2 SE {2 * se:.4f}, {len(cs)} circuits, {N} shots) against the ceiling {ceil:.4f} "
              f"-> {v}; off as read {po:.4f}; margin {p - ceil:+.4f}; sentinel {cs[0]['sentinel']}")
    G = out["groups"]
    a2, a3 = G["ipe2"], G["ipe3"]
    d = a3["margin"] - a2["margin"]
    sd = math.sqrt(a2["se"] ** 2 + a3["se"] ** 2)
    out["A_growth"] = dict(d=d, two_se=2 * sd, verdict="GROWS" if d >= 2 * sd else "NOT SHOWN")
    print(f"A: margin at n = 3 minus margin at n = 2 = {d:+.4f} (2 SE {2 * sd:.4f}) -> {out['A_growth']['verdict']}")
    b2, b4 = G["lr2"], G["lr4"]
    print(f"B beside: ff at k = 4 minus ff at k = 2 = {b4['ff'] - b2['ff']:+.4f} "
          f"(2 SE {2 * math.sqrt(b2['se'] ** 2 + b4['se'] ** 2):.4f})")
    out["predictions"] = {
        "T3-1 A BEYOND at n = 2 and n = 3": "held" if a2["verdict"] == a3["verdict"] == "BEYOND THE CEILING" else "failed",
        "T3-2 A GROWS from n = 2 to n = 3": "held" if out["A_growth"]["verdict"] == "GROWS" else "failed",
        "T3-3 B BEYOND at k = 2 and k = 4": "held" if b2["verdict"] == b4["verdict"] == "BEYOND THE CEILING" else "failed",
    }
    print("predictions:", out["predictions"])
    json.dump(out, open(os.path.join(a.out, "apps_scores.json"), "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ideal")
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    b.add_argument("--dry-clifford-sentinel", action="store_true",
                   help="dry runs only: the ring sentinel at its Clifford point; never for the device job")
    for nm in ("check", "score"):
        sub.add_parser(nm).add_argument("out")
    a = ap.parse_args()
    if a.cmd == "ideal":
        R = ideal()
        for n, r in R["A"].items():
            print(f"A n {n}: ff {r['ff']:.4f}; off as read {r['off']:.4f}; ceiling {r['ceiling']:.4f}")
        for k, r in R["B"].items():
            print(f"B k {k} (success = last bit 1): ff {r['ff']:.4f}; off {r['off']:.4f}; ceiling {r['ceiling']:.4f}")
        sys.exit(0)
    r = {"build": build, "check": check, "score": score}[a.cmd](a)
    sys.exit(0 if r is not False else 1)
