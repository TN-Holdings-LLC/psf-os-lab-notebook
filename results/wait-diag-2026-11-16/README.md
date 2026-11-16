# Cost of mid-circuit measurements and conditionals on a neighbouring output, 2026-11-16 (ibm_marrakesh) (`prereg/wait_diag_2026-11-16.md`)

- Declaration pushed 12:27:41 CET (reflog "587117a2 (origin/main, origin/HEAD) refs/remotes/origin/main@{2026-11-16
  12:27:41 +0100}: update by push"); queue read 12:27:55 CET: marrakesh 4, fez 130, kingston 0 -> ibm_marrakesh.
  Device record fetched 12:28:01 CET (calibration 2026-11-13 18:22 CET; failed qubits 82, 94, 113, 119, 130, coupler
  113-119) (`fetch_in/`).
- Built with `python gpu/wait_night.py build DEVDIR OUT`, psf-os feedforward-2026-11-16 at 32dc3e5 (checked on the
  owner's machine); 22 circuits, 4000 shots, 27.6 s by the model; gate hash 5247e60da043, the same as the try-build.
  Position A on chain qubits 0-1 (output physical q1), position B on chain qubits 0-5 (ancilla q4, output q5). Pre-run
  check: PASS. The job returned byte-identical to the one built.
- Job dbtei9fq0h0s73bkm4k0, submitted 12:29:42 CET, ran 12:29:44-12:30:15 CET, 26 s charged. Dynamical decoupling and
  twirling off, no mitigation. Sentinel DEAD.

## Scorer output (`python gpu/wait_night.py score OUT`, unchanged since the declaration's commit)

```
position A (output on q1): ref 0.7728; T_mid 0.5430; T_ff 0.5370; P_mid 0.6787; P_ff 0.6747
  D_meas +0.2298 (2 SE 0.0206)
  D_cond +0.0060 (2 SE 0.0223)
  D_phase_mid -0.1357 (2 SE 0.0216)
  D_phase_ff -0.1377 (2 SE 0.0216)
position B (output on q5): ref 0.9942; T_mid 0.9587; T_ff 0.9625; P_mid 0.9440; P_ff 0.9527
  D_meas +0.0355 (2 SE 0.0067)
  D_cond -0.0038 (2 SE 0.0087)
  D_phase_mid +0.0148 (2 SE 0.0096)
  D_phase_ff +0.0098 (2 SE 0.0090)
predictions: {'1 position A: D_cond >= 2 SE': 'failed', '2 ref at A below ref at B by >= 2 SE': 'held'}
reading (declared rule: the larger of D_cond and D_phase_ff): {'A': 'waits', 'B': 'phase'}
```

Every shot counted (4000 per arm, none discarded). Floor arms all zero 0.998-0.999 at A, 0.960-0.999 at B.

## Against the declaration

| prediction | numbers | |
|---|---|---|
| 1. A: D_cond >= 2 SE | +0.0060, 2 SE 0.0223 | failed |
| 2. ref at A below ref at B by >= 2 SE | 0.7728 against 0.9942 | held |

The declared reading rule gives "waits" at A and "phase" at B. Neither of the two numbers it compares is beyond 2 SE
at either position (A: D_cond +0.006, D_phase_ff -0.138; B: D_cond -0.004, D_phase_ff +0.010 at 1.1 SE), so the
rule's output rests on differences inside the noise: it names neither cause. The rule did not include D_meas, which
is the one large number of this job.

## Reading (an interpretation beside the declaration, not a judgement)

- **Conditionals that do not fire cost nothing measurable** at either position (D_cond +0.006 +- 0.022 at A,
  -0.004 +- 0.009 at B). Waiting for the decision is not what took the neuron's value.
- **Measuring the neighbouring ancilla costs the output at A a large share**: an output in |1> on q1 reads 1 in 0.773
  of the shots at once and in 0.543 after three measurements of q0 (-0.230). At B the same costs q5 -0.036. This job
  does not separate decay of q1 over the measurement time from an effect of reading q0 on q1; both are on q1 and the
  same duration.
- A superposition through the same measurements keeps more at A (0.679) than |1> (0.543), which fits decay toward |0>
  (amplitude) more than loss of phase; at B the phase cost is +0.010 to +0.015, about 1-1.5 SE.
- What this leaves for the neuron's ff loss at L = 2 and 3 (-0.22 to -0.24 against off): not the waits for unfired
  conditionals, and little phase loss on q5. Two pieces this job did not measure remain: the fired blocks (an attempt
  with CZ and controlled rotations, run in the shots that retry) and the timing of a retry's control: neuron j > 0's
  retries read neuron j-1's output again, later, after more ancilla measurements next to it; with q1 losing its |1>
  as seen here, a later retry is controlled by a decayed value. The off arm makes one attempt only, right after the
  previous neuron.
- Physical qubit 1 tonight: ref 0.773 (at once), against the whole-device floor's 1 + z(|1>) = 0.372 at 11:12 CET
  (0.814 read as 1): lower again 77 minutes later. Not used for placement.

## Files

`job/`, `runs/`, `build.json`, `wait_scores.json` (the scorer's output), `fetch_in/`.

## Reproduce

`python reproduce.py --psf-os PATH_TO_PSF_OS_AT_feedforward-2026-11-16 wait-diag-2026-11-16` (SAME, 2026-11-16).
