"""The repeat-until-success neuron with decay during the mid-circuit waits, under an ILLUSTRATIVE uniform noise model:
the three designs of 2026-11-16 and the form without mid-circuit measurements (workplace VS Claude, 2026-11-17; desk
only; nothing is fitted to any device, no calibration or error number is read).

Designs (theta 1.1, as run on 2026-11-16; L = 1, 2, 3 and m = 2, 3 here):
  D1   rus_chain(L, theta, m) (gpu/rus_night.py): attempt; after a recorded 1, undo RY(pi/2) on the output, X on the
       ancilla, attempt again, up to m attempts;
  D2   gpu/rus2_night.flip_chain: D1 with the outputs in use (the neuron's own and its control) flipped by X before
       every ancilla measurement and flipped back right after it, so that the likely value 1 waits as |0>;
  D3   gpu/rus3_night.chain: D2 with the last output read flipped (no X back before its measurement; the reading is
       relabelled 1 - bit);
  coh  notes/rus_coherent_2026-11-17/coherent.zipper(L, theta, m, plus=True) (the workplace design "zipper+"): no
       mid-circuit measurement; try r on a fresh ancilla, run coherently when the previous ancilla is |1>; every qubit
       measured once at the end.
Arms: ff = the circuit; off = D1-D3 with the conditional blocks removed (the ancilla is still measured m times, with
the same waits and X pairs, as psf_os.feedforward.build's off arm); coh's off = the same line with try 0 only
(coherent.zipper(..., tries=1); defined for L = 1 only).

Noise model (uniform, illustrative; the same numbers on every element, NOT any device's):
  - one-qubit gates (fused): depolarising 3e-4; CZ: depolarising 3e-3 (0.3 %);
  - readout: the recorded bit flipped with 0.015 (mid-circuit and final); table E adds an asymmetric readout of |1>;
  - during every mid-circuit measurement (the wait), every other qubit: amplitude damping gamma (|1> -> |0>) and a
    phase flip pz = (1 - exp(-0.05)) / 2; gamma = 0, 0.02, 0.05, 0.1, 0.2 per wait (examples);
  - coh has no mid-circuit wait; during each of its CZ the other live qubits get gamma / 40 and pz / 40 (a CZ layer
    taken as 1/40 of a mid-circuit wait: 68 ns against 2.6 us, the illustrative durations of the workplace design note;
    the wait of a dynamic circuit is longer than the measurement alone, so 1/40 is on coh's unfavourable side).
For comparison only (not fitted): in the control test of 2026-11-16 the |1> of q1 fell from 0.984 to 0.460 and that
of q3 from 0.961 to 0.720 over five measurement waits, about 0.14 and 0.06 per wait if the decay were uniform.

Exact method: density matrix with qubits allocated when first used and traced out after their last use (the measured
ancillas of coh, once they have served as controls), so coh fits at L = 3, m = 3 (12 qubits, at most 5 live). Checks:
(1) noiseless, every design gives the same P(last output 1), and coh equals D1; (2) with gate noise only, D1's ff
and off equal rus_noise_desk.exact_arm (a separate engine) to 1e-12; (3) with gamma > 0, a Monte Carlo over Kraus
trajectories on the state vector agrees within 4 SE.
usage: python notes/feedforward_2026-11-16/rus_decay_desk.py   (numpy and qiskit; writes rus_decay_desk.txt / .json)
"""
import importlib.util
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


R = _load("rus_noise_desk", os.path.join(HERE, "rus_noise_desk.py"))
COH = _load("coherent", os.path.join(ROOT, "notes", "rus_coherent_2026-11-17", "coherent.py"))

THETA = 1.1
P1, P2, E_RO = 3e-4, 3e-3, 0.015
PZ = (1 - math.exp(-0.05)) / 2
GAMMAS = (0.0, 0.02, 0.05, 0.1, 0.2)
LS = (1, 2, 3)
MS = (2, 3)
IDLE = 1 / 40
SHOTS = 4000
X = R.X
I2 = R.I2


