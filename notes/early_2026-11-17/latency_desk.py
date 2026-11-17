"""Why the early chain did not pay on fez (T4 against T2, 2026-11-17): an ILLUSTRATIVE noise model with a decision
latency per conditional and decay while waiting (home VS Claude, 2026-11-17 evening; desk only, not declared; nothing
is fitted to any device and no calibration or error number is read).

Circuits: the compiled circuits that ran on ibm_fez tonight, read from results/ff-night-2026-11-17/compound/job (T2,
the third design rd1..rd5) and results/ff-night-2026-11-17/early/job (T4, the early chain ea1..ea5), barriers kept.

Timing: the time-budget ledger (notes/timebudget_2026-11-17/ledger.py): FakeMarrakesh median lengths (sx / x 36 ns,
rz 0, cz 68 ns, measure 2.584 us), an as-soon-as-possible schedule as built (barriers kept), and a decision latency
LAT per conditional (0, 0.5, 1, 2 us; examples): the conditional's qubits wait LAT before its body runs (the ledger's
model: the latency holds the conditional's own qubits; whether a device holds every qubit is not modelled).

Noise (uniform, illustrative, the same on every element):
  - one-qubit gates sx / x: depolarising 3e-4; cz: two-qubit depolarising 3e-3 (0.3 % per CZ); rz exact;
  - readout: the recorded bit flipped with 0.015 (mid-circuit and final);
  - idle: on every qubit, between its first operation and each later one, amplitude damping 1 - exp(-t / T1) and a
    phase flip (1 - exp(-t / Tphi)) / 2 with 1 / Tphi = 1 / T2 - 1 / (2 T1); T2 = T1; T1 = 150 us and an effective
    50 us (examples; the control test of 2026-11-16 lost |1> as if T1 were 20-45 us during measurement waits);
  - a measured qubit is projected at the start of its measurement and then idles for the measurement's length.
Engine: noise trajectories, batched over shots on the state vector of the touched qubits, conditionals applied per
shot. Check: with every noise off, P(last output 1, as declared) equals the noiseless values of
notes/compound_2026-11-17/ideal.json within the shot error.
Scoring: the declared scorer of T4 (gpu/early_night.py score --rd) on copies of tonight's job folders whose user cells
are replaced by the simulated counts (the sentinel rows are left as the device returned them; never judged).
usage: python notes/early_2026-11-17/latency_desk.py WORKDIR [--shots 16000] [--workers 12]
Writes notes/early_2026-11-17/latency_desk.json and latency_desk.txt."""
import argparse
import itertools
import json
import math
import os
import shutil
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(NB, "notes", "timebudget_2026-11-17"))
import ledger as LG  # noqa: E402

P1Q, P2Q, E_RO = 3e-4, 3e-3, 0.015
LATS = (0.0, 0.5, 1.0, 2.0)
T1S = (150e-6, 50e-6)
JOBS = {"rd": os.path.join(NB, "results", "ff-night-2026-11-17", "compound"),
        "ea": os.path.join(NB, "results", "ff-night-2026-11-17", "early")}
PAULI = {"I": np.eye(2, dtype=complex), "X": np.array([[0, 1], [1, 0]], dtype=complex),
         "Y": np.array([[0, -1j], [1j, 0]], dtype=complex), "Z": np.diag([1, -1]).astype(complex)}


# ------------------------------------------------------------------------------------------------ batched trajectories

