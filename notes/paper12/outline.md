# Paper 12: outline (workplace, 2026-11-27; an outline, not a draft text)

Author TN Holdings (only). It follows paper 11 (doi:10.5281/zenodo.24496368) and covers the Ohm window night
(2026-11-23, ibm_kingston) and the four Ohm ruler nights (2026-11-24 to 11-26, ibm_fez), plus the fifth ruler night
when home runs it (`[NIGHT 5]` marks every place it enters). Every result was declared in git before its device record
was fetched; every shot counted; no mitigation, no post-selection. Calibration numbers enter no verdict, placement or
correction: the comparison with IBM's calibration is beside, made after a memo fixed before any number was read.

## Working titles (paper 11's form: a short head, a colon, what the paper finds)

1. Rulers Inside the Circuit: What Raw Quantum Dynamics Carries, and What It Leaves, on IBM Heron
2. Reading a Quantum Window Without Correction: Declared Rulers Inside the Job, Night by Night, on IBM Heron
3. What a Mirror Cannot See: Declared In-Circuit Rulers, a Readout Half Put Back, and a Residual Shrink on IBM Heron

## The claim, and its scope

- A raw result that reads (paper 9's rule) still sits away from the exact value; this paper asks whether a ruler
  carried inside the same job can say by how much, without correcting anything. Five candidate rulers were declared and
  judged night by night; their words, not their corrections, are the result.
- Found (each on declared nights): the circuit's total (a) does not carry the window's shrink; a mirror of the
  compiled circuit (b, c) carries part of it; a string mirror's odd part (d) carries more; the readout's half that a
  mirror leaves is put back by a readout pair in the same job ((de)), whose |d| was below (d)'s in all six cells on
  11-26. A positive shrink at t = 3 stays that no ruler carries (three nights), and a fixed-direction gate error does
  not explain it in dry runs. A per-qubit record from the rulers predicted the next night (OR4-2) and points at qubits
  that IBM's calibration map does not mark (fez 104).
- Not claimed: a correction of any result; that the rulers hold on another device, placement, circuit family or size;
  any quantum advantage (every answer is computed exactly on a classical machine).

## 1. Introduction (what is asked, why it matters)

- Raw dynamics on IBM Heron reads at moderate depth (papers 7 to 9) but its distance from the exact answer is not
  known from the result alone; mitigation corrects it with models, and a calibration map describes the device, not the
  job. Question: can rulers made of the job's own circuits say how far a raw window can be trusted?
  (src: notes/paper9/paper9.tex abstract; notes/paper11/paper11.tex section 1)
- The setting: the 11-12 Ohm circuits (a 40-qubit chain, a conserved transfer W across a window, light-cone circuits),
  read raw on 11-23 (window READS in all 24 cells) and with rulers on four nights.
  (src: results/ohm-window-night-2026-11-23/README.md; prereg/ohm_ruler_night_2026-11-24.md)
- Contribution in one line per ruler, with the night it was judged on; the per-qubit record; the calibration comparison
  as an outside check of what the rulers find.

## 2. Method

- Circuits: arms A0, A1, A2; t = 1, 3, 4; strings by a bits-only rule (seed 20261124); pairs s/c with odd part
  O = (Z_s - Z_c)/2 and W = -sum_window O / 2 + const; 7 pairs at t = 1, 3 and 7 then 9 at t = 4.
  (src: prereg/ohm_ruler3_night_2026-11-25.md "Circuits"; gpu/ohm_ruler_night.py)
- Rulers, each written before its night: (a) total T_dev / T0; (b) sqrt of the |0> mirror over the circuit; (c) the
  same over the window; (d) the string mirrors' odd part m_q, sqrt of its window mean; (b') and (a') leaving out
  outside qubits whose |0> mirror is below tau = 0.3; (e) a readout pair prepared with X alone; (de) sqrt(m_q e_q) per
  window qubit. Why sqrt(m e) = g e (the mirror passes the gates twice and the readout once).
  (src: prereg/ohm_ruler4_night_2026-11-26.md "The rulers"; prereg/ohm_ruler3_night_2026-11-25.md)
- Words: AGREES when |d| < t_{0.975,K-1} SE (rule 4), NOT READ at SE 0 (rule 5); the direction r - rho; reading
  tables fixed before the data. Rule 6 (the procedure run word for word before the push).
  (src: prereg/README.md rules 3 to 6)
- Placement: psf-os 0.3.3, no calibration number; the same chain copy (drow 4) on fez every ruler night; the job's
  costs. (src: results/ohm-ruler*-night-*/README.md job tables; psf-os 0.3.3 doi:10.5281/zenodo.24496267)
- Dry runs: illustrative noise only, never fitted (readout faults, gate depolarizing, damping, a fixed ZZ rotation).
  (src: notes/ohm_ruler3_2026-11-25/, notes/ohm_ruler4_2026-11-26/, the workplace VS's twirl runs 2026-11-27)
- Independent re-count every night and the README check tools. (src: notes/verify_2026-11-2[4-6]/; tools/)

## 3. Results

3.1 The raw window (vanity and essence side by side). Window READS in 24 of 24 cells on 11-23 (kingston); raw W READS
in 18 of 18 cells on 11-24 and 11-25, 17 of 18 on 11-26 (A2 t = 4: 0.526, DOES NOT READ, the first cell of the four
nights). But the raw W stays above the exact value by +0.14 to +0.47 at t = 3, 4 (11-24), +0.15 to +0.34 (11-25), +0.18
to +0.37 (11-26). `[NIGHT 5]` (src: results/*/README.md raw tables)

3.2 Which ruler carries the shrink (table 1). (a): 0 of 6 cells at t >= 3 on 11-24, 2 of 6 on 11-25; (b): 3 of 6
on 11-24 and 11-25; (c) 5 of 6 and (d) 5 of 6 on 11-25; (de) 4 of 6 and (a') 2 of 6 on 11-26; (e) 0 of 6 (beside, as
the dry runs foresaw). `[NIGHT 5]` (src: results/ohm-ruler-night-2026-11-24/README.md, ohm-ruler3-night-2026-11-25,
ohm-ruler4-night-2026-11-26 rulers tables)

3.3 The readout's half (figure 2). A mirror carries the readout once and the test carries it once, so sqrt(mirror)
takes out half of it; (de) puts it back. On 11-26 (de)'s |d| < (d)'s in 6 of 6 cells at t >= 3 (8 of 9 with
t = 1; A0 t = 1 NOT SMALLER). Dry runs: one-sided readout 0.02, (d) 43 of 96 AGREES, (de) 93.
`[NIGHT 5]` (src: results/ohm-ruler4-night-2026-11-26/score.txt; notes/ohm_ruler4_2026-11-26/ tables)

3.4 What no ruler carries (figure 3). At t = 3 every ruler's d is positive on 11-26 (+0.02 to +0.11), (d) and (c)
positive in all 6 cells at t >= 3 on 11-25 (+0.02 to +0.08). The twirl dry runs: a fixed ZZ over-rotation after every
CZ leaves (d), (de) negative (theta 0.05: -0.008; 0.10: -0.034); mirror-only twirl does not move them to 0; twirling
every circuit does, but breaks (e). So a fixed-direction gate error does not explain the residual (in this model).
Guess (not measured): a shrink that grows with the light cone's own waits or spectators, absent from the mirrors.
`[NIGHT 5]` (src: score.txt of 11-25 and 11-26; the workplace VS's twirl report, 2026-11-27)

3.5 The direction (table 2). With rho_a, WINDOW SHRINKS LESS at t = 4 in all three arms on 11-25; with rho_a' (the
outside low qubits left out) NOT SEEN on 11-25 (after the record, home VS) and judged on 11-26 (MORE at t = 3, NOT
SEEN at A1, A2 t = 4). `[NIGHT 5]` (src: results/ohm-ruler3-night-2026-11-25/README.md; ohm-ruler4 score.txt)

3.6 The qubit record predicts (figure 4). OR4-2 held: physical 104 and 102 below tau on the t = 4 mirror in all
three arms, the third night running. 104's mirror 0.05 (A0, t = 4) while its own r on the test was 0.846 and e 0.989:
"mirror low" and "r low" are two facts. OR5-2 (101 to 104) `[NIGHT 5]`. (src: results/ohm-ruler4-night-2026-11-26/
qubits.csv; tools/qubits_across.py summary 2026-11-27)

3.7 Against IBM's calibration (table 3; beside). Memo fixed before any number (a11c510b, addendum cd698ebe); 191
snapshots. The CZ column marks our mirror_low findings at 2.29 x chance and scan_listed at 1.73 x; per-qubit columns
rarely, except fez readout_error (2.48 x) and T1 in mirror_low (1.62 x). IBM marks no column for fez 104 (found 68
times) nor kingston 42 to 47. On marrakesh 17 of 67 jobs ran on a map older than 24 h; a qubit's readout error moves
3.3 to 7.8 times day to day (median). (src: vs branch calib-compare2-2026-11-27, 786ae051,
notes/calib_compare_2026-11-26/result_2026-11-27.md)

3.8 The record's own checks. Independent re-count every night: words differ 0, largest difference 3.3e-16 (11-24),
5.7e-14 (11-25), 1.1e-16 (11-26); README sentences corrected after each check (11-24: one; 11-25: one; 11-26: four).
(src: results/*/README.md "Independent check"; c32e1f56)

## 4. Discussion

- What a ruler inside the job can and cannot be: it reads, it does not correct; a word against the dry runs'
  expectation (fifth night's table D) points to a fault outside the illustrative noises without naming it.
- The mirrors' blind spot for fixed-direction errors (and the cost of a full twirl, +33 %).
- Calibration maps describe the device's level, not the qubit a job meets; in-job rulers record what the map omits.
- Toward an operating layer: the rulers need only the compiled circuit and its inverse plus four to six readout
  circuits (notes/psfos_direction_2026-11-27/README.md).

## 5. Limits

- One device for the ruler nights (fez), one placement (copy drow 4), one circuit family; 7 to 9 pairs per cell.
- The rulers' worth is read night by night; the dry runs' noises are illustrative.
- Errors that cancel in U U^dagger are invisible to every mirror ruler; the residual at t = 3 is unexplained.
- The calibration comparison is beside: counted after the records, with a memo fixed first; it decides nothing.
- Predictions in the series: 73 declared, 53 held, 20 failed (all failures on paper 10's nights) `[NIGHT 5]`.

## 6. Related work

See `related.md`.
