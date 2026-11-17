# The neuron with decay during the mid-circuit waits: the three designs of 2026-11-16 and the form without mid-circuit measurements (workplace VS Claude, 2026-11-17; desk only)

**This is an illustration, not a prediction for any device.**

- The noise model is uniform and was not fitted. No calibration or error number was read.
- The decay strengths are examples. The control test of 2026-11-16 is shown beside them for comparison only.
- What to run is the owner's decision.

`rus_decay_desk.py` writes `rus_decay_desk.txt` (tables A to E) and `rus_decay_desk.json`. It needs numpy and qiskit.
Aer is not needed.

## Designs (theta 1.1; L = 1, 2, 3; m = 2, 3)

| | circuit |
|---|---|
| D1 | `rus_chain` (first design, `gpu/rus_night.py`) |
| D2 | outputs in use flipped around every ancilla measurement (`gpu/rus2_night.flip_chain`) |
| D3 | D2 with the last output read flipped and relabelled (`gpu/rus3_night.chain`) |
| coh | no mid-circuit measurement: the workplace design `zipper+` (`notes/rus_coherent_2026-11-17/coherent.zipper(..., plus=True)`), lowered to CZ and fused one-qubit gates (CZ 8 / 15 / 18 / 32 / 28 / 49, as in the workplace table) |

- **D1-D3 are modelled as compiled on 2026-11-16.** I read the job's `circuits.qpy`: the ancilla is measured m times
  on every branch, outside the conditional blocks. So every shot waits m times, even after an early success, and a
  misread 1 after a success starts a retry.
- **The off arms are the same circuits without the blocks.** The coh off arm is try 0 on the same line, defined for
  L = 1 only.

## Model (the same numbers on every element; not any device's)

- **Gates:** the same as `RUS_NOISE_DESK.md`: one-qubit 3e-4, CZ 3e-3 (0.3 %).
- **Readout:** flipped with 0.015. Table E makes the readout of |1> worse.
- **During every mid-circuit wait, on every other qubit:**
  - amplitude damping gamma (|1> to |0>), with gamma = 0, 0.02, 0.05, 0.1, 0.2 per wait;
  - a phase flip of 0.024.
- **coh has no mid-circuit wait.** During each of its CZ, the other live qubits get gamma / 40 and the phase flip / 40.
  This takes a CZ layer as 1/40 of a wait: 68 ns against 2.6 us, the illustrative durations of the workplace note. The
  wait of a dynamic circuit also includes the decision, so 1/40 is on coh's unfavourable side.
- **For comparison only, not fitted:** in the control test the |1> of q1 fell from 0.984 to 0.460 over five waits,
  and that of q3 from 0.961 to 0.720. That is about gamma 0.14 and 0.06 per wait.

## Checks

1. **Noiseless:** D1, D2, D3 and coh give the same P(last output 1) in every (L, m), to 3e-16. For L = 1 that is
   0.890 at m = 2 and 0.922 at m = 3, as on the home desk.
2. **Gate noise only:** D1's ff and off equal `rus_noise_desk.exact_arm` (a separate engine) exactly.
3. **With decay:** an independent Monte Carlo over Kraus trajectories agrees within 2.3 SE in 5 cells (D1, D2, coh).

## Two numbers per cell

The table gives, for each cell:

- **error:** ff minus the exact value (sin^2 q)^L;
- **loss:** ff minus the noiseless value of the same circuit, which is what the noise takes.

| L | m | gamma | D1 | D2 / D3 | coh |
|---|---|---|---|---|---|
| 1 | 2 | 0 | -0.069 / -0.023 | -0.070 / -0.023 | -0.069 / -0.022 |
| 1 | 2 | 0.05 | -0.143 / -0.096 | -0.064 / -0.017 | -0.070 / -0.024 |
| 1 | 2 | 0.2 | -0.344 / -0.297 | -0.047 / -0.000 | -0.075 / -0.028 |
| 1 | 3 | 0.05 | -0.153 / -0.138 | -0.041 / -0.026 | -0.052 / -0.037 |
| 2 | 2 | 0.05 | -0.247 / -0.161 | -0.096 / -0.011 | -0.116 / -0.031 |
| 2 | 2 | 0.2 | -0.536 / -0.450 | -0.042 / +0.044 | -0.126 / -0.041 |
| 3 | 2 | 0.05 | -0.318 / -0.201 | -0.111 / +0.006 | -0.151 / -0.034 |
| 3 | 2 | 0.2 | -0.618 / -0.501 | -0.015 / +0.102 | -0.165 / -0.048 |
| 3 | 3 | 0.05 | -0.343 / -0.303 | -0.052 / -0.013 | -0.107 / -0.067 |
| 3 | 3 | 0.2 | -0.689 / -0.650 | +0.035 / +0.074 | -0.132 / -0.093 |

