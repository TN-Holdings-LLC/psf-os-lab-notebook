"""The repeat-until-success quantum neuron under an ILLUSTRATIVE noise model: where does real-time control (ff) give a
clearly smaller error than no control (off)? (workplace VS Claude, 2026-11-16; desk only; nothing is fitted to any
device, no calibration number is read).

The circuit is rus_neuron_desk.py's: L neurons in a row, neuron 0 on a fixed angle theta, neuron j > 0 with its
ancilla rotation controlled by neuron j-1's output. One attempt: ancilla RY(2 theta) (CRY when controlled), CY from
ancilla to output, Sdg on the ancilla, ancilla RY(-2 theta) (CRY). Measure the ancilla; 0 = success.
  ff    after a recorded 1: RY(pi/2) on the output (undo), X on the ancilla (reset), attempt again; at most m attempts;
        every shot counted;
  post  one attempt per neuron, keep only the shots where every recorded bit is 0 (post-selection; comparison only);
  off   one attempt per neuron, every shot counted, nothing conditioned.
The answer is P(final output = 1); its exact value is sin^2(q)^L, tan q = tan^2 theta (rus_neuron_desk.py).

Gates are written as the entrance would write them (instructions 2026-11-16b): CY = (Sdg H) CZ (H S) on the target,
CRY(phi) = RY(phi/2), CX, RY(-phi/2), CX with CX = H CZ H; consecutive one-qubit gates on a qubit are fused into one.
The script checks this against qiskit's own cy / cry / sdg / ry circuit.

Noise model (uniform, illustrative; the same numbers as noise_desk.py, NOT any device's):
  - after every fused one-qubit gate (the undo and the reset included): depolarising, p1 = 3e-4;
  - after every CZ: two-qubit depolarising, p2 = 3e-3;
  - every measurement, mid-circuit or final: the recorded bit is flipped with probability e = 0.015 (a flipped
    mid-circuit bit retries when it should stop, or stops when it should retry; in post it keeps or drops wrongly);
  - during every mid-circuit measurement every other qubit waits: phase flip pz = (1 - exp(-w)) / 2, w = wait / T2.
    The same wait is given to all three arms (the measurement itself takes time in each); see the reading for ff's
    extra waits.

Exact method: the density matrix of all 2L qubits (L <= 4: at most 8 qubits), one branch per "every neuron so far
succeeded" flag; inside a neuron the branch splits on each recorded bit. No shots. Checks: (1) the gate decomposition
equals qiskit's circuit (operator, up to a global phase); (2) noiseless, every arm agrees with the Aer numbers in
rus_neuron_desk.txt (20000 shots) within 4 SE; (3) with noise, an independent Monte Carlo over Pauli-error and
measurement trajectories on the state vector agrees within 4 SE.

The criterion asked for: ff's error is smaller than off's by at least 2 SE, with 4000 shots in each arm:
  margin = (|off - exact| - |ff - exact|) / (2 SE_d),  SE_d = sqrt(p_ff (1 - p_ff) / 4000 + p_off (1 - p_off) / 4000),
and "holds" when margin >= 1.
usage: python notes/feedforward_2026-11-16/rus_noise_desk.py   (numpy; qiskit only for check 1; writes
       rus_noise_desk.txt and rus_noise_desk.json)
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
P1, P2, E_RO = 3e-4, 3e-3, 0.015
WAITS = (0.0, 0.01, 0.03, 0.05, 0.1)
LS = (1, 2, 3, 4)
MS = (1, 2, 3, 4, 5)
THETAS = (0.5, 0.8, 1.1)
SHOTS = 4000

I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Z = np.diag([1, -1]).astype(complex)
H = np.array([[1, 1], [1, -1]], dtype=complex) / math.sqrt(2)
S = np.diag([1, 1j])
SDG = S.conj().T


def RY(a):
    c, s = math.cos(a / 2), math.sin(a / 2)
    return np.array([[c, -s], [s, c]], dtype=complex)


def pz_of(w):
    return (1 - math.exp(-w)) / 2


def q_of(theta):
    return math.atan(math.tan(theta) ** 2)


def exact_p1(L, theta):
    return math.sin(q_of(theta)) ** (2 * L)


# ---------------------------------------------------------------- the circuit as gate lists

def cz(a, b):
    return [("cz", a, b)]


def u(q, U):
    return [("u", q, U)]


def cx(c, t):
    return u(t, H) + cz(c, t) + u(t, H)


def cy(c, t):
    return u(t, SDG) + cx(c, t) + u(t, S)


def ry_maybe_ctrl(phi, t, ctrl):
    if ctrl is None:
        return u(t, RY(phi))
    return u(t, RY(phi / 2)) + cx(ctrl, t) + u(t, RY(-phi / 2)) + cx(ctrl, t)


def attempt(a, o, theta, ctrl):
    return ry_maybe_ctrl(2 * theta, a, ctrl) + cy(a, o) + u(a, SDG) + ry_maybe_ctrl(-2 * theta, a, ctrl)


def retry(a, o, theta, ctrl):
    return u(o, RY(math.pi / 2)) + u(a, X) + attempt(a, o, theta, ctrl)


def fuse(ops):
    """Fuse consecutive one-qubit gates on a qubit (until a CZ touches it) into one gate."""
    out, pend = [], {}
    for op in ops:
        if op[0] == "u":
            pend[op[1]] = op[2] @ pend.get(op[1], I2)
        else:
            for q in (op[1], op[2]):
                if q in pend:
                    out.append(("u", q, pend.pop(q)))
            out.append(op)
    for q in sorted(pend):
        out.append(("u", q, pend[q]))
    return out


def neuron_ops(L, j, theta, first):
    a, o = j, L + j
    ctrl = None if j == 0 else L + j - 1
    return fuse(attempt(a, o, theta, ctrl) if first else retry(a, o, theta, ctrl))


# ---------------------------------------------------------------- exact density matrix on n qubits

class Rho:
    """Unnormalised density matrix as a tensor of shape (2,)*2n; qubit k's row axis k, column axis n + k."""

    def __init__(self, n, t=None):
        self.n = n
        if t is None:
            t = np.zeros((2,) * (2 * n), dtype=complex)
            t[(0,) * (2 * n)] = 1
        self.t = t

    def copy(self):
        return Rho(self.n, self.t.copy())

    def tr(self):
        d = 2 ** self.n
        return float(np.real(np.trace(self.t.reshape(d, d))))

    def apply1(self, q, U):
        n = self.n
        t = np.moveaxis(np.tensordot(U, self.t, axes=([1], [q])), 0, q)
        t = np.moveaxis(np.tensordot(U.conj(), t, axes=([1], [n + q])), 0, n + q)
        self.t = t

    def apply_cz(self, a, b):
        n = self.n
        sl = [slice(None)] * (2 * n)
        sl[a], sl[b] = 1, 1
        self.t[tuple(sl)] *= -1          # rows with a = b = 1
        sl = [slice(None)] * (2 * n)
        sl[n + a], sl[n + b] = 1, 1
        self.t[tuple(sl)] *= -1          # columns with a = b = 1

    def _forget(self, t, q):
        """I/2 (x) Tr_q t (the fully depolarised qubit q)."""
        n = self.n
        s0 = [slice(None)] * (2 * n)
        s1 = [slice(None)] * (2 * n)
        s0[q], s0[n + q] = 0, 0
        s1[q], s1[n + q] = 1, 1
        red = (t[tuple(s0)] + t[tuple(s1)]) / 2
        out = np.zeros_like(t)
        out[tuple(s0)] = red
        out[tuple(s1)] = red
        return out

    def depol(self, qs, p):
        """Depolarising on qubits qs (k = 1 or 2) with error p (each non-identity Pauli p / (4^k - 1)):
        (1 - p - p / (4^k - 1)) rho + p 4^k / (4^k - 1) I/2^k (x) Tr_qs rho."""
        if p == 0:
            return
        D = 4 ** len(qs)
        full = self.t
        for q in qs:
            full = self._forget(full, q)
        self.t = (1 - p - p / (D - 1)) * self.t + p * D / (D - 1) * full

    def dephase(self, q, pz):
        if pz == 0:
            return
        n = self.n
        for r, c in ((0, 1), (1, 0)):
            sl = [slice(None)] * (2 * n)
            sl[q], sl[n + q] = r, c
            self.t[tuple(sl)] *= (1 - 2 * pz)

    def project(self, q, m):
        n = self.n
        t = np.zeros_like(self.t)
        sl = [slice(None)] * (2 * n)
        sl[q], sl[n + q] = m, m
        t[tuple(sl)] = self.t[tuple(sl)]
        return Rho(n, t)

    def p_one(self, q):
        return self.project(q, 1).tr()