def kraus_ad(g):
    return [np.array([[1, 0], [0, math.sqrt(1 - g)]], dtype=complex),
            np.array([[0, math.sqrt(g)], [0, 0]], dtype=complex)]


# ------------------------------------------------------------------------------------------------ lazy density matrix

class LazyRho:
    """Density matrix over the live qubits only (axis order = self.live); a qubit is |0> until first touched."""

    def __init__(self):
        self.live = []
        self.m = np.ones((1, 1), dtype=complex)

    def copy(self):
        r = LazyRho()
        r.live, r.m = list(self.live), self.m.copy()
        return r

    def _ax(self, q):
        if q not in self.live:
            self.m = np.kron(self.m, np.array([[1, 0], [0, 0]], dtype=complex))
            self.live.append(q)
        return self.live.index(q)

    def _t(self):
        k = len(self.live)
        return self.m.reshape((2,) * (2 * k))

    def _set(self, t):
        d = 2 ** len(self.live)
        self.m = t.reshape(d, d)

    def tr(self):
        return float(np.real(np.trace(self.m)))

    def kraus1(self, q, K):
        """K rho K^dag on qubit q (K need not be unitary)."""
        i = self._ax(q)
        k = len(self.live)
        t = self._t()
        t = np.moveaxis(np.tensordot(K, t, axes=([1], [i])), 0, i)
        t = np.moveaxis(np.tensordot(K.conj(), t, axes=([1], [k + i])), 0, k + i)
        self._set(t)

    def channel1(self, q, Ks):
        self._ax(q)
        acc = None
        for K in Ks:
            r = self.copy()
            r.kraus1(q, K)
            acc = r.m if acc is None else acc + r.m
        self.m = acc

    def cz(self, a, b):
        ia, ib = self._ax(a), self._ax(b)
        k = len(self.live)
        t = self._t().copy()
        sl = [slice(None)] * (2 * k)
        sl[ia], sl[ib] = 1, 1
        t[tuple(sl)] *= -1
        sl = [slice(None)] * (2 * k)
        sl[k + ia], sl[k + ib] = 1, 1
        t[tuple(sl)] *= -1
        self._set(t)

    def depol(self, qs, p):
        if p == 0:
            return
        D = 4 ** len(qs)
        full = self.copy()
        for q in qs:
            i = full._ax(q)
            k = len(full.live)
            t = full._t()
            s0 = [slice(None)] * (2 * k)
            s1 = [slice(None)] * (2 * k)
            s0[i], s0[k + i] = 0, 0
            s1[i], s1[k + i] = 1, 1
            red = (t[tuple(s0)] + t[tuple(s1)]) / 2
            out = np.zeros_like(t)
            out[tuple(s0)] = red
            out[tuple(s1)] = red
            full._set(out)
        self.m = (1 - p - p / (D - 1)) * self.m + p * D / (D - 1) * full.m

    def phase_flip(self, q, pz):
        if pz == 0 or q not in self.live:
            return
        i = self.live.index(q)
        k = len(self.live)
        t = self._t().copy()
        for r, c in ((0, 1), (1, 0)):
            sl = [slice(None)] * (2 * k)
            sl[i], sl[k + i] = r, c
            t[tuple(sl)] *= (1 - 2 * pz)
        self._set(t)

    def damp(self, q, g):
        if g == 0 or q not in self.live:
            return
        self.channel1(q, kraus_ad(g))

    def project(self, q, v):
        i = self._ax(q)
        k = len(self.live)
        t = self._t()
        out = np.zeros_like(t)
        sl = [slice(None)] * (2 * k)
        sl[i], sl[k + i] = v, v
        out[tuple(sl)] = t[tuple(sl)]
        r = LazyRho()
        r.live = list(self.live)
        r._set(out)
        return r

    def trace_out(self, q):
        if q not in self.live:
            return
        i = self.live.index(q)
        k = len(self.live)
        t = np.trace(self._t(), axis1=i, axis2=k + i)
        self.live.pop(i)
        self._set(t)

    def p_one(self, q):
        return self.project(q, 1).tr()


