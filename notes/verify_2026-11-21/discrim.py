"""Discrimination of the three IPE forms under ILLUSTRATIVE noise (home VS, 2026-11-21; never fitted to a device;
qiskit / numpy only, no psf-os and no notebook dry tool). The noise is inserted by this script into the sent circuits:
  gates     depolarizing on every CZ
  damping   amplitude damping on every waiting qubit at every read (measure)
  dephasing phase damping on every waiting qubit at every conditional (if_else)
placed at the wait's position in the sent instruction order. Exact distributions by a branching density matrix over
the active qubits; shot noise by multinomial sampling (1950 shots per phase), 20 seeds per noise. Words and rows as
the draft prereg/drafts-2026-11-21/ipe_park_DRAFT.md: d >= 2 SE KEEPS MORE, d <= -2 SE KEEPS LESS, else SAME.
usage: python discrim.py OUT_JOB0 OUT_JOB1 [N_SEEDS]"""
import json
import sys

import numpy as np
from qiskit import qpy
from qiskit.circuit import Clbit
from qiskit.quantum_info import DensityMatrix, Kraus, Operator, SuperOp
from qiskit.quantum_info.operators.channel.transformations import _kraus_to_superop  # noqa: F401

SHOTS = 1950


def load(out):
    man = json.load(open(f"{out}/job/manifest.json"))
    circs = qpy.load(open(f"{out}/job/circuits.qpy", "rb"))
    cells = {c["cell"]: c["name"] for c in man["cells"]}
    return {cells[p["cell"]]: circs[i] for i, p in enumerate(man["pubs"]) if p["point"] == 0}


def amp_damp(g):
    return Kraus([np.array([[1, 0], [0, np.sqrt(1 - g)]]), np.array([[0, np.sqrt(g)], [0, 0]])])


def phase_damp(lam):
    return Kraus([np.array([[1, 0], [0, np.sqrt(1 - lam)]]), np.array([[0, 0], [0, np.sqrt(lam)]])])


def depol2(p):
    paulis = [np.eye(2), np.array([[0, 1], [1, 0]]), np.array([[0, -1j], [1j, 0]]), np.diag([1, -1])]
    ks = [np.sqrt(1 - p) * np.eye(4)]
    for a in range(4):
        for b in range(4):
            if a or b:
                ks.append(np.sqrt(p / 15) * np.kron(paulis[a], paulis[b]))
    return Kraus(ks)


def run(qc, noise):
    act = sorted({qc.find_bit(q).index for ins in qc.data if ins.operation.name not in ("barrier", "delay")
                  for q in ins.qubits})
    pos = {q: k for k, q in enumerate(act)}
    nc = qc.num_clbits
    state = {(0,) * nc: DensityMatrix.from_label("0" * len(act))}

    def chan(st, ch, ks):
        return {cl: rho.evolve(ch, ks) for cl, rho in st.items()}

    def waiting(qs):
        return [pos[q] for q in act if q not in qs]

    def apply(st, name, op, qs, cs, top):
        if name in ("barrier", "delay"):
            return st
        if top and name == "measure" and noise.get("damping"):
            for k in waiting(qs):
                st = chan(st, amp_damp(noise["damping"]), [k])
        if top and name == "if_else" and noise.get("dephasing"):
            for k in waiting(qs):
                st = chan(st, phase_damp(noise["dephasing"]), [k])
        if name == "measure":
            k = pos[qs[0]]
            out = {}
            for cl, rho in st.items():
                for v in (0, 1):
                    proj = np.zeros((2, 2))
                    proj[v, v] = 1
                    r = rho.evolve(Operator(proj), [k])
                    if np.real(np.trace(r.data)) < 1e-15:
                        continue
                    ncl = list(cl)
                    ncl[cs[0]] = v
                    ncl = tuple(ncl)
                    out[ncl] = out[ncl] + r if ncl in out else r
            return out
        if name == "if_else":
            tgt, val = op.condition
            assert isinstance(tgt, Clbit)
            ci = qc.find_bit(tgt).index
            out = {}
            for cl, rho in st.items():
                sub = {cl: rho}
                body = op.blocks[0] if cl[ci] == int(val) else (op.blocks[1] if len(op.blocks) > 1 else None)
                if body is not None:
                    for ins in body.data:
                        bq = [qs[body.find_bit(q).index] for q in ins.qubits]
                        bc = [cs[body.find_bit(c).index] for c in ins.clbits]
                        sub = apply(sub, ins.operation.name, ins.operation, bq, bc, False)
                for k2, r in sub.items():
                    out[k2] = out[k2] + r if k2 in out else r
            return out
        st = chan(st, Operator(op), [pos[q] for q in qs])
        if name == "cz" and noise.get("cz"):
            st = chan(st, depol2(noise["cz"]), [pos[q] for q in qs])
        return st

    for ins in qc.data:
        qs = [qc.find_bit(q).index for q in ins.qubits]
        cs = [qc.find_bit(c).index for c in ins.clbits]
        state = apply(state, ins.operation.name, ins.operation, qs, cs, True)
    return {"".join(str(b) for b in reversed(cl)): float(np.real(np.trace(r.data))) for cl, r in state.items()}


