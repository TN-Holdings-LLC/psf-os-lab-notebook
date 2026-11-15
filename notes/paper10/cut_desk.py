"""Paper 10, first test, desk part (workplace, 2026-11-16; draft, not declared, no device): the 81-qubit XX chain with
the bond between sites 32 and 33 (the 33rd and 34th qubits) cut, everything else as the size test and the light-cone
repeat of 11-14 (gpu/ffxx91.py on the ibm_marrakesh record of the repeat).

Arms (each a full job as ffxx91 builds it: theta pi/4 and pi/2, steps 2, 4, 8, 12, 16 = 8 to 64 CZ layers):
  N33        the 33-qubit chain (the first 33 qubits of the 81-qubit chain, checked)
  N81        the 81-qubit chain, as on 11-14
  N81cut     the 81-qubit chain, the gate on bond (32, 33) replaced by CZ, barrier, CZ (an identity with the same two
             CZ on the same coupler; the barrier keeps the compiler from cancelling them, as the Hubbard U = 0 ruler)
  N81idle    the 81-qubit chain, the gate on bond (32, 33) left out (the coupler idles)
The other 48 qubits run exactly the gates they run in N81; only the coupling across the cut is gone.

Checks here:
  1. exact answers: the cut chain's first 33 sites equal the 33-qubit chain's at every step and both angles (free
     fermions; the cut decouples the two segments); no amplitude crosses the cut (the single-particle matrix is block-diagonal);
  2. the N33 and N81 builds equal the recorded 11-14 repeat circuits by gate hash (so the arms are built as declared
     then); CZ counts and depths of the four arms; the placement of N81cut / N81idle equals N81's;
  3. stim, theta = pi/2 (Clifford), one uniform local noise model (as notes/xxcone_2026-11-14/stim_noise.py: CZ
     depolarising 0.003, single-qubit 0.0003, readout 0.015; nothing from the device): the block gaps
     g = r(N33) - r(arm) on the 33 shared qubits for N81, N81cut and N81idle stay at zero; and, as an illustration
     only (not a fit), the same with the CZ error tripled on couplers touching the extension (as stim_ext.py), with
     the cut coupler counted as touching it.
usage: PYTHONPATH=<psf-os>:<notebook>:<notebook>/gpu python notes/paper10/cut_desk.py DEV_DIR WORK [REPEAT_RUNS_DIR]
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "gpu"))
import ff_xx as F  # noqa: E402

CUT = 32
STEPS = (2, 4, 8, 12, 16)
THETAS = (math.pi / 4, math.pi / 2)
BLOCKS = {"far": range(0, 11), "mid": range(11, 22), "near": range(22, 33)}
P2, P1, PM, SHOTS, BOOST = 0.003, 0.0003, 0.015, 20000, 3.0


def tag(n, th, s, arm=""):
    return f"N{n}{arm}_th{int(round(th * 1000)):04d}_s{s:02d}"


def single_particle_cut(N, steps, theta, cut=CUT):
    c, s = np.cos(theta), np.sin(theta)
    block = np.array([[c, -1j * s], [-1j * s, c]])
    U = np.eye(N, dtype=complex)
    for _ in range(steps):
        for start in (0, 1):
            layer = np.eye(N, dtype=complex)
            for a in range(start, N - 1, 2):
                if a != cut:
                    layer[a:a + 2, a:a + 2] = block
            U = layer @ U
    return U


def z_cut(N, steps, theta):
    occ = list(range(1, N, 2))
    U = single_particle_cut(N, steps, theta)
    return 1 - 2 * np.sum(np.abs(U[:, occ]) ** 2, axis=1)


def circuit_arm(N, steps, theta, arm):
    """N81cut ('cut'): CZ, barrier, CZ on the cut bond; N81idle ('idle'): nothing on it; '' : the ffxx91 circuit."""
    from qiskit import QuantumCircuit
    if not arm:
        return F.circuit(N, steps, theta, measure=False)
    qc = QuantumCircuit(N)
    for q in range(1, N, 2):
        qc.x(q)
    for _ in range(steps):
        for start in (0, 1):
            for a in range(start, N - 1, 2):
                if a == CUT:
                    if arm == "cut":
                        qc.cz(a, a + 1)
                        qc.barrier(a, a + 1)
                        qc.cz(a, a + 1)
                    continue
                F.xxyy(qc, theta, a, a + 1)
    return qc


def build(dev, n, arm, work):
    """One job as gpu/ffxx91.py builds it (chain_of, on_chain, the compiled mirror, user2d.build_batch)."""
    import hub_build as HB
    from psf_os import user2d as U
    labels, how = HB.chain_of(dev, n)
    items = [(tag(n, th, s, {"cut": "cut", "idle": "idle"}.get(arm, "")),
              HB.on_chain(circuit_arm(n, s, th, arm), labels, dev.num_qubits)) for th in THETAS for s in STEPS]
    out = os.path.join(work, f"N{n}{arm}")
    HB._mirror_from_compiled(dev, U)
    rep = U.build_batch(dev, items, out, shots=4000, max_seconds=160)
    return out, labels, how, rep


def to_stim(c, ext=None, noise=True):
    import stim
    s, meas = stim.Circuit(), []
    idx = {q: c.find_bit(q).index for q in c.qubits}
    for ins in c.data:
        n, qs = ins.operation.name, [idx[q] for q in ins.qubits]
        if n == "rz":
            k = round(float(ins.operation.params[0]) / (math.pi / 2)) % 4
            if k:
                s.append({1: "S", 2: "Z", 3: "S_DAG"}[k], qs)
        elif n in ("sx", "x"):
            s.append("SQRT_X" if n == "sx" else "X", qs)
            if noise:
                s.append("DEPOLARIZE1", qs, P1)
        elif n == "cz":
            s.append("CZ", qs)
            if noise:
                s.append("DEPOLARIZE2", qs, P2 * (BOOST if ext and set(qs) & ext else 1))
        elif n == "measure":
            meas.append(qs[0])
    if noise:
        s.append("X_ERROR", meas, PM)
    s.append("M", meas)
    return s, meas


def z_stim(runs, t, ext=None):
    from qiskit import qpy
    (c,) = qpy.load(open(os.path.join(runs, f"p2d_{t}.qpy"), "rb"))
    labels = json.load(open(os.path.join(runs, f"p2d_{t}.json")))["labels"]
    s, meas = to_stim(c, ext)
    ideal = 1 - 2 * to_stim(c, noise=False)[0].compile_sampler().sample(1)[0].astype(float)
    smp = 1 - 2 * s.compile_sampler(seed=1116).sample(SHOTS).astype(float)
    z, e = dict(zip(meas, smp.mean(axis=0))), dict(zip(meas, ideal))
    return np.array([z[q] for q in labels]), np.array([e[q] for q in labels]), labels


def main(dev_dir, work, repeat_runs=None):
    from psf_os import device as Dv
    from psf_os import gatehash
    from qiskit import qpy
    os.makedirs(work, exist_ok=True)
    res = {}
    # 1. exact answers
    worst = 0.0
    for th in THETAS:
        for s in STEPS:
            zc = z_cut(81, s, th)
            worst = max(worst, float(np.max(np.abs(zc[:33] - F.z_exact(33, s, th)))))
            U = single_particle_cut(81, s, th)                  # the cut makes U block-diagonal (33 + 48)
            worst = max(worst, float(np.max(np.abs(U[:33, 33:]))), float(np.max(np.abs(U[33:, :33]))))
    res["exact_cut_first33_equals_N33_worst"] = worst
    print(f"1. exact: cut chain's first 33 = N33, nothing crosses the cut; worst {worst:.1e}")
    # 2. builds
    dev = Dv.Device.load(dev_dir)
    builds = {}
    for n, arm in ((33, ""), (81, ""), (81, "cut"), (81, "idle")):
        out, labels, how, rep = build(dev, n, arm, work)
        builds[(n, arm)] = dict(out=out, labels=labels, rule=how["rule"], circuits=rep["circuits"],
                                seconds=rep["qpu_seconds_model"],
                                cz={t: r["cz"] for t, r in rep["items"].items()},
                                mapping={t: r["mapping"] for t, r in rep["items"].items()})
    l33, l81 = builds[(33, "")]["labels"], builds[(81, "")]["labels"]
    res["n33_is_first33_of_n81"] = l33 == l81[:33]
    m81 = builds[(81, "")]["mapping"]
    for arm in ("cut", "idle"):
        mm = builds[(81, arm)]["mapping"]
        res[f"placement_{arm}_equals_N81"] = all(mm[tag(81, th, s, arm)] == m81[tag(81, th, s)] for th in THETAS
                                                 for s in STEPS)
    if repeat_runs:
        same = differ = 0
        for th in THETAS:
            for s in STEPS:
                t = tag(81, th, s)
                for suf in ("", "_floor", "_mirror"):
                    f = os.path.join(repeat_runs, f"p2d_{t}{suf}.qpy")
                    if os.path.exists(f):
                        a = gatehash.qpy_hash(f)["gate_sha256"]
                        b = gatehash.qpy_hash(os.path.join(builds[(81, '')]["out"], "runs", f"p2d_{t}{suf}.qpy"))["gate_sha256"]
                        same, differ = same + (a == b), differ + (a != b)
        res["N81_equals_recorded_repeat_records"] = dict(same=same, differ=differ)
    print(f"2. N33 = first 33 of N81: {res['n33_is_first33_of_n81']}; placement cut / idle = N81: "
          f"{res['placement_cut_equals_N81']} / {res['placement_idle_equals_N81']}; "
          f"N81 vs recorded repeat: {res.get('N81_equals_recorded_repeat_records')}")
    res["arms"] = {}
    for (n, arm), b in builds.items():
        from psf_os import mirror2d as Mi
        lay = {}
        for th in THETAS:
            for s in STEPS:
                t = tag(n, th, s, arm)
                (c,) = qpy.load(open(os.path.join(b["out"], "runs", f"p2d_{t}.qpy"), "rb"))
                lay[t] = (b["cz"][t], c.depth(lambda i: i.operation.name == "cz"))
        res["arms"][f"N{n}{arm}"] = dict(circuits=b["circuits"], seconds=b["seconds"], rule=b["rule"], cz_and_layers=lay)
        print(f"   N{n}{arm:5}: {b['circuits']} circuits, {b['seconds']} s by the model; CZ / layers at pi/2: "
              + ", ".join(f"{lay[tag(n, math.pi / 2, s, arm)][0]}/{lay[tag(n, math.pi / 2, s, arm)][1]}" for s in STEPS))
    # 3. stim at pi/2
    rr = lambda z, e: float(np.dot(z, e) / np.dot(e, e))
    ext = set(l81[33:])
    res["stim"] = {}
    for model, ex in (("uniform", None), ("extension x3 (illustration)", ext)):
        rows = {}
        print(f"3. stim, {model}: g = r(N33) - r(arm) on the shared qubits, blocks far / mid / near")
        for s in STEPS:
            z33, e33, _ = z_stim(os.path.join(builds[(33, '')]["out"], "runs"), tag(33, math.pi / 2, s), ex)
            row = {}
            for arm in ("", "cut", "idle"):
                z, e, _ = z_stim(os.path.join(builds[(81, arm)]["out"], "runs"), tag(81, math.pi / 2, s, arm), ex)
                row[f"N81{arm}"] = {b: rr(z33[list(i)], e33[list(i)]) - rr(z[list(i)], e[list(i)]) for b, i in BLOCKS.items()}
            rows[4 * s] = row
            print(f"   {4 * s:2d} layers: " + " | ".join(
                f"{k}: " + " ".join(f"{v[b]:+.3f}" for b in BLOCKS) for k, v in row.items()))
        res["stim"][model] = rows
    json.dump(res, open(os.path.join(HERE, "cut_desk.json"), "w"), indent=1, default=str)


if __name__ == "__main__":
    main(*sys.argv[1:4])
