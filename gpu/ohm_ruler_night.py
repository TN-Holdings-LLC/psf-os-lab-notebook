"""Ohm with rulers inside the circuit (workplace Claude, 2026-11-24; home's instruction "オームの「回路の中の物差し」の
晩"; prereg/README.md rule 3; draft prereg/drafts-2026-11-24/ohm_ruler_night_DRAFT.md; not declared).

The 11-23 test (gpu/ohm_window_night.py, read only) read the window's transfer M and W on raw kingston, and the device's
W at t = 3 was 11 to 26 % above the exact value. notes/ohm_window_beside_2026-11-24 read that excess, in that record, as
a uniform shrink of the odd part of <Z> (O = (Z_s - Z_c) / 2 over a string s and its complement c): one factor r of
0.86 to 0.89 per cell. This test declares two rulers that a circuit or its job carries in itself (rule 3):

  (a) the circuit's own total odd part. fSim and RZ keep the number of 1s, so on the circuit's measured qubits the exact
      total T = sum O equals its initial value T0 (known from the bits). rho_a = T_device / T0, per pair;
  (b) the mirror of the same layers in the same job (the compiled circuit and its inverse; ideal: every qubit |0>).
      rho_b = sqrt(mean <Z> of the mirror), one per (arm, t, form).
The ruled window: O_window / rho, read as W_a and W_b (the raw W with O_device replaced by O_device / rho). Their exact
values are the raw W's (rho is 1 without noise). The raw M, W and S are reported as on 11-23, with the same words.

Strings (decided by the bits alone, before any data): the 11-12 generator (left half |1> with probability 0.75, right
half 0.25, and each string's complement), seed SEED, drawn in order; a string is kept when |T0| over every declared
region is at least its threshold (the window's light cone at each t >= 3, and the whole chain when F is built):
THRESH. The first PAIRS kept strings and their complements are the test's strings.

Circuits: as gpu/ohm_window_night.py (N 40 chain, fSim(pi/4, phi) brickwork, arms A0 / A1 / A2): L the light-cone
circuit of the window (positions 20 .. 20 + 2t - 2), F the 40-qubit circuit, L on F's physical qubits. One mirror per
(arm, t, form), on string s00 of that cell (psf-os's user entrance builds it; the floors are not sent unless named).

Subcommands:
  strings [--pairs 7] [--ts 1 3 4] [--forms L]  the kept strings and the draws tried (bits only)
  answers OUT.json [--pairs 7] [--ts ...] [--forms ...]   sealed: per-qubit <Z> of every item and the rulers' exact
                                                 values; prints checks only
  pick QUEUE.json                               as gpu/ohm_window_night.py
  build DEV_DIR OUT ANS_IN ANS_OUT [--shots 1000] [--mirrors TAG ...] [--floors TAG ...] [--max-seconds 60]
  check OUT ANS_OUT                             noise-free, on the job's compiled circuits: per-qubit <Z> within 1e-6
                                                 of the answers, every mirror all zeros, CZ as intended, the exact
                                                 totals equal to T0 (conservation), the twins' windows equal
  score OUT ANS_OUT                             the declared words (the draft's reading tables)
Charge estimate: 2.6 s + 0.000269 s x circuits x shots, with psf-os's model beside.
usage: PYTHONPATH=<psf-os 0.3.3>:<TOQB> python gpu/ohm_ruler_night.py SUBCOMMAND ...
"""
import argparse
import ast
import hashlib
import json
import math
import os
import shutil
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import ohm_answers as OA  # noqa: E402  (read only)
import ohm_window_night as OW  # noqa: E402  (read only: circuits, light cone, placement, pick)

N, H = 40, 20
M_BIAS = 0.5
SEED = 20261124
ARMS = ("A0", "A1", "A2")
CZ_PER_FSIM = {"A0": 2, "A1": 3, "A2": 3}
THRESH = {"cone": 6, "full": 8}         # |T0| at least: each declared light cone (t >= 3), the whole chain (with F)
DRAWS_MAX = 100000
UNIFORM_FLOOR = 0.05                    # a window position takes part in the uniformity test when sum_k O_ex^2 >= this x K
LEVEL = 0.05


def window(t):
    return OW.window(t)


def tag(arm, t, form, name):
    return f"{arm}_t{t}_{form}_{name}"


def regions(ts, forms):
    """{region name: chain positions} whose |T0| the string rule bounds."""
    out = {f"cone_t{t}": OW.cone(t)[0] for t in ts if t >= 3}
    if "F" in forms:
        out["full"] = list(range(N))
    return out


