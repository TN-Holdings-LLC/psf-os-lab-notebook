"""Decoy test: does a fixed item in the register's first bits take the packing loss? (draft
prereg/drafts-2026-11-20/decoy_DRAFT.md; workplace Claude, 2026-11-20; not declared)

2026-11-18 P-B and 2026-11-19 E3: of two conditional items in one circuit, the one whose bits come first in the register
lost (-0.06, -0.037), the other did not. Is it "the register's first bits" or "the first conditional item's bits"?
Three bundles and three singles in ONE job (rd2 = gpu/rus3_night.chain(2, 1.1, 2); Z = rd2's off arm, fixed):

  D0  A rd2, B rd2                       gap 1        bits A, B       control (E3 / P-B again)
  D1  A rd2, B rd2, Z fixed              gaps 1, ZG   bits Z, A, B    the decoy's bits first
  D2  A rd2, B rd2, Z fixed              gaps 1, ZG   bits A, B, Z    a third item present but last
  sa, sb, sz  rd2 alone on A's, B's and Z's qubits

A and B sit on the same qubits in every bundle (checked against D0). Z sits ZG sites past B (default 2: Z then shares
no coupler within two steps of B, as the draft's check asks; ZG = 1 puts Z on the next free site, two steps from B,
and that check fails; the owner's choice, [OWNER] in the draft). The per-pair gap is psf-os's build_bundle
gap=[1, ZG] (added 2026-11-20; gap=[1, 1] is byte-identical to gap=1).

  python gpu/decoy_night.py build DEVDIR OUT [--z-gap 3] [--dry-clifford-sentinel]
  python gpu/decoy_night.py check OUT
  python gpu/decoy_night.py score OUT
  python gpu/decoy_night.py dry OUT NOISE.json [--seed S]      dry runs only: ILLUSTRATIVE noise, never fitted

check (PASS / FAIL, exit 1 on FAIL), as interfere_night's: independence of every bundle arm; per packed sub-item the
same instructions per wire and the same exact distribution as its single reference (Z against sz's off arm); the same
physical qubits; the recorded acceptance of every arm; no sx / x in a floor; no conditional in an off arm;
conditionals kept in every single ff and every conditional sub-item; the manifest records allow_conditional_neighbours;
and for this test: A and B on D0's qubits in D1 and D2; Z's bits first in D1 and last in D2; Z's qubits at coupling
distance >= 3 from B's (no coupler, working or failed, within two steps); one job within 30 s by the model.
score: per conditional sub-item d = |s - v| - |p - v| (s its single's ff, p its ff packed, v rd2's noiseless ff,
computed here exactly from the single circuit) with the words PACKED KEEPS LESS (d <= -2 SE) / PACKED KEEPS MORE
(d >= 2 SE) / SAME WITHIN ERROR [OWNER], per sub-item and per bundle (mean of its conditional sub-items); Z against
sz's off arm beside; the draft's reading table row, if one matches [OWNER].
"""
import argparse
import json
import math
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
for d in ("notes/early_2026-11-17", "notes/compound_2026-11-17", "notes/rus_coherent_2026-11-17",
          "notes/timebudget_2026-11-17", "notes/os2_2026-11-18"):
    sys.path.insert(0, os.path.join(NB, d))
import parallel_night as PN  # noqa: E402  (read only: rd2, offvariant)

SHOTS = 4000
MAX_S = 30
Z_GAP = 2
SPEC_DRY = dict(kind="echo_clifford", D=24)
BUNDLES = {
    "D0": dict(items=["d0a", "d0b"], bit_order=None),
    "D1": dict(items=["d1a", "d1b", "d1z"], bit_order=["d1z", "d1a", "d1b"]),
    "D2": dict(items=["d2a", "d2b", "d2z"], bit_order=None),
}
# sub-item -> (single, arm it is judged against)
REFS = {"d0a": ("sa", "ff"), "d0b": ("sb", "ff"), "d1a": ("sa", "ff"), "d1b": ("sb", "ff"), "d1z": ("sz", "off"),
        "d2a": ("sa", "ff"), "d2b": ("sb", "ff"), "d2z": ("sz", "off")}


