"""The exact shares of every circuit a stack of the loop can use, under the ILLUSTRATIVE noise of
notes/os2_2026-11-18/branch_noise.py, on a grid of damping strengths (home VS Claude, 2026-11-21; desk only; never
fitted to a device). Used by sim_compare.py to simulate many nights without simulating every circuit again.

The noise as branch_noise defines it: amplitude damping gamma on every qubit not read, after each group of top-level
measurements; readout P(1|1) = p11, P(0|0) = p00 per physical qubit (the recorded bit is flipped, the state collapses
to the true outcome; conditionals read the recorded bit, as Aer's readout error). Exact: a branching density matrix
over the circuit's qubits (no sampling).

  python catalog.py DEVDIR OUT.json NOISE.json [--grid -0.4,-0.3,...]"""
import argparse
import json
import os
import shutil
import sys
import tempfile

import numpy as np
from qiskit import qpy
from qiskit.circuit import Clbit
from qiskit.quantum_info import DensityMatrix, Kraus, Operator

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(NB, "gpu"))
for d in ("notes/rus_coherent_2026-11-17", "notes/compound_2026-11-17", "notes/os2_2026-11-18"):
    sys.path.insert(0, os.path.join(NB, d))

LS = (1, 2, 3)


def variants():
    """(tag, presc, L, m, role, offset) of every circuit a stack can use."""
    out = []
    for L in LS:
        out.append((f"p0_{L}", "P0", L, 3, "p0", 0))
        for m in (2, 3):
            out.append((f"P1m{m}L{L}", "P1", L, m, "x", 0))
            for o in (0, 2, 4):
                out.append((f"P2m{m}L{L}o{o}", "P2", L, m, "xr" if o else "x", o))
                out.append((f"NFm{m}L{L}o{o}", "NF", L, m, "xn", o))
    return out


def amp(g):
    return Kraus([np.array([[1, 0], [0, np.sqrt(1 - g)]]), np.array([[0, np.sqrt(g)], [0, 0]])])


def exact_dist(cc, phys, gamma, noise):
    """Exact distribution of the recorded register of compact circuit cc under the noise."""
    p11, p00 = noise.get("p11", {}), noise.get("p00", {})
    nq, nc = cc.num_qubits, cc.num_clbits
    conf = [((float(p00.get(str(phys[i]), 1.0)), float(p11.get(str(phys[i]), 1.0)))) for i in range(nq)]
    state = {(0,) * nc: DensityMatrix.from_label("0" * nq)}
    damp = amp(gamma) if gamma else None

    def add(d, k, r):
        d[k] = d[k] + r if k in d else r

    def apply(st, ins, qmap, cmap, top, group):
        op = ins.operation
        name = op.name
        qs = [qmap[cc_bit(ins, q)] for q in ins.qubits]
        if name in ("barrier", "delay"):
            return st
        if name == "measure":
            k = qs[0]
            c = cmap[ins.clbits[0]]
            a0, a1 = conf[k]
            out = {}
            for cl, rho in st.items():
                for v in (0, 1):
                    proj = np.zeros((2, 2))
                    proj[v, v] = 1
                    r = rho.evolve(Operator(proj), [k])
                    w = float(np.real(np.trace(r.data)))
                    if w < 1e-15:
                        continue
                    pr = (a0, 1 - a0) if v == 0 else (1 - a1, a1)          # P(recorded 0), P(recorded 1)
                    for rec in (0, 1):
                        if pr[rec] < 1e-15:
                            continue
                        ncl = list(cl)
                        ncl[c] = rec
                        add(out, tuple(ncl), r * pr[rec])
            if top:
                group.append(k)
            return out
        if name == "if_else":
            tgt, val = op.condition
            assert isinstance(tgt, Clbit)
            ci = cmap[tgt]
            out = {}
            for cl, rho in st.items():
                sub = {cl: rho}
                body = op.blocks[0] if cl[ci] == int(val) else (op.blocks[1] if len(op.blocks) > 1 else None)
                if body is not None:
                    bq = {b: qs[i] for i, b in enumerate(body.qubits)}
                    bc = {b: cmap[ins.clbits[i]] for i, b in enumerate(body.clbits)}
                    for bi in body.data:
                        sub = apply(sub, bi, bq, bc, False, group)
                for k2, r in sub.items():
                    add(out, k2, r)
            return out
        mat = Operator(op)
        return {cl: rho.evolve(mat, qs) for cl, rho in st.items()}

    def cc_bit(ins, q):
        return q

    qmap = {q: i for i, q in enumerate(cc.qubits)}
    cmap = {c: i for i, c in enumerate(cc.clbits)}
    group = []

    def flush(st):
        if group and damp is not None:
            for q in range(nq):
                if q not in group:
                    st = {cl: rho.evolve(damp, [q]) for cl, rho in st.items()}
        group.clear()
        return st
    for ins in cc.data:
        if ins.operation.name != "measure":
            state = flush(state)
        state = apply(state, ins, qmap, cmap, True, group)
    state = flush(state)
    return {cl: float(np.real(np.trace(r.data))) for cl, r in state.items()}


