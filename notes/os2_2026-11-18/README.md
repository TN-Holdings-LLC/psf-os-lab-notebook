# The prescription loop with compounding: design, desk trial, dry run (workplace Claude, 2026-11-18; desk only, not declared)

Home handover 2026-11-17 night, section 3 ("the OS has no compounding yet"). Tool: `gpu/os2_night.py`; declaration
draft: `prereg/drafts-2026-11-18/os2_DRAFT.md`; the queue / timing record draft: `QUEUE_RECORD_DRAFT.md` and
`gpu/job_timing.py`. psf-os unchanged (feedforward-2026-11-16 at 0f57c76: the placement from outside, `chains=`, is
used for +Q).

## Simple interest and compound interest in the loop

gpu/os_night.py (2026-11-17) diagnoses once, picks once per L from a fixed list, runs one main job, and its result is
used for nothing after. os2_night.py keeps that as round 1 and adds:
- **rounds within a night**: round k's own scores (verdict, overshoot flag, the two frames' shares, P0, the readout
  gap Dr from a probe in the same job) are the input of the rule for round k + 1;
- **stacked prescriptions**: base (P0 / P1 / P2 / P3), then +B (frame balance), then +Q (output on the qubit with the
  smallest readout gap, by shifting the item along the same rule-C chain by 0, 2 or 4); added only in that order,
  removed only from the end;
- **a stop-loss and a stop rule**: NOT SHOWN twice with the same stack removes the last layer; the night stops at a
  fixed point (no change, no overshoot, no first NOT SHOWN), at K_MAX rounds, at the budget, or at a FAIL / refusal;
- **the OS's own compounding**: G_k (mean g over the L credited in every round) and its slope over k.
The rule reads no calibration number; Dr comes from the job's own probe (X on chain positions 1, 3, 5, 7, 9, read at
once; P(0|0) from the probe's floor arm).

## The desk trial on 2026-11-17's records (`trial.txt`, `trial.json`)

| | L = 1 | L = 2 | L = 3 |
|---|---|---|---|
| round 1 (loop main job, P2) | P 0.9025 > noiseless 0.8915: OVERSHOOT | g +0.043 HELPS | g +0.079 HELPS |
| rule -> round 2 | R1: P2 + B | keep P2 | keep P2 |
| round 2 'as if' (frame-balanced job; P0 from round 1, another job) | pool 0.775, g +0.057 HELPS; rd share 1.013, nf 0.727 | rd2 0.744, g +0.049 HELPS | rd3 0.661, g +0.083 HELPS |
| rule -> round 3 | R2: P2 + B + Q4 (nf's output on qubit 1, Dr gap +0.174; offset 4 puts it on qubit 5, gap +0.0055) | keep | keep |

- The balanced job holds exactly the circuits the rule picks for round 2, but no P0; its g uses round 1's P0 an hour
  earlier (flagged; not a verdict).
- The fifth round (packing) adds the constraint "conditional items are not packed"; its single job is another
  observation of P2 at L = 1 (0.852, below its noiseless 0.890: no overshoot that time): the overshoot at L = 1 is not
  stable from round to round, which is a reason to let R1 act on the round's own data and not on a standing rule.
- OS compounding over L = 2, 3 (credited in both rounds): G +0.061 -> +0.066, a difference +0.005 (2 SE 0.021): not
  shown. Expected: their stacks did not change, so round 2 repeats round 1. G can grow only where the rule changes a
  stack, so a declared OS-compounding test needs nights where it does (L = 1 here: OVERSHOOT -> credited HELPS +0.057
  is a change of verdict, not a slope).

## Dry run (11-17 marrakesh record, noiseless, Clifford sentinel)

- The loop from the recorded rule.json: round 1 P2 everywhere, check PASS, 25 circuits 30.9 s; noiselessly P0 (m = 3)
  is closer to the exact value than P2 (m = 2), so g < 0: NOT SHOWN at every L; round 2 the same (not a fixed point
  yet: a first NOT SHOWN); R3 -> P0 at every L; round 3 (16 circuits, 20.9 s) NO PRESCRIPTION; fixed point, stop. The
  tool runs the loop end to end and steps back where the prescription costs more than it saves.
- The +B and +Q paths (a forced rule, dry only: L 1 P2 + B + Q4, L 2 P2 + B, L 3 P1): 31 circuits, 37.6 s, check PASS;
  L 1's frames read their output on qubit 5 (offset 4), the pool equals its noiseless value (0.8925 against 0.8904).
- The rule on hand-made round scores: R1, R2 (offset by the smallest Dr gap: L 2 -> Q2, output on qubit 5), R3 and the
  budget stop each fire as written.

## Open points

- +Q shifts an item along one rule-C chain and needs rule C's chain for n + o sites to start as the probe's chain
  (true on this record for 2 .. 14 sites; the build refuses otherwise).
- The probe reads five qubits at once after X on each; a single-qubit probe per candidate would separate readout
  crosstalk, at more circuits.
- R2 compares the frames' shares of their noiseless value; on 2026-11-17 the gap is large (0.29). With a small gap R2
  does not fire and +B stays; whether +B is worth its double cost when it does not overshoot is not in the rule.
- Within a night the device record is fixed and the device may drift; P0 is rerun in every round so g sees the drift
  on both sides.

## 2026-11-18, later: the night to run (`RUN.md`)

The draft above became the declared-to-be tools: `gpu/os2_night.py` with the owner's values (2 SE, K_MAX 4, 240 s with
the diagnostics, the last round primary, nothing from earlier nights), `gpu/os2_run.py` (preflight / go / resume /
verify), and the READY declaration text with two predictions (OS2-1, OS2-2; the OS's own compounding beside as
numbers). The dry runs, the stops and the tests: `RUN.md`. `prereg/drafts-2026-11-18/os2_DRAFT.md` is superseded by
`os2_night_2026-11-18_READY.md`.
