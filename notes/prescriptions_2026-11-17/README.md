# A fixed list of prescriptions with their diagnostics (draft, workplace, 2026-11-17; not declared)

Handover of 2026-11-16 night, item 3 ("the seed of an AI OS"). The fixes found on 2026-11-16 for the feed-forward
neuron, written as a finite list fixed by a declaration, each paired with a short diagnostic and a rule that picks it.
The OS runs, each night: diagnose -> pick by the rule -> run the main job once. Same shape as the self-repair chain of
2026-11-04 (no search: a fixed list, a fixed order, a fixed rule; the data only choose among declared entries).

## 1. The list (fixed; a new entry is a new declaration)

| id | prescription | what it changes | evidence of 11-16 (marrakesh unless said) |
|---|---|---|---|
| P0 | none | the circuit as written (first design, m = 3) | ff 0.599 / 0.629 / 0.551 against exact 0.937 / 0.878 / 0.823 |
| P1 | hold flipped while waiting | an output in use is flipped (X) around every ancilla measurement, so its likely 1 waits as \|0> | second design: ff +0.113 / +0.179 / +0.182 toward exact |
| P2 | read flipped | P1, and the last output is read without the flip back, its bit relabelled 1 - bit (a fixed map of one bit) | third design: L 1 gain +0.217 (2 SE 0.018); L 2, 3 no change |
| P3 | fewer tries | m = 2 instead of 3 (fewer waits; the noiseless gap grows: 0.892 against 0.922 at L 1) | part of the second design's gain (not separated) |
| P4 | no barrier pairs | P1 without the barriers that keep each X pair (the compiler may cancel the pair) | the barriers cost (home's note); not measured alone |
| P5 | coherent tries | no mid-circuit measurement (notes/rus_coherent_2026-11-17, zipper+) | not run; noiselessly equal to the measured form |

Each entry is a circuit transformation with an exact noiseless identity (checked before the night: the transformed
circuit's distribution, after its declared relabelling, equals the original's to 1e-12). An entry whose identity
fails is not run.

## 2. The diagnostics (short jobs, the shapes of 11-16)

| id | diagnostic | measures | job (model) |
|---|---|---|---|
| Dw | wait (as `prereg/wait_diag_2026-11-16.md`) | a \|1> on the output's qubit read at once and after k ancilla measurements; unfired conditionals | 22 circuits, 27.6 s |
| Dc | control (as `prereg/ctrl_diag_2026-11-16.md`) | a \|1> used as a control at once and after the wait, read through a neighbour; neighbour reads against far reads | 22 circuits, 27.6 s |
| Dr | readout of the output qubit | \|0> and \|1> read at once on the qubit that will hold the last output (from the night's whole-device floor, no extra job) | 0 s (the floor job) |

## 3. The rule (fixed order, first match wins; thresholds in SE of the diagnostic itself)

1. If Dc shows a late-use loss D_late >= 2 SE at the position of any output used as a control: take P1.
2. If additionally Dr shows the last output's qubit reads \|1> as 1 below its \|0> as 0 by >= 2 SE: take P2 (implies P1).
3. If Dw shows unfired conditionals cost D_cond >= 2 SE: take P3 (fewer conditionals).
4. If neither 1 nor 3 holds: P0.
P4 and P5 are not chosen by the rule until each has its own declared test (P5's first test is drafted in
notes/rus_coherent_2026-11-17).
The rule reads only the night's own diagnostics (no calibration number, no earlier night), and its output is written
before the main job is built.

## 4. Chance hits (how many tries, where the line goes)

- At most 3-5 jobs a night: the diagnostics (Dw, Dc: 2), the main job (1), optionally a repeat of the main job (1).
- The main verdict is the declared one (e.g. CLOSER WITH CONTROL at 2 SE) on the main job only. The diagnostics choose,
  they never judge.
- The rule chooses among at most 4 entries; if the night's verdict were taken as "the best of the entries", the line
  would need a correction for 4 looks (2 SE -> about 2.5 SE, Bonferroni at 5 % two-sided over 4). It is not taken so:
  only the chosen entry runs as the main job, so one look, and the 2 SE line stands. A night that runs two entries
  (e.g. a repeat with another prescription) uses 2.5 SE for either.
- Across nights: a prescription is kept in the list only by a declaration; three nights in a row where the rule picks
  it and the main job does not improve on P0's last value by 2 SE retire it (a new declaration).

## 5. Two operations a night

1. **Declarations pushed together (VPN ON)**: the night file naming the diagnostics, the rule (this file's section 3,
   unchanged), the list of entries with their noiseless identities, and the main job's verdict.
2. **Device runs together (VPN OFF)**: fetch the record, run Dw and Dc (one batch), score them, apply the rule (a
   script; its output and the chosen entry written to the results folder before the main job is built), build and
   check the chosen main job, submit, collect, score. The job files and the rule's output are committed afterwards
   and pushed at the next VPN ON.

Only the main job's ids, the rule's output and the verdict leave the night; nothing is re-chosen after the main job's
data.

## Not yet

The rule's thresholds are proposals. Whether P5 belongs in the list waits for its first test. The diagnostics cost
about 55 s of device time a night; Dr is free (the floor job).
