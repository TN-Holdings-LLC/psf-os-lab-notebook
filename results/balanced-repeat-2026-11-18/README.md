# The frame-balanced neuron chain again, 2026-11-18 on ibm_marrakesh (`prereg/balanced_repeat_2026-11-18.md`)

- Declarations pushed 11:12:46 CET (reflog "f7d1a8cc refs/remotes/origin/main@{2026-11-18 11:12:46 +0100}: update by
  push"; the declaring commit 16d14fc8). Queue read with the device record: marrakesh 1, fez 0, kingston 2 ->
  ibm_marrakesh: **a same-device repeat** of 2026-11-17. Device record fetched 11:17:03 CET (calibration **2026-11-18
  10:40 CET**, a new calibration since 2026-11-17's run, which read 2026-11-13 18:22; failed qubits 82, 94, 113, 119,
  130; coupler 113-119) (`fetch_in/`). The same physical qubits as 2026-11-17 (rule C chain from qubit 0).
- Built and submitted on the owner's machine from the declared checkout (`versions.txt`: Python 3.12.13, qiskit
  2.5.2, qiskit-aer 0.17.2, qiskit-ibm-runtime 0.49.0, numpy 2.5.3; psf-os 0f57c76). Pre-run check PASS. Rebuilt at
  home from the same record: every user, off and floor circuit byte-identical; the four ring-sentinel circuits differ
  in their compiled bytes (the sentinel's one-qubit synthesis differs between environments, as the workplace found on
  2026-11-18; the sentinel is never judged).
- Job dbunml7f8rhs73bmk5eg (created 11:17:56, finished 11:18:46 CET; 34 circuits, 40.9 s by the model, 41 s charged;
  DD and twirling off, no mitigation, 4000 shots). Sentinel DEAD (beside).

## Verdicts (`python gpu/balanced_night.py score .`)

```
L 1: rd 0.753  nf 0.465  pooled 0.609 (noiseless 0.890, -0.281)  g -0.185 (2 SE 0.010) -> NOT BEYOND
L 2: rd 0.551  nf 0.468  pooled 0.510 (noiseless 0.793, -0.283)  g -0.121 (2 SE 0.011) -> NOT BEYOND
L 3: rd 0.524  nf 0.345  pooled 0.434 (noiseless 0.706, -0.272)  g -0.067 (2 SE 0.011) -> NOT BEYOND
L 4: rd 0.466  nf 0.308  pooled 0.387 (noiseless 0.629, -0.241)  g -0.011 (2 SE 0.011) -> NOT BEYOND
L 5: rd 0.434  nf 0.245  pooled 0.340 (noiseless 0.560, -0.220)  g +0.024 (2 SE 0.010) -> BEYOND THE CORRECTION CEILING
slope of the pooled g over L +0.0528 (2 SE 0.0033) -> COMPOUNDS
```

## Against the declaration

| prediction | numbers | |
|---|---|---|
| R-1 no L overshoots | the pool 0.22-0.28 below its noiseless value at every L | held |
| R-2 BEYOND at L = 2, 3, 4, 5 | beyond only at L = 5 (g +0.024); L = 2, 3, 4 not beyond (g -0.121, -0.067, -0.011) | failed |
| R-3 COMPOUNDS | slope +0.053 per step (2 SE 0.003), no overshoot | held |

## Two numbers side by side

- Vanity: the margin over the correction ceiling grows with depth again, faster than on 2026-11-17 (+0.053 against
  +0.031 per step), and crosses the ceiling at L = 5.
- Essence: tonight the pool keeps only 0.68 / 0.64 / 0.61 / 0.62 / 0.61 of its noiseless value (2026-11-17: 0.87 /
  0.87 / 0.79 / 0.77 / 0.77). The growth of g tonight comes from the ceiling c(L) rising with L faster than the device
  loses, not from the device keeping more.

## Beside, never judged

- Against 2026-11-17 on the same device and qubits (pooled): -0.166 / -0.178 / -0.124 / -0.094 / -0.093; rd -0.149 /
  -0.193 / -0.136 / -0.114 / -0.094; nf -0.183 / -0.164 / -0.110 / -0.075 / -0.093 (2 SE about 0.02 each).
- The device was recalibrated at 10:40 CET today. The readout of qubit 1 (the L = 1 output) changed: the
  compounding OS's diagnostics 9 minutes later read P(1 | |1>) 0.967 and P(0 | |0>) 0.955 (2026-11-17: 0.826 and
  0.9995), so tonight the frame holding logical 1 as |0> (rd) is the one that loses on readout.
- Execution 38.3 s of 49.4 s from creation to finish.

## Reproduce

`python reproduce.py --psf-os PATH_TO_PSF_OS_AT_0f57c76 balanced-repeat-2026-11-18` (SAME, 2026-11-18).
