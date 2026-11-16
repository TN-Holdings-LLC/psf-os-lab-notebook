"""Feed-forward test under an ILLUSTRATIVE noise model: how far above 0.75 does the success stay, per k? (workplace VS
Claude, 2026-11-16; desk only; nothing is fitted to any device, no calibration number is read).

The circuit is ff_desk.py's: qubit 0 gets H, T^dag and H^k; then k hops (qubit i+1: H; CZ(i, i+1); H on qubit i;
measure qubit i; if the recorded bit is 1, X on qubit i+1 at once); at the end T and H on qubit k and its measurement.
Success = the final recorded bit is 0. Ideal: 1 with feed-forward ("ff"), 0.75 / 0.5 without ("off", k = 1 / k >= 2);
no processing of the recorded bits without feed-forward gets above 0.75 (ff_desk.py).

Noise model (uniform, illustrative; the same number on every element, NOT any device's):
  - after every one-qubit gate (H, T, T^dag, the conditional X): depolarising, error p1 = 3e-4 (X, Y, Z each p1/3);
  - after every CZ: two-qubit depolarising, error p2 = 3e-3 (each of the 15 non-identity Paulis p2/15);
  - every measurement, mid-circuit or final: the recorded bit is flipped with probability e = 0.015 (a flipped
    mid-circuit bit applies the wrong correction);
  - while qubit i is measured and the condition is decided, qubit i+1 waits: phase flip with probability
    pz = (1 - exp(-w)) / 2, w = (measurement + feed-forward wait) / T2, for several illustrative w.
    w = 0.05 is, e.g., a 5 us wait against T2 = 100 us; these are examples, not a device's numbers.

Exact method: after its measurement a qubit is never used again, so at any time only two qubits are alive (the
carrier and the next one). Each hop is applied as a channel on a 2-qubit density matrix, the measured qubit is
traced out per outcome, and the recorded bit's flip and the conditional X are mixed in. No shots: exact
probabilities. Cross-check: an independent Monte Carlo over Pauli-error trajectories on the full (k + 1)-qubit state
vector (k = 1, 2, 3, 50000 shots each) must agree within 4 standard errors.

The margin is written in units of the 2 SE of a 4000-shot job (binomial, at the noisy success p): (p - 0.75) / (2 SE).
usage: python notes/feedforward_2026-11-16/noise_desk.py   (writes noise_desk.txt and noise_desk.json)
"""
import itertools
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
P1, P2, E_RO = 3e-4, 3e-3, 0.015
WAITS = (0.0, 0.01, 0.03, 0.05, 0.1, 0.2)         # w = wait / T2, illustrative
KS = (1, 2, 3, 4, 6, 8, 12, 16, 24, 32)
SHOTS = 4000
BOUND = 0.75

I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.diag([1, -1]).astype(complex)
H = np.array([[1, 1], [1, -1]], dtype=complex) / math.sqrt(2)
T = np.diag([1, np.exp(1j * math.pi / 4)])
TDG = T.conj().T
PAULI = (I2, X, Y, Z)
CZ = np.diag([1, 1, 1, -1]).astype(complex)


def pz_of(w):
    return (1 - math.exp(-w)) / 2


# ---------------------------------------------------------------- exact channel (1 or 2 live qubits)

def u1(rho, U):
    return U @ rho @ U.conj().T


def dep1(rho, p):
    return (1 - p) * rho + p / 3 * sum(u1(rho, P) for P in PAULI[1:])


def on(U, which):
    """U on qubit `which` (0 = carrier, 1 = next) of the 2-qubit space (carrier is the first tensor factor)."""
    return np.kron(U, I2) if which == 0 else np.kron(I2, U)


def dep1_2(rho, p, which):
    return (1 - p) * rho + p / 3 * sum(u1(rho, on(P, which)) for P in PAULI[1:])


def dep2(rho, p):
    out = (1 - p) * rho
    for a, b in itertools.product(range(4), repeat=2):
        if a or b:
            out = out + p / 15 * u1(rho, np.kron(PAULI[a], PAULI[b]))
    return out


def dephase(rho, pz, which=None):
    Zq = Z if which is None else on(Z, which)
    return (1 - pz) * rho + pz * u1(rho, Zq)


