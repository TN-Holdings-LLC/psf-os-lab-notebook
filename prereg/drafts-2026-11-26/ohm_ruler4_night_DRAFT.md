# Ohm with rulers inside the circuit, the fourth night (DRAFT, not declared; workplace, 2026-11-26)

Draft by the workplace for home to declare, from the third night's declaration (`prereg/ohm_ruler3_night_2026-11-25.md`,
ec67e8a6) and record (`results/ohm-ruler3-night-2026-11-25`, with home VS's beside values in
`notes/verify_2026-11-25/`). The owner's decisions, 2026-11-25 evening: the readout ruler (e), ruler (a') and the
per-qubit record go into the fourth night; the placement stays psf-os's rule (no rule that avoids bad qubits); OR4-2
is declared. Home's addendum of 2026-11-25 (home VS's proposals) is followed where it differs from the instruction:
4 readout circuits instead of 18, (de) = sqrt(m_q e_q), 9 pairs at t = 4, tau 0.2 / 0.3 / 0.4 beside, one
`qubits.csv` per night. Under `prereg/README.md` rules 3 to 6. Tool `gpu/ohm_ruler_night4.py` (new; the declared
`gpu/ohm_ruler_night.py`, `gpu/ohm_ruler_night2.py` and `gpu/ohm_ruler_night3.py` are imported read only), psf-os 0.3.3
(e652257). Notes `notes/ohm_ruler4_2026-11-26/`.

## Why (after the 11-24 and 11-25 records; every idea below came after its data were seen)

- 11-25, ibm_fez, 169 circuits, 47 s: OR3-1 held (raw W 0.059 / 0.109 / 0.243). At t >= 3, AGREES: (d) 5 of 6,
  (c) 5 of 6, (b) 3 of 6, (a) 2 of 6. The direction at t = 4: WINDOW SHRINKS LESS in all three arms, (a) DIFFERS.
- Beside (11-25): (b') 6 of 6 AGREES, leaving out physical 101 to 104 at t = 4. After the record (home VS), (a'), the
  circuit's total over the qubits (b') keeps: 5 of 6 AGREES, and the t = 4 direction NOT SEEN in all three arms.
  Guess (not measured): the direction of that night came from 101 to 104 pulling the total down.
- (c) and (d)'s d was positive in all 6 cells at t >= 3 (+0.02 to +0.08). Guess (not measured): part of it is the
  readout, which every mirror carries once and the test carries once, so a square root of a mirror takes out only half
  of it.