def word(d, se):
    return "KEEPS MORE" if d >= 2 * se else ("KEEPS LESS" if d <= -2 * se else "SAME WITHIN ERROR")


def row(park, fence):
    if park == "KEEPS MORE" and fence == "KEEPS LESS":
        return "decay"
    if park == "KEEPS MORE" and fence == "KEEPS MORE":
        return "dephasing"
    if park == "KEEPS MORE" and fence == "SAME WITHIN ERROR":
        return "|0> keeps more, |1> neither"
    if park == "SAME WITHIN ERROR" and fence == "SAME WITHIN ERROR":
        return "not seen"
    return "against the expectation"


NOISES = {
    "gates only (CZ 1 %)": dict(cz=0.01),
    "damping 6 % per read": dict(damping=0.06),
    "dephasing 5 % per conditional": dict(dephasing=0.05),
    "CZ 1 % + damping 2 % per read": dict(cz=0.01, damping=0.02),
    "CZ 1 % + dephasing 12 % per conditional": dict(cz=0.01, dephasing=0.12),
    "CZ 1 % + damping 2 % + dephasing 12 %": dict(cz=0.01, damping=0.02, dephasing=0.12),
}


def main():
    outs = sys.argv[1:3]
    nseeds = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    circs = {}
    for o in outs:
        for nm, qc in load(o).items():
            if nm.startswith("ff_") and not nm.endswith(("_off", "_floor")):
                circs[nm] = (qc, json.load(open(f"{o}/runs/{nm}.json"))["success"])
    phases = sorted({nm.split("_")[2] for nm in circs}, key=int)
    n = int(circs[next(iter(circs))][0].num_clbits)
    res = {}
    for label, noise in NOISES.items():
        exact = {}
        for f in ("pl", "fe", "pk"):
            exact[f] = []
            for j in phases:
                qc, succ = circs[f"ff_{f}{n}_{j}"]
                dist = run(qc, noise)
                keys = list(dist)
                good = [all(int(k[::-1][int(c)]) == v for c, v in succ.items()) for k in keys]
                exact[f].append((keys, np.array([dist[k] for k in keys]), np.array(good)))
        ex_share = {f: float(np.mean([p[g].sum() for _, p, g in exact[f]])) for f in exact}
        rows = {}
        for s in range(nseeds):
            rng = np.random.default_rng(20261121 + 1000 * s)
            share = {}
            for f in ("pl", "fe", "pk"):
                hits = 0
                for keys, p, g in exact[f]:
                    c = rng.multinomial(SHOTS, p / p.sum())
                    hits += int(c[g].sum())
                share[f] = hits / (SHOTS * len(phases))
            N = SHOTS * len(phases)

            def d_se(x, y):
                return share[x] - share[y], np.sqrt(share[x] * (1 - share[x]) / N + share[y] * (1 - share[y]) / N)
            pw = word(*d_se("pk", "pl"))
            fw = word(*d_se("fe", "pl"))
            r = row(pw, fw)
            rows[r] = rows.get(r, 0) + 1
        res[label] = dict(exact=ex_share, rows=rows)
        print(f"{label}: exact shares pl {ex_share['pl']:.4f} fe {ex_share['fe']:.4f} pk {ex_share['pk']:.4f}; "
              f"rows over {nseeds} seeds {rows}", flush=True)
    json.dump(res, open(f"discrim_n{n}.json", "w"), indent=1)


if __name__ == "__main__":
    main()
