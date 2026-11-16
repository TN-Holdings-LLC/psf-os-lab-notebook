# Repeat-until-success neuron chain, 2026-11-16 (ibm_marrakesh) (`prereg/rus_neuron_2026-11-16.md`)

- Declaration pushed 11:37:48 CET (reflog "7e01a11a (origin/main, origin/HEAD) refs/remotes/origin/main@{2026-11-16
  11:37:48 +0100}: update by push"); queue read 11:38:06 CET: marrakesh 1, fez 131, kingston 0 -> ibm_marrakesh (the
  first qualifying device in the declared order). Device record fetched 11:38:10 CET (calibration 2026-11-13 18:22
  CET; failed qubits 82, 94, 113, 119, 130, coupler 113-119) (`fetch_in/`).
- Built with `python gpu/rus_night.py build DEVDIR OUT` (no dry-run flag), psf-os branch feedforward-2026-11-16 at
  32dc3e5 (checked on the owner's machine before submission); 13 circuits, 4000 shots, 17.5 s by the model; gate hash
  e2f12c8ac138, the same as the try-build on the 11:07 record. Chains on qubits 0-1 (L 1), 0-3 (L 2), 0-5 (L 3).
  Pre-run check `python gpu/rus_night.py check OUT`: PASS (ff 0.918 / 0.850 / 0.790, off 0.792 / 0.628 / 0.512, floor
  1.000). The job returned byte-identical to the one built.
- Job dbtdra3eq3sc73evmjng, submitted 11:40:40 CET, ran 11:40:43-11:41:04 CET, 17 s charged. Dynamical decoupling and
  twirling off, no mitigation.

## Scorer output (`python gpu/rus_night.py score OUT`, unchanged since the declaration's commit)

```
rus1: exact 0.9371; ff 0.5992 (still failed after 3 0.0375); off 0.5982; d 0.0010 (2 SE_d 0.0219) -> NOT CLOSER; post 0.6738 (kept 0.6905, discarded 1238); floor all zero 0.9962; sentinel DEAD
rus2: exact 0.8782; ff 0.6290 (still failed after 3 0.0625); off 0.6150; d 0.0140 (2 SE_d 0.0217) -> NOT CLOSER; post 0.8385 (kept 0.4457, discarded 2217); floor all zero 0.9765; sentinel DEAD
rus3: exact 0.8230; ff 0.5510 (still failed after 3 0.0783); off 0.5085; d 0.0425 (2 SE_d 0.0223) -> CLOSER WITH CONTROL; post 0.6659 (kept 0.3307, discarded 2677); floor all zero 0.9497; sentinel DEAD
```

Every shot of ff and off counted (4000 each); post is beside and discards shots.

## Against the declaration

| prediction | numbers | |
|---|---|---|
| 1. L = 1 CLOSER WITH CONTROL | d 0.0010, 2 SE_d 0.0219 | failed |
| 2. L = 2 CLOSER WITH CONTROL | d 0.0140, 2 SE_d 0.0217 | failed |
| 3. L = 3 CLOSER WITH CONTROL | d 0.0425, 2 SE_d 0.0223 | held |

Two numbers side by side: the verdict holds at L = 3 (d = 3.8 SE_d), while the ff arm there gives 0.551 against the
exact 0.823 (-0.272, 35 SE of the ff share), further from the exact value than the noiseless 3-try gap (-0.03) by
far. On this night no arm reproduces the neuron's value.

## Beside, never judged

Device against noiseless (noiseless: the pre-run check's Aer of the same compiled circuits, 4000 shots):

| L | ff device / noiseless | off device / noiseless | post device / noiseless (dry run) |
|---|---|---|---|
| 1 | 0.599 / 0.918 | 0.598 / 0.792 | 0.674 / 0.942 |
| 2 | 0.629 / 0.850 | 0.615 / 0.628 | 0.839 / 0.838 |
| 3 | 0.551 / 0.790 | 0.509 / 0.512 | 0.666 / 0.752 |

Neuron 0's try bits (`branch.py`, `branch.json`), L = 1, P(out 1) per pattern (first..last try; noiseless: 0.937
after a success, 0.5 when every try failed):

| arm | 000 | 100 | 110 | 111 |
|---|---|---|---|---|
| ff | 0.607 (n 2741) | 0.600 (n 855) | 0.665 (n 251) | 0.333 (n 150) |
| off | 0.674 (n 2755) | 0.347 (n 49) | 0.354 (n 48) | 0.436 (n 1141) |

## Reading (an interpretation beside the verdict, not a judgement)

- The control fires as the circuit says: neuron 0's tries in the ff arm at L = 1 end in 000 / 100 / 110 / 111 for
  0.685 / 0.214 / 0.063 / 0.038 of the shots (noiseless 0.673 / 0.220 / 0.072 / 0.034), and repeated measurements of
  an untouched ancilla in the off arm agree (000 or 111 in 97 % of the shots).
- What fails is the output's value. At L = 1 the output is physical qubit 1. Its whole-device floor 1 + z(|1>) on
  nights 1-4 (11-13 to 11-16): 0.051, 0.080, 0.249, 0.372, so tonight about 19 % of |1> read as 0 at 11:12 CET.
  Readout alone would take 0.937 to about 0.76; the off arm's success branch gives 0.674 and the ff arm's 0.607, so
  readout explains part of the loss at L = 1, not all. Every chain starts on qubits 0 and 1 (rule C), so qubit 1 is
  neuron 0's output at every L. Placement reads no error numbers by the declaration; the floor record was not used.
- At L = 2 and 3, where the output is qubit 3 or 5, the off arm sits at its noiseless value (0.615 / 0.628,
  0.509 / 0.512) and so does post at L = 2 (0.839 / 0.838), while the ff arm falls by 0.22 and 0.24. The loss is
  specific to the arm with real-time control: the waits for the conditional decisions and the undo RY(pi/2), which
  needs the output's phase. This record does not separate the two.
- The workplace's noise illustration (`RUS_NOISE_DESK.md`) put d near 7-11 SE_d; it leaves out T1 during the wait and
  the conditional timing, which this night points to.

## Files

`job/` (circuits.qpy, manifest.json, raw_counts.json, submission.json), `runs/`, `build.json`, `rus_scores.json` (the
scorer's output), `fetch_in/` (queue and device records), `branch.py` / `branch.json` (beside).

## Reproduce

`python reproduce.py --psf-os PATH_TO_PSF_OS_AT_feedforward-2026-11-16 rus-neuron-2026-11-16` (SAME, 2026-11-16).