def build_catalog(devdir):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    import os2_night as O2
    import os3_night as O3
    dev = Device.load(devdir)
    vs = variants()
    its = [(t, *O3.item(presc, L, m)) for t, presc, L, m, role, o in vs]
    chains = O2.chains_for(dev, {t: (L, role, o) for t, presc, L, m, role, o in vs})
    tmp = tempfile.mkdtemp(prefix="catalog_")
    out = os.path.join(tmp, "c")
    rep = FF.build(dev, its, out, shots=4000, max_seconds=10_000, chains=chains, record_checks="off")
    man = json.load(open(os.path.join(out, "job", "manifest.json")))
    circs = qpy.load(open(os.path.join(out, "job", "circuits.qpy"), "rb"))
    cells = {c["cell"]: c["name"] for c in man["cells"]}
    got = {}
    for i, p in enumerate(man["pubs"]):
        name = cells[p["cell"]]
        if name.startswith("ff_") and not name.endswith(("_off", "_floor")):
            c = circs[i]
            phys = sorted({q for _, qs in FF.walk(c) for q in qs})
            got[name[3:]] = (FF.compact(c), phys, rep["items"][name[3:]]["chain"])
    probe = FF.place(dev, O2.PROBE_N)["chain"]
    shutil.rmtree(tmp, ignore_errors=True)
    return vs, got, probe


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("devdir")
    ap.add_argument("out")
    ap.add_argument("noise")
    ap.add_argument("--grid", default="-0.4,-0.3,-0.2,-0.1,0,0.1,0.2,0.3,0.4")
    a = ap.parse_args()
    import os3_night as O3
    noise = json.load(open(a.noise))
    grid = [float(x) for x in a.grid.split(",")]
    vs, got, probe = build_catalog(a.devdir)
    res = dict(noise=noise, illustrative=True, grid=grid, probe_chain=probe, items={})
    for t, presc, L, m, role, o in vs:
        cc, phys, chain = got[t]
        bit = L * m
        ps = []
        for e in grid:
            g = noise.get("gamma", 0.0) * (1 + e)
            dist = exact_dist(cc, phys, g, noise)
            p1 = sum(w for cl, w in dist.items() if cl[bit] == 1)
            ps.append(1 - p1 if presc == "P2" else p1)
        res["items"][t] = dict(presc=presc, L=L, m=m, offset=o, chain=chain, output_qubit=chain[2 * L - 1],
                               noiseless=O3.noiseless(presc, L, m), p=ps)
        print(f"{t}: output q{chain[2 * L - 1]} noiseless {O3.noiseless(presc, L, m):.4f} p(eps=0) "
              f"{ps[grid.index(0.0)]:.4f}", flush=True)
    json.dump(res, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
