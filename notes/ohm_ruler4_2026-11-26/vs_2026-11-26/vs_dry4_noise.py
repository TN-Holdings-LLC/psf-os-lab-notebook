"""Dry runs of gpu/ohm_ruler_night3.py's / ohm_ruler_night4.py's job under ILLUSTRATIVE noise (workplace VS,
2026-11-25 sono2 and 2026-11-26; author The Architect). Desk or pod only, never a device; every noise value is written by hand and
never fitted to any device.

Every circuit is put on its touched qubits (in the order of the physical labels; barriers removed) and sampled with
one noise trajectory per shot: Aer's matrix-product state on the CPU (the noises written into the circuit as
instructions), or, with --gpu, the statevector on the GPU with the same CZ noises as a noise model (the amplitude
damping is slow on the MPS; on the GPU a noise model is about five times faster than instructions). Noises (any together):
  --p2 P       two-qubit depolarizing P after every CZ
  --damp G     amplitude damping G on both qubits after every CZ (one-sided decay towards |0>)
  --t2 T       dephasing while a qubit waits: the circuit is scheduled as late as possible (ALAP) with the
               illustrative lengths --len-1q (sx, x), --len-cz, rz 0; each wait of length d becomes a Z error with
               probability (1 - exp(-d / T)) / 2 (the dephasing that leaves exp(-d / T) of the coherence); times in ns
  --bad-pos P,... --bad-damp G / --bad-dep P   chain positions whose qubit, after every CZ it takes part in, gets an
               amplitude damping G or a one-qubit depolarizing P (positions chosen by hand)
--q10 Q (2026-11-26): every measured 1 is read as 0 with probability Q (a one-sided readout fault on every qubit),
applied after the symmetric flip. From the same shots, one raw_counts.json per readout flip q in --flips (each bit flipped with probability q). The ring
sentinel (40 qubits) is given all-zero counts. --skip drops cells by name part (all-zero counts); --shard I N and
--merge split one seed over processes (each circuit keeps its own seed, seed + 10007 k).

  python vs_dry3_noise.py BUILT WORK TAG --seed S [--p2 ..] [--damp ..] [--t2 ..] [--bad-pos ..] --flips 0 0.02
writes WORK/{TAG}_q{q}_s{S}/ (a copy of BUILT with job/raw_counts.json and job/submission.json)
"""
import argparse
import glob
import json
import math
import os
import shutil
import time

import numpy as np


def touched(qc):
    return sorted({qc.find_bit(q).index for ins in qc.data if ins.operation.name != "barrier" for q in ins.qubits})


def put_on_touched(qc):
    """(circuit on the touched qubits, physical label -> new index); barriers dropped, clbits kept."""
    from qiskit import QuantumCircuit
    act = touched(qc)
    idx = {q: i for i, q in enumerate(act)}
    out = QuantumCircuit(len(act), qc.num_clbits)
    for ins in qc.data:
        if ins.operation.name == "barrier":
            continue
        out.append(ins.operation, [idx[qc.find_bit(q).index] for q in ins.qubits],
                   [qc.find_bit(c).index for c in ins.clbits])
    return out, idx


def with_errors(cc, a, bad_idx):
    """The circuit with the noises inserted as instructions (so the MPS and the GPU statevector both take them)."""
    from qiskit import QuantumCircuit
    from qiskit_aer.noise import amplitude_damping_error, depolarizing_error, pauli_error
    if a.t2:
        from qiskit.transpiler import InstructionDurations, PassManager
        from qiskit.transpiler.passes import ALAPScheduleAnalysis, PadDelay
        durs = InstructionDurations([("sx", None, a.len_1q), ("x", None, a.len_1q), ("rz", None, 0),
                                     ("cz", None, a.len_cz), ("measure", None, 0), ("delay", None, 0)], dt=1e-9)
        cc = PassManager([ALAPScheduleAnalysis(durs), PadDelay(durations=durs)]).run(cc)
    e2 = depolarizing_error(a.p2, 2) if a.p2 else None
    ed = amplitude_damping_error(a.damp) if a.damp else None
    eb = (amplitude_damping_error(a.bad_damp) if a.bad_damp else depolarizing_error(a.bad_dep, 1)) \
        if (a.bad_damp or a.bad_dep) else None
    out = QuantumCircuit(cc.num_qubits, cc.num_clbits)
    for ins in cc.data:
        name = ins.operation.name
        qs = [cc.find_bit(q).index for q in ins.qubits]
        cs = [cc.find_bit(c).index for c in ins.clbits]
        if name == "delay":
            d = ins.operation.duration          # in dt = 1 ns
            if a.t2 and d:
                p = (1 - math.exp(-d / a.t2)) / 2
                out.append(pauli_error([("Z", p), ("I", 1 - p)]), qs)
            continue
        out.append(ins.operation, qs, cs)
        if name == "cz":
            if e2 is not None:
                out.append(e2, qs)
            if ed is not None:
                out.append(ed, [qs[0]])
                out.append(ed, [qs[1]])
            if eb is not None:
                for q in qs:
                    if q in bad_idx:
                        out.append(eb, [q])
    return out