class Batch:
    def __init__(self, n, nc, B, rng):
        self.n, self.B, self.rng = n, B, rng
        self.psi = np.zeros((B,) + (2,) * n, dtype=complex)
        self.psi[(slice(None),) + (0,) * n] = 1.0
        self.bits = np.zeros((B, nc), dtype=np.int8)

    def u1(self, q, U, rows=None):
        ax = 1 + q
        if rows is None:
            self.psi = np.moveaxis(np.tensordot(U, self.psi, axes=([1], [ax])), 0, ax)
        elif rows.any():
            sub = self.psi[rows]
            self.psi[rows] = np.moveaxis(np.tensordot(U, sub, axes=([1], [ax])), 0, ax)

    def cz(self, a, b, rows=None):
        sl = [slice(None)] * (1 + self.n)
        sl[1 + a], sl[1 + b] = 1, 1
        if rows is None:
            self.psi[tuple(sl)] *= -1
        else:
            idx = np.nonzero(rows)[0]
            sl[0] = idx
            self.psi[tuple(sl)] *= -1

    def p_one(self, q):
        sl = [slice(None)] * (1 + self.n)
        sl[1 + q] = 1
        a = np.abs(self.psi[tuple(sl)]) ** 2
        return a.reshape(self.B, -1).sum(1)

    def _norm(self):
        nrm = np.sqrt((np.abs(self.psi) ** 2).reshape(self.B, -1).sum(1))
        self.psi /= nrm.reshape((self.B,) + (1,) * self.n)

    def pauli1(self, q, p, rows=None):
        if p <= 0:
            return
        r = self.rng.random(self.B)
        hit = r < p
        if rows is not None:
            hit &= rows
        if not hit.any():
            return
        which = self.rng.integers(0, 3, self.B)
        for k, P in enumerate(("X", "Y", "Z")):
            self.u1(q, PAULI[P], hit & (which == k))

    def pauli2(self, a, b, p, rows=None):
        if p <= 0:
            return
        hit = self.rng.random(self.B) < p
        if rows is not None:
            hit &= rows
        if not hit.any():
            return
        pairs = [x for x in itertools.product("IXYZ", repeat=2) if x != ("I", "I")]
        which = self.rng.integers(0, 15, self.B)
        for k, (pa, pb) in enumerate(pairs):
            m = hit & (which == k)
            if m.any():
                if pa != "I":
                    self.u1(a, PAULI[pa], m)
                if pb != "I":
                    self.u1(b, PAULI[pb], m)

    def damp(self, q, g):
        if g <= 0:
            return
        p1 = self.p_one(q)
        jump = self.rng.random(self.B) < g * p1
        sl1 = [slice(None)] * (1 + self.n)
        sl0 = list(sl1)
        sl1[1 + q], sl0[1 + q] = 1, 0
        sl1, sl0 = tuple(sl1), tuple(sl0)
        new = self.psi.copy()
        # jump rows: |1> -> |0>
        j = np.nonzero(jump)[0]
        if len(j):
            a1 = self.psi[sl1][j]
            new[(j,) + sl0[1:]] = a1
            new[(j,) + sl1[1:]] = 0
        nj = np.nonzero(~jump)[0]
        if len(nj):
            new[(nj,) + sl1[1:]] = self.psi[(nj,) + sl1[1:]] * math.sqrt(1 - g)
        self.psi = new
        self._norm()

    def dephase(self, q, pz):
        if pz <= 0:
            return
        self.u1(q, PAULI["Z"], self.rng.random(self.B) < pz)

    def measure(self, q, c, e_ro):
        p1 = self.p_one(q)
        out = (self.rng.random(self.B) < p1)
        sl1 = [slice(None)] * (1 + self.n)
        sl0 = list(sl1)
        sl1[1 + q], sl0[1 + q] = 1, 0
        o = np.nonzero(out)[0]
        z = np.nonzero(~out)[0]
        if len(o):
            self.psi[(o,) + tuple(sl0[1:])] = 0
        if len(z):
            self.psi[(z,) + tuple(sl1[1:])] = 0
        self._norm()
        flip = self.rng.random(self.B) < e_ro
        self.bits[:, c] = (out ^ flip).astype(np.int8)


def run_circuit(qc, shots, lat_us, T1, noise=True, seed=0, chunk=4000):
    """Counts {bitstring: n} (clbit 0 rightmost) of one compiled circuit under the model."""
    from psf_os import feedforward as FF
    act = sorted({q for _, qs in FF.walk(qc) for q in qs})
    idx = {q: i for i, q in enumerate(act)}
    ins = LG._instructions(qc, lat_us * 1e-6, False)
    start, _ = LG._schedule(ins, qc.num_qubits, qc.num_clbits, False)
    T2 = T1
    tphi = 1 / (1 / T2 - 1 / (2 * T1))
    rng = np.random.default_rng(seed)
    counts = {}
    left = shots
    while left > 0:
        B = min(chunk, left)
        left -= B
        st = Batch(len(act), qc.num_clbits, B, rng)
        ready = {}

        def idle(q, t_to):
            if not noise:
                ready[q] = t_to
                return
            if q in ready:
                dt = t_to - ready[q]
                if dt > 1e-12:
                    st.damp(idx[q], 1 - math.exp(-dt / T1))
                    st.dephase(idx[q], (1 - math.exp(-dt / tphi)) / 2)
            ready[q] = t_to

        def gate(op, qs, rows=None):
            nm = op.name
            if nm in ("barrier", "delay", "id"):
                return
            if nm == "cz":
                st.cz(idx[qs[0]], idx[qs[1]], rows)
                if noise:
                    st.pauli2(idx[qs[0]], idx[qs[1]], P2Q, rows)
                return
            if nm in ("rz", "sx", "x"):
                st.u1(idx[qs[0]], op.to_matrix(), rows)
                if noise and nm != "rz":
                    st.pauli1(idx[qs[0]], P1Q, rows)
                return
            raise ValueError(f"no model for {nm}")

        for k, inst in enumerate(qc.data):
            qs_i, cs_i, kind, d, _, latency = ins[k]
            s = start[k]
            op = inst.operation
            qs = [qc.find_bit(q).index for q in inst.qubits]
            if kind == "barrier":
                continue
            for q in qs:
                idle(q, s)
            if kind == "measure":
                c = qc.find_bit(inst.clbits[0]).index
                st.measure(idx[qs[0]], c, E_RO if noise else 0.0)
                idle(qs[0], s + d)              # projected at the start, then idles through the measurement
                continue
            if kind == "if_else":
                cond = op.condition
                cb = cond[0]
                if type(cb).__name__ != "Clbit":
                    raise ValueError("only single-bit conditions are modelled")
                cval = int(cond[1])
                rows = st.bits[:, qc.find_bit(cb).index] == cval
                for q in qs:
                    idle(q, s + latency)         # the decision latency, waited on the conditional's qubits
                for bi, body in enumerate(op.blocks):
                    if body is None:
                        continue
                    r = rows if bi == 0 else ~rows
                    for bins in body.data:
                        bq = [qs[body.find_bit(x).index] for x in bins.qubits]
                        gate(bins.operation, bq, r)
                for q in qs:
                    ready[q] = s + d
                continue
            gate(op, qs)
            for q in qs:
                ready[q] = s + d
        for row in st.bits:
            key = "".join(str(int(b)) for b in row[::-1])
            counts[key] = counts.get(key, 0) + 1
    return counts


