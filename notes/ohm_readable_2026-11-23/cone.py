"""Only the qubits the light-cone window needs (home VS, 2026-11-23; desk, no device).

For t = 1..4 cycles and each arm, the window is the 2t - 1 chain sites next to the wall (positions 20 .. 20 + 2t - 2
of N 40). Its backward light cone through the brickwork (even bonds, then odd bonds, per cycle; the field's RZ does not
spread) gives the qubits and the fSim gates that can change the window's <Z>; the circuit of those alone is built and:
  * compiled with qiskit (basis cz, rz, sx, x; a line of qubits; optimization level 2; seed 1) for its CZ count and CZ
    layers, and the full 40-qubit circuit the same way (at t = 3 the full circuit's CZ count is compared with the
    11-12 records' compiled count, 234 / 351);
  * simulated noise-free (quimb CircuitMPS, chi 2048, cutoff 1e-10) on every 11-12 string: the window's <Z> against
    the full 40-qubit circuit's.
A rough guide, never fitted to the device and marked as such: the 11-12 records' uniform shrink 1 - r (mean r per
cell, notes/ohm_idle_2026-11-23/bound.json) is made simply proportional to CZ layers (a line through 0 on the two
cycle counts 3 and 6), and, as a second guide, also to the number of qubits measured (n / 40). Guess, not measured.

usage: python notes/ohm_readable_2026-11-23/cone.py OUT.json
"""
import json
import os
import sys

import numpy as np

NB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(NB, "gpu"))
import ohm_answers as OA  # noqa: E402

N, K, M, SEED = 40, 14, 0.5, 20261112
TS = (1, 2, 3, 4)


def layers(t):
    """[(cycle, parity, [(q, q + 1), ...])] in time order."""
    return [(c, p, [(q, q + 1) for q in range(p, N - 1, 2)]) for c in range(t) for p in (0, 1)]


def cone(t, window):
    """(qubits in the backward light cone, kept gates as (cycle, parity, q))."""
    s, kept = set(window), []
    for c, p, gates in reversed(layers(t)):
        for a, b in gates:
            if a in s or b in s:
                kept.append((c, p, a))
                s |= {a, b}
    return sorted(s), sorted(kept)


def circuit(arm, t, bits, qubits, kept):
    """Logical qiskit circuit on len(qubits) qubits (qubit i = chain position qubits[i])."""
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import UnitaryGate
    phi, H = OA.ARMS[arm]
    G = UnitaryGate(OA.fsim(OA.THETA, phi))
    ix = {q: i for i, q in enumerate(qubits)}
    keep = set(kept)
    qc = QuantumCircuit(len(qubits))
    for q in qubits:
        if bits[q]:
            qc.x(ix[q])
    for c in range(t):
        for p in (0, 1):
            for q in range(p, N - 1, 2):
                if (c, p, q) in keep:
                    qc.append(G, [ix[q], ix[q + 1]])
        if H:
            for q in qubits:
                if OA.PATTERN[q % 3]:
                    qc.rz(H * OA.PATTERN[q % 3], ix[q])
    return qc


def compiled_counts(qc):
    from qiskit import transpile
    from qiskit.transpiler import CouplingMap
    n = qc.num_qubits
    tq = transpile(qc, basis_gates=["cz", "rz", "sx", "x"], coupling_map=CouplingMap.from_line(n),
                   initial_layout=list(range(n)), optimization_level=2, seed_transpiler=1)
    return int(tq.count_ops().get("cz", 0)), int(tq.depth(filter_function=lambda i: i.operation.name == "cz"))


def z_mps(arm, t, bits, qubits, kept):
    """Window-relevant <Z> by quimb on the given qubits and gates (all qubits and gates: the full circuit)."""
    import quimb.tensor as qtn
    phi, H = OA.ARMS[arm]
    ix = {q: i for i, q in enumerate(qubits)}
    keep = set(kept)
    c = qtn.CircuitMPS(len(qubits), max_bond=2048, cutoff=1e-10)
    X = np.array([[0, 1], [1, 0]])
    for q in qubits:
        if bits[q]:
            c.apply_gate_raw(X, (ix[q],))
    G = OA.fsim(OA.THETA, phi)
    for cy in range(t):
        for p in (0, 1):
            for q in range(p, N - 1, 2):
                if (cy, p, q) in keep:
                    c.apply_gate_raw(G, (ix[q], ix[q + 1]))
        if H:
            for q in qubits:
                h = H * OA.PATTERN[q % 3]
                if h:
                    c.apply_gate_raw(np.diag([np.exp(-0.5j * h), np.exp(0.5j * h)]), (ix[q],))
    Z = np.diag([1.0, -1.0])
    return {q: float(np.real(c.psi.local_expectation(Z, ix[q]))) for q in qubits}