- The 11-24 and 11-25 |0> mirrors sat near 0 on physical 104 and 102 at t = 4 on both nights (same device, same copy).
- So three additions follow, each written so that it can be read or left alone without changing the rest:
  1. a readout ruler (e) from strings prepared and measured with no gate, and (de), the string mirrors with the
     readout's half put back;
  2. (a') judged, with its direction;
  3. a per-qubit record (`qubits.csv`), beside, never judged.

## Question

On the 11-12 Ohm circuits (as 11-24 and 11-25: light-cone circuits, strings by a bits-only rule, t = 1, 3, 4):
- does the window's transfer, divided by a ruler carried inside the circuit or its job, agree with the exact value?
- which way does the window's shrink lean against the circuit's total over the kept qubits?
The raw M, W and S are read and reported as on 11-23 to 11-25.

## Circuits

- The 11-25 job unchanged (`build3 --smirrors sc --pairs-t 1:7 3:7 4:9`): A0, A1, A2 on the 40-qubit chain's
  light-cone circuits L of the window, t = 1, 3, 4; the 11-12 string generator with seed **20261124**; **7 pairs at
  t = 1 and 3, 9 at t = 4**; one |0> mirror per (arm, t); two string mirrors per (arm, t) (s00, c00); 169 circuits.
- **4 readout circuits** (new): on the t = 4 cone's 22 physical qubits (positions 12 to 33), the strings s00, c00, s01
  and c01 restricted to the cone, prepared with X alone, a barrier, then measured at once (no other gate; Z readout,
  ideal <Z_q> = 1 - 2 b_q). The three arms sit on the same physical qubits and the t = 1 and 3 cones lie inside the t = 4
  cone, so e_q depends on neither arm nor t: one set serves every cell. The second pair (s01, c01) puts each qubit's
  neighbours in other states, to see whether e_q moves with them (beside).
- The readout circuits measure in the order of the user records' labels, so the job reader maps bits to qubits as for
  every other record (an earlier try-build measured them in another order and read e_q near 0.6 without
  noise; fixed and tested before this draft).
- No floors; no mid-circuit measurement, no delay (nothing to park; the build records it). 173 circuits.

## The rulers (rule 3; written before the data)

Per pair k and chain position q, O_kq = (Z_s - Z_c) / 2; W_k = -sum_{q in window} O_kq / 2 + const_k (11-24's
identity). Each ruler gives a rho; W_x,k is W_k with O_device replaced by O_device / rho_x. Without noise every rho is
1 and every W_x equals W_exact. (a), (b), (b'), (c) and (d) are 11-25's, unchanged (`score3`, its scores3.json written
first and kept).

- **(e) the readout ruler** (new): per qubit, e_q = (Z_s00,q - Z_c00,q) / 2 x (1 - 2 b_s00,q) on the readout circuits.
  If a 0 reads as 1 with p01 and a 1 as 0 with p10, then Z_s = sig (1 - p01 - p10) + (p10 - p01) and
  Z_c = -sig (1 - p01 - p10) + (p10 - p01), with sig = 1 - 2 b_s00: the odd part keeps only the shrink
  e_q = 1 - p01 - p10 (ideal 1); a one-sided lean cancels. rho_e = mean of e_q over the window (no square root: the
  test reads out once, as the readout circuit does).
- **(de) the string mirrors with the readout's half put back** (new): per window qubit, rho_q = sqrt(m_q e_q), m_q
  11-25's string-mirror odd part. A string mirror passes the gates twice and the readout once (m = g^2 e); the test
  passes the gates once and the readout once (g e); so sqrt(m e) = g e. W_de,k = -sum_{q in window} O_kq / rho_q / 2 +
  const_k. NOT READ when any window qubit's m_q e_q is not positive.
- **(a') the circuit's total over the kept qubits** (judged; beside on 11-25): the qubits (b') keeps at **tau = 0.3**
  (every window qubit; a qubit outside the window when its |0> mirror <Z_q> >= tau), per pair rho_a',k = sum over the
  kept qubits of O_device,kq / sum over the same qubits of O_exact,kq (the sealed answers, qubit by qubit). Read at
  t >= 3 (as (a)). **NOT READ when fewer than half of the circuit's qubits are kept**, or an exact sum is 0.
- SEs: (e) adds the readout circuits' shot noise through the mean (delta method, the sum of the per-qubit shot
  variances over the window, the qubits taken as independent); (de) adds the string mirrors' and
  the readout's shot noise per qubit through the square root; (a') takes the pairs' scatter only (as (a)).
- Words per cell: d_x = mean_k (W_x,k - W_exact,k); **AGREES when |d_x| < t_{0.975,K-1} SE** (rule 4: K = 7, 2.447;
  K = 9 at t = 4, 2.306), DIFFERS otherwise; **NOT READ when SE = 0** (rule 5) or as written above. The 2 SE word is
  written beside.
- **Judged tonight: (a), (b), (c), (d) as 11-25, and (de), (a').** (b') and (e) stay beside. Which of (e) and (de)
  to judge was settled by the dry runs below: (e) carries the readout's shrink only, so with any gate noise or damping
  it DIFFERS in every cell at t = 3 and 4 (the workplace VS: 0 of 30 and 0 of 9 in every row), while (de) AGREES in
  89 to 100 % of the cells in every row, readout faults included. (e) is still computed and written beside (its e_q
  is in (de) and in qubits.csv), with its rows of table C read beside.

## The direction r - rho_a' (judged) and r - rho_a (beside)

- Per pair: r_k = sum_{q in window} O_device,kq O_exact,kq / sum_{q in window} O_exact,kq^2 (positions with sum_k
  O_exact^2 below 0.05 K take no part, as 11-24); delta_k = r_k - rho_a',k.
- Per cell (t >= 3): delta = mean_k delta_k with its SE from the pairs' scatter. WINDOW SHRINKS LESS when delta > t SE;
  WINDOW SHRINKS MORE when delta < -t SE; NOT SEEN otherwise; NOT READ when SE = 0 or (a') is NOT READ.
- The same with rho_a (11-25's direction) is written beside.

## Beside, never judged

- **(e)**, the readout ruler, its words and d per cell (table C's (e) rows, read beside).
- **tau 0.2, 0.3, 0.4**: (a')'s and (b')'s words at each tau, with the qubits left out (judged at 0.3).
- **(de) against (d)**, a reading row, not a prediction (it rests on two nights' arithmetic after the records): per
  cell, whether |d| of (de) is below |d| of (d).
- **The second readout pair**: e_q from s01 / c01 and its difference from s00 / c00, per qubit.
- **`results/<night>/qubits.csv`**, one per night, one row per (arm, t, chain position), with these columns:
  - device: the device's name
  - calibration_time: the device record's calibration time (a time only; no error number is read)
  - copy_drow: the copy of the chain on the device (11-24 and 11-25: 4)
  - arm, t, position: the cell and the chain position
  - physical: the physical qubit
  - in_window: whether the position is in the window
  - mirror_z: the |0> mirror's <Z_q>
  - m_q: the string mirrors' odd part
  - r_q: the position's factor on the test, sum_k O_device O_exact / sum_k O_exact^2 (outside the window too; empty
    where sum_k O_exact^2 is below 0.05 K)
  - e_q: the readout ruler's value (empty off the t = 4 cone)
  - left_out_at_tau: outside the window and mirror_z below tau
  - MIRROR_LOW: mirror_z below tau (0.3)
  - R_LOW: r_q below the window's pooled r by more than 2 shot-noise SE (the lower side only; outside the window
    too; score3's outlying positions, both sides, stay in scores3.json)
  The values are written to 3 decimals.
  MIRROR LOW and R LOW are two columns because they are two facts (the 11-25 README first read one for the other).
  A tool that sets nights side by side reads these files only and is not part of any verdict; it sets a row beside
  another night's only when the physical qubit and the copy are the same, and compares nothing.
- 11-25's beside values (order, growth, smallest difference, (b'), outlying positions, sentinel) as declared then.

## Job and seconds (2.6 s + 0.000269 s x circuits x shots; psf-os's model beside; 11-25 ran 169 circuits in 47 s)

| plan | pairs (t = 1, 3 / t = 4) | mirrors | readout | circuits | shots | seconds (formula) | psf-os model | check |
|---|---|---|---|---|---|---|---|---|
| 11-25 as declared | 7 / 9 | 9 + 18 | 0 | 169 | 1000 | 48.1 | 54.7 | check3 ALL PASS |
| **11-25 + readout** (proposed) | 7 / 9 | 9 + 18 | 4 | **173** | 1000 | **49.1** | **55.9** | check4 ALL PASS |
| option: 13 pairs at t = 4 | 7 / 13 | 9 + 18 | 4 | 197 | 1000 | 55.6 | 63.3 | (not built) |

The proposed line was built on the 11-25 ibm_fez record (`fetch_in/ibm_fez/dev`, copy drow 4) with the sealed 9-pair
answers of 11-25; check4 (check3, then every readout circuit noise-free equal to its string within 1e-9) ALL PASS. The
job is build3's byte for byte but for the 4 readout circuits and the sentinel's 4 circuits, which differ between
builds (seen on the try-builds; the cause in psf-os not looked into). The 13-pair line is counted (+4 pairs x 2 x 3 arms = 24 circuits), not built: 13 pairs need 13 sealed pairs.

### 13 pairs at t = 4 (an option for the owner; planning numbers, not a ruler)

With 11-25's scatter at t = 4, t SE x 2.179 / 2.306 x sqrt(9 / 13) = x 0.79:

| cell (11-25) | (a') t SE, 9 pairs | 13 pairs | (d) t SE, 9 pairs | 13 pairs |
|---|---|---|---|---|
| A0 t4 | 0.049 | 0.038 | 0.106 | 0.083 |
| A1 t4 | 0.067 | 0.053 | 0.082 | 0.064 |
| A2 t4 | 0.086 | 0.067 | 0.052 | 0.040 |

(from `notes/verify_2026-11-25/or3_beside_aprime_dq.json`). 24 more circuits, about 6.5 s more by the formula. The
draft proposes 9 (home's addendum): (a') is already narrower than (d) at A0 and A1.

## Device and placement (no quality number)

- As 11-25: of ibm_fez and ibm_kingston, the one with fewer pending jobs; not ibm_marrakesh; the chain by
  `gpu/hub_build.py`'s rule. The device record's lengths of time are read by psf-os 0.3.3; no error number is read.
  The calibration time is written into qubits.csv as a time only.
- psf-os is not changed. The sentinel's overlap with the user's qubits is counted from the circuits as sent (beside).

## Answers (sealed), pre-run check

- The 11-25 sealed answers (9 pairs, sha256 e581df9d4fbb99ca219f3beb1e3efbf6b2d34be0477d32fc7bf51071207497ac): the
  strings and their answers are the same circuits as 11-25 (seed 20261124), so nothing new is sealed. The readout
  circuits' answers are their strings (no gate).
- `check4 OUT ANS`: the declared check (check3), then every readout circuit noise-free equal to its string within
  1e-9. ALL PASS or no run.

## Verdicts (`score4 OUT ANS --tau 0.3`)

Per cell, over its K pairs:
- raw M, W as 11-24 (READS at a ratio of 0.5 or below);
- rulers (a), (b), (c), (d) as 11-25 (scores3.json); (de), (a') (scores4.json): AGREES / DIFFERS / NOT READ
  (t quantile; 2 SE beside); (e) beside;
- one factor on the window (t >= 3), as 11-24;
- the direction with rho_a' (t >= 3);
- OR4-2;
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

## Predictions

- **OR4-1: the raw W READS at t = 3 in every arm** (A0, A1, A2). Held if the raw W's word is READS in all three cells.
  11-24: 0.050, 0.119, 0.261; 11-25: 0.059, 0.109, 0.243.
- **OR4-2** (the owner's decision of 2026-11-25): if the fourth night is placed on ibm_fez at the same copy (drow 4),
  physical 104 and 102 sit below tau = 0.3 on the t = 4 |0> mirror in all three arms. Held if all six values
  (2 qubits x 3 arms) are below 0.3; NOT HELD otherwise; NOT READ on another device or copy, or if either qubit is not
  on the t = 4 cone. Grounds: two nights (11-24 and 11-25, both near 0). It is closed inside the job and is not tied
  to the placement (the placement rule does not read it).
- No other prediction: (de), (a') and the direction with rho_a' rest on at most one record each, and (e) on none.

## Dry runs (no device; `notes/ohm_ruler4_2026-11-26/`)

All noise ILLUSTRATIVE, written by hand, at chain positions chosen by hand (not where any device's qubits failed).

DRY_RUN_TABLES

## Device procedure (home)

As 11-25: GitHub first (VPN ON), push the declaration. Then the device (VPN OFF), from a fresh notebook clone at the
declaring commit, with psf-os 0.3.3 (e652257) on PYTHONPATH and the sealed answers (9 pairs) outside the repository:
```
python gpu/daily_fetch.py OUT/fetch_in
DEV=$(python gpu/ohm_ruler_night.py pick OUT/fetch_in/queue.json | cut -d' ' -f1)
python gpu/ohm_ruler_night4.py build4 OUT/fetch_in/$DEV/dev OUT/or4 ANSWERS_SEALED OUT/or4_answers --pairs-t 1:7 3:7 4:9
python gpu/ohm_ruler_night4.py check4 OUT/or4 OUT/or4_answers                  # ALL PASS, or no run
python -m psf_os submit --job OUT/or4/job ; python -m psf_os collect --job OUT/or4/job --wait-min 20
python gpu/ohm_ruler_night4.py score4 OUT/or4 OUT/or4_answers --tau 0.3
```
`score4` writes scores3.json (score3, unchanged) first, then scores4.json and qubits.csv; copy qubits.csv to
`results/<night>/qubits.csv`. If the chosen device does not build, the other; if neither builds, no run. Rule 6: before
the push, this block is run word for word on a try-build (`tools/procedure_dry.py`, the 11-25 ibm_fez record, the
sealed 9-pair answers).

## Limits

- One device night per declaration; (e), (de) and (a') come from two records, so their worth is read on a new night.
- (e) reads the readout once, on its own circuits, after no gate: a readout that changes with what came before (a
  qubit left in a state by the gates) is not in it. The second pair reads a change with the neighbours' states only.
- (de) assumes m = g^2 e (the mirror's two passes shrink alike and the readout once); a fault that a mirror's second
  pass undoes or doubles differently from the test breaks it.
- (a') keeps the window always; a window qubit that fails stays in W and in (a'), as in the test.
- tau is set from illustrative noise; a device whose ordinary qubits sit below tau would leave them out (the NOT READ
  rule bounds this; tau 0.2 and 0.4 are written beside).
- A mirror waits differently from the forward circuit, so dephasing while waiting moves the mirrors more than the test
  (11-25's limit, unchanged); the readout circuits do not wait.
- OR4-2 rests on two nights; its result says how long a per-qubit record lasts, not why those qubits read low.
- Not error correction, not post-selection: every shot counts; the rulers are declared before the data.
