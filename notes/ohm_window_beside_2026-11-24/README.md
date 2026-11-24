# Ohm on the window, read again beside: per-qubit twins, and where the bias goes (workplace Claude, 2026-11-24; desk, no device)

The owner asked for the home VS's two desk suggestions of 2026-11-23 ("作って"). This note re-reads
`results/ohm-window-night-2026-11-23` from its committed files. It writes no verdict and no declaration, and it
corrects no recorded value. It fits no noise model to the device and reads no calibration number.

## Inputs

The files of `results/ohm-window-night-2026-11-23` at notebook dd0d1393. They were read from
`notebook_ow_rec2.bundle`'s objects: the base commit 0aa31ca0 is not at the workplace, so the pack was read object by
object (`tools/packread.py`), and the folder was taken from its git tree.

| file | sha256 (first 16) | check |
|---|---|---|
| `ow/job/raw_counts.json` | 05bd8f273e975033 | |
| `ow/job/circuits.qpy.gz` (gunzipped) | d428dec065417170 | the manifest's `circuits_sha256` |
| `answers/ohm_window_answers.json` | 216d6b960c927df4 | the declared sealed answers |
| `ow/build.json` | 8127bf06a9d40f3a | |

The qubit-to-clbit map is read from each sent circuit's measure instructions, and the chain's physical qubits by
position from `build.json`, as the home VS's independent check does. Only qiskit and numpy are used (no psf-os, no
notebook scorer).

Run it with `python ow_beside.py <results>/ohm-window-night-2026-11-23 ow_beside.json`, which writes
`ow_beside.json` and prints `ow_beside.txt`. Bootstrap over the 7 pairs: 2000 draws, seed 20261124.

On the window's qubits (positions 20 .. 20 + 2t - 2), the exact <Z> of the light-cone circuit (L) and of the 40-qubit
circuit (F) agree to 7.3e-15.

## 1. Per-qubit twins (F - L on the same physical qubits)

| arm, t | points | mean of Z_F - Z_L (shot SE) | chi2 / dof against shot noise | squared error F - L (SE) | exact Z^2 mean |
|---|---|---|---|---|---|
| A0, 1 | 14 | +0.0043 (0.0116) | 0.60 | +0.00127 (0.00057) | 0.071 |
| A0, 3 | 70 | +0.0046 (0.0047) | 1.00 | +0.00004 (0.00058) | 0.272 |
| A1, 1 | 14 | +0.0099 (0.0116) | 1.17 | +0.00074 (0.00098) | 0.071 |
| A1, 3 | 70 | -0.0027 (0.0049) | 0.96 | +0.00083 (0.00056) | 0.214 |
| A2, 1 | 14 | -0.0084 (0.0116) | 0.44 | -0.00003 (0.00054) | 0.071 |
| A2, 3 | 70 | +0.0076 (0.0048) | 0.97 | +0.00000 (0.00061) | 0.252 |

- **Per qubit, the twins differ by shot noise only.** At t = 3, chi2 / dof is 0.96 to 1.00 on 70 points each, and
  the mean difference is within 2 shot SE in every cell (the largest is A2 at t = 3, 1.6 SE). This says more than the
  record's window-sum SAME: cutting the outside 24 qubits and 72 % of the CZ did not move any window qubit's <Z>
  beyond shot noise.
- A0 at t = 1: the squared error is larger in F by +0.00127 (2.2 SE), the record's KEEPS MORE seen again per qubit, on
  a small scale (exact Z^2 0.071). Not judged.
- Per qubit, the squared-error difference has an SE of about 0.0006 at t = 3, against an exact Z^2 of 0.21 to 0.27.

## 2. Where the bias goes: the odd part (W) and the even part (S)

Per pair (string s, complement c) and window qubit, split the <Z>:

- odd part O = (Z_s - Z_c) / 2;
- even part E = (Z_s + Z_c) / 2.

W depends on the odd parts only and S on the even parts only. These are identities of the definitions
(W = -sum O / 2 + const, S = -sum E + const). r is the odd part's shrink, sum O_dev O_ex / sum O_ex^2: a summary of the
data, not a noise model.