def ruler_a_read(t, form):
    """Ruler (a) is read where the string rule bounds |T0|: F (the whole chain) at every t, L at t >= 3. L at t = 1 has
    4 qubits, whose total can be 0: not read there."""
    return form == "F" or t >= 3


def t0(bits, qs):
    return int(sum(1 - 2 * bits[q] for q in qs))


def strings(pairs, ts, forms):
    """([(name, bits)] for s00.. and c00.., draws tried): the 11-12 generator with SEED, kept by THRESH (bits only)."""
    rng = np.random.default_rng(SEED)
    reg = regions(ts, forms)
    kept, tried = [], 0
    while len(kept) < pairs:
        tried += 1
        if tried > DRAWS_MAX:
            raise SystemExit("STOP: too few strings pass the rule")
        b = [int(rng.random() < ((1 + M_BIAS) / 2 if k < H else (1 - M_BIAS) / 2)) for k in range(N)]
        if all(abs(t0(b, qs)) >= (THRESH["full"] if r == "full" else THRESH["cone"]) for r, qs in reg.items()):
            kept.append(b)
    out = []
    for i, b in enumerate(kept):
        out.append((f"s{i:02d}", b))
        out.append((f"c{i:02d}", [1 - x for x in b]))
    return out, tried


def positions(t, form):
    return OW.positions(t, form)


def charge(circuits, shots):
    return 2.6 + 0.000269 * circuits * shots


# ------------------------------------------------------------------------------------------------------- strings

def cmd_strings(a):
    s, tried = strings(a.pairs, a.ts, a.forms)
    reg = regions(a.ts, a.forms)
    print(f"seed {SEED}, thresholds {THRESH}, regions {list(reg)}: {a.pairs} strings kept of {tried} drawn")
    for n, b in s:
        if n.startswith("s"):
            print(n, "".join(map(str, b)), " T0: " + ", ".join(f"{r} {t0(b, qs):+d}" for r, qs in reg.items()))


# ------------------------------------------------------------------------------------------------------- answers

def cmd_answers(a):
    if os.path.exists(a.out):
        raise SystemExit(f"STOP: {a.out} exists")
    strs, tried = strings(a.pairs, a.ts, a.forms)
    bits_of = dict(strs)
    z, checks = {}, dict(window_L_vs_F=0.0, A0_quimb_vs_free=0.0, total_vs_T0=0.0)
    t_start = time.time()
    for arm in ARMS:
        for t in a.ts:
            for name, bits in strs:
                zf = None
                if "F" in a.forms:
                    zf = OA.z_free(N, t, bits) if arm == "A0" else OA.z_quimb(N, t, arm, bits, 2048, 1e-10)[0]
                    z[tag(arm, t, "F", name)] = [float(x) for x in zf]
                    checks["total_vs_T0"] = max(checks["total_vs_T0"], abs(float(np.sum(zf)) - t0(bits, range(N))))
                    if arm == "A0" and name in ("s00", "c00"):
                        zq = OA.z_quimb(N, t, arm, bits, 2048, 1e-10)[0]
                        checks["A0_quimb_vs_free"] = max(checks["A0_quimb_vs_free"], float(np.abs(zq - zf).max()))
                if "L" in a.forms:
                    zl = OW.z_cone_quimb(arm, t, bits)
                    qs = positions(t, "L")
                    z[tag(arm, t, "L", name)] = [float(x) for x in zl]
                    checks["total_vs_T0"] = max(checks["total_vs_T0"], abs(float(np.sum(zl)) - t0(bits, qs)))
                    if zf is not None:
                        zl_by = dict(zip(qs, zl))
                        checks["window_L_vs_F"] = max(checks["window_L_vs_F"],
                                                      max(abs(zl_by[q] - zf[q]) for q in window(t)))
        print(f"{arm}: {time.time() - t_start:.0f} s", flush=True)
    # the rulers' exact values per pair: the window's odd sum, the circuit's total odd T0 (= the exact total), and
    # the ruled W (equal to the raw W without noise: rho 1)
    rulers = {}
    for arm in ARMS:
        for t in a.ts:
            for form in a.forms:
                pos = positions(t, form)
                w = window(t)
                for k in range(a.pairs):
                    s, c = f"s{k:02d}", f"c{k:02d}"
                    zs, zc = np.array(z[tag(arm, t, form, s)]), np.array(z[tag(arm, t, form, c)])
                    o = (zs - zc) / 2
                    ow = float(sum(o[pos.index(q)] for q in w))
                    tz = t0(bits_of[s], pos)
                    rulers[f"{arm}_t{t}_{form}_k{k:02d}"] = dict(
                        O_window=ow, T0=tz, T_exact=float(o.sum()), rho_a=1.0, rho_b=1.0,
                        a_ratio=ow / tz if ruler_a_read(t, form) else None, ruler_a_read=ruler_a_read(t, form))
    meta = dict(N=N, m=M_BIAS, seed=SEED, thresholds=THRESH, regions={r: q for r, q in regions(a.ts, a.forms).items()},
                draws_tried=tried, pairs=a.pairs, cycles=list(a.ts), forms=list(a.forms), arms=list(ARMS),
                strings={n: "".join(map(str, b)) for n, b in strs},
                positions={f"t{t}_{f}": positions(t, f) for t in a.ts for f in a.forms},
                windows={f"t{t}": window(t) for t in a.ts}, checks=checks, theta=OA.THETA,
                note="per-qubit <Z> by chain position (the order of meta.positions); rulers: exact values per pair")
    json.dump(dict(meta=meta, z=z, rulers=rulers), open(a.out, "w"), sort_keys=True)
    print(f"strings: {a.pairs} kept of {tried} drawn; checks: window L against F {checks['window_L_vs_F']:.1e}; "
          f"A0 quimb against free fermions {checks['A0_quimb_vs_free']:.1e}; |total - T0| {checks['total_vs_T0']:.1e}")
    print("answers", a.out, "sha256", hashlib.sha256(open(a.out, "rb").read()).hexdigest())