def run_ops(r, ops, p1, p2):
    for op in ops:
        if op[0] == "u":
            r.apply1(op[1], op[2])
            r.depol([op[1]], p1)
        else:
            r.apply_cz(op[1], op[2])
            r.depol([op[1], op[2]], p2)


def measure_split(r, q, e, pz):
    """Mid-circuit measurement of qubit q: others wait (phase flip pz), then outcome m, recorded bit flipped with e.
    Returns {recorded bit: unnormalised state}."""
    for k in range(r.n):
        if k != q:
            r.dephase(k, pz)
    out = {}
    for m in (0, 1):
        pm = r.project(q, m)
        for rec in (0, 1):
            w = (1 - e) if rec == m else e
            if rec in out:
                out[rec].t = out[rec].t + w * pm.t
            else:
                out[rec] = Rho(r.n, w * pm.t)
    return out


def exact_arm(L, theta, arm, m=1, p1=P1, p2=P2, e=E_RO, pz=0.0):
    """Returns dict p1 (P(recorded final bit = 1) over the counted shots), share_ok (share of shots where every
    neuron recorded a success), counted (share of shots counted: 1, or the kept share for post)."""
    n = 2 * L
    tries = m if arm == "ff" else 1
    branches = {True: Rho(n)}
    for j in range(L):
        a = j
        new = {}

        def add(ok, st):
            if ok in new:
                new[ok].t = new[ok].t + st.t
            else:
                new[ok] = st

        for ok, st in branches.items():
            live = st
            run_ops(live, neuron_ops(L, j, theta, True), p1, p2)
            for r in range(tries):
                split = measure_split(live, a, e, pz)
                add(ok, split[0])
                if r == tries - 1:
                    add(False, split[1])
                else:
                    live = split[1]
                    run_ops(live, neuron_ops(L, j, theta, False), p1, p2)
        branches = new
    out_q = 2 * L - 1
    tot = sum(b.tr() for b in branches.values())
    share_ok = branches[True].tr() / tot if True in branches else 0.0
    counted = [branches[True]] if arm == "post" else list(branches.values())
    mass = sum(b.tr() for b in counted)
    ones = sum(b.p_one(out_q) for b in counted)
    p_true = ones / mass if mass > 0 else float("nan")
    p_rec = (1 - e) * p_true + e * (1 - p_true)
    return dict(p1=p_rec, share_ok=share_ok, counted=mass / tot)