def _merge(dev, parts, runs, job, extra):
    from psf_os import job as J
    os.makedirs(runs)
    for k, p in enumerate(parts):
        for f in sorted(os.listdir(os.path.join(p, "runs"))):
            if k > 0 and not f.startswith("ff_"):
                continue
            dst = os.path.join(runs, f)
            if os.path.exists(dst):
                raise RuntimeError(f"two records named {f}")
            shutil.copy2(os.path.join(p, "runs", f), dst)
    return J.assemble(dev, runs, job, max_seconds=MAX_S, extra=extra)


def _rec(out, name):
    from qiskit import qpy
    rec = json.load(open(os.path.join(out, "runs", name + ".json")))
    (c,) = qpy.load(open(os.path.join(out, "runs", name + ".qpy"), "rb"))
    return rec, c


def _distance(dev, src, dst):
    """Smallest number of couplers (working or failed) between a qubit of src and a qubit of dst."""
    adj = {}
    for a, b in dev.all_couplers():
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    seen, front, d = set(src), set(src), 0
    while front:
        if front & set(dst):
            return d
        nxt = {y for x in front for y in adj.get(x, ())} - seen
        seen |= nxt
        front, d = nxt, d + 1
    return None


def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    if os.path.exists(a.out):
        print(f"REFUSED: {a.out} exists")
        return False
    dev = Device.load(a.devdir)
    spec = SPEC_DRY if a.dry_clifford_sentinel else None          # dry runs only, never a device
    qc, sp = PN.rd2()
    off = PN.offvariant(qc, sp)
    circ = {"a": (qc, sp), "b": (qc, sp), "z": (off, sp)}
    tmp = tempfile.mkdtemp(prefix="decoy_night_")
    try:
        reps, extra, chains = {}, {}, {}
        for name, b in BUNDLES.items():
            items = [(t, *circ[t[-1]]) for t in b["items"]]
            gap = 1 if len(items) == 2 else [1, a.z_gap]
            reps[name] = FF.build_bundle(dev, items, os.path.join(tmp, name), tag=name, shots=SHOTS, max_seconds=60,
                                         sentinel_spec=spec, allow_conditional_neighbours=True, gap=gap,
                                         bit_order=b["bit_order"])
            chains[name] = {t[-1]: reps[name]["items"][t]["chain"] for t in b["items"]}
            m = json.load(open(os.path.join(tmp, name, "job", "manifest.json")))
            extra[name] = {k: m[k] for k in ("conditional_neighbours", "conditionals_per_item", "bundle_gap",
                                             "bit_order") if k in m}
        chA, chB = chains["D0"]["a"], chains["D0"]["b"]
        for name in ("D1", "D2"):
            if [chains[name]["a"], chains[name]["b"]] != [chA, chB]:
                raise FF.Refused(f"{name}: A, B on {chains[name]['a']}, {chains[name]['b']}, D0's on {chA}, {chB}")
        if chains["D1"]["z"] != chains["D2"]["z"]:
            raise FF.Refused(f"Z on {chains['D1']['z']} in D1 and {chains['D2']['z']} in D2")
        chZ = chains["D1"]["z"]
        single = FF.build(dev, [("sa", qc, sp), ("sb", qc, sp), ("sz", qc, sp)], os.path.join(tmp, "single"),
                          shots=SHOTS, max_seconds=60, sentinel_spec=spec, chains={"sa": chA, "sb": chB, "sz": chZ})
        man = _merge(dev, [os.path.join(tmp, "single")] + [os.path.join(tmp, k) for k in BUNDLES],
                     os.path.join(a.out, "runs"), os.path.join(a.out, "job"), dict(decoy_bundles=extra))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    plan = dict(device=dev.name, dry_clifford_sentinel=bool(a.dry_clifford_sentinel), chain_A=chA, chain_B=chB,
                chain_Z=chZ, z_gap=a.z_gap, z_distance_to_B=_distance(dev, chZ, chB), circuits=len(man["pubs"]),
                s_model=man["qpu_seconds_model"],
                bundles={k: dict(items=v["items"], bit_order=v["bit_order"]) for k, v in BUNDLES.items()},
                manifest_bundles=extra, build_single=single, build_bundles=reps)
    json.dump(plan, open(os.path.join(a.out, "plan.json"), "w"), indent=1, default=str)
    print(f"{dev.name}: {plan['circuits']} circuits {plan['s_model']:.1f} s by the model; A {chA}, B {chB}, Z {chZ} "
          f"(coupling distance from B {plan['z_distance_to_B']})")
    return True