# --------------------------------------------------------------------------------------------------------- build

def cmd_build(a):
    sys.path.insert(0, HERE)
    import hub_build as HB
    from qiskit import qpy
    from psf_os import device as Dv
    from psf_os import job as J
    from psf_os import lattice2d as L
    from psf_os import user2d as U
    for p in (a.out, a.ans_out):
        if os.path.exists(p):
            raise SystemExit(f"STOP: {p} exists")
    dev = Dv.Device.load(a.dev)
    A = json.load(open(a.ans_in))
    meta = A["meta"]
    ts, forms = tuple(meta["cycles"]), tuple(meta["forms"])
    strs, _ = strings(meta["pairs"], ts, forms)
    if {n: "".join(map(str, b)) for n, b in strs} != meta["strings"]:
        raise SystemExit("REFUSED: the strings regenerated from the rule differ from the answers file's")
    chain, how = HB.chain_of(dev, N)
    probe = HB.on_chain(OW.logical("A1", 1, "F", strs[0][1]), chain, dev.num_qubits)
    lab, edges, _ = U.analyse(probe, dev)
    dr, dc, m, reasons = L.place(dev, edges, lab)
    phys_of_pos = [int(m[chain[k]]) for k in range(N)]
    items, want = [], {}
    for arm in ARMS:
        for t in ts:
            for form in forms:
                pos = positions(t, form)
                where = [chain[k] for k in pos] if form == "F" else [phys_of_pos[k] for k in pos]
                for name, bits in strs:
                    tg = tag(arm, t, form, name)
                    items.append((tg, HB.on_chain(OW.logical(arm, t, form, bits), where, dev.num_qubits)))
                    want[tg] = dict(positions=pos, given_labels=where, physical=[phys_of_pos[k] for k in pos])
    HB._mirror_from_compiled(dev, U)
    OW._pin_light_cone(L, {frozenset(w["given_labels"]) for tg, w in want.items() if "_L_" in tg})
    first = os.path.join(a.out, "unsent_first_build")
    rep = U.build_batch(dev, items, first, shots=a.shots, max_seconds=1e9)
    bad = []
    for tg, w in want.items():
        got = {str(k): int(v) for k, v in rep["items"][tg]["mapping"].items()}
        if [got[str(lb)] for lb in w["given_labels"]] != w["physical"]:
            bad.append(tg)
    if bad:
        raise SystemExit(f"STOPPED: psf-os placed {len(bad)} items off F's physical qubits (e.g. {bad[:3]}).")
    mirrors = set(a.mirrors) if a.mirrors is not None else {tag(arm, t, f, "s00") for arm in ARMS for t in ts
                                                            for f in forms}
    floors = set(a.floors or [])
    unknown = (mirrors | floors) - set(want)
    if unknown:
        raise SystemExit(f"STOP: --mirrors / --floors name unknown items {sorted(unknown)}")
    runs, unsent = os.path.join(a.out, "runs"), os.path.join(a.out, "unsent_runs")
    shutil.copytree(os.path.join(first, "runs"), runs)
    os.makedirs(unsent)
    for tg in want:
        for suf, keep in (("_floor", tg in floors), ("_mirror", tg in mirrors)):
            if keep:
                continue
            for ext in (".json", ".qpy"):
                p = os.path.join(runs, f"p2d_{tg}{suf}{ext}")
                if os.path.exists(p):
                    shutil.move(p, os.path.join(unsent, os.path.basename(p)))
    man = J.assemble(dev, runs, os.path.join(a.out, "job"), max_seconds=a.max_seconds)
    n_c = len(man["pubs"])
    cz, depth, park = {}, {}, {}
    for tg in want:
        c = qpy.load(open(os.path.join(runs, f"p2d_{tg}.qpy"), "rb"))[0]
        cz[tg] = int(c.count_ops().get("cz", 0))
        depth[tg] = int(c.depth(filter_function=lambda i: i.operation.name == "cz"))
        seen, late = set(), False
        for ins in c.data:
            qs = [c.find_bit(q).index for q in ins.qubits]
            if ins.operation.name == "measure":
                seen.update(qs)
            elif any(q in seen for q in qs):
                late = True
        park[tg] = dict(delays=int(c.count_ops().get("delay", 0)), gate_after_measure=late)
    errs = []
    for tg in want:
        arm, tt, form, _ = tg.split("_")
        t = int(tt[1:])
        if cz[tg] != CZ_PER_FSIM[arm] * OW.fsim_count(t, form):
            errs.append(f"{tg}: CZ {cz[tg]}, intended {CZ_PER_FSIM[arm] * OW.fsim_count(t, form)}")
        if park[tg]["delays"] or park[tg]["gate_after_measure"]:
            errs.append(f"{tg}: a delay or a gate after a measurement")
        if arm == "A1":
            t2 = "A2" + tg[2:]
            if (cz[tg], depth[tg]) != (cz[t2], depth[t2]):
                errs.append(f"{tg[3:]}: A1 / A2 CZ {cz[tg]} / {cz[t2]}, depth {depth[tg]} / {depth[t2]}")
    if errs:
        raise SystemExit("REFUSED: " + "; ".join(errs[:6]))
    answers = {tg: {str(lb): v for lb, v in zip(w["given_labels"], A["z"][tg])} for tg, w in want.items()}
    with open(a.ans_out, "w") as f:
        json.dump(dict(meta=meta, z=answers, rulers=A["rulers"]), f, indent=1, sort_keys=True)
    sec = charge(n_c, a.shots)
    b = dict(device=dev.name, chain=dict(labels=chain, **how), copy_of_F=dict(drow=dr, dcol=dc, passed_over=reasons),
             items=want, cz=cz, cz_depth=depth, mirrors=sorted(mirrors), floors=sorted(floors),
             parking=dict(delays=sum(p["delays"] for p in park.values()),
                          gates_after_a_measurement=sum(p["gate_after_measure"] for p in park.values()),
                          note="no mid-circuit measurement and no delay: nothing to park"),
             shots=a.shots, strings=meta["strings"], pairs=meta["pairs"], cycles=list(ts), forms=list(forms),
             circuits=n_c, charge_seconds=round(sec, 1), qpu_seconds_model_psf_os=man["qpu_seconds_model"],
             circuits_sha256=man.get("circuits_sha256"))
    json.dump(b, open(os.path.join(a.out, "build.json"), "w"), indent=1)
    print(f"device {dev.name}; chain by rule {how['rule']} ({how.get('shape', how.get('start'))}); F copy drow {dr} "
          f"dcol {dc}; every L item on F's physical qubits")
    for arm in ARMS:
        for t in ts:
            for form in forms:
                tg = tag(arm, t, form, "s00")
                print(f"{arm} t {t} {form}: {len(want[tg]['positions'])} qubits, CZ {cz[tg]}, CZ layers {depth[tg]}")
    print(f"mirrors sent for {len(mirrors)} cells; floors {sorted(floors) or 'none'}; circuits {n_c}; {a.shots} shots; "
          f"charge {sec:.1f} s (2.6 + 0.000269 x circuits x shots); psf-os model {man['qpu_seconds_model']} s")
    print("answers by label sha256", hashlib.sha256(open(a.ans_out, "rb").read()).hexdigest())