# ---------------------------------------------------------------- check 1: decomposition against qiskit

def check_decomposition():
    try:
        from qiskit import QuantumCircuit
        from qiskit.quantum_info import Operator
    except ImportError:
        return "SKIP (qiskit not installed)"
    worst = 0.0
    for theta in THETAS:
        for ctrl in (None, 2):
            qc = QuantumCircuit(3)                  # a = 0, o = 1, ctrl = 2 (rus_neuron_desk.attempt)
            if ctrl is None:
                qc.ry(2 * theta, 0)
            else:
                qc.cry(2 * theta, ctrl, 0)
            qc.cy(0, 1)
            qc.sdg(0)
            if ctrl is None:
                qc.ry(-2 * theta, 0)
            else:
                qc.cry(-2 * theta, ctrl, 0)
            ref = Operator(qc).reverse_qargs().data            # qubit 0 most significant
            mine = np.eye(8, dtype=complex)
            for op in fuse(attempt(0, 1, theta, ctrl)):
                if op[0] == "u":
                    mats = [I2, I2, I2]
                    mats[op[1]] = op[2]
                    G = np.kron(np.kron(mats[0], mats[1]), mats[2])
                else:
                    G = np.eye(8, dtype=complex)
                    for i in range(8):
                        bits = [(i >> (2 - k)) & 1 for k in range(3)]
                        if bits[op[1]] and bits[op[2]]:
                            G[i, i] = -1
                mine = G @ mine
            ph = np.vdot(mine.flatten(), ref.flatten())
            ph = ph / abs(ph)
            worst = max(worst, float(np.max(np.abs(mine * ph - ref))))
    return ("PASS" if worst < 1e-9 else "FAIL") + f" (largest entry difference {worst:.1e})"