def exact_success(k, ff=True, p1=P1, p2=P2, e=E_RO, pz=0.0):
    plus0 = np.array([[1, 0], [0, 0]], dtype=complex)
    rho = plus0
    for U in [H, TDG] + [H] * k:
        rho = dep1(u1(rho, U), p1)
    for _ in range(k):
        nxt = dep1(u1(plus0, H), p1)
        r2 = np.kron(rho, nxt)
        r2 = dep2(u1(r2, CZ), p2)
        r2 = dep1_2(u1(r2, on(H, 0)), p1, 0)
        r2 = dephase(r2, pz, 1)                          # the next qubit waits during the measurement
        new = np.zeros((2, 2), dtype=complex)
        for m in (0, 1):
            Pm = np.zeros((2, 2))
            Pm[m, m] = 1
            blk = np.kron(Pm, I2) @ r2 @ np.kron(Pm, I2)
            red = blk.reshape(2, 2, 2, 2)[m, :, m, :]    # trace out the carrier, outcome m
            for r in (0, 1):
                w = (1 - e) if r == m else e
                st = red
                if ff and r == 1:
                    st = dep1(u1(st, X), p1)
                new = new + w * st
        rho = new
    for U in (T, H):
        rho = dep1(u1(rho, U), p1)
    p0 = float(np.real(rho[0, 0]))
    return (1 - e) * p0 + e * (1 - p0)


# ---------------------------------------------------------------- independent cross-check: trajectories

