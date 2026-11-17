"""The next step after T3-A (draft for a declaration; workplace Claude, 2026-11-17, home instruction 17f 1b):
iterative phase estimation at n = 4, every phase phi = j / 16. To be used if T3-A was BEYOND THE CEILING at n = 2 and 3.
Not declared; the numbers and verdict words are the owner's.

  python gpu/apps2_night.py ideal                  exact ff, off and ceiling C(4) (branching simulation, no sampling)
  python gpu/apps2_night.py build DEVDIR OUT [--dry-clifford-sentinel]
  python gpu/apps2_night.py check OUT
  python gpu/apps2_night.py score OUT
  python gpu/apps2_night.py textbook DEVDIR        beside: textbook phase estimation (n counting qubits, coherent
                                                   inverse QFT) on the same record, its CZ and depth (not a job)

Items: ipe4_{j} for j = 0 .. 15 (notes/ffapps_2026-11-17/apps.ipe(4, j)): one ancilla and one target; success = all 4
bits right; the off arm (given explicitly) removes the phase feedback and keeps the ancilla reset. ff, off and floor
arms, one ring sentinel, 4000 shots. All 16 phases: the ceiling C(4) is an average over all phases, so a subset would
need its own ceiling; 16 circuits fit one job (see `build`), so no selection rule is needed.

Verdict (as T3-A): the ff success share of all 16 circuits pooled (every shot counted) against C(4) + 2 SE: BEYOND THE
CEILING, otherwise NOT BEYOND. Beside: the margin at n = 4 next to tonight's n = 2 and 3 (another job: beside only),
the off arm as read, the per-phase ff."""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(NB, "notes", "ffapps_2026-11-17"))
sys.path.insert(0, os.path.join(NB, "notes", "rus_coherent_2026-11-17"))
import apps as AP  # noqa: E402

N = 4
SHOTS = 4000
TOL = 0.03


def ideal():
    r = AP.ipe_ideal(N)
    return dict(n=N, ff=r["ff"], ff_min=r["ff_min"], off=r["off"], ceiling=r["ceiling"])


def items():
    out = []
    for j in range(2 ** N):
        qc, succ = AP.ipe(N, j, True)
        off, _ = AP.ipe(N, j, False)
        out.append((f"ipe{N}_{j}", qc, dict(success=succ, off_circuit=off, form="blocks")))
    return out


def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None   # dry runs only, never a device
    rep = FF.build(Device.load(a.devdir), items(), a.out, shots=SHOTS, max_seconds=160, sentinel_spec=spec)
    print(json.dumps({k: rep[k] for k in ("device", "circuits", "qpu_seconds_model", "shots") if k in rep}))
    v = list(rep["items"].values())
    print(f"per circuit: CZ {min(x['cz'] for x in v)}-{max(x['cz'] for x in v)}, depth {min(x['depth'] for x in v)}-"
          f"{max(x['depth'] for x in v)}, mid {v[0]['mid']}, conditionals {v[0]['conditionals']}, chain {v[0]['chain']}")