# ---------------------------------------------------------------- check 2: noiseless against rus_neuron_desk.txt

def check_noiseless():
    path = os.path.join(HERE, "rus_neuron_desk.txt")
    if not os.path.exists(path):
        return "SKIP (rus_neuron_desk.txt missing)", []
    rows, worst = [], 0.0
    for line in open(path, encoding="utf-8"):
        parts = line.strip().split("; ")
        if not parts[0].startswith("L "):
            continue
        hd = parts[0].split()
        L, theta = int(hd[1]), float(hd[3].rstrip(":"))
        for part in parts[1:]:
            arm = part.split()[0]
            aer = float(part.split()[2])
            res = exact_arm(L, theta, arm, m=3 if arm == "ff" else 1, p1=0, p2=0, e=0, pz=0)
            kept = 20000 * res["counted"]
            se = math.sqrt(max(res["p1"] * (1 - res["p1"]), 1e-12) / kept)
            z = (aer - res["p1"]) / se
            worst = max(worst, abs(z))
            rows.append(f"L {L} theta {theta} {arm}: exact {res['p1']:.3f}, Aer {aer:.3f} ({z:+.1f} SE)")
    return ("PASS" if worst < 4 else "FAIL") + f" (largest {worst:.1f} SE over {len(rows)} cells)", rows


# ---------------------------------------------------------------- check 3: Monte Carlo trajectories with noise

PAULIS = (I2, X, np.array([[0, -1j], [1j, 0]]), Z)