| cell | r (SE) | odd error left after r | W excess (SE) | of it, the shrink term (SE) | even shift (SE) | S excess (SE) |
|---|---|---|---|---|---|---|
| A0 t3 L | 0.891 (0.008) | 0.16 | +0.093 (0.016) | +0.082 (0.021) | -0.006 (0.002) | +0.028 (0.009) |
| A0 t3 F | 0.891 (0.005) | 0.13 | +0.083 (0.016) | +0.082 (0.019) | -0.001 (0.004) | +0.005 (0.020) |
| A1 t3 L | 0.874 (0.005) | 0.12 | +0.115 (0.023) | +0.107 (0.020) | +0.008 (0.002) | -0.040 (0.011) |
| A1 t3 F | 0.863 (0.008) | 0.13 | +0.112 (0.024) | +0.116 (0.023) | +0.005 (0.003) | -0.026 (0.017) |
| A2 t3 L | 0.870 (0.008) | 0.10 | +0.135 (0.019) | +0.127 (0.018) | +0.002 (0.004) | -0.009 (0.020) |
| A2 t3 F | 0.875 (0.008) | 0.16 | +0.135 (0.017) | +0.122 (0.019) | +0.009 (0.004) | -0.047 (0.020) |

At t = 1 (`ow_beside.txt`), r is 0.87 to 0.93. The W excess is -0.001 to -0.009 and the shrink term -0.005 to -0.010,
both within about 2 SE of 0. The window is one qubit there and the odd signal is small.

- **At t = 3 the device's W excess is, in this record, almost all a uniform shrink of the odd part of <Z>.** A single
  factor r of 0.86 to 0.89 per cell leaves 10 to 16 % of the odd part's squared error, and the shrink term alone gives
  the W excess within its SE in all six cells.
- The sign of the excess follows the exact profile, not an extra transport. Shrinking the window's odd <Z> towards 0
  raised W at t = 3 and lowered it slightly at t = 1. So the record's guess, "noise mixes spins and looks like extra
  transport", is in this record more precisely a uniform contraction whose effect on W can be read from r and the
  exact values.
- The even part is a one-sided shift, such as decay towards |0>.
  - At t = 3 it is small on the window: -0.006 to +0.009 (2 SE 0.003 to 0.008), three of six cells within 2 SE (corrected 2026-11-24: "mostly within 2 SE" before).
  - At t = 1 it reaches +0.021 (A1 F, 4 SE), seen in S as -0.021.
- **r is the same in L and F within SE** (0.891 / 0.891, 0.874 / 0.863, 0.870 / 0.875 at t = 3). The shrink follows
  the layers, not the number of qubits measured, as the record's twins read for the window sums.

## 3. Rulers for the shrink inside the job (beside)

- **The mirror** (the circuit and its inverse, ideal all |0>; A1 s00 only). The square root of its mean <Z> is 0.849
  (L) and 0.850 (F) at t = 3, against r of 0.874 and 0.863. At t = 1 it is 0.932 and 0.948, against 0.921 and 0.881.
  The mirror has twice the layers. On this one string its square root lands within 0.013 to 0.025 of r at t = 3, and
  within 0.011 and 0.067 at t = 1.
- **The conserved total <Z>.** fSim keeps the number of 1s, so the exact total equals the initial one. The odd
  combination per pair, (T_s - T_c) / (T0_s - T0_c), cancels a one-sided shift.
  - At t = 3 its pair means are 0.88 (A0), 0.83 (A1) and 0.86 (A2), with SE 0.06 to 0.08, near r on the window.
  - Per pair it scatters from 0.59 to 1.19, because the 11-12 strings are nearly balanced (initial |total| 2 to 8 of 40).

## What this suggests for a next Ohm declaration (for the owner; not a draft)

- If the shrink stays uniform, a ratio taken inside one circuit cancels it. One example is the window's odd part over
  the circuit's own total odd part, or over a mirror of the same layers. Such a ratio would read the transport without
  the W bias. It is a new quantity to declare, not a correction of W. The raw verdict words can stay as they are, with
  the ratio beside at first.
- To make the in-circuit ruler usable, the design should do one or both of these:
  - pick strings with a large |total Z|;
  - add a mirror per arm and t.
- Whether r stays uniform across positions and at t = 4 is the question a next run would answer.

## Limits

- One device-day, 7 pairs. r is a summary of the data; no noise model is fitted.
- "Uniform" is read on the window's 1 or 5 qubits only.
- The mirror was sent on one string (A1 s00), and the total ruler is poorly conditioned on these strings.
- The odd / even split assumes the complement pairing of the declared strings, which holds (`strings`).