def readout(p_true, e0, e1):
    """P(recorded 1) for P(true 1) = p_true, with P(1|0) = e0 and P(0|1) = e1."""
    return (1 - p_true) * e0 + p_true * (1 - e1)


# ------------------------------------------------------------------------------------------------ D1-D3 (dynamic)

def run_ops(r, ops, nz):
    for op in ops:
        if op[0] == "u":
            r.kraus1(op[1], op[2])
            r.depol([op[1]], nz["p1"])
        else:
            r.cz(op[1], op[2])
            r.depol([op[1], op[2]], nz["p2"])


def x_on(r, qs, nz):
    for q in qs:
        r.kraus1(q, X)
        r.depol([q], nz["p1"])


def measure_split(r, q, nz):
    """Mid-circuit measurement of q: the others wait (damping, phase flip), outcome, recorded flip (symmetric e)."""
    for k in list(r.live):
        if k != q:
            r.damp(k, nz["gamma"])
            r.phase_flip(k, nz["pz"])
    out = {}
    for v in (0, 1):
        pv = r.project(q, v)
        for rec in (0, 1):
            w = (1 - nz["e"]) if rec == v else nz["e"]
            if rec in out:
                out[rec].m = out[rec].m + w * pv.m
            else:
                out[rec] = pv.copy()
                out[rec].m = w * pv.m
    return out


def dynamic_any(L, m, design, arm, nz, theta=THETA):
    """D1, D2 or D3 as compiled on 2026-11-16 (checked against the job's circuits.qpy): per neuron the first attempt,
    then m ancilla measurements on every branch; before measurement r > 0 the retry block runs when the bit recorded at
    measurement r - 1 is 1 (ff only; the off arm has no blocks). D2 / D3: X on the outputs in use before every ancilla
    measurement and X after it; D3 leaves out the last X back on the last output and relabels its reading (1 - bit).
    Returns (P(recorded last output 1) after the relabelling, share whose last recorded ancilla bit is 1 in some
    neuron: the circuit's own "still failed")."""
    flip = design in ("D2", "D3")
    states = {True: LazyRho()}
    for q in range(2 * L):
        states[True]._ax(q)                    # one axis order for every branch, so that branches can be added
    for j in range(L):
        a, o = j, L + j
        ctrl = None if j == 0 else L + j - 1
        live = [o] if ctrl is None else [ctrl, o]
        first, again = R.neuron_ops(L, j, theta, True), R.neuron_ops(L, j, theta, False)
        nxt = {}
        for ok, st in states.items():
            run_ops(st, first, nz)
            br = {0: st}                       # key: the bit recorded at the previous measurement (none yet: 0)
            for r in range(m):
                if r > 0 and arm == "ff" and 1 in br:
                    run_ops(br[1], again, nz)
                final = (j == L - 1) and (r == m - 1)
                back = [q for q in live if not (design == "D3" and final and q == o)]
                new = {}
                for st2 in br.values():
                    if flip:
                        x_on(st2, live, nz)
                    sp = measure_split(st2, a, nz)
                    for rec, x in sp.items():
                        if flip:
                            x_on(x, back, nz)
                        if rec in new:
                            new[rec].m = new[rec].m + x.m
                        else:
                            new[rec] = x
                br = new
            for rec, x in br.items():
                key = ok and rec == 0
                if key in nxt:
                    nxt[key].m = nxt[key].m + x.m
                else:
                    nxt[key] = x
        states = nxt
    out_q = 2 * L - 1
    tot = sum(b.tr() for b in states.values())
    still_failed = 1 - (states[True].tr() / tot if True in states else 0.0)
    p_true = sum(b.p_one(out_q) for b in states.values()) / tot
    p_rec = readout(p_true, nz["e"], nz.get("e1", nz["e"]))
    return (1 - p_rec if design == "D3" else p_rec), still_failed


