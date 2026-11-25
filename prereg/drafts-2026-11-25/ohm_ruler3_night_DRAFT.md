# DRAFT (not declared): Ohm with rulers inside the circuit, the third night (Heron)

Workplace Claude, 2026-11-25, on home's instructions "オームの物差し、次の晩の宣言の下書き" and "下書きの仕上げ" (b,
home's proposals put in, each marked [OWNER: home's proposal]) and the 11-24 record
(`results/ohm-ruler-night-2026-11-24`, declared `prereg/ohm_ruler_night_2026-11-24.md`, c4518f53). Words, tables,
thresholds and every item marked [OWNER] are the owner's to choose; home declares. Under `prereg/README.md` rules 3, 4
and 5: rulers carried by the circuit or its job may be declared (3); with fewer than 10 units the words use the t
quantile with n - 1 degrees of freedom (4); a word whose SE is 0 is NOT READ (5). Tool `gpu/ohm_ruler_night3.py`
(new; the declared `gpu/ohm_ruler_night.py` and `gpu/ohm_ruler_night2.py` are imported read only), psf-os 0.3.3
(e652257). Notes `notes/ohm_ruler3_2026-11-25/`.

## Why (after the 11-24 record; every idea below came after its data were seen)

- 11-24, ibm_fez, plan B (7 pairs, t = 1, 3, 4): the raw W READS in all cells (OR-1 held), but stays above the exact
  value by +0.14 to +0.47 at t = 3 and 4 (each beyond 2 SE).
- Ruler (a), the circuit's total: DIFFERS in all 6 cells, in the direction opposite to the dry runs' gate-noise model:
  the window's factor r exceeds rho_a by +0.03 to +0.12 (the window shrinks less than the total).
- Ruler (b), sqrt of the |0> mirror: AGREES in 3 of 6 cells; at t = 4 its 2 SE is about 0.10.
- Beside (home, after the record; not judged): ruler (c), the mirror on the window alone, DIFFERS on the positive side
  in 5 of 6 cells. Per position: at t = 4 three mirror qubits sit near <Z> = 0 while their neighbours do not; at t = 3
  one qubit outside the window has r near 0.42 while its |0> mirror looks ordinary.
- Guess (not measured): a few qubits that fail badly pull the circuit's total and the mirror's mean away from the
  window; and a mirror that starts from |0> does not see faults that a |1> suffers (decay, readout asymmetry).
- So three candidates follow, each written so that it can be taken or left alone without changing the rest:
  1. a per-qubit rule on the mirrors, fixed before the data, that leaves badly failing qubits out of the rulers' means;
  2. a mirror that starts from the test's own string and its complement (ruler (d));
  3. a fixed beside column r - rho_a with its t-quantile SE, and reading tables split into "which ruler reads" and
     "the direction of the shrink".

## Question

On the 11-12 Ohm circuits (as 11-24: light-cone circuits, strings by a bits-only rule, t = 1, 3, 4):
- does the window's transfer, divided by a ruler carried inside the circuit or its job, agree with the exact value?
- which way does the window's shrink lean against the circuit's total (candidate 3)?
The raw M, W and S are read and reported as on 11-23 and 11-24.

## Circuits

- The 11-24 plan B: A0, A1, A2 on the 40-qubit chain's light-cone circuits L of the window (positions 20 .. 20 + 2t - 2),
  t = 1, 3, 4; the 11-12 string generator with seed **20261124**, kept when |T0| >= 6 on each t >= 3 cone.
