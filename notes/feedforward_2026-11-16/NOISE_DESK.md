# Feed-forward under an illustrative noise model: how the margin above 0.75 falls with k (workplace VS Claude, 2026-11-16; desk only)

**This is an illustration, not a prediction for any device.** The noise model is uniform and was chosen before
looking at any device. It is not fitted, and no calibration number was read. It shows the shape of the trade-off:
how the margin falls with k and with the wait during a mid-circuit measurement. The k to run is the owner's
decision.

`noise_desk.py` writes `noise_desk.txt` and `noise_desk.json`. It needs numpy only; Aer is not needed.

## Model

Every element gets the same numbers:

- **One-qubit gates:** depolarising 3e-4 after every one-qubit gate, the conditional X included.
- **CZ:** two-qubit depolarising 3e-3 after every CZ.
- **Readout:** the recorded bit is flipped with probability 0.015, at every mid-circuit measurement and at the final
  measurement. A flipped mid-circuit bit applies the wrong correction.
- **Wait:** while qubit i is measured and the condition is decided, qubit i+1 waits and loses phase. This is a phase
  flip with pz = (1 - exp(-w)) / 2, for w = wait / T2 = 0, 0.01, 0.03, 0.05, 0.1, 0.2. For example, w = 0.05 is a 5 us
  wait against T2 = 100 us; both numbers are examples, not a device's.

## Method

- **Exact, no shots.** After its measurement a qubit is never used again, so only two qubits are alive at any time.
  Each hop is applied exactly as a channel on a 2 x 2-qubit density matrix.
- **Check 1:** without noise, ff is 1 for every k, and off is 0.75 at k = 1 and 0.5 at k >= 2. This is ff_desk.py's
  Aer result, here exact.
- **Check 2:** an independent Monte Carlo over Pauli-error trajectories on the full (k + 1)-qubit state, at
  k = 1, 2, 3, both arms, 50000 shots each. It agrees within 1.8 SE in every case.

## Result

The margin is (p - 0.75) / (2 SE), with the 2 SE of a 4000-shot job. The full table, with the off arm, is in
noise_desk.txt.

| k | w = 0 | w = 0.01 | w = 0.03 | w = 0.05 | w = 0.1 | w = 0.2 |
|---|---|---|---|---|---|---|
| 1 | 0.975 / 45 | 0.970 / 41 | 0.961 / 34 | 0.952 / 30 | 0.930 / 22 | 0.889 / 14 |
| 2 | 0.959 / 33 | 0.952 / 30 | 0.939 / 25 | 0.926 / 21 | 0.896 / 15 | 0.842 / 8 |
| 4 | 0.934 / 24 | 0.922 / 20 | 0.898 / 15 | 0.875 / 12 | 0.824 / 6 | 0.745 / -0.4 |
| 8 | 0.890 / 14 | 0.868 / 11 | 0.828 / 6.5 | 0.792 / 3.3 | 0.721 / -2.0 | 0.630 / -7.9 |
| 16 | 0.816 / 5.3 | 0.781 / 2.4 | 0.725 / -1.8 | 0.681 / -4.7 | 0.608 / -9.2 | 0.541 / -13 |
| 32 | 0.709 / -2.9 | 0.668 / -5.5 | 0.611 / -9.0 | 0.574 / -11 | 0.529 / -14 | 0.505 / -16 |

**Largest k in the list (1, 2, 3, 4, 6, 8, 12, 16, 24, 32) whose margin is at least 3 / 5 / 10 times 2 SE:**

| w | margin >= 3 | margin >= 5 | margin >= 10 |
|---|---|---|---|
| 0 | 16 | 16 | 8 |
| 0.01 | 12 | 12 | 8 |
| 0.03 | 8 | 8 | 6 |
| 0.05 | 8 | 6 | 4 |
| 0.1 | 4 | 4 | 2 |
| 0.2 | 2 | 2 | 1 |

## Reading

- **The wait matters most at large k.** In this model each hop costs mostly readout (a wrong correction) plus the
  phase lost while waiting.
- **Small k has a wide margin under every wait in the table.** k = 1 or 2 stays at least 8 times 2 SE above 0.75,
  even at w = 0.2.
- **k = 4 keeps a margin of 5 times 2 SE up to w = 0.1** and loses it at w = 0.2. k = 8 keeps it only up to
  w = 0.03 (3.3 times at w = 0.05).
- **The off arm stays at its ideal under this noise:** 0.70-0.74 at k = 1 and 0.500 at k >= 2. So the arm's spread
  between ff and off is large wherever ff is above 0.75.

## What this model leaves out

- **Not modelled:**
  - amplitude damping (T1) during the wait;
  - a mid-circuit measurement error different from the final readout's;
  - measurement-induced dephasing of neighbours;
  - leakage;
  - a conditional gate whose timing depends on the branch.
- **On a device the wait itself is not known before the run.** A dynamic circuit's latency is set by IBM's control
  system.
- **The table can only say which k keep a margin if the wait is this small.** It cannot say what the device will
  give.
