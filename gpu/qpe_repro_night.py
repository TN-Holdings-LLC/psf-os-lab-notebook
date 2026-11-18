"""Phase estimation, reproduced and compared (draft for a declaration; workplace Claude, 2026-11-18, owner's "1" and
home's supplement "職場クロードへの補足_位相推定の比較_2026-11-18"). Not declared; verdict words, thresholds, shots
and predictions are the owner's ([OWNER] in prereg/drafts-2026-11-19/qpe_repro_DRAFT.md).

What is reproduced: the iterative phase estimation (IPE) with dynamic circuits of Corcoles et al., PRL 127, 100501
(2021), here in the form of notes/ffapps_2026-11-17 (one ancilla, one target in |1>, U = P(2 pi phi), phi = j / 2^n
for every j; the bits read least significant first with the phase feedback and a conditional-X reset). New against
the paper and against 11-17 (T3-A on fez n = 2, 3; N3 on marrakesh n = 4): n = 2, 3, 4 on the same device the same
night, and beside each n the textbook phase estimation (n counting qubits, coherent inverse QFT, final measurements
only) of the same phases. (The paper's own baseline was Kitaev's non-adaptive estimation, not the textbook circuit.)

Two yardsticks with their own words (home's supplement 1):
  - IPE against its ceiling C(n), the best fixed decoder of the off arm's bits (the noiseless value of the circuit
    without feedback): BEYOND THE CEILING / NOT BEYOND, as T3-A and N3.
  - IPE against the textbook circuit, per shot, no correction: the share of shots with all n bits right. The textbook
    circuit reads every phi exactly noiselessly, so it has no ceiling: this yardstick is the essence number only, not a
    ceiling claim. Draft words [OWNER]: IPE RIGHT MORE OFTEN / TEXTBOOK RIGHT MORE OFTEN / NOT SEPARATED.

  python gpu/qpe_repro_night.py ideal
  python gpu/qpe_repro_night.py build DEVDIR OUT --part A|B [--shots S] [--dry-clifford-sentinel]
        part A: n = 2, 3 (IPE and textbook, 24 items); part B: n = 4 (32 items). Every ratio and difference that is
        judged is read within one job.
  python gpu/qpe_repro_night.py check OUT
  python gpu/qpe_repro_night.py dry OUT NOISE.json [--seed S]     dry runs only (illustrative noise, never fitted)
  python gpu/qpe_repro_night.py score OUT [OUT2]
  python gpu/qpe_repro_night.py digest OUT       the circuits' digest, comparable across qiskit versions (part.json
                                                  also keeps circuits_sha256, the digest and the versions)
  The noiseless dry run is psf_os.feedforward.run_local(OUT, seed=20261119), not `dry`.

Placement: rule C chains (psf-os feedforward.place: coupling graph and failed marks only); no calibration error number
is read. The textbook circuit is routed on a line by the fixed rule of notes/rus_coherent_2026-11-17 (no search).
Its off arm is the same circuit (it has no conditionals): kept as a same-job replicate, beside, never judged."""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(NB, "notes", "ffapps_2026-11-17"))
sys.path.insert(0, os.path.join(NB, "notes", "rus_coherent_2026-11-17"))
sys.path.insert(0, os.path.join(NB, "notes", "os2_2026-11-18"))
import apps as AP  # noqa: E402

PARTS = {"A": (2, 3), "B": (4,)}
SHOTS = 2000          # [OWNER]: 2000 keeps each part near 60 s by the model; 4000 doubles it
TOL = 0.03
SEED = 20261119


def textbook_logical(n, j):
    """Textbook phase estimation of U = P(2 pi j / 2^n) on |1>, routed on a line, in CZ / RZ / SX / X, with clbit k =
    bit k of j (k = 0 least significant) read from the line position the router leaves counting qubit k on."""
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister, transpile
    import apps2_night as A2
    import coherent as CO
    flat = transpile(A2.textbook_circuit(n, j), basis_gates=["cx", "u"], optimization_level=1, seed_transpiler=0)
    line, pos, swaps = CO.route_line(flat)
    body = CO.to_basis(line)
    q, c = QuantumRegister(n + 1, "q"), ClassicalRegister(n, "c")
    qc = QuantumCircuit(q, c)
    qc.compose(body, qubits=list(range(n + 1)), inplace=True)
    for k in range(n):
        qc.measure(pos[k], k)
    return qc, {k: (j >> k) & 1 for k in range(n)}, swaps