def check(a):
    import coherent as CO
    from psf_os import feedforward as FF
    plan = json.load(open(os.path.join(a.out, "plan.json")))
    man = json.load(open(os.path.join(a.out, "job", "manifest.json")))
    bad, lines = [], []
    say = lambda s: (print(s), lines.append(s))
    single = {t: {arm: _rec(a.out, f"ff_{t}" + ("" if arm == "ff" else f"_{arm}")) for arm in ("ff", "off", "floor")}
              for t in ("sa", "sb", "sz")}
    for name, b in BUNDLES.items():
        arms = {arm: _rec(a.out, f"ff_{name}" + ("" if arm == "ff" else f"_{arm}")) for arm in ("ff", "off", "floor")}
        table = arms["ff"][0]["bundle"]
        tags = list(table)
        qsets = [set(table[t]["qubits"]) for t in tags]
        bsets = [set(range(table[t]["bit_offset"], table[t]["bit_offset"] + table[t]["clbits"])) for t in tags]
        try:
            FF.bundle_acceptance({k: v[1] for k, v in arms.items()}, qsets, bsets)
            ind = "ok"
        except FF.Refused as e:
            ind = f"FAIL {e}"
            bad.append(f"{name} independence")
        parts = []
        for t in tags:
            st, sarm = REFS[t]
            info = table[t]
            bits = list(range(info["bit_offset"], info["bit_offset"] + info["clbits"]))
            mine = FF.restrict(arms["ff"][1], info["qubits"], bits)
            ref = FF.restrict(single[st][sarm][1], info["qubits"], list(range(info["clbits"])))
            same = FF.wire_signature(mine) == FF.wire_signature(ref)
            tv = float(CO.tvd(CO.branch_distribution(mine), CO.branch_distribution(ref)))
            q_same = info["qubits"] == single[st][sarm][0]["chain"]
            ok = same and tv < 1e-12 and q_same
            bad += [] if ok else [f"{name} {t} identity"]
            parts.append(f"{t} vs {st} {sarm}: same per wire {same}, TV {tv:.1e}, same qubits {q_same}, bits "
                         f"{bits[0]}..{bits[-1]}")
        acc = all(all(r["checks"].values()) for r, _ in arms.values())
        fl = not ({n for n, _ in FF.walk(arms["floor"][1])} & {"sx", "x"})
        of = "if_else" not in {n for n, _ in FF.walk(arms["off"][1])}
        cond_items = [t for t in tags if table[t]["conditionals"]]
        kept = all(any(nm == "if_else" for nm, qs in FF.walk(arms["ff"][1]) if set(qs) <= set(table[t]["qubits"]))
                   for t in cond_items)
        z_fixed = all(not table[t]["conditionals"] for t in tags if t.endswith("z"))
        rec_allow = man["decoy_bundles"][name]["conditional_neighbours"]["allowed"] is True
        extra_ok = z_fixed and cond_items == [t for t in tags if not t.endswith("z")]
        if name == "D1":
            first = table["d1z"]["bit_offset"] == 0
            extra_ok = extra_ok and first
            parts.append(f"Z's bits first: {first} (Z at {table['d1z']['bit_offset']}.., A at "
                         f"{table['d1a']['bit_offset']}.., B at {table['d1b']['bit_offset']}..)")
        if name == "D2":
            last = table["d2z"]["bit_offset"] > max(table["d2a"]["bit_offset"], table["d2b"]["bit_offset"])
            extra_ok = extra_ok and last
            parts.append(f"Z's bits last: {last} (A at {table['d2a']['bit_offset']}.., B at "
                         f"{table['d2b']['bit_offset']}.., Z at {table['d2z']['bit_offset']}..)")
        if name in ("D1", "D2"):
            ab = [table[f"{name.lower()}a"]["qubits"], table[f"{name.lower()}b"]["qubits"]]
            on_d0 = ab == [plan["chain_A"], plan["chain_B"]]
            extra_ok = extra_ok and on_d0
            parts.append(f"A, B on D0's qubits: {on_d0}")
        ok = ind == "ok" and acc and fl and of and kept and rec_allow and extra_ok
        bad += [] if ok else [f"{name} acceptance/extras"]
        say(f"{name}: independence {ind}; acceptance {acc}; floor without sx/x {fl}; off without conditionals {of}; "
            f"conditionals kept {kept}; Z fixed {z_fixed}; manifest records allow {rec_allow}; " + "; ".join(parts))
    dist = plan["z_distance_to_B"]                 # computed at build on the device record's coupling graph
    far = dist is not None and dist >= 3
    say(f"Z's qubits {plan['chain_Z']} at coupling distance {dist} from B's {plan['chain_B']} (no coupler within two "
        f"steps: {far})")
    bad += [] if far else ["Z within two steps of B"]
    sfail = [t for t in single for arm in ("ff", "off", "floor") if not all(single[t][arm][0]["checks"].values())]
    sk = all(any(n == "if_else" for n, _ in FF.walk(single[t]["ff"][1])) for t in single)
    say(f"singles: acceptance {'ok' if not sfail else sfail}; conditionals kept {sk}; chains A {plan['chain_A']}, "
        f"B {plan['chain_B']}, Z {plan['chain_Z']}; {plan['circuits']} circuits {plan['s_model']:.1f} s")
    bad += sfail + ([] if sk else ["single conditionals"])
    if plan["s_model"] > MAX_S:
        bad.append(f"over {MAX_S} s")
    say("PASS" if not bad else f"FAIL {bad}")
    open(os.path.join(a.out, "check.txt"), "w").write("\n".join(lines) + "\n")
    return not bad