The full grid is in `rus_decay_desk.txt`, tables A and B.

## Reading

- **D1 loses most of its value to the decay.**
  - At gamma 0.1 per wait it loses 0.17 to 0.47 against its noiseless value.
  - This matches the finding of 2026-11-16 (the value is lost while waiting), in the model.
- **D2 / D3 turn the decay into a bias toward 1.**
  - At gamma 0.05 their loss is within 0.03, against 0.10 to 0.30 for D1.
  - At large gamma and L >= 2 they overshoot their noiseless value (+0.02 to +0.10). There a logical 0 waiting as |1>
    decays into a logical 1.
  - Because the exact value is above the noiseless value of m tries at theta 1.1, this bias moves D2 / D3 toward the
    exact value. Their small "error" at large gamma is therefore not noise removed. **Error is the showy number, loss
    is the essential one.**
- **coh loses 0.02 to 0.09 and changes slowly with gamma.**
  - Without decay, coh and D1 lose about the same (0.022 / 0.023 at L = 1, m = 2; 0.058 / 0.054 at L = 3, m = 3). In
    this model the 0.3 % CZ of coh's extra gates cost about what D1's mid-circuit readout flips and phase loss cost.
  - With decay coh stays near its gamma-0 value. Only the idle share during its CZ reaches it.
- **Which design stays closest to its own noiseless value (table D):**
  - D2 / D3 at gamma 0.02 to 0.1;
  - coh where D2 / D3 overshoot (L = 3, m = 2 at gamma >= 0.1; L = 2, m = 2 at 0.2);
  - **the gaps are mostly under 2 SE of one 4000-shot job.** The model does not say that one job could tell the
    designs apart, except in a few cells.
- **CLOSER WITH CONTROL in each design's own pair (table C):** it holds in every cell, except D2 / D3 at L = 3, m = 3,
  gamma 0.2 (there the overshoot reverses it). coh's L = 1 pair keeps the largest margin as gamma grows: 4.6 to 5.0 at
  m = 2, against 2.3 to 5.0 for D2 / D3.
- **The readout of |1> (table E, gamma 0.05) explains the step from D2 to D3 at L = 1.**
  - With P(0|1) = 0.2, D2's error is -0.228 and D3's is -0.043 (L = 1, m = 2).
  - On 2026-11-16 at L = 1 the output was physical qubit 1. Its full-floor 1 + z(|1>) of 0.372 is a P(0|1) of about
    0.19. The 0.2 row was put in the grid because of that floor record; it is not fitted to the neuron results.
  - **coh reads the output as |1> and loses as D2 does (-0.233).** Reading coh's output flipped (an X before the
    final measurement, relabelled; an identity, checkable noiselessly) would remove that. This is a proposal for the
    design, not a result.

## Beside: the values of 2026-11-16 (comparison only; nothing fitted)

| L | device D1 (m = 3) | model D1, gamma 0.05 / 0.1 | device D2 | model D2, gamma 0.05 / 0.1 | device D3 (marrakesh) | model D3, gamma 0.05, P(0\|1) 0.2 at L = 1 |
|---|---|---|---|---|---|---|
| 1 | 0.599 | 0.784 / 0.684 | 0.672 | 0.873 / 0.879 | 0.883 | 0.894 |
| 2 | 0.629 | 0.611 / 0.459 | 0.734 | 0.782 / 0.802 | 0.740 | 0.782 (P(0\|1) 0.015) |
| 3 | 0.551 | 0.480 / 0.314 | 0.626 | 0.712 / 0.749 | 0.631 | 0.712 (P(0\|1) 0.015) |

- **The model is not the device.** With one gamma on every qubit (0.05 to 0.1) it is too pessimistic for D1 at L >= 2,
  and too optimistic for D2 / D3 at L >= 2.
  - The control test already shows that the decay differs per qubit (0.14 and 0.06 per wait).
  - The device has losses that are not modelled here.
- **D2 at L = 1 (0.672 against the model's 0.87) is the readout of qubit 1.** Model D2 with P(0|1) 0.2 gives 0.709.

## What this model leaves out

- **Not modelled:**
  - decay that differs per qubit;
  - the decision's own latency differing per branch;
  - measurement-induced dephasing;
  - leakage;
  - crosstalk;
  - a mid-circuit measurement error different from the final one.
- **coh's idle share (1/40) is an example.** Its CZ errors are this model's 0.3 %, and its routing is the zipper line
  as the workplace built it.
