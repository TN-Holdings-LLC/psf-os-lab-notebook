# Declared: the time a feed-forward decision costs, read by clock qubits on a ruler of delays, night of 2026-11-18

Workplace Claude, 2026-11-18 (owner: the third missing piece, the time specification; home instruction 18d with the
owner's choices of 11:1x JST). READY text: moved to `prereg/timing_night_2026-11-18.md` and committed at home on top of
d40c8556 (after ecf9f73d; the night's other declarations, 16d14fc8, unchanged); declared when that commit is pushed, before the device
records of the night are fetched. Tool: `gpu/timing_night.py` as of that commit. Design and planted checks:
`notes/timing_2026-11-18/README.md`.

## Common

- psf-os branch feedforward-2026-11-16 at 0f57c76. The device and its record: the night's (`gpu/daily_fetch.py`, the
  first chosen in the order ibm_marrakesh, ibm_fez, ibm_kingston; the record the other jobs of the night use).
- Rule C placement (coupling graph and failed marks only); no mitigation; dynamical decoupling and twirling off; 4000
  shots per circuit; every shot counted. No device error number is read. Conditional items are not packed with other
  tests: two jobs of this test only, every item its own circuit.
- The device's dt (dt.json, read at home with the saved account: a time, not a quality number) sets the ruler's delays
  in dt and converts dt to microseconds; the same file is given to build and score.
- Each job's `check` before submission; a FAIL means that job is not run. `score` as of this commit is the verdict tool.

## What is run (two jobs)

Every item: one chain of 9 sites; two clocks (sites 0 and 8) in |+> with an echo X halfway, read at the end (ideal 0;
the loss is reading 1); actor 1 on site 2 with its partner on 3, actor 2 on 5 with its partner on 6; sites 1, 4, 7
idle. Barriers fence the two halves; per half the actors do:
- R(d): a delay on actor 1; d = 0, 4.032, 8, 16, 24, 32 us in dt (multiples of 16 dt): the ruler, in both jobs;
- C(n), n = 2, 4, 8: measure actor 1, then a conditional X on it that never fires (IBM's fast-path shape);
- F(n), n = 4, 8: the same with the conditional firing (the actor prepared |1>);
- D(n), n = 2, 4: C(n) on both actors at once (fast-path shape);
- K(n), n = 2, 4, 8: measure actor 1, then a conditional CZ between it and its partner, never firing (not fast path);
- DK(n), n = 2, 4: K(n) on both pairs at once.
Job A: R, C, F, D (43 circuits, 51.0 s by the model). Job B: R, K, DK (37 circuits, 44.3 s). ff, off (the
measurements alone) and floor arms; one ring sentinel per job. `check` also requires every conditional of C, F, D in
the fast-path shape and none of K, DK (notes/packing_2026-11-17/fastpath.py's three conditions).

## What is read (`score OUT_A OUT_B --dt-file dt.json`)

Per job, each clock's ruler (made non-decreasing, read piecewise linearly on tau = -ln(1 - 2 (loss - loss0))) turns
an item's loss into an equivalent wait; the two clocks are averaged with inverse-variance weights; per step, weighted
least squares against the number of steps: s_M (job A, the off arms of C), s_C, s_F, s_D (job A); s_K, s_DK (job B).

## Verdicts (every threshold 2 SE)

- Fast-path decision latency, s_C - s_M: **DECISION LATENCY RESOLVED** when >= 2 SE; otherwise **NOT RESOLVED**.
- Two fast-path actors, the ratio s_D / s_C; two actors with a CZ, the ratio s_DK / s_K: **DECISIONS WAIT FOR EACH
  OTHER** when ratio - 1 >= 2 SE; **IN PARALLEL** when |ratio - 1| < 2 SE and ratio - 2 <= -2 SE; otherwise **NOT
  SHOWN**. The SE of a ratio by the delta method with the two slopes taken as independent.
- Beside, never judged: s_K - s_M (job B, the CZ path's latency), s_K - s_C (two jobs), s_F - s_C, s_M itself, each
  clock's ruler, the jobs' execution times from the runtime's metrics.

## Predictions (written before the data)

1. T-1 The fast-path decision latency (s_C - s_M) is DECISION LATENCY RESOLVED.
2. T-2 Two fast-path actors (s_D / s_C) are IN PARALLEL (as IBM's documentation describes the fast path).
3. T-3 Two actors with a CZ (s_DK / s_K) are DECISIONS WAIT FOR EACH OTHER (the hypothesis from the packing loss of
   2026-11-17).

Each prediction holds or fails as a whole; a failed one is reported as failed. Basis: the planted checks (synthetic
counts, six seeds per scenario; and the real circuits of both jobs under a planted dephasing): with the CZ actors
planted to wait for each other every seed reads IN PARALLEL / WAIT FOR EACH OTHER; with the fast-path actors planted to
wait, the reverse; the planted latency 0.9 us read back +0.99 (2 SE 0.47). With a clock decay time of 100 us the
latency's 2 SE is about 0.5 us; a slower decay gives a larger SE, so T-1 can fail by NOT RESOLVED without the latency
being zero.

## Reproduce

`python gpu/timing_night.py score OUT_A OUT_B --dt-file dt.json` from the recorded jobs gives the same
`timing_scores.json`; `build` with the recorded device record, part and dt file gives the same circuits.