# ------------------------------------------------------------------------------------------------ driver

def _task(args):
    tag, k, lat, T1, shots, noise = args
    from qiskit import qpy
    circs = qpy.load(open(os.path.join(JOBS[tag], "job", "circuits.qpy"), "rb"))
    seed = 1000003 * k + int(lat * 10) + int(T1 * 1e6) + (0 if noise else 7)
    return tag, k, lat, T1, noise, run_circuit(circs[k], shots, lat, T1, noise=noise, seed=seed)


def user_pubs(tag):
    from qiskit import qpy
    circs = qpy.load(open(os.path.join(JOBS[tag], "job", "circuits.qpy"), "rb"))
    return [(k, c.name) for k, c in enumerate(circs) if c.name.startswith("ff_")]


def write_and_score(work, cells, lat, T1, noise):
    """Copies of tonight's two job folders with the simulated user cells; returns the declared T4 scorer's output."""
    tag_dirs = {}
    for tag in ("rd", "ea"):
        d = os.path.join(work, f"{tag}_lat{lat}_T1{int(T1 * 1e6)}_{'noise' if noise else 'clean'}")
        if os.path.exists(d):
            shutil.rmtree(d)
        shutil.copytree(JOBS[tag], d, ignore=shutil.ignore_patterns("*_scores.json"))
        raw = json.load(open(os.path.join(d, "job", "raw_counts.json")))
        for row in raw["rows"]:
            key = (tag, row["pub"])
            if key in cells:
                row["counts"] = cells[key]
        raw["status"] = "SIMULATED (latency_desk.py, illustrative model; user cells replaced)"
        json.dump(raw, open(os.path.join(d, "job", "raw_counts.json"), "w"))
        tag_dirs[tag] = d
    env = dict(os.environ)
    r = subprocess.run([sys.executable, os.path.join(NB, "gpu", "compound_night.py"), "score", tag_dirs["rd"]],
                       capture_output=True, text=True, env=env)
    r2 = subprocess.run([sys.executable, os.path.join(NB, "gpu", "early_night.py"), "score", tag_dirs["ea"], "--rd",
                         tag_dirs["rd"]], capture_output=True, text=True, env=env)
    if r.returncode or r2.returncode:
        raise RuntimeError(r.stderr[-2000:] + r2.stderr[-2000:])
    t2 = json.load(open(os.path.join(tag_dirs["rd"], "compound_scores.json")))
    t4 = json.load(open(os.path.join(tag_dirs["ea"], "early_scores.json")))
    return t2, t4, r.stdout, r2.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    ap.add_argument("--shots", type=int, default=16000)
    ap.add_argument("--workers", type=int, default=12)
    a = ap.parse_args()
    os.makedirs(a.work, exist_ok=True)
    pubs = {tag: user_pubs(tag) for tag in JOBS}
    tasks = [(tag, k, 0.0, T1S[0], a.shots, False) for tag in JOBS for k, _ in pubs[tag]]
    tasks += [(tag, k, lat, T1, a.shots, True) for T1 in T1S for lat in LATS for tag in JOBS for k, _ in pubs[tag]]
    res = {}
    with ProcessPoolExecutor(a.workers) as ex:
        for tag, k, lat, T1, noise, cnt in ex.map(_task, tasks):
            res.setdefault((lat, T1, noise), {})[(tag, k)] = cnt
    out = dict(model=dict(p1q=P1Q, p2q=P2Q, readout=E_RO, T1_us=[t * 1e6 for t in T1S], T2="= T1",
                          latency_us=list(LATS), shots=a.shots, schedule="ASAP as built (barriers kept), ledger lengths"),
               cells={})
    lines = []
    for (lat, T1, noise), cells in sorted(res.items(), key=lambda x: (not x[0][2] is False, x[0][1], x[0][0])):
        t2, t4, s2, s4 = write_and_score(a.work, cells, lat, T1, noise)
        key = "clean" if not noise else f"T1 {int(T1 * 1e6)} us, latency {lat} us"
        out["cells"][key] = dict(T2=t2, T4=t4)
        lines.append(f"== {key}\n-- T2 (third design) scorer:\n{s2}\n-- T4 (early chain) scorer:\n{s4}")
    json.dump(out, open(os.path.join(HERE, "latency_desk.json"), "w"), indent=1, default=str)
    open(os.path.join(HERE, "latency_desk.txt"), "w").write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