def noise_model_for(cc, a, bad_idx):
    """The same CZ noises (p2, damp, bad positions) as a noise model on this circuit's CZ pairs: the GPU statevector
    samples a noise model about five times faster than errors written into the circuit (pod, 2026-11-25). The wait
    dephasing (--t2) is not available here."""
    from qiskit_aer.noise import NoiseModel, QuantumError, amplitude_damping_error, depolarizing_error
    from qiskit.quantum_info import Kraus
    if a.t2:
        raise SystemExit("--t2 runs on the MPS (errors in the circuit), not with --gpu")
    ident = QuantumError(Kraus([[[1, 0], [0, 1]]]))
    ed = amplitude_damping_error(a.damp) if a.damp else None
    eb = (amplitude_damping_error(a.bad_damp) if a.bad_damp else depolarizing_error(a.bad_dep, 1)) \
        if (a.bad_damp or a.bad_dep) else None
    nm = NoiseModel()
    pairs = {tuple(cc.find_bit(q).index for q in ins.qubits) for ins in cc.data if ins.operation.name == "cz"}
    for q0, q1 in sorted(pairs):
        err = None
        if a.p2:
            err = depolarizing_error(a.p2, 2)
        if ed is not None:                      # QuantumError.tensor: the right factor acts on the first qubit
            e = ed.tensor(ed)
            err = e if err is None else err.compose(e)
        if eb is not None and (q0 in bad_idx or q1 in bad_idx):
            e = (eb if q1 in bad_idx else ident).tensor(eb if q0 in bad_idx else ident)
            err = e if err is None else err.compose(e)
        if err is not None:
            nm.add_quantum_error(err, "cz", [q0, q1])
    return nm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("built")
    ap.add_argument("work")
    ap.add_argument("tag")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--p2", type=float, default=0.0)
    ap.add_argument("--damp", type=float, default=0.0)
    ap.add_argument("--t2", type=float, default=0.0)
    ap.add_argument("--len-1q", type=int, default=36)
    ap.add_argument("--len-cz", type=int, default=68)
    ap.add_argument("--bad-pos", default="")
    ap.add_argument("--bad-damp", type=float, default=0.0)
    ap.add_argument("--bad-dep", type=float, default=0.0)
    ap.add_argument("--flips", type=float, nargs="+", default=[0.0])
    ap.add_argument("--q10", type=float, default=0.0)
    ap.add_argument("--skip", nargs="*", default=[])
    ap.add_argument("--gpu", action="store_true")
    ap.add_argument("--shard", type=int, nargs=2, metavar=("I", "N"))
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--mem-dir")
    a = ap.parse_args()
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    job = os.path.join(a.built, "job")
    man = json.load(open(os.path.join(job, "manifest.json")))
    b = json.load(open(os.path.join(a.built, "build.json")))
    circs = qpy.load(open(os.path.join(job, "circuits.qpy"), "rb"))
    phys_of = {}
    for w in b["items"].values():
        phys_of.update(dict(zip(w["positions"], w["physical"])))
    bad = {phys_of[int(p)] for p in a.bad_pos.split(",") if p}
    sim = AerSimulator(method="statevector", device="GPU") if a.gpu else AerSimulator(method="matrix_product_state")
    cname = {cl["cell"]: cl["name"] for cl in man["cells"]}
    merged = {}
    if a.merge:
        for f in glob.glob(os.path.join(a.mem_dir, "mem_*.npz")):
            z = np.load(f)
            merged.update({int(k[1:]): z[k] for k in z.files})
    t0, mems, skipped, nsim, shard_mems = time.time(), [], [], 0, {}
    for k, c in enumerate(circs):
        if any(s in cname[man["pubs"][k]["cell"]] for s in a.skip) or len(touched(c)) > 28:
            mems.append(None)
            skipped.append(k)
            continue
        nsim += 1
        if a.merge:
            mems.append(merged[k])
            continue
        if a.shard and (nsim - 1) % a.shard[1] != a.shard[0]:
            mems.append(None)
            continue
        cc, idx = put_on_touched(c)
        bad_idx = {idx[q] for q in bad if q in idx}
        if a.gpu:          # a noise model on the GPU (about five times faster than errors in the circuit)
            mem = sim.run(cc, shots=man["shots"], memory=True, seed_simulator=a.seed + 10007 * k,
                          noise_model=noise_model_for(cc, a, bad_idx)).result().get_memory(0)
        else:
            nc = with_errors(cc, a, bad_idx)
            mem = sim.run(nc, shots=man["shots"], memory=True,
                          seed_simulator=a.seed + 10007 * k).result().get_memory(0)
        mems.append(np.array([[int(ch) for ch in m.replace(" ", "")] for m in mem], dtype=np.int8))
        if a.shard:
            shard_mems[f"k{k}"] = mems[-1]
    if a.shard:
        os.makedirs(a.mem_dir, exist_ok=True)
        np.savez_compressed(os.path.join(a.mem_dir, f"mem_{a.shard[0]}.npz"), **shard_mems)
        print(f"shard {a.shard[0]} of {a.shard[1]}: {len(shard_mems)} circuits, {time.time() - t0:.0f} s")
        return
    desc = (f"aer {'statevector GPU' if a.gpu else 'matrix_product_state'}; p2 {a.p2}, damp {a.damp}, t2 {a.t2} ns "
            f"(1q {a.len_1q} ns, cz {a.len_cz} ns, ALAP), bad positions {a.bad_pos or 'none'} (damp {a.bad_damp}, "
            f"dep {a.bad_dep}), readout 1 -> 0 {a.q10} (ILLUSTRATIVE, never fitted)")
    for q in a.flips:
        rng = np.random.default_rng(a.seed * 7 + int(round(q * 1e6)))
        rows = []
        for k, (c, bits) in enumerate(zip(circs, mems)):
            if bits is None:
                rows.append(dict(pub=k, counts={"0" * c.num_clbits: man["shots"]}))
                continue
            bb = bits.copy()
            if q:
                bb ^= (rng.random(bb.shape) < q).astype(np.int8)
            if a.q10:
                bb &= (rng.random(bb.shape) >= a.q10).astype(np.int8)     # a 1 read as 0 with probability q10
            counts = {}
            for row in bb:
                key = "".join(map(str, row))
                counts[key] = counts.get(key, 0) + 1
            rows.append(dict(pub=k, counts=counts))
        out = os.path.join(a.work, f"{a.tag}_q{q}_s{a.seed}")
        if os.path.exists(out):
            raise SystemExit(f"{out} exists")
        shutil.copytree(a.built, out)
        jid = f"local-vsdry3-{a.tag}-q{q}-{a.seed}"
        json.dump(dict(job_id=jid, submitted="dry", local=True, backend=man["fetch"]["backend"],
                       simulator=desc + f", readout flip {q}", not_sampled=skipped, skip=a.skip,
                       bad_physical=sorted(bad)), open(os.path.join(out, "job", "submission.json"), "w"), indent=1)
        json.dump(dict(fetched="dry", job_id=jid, status="DONE (dry)", rows=rows),
                  open(os.path.join(out, "job", "raw_counts.json"), "w"))
    print(f"{len(circs)} circuits, {a.tag}, seed {a.seed}, flips {a.flips}: {time.time() - t0:.0f} s; {desc}")


if __name__ == "__main__":
    main()