def verdict(d, two_se):
    """The words of P-B / E1-E3 [OWNER in the draft]: per sub-item and per bundle."""
    if d <= -two_se:
        return "PACKED KEEPS LESS"
    if d >= two_se:
        return "PACKED KEEPS MORE"
    return "SAME WITHIN ERROR"


def reading(rows):
    """The draft's reading table [OWNER]: the first row whose conditions all hold, else None. 'loses' is PACKED KEEPS
    LESS for that sub-item; 'keeps' is either other word."""
    lose = lambda t: rows[t]["verdict"] == "PACKED KEEPS LESS"
    if not lose("d0a"):
        return "the control did not repeat 11-18 / 11-19 on this night; D1, D2 not read for the mechanism"
    if not lose("d1a") and not lose("d1b") and lose("d2a"):
        return "the loss sits on the register's first bits; a fixed first item shields"
    if lose("d1a") and lose("d2a"):
        return "the loss belongs to the first conditional item, whatever stands before it"
    if lose("d1b"):
        return "the loss moves to the item right after the first bits' owner (order, not first place)"
    return None


def score(a):
    import coherent as CO
    import rus3_night as R3
    from psf_os import feedforward as FF
    cards = FF.cards(a.out)
    rsa, csa = _rec(a.out, "ff_sa")
    out_bit = rsa["rus"]["out_bit"]
    allbits = list(range(csa.num_clbits))
    dist = CO.branch_distribution(FF.restrict(csa, rsa["chain"], allbits))
    v = 1 - sum(p for k, p in dist.items() if k[len(k) - 1 - out_bit] == "1")       # read flipped (rd)
    dist_off = CO.branch_distribution(FF.restrict(_rec(a.out, "ff_sa_off")[1], rsa["chain"], allbits))
    v_off = 1 - sum(p for k, p in dist_off.items() if k[len(k) - 1 - out_bit] == "1")
    rows, lines = {}, []
    say = lambda s: (print(s), lines.append(s))
    c = {t: R3.relabel(cards[t]) for t in cards}
    se_ = lambda x, y: math.sqrt(x["p1"] * (1 - x["p1"]) / x["counted"] + y["p1"] * (1 - y["p1"]) / y["counted"])
    say(f"noiseless ff of rd2 (exact, read flipped): {v:.4f}; off {v_off:.4f}; singles sa {c['sa']['ff']['p1']:.4f}, "
        f"sb {c['sb']['ff']['p1']:.4f}, sz {c['sz']['ff']['p1']:.4f}")
    for name, b in BUNDLES.items():
        ds, ses = [], []
        for t in b["items"]:
            st, sarm = REFS[t]
            s, p = c[st][sarm], c[t]["ff"]
            if t.endswith("z"):            # the fixed decoy, beside: against sz's off arm and the noiseless off value
                d = abs(s["p1"] - v_off) - abs(p["p1"] - v_off)
                rows[t] = dict(single_off=s["p1"], packed=p["p1"], noiseless_off=v_off, d=d, two_se=2 * se_(s, p),
                               ref=f"{st} off", beside=True)
                say(f"  beside: {t} (fixed) against {st}'s off arm: alone {s['p1']:.4f} packed {p['p1']:.4f} "
                    f"d {d:+.4f} (2 SE {2 * se_(s, p):.4f})")
                continue
            d = abs(s["p1"] - v) - abs(p["p1"] - v)
            se = se_(s, p)
            rows[t] = dict(single=s["p1"], packed=p["p1"], d=d, two_se=2 * se, ref=st, verdict=verdict(d, 2 * se),
                           still_single=s.get("still_failed_after_m"), still_packed=p.get("still_failed_after_m"))
            ds.append(d)
            ses.append(se)
            say(f"  {t} against {st}: alone {s['p1']:.4f}  packed {p['p1']:.4f}  d {d:+.4f} (2 SE {2 * se:.4f}) -> "
                f"{rows[t]['verdict']}")
        m, ms = sum(ds) / len(ds), 2 * math.sqrt(sum(x * x for x in ses)) / len(ses)
        rows[name] = dict(mean=m, two_se=ms, verdict=verdict(m, ms))
        say(f"{name}: mean d over its conditional sub-items {m:+.4f} (2 SE {ms:.4f}) -> {rows[name]['verdict']}")
    r = reading(rows)
    say(f"reading (the draft's table, [OWNER]): {r if r else 'no row matches'}")
    json.dump(dict(rows=rows, noiseless=v, noiseless_off=v_off, reading=r),
              open(os.path.join(a.out, "decoy_scores.json"), "w"), indent=1)
    open(os.path.join(a.out, "score.txt"), "w").write("\n".join(lines) + "\n")