def items(part):
    out = []
    for n in PARTS[part]:
        for j in range(2 ** n):
            qc, succ = AP.ipe(n, j, True)
            off, _ = AP.ipe(n, j, False)
            out.append((f"ipe{n}_{j}", qc, dict(success=succ, off_circuit=off, form="blocks")))
        for j in range(2 ** n):
            qc, succ, _ = textbook_logical(n, j)
            out.append((f"tqpe{n}_{j}", qc, dict(success=succ, form="pauli")))
    return out


def ideal():
    rows = {}
    for n in (2, 3, 4):
        r = AP.ipe_ideal(n)
        rows[n] = dict(ipe_ff=r["ff"], ipe_ff_min=r["ff_min"], ipe_off=r["off"], ceiling=r["ceiling"])
    return rows


def textbook_ideal(n):
    """Noiseless success of every textbook circuit as built (statevector of the routed CZ circuit): 1 for each j."""
    from qiskit.quantum_info import Statevector
    worst = 1.0
    for j in range(2 ** n):
        qc, succ, _ = textbook_logical(n, j)
        sv = Statevector(qc.remove_final_measurements(inplace=False))
        meas = {}
        for ins in qc.data:
            if ins.operation.name == "measure":
                meas[qc.find_bit(ins.clbits[0]).index] = qc.find_bit(ins.qubits[0]).index
        p = sv.probabilities_dict(qargs=[meas[k] for k in range(n)])
        want = "".join(str(succ[k]) for k in reversed(range(n)))
        worst = min(worst, p.get(want, 0.0))
    return worst


def _gates(circuit, qmap=None, cmap=None):
    """Gate list that also opens conditional blocks (psf_os.gatehash writes a block's parameters as str() of the block,
    a text drawing that changes with the qiskit version; the workplace VS's check of 2026-11-18, item 2)."""
    from psf_os.gatehash import _param
    qmap = qmap or {q: circuit.find_bit(q).index for q in circuit.qubits}
    cmap = cmap or {c: circuit.find_bit(c).index for c in circuit.clbits}
    out = []
    for ins in circuit.data:
        op = ins.operation
        qs = [qmap[q] for q in ins.qubits]
        cs = [cmap[c] for c in ins.clbits]
        if op.name == "if_else":
            cond = op.condition
            bit = cmap[cond[0]] if cond[0] in cmap else str(cond[0])
            blocks = []
            for blk in op.blocks:
                if blk is None:
                    blocks.append(None)
                    continue
                qm = {bq: qs[i] for i, bq in enumerate(blk.qubits)}
                cm = {bc: cs[i] for i, bc in enumerate(blk.clbits)}
                blocks.append(_gates(blk, qm, cm))
            out.append(["if_else", qs, cs, [bit, int(cond[1])], blocks])
        else:
            out.append([op.name, qs, cs, [_param(p) for p in op.params]])
    return out


