# Ohm with rulers inside the circuit, the fifth night (DRAFT, not declared; workplace, 2026-11-27)

Draft by the workplace for home to declare, from the fourth night's declaration (`prereg/ohm_ruler4_night_2026-11-26.md`,
346934e9) and record (`results/ohm-ruler4-night-2026-11-26`, home VS's check in c32e1f56). The owner's decisions of
2026-11-26 evening: the readout circuits at the head and the tail of the job; an r / e column in qubits.csv; R columns
at t >= 3 only, said in one line; a table of the words the dry runs expect; the prediction that 101 to 104 all sit
below tau on the t = 4 mirror. The rulers judged are the fourth night's ((de), (a'), the direction with rho_a'), with 9
pairs at t = 4, under `prereg/README.md` rules 3 to 6. Tool `gpu/ohm_ruler_night5.py` (new; the declared
`gpu/ohm_ruler_night.py` to `gpu/ohm_ruler_night4.py` are imported read only), psf-os 0.3.3 (e652257). Notes
`notes/ohm_ruler5_2026-11-27/`.

## Why (after the 11-24 to 11-26 records; every idea below came after its data were seen)

- 11-26, ibm_fez, 173 circuits, 48 s: OR4-1 held (raw W 0.071 / 0.158 / 0.313); OR4-2 held (104 and 102 below tau on
  the t = 4 mirror in all three arms, the third night running). At t >= 3, AGREES: (de) 4 of 6 (DIFFERS at A1 t = 3,
  d 0.0383 against the width 0.0382, and A2 t = 3), (a') 2 of 6, (e) 0 of 6 (beside, as the dry runs foresaw). (de)'s
  |d| was below (d)'s in all six cells.
- At t = 3 every ruler's d was positive (+0.02 to +0.11): a shrink the readout does not explain is left. A2 t = 4's
  raw M and W did not read (0.529 / 0.526), the first cell of the four nights that does not.
- The 11-25 job ran in index order in two blocks about 19 s apart (`notes/pub_order_2026-11-26/`): a readout pair at
  the job's head and another at its tail sit at the two ends of the run, so their difference reads a change during the
  job on the user's own qubits.
- Guess (not measured): a fault fixed in direction (a coherent over- or under-rotation) cancels in a mirror U U^dagger
  and so never reaches (d) or (de); the workplace VS's twirl dry runs (2026-11-27) look at this, beside this draft.
- So four additions follow, none of which changes a ruler or a word:
  1. the readout pair s00 / c00 at the head and at the tail of the job (s01 / c01 at the tail only); e_q their mean;
  2. r / e per qubit in qubits.csv;
  3. a table of the words the dry runs expect per ruler and t, and reading table D that sets each word against it;
  4. OR5-2 on 101 to 104.

## Question

On the 11-12 Ohm circuits (as 11-24 to 11-26: light-cone circuits, strings by a bits-only rule, t = 1, 3, 4):
- does the window's transfer, divided by a ruler carried inside the circuit or its job, agree with the exact value?
- which way does the window's shrink lean against the circuit's total over the kept qubits?
- beside: does the readout change between the head and the tail of the job?
The raw M, W and S are read and reported as on 11-23 to 11-26.

## Circuits

- The 11-25 job unchanged (`build3 --smirrors sc --pairs-t 1:7 3:7 4:9`): A0, A1, A2, t = 1, 3, 4, seed **20261124**;
  **7 pairs at t = 1 and 3, 9 at t = 4**; one |0> mirror and two string mirrors (s00, c00) per (arm, t); 169 circuits.
- **6 readout circuits** on the t = 4 cone's 22 physical qubits (positions 12 to 33), each the string prepared with X
  alone, a barrier, then measured at once in the user records' label order (as 11-26):
  - at the head of the job: s00 and c00 (records `a_readout_s00_head`, `a_readout_c00_head`);
  - at the tail: s00, c00, s01, c01 (records `z_readout_*_tail`).
  psf-os 0.3.3 orders a job's pubs by its records' file names (`job.assemble`, sorted), so `a_` sorts before the
  sentinel (`ksent_`) and every user record (`p2d_`), and `z_` after them. build5 reads the assembled order and stops
  unless the head pair is pubs 0 and 1 and the tail four are the last four.
- No floors; no mid-circuit measurement, no delay (nothing to park). **175 circuits** (169 + 6; the 11-26 job's 4 readout
  circuits are replaced by these 6).

## The rulers (rule 3; written before the data)

As 11-26 (`prereg/ohm_ruler4_night_2026-11-26.md`, "The rulers"), with one change in e_q:
- **e_q = the mean of the head pair's and the tail pair's odd parts**, each (Z_s00,q - Z_c00,q) / 2 x (1 - 2 b_s00,q);
  its shot variance (var_head + var_tail) / 4 per qubit, summed over the window with the qubits taken as independent.
  Without noise e_q = 1; a readout that changes during the job enters the ruler at its mean over the job.
- **(de)**, per window qubit rho_q = sqrt(m_q e_q): judged. **(a')** at tau = 0.3: judged (read at t >= 3). The
  direction with rho_a': judged; with rho_a: beside. **(e)** = mean of e_q over the window: beside. (a), (b), (c), (d)
  as 11-25 (score3, unchanged); (b') beside.
- Words per cell as 11-26: AGREES when |d| < t_{0.975,K-1} SE (rule 4: 2.447 with K = 7, 2.306 with K = 9), DIFFERS
  otherwise, NOT READ when SE = 0 (rule 5) or as 11-26 writes; the 2 SE word beside.

## What the dry runs expect (fixed before the data)

The fifth night's job is the fourth night's with its readout circuits moved; no gate changed, so the fourth night's
dry runs carry over. Per ruler and t, the share (%) of cells that AGREE at the t quantile in each dry-run case
(workplace: none, the readout faults ro1, ro2, bo04, 2026-11-26; the workplace VS: dep, damp, rop2, 2026-11-26), and
the class by a rule fixed here: **EXPECTED TO AGREE** when the share is at least 85 % in every case; **EXPECTED TO
DIFFER** when it is at most 15 % in every gate-noise or damping case (dep, damp, rop2); **MIXED** otherwise. Written by
`notes/ohm_ruler5_2026-11-27/expect5.py` (its --check finds every row below); `-` where a case was not run (t = 4
with damping).

| ruler | t | none | ro1 | ro2 | bo04 | dep0.01 | dep0.02 | damp0.005 | damp0.01 | rop2 | class |
|---|---|---|---|---|---|---|---|---|---|---|---|
| (de) | 1 | 94 | 92 | 98 | 96 | 97 | 93 | 97 | 93 | 97 | EXPECTED TO AGREE |
| (de) | 3 | 96 | 96 | 96 | 94 | 97 | 93 | 100 | 93 | 100 | EXPECTED TO AGREE |
| (de) | 4 | 95 | 98 | 98 | 100 | 89 | 100 | - | - | 89 | EXPECTED TO AGREE |
| (a') | 3 | 96 | 94 | 94 | 98 | 0 | 0 | 3 | 0 | 0 | EXPECTED TO DIFFER |
| (a') | 4 | 95 | 96 | 96 | 98 | 56 | 100 | - | - | 67 | MIXED |
| (d) | 1 | 94 | 92 | 92 | 96 | 97 | 93 | 97 | 93 | 97 | EXPECTED TO AGREE |
| (d) | 3 | 96 | 48 | 8 | 94 | 97 | 93 | 100 | 93 | 90 | MIXED |
| (d) | 4 | 95 | 42 | 12 | 100 | 89 | 89 | - | - | 89 | MIXED |
| (e) | 1 | 94 | 94 | 96 | 96 | 97 | 97 | 93 | 87 | 97 | EXPECTED TO AGREE |
| (e) | 3 | 96 | 96 | 92 | 94 | 0 | 0 | 0 | 0 | 0 | EXPECTED TO DIFFER |
| (e) | 4 | 95 | 100 | 98 | 100 | 0 | 0 | - | - | 0 | EXPECTED TO DIFFER |

- (a') at t = 3 AGREES in 0 to 3 % of the cells under every gate-noise or damping case (0 of 30 in four of five): it
  is not a ruler for t = 3. Its use is at t = 4, to leave out the qubits outside the window that fail badly there (the
  11-25 and 11-26 records: 101 to 104); there it is MIXED.
- (de) is EXPECTED TO AGREE at every t, so a (de) DIFFERS on the device reads against the dry runs: the device holds a
  fault none of the illustrative noises holds (11-26: A1 t = 3 and A2 t = 3 would have read so).

score5 writes, per judged cell, the class and table D's reading beside the word.

## Beside, never judged

- **The readout at the head and the tail**: per qubit, e_q at the head, at the tail, tail minus head with its shot SE
  (a change during the job, on the user's own qubits, about a minute apart on 11-25's timing), and at the tail the
  s01 / c01 pair minus the s00 / c00 pair (the neighbours' states).
- **(e)**, the readout ruler, its words and d per cell (table C's (e) rows, read beside).
- **tau 0.2, 0.3, 0.4**: (a')'s and (b')'s words at each tau, with the qubits left out (judged at 0.3).
- **(de) against (d)**, a reading row, not a prediction.
- **`results/<night>/qubits.csv`**, one per night, one row per (arm, t, chain position), with the 11-26 columns
  (device, calibration_time, copy_drow, arm, t, position, physical, in_window, mirror_z, m_q, r_q, e_q,
  left_out_at_tau, MIRROR_LOW, R_LOW, R_HIGH) and three more:
  - e_head, e_tail: the head and tail pairs' e_q (empty off the t = 4 cone)
  - r_over_e: r_q / e_q where both are present and e_q > 0 (a qubit's shrink on the test against its readout's: near
    1, the readout explains the qubit's shrink; well below 1, the gates do)
  **R_LOW and R_HIGH are tested at t >= 3 only** (where the window has a pooled r; at t = 1 they read False), as the
  11-26 tool does. Values to 3 decimals.
- 11-25's beside values (order, growth, smallest difference, (b'), outlying positions, sentinel) as declared then.

## Job and seconds (2.6 s + 0.000269 s x circuits x shots; psf-os's model beside; 11-26 ran 173 circuits in 48 s)

| plan | pairs (t = 1, 3 / t = 4) | mirrors | readout | circuits | shots | seconds (formula) | psf-os model | check |
|---|---|---|---|---|---|---|---|---|
| 11-26 as declared | 7 / 9 | 9 + 18 | 4 | 173 | 1000 | 49.1 | 55.9 | check4 ALL PASS |
| **readout at the head and the tail** (proposed) | 7 / 9 | 9 + 18 | 6 | **175** | 1000 | **49.7** | **56.5** | check5 ALL PASS |

The proposed line was built on the 11-26 ibm_fez record (`results/ohm-ruler4-night-2026-11-26/fetch_in/ibm_fez/dev`,
copy drow 4) with the sealed 9-pair answers of 11-25: the readout pubs at 0, 1 and 171 to 174 of 175; check5 ALL PASS
(check3, then every readout circuit noise-free equal to its string within 1e-9). (Home's instruction counted 179 = 173
+ 6; the 11-26 job's 4 readout circuits are not kept, so 169 + 6 = 175.)

## Device and placement (no quality number)

As 11-26: of ibm_fez and ibm_kingston, the one with fewer pending jobs; not ibm_marrakesh; the chain by
`gpu/hub_build.py`'s rule; no error number is read; the calibration time is written into qubits.csv as a time only.
psf-os is not changed.

## Answers (sealed), pre-run check

- The 11-25 sealed answers (9 pairs, sha256 e581df9d4fbb99ca219f3beb1e3efbf6b2d34be0477d32fc7bf51071207497ac): the same
  circuits, nothing new is sealed. The readout circuits' answers are their strings.
- `check5 OUT ANS`: check3, then every readout circuit noise-free equal to its string within 1e-9. ALL PASS or no run.

## Verdicts (`score5 OUT ANS --tau 0.3`)

Per cell, over its K pairs:
- raw M, W as 11-24 (READS at a ratio of 0.5 or below);
- rulers (a), (b), (c), (d) as 11-25 (scores3.json); (de), (a') (scores5.json): AGREES / DIFFERS / NOT READ (t quantile;
  2 SE beside), each with its class and table D's reading; (e) beside;
- one factor on the window (t >= 3), as 11-24;
- the direction with rho_a' (t >= 3);
- OR5-1, OR5-2;
- beside, as listed above, and qubits.csv.

## Reading tables (fixed before the data; every combination on one row; each row reads on its own conditions)

Tables A and B as 11-25 (rulers (a) to (d), and the direction with ruler (a) for the beside row). Table B's rows are
read with (a') in the place of (a) for the judged direction:

| direction | ruler (a') | reading |
|---|---|---|
| WINDOW SHRINKS LESS | DIFFERS | the window keeps more of its odd part than the kept qubits' total: that total overstates the window's shrink |
| WINDOW SHRINKS LESS | AGREES | the window keeps more than the kept qubits' total, within what ruler (a')'s word can see |
| WINDOW SHRINKS MORE | DIFFERS | the window loses more of its odd part than the kept qubits' total: that total understates the window's shrink |
| WINDOW SHRINKS MORE | AGREES | the window loses more than the kept qubits' total, within what ruler (a')'s word can see |
| NOT SEEN | DIFFERS | no lean between the window and the kept qubits' total is seen, yet that total does not carry the window's shrink: read with the one-factor word |
| NOT SEEN | AGREES | the window and the kept qubits' total shrink alike |

Table C, the readout rulers and (a') (per cell; each ruler on its own rows; the (e) rows are read beside):

| ruler | word | reading |
|---|---|---|
| (e) | AGREES | the readout's shrink on the window carries the window's shrink |
| (e) | DIFFERS | the readout's shrink on the window does not carry the window's shrink |
| (e) | NOT READ | no scatter (rule 5) |
| (de) | AGREES | the string mirrors with the readout's half put back carry the window's shrink |
| (de) | DIFFERS | the string mirrors with the readout's half put back do not carry the window's shrink |
| (de) | NOT READ | no scatter (rule 5), or a mirror or readout value not positive |
| (a') | AGREES | the circuit's total over the kept qubits carries the window's shrink |
| (a') | DIFFERS | the circuit's total over the kept qubits does not carry the window's shrink |
| (a') | NOT READ | fewer than half of the circuit's qubits kept, or no scatter (rule 5) |

Reading row, beside (not a prediction), (de) against (d) per cell:

| (de) against (d) | reading |
|---|---|
| SMALLER | |d| of (de) below |d| of (d): the readout would explain part of (d)'s gap |
| NOT SMALLER | |d| of (de) not below |d| of (d): the readout does not explain (d)'s gap |

Read together (beside, never a word): (e) AGREES with (de) DIFFERS points to a shrink in the readout alone; (de)
AGREES with (e) DIFFERS points to a shrink in the gates that the string mirrors carry; both DIFFER, to neither.

Table D, a judged ruler's word against the dry runs' expectation (per cell; the class from the table above):

| class | word | reading |
|---|---|---|
| EXPECTED TO AGREE | AGREES | as the dry runs expect |
| EXPECTED TO AGREE | DIFFERS | against the dry runs: the device holds a fault that none of the dry runs' illustrative noises holds |
| EXPECTED TO DIFFER | AGREES | against the dry runs: the gates shrank the signal less than the dry runs' gate noise, or not at all |
| EXPECTED TO DIFFER | DIFFERS | as the dry runs expect under gate noise or damping |
| MIXED | AGREES | within what the dry runs allow |
| MIXED | DIFFERS | within what the dry runs allow |

## Predictions

- **OR5-1: the raw W READS at t = 3 in every arm** (A0, A1, A2). Held if the raw W's word is READS in all three cells.
  11-24: 0.050, 0.119, 0.261; 11-25: 0.059, 0.109, 0.243; 11-26: 0.071, 0.158, 0.313.
- **OR5-2** (the owner's decision of 2026-11-26): if the fifth night is placed on ibm_fez at the same copy (drow 4),
  physical 101, 102, 103 and 104 sit below tau = 0.3 on the t = 4 |0> mirror in all three arms. Held if all twelve
  values (4 qubits x 3 arms) are below 0.3; NOT HELD otherwise; NOT READ on another device or copy, or if a qubit is
  not on the t = 4 cone. Grounds: 102 and 104 three nights (11-24 to 11-26), 101 and 103 two (11-25, 11-26; on 11-26
  the largest of the twelve was 0.29, 101 in A2).
- No other prediction.

## Dry runs (no device; `notes/ohm_ruler5_2026-11-27/`)

All noise ILLUSTRATIVE, written by hand, at chain positions chosen by hand (not where any device's qubits failed). The
fourth night's dry runs (above, and `notes/ohm_ruler4_2026-11-26/`) carry over; these runs check the fifth night's job
and tool.

DRY5_TABLES

## Device procedure (home)

As 11-26: GitHub first (VPN ON), push the declaration. Then the device (VPN OFF), from a fresh notebook clone at the
declaring commit, with psf-os 0.3.3 (e652257) on PYTHONPATH and the sealed answers (9 pairs) outside the repository:
```
python gpu/daily_fetch.py OUT/fetch_in
DEV=$(python gpu/ohm_ruler_night.py pick OUT/fetch_in/queue.json | cut -d' ' -f1)
python gpu/ohm_ruler_night5.py build5 OUT/fetch_in/$DEV/dev OUT/or5 ANSWERS_SEALED OUT/or5_answers --pairs-t 1:7 3:7 4:9
python gpu/ohm_ruler_night5.py check5 OUT/or5 OUT/or5_answers                  # ALL PASS, or no run
python -m psf_os submit --job OUT/or5/job ; python -m psf_os collect --job OUT/or5/job --wait-min 20
python gpu/ohm_ruler_night5.py score5 OUT/or5 OUT/or5_answers --tau 0.3
```
`score5` writes scores3.json (score3, unchanged) first, then scores5.json and qubits.csv; copy qubits.csv to
`results/<night>/qubits.csv`. If the chosen device does not build, the other; if neither builds, no run. Rule 6: before
the push, this block is run word for word on a try-build (`tools/procedure_dry.py`, the 11-26 ibm_fez record, the sealed
9-pair answers). A run script in the 11-26 form: `notes/ohm_ruler5_2026-11-27/run_ohm_ruler5_night_DRAFT.sh`.

## Limits

- One device night per declaration; the head-tail difference is read on one night.
- The head and tail pairs are a minute apart at most (11-25's two blocks); a slower drift is not in them.
- e_q is a mean over the job: a readout that changes during the job enters (de) at its mean.
- The expected words come from illustrative noises; a device fault outside them (a coherent rotation, a leak, a
  crosstalk that the dry runs do not hold) is what table D's "against the dry runs" rows point to, without naming it.
- (a') keeps the window always; at t = 3 it DIFFERS under any gate shrink (dry runs), so its t = 3 words are expected.
- OR5-2 rests on two to three nights; its result says how long a per-qubit record lasts, not why the qubits read low.
- Not error correction, not post-selection: every shot counts; the rulers are declared before the data.