- **Pairs: 7 at t = 1 and 3, 9 at t = 4** [OWNER: home's proposal]. The 9 are the same rule's first 9 draws kept (31
  draws); the first 7 are 11-24's 14 strings.
- One |0> mirror per (arm, t) on s00, as 11-24 (rulers (b), (c)).
- **Two string mirrors per (arm, t)** [OWNER: home's proposal, ruler (d)]: s00 -> U U^dagger -> s00 and c00 -> U
  U^dagger -> c00, built as the compiled circuit, a barrier, its inverse, a barrier, X on the physical qubits whose bit
  is 1, Z readout (ideal <Z_q> = 1 - 2 b_q); 18 circuits.
- No floors; no mid-circuit measurement, no delay (nothing to park; the build records it).

## The rulers (rule 3; written before the data)

Per pair k and chain position q, O_kq = (Z_s - Z_c) / 2; W_k = -sum_{q in window} O_kq / 2 + const_k (11-24's identity).
Each ruler gives a rho; W_x,k is W_k with O_device replaced by O_device / rho_x (rho per pair for (a), per cell for the
mirrors). Without noise every rho is 1 and every W_x equals W_exact.

- **(a) the circuit's total** (as 11-24): rho_a,k = T_device,k / T0_k. Read at t >= 3.
- **(b) the |0> mirror over the circuit** (as 11-24): rho_b = sqrt(mean over the circuit's qubits of the mirror's <Z>).
- **(b') candidate 1, the |0> mirror over the circuit with its low qubits outside the window left out** [OWNER: home's
  proposal was "judged if the dry runs meet both conditions, beside otherwise"; the dry runs below do not meet them
  under gate noise, so (b') is **beside, not judged**]: a qubit **outside the
  window** whose |0> mirror <Z_q> is below **tau = 0.3** is left out of (b)'s mean (not out of the circuit or of W);
  window qubits always stay (W carries their shrink). When fewer than half of the circuit's qubits are left, NOT READ.
  tau is set from the dry runs, never from a device record.
- **(c) the |0> mirror over the window**: rho_c = sqrt(mean over the window's qubits of the mirror's <Z>).
- **(d) the string mirrors' odd part over the window**: per qubit, m_q = (Z^m_s,q - Z^m_c,q) / 2 x (1 - 2 b_s00,q),
  ideal 1; rho_d = sqrt(mean over the window's qubits of m_q). The odd part cancels what s and c share; a fault that a
  |1> suffers and a |0> does not stays in m_q, as it stays in the test's own odd part.
- Each mirror ruler's SE adds its mirror's shot noise on the averaged qubits (per-shot mean), through the square root.
- Words per cell: d_x = mean_k (W_x,k - W_exact,k); **AGREES when |d_x| < t_{0.975,K-1} SE** (rule 4: K = 7, 2.447;
  K = 9 at t = 4, 2.306), DIFFERS otherwise; **NOT READ when SE = 0** (rule 5) or (b') keeps too few qubits. The 2 SE
  word is written beside.

## The direction r - rho_a (candidate 3) [OWNER: home's proposal]

- Per pair: r_k = sum_{q in window} O_device,kq O_exact,kq / sum_{q in window} O_exact,kq^2 (positions with sum_k
  O_exact^2 below 0.05 K take no part, as 11-24); delta_k = r_k - rho_a,k.
- Per cell (t >= 3): delta = mean_k delta_k with its SE from the pairs' scatter. WINDOW SHRINKS LESS when delta > t SE;
  WINDOW SHRINKS MORE when delta < -t SE; NOT SEEN otherwise; NOT READ when SE = 0.

## Job and seconds (2.6 s + 0.000269 s x circuits x shots; psf-os's model beside; 11-24 ran plan B in 39 s)

| plan | pairs (t = 1, 3 / t = 4) | mirrors | circuits | shots | seconds (formula) | psf-os model | check3 |
|---|---|---|---|---|---|---|---|
| B (11-24) | 7 / 7 | 9 | 139 | 1000 | 40.0 | 45.5 | ALL PASS |
| B + d | 7 / 7 | 9 + 18 | 157 | 1000 | 44.8 | 51.0 | ALL PASS |
| B9 at t = 4 | 7 / 9 | 9 | 151 | 1000 | 43.2 | 49.2 | (built) |
| **B9 at t = 4 + d** [OWNER: home's proposal] | 7 / 9 | 9 + 18 | **169** | 1000 | **48.1** | **54.7** | ALL PASS |

Try-builds on the 11-23 ibm_fez record (`notes/ohm_ruler3_2026-11-25`). `build3 --smirrors none` with 7 pairs writes
the declared 11-24 job byte for byte. (b'), the direction and the tables add no circuit.

### The smallest difference each cell can see (planning numbers from the 11-24 record's SEs; not a ruler)

t SE with 11-24's scatter of ruler (b): at t = 3 (7 pairs, 2.447) 0.03 to 0.05; at t = 4 with 9 pairs (SE x sqrt(7/9),
2.306) 0.09 to 0.12, against 0.11 to 0.14 with 7. Each cell's own t SE is written beside its words.

## Device and placement (no quality number)

- As 11-24: of ibm_fez and ibm_kingston, the one with fewer pending jobs; not ibm_marrakesh; the chain by
  `gpu/hub_build.py`'s rule. The device record's lengths of time are read by psf-os 0.3.3; no error number is read.
- psf-os is not changed. The sentinel's overlap with the user's qubits is counted from the circuits as sent (score3,
  beside); when it is 0 the record says NOT ON USER QUBITS, and the README says what that night's sentinel did not see
  (the user's qubits).

## Answers (sealed), pre-run check

- `answers ANS.json --pairs 9 --ts 1 3 4 --forms L`: **sha256 e581df9d4fbb99ca219f3beb1e3efbf6b2d34be0477d32fc7bf51071207497ac**
  (made again at the workplace, 2026-11-25; equal to the workplace's 11-24 try file for 9 pairs, which home and the
  workplace VS hold outside the notebook). Kept outside the notebook until the scores; build3 takes the first 7 pairs
  at t = 1 and 3.
- `check3 OUT ANS`, noise-free on the compiled circuits: the declared check (every item within 1e-6 of the answers,
  every total equal to T0, every |0> mirror all |0>, the rulers' exact totals), then every string mirror equal to its
  string within 1e-6. ALL PASS or no run.

## Verdicts (`score3 OUT ANS --tau 0.3`)

Per cell, over its K pairs:
- raw M, W as 11-24 (READS at a ratio of 0.5 or below);
- rulers (a), (b), (c), (d): AGREES / DIFFERS / NOT READ (t quantile; 2 SE beside);
- one factor on the window (t >= 3), as 11-24 (UNIFORM at p >= 0.05; NOT READ with fewer than 2 positions or a 0 SE);
- the direction (t >= 3).
- Beside, never judged:
  - order: the order of W, W_a, W_b, W_b', W_c and W_d at t = 3 and 4 (A0 > A1 > A2)
  - growth: W(t) / W(1), raw and exact
  - smallest difference: each ruler's t SE per cell
  - candidate 1: ruler (b')'s words and the qubits it leaves out, per cell
  - sentinel: the sentinel's word and its overlap with the user's qubits

## Reading tables (fixed before the data; every combination on one row; each row reads on its own conditions)

Table A, which rulers carry the window's shrink (per cell; each ruler on its own rows):

| ruler | word | reading |
|---|---|---|
| (a) | AGREES | the circuit's total carries the window's shrink |
| (a) | DIFFERS | the circuit's total does not carry the window's shrink |
| (a) | NOT READ | no scatter between the pairs (rule 5) |
| (b) | AGREES | the |0> mirror's mean over the circuit carries the window's shrink |
| (b) | DIFFERS | the |0> mirror's mean over the circuit does not carry the window's shrink |
| (b) | NOT READ | no scatter (rule 5) |
| (b_out) | AGREES | the |0> mirror's mean over the circuit, its low qubits outside the window left out, carries the window's shrink |
| (b_out) | DIFFERS | the |0> mirror's mean over the circuit, its low qubits outside the window left out, does not carry the window's shrink |
| (b_out) | NOT READ | fewer than half of the circuit's qubits left, or no scatter (rule 5) |
| (c) | AGREES | the |0> mirror's mean over the window carries the window's shrink |
| (c) | DIFFERS | the |0> mirror's mean over the window does not carry the window's shrink |
| (c) | NOT READ | no scatter (rule 5) |
| (d) | AGREES | the string mirrors' odd part over the window carries the window's shrink |
| (d) | DIFFERS | the string mirrors' odd part over the window does not carry the window's shrink |
| (d) | NOT READ | no scatter (rule 5) |

(b_out) is (b'); the tool's key is b_out. Its rows are read only if the owner judges (b') [OWNER: home's proposal
leads to beside, see the dry runs].

Table B, the direction (per cell at t >= 3; 3 words x ruler (a) 2 words = 6 rows; a cell where either is NOT READ is
not read here):

| direction | ruler (a) | reading |
|---|---|---|
| WINDOW SHRINKS LESS | DIFFERS | the window keeps more of its odd part than the circuit's total: the total overstates the window's shrink |
| WINDOW SHRINKS LESS | AGREES | the window keeps more than the total, within what ruler (a)'s word can see |
| WINDOW SHRINKS MORE | DIFFERS | the window loses more of its odd part than the circuit's total: the total understates the window's shrink |
| WINDOW SHRINKS MORE | AGREES | the window loses more than the total, within what ruler (a)'s word can see |
| NOT SEEN | DIFFERS | no lean between the window and the total is seen, yet the total does not carry the window's shrink: read with the one-factor word |
| NOT SEEN | AGREES | the window and the total shrink alike |

The raw words keep 11-23's meaning. The one-factor word is read on its own line, as 11-24.

## Predictions [OWNER: home's proposal]

- **OR3-1: the raw W READS at t = 3 in every arm** (A0, A1, A2). Held if the raw W's word is READS in all three cells.
  11-24: 0.050, 0.119, 0.261.
- No other prediction: the direction (11-24 beside: r - rho_a +0.03 to +0.12) rests on one night and may come from that
  night's few failing qubits; no record reads (b'), (c), (d) or t = 4 with 9 pairs.

## Dry runs (no device; `notes/ohm_ruler3_2026-11-25/` and the workplace VS's その2)

All noise ILLUSTRATIVE, written by hand, at chain positions chosen by hand (not where any device's qubits failed).

**Readout-like faults** (workplace; plan B + d on the 11-23 ibm_fez record; `dry3.py`; 16 seeds per case; t >= 3, 96
cells per row; AGREES at the t quantile, 2 SE in brackets):

| case | (a) | (b) | (b') | (c) | (d) |
|---|---|---|---|---|---|
| no noise | 92 (87) | 92 (87) | 92 (87) | 92 (87) | 92 (87) |
| positions 15, 18, 22: 1 read as 0 with 0.4 | 73 (68) | 30 (26) | 30 (26) | 30 (26) | 61 (57) |
| the same with 0.8 | 69 (66) | 31 (27) | 31 (27) | 31 (27) | 60 (52) |
| positions 14, 17, 18 (outside the window): both ways 0.4 | 67 (62) | 0 (0) | 91 (86) | 92 (87) | 92 (87) |
| every bit flips with 0.02 | 91 (89) | 2 (0) | 2 (0) | 3 (1) | 1 (0) |

**Gate noise, idle dephasing, amplitude damping** (the workplace VS's その2: plan B + d on the 11-24 ibm_fez record,
Aer trajectories; t = 3, 30 cells per row (6 where the VS kept 2 seeds); read again by the workplace with this score3,
whose (b), (c), (d) equal the VS's table):

| case | (a) | (b) | (b') | (c) | (d) |
|---|---|---|---|---|---|
| depolarizing per CZ, p2 0.005 | 1 (0) | 29 (27) | 29 (27) | 30 (29) | 28 (25) |
| p2 0.01 | 0 (0) | 28 (26) | 28 (26) | 30 (28) | 29 (27) |
| p2 0.02 | 0 (0) | 22 (17) | 9 (6) | 29 (28) | 28 (25) |
| idle dephasing, T2 10 us | 20 (20) | 0 (0) | 0 (0) | 14 (8) | 13 (12) |
| amplitude damping per CZ, gamma 0.005 (2 seeds) | 0 (0) | 6 (4) | 6 (4) | 2 (2) | 6 (6) |
| positions 15, 18, 22 depolarized 0.1 per CZ | 0 (0) | 22 (20) | 10 (4) | 30 (30) | 30 (30) |
| positions 15, 18, 22 damped 0.1 per CZ (2 seeds) | 0 (0) | 4 (4) | 2 (2) | 4 (4) | 6 (6) |

- Rule 4 halves the false words: without noise 4 of 96 DIFFERS at the t quantile, 9 of 96 at 2 SE (the VS's 64 seeds:
  4.2 % and 7.6 % with 7 pairs, 6.0 % and 8.3 % with 9).
- (d) reads a fault that a |1> suffers and a |0> does not (61 and 60 of 96 against 30 and 31), the 3-qubit faults under
  gate noise (30 of 30) and the damping (6 of 6). (c) and (d) follow r under uniform depolarizing up to p2 0.02.
- Home's two conditions for (b'), on the readout cases: (d) does not fall when a window qubit fails (61, 60: (b') does
  not touch the window rulers), and (b) comes back when the faults sit outside the window (0 -> 91 of 96). Both hold.
- Under gate noise (b') does worse than (b): p2 0.02 22 -> 9 of 30, the 3-qubit depolarizing 22 -> 10. Guess (not
  measured): the mirror holds the layers twice, so the qubits it leaves out are the cone's spreading ones, and the
  mean of the rest is less shrunk than the window. [OWNER: home's rule judged (b') on the two readout conditions; with
  the gate-noise rows it is written here as beside]
- Readout flips (q 0.02) hit each mirror once: every mirror ruler's square root misses them; (a) does not.
- Idle dephasing (T2 10 us) moves the |0> mirror far more than the forward circuit (r - sqrt(mirror) +0.086, the VS):
  (b) DIFFERS in every cell; (c), (d) in about half.
- t = 4 with gate noise (p2 0.01, 3 seeds, 9 cells, the VS): (c), (d) AGREES in 4 and 3 of 9, on the other side
  (r - rho positive); (a) in 9 of 9. Coarse.
- The direction without noise: 7 of 96 false words. Uniform depolarizing: WINDOW SHRINKS MORE in every cell (the VS).

## Device procedure (home)

As 11-24: GitHub first (VPN ON), push the declaration. Then the device (VPN OFF), from a fresh notebook clone at the
declaring commit, with psf-os 0.3.3 (e652257) on PYTHONPATH and the sealed answers (9 pairs) outside the repository:
```
python gpu/daily_fetch.py OUT/fetch_in
DEV=$(python gpu/ohm_ruler_night.py pick OUT/fetch_in/queue.json | cut -d' ' -f1)
python gpu/ohm_ruler_night3.py build3 OUT/fetch_in/$DEV/dev OUT/or3 ANSWERS_SEALED OUT/or3_answers --smirrors sc --pairs-t 1:7 3:7 4:9
python gpu/ohm_ruler_night3.py check3 OUT/or3 OUT/or3_answers                  # ALL PASS, or no run
python -m psf_os submit --job OUT/or3/job ; python -m psf_os collect --job OUT/or3/job --wait-min 20
python gpu/ohm_ruler_night3.py score3 OUT/or3 OUT/or3_answers --tau 0.3
```
If the chosen device does not build, the other; if neither builds, no run. Before declaring, the block is run word for
word on a try-build by the workplace VS's `tools/procedure_dry.py` (11-24's first try stopped on a line of this
section).

## Limits

- One device night per declaration; the candidates come from one record, so their worth is read on a new night.
- Candidate 1's tau is set from illustrative noise; a device whose ordinary qubits sit below tau would leave them out
  (the NOT READ rule bounds this).
- Ruler (d) adds 9 or 18 circuits with twice the layers of the test; its own SE is larger than (b)'s on the window.
- Not error correction, not post-selection: every shot counts; the rulers are declared before the data.
