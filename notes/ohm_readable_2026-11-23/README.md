# Ohm in a readable form: a desk design (home VS, 2026-11-23; desk, no device)

Home's instruction "オームを読める形にする机上設計". The owner asked for ways to read Ohm, not reasons against. This note
checks four leads at the desk:
- the wall-reversal bias collects in S, not in W;
- the light-cone M read at 3 cycles on both devices;
- the W order A0 > A1 > A2 held on 11-12;
- fewer CZ, more survives.

Nothing under `results/` or the declarations is written. psf-os is not changed (0.3.3 is used for the time model only).
No error number is read. Durations and the gates' presence are read; noise is not fitted to anything. This is not a
declaration draft and there is no prediction.

| file | what it holds |
|---|---|
| `arms_shallow.py`, `arms_shallow.json`, `arms_shallow.txt` | 1. exact W at t = 1..4 over the light-cone window and the half; measures to tell the arms apart; the 11-12 records beside |
| `cone.py`, `cone.json`, `cone.txt` | 2. the backward-light-cone circuits: qubits, CZ, CZ layers, noise-free check; a rough shrink guide |
| `frac.py`, `frac.json`, `frac.txt` | 3. fractional RZZ: the fake targets, the RZZ form against the CZ form |
| `design.py`, `design.json`, `design.txt` | 4. two test forms: circuits, shots, seconds by the time model |

The run took about 9 minutes on the home PC's CPU (MPS answers 185 s, cone checks 332 s, the rest seconds). The POD
and the RTX 4070 were not used.

## 1. Telling the arms apart at shallow times (exact answers; the 11-12 strings, N 40)

The t = 3 values equal the sealed answers to 7e-15.

| window | arm | W(1) | W(2) | W(3) | W(4) | slope of log W over log t (1..4) | W(4) / W(1) |
|---|---|---|---|---|---|---|---|
| light cone (2t - 1) | A0 | 0.304 | 0.295 | 0.760 | 0.842 | 0.817 | 2.77 |
| light cone | A1 | 0.304 | 0.268 | 0.679 | 0.694 | 0.689 | 2.29 |
| light cone | A2 | 0.304 | 0.300 | 0.568 | 0.583 | 0.534 | 1.92 |
| half (20) | A0 | 0.268 | 0.446 | 0.709 | 0.920 | 0.898 | 3.43 |
| half | A1 | 0.268 | 0.402 | 0.602 | 0.730 | 0.736 | 2.72 |
| half | A2 | 0.268 | 0.425 | 0.519 | 0.609 | 0.591 | 2.27 |

- At t = 1 the three arms are exactly equal: the field acts after a cycle, and one cycle does not tell the
  interactions apart. W(1) is therefore a common reference for all arms.
- At t = 2 the light-cone order is A2 > A0 > A1, not the full order.
- From t = 3 on, every measure orders A0 > A1 > A2:
  - slope gaps 0.13 and 0.16 (light cone);
  - W(4) / W(1) gaps 0.49 and 0.37;
  - W(3) gaps 0.08 and 0.11.

Beside, the 11-12 records (t = 3 and 6; device, with the exact value in brackets):

| device | window | W(3) A0 / A1 / A2 | order of W(3) | log2 W(6)/W(3) A0 / A1 / A2 | order |
|---|---|---|---|---|---|
| fez | light cone | 0.835 / 0.781 / 0.695 (0.760 / 0.679 / 0.568) | kept | 1.50 / 1.45 / 1.47 (0.86 / 0.55 / 0.39) | not kept |
| kingston | light cone | 0.854 / 0.797 / 0.693 (same) | kept | 0.99 / 0.88 / 0.83 (same) | kept |
| fez | half | 1.94 / 1.95 / 1.93 (0.71 / 0.60 / 0.52) | not kept | 0.76 / 0.63 / 0.52 (0.97 / 0.66 / 0.45) | kept |
| kingston | half | 1.38 / 1.39 / 1.30 (same) | not kept | 0.74 / 0.61 / 0.51 (same) | kept |

- On the light-cone window, the device's W(3) kept the order on both devices, with gaps of 0.05-0.10 against the exact
  0.08-0.11.
- On the half, W(3) did not keep the order: the shrink buries it.

## 2. Only the qubits the window needs (`cone.py`)