def main(out):
    if os.path.exists(out):
        raise SystemExit(f"STOP: {out} exists")
    strs = OA.strings(N, K, M, SEED)
    bound = json.load(open(os.path.join(NB, "notes/ohm_idle_2026-11-23/bound.json")))["cells"]
    res = dict(note="noise-free; compiled counts by qiskit on a line (basis cz, rz, sx, x, level 2); the shrink guide "
                    "is a rough proportional guide from the 11-12 records, never fitted to the device, a guess", rows={})
    allq = list(range(N))
    full_gates = [(c, p, q) for c, p, g in layers(max(TS)) for q, _ in g]
    for arm in ("A0", "A1", "A2"):
        for t in TS:
            win = list(range(N // 2, N // 2 + 2 * t - 1))
            qs, kept = cone(t, win)
            full = [(c, p, q) for (c, p, q) in full_gates if c < t]
            cz_c, lay_c = compiled_counts(circuit(arm, t, strs[0][1], qs, kept))
            cz_f, lay_f = compiled_counts(circuit(arm, t, strs[0][1], allq, full))
            diff = 0.0
            for name, bits in strs:
                zc = z_mps(arm, t, bits, qs, kept)
                zf = z_mps(arm, t, bits, allq, full)
                diff = max(diff, max(abs(zc[q] - zf[q]) for q in win))
            res["rows"][f"{arm}_t{t}"] = dict(window=[win[0], win[-1]], cone_qubits=len(qs), cone_span=[qs[0], qs[-1]],
                                              fsim_cone=len(kept), fsim_full=len(full), cz_cone=cz_c,
                                              cz_layers_cone=lay_c, cz_full=cz_f, cz_layers_full=lay_f,
                                              window_z_cone_vs_full_max=diff)
            print(f"{arm} t {t}: cone {len(qs)} qubits {qs[0]}..{qs[-1]}, fSim {len(kept)} / {len(full)}, CZ {cz_c} / "
                  f"{cz_f}, CZ layers {lay_c} / {lay_f}, window <Z> cone vs full {diff:.1e}", flush=True)
    # rough guide from the records: 1 - r = a x CZ layers, a from the 11-12 cells at t = 3 and 6
    rec = {}
    for dev, path in (("fez", "results/ohm-2026-11-12/ibm_fez/build.json"),
                      ("kingston", "results/ohm-kingston-2026-11-12/ibm_kingston/build.json")):
        b = json.load(open(os.path.join(NB, path)))
        for arm in ("A0", "A1", "A2"):
            xs, ys = [], []
            for t in (3, 6):
                d = [v for k, v in b["cz_depth"].items() if k.startswith(f"{arm}_t{t}_")]
                xs.append(float(np.mean(d)))
                ys.append(1 - bound[f"{dev}_{arm}_t{t}"]["r_mean"])
            a = float(np.dot(xs, ys) / np.dot(xs, xs))
            rec[f"{dev}_{arm}"] = dict(cz_layers_records=xs, one_minus_r_records=ys, per_layer=a)
            for t in TS:
                row = res["rows"][f"{arm}_t{t}"]
                row.setdefault("guide", {})[dev] = dict(
                    r_full_40_by_layers=1 - a * row["cz_layers_full"],
                    r_cone_by_layers=1 - a * row["cz_layers_cone"],
                    r_cone_by_layers_and_qubits=1 - a * row["cz_layers_cone"] * row["cone_qubits"] / N)
    res["guide_from_records"] = rec
    json.dump(res, open(out, "w"), indent=1)
    print("rough guide (not measured): r by CZ layers (records' 1 - r per layer), full 40 / cone / cone x qubits/40")
    for k, row in res["rows"].items():
        print(f"  {k}: " + "; ".join(f"{d} {g['r_full_40_by_layers']:.3f} / {g['r_cone_by_layers']:.3f} / "
                                     f"{g['r_cone_by_layers_and_qubits']:.3f}" for d, g in row["guide"].items()))
    for k, v in rec.items():
        print(f"  {k}: CZ layers {v['cz_layers_records']}, 1 - r {[round(y, 3) for y in v['one_minus_r_records']]}, "
              f"per layer {v['per_layer']:.4f}")


if __name__ == "__main__":
    main(sys.argv[1])