def check(a):
    """Noiseless Aer of every arm: ff success 1, off within 0.03 of its exact value per circuit, floor all zero."""
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    from psf_os import feedforward as FF
    import coherent as CO
    m = json.load(open(os.path.join(a.out, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(a.out, "job", "circuits.qpy"), "rb"))
    spec = {t: sp for t, _, sp in items()}
    i, bad = 0, []
    for cell in m["cells"]:
        for _ in range(cell["points"]):
            c = cs[i]
            i += 1
            if cell["role"] == "sentinel":
                continue
            tag = cell["name"][3:].replace("_floor", "").replace("_off", "")
            succ = spec[tag]["success"]
            cc = FF.compact(c)
            n = cc.num_clbits
            cnt = AerSimulator().run(cc, shots=SHOTS, seed_simulator=20261117).result().get_counts()
            tot = sum(cnt.values())
            ok_sh = sum(v for k, v in cnt.items() if all(FF._bits(k, n)[b] == val for b, val in succ.items())) / tot
            allz = sum(v for k, v in cnt.items() if set(FF._bits(k, n)) == {0}) / tot
            if cell["role"] == "floor":
                ok = allz == 1.0
            elif cell["role"] == "user":
                ok = ok_sh == 1.0
            else:
                dist = CO.branch_distribution(spec[tag]["off_circuit"])
                want = sum(p for k, p in dist.items() if all(k[N - 1 - b] == str(v) for b, v in succ.items()))
                ok = abs(ok_sh - want) <= TOL
            print(f"{cell['name']:16s} {cell['role']:6s} success {ok_sh:.3f}  all zero {allz:.3f}  {'ok' if ok else 'FAIL'}")
            bad += [] if ok else [cell["name"]]
    print("PASS" if not bad else f"FAIL {bad}")
    return not bad


def score(a):
    from psf_os import feedforward as FF
    R = ideal()
    cards = FF.cards(a.out)
    cs = [cards[f"ipe{N}_{j}"] for j in range(2 ** N)]
    Nn = sum(c["ff"]["counted"] for c in cs)
    p = sum(c["ff"]["success"] for c in cs) / Nn
    po = sum(c["off"]["success"] for c in cs) / sum(c["off"]["counted"] for c in cs)
    se = math.sqrt(p * (1 - p) / Nn) if 0 < p < 1 else 0.0
    v = "BEYOND THE CEILING" if p >= R["ceiling"] + 2 * se else "NOT BEYOND"
    per = {j: cs[j]["ff"]["success"] / cs[j]["ff"]["counted"] for j in range(2 ** N)}
    out = dict(ff=p, se=se, two_se=2 * se, N=Nn, ceiling=R["ceiling"], margin=p - R["ceiling"], verdict=v,
               off_as_read=po, per_phase_ff=per, sentinel=cs[0]["sentinel"])
    print(f"ipe{N}: ff {p:.4f} (2 SE {2 * se:.4f}, {len(cs)} circuits, {Nn} shots) against the ceiling "
          f"{R['ceiling']:.4f} -> {v}; margin {p - R['ceiling']:+.4f}; off as read {po:.4f}; sentinel {cs[0]['sentinel']}")
    print("per phase ff: " + " ".join(f"{j}:{x:.3f}" for j, x in per.items()))
    json.dump(out, open(os.path.join(a.out, "apps2_scores.json"), "w"), indent=1)


def textbook_circuit(n, j):
    """Textbook phase estimation of U = P(2 pi j / 2^n) on |1>: counting qubits 0 .. n-1 (qubit k carries bit k of
    the estimate after the inverse QFT, swaps included), target n."""
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import QFT
    phi = j / 2 ** n
    qc = QuantumCircuit(n + 1)
    qc.x(n)
    for k in range(n):
        qc.h(k)
        qc.cp(2 * math.pi * phi * 2 ** k, k, n)
    qc.compose(QFT(n, inverse=True, do_swaps=True), qubits=list(range(n)), inplace=True)
    return qc


def textbook(a):
    """Beside: CZ and depth of textbook phase estimation on the same record (rule C line, the fixed line routing of
    notes/rus_coherent_2026-11-17, psf-os's map-free compiler). Noiseless correctness checked (all n bits right)."""
    from qiskit import transpile
    from qiskit.quantum_info import Statevector
    from psf_os.device import Device
    import coherent as CO
    dev = Device.load(a.devdir)
    rows = {}
    for n in (2, 3, 4):
        cz, dep = [], []
        for j in range(2 ** n):
            qc = textbook_circuit(n, j)
            probs = Statevector(qc).probabilities_dict(qargs=list(range(n)))
            want = format(j, f"0{n}b")
            assert abs(probs.get(want, 0) - 1) < 1e-9, (n, j, probs)
            flat = transpile(qc, basis_gates=["cx", "u"], optimization_level=1, seed_transpiler=0)
            line, pos, swaps = CO.route_line(flat)
            meas = [(pos[k], k) for k in range(n)]
            c, chain = CO.on_device(dev, CO.to_basis(line), meas)
            st = CO.stats(c)
            cz.append(st["cz"])
            dep.append(st["depth"])
        rows[n] = dict(qubits=n + 1, cz_min=min(cz), cz_max=max(cz), depth_min=min(dep), depth_max=max(dep))
        print(f"textbook n {n}: {n + 1} qubits, CZ {min(cz)}-{max(cz)}, depth {min(dep)}-{max(dep)} (all phases, "
              f"noiseless all bits right)")
    json.dump(rows, open(os.path.join(NB, "notes", "ffapps_2026-11-17", "textbook_qpe.json"), "w"), indent=1)


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
    sub.add_parser("textbook").add_argument("devdir")
    a = ap.parse_args()
    if a.cmd == "ideal":
        r = ideal()
        print(f"n {N}: ff {r['ff']:.4f} (min over phi {r['ff_min']:.4f}); off as read {r['off']:.4f}; ceiling C(4) "
              f"{r['ceiling']:.4f}; margin {r['ff'] - r['ceiling']:+.4f}")
        sys.exit(0)
    r = {"build": build, "check": check, "score": score, "textbook": textbook}[a.cmd](a)
    sys.exit(0 if r is not False else 1)