# ------------------------------------------------------------------------------------------------ coh (no mid-circuit)

def coh_ops(L, m, tries=None, theta=THETA):
    """coherent.zipper(plus=True) lowered to fused one-qubit gates and CZ (Qiskit transpile, basis cz + u, level 1,
    no coupling map: the zipper line is already nearest-neighbour), and the measured (position, bit) list."""
    from qiskit import transpile
    from qiskit.quantum_info import Operator
    qc, measured = COH.zipper(L, theta, m, plus=True, tries=tries)
    tq = transpile(qc, basis_gates=["cz", "u"], optimization_level=1, seed_transpiler=1)
    ops = []
    for ins in tq.data:
        qs = [tq.find_bit(x).index for x in ins.qubits]
        if ins.operation.name == "cz":
            ops.append(("cz", qs[0], qs[1]))
        elif ins.operation.name == "u":
            ops.append(("u", qs[0], Operator(ins.operation).data))
        elif ins.operation.name not in ("barrier",):
            raise ValueError(ins.operation.name)
    return R.fuse(ops), measured, qc.num_qubits


def coherent_p1(L, m, nz, tries=None, theta=THETA):
    ops, measured, n = coh_ops(L, m, tries, theta)
    out_pos = measured[-1][0]
    last = {}
    for k, op in enumerate(ops):
        for q in op[1:3] if op[0] == "cz" else (op[1],):
            last[q] = k
    r = LazyRho()
    for k, op in enumerate(ops):
        if op[0] == "u":
            r.kraus1(op[1], op[2])
            r.depol([op[1]], nz["p1"])
        else:
            r.cz(op[1], op[2])
            r.depol([op[1], op[2]], nz["p2"])
            for q in list(r.live):
                if q not in (op[1], op[2]):
                    r.damp(q, nz["gamma"] * IDLE)
                    r.phase_flip(q, nz["pz"] * IDLE)
        for q in (op[1:3] if op[0] == "cz" else (op[1],)):
            if last[q] == k and q != out_pos:
                r.trace_out(q)               # measured at the end, never used again: its bit does not enter P
    p_true = r.p_one(out_pos) / r.tr()
    cz = sum(1 for op in ops if op[0] == "cz")
    return readout(p_true, nz["e"], nz.get("e1", nz["e"])), cz


# ------------------------------------------------------------------------------------------------ Monte Carlo check