def mc_success(k, ff, pz, shots, seed):
    """Pauli-error trajectories on the full (k + 1)-qubit state vector; measurement by sampling and collapse."""
    rng = np.random.default_rng(seed)
    n = k + 1
    ok = 0

    def apply1(psi, U, q):
        psi = psi.reshape([2] * n)
        psi = np.moveaxis(np.tensordot(U, psi, axes=([1], [q])), 0, q)
        return psi.reshape(-1)

    def err1(psi, q, p):
        if rng.random() < p:
            psi = apply1(psi, PAULI[rng.integers(1, 4)], q)
        return psi

    def gate1(psi, U, q):
        return err1(apply1(psi, U, q), q, P1)

    def cz(psi, a, b):
        psi = psi.reshape([2] * n).copy()
        idx = [slice(None)] * n
        idx[a], idx[b] = 1, 1
        psi[tuple(idx)] *= -1
        psi = psi.reshape(-1)
        if rng.random() < P2:
            c = rng.integers(1, 16)
            psi = apply1(apply1(psi, PAULI[c // 4], a), PAULI[c % 4], b)
        return psi

    def measure(psi, q):
        t = psi.reshape([2] * n)
        p1_ = float(np.sum(np.abs(np.take(t, 1, axis=q)) ** 2))
        m = int(rng.random() < p1_)
        t = t.copy()
        idx = [slice(None)] * n
        idx[q] = 1 - m
        t[tuple(idx)] = 0
        t = t / math.sqrt(p1_ if m else 1 - p1_)
        rec = m ^ int(rng.random() < E_RO)
        return t.reshape(-1), rec

    for _ in range(shots):
        psi = np.zeros(2 ** n, dtype=complex)
        psi[0] = 1
        for U in [H, TDG] + [H] * k:
            psi = gate1(psi, U, 0)
        for i in range(k):
            psi = gate1(psi, H, i + 1)
            psi = cz(psi, i, i + 1)
            psi = gate1(psi, H, i)
            if rng.random() < pz:
                psi = apply1(psi, Z, i + 1)
            psi, rec = measure(psi, i)
            if ff and rec:
                psi = gate1(psi, X, i + 1)
        psi = gate1(psi, T, k)
        psi = gate1(psi, H, k)
        _, rec = measure(psi, k)
        ok += rec == 0
    return ok / shots


def main():
    L = ["Feed-forward test under an ILLUSTRATIVE uniform noise model (not fitted to any device; no calibration read)",
         f"p1 = {P1:.0e} (one-qubit depolarising), p2 = {P2:.0e} (CZ depolarising), readout flip e = {E_RO:g} "
         "(mid-circuit and final), phase flip pz = (1 - exp(-w)) / 2 on the waiting qubit per hop, w = wait / T2.",
         f"Exact (2 live qubits per hop). Margin = (p - {BOUND}) / (2 SE), 2 SE = 2 sqrt(p (1 - p) / {SHOTS}).", ""]
    # checks: noiseless ideal values
    ideal = [(k, exact_success(k, True, 0, 0, 0, 0), exact_success(k, False, 0, 0, 0, 0)) for k in KS]
    assert all(abs(f - 1) < 1e-12 for _, f, _ in ideal)
    assert all(abs(o - (0.75 if k == 1 else 0.5)) < 1e-12 for k, _, o in ideal)
    L.append("Check, noiseless: ff = 1 for every k; off = 0.75 at k = 1 and 0.5 at k >= 2 (exact). PASS")
    # cross-check against trajectories
    cc = []
    for k, w in ((1, 0.05), (2, 0.1), (3, 0.2)):
        pz = pz_of(w)
        for ff in (True, False):
            ex = exact_success(k, ff, pz=pz)
            mc = mc_success(k, ff, pz, 50000, seed=100 * k + ff)
            se = math.sqrt(ex * (1 - ex) / 50000)
            cc.append(dict(k=k, w=w, arm="ff" if ff else "off", exact=ex, mc=mc, z=(mc - ex) / se))
    assert all(abs(c["z"]) <= 4 for c in cc), cc
    L.append("Cross-check, Monte Carlo over Pauli trajectories on the full state (50000 shots each): "
             + "; ".join(f"k {c['k']} w {c['w']} {c['arm']}: exact {c['exact']:.3f}, MC {c['mc']:.3f} "
                         f"({c['z']:+.1f} SE)" for c in cc) + ". PASS (all within 4 SE)")
    L.append("")
    rows = []
    hdr = "| k | " + " | ".join(f"w = {w:g} (pz {pz_of(w):.3f})" for w in WAITS) + " |"
    L += ["## Success with feed-forward, and the margin above 0.75 in units of 2 SE (4000 shots)", "",
          "Each cell: success p / margin. The ideal is 1; without feed-forward no processing exceeds 0.75.", "",
          hdr, "|---|" + "---|" * len(WAITS)]
    for k in KS:
        cells = []
        for w in WAITS:
            p = exact_success(k, True, pz=pz_of(w))
            off = exact_success(k, False, pz=pz_of(w))
            se2 = 2 * math.sqrt(p * (1 - p) / SHOTS)
            mg = (p - BOUND) / se2
            rows.append(dict(k=k, w=w, pz=pz_of(w), success_ff=p, success_off=off, two_se=se2, margin_in_2se=mg))
            cells.append(f"{p:.3f} / {mg:.1f}")
        L.append(f"| {k} | " + " | ".join(cells) + " |")
    L += ["", "## The off arm (conditional X removed) under the same noise", "",
          "| k | " + " | ".join(f"w = {w:g}" for w in WAITS) + " |", "|---|" + "---|" * len(WAITS)]
    for k in KS:
        L.append(f"| {k} | " + " | ".join(f"{r['success_off']:.3f}" for r in rows if r["k"] == k) + " |")
    L += ["", "## Largest k in this list whose margin is at least 3, 5, 10 times 2 SE (4000 shots)", "",
          "| w | margin >= 3 | >= 5 | >= 10 |", "|---|---|---|---|"]
    for w in WAITS:
        mk = []
        for t in (3, 5, 10):
            ks = [r["k"] for r in rows if r["w"] == w and r["margin_in_2se"] >= t]
            mk.append(str(max(ks)) if ks else "none")
        L.append(f"| {w:g} | " + " | ".join(mk) + " |")
    L += ["", "These are illustrations of the shape (how the margin falls with k and with the wait), not predictions "
          "for a device. The k to run is the owner's decision."]
    open(os.path.join(HERE, "noise_desk.txt"), "w", encoding="utf-8").write("\n".join(L) + "\n")

    def ex(o):  # exponent strings (seal.py leakcheck)
        if isinstance(o, float):
            return f"{o:.3e}"
        if isinstance(o, dict):
            return {k_: ex(v) for k_, v in o.items()}
        if isinstance(o, list):
            return [ex(v) for v in o]
        return o
    json.dump(ex(dict(model=dict(p1=P1, p2=P2, readout_flip=E_RO, waits=list(WAITS), shots=SHOTS,
                                 note="illustrative, uniform, not fitted to any device"),
                      cross_check=cc, rows=rows)),
              open(os.path.join(HERE, "noise_desk.json"), "w"), indent=1)
    print("\n".join(L))


if __name__ == "__main__":
    main()