def circuits_digest(path):
    """SHA-256 of the canonical JSON of every circuit's gate list, conditional blocks opened: comparable across
    qiskit versions, where circuits_sha256 (the QPY bytes) is not."""
    import hashlib
    from qiskit import qpy
    cs = qpy.load(open(path, "rb"))
    doc = [dict(num_qubits=c.num_qubits, num_clbits=c.num_clbits, gates=_gates(c)) for c in cs]
    return hashlib.sha256(json.dumps(doc, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _versions():
    import subprocess
    import qiskit
    import qiskit_aer
    import psf_os
    try:
        head = subprocess.run(["git", "-C", os.path.dirname(os.path.dirname(psf_os.__file__)), "rev-parse",
                               "--short=7", "HEAD"], capture_output=True, text=True).stdout.strip() or None
    except OSError:
        head = None
    return dict(qiskit=qiskit.__version__, qiskit_aer=qiskit_aer.__version__, psf_os=head,
                python=sys.version.split()[0])


def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None   # dry runs only, never a device
    rep = FF.build(Device.load(a.devdir), items(a.part), a.out, shots=a.shots, max_seconds=a.max_seconds,
                   sentinel_spec=spec)
    man = json.load(open(os.path.join(a.out, "job", "manifest.json")))
    info = dict(part=a.part, ns=list(PARTS[a.part]), shots=a.shots, device=rep["device"], circuits=rep["circuits"],
                qpu_seconds_model=rep["qpu_seconds_model"], circuits_sha256=man["circuits_sha256"],
                circuits_digest=circuits_digest(os.path.join(a.out, "job", "circuits.qpy")), versions=_versions())
    json.dump(info, open(os.path.join(a.out, "part.json"), "w"), indent=1)
    print(json.dumps(info))
    for n in PARTS[a.part]:
        for fam in ("ipe", "tqpe"):
            v = [x for t, x in rep["items"].items() if t.startswith(f"{fam}{n}_")]
            print(f"{fam}{n}: {len(v)} items, CZ {min(x['cz'] for x in v)}-{max(x['cz'] for x in v)}, depth "
                  f"{min(x['depth'] for x in v)}-{max(x['depth'] for x in v)}, mid {max(x['mid'] for x in v)}, "
                  f"conditionals {max(x['conditionals'] for x in v)}, qubits {v[0]['n']}")


def _spec_by_tag(part):
    return {t: sp for t, _, sp in items(part)}


def check(a):
    """Noiseless Aer of every arm: ff success 1 (IPE and textbook), the IPE off arm within 0.03 of its exact value,
    the textbook replicate arm 1, every floor all zero."""
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    from psf_os import feedforward as FF
    import coherent as CO
    part = json.load(open(os.path.join(a.out, "part.json")))
    m = json.load(open(os.path.join(a.out, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(a.out, "job", "circuits.qpy"), "rb"))
    spec = _spec_by_tag(part["part"])
    i, bad = 0, []
    for cell in m["cells"]:
        for _ in range(cell["points"]):
            c = cs[i]
            i += 1
            if cell["role"] == "sentinel":
                continue
            tag = cell["name"][3:].replace("_floor", "").replace("_off", "")
            succ = spec[tag]["success"]
            n = len(succ)
            cc = FF.compact(c)
            nb = cc.num_clbits
            cnt = AerSimulator().run(cc, shots=part["shots"], seed_simulator=SEED).result().get_counts()
            tot = sum(cnt.values())
            ok_sh = sum(v for k, v in cnt.items() if all(FF._bits(k, nb)[b] == val for b, val in succ.items())) / tot
            allz = sum(v for k, v in cnt.items() if set(FF._bits(k, nb)) == {0}) / tot
            if cell["role"] == "floor":
                ok = allz == 1.0
            elif cell["role"] == "user" or tag.startswith("tqpe"):
                ok = ok_sh == 1.0
            else:
                dist = CO.branch_distribution(spec[tag]["off_circuit"])
                want = sum(p for k, p in dist.items() if all(k[n - 1 - b] == str(v) for b, v in succ.items()))
                ok = abs(ok_sh - want) <= TOL
            if not ok or a.verbose:
                print(f"{cell['name']:18s} {cell['role']:6s} success {ok_sh:.3f}  all zero {allz:.3f}  "
                      f"{'ok' if ok else 'FAIL'}")
            bad += [] if ok else [cell["name"]]
    print(f"{i} circuits; " + ("PASS" if not bad else f"FAIL {bad}"))
    return not bad


def _dephase_after_conditionals(cc, lam):
    """Illustrative stand-in for the wait a conditional costs: phase damping lam on every qubit after each top-level
    conditional block (dry runs only; makes the per-shot comparison read the other way when lam is large)."""
    from qiskit_aer.noise import phase_damping_error
    if not lam:
        return cc
    err = phase_damping_error(lam).to_instruction()
    out = cc.copy_empty_like()
    for ins in cc.data:
        out.append(ins.operation, ins.qubits, ins.clbits)
        if ins.operation.name == "if_else":
            for q in out.qubits:
                out.append(err, [q])
    return out


def dry(a):
    """Dry runs only: every circuit under an ILLUSTRATIVE noise written by hand (never fitted, no calibration number):
    depolarizing p2 on every CZ, damping gamma on the other qubits at each mid-circuit read (the workplace VS's
    branch_noise.noisy_circuit), readout p00 / p11 per physical qubit. Writes the job's submission.json and
    raw_counts.json as psf_os.feedforward.run_local does (local=True, the noise written in)."""
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import depolarizing_error
    from psf_os import feedforward as FF
    from psf_os.ibm import _stamp
    from psf_os.sim import to_clifford_gates
    import branch_noise as BN
    noise = json.load(open(a.noise))
    job = os.path.join(a.out, "job")
    sub = os.path.join(job, "submission.json")
    if os.path.exists(sub):
        raise SystemExit(f"{sub} exists: this job was already run")
    man = json.load(open(os.path.join(job, "manifest.json")))
    circs = qpy.load(open(os.path.join(job, "circuits.qpy"), "rb"))
    rows = []
    for k, c in enumerate(circs):
        phys = sorted({q for _, qs in FF.walk(c) for q in qs})
        cc = FF.compact(c)
        seed = a.seed + BN.WIDE_CIRCUIT * k
        cl = None if cc.has_control_flow_op() else to_clifford_gates(cc)
        if cl is not None and cc.num_qubits > FF.LOCAL_MAX_QUBITS:
            res = AerSimulator(method="stabilizer").run(cl, shots=man["shots"], seed_simulator=seed).result()
        else:
            nm = BN.readout_model(phys, noise)
            if noise.get("p2"):
                nm.add_all_qubit_quantum_error(depolarizing_error(float(noise["p2"]), 2), ["cz"])
            sim = AerSimulator(method="density_matrix", noise_model=nm)
            nc = _dephase_after_conditionals(BN.noisy_circuit(cc, noise.get("gamma", 0.0)), noise.get("dephase_cond", 0.0))
            res = sim.run(nc, shots=man["shots"], seed_simulator=seed).result()
        rows.append(dict(pub=k, counts={key.replace(" ", ""): v for key, v in res.get_counts(0).items()}))
    t = _stamp()
    jid = f"local-illustrative-noise-{a.seed}"
    json.dump(dict(job_id=jid, submitted=t, local=True, backend=man["fetch"]["backend"],
                   simulator="aer, ILLUSTRATIVE noise (not fitted to any device)", noise=noise, seed=a.seed,
                   circuit_stride=BN.WIDE_CIRCUIT), open(sub, "w"), indent=1)
    json.dump(dict(fetched=t, job_id=jid, status="DONE (local, illustrative noise)", rows=rows),
              open(os.path.join(job, "raw_counts.json"), "w"))
    print(f"dry run written ({len(rows)} circuits, {jid}, noise {noise})")


def _pool(cs, arm):
    N = sum(c[arm]["counted"] for c in cs)
    p = sum(c[arm]["success"] for c in cs) / N
    se = math.sqrt(p * (1 - p) / N) if 0 < p < 1 else 0.0
    return p, se, N


def ceiling_verdict(p, se, C):                  # T3-A / N3 words
    return "BEYOND THE CEILING" if p >= C + 2 * se else "NOT BEYOND"


def per_shot_verdict(d, se_d):                  # draft words [OWNER]
    if d > 0 and d >= 2 * se_d:                 # strict: equal shares (e.g. both 1 noiselessly) never separate
        return "IPE RIGHT MORE OFTEN"
    if d < 0 and d <= -2 * se_d:
        return "TEXTBOOK RIGHT MORE OFTEN"
    return "NOT SEPARATED"


def score_part(out, R):
    from psf_os import feedforward as FF
    part = json.load(open(os.path.join(out, "part.json")))
    cards = FF.cards(out)
    res = {}
    for n in part["ns"]:
        ipe = [cards[f"ipe{n}_{j}"] for j in range(2 ** n)]
        tb = [cards[f"tqpe{n}_{j}"] for j in range(2 ** n)]
        p, sp, Np = _pool(ipe, "ff")
        q, sq, Nq = _pool(tb, "ff")
        po, _, _ = _pool(ipe, "off")
        qr, sqr, _ = _pool(tb, "off")
        C = R[n]["ceiling"]
        d, sd = p - q, math.sqrt(sp ** 2 + sq ** 2)
        res[n] = dict(
            ipe=dict(ff=p, two_se=2 * sp, N=Np, ceiling=C, margin=p - C, verdict=ceiling_verdict(p, sp, C),
                     off_as_read=po, per_phase={j: c["ff"]["success"] / c["ff"]["counted"] for j, c in enumerate(ipe)}),
            textbook=dict(ff=q, two_se=2 * sq, N=Nq, replicate_arm=qr, replicate_minus_ff=qr - q,
                          per_phase={j: c["ff"]["success"] / c["ff"]["counted"] for j, c in enumerate(tb)}),
            per_shot=dict(d=d, two_se=2 * sd, verdict=per_shot_verdict(d, sd)),
            sentinel=ipe[0]["sentinel"])
        print(f"n {n}: IPE {p:.4f} (2 SE {2 * sp:.4f}, {Np} shots) against the ceiling {C:.4f} -> "
              f"{res[n]['ipe']['verdict']} (margin {p - C:+.4f}); off as read {po:.4f}")
        print(f"     textbook {q:.4f} (2 SE {2 * sq:.4f}); IPE - textbook {d:+.4f} (2 SE {2 * sd:.4f}) -> "
              f"{res[n]['per_shot']['verdict']}; beside: replicate arm {qr:.4f} ({qr - q:+.4f}); sentinel "
              f"{ipe[0]['sentinel']}")
    return part, res


def score(a):
    R = ideal()
    allres = {}
    for out in [a.out] + ([a.out2] if a.out2 else []):
        part, res = score_part(out, R)
        allres[part["part"]] = res
        json.dump(dict(part=part, results=res), open(os.path.join(out, "qpe_scores.json"), "w"), indent=1)
    flat = {n: r for res in allres.values() for n, r in res.items()}
    if len(flat) > 1:
        print("beside (across jobs, never judged): IPE margin over the ceiling by n: " +
              ", ".join(f"n {n} {flat[n]['ipe']['margin']:+.4f}" for n in sorted(flat)) +
              "; IPE - textbook by n: " + ", ".join(f"n {n} {flat[n]['per_shot']['d']:+.4f}" for n in sorted(flat)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ideal")
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    b.add_argument("--part", choices=sorted(PARTS), required=True)
    b.add_argument("--shots", type=int, default=SHOTS)
    b.add_argument("--max-seconds", type=float, default=70)
    b.add_argument("--dry-clifford-sentinel", action="store_true",
                   help="dry runs only: the ring sentinel at its Clifford point; never for the device job")
    c = sub.add_parser("check")
    c.add_argument("out")
    c.add_argument("--verbose", action="store_true")
    d = sub.add_parser("dry")
    d.add_argument("out")
    d.add_argument("noise")
    d.add_argument("--seed", type=int, default=SEED)
    sub.add_parser("digest").add_argument("out")
    s = sub.add_parser("score")
    s.add_argument("out")
    s.add_argument("out2", nargs="?")
    a = ap.parse_args()
    if a.cmd == "ideal":
        for n, r in ideal().items():
            print(f"n {n}: IPE ff {r['ipe_ff']:.4f} (min {r['ipe_ff_min']:.4f}); off as read {r['ipe_off']:.4f}; "
                  f"ceiling {r['ceiling']:.4f}; margin {r['ipe_ff'] - r['ceiling']:+.4f}; textbook as built: worst "
                  f"phase {textbook_ideal(n):.6f}")
        sys.exit(0)
    if a.cmd == "digest":
        print(circuits_digest(os.path.join(a.out, "job", "circuits.qpy")))
        sys.exit(0)
    r = {"build": build, "check": check, "dry": dry, "score": score}[a.cmd](a)
    sys.exit(0 if r is not False else 1)