def mc_dynamic(L, m, design, nz, shots, seed, theta=THETA):
    """Kraus-trajectory Monte Carlo of the ff arm on the state vector (D1 or D2)."""
    rng = np.random.default_rng(seed)
    n = 2 * L
    flip = design == "D2"
    paulis = R.PAULIS

    def ap(psi, q, K):
        return np.moveaxis(np.tensordot(K, psi, axes=([1], [q])), 0, q)

    def kr(psi, q, Ks):
        outs = [ap(psi, q, K) for K in Ks]
        ps = [float(np.sum(np.abs(o) ** 2)) for o in outs]
        k = rng.choice(len(Ks), p=np.array(ps) / sum(ps))
        return outs[k] / math.sqrt(ps[k])

    def run(psi, ops):
        for op in ops:
            if op[0] == "u":
                psi = ap(psi, op[1], op[2])
                if rng.random() < nz["p1"]:
                    psi = ap(psi, op[1], paulis[rng.integers(1, 4)])
            else:
                sl = [slice(None)] * n
                sl[op[1]], sl[op[2]] = 1, 1
                psi = psi.copy()
                psi[tuple(sl)] *= -1
                if rng.random() < nz["p2"]:
                    k = rng.integers(1, 16)
                    psi = ap(ap(psi, op[1], paulis[k // 4]), op[2], paulis[k % 4])
        return psi

    def xs(psi, qs):
        for q in qs:
            psi = ap(psi, q, X)
            if rng.random() < nz["p1"]:
                psi = ap(psi, q, paulis[rng.integers(1, 4)])
        return psi

    def meas(psi, q):
        sl = [slice(None)] * n
        sl[q] = 1
        p = float(np.sum(np.abs(psi[tuple(sl)]) ** 2))
        v = int(rng.random() < p)
        sl0 = [slice(None)] * n
        sl0[q] = 1 - v
        psi = psi.copy()
        psi[tuple(sl0)] = 0
        psi = psi / math.sqrt(p if v else 1 - p)
        return psi, v ^ int(rng.random() < nz["e"])

    ad = kraus_ad(nz["gamma"])
    ones = 0
    for _ in range(shots):
        psi = np.zeros((2,) * n, dtype=complex)
        psi[(0,) * n] = 1
        for j in range(L):
            a, o = j, L + j
            ctrl = None if j == 0 else L + j - 1
            live = [o] if ctrl is None else [ctrl, o]
            psi = run(psi, R.neuron_ops(L, j, theta, True))
            rec = 0
            for r in range(m):
                if r > 0 and rec == 1:
                    psi = run(psi, R.neuron_ops(L, j, theta, False))
                if flip:
                    psi = xs(psi, live)
                for k in range(n):
                    if k != a:
                        psi = kr(psi, k, ad)
                        if rng.random() < nz["pz"]:
                            psi = ap(psi, k, R.Z)
                psi, rec = meas(psi, a)
                if flip:
                    psi = xs(psi, live)
        psi, fin = meas(psi, 2 * L - 1)
        ones += fin
    return ones / shots


def mc_coherent(L, m, nz, shots, seed, theta=THETA):
    rng = np.random.default_rng(seed)
    ops, measured, n = coh_ops(L, m, None, theta)
    out_pos = measured[-1][0]
    paulis = R.PAULIS
    ad_i = kraus_ad(nz["gamma"] * IDLE)

    def ap(psi, q, K):
        return np.moveaxis(np.tensordot(K, psi, axes=([1], [q])), 0, q)

    ones = 0
    for _ in range(shots):
        psi = np.zeros((2,) * n, dtype=complex)
        psi[(0,) * n] = 1
        for op in ops:
            if op[0] == "u":
                psi = ap(psi, op[1], op[2])
                if rng.random() < nz["p1"]:
                    psi = ap(psi, op[1], paulis[rng.integers(1, 4)])
                continue
            sl = [slice(None)] * n
            sl[op[1]], sl[op[2]] = 1, 1
            psi = psi.copy()
            psi[tuple(sl)] *= -1
            if rng.random() < nz["p2"]:
                k = rng.integers(1, 16)
                psi = ap(ap(psi, op[1], paulis[k // 4]), op[2], paulis[k % 4])
            for q in range(n):
                if q in (op[1], op[2]):
                    continue
                outs = [ap(psi, q, K) for K in ad_i]
                ps = [float(np.sum(np.abs(x) ** 2)) for x in outs]
                k = int(rng.random() < ps[1] / (ps[0] + ps[1]))
                psi = outs[k] / math.sqrt(ps[k])
                if rng.random() < nz["pz"] * IDLE:
                    psi = ap(psi, q, R.Z)
        sl = [slice(None)] * n
        sl[out_pos] = 1
        p = float(np.sum(np.abs(psi[tuple(sl)]) ** 2))
        v = int(rng.random() < p)
        ones += v ^ int(rng.random() < nz["e"])
    return ones / shots


# ------------------------------------------------------------------------------------------------ tables

def noise(gamma, e1=None, off=False):
    if off:
        return dict(p1=0, p2=0, e=0, pz=0, gamma=0)
    nz = dict(p1=P1, p2=P2, e=E_RO, pz=PZ, gamma=gamma)
    if e1 is not None:
        nz["e1"] = e1
    return nz


def as_text(v):
    if isinstance(v, dict):
        return {str(k): as_text(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [as_text(x) for x in v]
    if isinstance(v, (float, np.floating)):
        return "%.3e" % v
    return v


def main():
    quick = "--quick" in sys.argv
    exact = {L: R.exact_p1(L, THETA) for L in LS}
    L_ = ["Repeat-until-success neuron with decay during the mid-circuit waits, ILLUSTRATIVE uniform noise model (not "
          "fitted to any device; no calibration or error number read)",
          f"theta {THETA}; one-qubit {P1:.0e}, CZ {P2:.0e}, readout flip {E_RO}; per mid-circuit wait on every other "
          f"qubit: amplitude damping gamma and phase flip {PZ:.3f}; coh: gamma / 40 and phase flip / 40 per CZ on the "
          "other live qubits. Exact density matrix; SE for 4000 shots.", ""]
    out = dict(model=dict(p1=P1, p2=P2, readout=E_RO, pz=PZ, gammas=GAMMAS, idle_per_cz=IDLE, theta=THETA,
                          illustrative=True, fitted_to_device=False), cells=[])

    # check 1: noiseless, all designs agree; coh equals D1
    worst, rows = 0.0, []
    for L in LS:
        for m in MS:
            vals = {d: dynamic_any(L, m, d, "ff", noise(0, off=True))[0] for d in ("D1", "D2", "D3")}
            vals["coh"] = coherent_p1(L, m, noise(0, off=True))[0]
            spread = max(vals.values()) - min(vals.values())
            worst = max(worst, spread)
            rows.append(f"L {L} m {m}: " + ", ".join(f"{k} {v:.6e}" for k, v in vals.items()))
    L_.append(f"Check 1, noiseless P(last output 1), D1 / D2 / D3 / coh: {'PASS' if worst < 1e-9 else 'FAIL'} "
              f"(largest spread {worst:.1e})")
    L_ += ["  " + r for r in rows]
    # check 2: gates noisy, readout and waits off: D1 against rus_noise_desk.exact_arm (separate engine; there the
    # ancilla is measured inside the block, here m times on every branch, which is the same when nothing flips a bit)
    worst = 0.0
    nz2 = dict(p1=P1, p2=P2, e=0.0, pz=0.0, gamma=0.0)
    for L in LS:
        for m in MS:
            for arm in ("ff", "off"):
                mine = dynamic_any(L, m, "D1", arm, nz2)[0]
                ref = R.exact_arm(L, THETA, arm, m=m, e=0.0, pz=0.0)["p1"]
                worst = max(worst, abs(mine - ref))
    L_.append(f"Check 2, gate noise only: D1 ff and off against rus_noise_desk.exact_arm (separate engine), L 1-3, "
              f"m 2-3: {'PASS' if worst < 1e-12 else 'FAIL'} (largest difference {worst:.1e})")
    if not quick:
        rows, worst = [], 0.0
        cases = [("D1", 1, 2, 0.1, 20000, 1), ("D2", 2, 2, 0.1, 20000, 2), ("D2", 1, 3, 0.2, 20000, 3),
                 ("coh", 1, 2, 0.2, 20000, 4), ("coh", 2, 2, 0.2, 10000, 5)]
        for d, L, m, g, shots, seed in cases:
            nz = noise(g)
            ex = coherent_p1(L, m, nz)[0] if d == "coh" else dynamic_any(L, m, d, "ff", nz)[0]
            mc = mc_coherent(L, m, nz, shots, seed) if d == "coh" else mc_dynamic(L, m, d, nz, shots, seed)
            z = (mc - ex) / math.sqrt(ex * (1 - ex) / shots)
            worst = max(worst, abs(z))
            rows.append(f"{d} L {L} m {m} gamma {g}: exact {ex:.3f}, MC {mc:.3f} ({z:+.1f} SE, {shots} shots)")
        L_.append(f"Check 3, gamma > 0, Monte Carlo over Kraus trajectories (state vector): "
                  f"{'PASS' if worst < 4 else 'FAIL'} (largest {worst:.1f} SE)")
        L_ += ["  " + r for r in rows]
    L_.append("")

    # main table
    res = {}
    for L in LS:
        for m in MS:
            for g in GAMMAS:
                nz = noise(g)
                for d in ("D1", "D2", "D3"):
                    for arm in ("ff", "off"):
                        res[(L, m, g, d, arm)] = dynamic_any(L, m, d, arm, nz)
                res[(L, m, g, "coh", "ff")] = coherent_p1(L, m, nz)
                if L == 1:
                    res[(L, m, g, "coh", "off")] = coherent_p1(L, m, nz, tries=1)
    nl = {(L, m): dynamic_any(L, m, "D1", "ff", noise(0, off=True))[0] for L in LS for m in MS}
    czs = {(L, m): coherent_p1(L, m, noise(0, off=True))[1] for L in LS for m in MS}

    L_.append("## A. ff: P(last output 1) and its error against the exact value (sin^2 q)^L, per design")
    L_.append("noiseless m tries = the value the designs reach without noise (the truncation at m tries). coh CZ = its "
              "CZ count (zipper+ lowered to cz + u).")
    L_.append("")
    L_.append("| L | m | exact | noiseless m tries | coh CZ | gamma | D1 | D2 | D3 | coh |")
    L_.append("|---|---|---|---|---|---|---|---|---|---|")
    for L in LS:
        for m in MS:
            for i, g in enumerate(GAMMAS):
                head = (f"| {L} | {m} | {exact[L]:.3f} | {nl[(L, m)]:.3f} | {czs[(L, m)]} |" if i == 0
                        else "| | | | | |")
                cells = [f"{res[(L, m, g, d, 'ff')][0]:.3f} ({res[(L, m, g, d, 'ff')][0] - exact[L]:+.3f})"
                         for d in ("D1", "D2", "D3", "coh")]
                L_.append(f"{head} {g} | " + " | ".join(cells) + " |")
    L_.append("")

    L_.append("## B. Loss to the device model: ff minus the noiseless value with the same m (what the noise takes)")
    L_.append("")
    L_.append("| L | m | gamma | D1 | D2 | D3 | coh |")
    L_.append("|---|---|---|---|---|---|---|")
    for L in LS:
        for m in MS:
            for g in GAMMAS:
                cells = [f"{res[(L, m, g, d, 'ff')][0] - nl[(L, m)]:+.3f}" for d in ("D1", "D2", "D3", "coh")]
                L_.append(f"| {L} | {m} | {g} | " + " | ".join(cells) + " |")
    L_.append("")

    L_.append("## C. CLOSER WITH CONTROL in each design's own pair (|off error| - |ff error| >= 2 SE_d, 4000 shots per "
              "arm): margin in units of 2 SE_d")
    L_.append("")
    L_.append("| L | m | gamma | D1 | D2 | D3 | coh (L = 1 only) |")
    L_.append("|---|---|---|---|---|---|---|")
    for L in LS:
        for m in MS:
            for g in GAMMAS:
                cells = []
                for d in ("D1", "D2", "D3", "coh"):
                    if (L, m, g, d, "off") not in res:
                        cells.append("-")
                        continue
                    f, o = res[(L, m, g, d, "ff")][0], res[(L, m, g, d, "off")][0]
                    sd = math.sqrt(f * (1 - f) / SHOTS + o * (1 - o) / SHOTS)
                    cells.append(f"{(abs(o - exact[L]) - abs(f - exact[L])) / (2 * sd):+.1f}")
                L_.append(f"| {L} | {m} | {g} | " + " | ".join(cells) + " |")
    L_.append("")

    L_.append("## D. Which design stays closest to what its circuit should give (smallest |ff - noiseless value with "
              "the same m|), and by how many 2 SE over the next (SE of the difference of two 4000-shot arms)")
    L_.append("Closeness to the exact value (table A) can come from a bias: in D2 / D3 the decay during a flipped wait "
              "turns a logical 0 into 1, toward the exact value at theta 1.1. This table judges against the noiseless "
              "value of the same circuit instead.")
    L_.append("")
    L_.append("| L | m | " + " | ".join(f"gamma {g}" for g in GAMMAS) + " |")
    L_.append("|---|---|" + "---|" * len(GAMMAS))
    for L in LS:
        for m in MS:
            cells = []
            for g in GAMMAS:
                errs = sorted((abs(res[(L, m, g, d, 'ff')][0] - nl[(L, m)]), d) for d in ("D1", "D2", "D3", "coh"))
                (e0, d0), (e1, d1) = errs[0], errs[1]
                if {d0, d1} == {"D2", "D3"}:
                    e1, d1 = errs[2][0], errs[2][1]
                    d0 = "D2/D3"
                p0 = res[(L, m, g, d0.split("/")[0], "ff")][0]
                p1_ = res[(L, m, g, d1, "ff")][0]
                sd = math.sqrt(p0 * (1 - p0) / SHOTS + p1_ * (1 - p1_) / SHOTS)
                cells.append(f"{d0} ({(e1 - e0) / (2 * sd):.1f} over {d1})")
            L_.append(f"| {L} | {m} | " + " | ".join(cells) + " |")
    L_.append("")

    L_.append("## E. Reading the last output flipped (D3) against flipped back (D2) when |1> is read worse: P(0|1) = "
              "e1, P(1|0) = 0.015; gamma 0.05; ff error")
    L_.append("")
    E1S = (0.015, 0.05, 0.1, 0.2)
    L_.append("| L | m | " + " | ".join(f"e1 {e:.3f}: D2 / D3 / coh" for e in E1S) + " |")
    L_.append("|---|---|" + "---|" * len(E1S))
    tabE = {}
    for L in LS:
        for m in MS:
            cells = []
            for e1 in E1S:
                nz = noise(0.05, e1=e1)
                v = [dynamic_any(L, m, "D2", "ff", nz)[0], dynamic_any(L, m, "D3", "ff", nz)[0],
                     coherent_p1(L, m, nz)[0]]
                tabE[(L, m, e1)] = v
                cells.append(" / ".join(f"{x - exact[L]:+.3f}" for x in v))
            L_.append(f"| {L} | {m} | " + " | ".join(cells) + " |")
    L_.append("")
    L_.append("These are illustrations of the shape (how each design's error moves with L, m and the decay during the "
              "waits), not predictions for a device. What to run is the owner's decision.")

    for k, v in res.items():
        L, m, g, d, arm = k
        out["cells"].append(dict(L=L, m=m, gamma=g, design=d, arm=arm, p1=v[0],
                                 still_failed=(v[1] if d != "coh" else None), exact=exact[L], noiseless=nl[(L, m)]))
    out["coh_cz"] = {f"L{L} m{m}": czs[(L, m)] for L, m in czs}
    out["readout_asymmetry"] = [dict(L=L, m=m, e1=e1, D2=v[0], D3=v[1], coh=v[2]) for (L, m, e1), v in tabE.items()]
    txt = "\n".join(L_) + "\n"
    if not quick:
        with open(os.path.join(HERE, "rus_decay_desk.txt"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(txt)
        with open(os.path.join(HERE, "rus_decay_desk.json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(as_text(out), fh, indent=1)
    print(txt)


if __name__ == "__main__":
    main()
