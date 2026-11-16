# Does a control keep its |1> until a late use? 2026-11-16 (ibm_marrakesh) (`prereg/ctrl_diag_2026-11-16.md`)

- Declaration pushed 12:38:03 CET (reflog "97d507b4 (origin/main, origin/HEAD) refs/remotes/origin/main@{2026-11-16
  12:38:03 +0100}: update by push"); queue read 12:38:19 CET: marrakesh 1, fez 130, kingston 14 -> ibm_marrakesh only.
  Device record fetched 12:38:25 CET (calibration 2026-11-13 18:22 CET; failed qubits 82, 94, 113, 119, 130, coupler
  113-119) (`fetch_in/`).
- Built with `python gpu/ctrl_night.py build DEVDIR OUT` (the tool unchanged since 97d507b4), psf-os
  feedforward-2026-11-16 at 32dc3e5 (checked on the owner's machine); chain on physical qubits 0-5; 22 circuits, 4000
  shots, 27.6 s by the model; gate hash 5b5d82002a99, the same as the try-build. Pre-run check: PASS. The job returned
  byte-identical to the one built.
- Job dbten1hvvpic738mss1g, submitted 12:39:51 CET, ran 12:39:52-12:41:05 CET, 26 s charged. Dynamical decoupling and
  twirling off, no mitigation. Sentinel DEAD.

## Scorer output (`python gpu/ctrl_night.py score OUT`)

```
position A (control chain qubit 1):
  now         target 1 0.9840 (2 SE 0.0040)  control 1 0.7830
  now_repeat  target 1 0.9872 (2 SE 0.0035)  control 1 0.7610
  far         target 1 0.4595 (2 SE 0.0158)  control 1 0.3493
  far_repeat  target 1 0.4500 (2 SE 0.0157)  control 1 0.3513
  nb          target 1 0.4490 (2 SE 0.0157)  control 1 0.3420
  nb_repeat   target 1 0.4462 (2 SE 0.0157)  control 1 0.3533
  D_late_far +0.5245 (2 SE 0.0163)
  D_late_nb +0.5350 (2 SE 0.0162)
  D_nb_beyond_time +0.0105 (2 SE 0.0223)
position B (control chain qubit 3):
  now         target 1 0.9613 (2 SE 0.0061)  control 1 0.9865
  now_repeat  target 1 0.9615 (2 SE 0.0061)  control 1 0.9888
  far         target 1 0.7198 (2 SE 0.0142)  control 1 0.7328
  far_repeat  target 1 0.7270 (2 SE 0.0141)  control 1 0.7350
  nb          target 1 0.7183 (2 SE 0.0142)  control 1 0.7302
  nb_repeat   target 1 0.7153 (2 SE 0.0143)  control 1 0.7285
  D_late_far +0.2415 (2 SE 0.0155)
  D_late_nb +0.2430 (2 SE 0.0155)
  D_nb_beyond_time +0.0015 (2 SE 0.0201)
predictions: {'1 position A: D_late_nb >= 2 SE': 'held'}
reading (declared rule): {'A': 'time', 'B': 'time'}
floor all zero: {'Afar': 0.9875, 'Anb': 0.984, 'Anow': 0.992, 'Bfar': 0.9755, 'Bnb': 0.9377, 'Bnow': 0.9735} sentinel DEAD
```

## Against the declaration

| prediction | numbers | |
|---|---|---|
| 1. A: D_late_nb positive and >= 2 SE | +0.535, 2 SE 0.016 | held |

Reading rule: "time" at A and at B (D_nb_beyond_time +0.011 and +0.002, inside 2 SE; D_late_far +0.525 and +0.242).

## Reading (an interpretation beside the declaration, not a judgement)

- **The loss is time.** A |1> held on physical qubit 1 through the wait of five mid-circuit measurements is used as a
  control with value 0.46 (0.98 at once); on qubit 3, 0.72 (0.96 at once). Measuring the neighbours instead of a far
  qubit, at the same count, adds nothing beyond 2 SE at either position. The repeats agree with the first arms within
  2 SE in every case.
- Qubit 1 has two separate faults tonight: its readout (control read 1 in 0.78 of the shots where the target, read
  through qubit 2, sees 0.98) and its loss of |1> during waits. The target route removes the first.
- For the neuron: every retry adds measurement waits, during which earlier outputs (later used as controls) and the
  current output lose |1>. The off arm makes one attempt per neuron and moves on, so it waits less. This is consistent
  with ff falling below off at L = 2 and 3 and with the wait diagnostic (conditionals themselves free, neighbour
  measurements costly on qubit 1). The loss is toward |0> (amplitude), which dynamical decoupling does not undo.
- Design consequences to weigh (owner's decision, not tested here): fewer waits (m = 2; measure the ancilla fewer
  times), and holding a value whose likely outcome is 1 in the ground state during waits (X before the wait, X before
  its use), so that decay moves the unlikely value instead.

## Files

`job/`, `runs/`, `build.json`, `ctrl_scores.json` (the scorer's output), `fetch_in/`.

## Reproduce

`python reproduce.py --psf-os PATH_TO_PSF_OS_AT_feedforward-2026-11-16 ctrl-diag-2026-11-16` (SAME, 2026-11-16).