def _pay(sub, lam):
    """sub with a one-qubit depolarizing lam on every qubit of the part after each of its top-level conditionals
    (ILLUSTRATIVE: a part that waits on the controller loses; written by hand, never fitted)."""
    from qiskit_aer.noise import depolarizing_error
    if not lam:
        return sub
    err = depolarizing_error(lam, 1).to_instruction()
    out = sub.copy_empty_like()
    for ins in sub.data:
        out.append(ins.operation, ins.qubits, ins.clbits)
        if ins.operation.name == "if_else":
            for q in out.qubits:
                out.append(err, [q])
    return out


def dry(a):
    """Dry runs only, ILLUSTRATIVE noise written by hand and never fitted: depolarizing p2 on every cz, a symmetric
    readout flip q, and (key "pay") an illustrative packing cost, a depolarizing `lam` after every conditional of ONE
    part of a circuit that holds two or more conditional parts: "first_bits" the part holding bit 0 (nobody when that
    part has no conditional, e.g. Z first in D1), "first_conditional" the conditional part with the lowest bits.
    Each independent part is simulated alone (density matrix) and the parts are joined shot by shot."""
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error
    from psf_os import feedforward as FF
    from psf_os.ibm import _stamp
    from psf_os.sim import to_clifford_gates
    noise = json.load(open(a.noise))
    job = os.path.join(a.out, "job")
    if os.path.exists(os.path.join(job, "submission.json")):
        raise SystemExit("this job was already run")
    man = json.load(open(os.path.join(job, "manifest.json")))
    shots = man["shots"]
    nm = NoiseModel()
    if noise.get("p2"):
        nm.add_all_qubit_quantum_error(depolarizing_error(float(noise["p2"]), 2), ["cz"])
    q = float(noise.get("q", 0.0))
    if q:
        nm.add_all_qubit_readout_error(ReadoutError([[1 - q, q], [q, 1 - q]]))
    sim = AerSimulator(method="density_matrix", noise_model=nm)
    rows = []
    for k, cfull in enumerate(qpy.load(open(os.path.join(job, "circuits.qpy"), "rb"))):
        parts = [(qs, cs) for qs, cs in FF.components(cfull) if cs]
        subs = [FF.restrict(cfull, qs, cs) for qs, cs in parts]
        has_cond = [any(n == "if_else" for n, _ in FF.walk(s)) for s in subs]
        payer = None
        if sum(has_cond) >= 2 and noise.get("pay"):
            if noise["pay"] == "first_bits":
                j0 = min(range(len(parts)), key=lambda j: min(parts[j][1]))
                payer = j0 if has_cond[j0] else None
            elif noise["pay"] == "first_conditional":
                payer = min((j for j in range(len(parts)) if has_cond[j]), key=lambda j: min(parts[j][1]))
        nb = cfull.num_clbits
        shot_bits = [["0"] * nb for _ in range(shots)]
        for j, ((qs, cs), sub) in enumerate(zip(parts, subs)):
            seed = a.seed + 10 ** 6 * k + 10 ** 4 * j     # strides above the shots: Aer seeds shot by shot from it
            if len(qs) > 12:                   # the Clifford echo sentinel of a dry build: noiseless, never scored here
                cl = None if sub.has_control_flow_op() else to_clifford_gates(sub)
                if cl is None:
                    raise SystemExit(f"circuit {k}: a part of {len(qs)} qubits is too large for the density matrix "
                                     "here; build the dry job with --dry-clifford-sentinel")
                mem = AerSimulator(method="stabilizer").run(cl, shots=shots, memory=True,
                                                            seed_simulator=seed).result().get_memory(0)
            else:
                s2 = _pay(sub, float(noise.get("lam", 0.0))) if j == payer else sub
                mem = sim.run(s2, shots=shots, memory=True, seed_simulator=seed).result().get_memory(0)
            for s, key in enumerate(mem):
                key = key.replace(" ", "")
                for i, bpos in enumerate(cs):
                    shot_bits[s][nb - 1 - bpos] = key[len(key) - 1 - i]
        counts = {}
        for row in shot_bits:
            key = "".join(row)
            counts[key] = counts.get(key, 0) + 1
        rows.append(dict(pub=k, counts=counts))
    t = _stamp()
    jid = f"local-illustrative-noise-{a.seed}"
    json.dump(dict(job_id=jid, submitted=t, local=True, backend=man["fetch"]["backend"], noise=noise, seed=a.seed,
                   simulator="aer per part, ILLUSTRATIVE noise (not fitted to any device)"),
              open(os.path.join(job, "submission.json"), "w"), indent=1)
    json.dump(dict(fetched=t, job_id=jid, status="DONE (local, illustrative noise)", rows=rows),
              open(os.path.join(job, "raw_counts.json"), "w"))
    print(f"dry run written ({len(rows)} circuits)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    b.add_argument("--z-gap", type=int, default=Z_GAP, help="sites skipped between B and Z (default 2) [OWNER]")
    b.add_argument("--dry-clifford-sentinel", action="store_true",
                   help="a Clifford echo sentinel instead of the ring (dry runs only; never for a device)")
    sub.add_parser("check").add_argument("out")
    sub.add_parser("score").add_argument("out")
    d = sub.add_parser("dry")
    d.add_argument("out")
    d.add_argument("noise")
    d.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    res = {"build": build, "check": check, "score": score, "dry": dry}[a.cmd](a)
    sys.exit(0 if res is not False else 1)