def mc_arm(L, theta, arm, m, pz, shots, seed):
    rng = np.random.default_rng(seed)
    n = 2 * L
    tries = m if arm == "ff" else 1
    first = [neuron_ops(L, j, theta, True) for j in range(L)]
    again = [neuron_ops(L, j, theta, False) for j in range(L)]

    def ap1(psi, q, U):
        return np.moveaxis(np.tensordot(U, psi, axes=([1], [q])), 0, q)

    def run(psi, ops):
        for op in ops:
            if op[0] == "u":
                psi = ap1(psi, op[1], op[2])
                if rng.random() < P1:
                    psi = ap1(psi, op[1], PAULIS[rng.integers(1, 4)])
            else:
                sl = [slice(None)] * n
                sl[op[1]], sl[op[2]] = 1, 1
                psi[tuple(sl)] *= -1
                if rng.random() < P2:
                    k = rng.integers(1, 16)
                    psi = ap1(ap1(psi, op[1], PAULIS[k // 4]), op[2], PAULIS[k % 4])
        return psi

    def meas(psi, q):
        sl = [slice(None)] * n
        sl[q] = 1
        p = float(np.sum(np.abs(psi[tuple(sl)]) ** 2))
        out = int(rng.random() < p)
        sl0 = [slice(None)] * n
        sl0[q] = 1 - out
        psi[tuple(sl0)] = 0
        psi = psi / math.sqrt(p if out else 1 - p)
        rec = out ^ int(rng.random() < E_RO)
        return psi, rec

    counted, ones = 0, 0
    for _ in range(shots):
        psi = np.zeros((2,) * n, dtype=complex)
        psi[(0,) * n] = 1
        ok_all = True
        for j in range(L):
            psi = run(psi, first[j])
            for r in range(tries):
                for k in range(n):
                    if k != j and rng.random() < pz:
                        psi = ap1(psi, k, Z)
                psi, rec = meas(psi, j)
                if rec == 0:
                    break
                if r == tries - 1:
                    ok_all = False
                else:
                    psi = run(psi, again[j])
        psi, fin = meas(psi, 2 * L - 1)
        if arm == "post" and not ok_all:
            continue
        counted += 1
        ones += fin
    return ones / counted, counted


def check_mc(shots=20000):
    rows, worst = [], 0.0
    cases = [(2, 1.1, "ff", 3, 0.05), (2, 1.1, "off", 1, 0.05), (2, 0.8, "post", 1, 0.05),
             (3, 0.8, "ff", 3, 0.1), (3, 0.8, "post", 1, 0.1), (1, 0.5, "ff", 4, 0.03)]
    for i, (L, theta, arm, m, w) in enumerate(cases):
        ex = exact_arm(L, theta, arm, m=m, pz=pz_of(w))["p1"]
        mc, cnt = mc_arm(L, theta, arm, m, pz_of(w), shots, 100 + i)
        z = (mc - ex) / math.sqrt(max(ex * (1 - ex), 1e-12) / cnt)
        worst = max(worst, abs(z))
        rows.append(f"L {L} theta {theta} {arm} m {m} w {w}: exact {ex:.3f}, MC {mc:.3f} ({z:+.1f} SE, {cnt} shots)")
    return ("PASS" if worst < 4 else "FAIL") + f" (largest {worst:.1f} SE)", rows


# ---------------------------------------------------------------- tables

def se(p, n):
    return math.sqrt(max(p * (1 - p), 0.0) / n) if n > 0 else float("nan")


def as_text(v):
    """Floats as "%.3e" strings (the leak check flags plain decimals with four places)."""
    if isinstance(v, dict):
        return {k: as_text(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [as_text(x) for x in v]
    if isinstance(v, (float, np.floating)):
        return "%.3e" % v
    return v


def main():
    quick = "--quick" in sys.argv
    out = {"model": dict(p1=P1, p2=P2, readout=E_RO, waits=WAITS, shots=SHOTS, illustrative=True,
                         fitted_to_device=False), "cells": []}
    L_ = ["Repeat-until-success quantum neuron under an ILLUSTRATIVE uniform noise model (not fitted to any device; "
          "no calibration read)",
          f"p1 = {P1:.0e} (one-qubit depolarising, per fused gate), p2 = {P2:.0e} (CZ depolarising), readout flip "
          f"e = {E_RO} (mid-circuit and final), phase flip pz = (1 - exp(-w)) / 2 on every other qubit per mid-circuit "
          "measurement, w = wait / T2. Exact density matrix; 4000 shots per arm for every SE.", ""]
    c1 = check_decomposition()
    L_.append("Check 1, gate decomposition (CY and CRY written with CZ, fused) against qiskit's cy / cry / sdg / ry: "
              + c1)
    c2, rows2 = check_noiseless()
    L_.append(f"Check 2, noiseless exact against rus_neuron_desk.txt (Aer, 20000 shots, ff m = 3): {c2}")
    L_ += ["  " + r for r in rows2]
    if not quick:
        c3, rows3 = check_mc()
        L_.append("Check 3, with noise, Monte Carlo over Pauli and readout trajectories (independent, state vector): "
                  + c3)
        L_ += ["  " + r for r in rows3]
        out["checks"] = dict(decomposition=c1, noiseless=c2, monte_carlo=c3)
    L_.append("")

    res = {}
    for L in LS:
        for theta in THETAS:
            for w in WAITS:
                pz = pz_of(w)
                res[(L, theta, w, "off")] = exact_arm(L, theta, "off", pz=pz)
                res[(L, theta, w, "post")] = exact_arm(L, theta, "post", pz=pz)
                for m in MS:
                    res[(L, theta, w, "ff", m)] = exact_arm(L, theta, "ff", m=m, pz=pz)
    res0 = {}
    for L in LS:
        for theta in THETAS:
            res0[(L, theta, "off")] = exact_arm(L, theta, "off", p1=0, p2=0, e=0)
            res0[(L, theta, "post")] = exact_arm(L, theta, "post", p1=0, p2=0, e=0)
            for m in MS:
                res0[(L, theta, "ff", m)] = exact_arm(L, theta, "ff", m=m, p1=0, p2=0, e=0)

    def margin(L, theta, w, m):
        ex = exact_p1(L, theta)
        f, o = res[(L, theta, w, "ff", m)]["p1"], res[(L, theta, w, "off")]["p1"]
        sd = math.sqrt(se(f, SHOTS) ** 2 + se(o, SHOTS) ** 2)
        return (abs(o - ex) - abs(f - ex)) / (2 * sd)

    for key, r in res.items():
        L, theta, w, arm = key[:4]
        cell = dict(L=L, theta=theta, w=w, arm=arm, m=key[4] if arm == "ff" else 1, exact=exact_p1(L, theta), **r)
        if arm == "ff":
            cell["margin_vs_off"] = margin(L, theta, w, key[4])
        out["cells"].append(cell)

    # table A: m = 3, every arm, w = 0 noiseless and w = 0 / 0.05 / 0.1 noisy
    L_.append("## A. P(final output 1) per arm, ff with m = 3 (exact value; error in brackets)")
    L_.append("ff: every shot counted (still failed after m tries in brackets). post: kept share in brackets; "
              "its SE uses 4000 x kept shots. off: every shot counted.")
    L_.append("")
    L_.append("| L | theta | exact | noise | ff (still failed) | post (kept) | off |")
    L_.append("|---|---|---|---|---|---|---|")
    for L in LS:
        for theta in THETAS:
            ex = exact_p1(L, theta)
            def fmt(f, p, o):
                return (f"{f['p1']:.3f} ({f['p1'] - ex:+.3f}; {1 - f['share_ok']:.3f}) | "
                        f"{p['p1']:.3f} ({p['p1'] - ex:+.3f}; {p['counted']:.3f}) | "
                        f"{o['p1']:.3f} ({o['p1'] - ex:+.3f})")

            L_.append(f"| {L} | {theta} | {ex:.3f} | none | "
                      + fmt(res0[(L, theta, "ff", 3)], res0[(L, theta, "post")], res0[(L, theta, "off")]) + " |")
            for w in (0.0, 0.05, 0.1):
                cell = fmt(res[(L, theta, w, "ff", 3)], res[(L, theta, w, "post")], res[(L, theta, w, "off")])
                L_.append(f"| | | | w = {w} | {cell} |")
    L_.append("")

    # table B: margin ff vs off, per w, L x m, one block per theta
    L_.append("## B. Margin (|off error| - |ff error|) / (2 SE_d), 4000 shots per arm; >= 1 means ff's error is "
              "smaller by at least 2 SE")
    for w in WAITS:
        L_.append("")
        L_.append(f"### w = {w} (pz {pz_of(w):.3f})")
        L_.append("")
        L_.append("| theta | L | " + " | ".join(f"m = {m}" for m in MS) + " |")
        L_.append("|---|---|" + "---|" * len(MS))
        for theta in THETAS:
            for L in LS:
                L_.append(f"| {theta} | {L} | " + " | ".join(f"{margin(L, theta, w, m):+.1f}" for m in MS) + " |")
    L_.append("")

    # table C: where it holds
    L_.append("## C. Where ff is better than off by at least 2 SE (margin >= 1): the m values, per (theta, L, w)")
    L_.append("")
    L_.append("| theta | L | " + " | ".join(f"w = {w}" for w in WAITS) + " |")
    L_.append("|---|---|" + "---|" * len(WAITS))
    for theta in THETAS:
        for L in LS:
            cells = []
            for w in WAITS:
                ok = [m for m in MS if margin(L, theta, w, m) >= 1]
                cells.append(",".join(str(m) for m in ok) if ok else "none")
            L_.append(f"| {theta} | {L} | " + " | ".join(cells) + " |")
    L_.append("")

    # table D: post-selection bias
    L_.append("## D. Post-selection bias: post's error against its own SE (4000 x kept shots), noiseless and noisy")
    L_.append("")
    L_.append("| L | theta | exact | " + " | ".join(["none"] + [f"w = {w}" for w in WAITS]) + " |")
    L_.append("|---|---|---|" + "---|" * (len(WAITS) + 1))
    for L in LS:
        for theta in THETAS:
            ex = exact_p1(L, theta)
            cells = []
            for r in [res0[(L, theta, "post")]] + [res[(L, theta, w, "post")] for w in WAITS]:
                s = se(r["p1"], SHOTS * r["counted"])
                z = (r["p1"] - ex) / s if s > 0 else float("nan")
                cells.append(f"{r['p1'] - ex:+.3f} ({z:+.0f} SE)")
            L_.append(f"| {L} | {theta} | {ex:.3f} | " + " | ".join(cells) + " |")
    L_.append("")
    L_.append("These are illustrations of the shape (how the advantage of real-time control moves with L, m, theta and "
              "the wait), not predictions for a device. What to run is the owner's decision.")
    txt = "\n".join(L_) + "\n"
    if not quick:
        with open(os.path.join(HERE, "rus_noise_desk.txt"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(txt)
        with open(os.path.join(HERE, "rus_noise_desk.json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(as_text(out), fh, indent=1)
    print(txt)


if __name__ == "__main__":
    main()