# --------------------------------------------------------------------------------------------------------- check

def cmd_check(a):
    sys.path.insert(0, HERE)
    import hub_check as HK
    b = json.load(open(os.path.join(a.out, "build.json")))
    A = json.load(open(a.answers))
    ans, rul = A["z"], A["rulers"]
    runs = os.path.join(a.out, "runs")
    res, ok, win = {}, True, {}
    t_all = time.time()
    for tg, w in sorted(b["items"].items()):
        rec = json.load(open(os.path.join(runs, f"p2d_{tg}.json")))
        mp = rec["mapping"] if isinstance(rec["mapping"], dict) else ast.literal_eval(rec["mapping"])
        phys = [int(mp[str(lb)]) for lb in w["given_labels"]]
        z, method = HK.z_of(HK.reduced(HK.load(os.path.join(runs, f"p2d_{tg}.qpy")), phys))
        e = np.array([ans[tg][str(lb)] for lb in w["given_labels"]])
        r = dict(qubits=len(phys), cz=b["cz"][tg], method=method, worst=float(np.abs(z - e).max()))
        good = r["worst"] < 1e-6
        if tg in b["mirrors"]:
            zm, _ = HK.z_of(HK.reduced(HK.load(os.path.join(runs, f"p2d_{tg}_mirror.qpy")), phys))
            r["mirror_worst"] = float(np.abs(zm - 1.0).max())
            good &= r["mirror_worst"] < 1e-6
        arm, tt, form, name = tg.split("_")
        t = int(tt[1:])
        win[tg] = {p: float(z[i]) for i, p in enumerate(w["positions"]) if p in window(t)}
        r["total_minus_T0"] = float(abs(z.sum() - sum(1 - 2 * int(b["strings"][name][p]) for p in w["positions"])))
        good &= r["total_minus_T0"] < 1e-5
        r["ok"] = bool(good)
        ok &= good
        res[tg] = r
        print(f"{tg}: {r['qubits']} qubits, CZ {r['cz']}; {method}: worst {r['worst']:.1e}; |total - T0| "
              f"{r['total_minus_T0']:.1e}" + (f"; mirror {r['mirror_worst']:.1e}" if "mirror_worst" in r else "")
              + f" {'PASS' if good else 'FAIL'}", flush=True)
    twins = 0.0
    for tg in win:
        if "_L_" in tg and tg.replace("_L_", "_F_") in win:
            f = tg.replace("_L_", "_F_")
            twins = max(twins, max(abs(win[tg][p] - win[f][p]) for p in win[tg]))
    ok &= twins < 1e-6
    # the rulers' exact values: T_exact equals T0 for every pair (conservation, from the answers)
    rworst = max(abs(v["T_exact"] - v["T0"]) for v in rul.values())
    ok &= rworst < 1e-6
    res.update(twins_window_worst=twins, rulers_T_exact_minus_T0=rworst, ALL="PASS" if ok else "FAIL",
               seconds=round(time.time() - t_all, 1))
    json.dump(res, open(os.path.join(a.out, "check.json"), "w"), indent=1)
    print(f"twins' windows worst {twins:.1e}; rulers: exact total against T0 worst {rworst:.1e}")
    print("ALL", res["ALL"], f"({res['seconds']} s)")


