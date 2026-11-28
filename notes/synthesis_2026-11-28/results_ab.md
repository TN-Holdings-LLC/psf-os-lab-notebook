# Analyses A and B: first results (home, 2026-11-28)

Both declared in `outline.md` (423b8f3d) before they were run; run once on the committed records (main at e26595a4).
Nothing under `results/` or `prereg/` is changed.

## A. The prediction ledger, nights of 2026-11-16 to 2026-11-27 (first part)

`python notes/synthesis_2026-11-28/ledger_a.py --summary` (output `ledger_a.json`, 75 rows). Read from the
"Against the declaration" tables and bullets of every night's README (table rows whose last cell is a verdict list,
and bold bullets whose head ends in one).

- **The ledger finds 75 predictions: 54 held, 20 failed, 1 not read, the same counts as the running total in
  `results/ohm-ruler5-night-2026-11-27/README.md`.** Paper 10's nights (11-16 to 11-19): 57 (37 held, 20 failed),
  as paper 10's abstract (33 / 16 of 49, and 4 / 4 of 8). After them (11-20 to 11-27): 18 declared, 17 held, none
  failed, 1 not read (OR5-2, another device).
- By kind (the kind rules are written in `ledger_a.py`, first match wins; the ff-night rows take their declaration's
  words):

| kind | paper 10's nights: declared / held / failed | after: declared / held / failed / not read |
|---|---|---|
| beyond a bound (BEYOND, CLOSER, ABOVE, READS) | 23 / 16 / 7 | 8 / 8 / 0 / 0 |
| direction between two arms (KEEPS MORE, gain, ...) | 10 / 5 / 5 | 5 / 5 / 0 / 0 |
| null, no difference (SAME WITHIN ERROR, no overshoot, ...) | 11 / 8 / 3 | 3 / 3 / 0 / 0 |
| trend over size (COMPOUNDS, GROWS) | 6 / 5 / 1 | — |
| loop behaviour (the rule changes a stack, ...) | 3 / 1 / 2 | — |
| timing (RESOLVED, IN PARALLEL, WAIT FOR EACH OTHER) | 3 / 1 / 2 | — |
| cost (charged below a third) | 1 / 1 / 0 | — |
| per-qubit record (a named qubit low next night) | — | 2 / 1 / 0 / 1 |

- Reading. On paper 10's nights the failures sit in the kinds that ask about a mechanism the series had not yet
  measured: loop behaviour 2 of 3, timing 2 of 3, a direction between arms 5 of 10; predictions that a known effect
  passes a bound failed less often (7 of 23). After 11-19 a prediction was declared only where an earlier device
  record grounded it (paper 11), and none failed. **That is a change in what was predicted, not evidence that the
  predictions got better:** 18 grounded predictions against 57 of every kind. The ledger shows both sides; the paper
  must say this in those words.
- Beside: T4-3 (11-17) was declared although the dry run without noise said it must fail (its declaration says so);
  it failed.
- Not yet: papers 1 to 6's predictions (their declarations are in psf-zero and the notebook's earlier `prereg/`), and
  the hand label "first night of a design or a repeat" for paper 10's 57 (its rule is still to be written before the
  labels).

## B. Paper 9's line, out of sample

`python notes/synthesis_2026-11-28/yardstick_b.py --psf-os <psf-os 0.3.3>` (output `yardstick_b.json`). The results
recorded after 2026-11-16 that are judged by paper 9's reading (MSE at most half the mean square of the exact answer):
the Ohm window night (11-23) and the four ruler nights (11-24 to 11-27), raw M and raw W per cell; 48 cells, 96 units.
Each night is scored by its own declared scorer on a copy; one added line writes the vectors the scorer already holds.
Check: every unit's ratio equals the recorded M_ratio or W_ratio exactly, and every READS word is the recorded one.
(A re-run of paper 9's own `line_all.py` finds only 6 new rows, the daily record of 11-15 and 11-16, all with
r >= 0.293 and all READ; they are not after 11-16 and are set beside.)

- **Declared reading: holds.** Above the line, 94 of 96 units read (0.979), against the declared threshold 0.935
  (paper 9's 160 / 166 = 0.964 minus its binomial 2 SE). M: 47 of 48; W: 47 of 48. No unit fell below the line.
- The two that do not read are one cell, A2 t = 4 on 11-26 (ibm_fez): ratio 0.529 and 0.526, r 1.56 and 1.57, rest
  +0.22 and +0.20. As in paper 9's six, the error that is not a shrink decided.
- **What this test cannot say.** Every unit sits far above the line: r from 0.939 to 1.575. r above 1 means the raw
  values are larger than the exact ones, not smaller: all 60 units at t = 3 and 4 have r above 1 (the device's error
  adds to the window's transfer), and at t = 1, 14 of 36 do (smallest r 0.939). So the out-of-sample
  units test only the measured direction's far side ("r high, the result reads unless the shape is wrong"); they do
  not test the region near 0.293, where paper 9's misses sat. The paper must say both.
- The units are not independent: M and W of a cell come from the same circuits, and the cells of one night from one
  job.

## What follows

- A, second part: papers 1 to 6's declared predictions; then the label rule for "first night of a design or repeat".
- C: already in `notes/calib_compare_2026-11-26/`; to be summarised for the paper.
- D and E: next.

## E. The re-score census (2026-11-28)

`python reproduce.py --psf-os <psf-os 0.3.3 at e652257>` over every entry, on home's cloud workspace (Python 3.13.18,
qiskit 2.5.2, qiskit-aer 0.17.2, numpy 2.5.3), notebook at e26595a4 plus this folder: **98 of 98 SAME** (every number
equal to 1e-9 against the committed scores). Output: `reproduce_all_2026-11-28.txt`. Entries whose comments name
psf-os's feedforward branch also re-scored the same with 0.3.3. The census covers the scorers only; `--gate-hash`
(rebuilding the run2d circuits and comparing gates) was not run.