| t | window (sites) | cone qubits (positions) | CZ A0 cone / 40 | CZ A1, A2 cone / 40 | CZ layers A0 / A1, A2 (cone = 40) |
|---|---|---|---|---|---|
| 1 | 1 | 4 (18-21) | 6 / 78 | 9 / 117 | 4 / 6 |
| 2 | 3 | 10 (16-25) | 28 / 156 | 42 / 234 | 8 / 12 |
| 3 | 5 | 16 (14-29) | 66 / 234 | 99 / 351 | 12 / 18 |
| 4 | 7 | 22 (12-33) | 120 / 312 | 180 / 468 | 16 / 24 |

- Compiled by qiskit on a line (basis cz, rz, sx, x, level 2). At t = 3 the 40-qubit counts equal the 11-12 records'
  (234 / 351).
- Noise-free, on all 28 strings: the window's <Z> from the cone circuit against the 40-qubit circuit differs by at most
  1.8e-10 (A0 t = 4; otherwise below 1e-11).
- The cone keeps 28-38% of the CZ at t = 3-4 but **the same number of CZ layers**: the window sits in the middle of the
  cone, so its depth is the full depth.

Rough guide (guess, not measured; never fitted to the device). The 11-12 records' 1 - r is made proportional to the CZ
layers, a line through 0 on t = 3 and 6. In `cone.json`:
- by layers alone, the cone circuit has the same r as the 40-qubit one at the same t;
- r grows as t falls, e.g. fez A1: 0.94 / 0.87 / 0.81 / 0.74 at t = 1 / 2 / 3 / 4;
- if the shrink also scaled with the qubits measured (x n / 40), the cone would reach r of about 0.92 (fez) and 0.95
  (kingston) at t = 3, against 0.81 / 0.87.

Whether fewer qubits shrink less is not known from these records. The two points do not lie on a line through 0 (fez
A1: 0.23 at 18 layers, 0.37 at 36). A part of the shrink, about 0.1, does not grow with the layers; guess (not measured):
readout.

## 3. Fractional gates (`frac.py`)

- The fake targets (FakeFez, FakeKingston) list **no rzz and no rx**. Their instructions are cz, rz, sx, x (plus id,
  delay, measure, reset and control flow).
- fSim(pi/4, phi) in the RZZ form is equal to the gate (operator check). On a 12-qubit chain at t = 3, both compiled
  forms give the logical statevector (fidelity 1 to 1e-14).
- Two-qubit gate counts are **the same** in both forms:
  - A0: 2 RZZ against 2 CZ; A1 and A2: 3 against 3;
  - at t = 3: 234 / 351 (40 qubits) and 66 / 99 (cone), with the same layers.
- The RZZ angles are all |pi/4|, of both signs. A negative angle can be turned positive with X on one qubit, at the
  cost of one-qubit gates.
- So the RZZ form does not reduce the gate count or the layers. Any gain would be per gate, and that is not in this
  notebook. Whether the devices accept rzz and these angles has to be checked in the devices' records.

## 4. Test forms (not a declaration draft; no prediction)

Circuits as psf-os's user entrance builds them: each item with its floor and mirror, plus one ring sentinel. Seconds by
`psf_os.job.qpu_seconds`. The shot error of W on the window is a rough guide from the records' per-pair shot errors.

| plan | what | items | circuits | shots | seconds (model) | shot SE of W (rough) |
|---|---|---|---|---|---|---|
| A | light-cone circuits only, t = 1, 2, 3, 4, three arms, 7 pairs | 168 | 505 | 1000 | 157.5 | about 0.007 |
| B | t = 1 and 3, three arms, 7 pairs, each as twins in one job: light-cone circuit and 40-qubit circuit | 168 | 505 | 1000 | 157.5 | about 0.007 |

Reading table, a first sketch:

| if this reads | then this can be said |
|---|---|
| A: W(3), W(4) on the window keep A0 > A1 > A2, gaps beyond 2 SE | the arms are told apart on the device at shallow times |
| A: W(t) / W(1) against the exact ratio | the growth from the common t = 1 reference, arm by arm |
| A: the slope over t = 1..4 keeps the order | a shallow transport exponent, ordered |
| A: M on the window READS per cell (MSE at most half the mean square) | the transfer itself, cycle by cycle |
| B: the cone twin's r (or M error) smaller than the 40-qubit twin's | cutting the qubits measured lowers the shrink at equal layers |
| B: the twins equal within SE | the shrink is set by the layers, not by the qubits measured |