# --------------------------------------------------------------------------------------------------------- score

def chi2_sf(x, k):
    """Survival function of chi-square with k degrees of freedom (k >= 1)."""
    if k % 2 == 0:
        s, term = 0.0, 1.0
        for i in range(k // 2):
            if i:
                term *= (x / 2) / i
            s += term
        return math.exp(-x / 2) * s
    s = math.erfc(math.sqrt(x / 2))
    term = math.sqrt(2 * x / math.pi) * math.exp(-x / 2)
    for i in range(1, (k - 1) // 2 + 1):
        s += term
        term *= x / (2 * i + 1)
    return s


def word_ruler(d, se):                                      # [OWNER]
    return "AGREES" if abs(d) < 2 * se else "DIFFERS"


def word_uniform(p, n):                                     # [OWNER]
    if n < 2:
        return "NOT READ"
    return "UNIFORM" if p >= LEVEL else "NOT UNIFORM"


READ_UNIFORM_A = {                                          # [OWNER] table 1, per cell at t >= 3
    ("UNIFORM", "AGREES"): "the shrink is one factor on the window, and the circuit's own total carries it: the "
                           "transfer reads through ruler (a)",
    ("UNIFORM", "DIFFERS"): "one factor on the window, but the circuit's total carries another (the outside of the "
                            "window shrinks differently): ruler (a) not read for the transfer",
    ("NOT UNIFORM", "AGREES"): "the total carries the window's mean shrink, but the window's positions differ: the "
                               "transfer reads on the mean only",
    ("NOT UNIFORM", "DIFFERS"): "neither one factor nor the total's: ruler (a) not read",
    ("NOT READ", "AGREES"): "too few window positions to test one factor; ruler (a) agrees",
    ("NOT READ", "DIFFERS"): "too few window positions to test one factor; ruler (a) differs",
}
READ_A_B = {                                                # [OWNER] table 2, per cell with a mirror
    ("AGREES", "AGREES"): "both rulers read the transfer",
    ("AGREES", "DIFFERS"): "the circuit's total reads it; the mirror's square root does not",
    ("DIFFERS", "AGREES"): "the mirror's square root reads it; the circuit's total does not",
    ("DIFFERS", "DIFFERS"): "neither ruler reads it",
}


def _z_and_shotse(counts, rec_labels, labels):
    k_of = {lb: k for k, lb in enumerate(rec_labels)}
    tot = sum(counts.values())
    z = np.zeros(len(labels))
    mean_per_shot = []
    for key, c in counts.items():
        s = key.replace(" ", "")
        v = np.array([1 - 2 * int(s[-1 - k_of[lb]]) for lb in labels])
        z += c * v
        mean_per_shot.append((float(v.mean()), c))
    z /= tot
    mu = sum(m * c for m, c in mean_per_shot) / tot
    var = sum(c * (m - mu) ** 2 for m, c in mean_per_shot) / (tot - 1)
    return z, math.sqrt(var / tot)


def cmd_score(a):
    from psf_os import job as J
    from psf_os import sentinel
    from psf_os import user2d as U
    b = json.load(open(os.path.join(a.out, "build.json")))
    A = json.load(open(a.answers))
    ans = A["z"]
    runs, jobd = os.path.join(a.out, "runs"), os.path.join(a.out, "job")
    read = J.read(jobd, runs)
    zz, mirror, mirror_se, floor = {}, {}, {}, {}
    for name, (rec, cc) in read.items():
        kind = rec.get("psfos_job", {}).get("kind")
        if kind not in ("user2d", "user2d_floor", "user2d_mirror"):
            continue
        tg = U._tag_of(name, rec)
        labels = b["items"][tg]["given_labels"]
        z, se = _z_and_shotse(cc[(rec["points"][0]["input"], "z")], rec["labels"], labels)
        if kind == "user2d":
            zz[tg] = z
        elif kind == "user2d_mirror":
            mirror[tg], mirror_se[tg] = float(z.mean()), se
        else:
            floor[tg] = float(z.mean())
    strs = b["strings"]
    ks = sorted({n[1:] for n in strs})
    ts, forms = b["cycles"], b["forms"]
    res = dict(device=b["device"], cells={}, uniform={}, tables={}, twins={}, order={}, beside={})

    def zex(tg):
        return np.array([ans[tg][str(lb)] for lb in b["items"][tg]["given_labels"]])

    for arm in ARMS:
        for t in ts:
            for form in forms:
                pos = b["items"][tag(arm, t, form, "s00")]["positions"]
                wi = [i for i, p in enumerate(pos) if p in window(t)]
                Od, Oe, T0, M0 = [], [], [], []
                for k in ks:
                    s, c = tag(arm, t, form, "s" + k), tag(arm, t, form, "c" + k)
                    Od.append((zz[s] - zz[c]) / 2)
                    Oe.append((zex(s) - zex(c)) / 2)
                    T0.append(sum(1 - 2 * int(strs["s" + k][p]) for p in pos))
                    M0.append((sum(int(strs["s" + k][p]) for p in window(t)),
                               sum(int(strs["c" + k][p]) for p in window(t))))
                Od, Oe, T0 = np.array(Od), np.array(Oe), np.array(T0, dtype=float)
                nshots = b["shots"]
                VarZ = np.array([[(1 - zz[tag(arm, t, form, p + k)] ** 2) / nshots for p in "sc"] for k in ks])
                const = np.array([-(ms - mc) / 2 for ms, mc in M0])
                w_ex = -Oe[:, wi].sum(axis=1) / 2 + const
                w_raw = -Od[:, wi].sum(axis=1) / 2 + const
                K = len(ks)
                se_k = lambda x: float(np.std(x, ddof=1) / np.sqrt(K))
                d_raw = w_raw - w_ex
                if ruler_a_read(t, form):
                    rho_a = Od.sum(axis=1) / T0
                    w_a = -(Od[:, wi].sum(axis=1) / rho_a) / 2 + const
                    d_a = w_a - w_ex
                # the raw M, W, S as 11-23 (READS at a ratio of 0.5 or below)
                m_dev, m_ex, s_dev = [], [], []
                for j, k in enumerate(ks):
                    for nm, sign in (("s" + k, 1), ("c" + k, -1)):
                        tg = tag(arm, t, form, nm)
                        m0 = sum(int(strs[nm][p]) for p in window(t))
                        m_dev.append(float(((1 - zz[tg][wi]) / 2).sum() - m0))
                        m_ex.append(float(((1 - zex(tg)[wi]) / 2).sum() - m0))
                    s_dev.append(m_dev[-2] + m_dev[-1])
                m_dev, m_ex = np.array(m_dev), np.array(m_ex)
                rM = float(np.mean((m_dev - m_ex) ** 2) / np.mean(m_ex ** 2))
                rW = float(np.mean(d_raw ** 2) / np.mean(w_ex ** 2))
                cell = dict(M_ratio=rM, M="READS" if rM <= 0.5 else "DOES NOT READ", W_ratio=rW,
                            W="READS" if rW <= 0.5 else "DOES NOT READ", W_device=float(w_raw.mean()),
                            W_exact=float(w_ex.mean()), S_device=float(np.mean(s_dev)),
                            W_excess=float(d_raw.mean()), W_excess_2se=2 * se_k(d_raw), errors_M=(m_dev - m_ex).tolist())
                if ruler_a_read(t, form):
                    cell.update(rho_a=rho_a.tolist(), W_a=float(w_a.mean()), d_a=float(d_a.mean()), d_a_2se=2 * se_k(d_a),
                                ruler_a=word_ruler(float(d_a.mean()), se_k(d_a)))
                else:
                    cell.update(ruler_a="NOT READ")
                mt = tag(arm, t, form, "s00")
                if mt in mirror and mirror[mt] > 0:
                    rb = math.sqrt(mirror[mt])
                    w_b = -(Od[:, wi].sum(axis=1) / rb) / 2 + const
                    d_b = w_b - w_ex
                    dmdm = float(np.mean(Od[:, wi].sum(axis=1)) / (4 * mirror[mt] ** 1.5))
                    se_b = math.sqrt(se_k(d_b) ** 2 + (dmdm * mirror_se[mt]) ** 2)
                    cell.update(mirror=mirror[mt], rho_b=rb, W_b=float(w_b.mean()), d_b=float(d_b.mean()),
                                d_b_2se=2 * se_b, ruler_b=word_ruler(float(d_b.mean()), se_b))
                res["cells"][f"{arm}_t{t}_{form}"] = cell
                # uniformity on the window (t >= 3): r per position against the pooled r, bootstrap SEs over pairs
                if t >= 3:
                    use = [i for i in wi if np.sum(Oe[:, i] ** 2) >= UNIFORM_FLOOR * K]

                    # r per position and its shot-noise SE (the null: one factor and shot noise only): var(O_dev) =
                    # (var Z_s + var Z_c) / 4, var Z = (1 - Z^2) / shots, from the device's own <Z>
                    r_pos, se_pos = [], []
                    for i in use:
                        den = float(np.sum(Oe[:, i] ** 2))
                        r_pos.append(float(np.sum(Od[:, i] * Oe[:, i]) / den))
                        var_o = (VarZ[:, 0, i] + VarZ[:, 1, i]) / 4
                        se_pos.append(math.sqrt(float(np.sum(Oe[:, i] ** 2 * var_o))) / den)
                    r_pos, se_pos = np.array(r_pos), np.array(se_pos)
                    wts = 1 / se_pos ** 2 if len(use) else np.array([])
                    r_pool = float(np.sum(wts * r_pos) / np.sum(wts)) if len(use) else float("nan")
                    chi2 = float(np.sum(((r_pos - r_pool) / se_pos) ** 2)) if len(use) >= 2 else 0.0
                    p = chi2_sf(chi2, len(use) - 1) if len(use) >= 2 else float("nan")
                    u = word_uniform(p, len(use))
                    res["uniform"][f"{arm}_t{t}_{form}"] = dict(positions=[pos[i] for i in use], r=r_pos.tolist(),
                                                                se=se_pos.tolist(), r_pool=r_pool, chi2=chi2,
                                                                dof=len(use) - 1, p=p, word=u)
                    res["tables"][f"{arm}_t{t}_{form}"] = dict(table1=READ_UNIFORM_A[(u, cell["ruler_a"])])
                    if "ruler_b" in cell and cell["ruler_a"] != "NOT READ":
                        res["tables"][f"{arm}_t{t}_{form}"]["table2"] = READ_A_B[(cell["ruler_a"], cell["ruler_b"])]
            if "L" in forms and "F" in forms:
                eL = np.array(res["cells"][f"{arm}_t{t}_L"]["errors_M"])
                eF = np.array(res["cells"][f"{arm}_t{t}_F"]["errors_M"])
                dl = eF ** 2 - eL ** 2
                mu, se = float(dl.mean()), float(dl.std(ddof=1) / np.sqrt(len(dl)))
                res["twins"][f"{arm}_t{t}"] = dict(mse_F_minus_mse_L=mu, se=se, verdict="KEEPS MORE" if mu > 2 * se
                                                    else ("KEEPS LESS" if mu < -2 * se else "SAME"))
    for form in forms:
        for t in ts:
            if t < 3:
                continue
            for q in ("W_device", "W_a", "W_b"):
                if any(q not in res["cells"][f"{arm}_t{t}_{form}"] for arm in ARMS):
                    continue
                v = [res["cells"][f"{arm}_t{t}_{form}"][q] for arm in ARMS]
                res["order"][f"{q}_t{t}_{form}"] = "yes" if v[0] > v[1] > v[2] else "no"
        for arm in ARMS:
            for t in ts:
                if t == min(ts):
                    continue
                c1, ct = res["cells"][f"{arm}_t{min(ts)}_{form}"], res["cells"][f"{arm}_t{t}_{form}"]
                g = dict(raw=ct["W_device"] / c1["W_device"], exact=ct["W_exact"] / c1["W_exact"])
                for q in ("W_a", "W_b"):
                    if q in c1 and q in ct:
                        g[q] = ct[q] / c1[q]
                res["beside"][f"{arm}_{form}_W{t}_over_W{min(ts)}"] = g
    res["beside"]["floor_mean"] = floor
    res["beside"]["sentinel"] = sentinel.verdict(jobd, runs)["status"]
    json.dump(res, open(os.path.join(a.out, "scores.json"), "w"), indent=1)
    for k, c in res["cells"].items():
        line = (f"{k}: raw M {c['M']} ({c['M_ratio']:.3f}), W {c['W']} ({c['W_ratio']:.3f}); W device {c['W_device']:.3f} "
                f"exact {c['W_exact']:.3f} (excess {c['W_excess']:+.3f}, 2 SE {c['W_excess_2se']:.3f}); ruler (a) "
                + (f"W {c['W_a']:.3f}, d {c['d_a']:+.3f} (2 SE {c['d_a_2se']:.3f}) {c['ruler_a']}" if "W_a" in c
                   else "NOT READ"))
        if "ruler_b" in c:
            line += f"; ruler (b) sqrt(mirror) {c['rho_b']:.3f}, d {c['d_b']:+.3f} (2 SE {c['d_b_2se']:.3f}) {c['ruler_b']}"
        print(line)
    for k, u in res["uniform"].items():
        print(f"uniform {k}: r by position {[round(x, 3) for x in u['r']]} (pooled {u['r_pool']:.3f}); chi2 "
              f"{u['chi2']:.2f} on {u['dof']} dof, p {u['p']:.3f} -> {u['word']}")
    for k, v in res["tables"].items():
        print(f"reading {k}: " + "; ".join(f"{n}: {s}" for n, s in v.items()))
    for k, v in res["twins"].items():
        print(f"twins {k}: the light-cone circuit {v['verdict']} (MSE F - MSE L {v['mse_F_minus_mse_L']:+.4f}, SE "
              f"{v['se']:.4f})")
    print("order (A0 > A1 > A2): " + ", ".join(f"{k} {v}" for k, v in res["order"].items()))


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)

    def plan(p):
        p.add_argument("--pairs", type=int, default=7)
        p.add_argument("--ts", type=int, nargs="+", default=[1, 3, 4])
        p.add_argument("--forms", nargs="+", default=["L"], choices=["L", "F"])
    p = sp.add_parser("strings")
    plan(p)
    p = sp.add_parser("answers")
    p.add_argument("out")
    plan(p)
    p = sp.add_parser("pick")
    p.add_argument("queue")
    p = sp.add_parser("build")
    p.add_argument("dev")
    p.add_argument("out")
    p.add_argument("ans_in")
    p.add_argument("ans_out")
    p.add_argument("--shots", type=int, default=1000)
    p.add_argument("--mirrors", nargs="*", default=None, help="items with a mirror (default: s00 of every cell)")
    p.add_argument("--floors", nargs="*", default=None, help="items with a floor (default: none)")
    p.add_argument("--max-seconds", type=float, default=60)
    p = sp.add_parser("check")
    p.add_argument("out")
    p.add_argument("answers")
    p = sp.add_parser("score")
    p.add_argument("out")
    p.add_argument("answers")
    a = ap.parse_args()
    if a.cmd == "pick":
        return OW.cmd_pick(a)
    dict(strings=cmd_strings, answers=cmd_answers, build=cmd_build, check=cmd_check, score=cmd_score)[a.cmd](a)


if __name__ == "__main__":
    main()
