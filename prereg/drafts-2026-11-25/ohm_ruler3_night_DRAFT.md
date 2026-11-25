# DRAFT (not declared): Ohm with rulers inside the circuit, the third night (Heron)

Workplace Claude, 2026-11-25, on home's instruction "オームの物差し、次の晩の宣言の下書き" and the 11-24 record
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

## Circuits (unchanged from 11-24 unless a candidate is taken)

- The 11-24 plan B: A0, A1, A2 on the 40-qubit chain's light-cone circuits L of the window (positions 20 .. 20 + 2t - 2),
  t = 1, 3, 4; the 11-12 string generator with seed **20261124**, kept when |T0| >= 6 on each t >= 3 cone; K = 7 pairs
  (the same 14 strings as 11-24: `strings` gives them by hash).
- One |0> mirror per (arm, t) on s00, as 11-24 (rulers (b), (c)).
- [Candidate 2] Two string mirrors per (arm, t): s00 -> U U^dagger -> s00 and c00 -> U U^dagger -> c00. Built as the
  compiled circuit, a barrier, its inverse, a barrier, then X on the physical qubits whose bit is 1, then Z readout
  (the compiled circuit prepares the string, so its inverse returns |0>; the final X returns the string). Ideal:
  <Z_q> = 1 - 2 b_q. 18 circuits for 9 cells. [OWNER: home's note counts 9; one mirror per cell from s00 alone (ruler
  (d1), 9 circuits) keeps the even part of the readout in the ruler, see Rulers]
- No floors; no mid-circuit measurement, no delay (nothing to park; the build records it).
- [OWNER] Pairs per t (Job and seconds): 7 everywhere (as 11-24), or 9 at t = 4 alone (the next draws of the same rule).

## The rulers (rule 3; written before the data)

Per pair k and chain position q, O_kq = (Z_s - Z_c) / 2; W_k = -sum_{q in window} O_kq / 2 + const_k (11-24's identity).
Each ruler gives a rho; W_x,k is W_k with O_device replaced by O_device / rho_x (rho per pair for (a), per cell for the
mirrors). Without noise every rho is 1 and every W_x equals W_exact.

- **(a) the circuit's total** (as 11-24): rho_a,k = T_device,k / T0_k. Read at t >= 3.
- **(b) the |0> mirror** (as 11-24): rho_b = sqrt(mean over the circuit's qubits of the mirror's <Z>).
- **(c) the |0> mirror on the window** (11-24's beside, now declared): rho_c = sqrt(mean over the window's qubits).
- **[Candidate 2] (d) the string mirror on the window**: per qubit, m_q = (Z^m_s,q - Z^m_c,q) / 2 x (1 - 2 b_s00,q), the
  odd part of the two string mirrors, ideal 1. rho_d = sqrt(mean over the window's qubits of m_q).
  - The odd part cancels what the two strings share (a readout or decay offset the same for s and c); what a |1> suffers
    more than a |0> stays in m_q only through the difference, which is what the test's own odd part carries.
  - [OWNER alternative (d1), 9 circuits] m_q = Z^m_s,q x (1 - 2 b_s00,q) from s00 alone.
- The SE of each mirror ruler adds its mirror's shot noise on the averaged qubits (per-shot mean, as 11-24), propagated
  through the square root.
- **[Candidate 1] the per-qubit mirror rule.** A qubit whose mirror value (the |0> mirror's <Z_q> for (b) and (c); m_q for
  (d)) is below **tau** is left out of that ruler's mean, not out of the circuit or of W.
  - tau is fixed here from the dry runs (noise-free and the illustrative noises), never from a device record: the
    proposal is tau = **0.3** [OWNER], below the lowest per-qubit mirror value of every illustrative noise at t <= 4
    except the "a few qubits fail" case (the VS's dry runs, その2, give the margins).
  - When fewer than half of the averaged qubits are left, the ruler is NOT READ for that cell.
  - For (a), the rule is not applied (the conservation holds on the whole circuit only). [OWNER: or (a) over the kept
    qubits with the exact kept total from the answers, rho_a' = sum_kept O_device / sum_kept O_exact]
- The words of every ruler, per cell: d_x = mean_k (W_x,k - W_exact,k); AGREES when |d_x| < t_{0.975,K-1} SE (K = 7:
  2.447; K = 9: 2.306), DIFFERS otherwise; NOT READ when SE = 0 (rule 5) or when candidate 1 leaves too few qubits.
  The 2 SE word is written beside.

## [Candidate 3] the direction column r - rho_a

- Per pair: r_k = sum_{q in window} O_device,kq O_exact,kq / sum_{q in window} O_exact,kq^2 (the window's own factor;
  positions with sum_k O_exact^2 below 0.05 K take no part, as 11-24); delta_k = r_k - rho_a,k.
- Per cell: delta = mean_k delta_k, SE from the pairs' scatter, t quantile as above.
- Word (t >= 3): WINDOW SHRINKS LESS when delta > t SE; WINDOW SHRINKS MORE when delta < -t SE; NOT SEEN otherwise; NOT
  READ when SE = 0.

## Job and seconds (2.6 s + 0.000269 s x circuits x shots; psf-os's model beside; 11-24 ran plan B in 39 s)

| plan [OWNER] | pairs (t = 1, 3 / t = 4) | mirrors | circuits | shots | seconds (formula) | psf-os model |
|---|---|---|---|---|---|---|
| B (11-24) | 7 / 7 | 9 | 139 | 1000 | 40.0 | 45.5 |
| B + d | 7 / 7 | 9 + 18 | 157 | 1000 | 44.8 | 51.0 |
| B + d1 | 7 / 7 | 9 + 9 | 148 | 1000 | 42.4 | 48.3 |
| B9 at t = 4 | 7 / 9 | 9 | 151 | 1000 | 43.2 | (not try-built) |
| B9 at t = 4 + d | 7 / 9 | 9 + 18 | 169 | 1000 | 48.1 | (not try-built) |

Candidates 1 and 3 add no circuit. Try-builds on the 11-23 ibm_fez record (`notes/ohm_ruler3_2026-11-25`), each checked
ALL PASS by `check3`. `build3 --smirrors none` gives byte for byte the declared tool's job (circuits.qpy equal). The B9
rows need 9-pair answers (the same rule's next draws); their seconds are from the formula.

### The smallest difference each cell can see (planning numbers; from the 11-24 record's SEs, not a ruler)

t SE with the 11-24 scatter: at t = 3 ruler (b) 0.03 to 0.05 (7 pairs, t 2.447); at t = 4 0.11 to 0.14. With 9 pairs at
t = 4 the SE shrinks by sqrt(7/9) and the quantile is 2.306: 0.09 to 0.12. Each cell's own t SE is written beside the
words.

## Device and placement (no quality number)

- As 11-24: of ibm_fez and ibm_kingston, the one with fewer pending jobs; not ibm_marrakesh; the chain by
  `gpu/hub_build.py`'s rule. The device record's lengths of time are read by psf-os 0.3.3; no error number is read.
- The sentinel: written beside with the overlap of its qubits with the user's (`build.json`); when the overlap is 0 the
  record says NOT ON USER QUBITS (11-24: 0). psf-os is not changed.

## Answers (sealed), pre-run check

- As 11-24 (`answers`), the same strings: plan B's answers are 11-24's (sha256 59cbd7a0...). With 9 pairs at t = 4, new
  answers (sha256 written here at declaration).
- `check OUT ANS`, noise-free on the compiled circuits: as 11-24; every |0> mirror all |0> within 1e-6; [candidate 2]
  every string mirror equal to its string (<Z_q> = 1 - 2 b_q within 1e-6) and m_q = 1. ALL PASS or no run.

## Verdicts (`score3 OUT ANS`) [OWNER]

Per cell, over the K pairs:
- raw M, W, S as 11-24 (READS at a ratio of 0.5 or below);
- rulers (a), (b), (c), [(d)]: AGREES / DIFFERS / NOT READ (t quantile; 2 SE beside);
- one factor on the window (t >= 3), as 11-24 (UNIFORM at p >= 0.05; NOT READ with fewer than 2 positions or a 0 SE);
- [candidate 3] the direction word;
- beside, never judged: the order of W and the ruled W at t = 3, 4 (A0 > A1 > A2); W(t) / W(1); each ruler's t SE (the
  smallest difference the cell could see); [candidate 1] the qubits left out, per ruler and cell; the sentinel and its
  overlap with the user's qubits.

## Reading tables (fixed before the data; every combination on one row) [OWNER]

Table A, which rulers read the transfer (per cell at t >= 3). Each ruler's word is read on its own row:

| ruler | AGREES | DIFFERS | NOT READ |
|---|---|---|---|
| (a) total | the circuit's total carries the window's shrink | it does not | - |
| (b) mirror | the mirror's mean carries it | it does not | candidate 1 left too few qubits |
| (c) window mirror | the mirror on the window carries it | it does not | candidate 1 left too few qubits |
| (d) string mirror | the string mirror on the window carries it | it does not | candidate 1 left too few qubits |

Table B, the direction (candidate 3; per cell at t >= 3; 3 words x ruler (a) 2 words = 6 rows; the reading uses the
row's conditions only):

| direction | ruler (a) | reading |
|---|---|---|
| WINDOW SHRINKS LESS | DIFFERS | the window keeps more of its odd part than the circuit's total: the total overstates the window's shrink |
| WINDOW SHRINKS LESS | AGREES | the window keeps more than the total, within what ruler (a)'s word can see |
| WINDOW SHRINKS MORE | DIFFERS | the window loses more than the total: the total understates the window's shrink |
| WINDOW SHRINKS MORE | AGREES | the window loses more than the total, within what ruler (a)'s word can see |
| NOT SEEN | DIFFERS | no lean between window and total is seen, yet ruler (a) differs: the window's shrink is not one factor (read with the one-factor word) |
| NOT SEEN | AGREES | the window and the total shrink alike |

The raw words keep 11-23's meaning. The one-factor word is read on its own line, as 11-24.

## Predictions [OWNER] (candidates; each grounded on the 11-24 record, written after it was seen)

- OR3-1: the raw W READS at t = 3 in every arm (11-24: 0.050, 0.119, 0.261).
- OR3-2 [only with candidate 3]: at t = 3 the direction is WINDOW SHRINKS LESS in every arm (11-24 beside: r - rho_a
  +0.03 to +0.12 in all 6 cells). The weakest ground: one night, and the dry runs' gate-noise model leaned the other way.
- No prediction for rulers (c), (d) or for t = 4.

## Dry runs (no device; `notes/ohm_ruler3_2026-11-25/` and the workplace VS's その2)

Plan B + d, built on the 11-23 ibm_fez record; `dry3.py` samples every circuit noise-free (the sentinel not sampled)
and adds ILLUSTRATIVE readout-like faults written by hand, at chain positions chosen by hand (not where any device's
qubits failed). 16 seeds per case; t >= 3, 96 cells per row; AGREES at the t quantile (2 SE in brackets):

| case | (a) | (b) | (c) | (d) | (d1) | (b), tau 0.3 | (d), tau 0.3 |
|---|---|---|---|---|---|---|---|
| no noise | 92 (87) | 92 (87) | 92 (87) | 92 (87) | 92 (87) | 92 (87) | 92 (87) |
| positions 15, 18, 22: 1 read as 0 with 0.4 | 73 (68) | 30 (26) | 30 (26) | 61 (57) | 30 (26) | 30 (26) | 61 (57) |
| the same with 0.8 | 69 (66) | 31 (27) | 31 (27) | 60 (52) | 31 (27) | 31 (27) | 31 (27) |
| positions 14, 17, 18 (outside the window): both ways 0.4 | 67 (62) | 0 (0) | 92 (87) | 92 (87) | 92 (87) | 91 (86) | 92 (87) |
| every bit flips with 0.02 | 91 (89) | 2 (0) | 3 (1) | 1 (0) | 1 (0) | 2 (0) | 1 (0) |

- Rule 4 halves the false words: without noise 4 of 96 DIFFERS at the t quantile, 9 of 96 at 2 SE.
- A fault that a |1> suffers and a |0> does not is seen by (d) only (rho_d 0.965 and 0.929; rho_b, rho_c, rho_d1 1.000).
- Candidate 1 helps (b) when the faulty qubits sit outside the window (0 -> 91 of 96) and harms (d) when a faulty qubit
  sits in the window (60 -> 31 of 96 at q 0.8: the window's W carries that qubit's shrink). [OWNER: a rule that leaves
  out only qubits outside the window keeps the first and avoids the second; not built]
- Uniform readout flips hit each mirror once: every mirror ruler's square root misses them, (a) does not.
- The direction without noise: 7 of 96 false words. With the faults outside the window: WINDOW SHRINKS LESS 34 of 96.
- Gate noise, amplitude damping, idle dephasing and "a few qubits fail" under gate noise: the workplace VS's その2
  (pod), filled when it returns.

## Device procedure (home)

As 11-24: GitHub first (VPN ON), push the declaration. Then the device (VPN OFF), from a fresh notebook clone at the
declaring commit, with psf-os 0.3.3 (e652257) on PYTHONPATH and the sealed answers outside the repository:
```
python gpu/daily_fetch.py OUT/fetch_in
DEV=$(python gpu/ohm_ruler_night.py pick OUT/fetch_in/queue.json | cut -d' ' -f1)
python gpu/ohm_ruler_night3.py build3 OUT/fetch_in/$DEV/dev OUT/or3 ANSWERS_SEALED OUT/or3_answers --smirrors sc
python gpu/ohm_ruler_night3.py check3 OUT/or3 OUT/or3_answers                  # ALL PASS, or no run
python -m psf_os submit --job OUT/or3/job ; python -m psf_os collect --job OUT/or3/job --wait-min 20
python gpu/ohm_ruler_night3.py score3 OUT/or3 OUT/or3_answers --tau 0.3
```
[OWNER] `--smirrors sc` (candidate 2, 18 circuits), `s` (d1, 9) or `none` (no string mirror: the declared tool's job,
byte for byte); with 9 pairs at t = 4, `--pairs-t 4:9` and 9-pair answers. If the chosen device does not build, the
other; if neither builds, no run. Before declaring, the block is run word for word on a try-build by the workplace
VS's `tools/procedure_dry.py` (11-24's first try stopped on a line of this section).

## Limits

- One device night per declaration; the candidates come from one record, so their worth is read on a new night.
- Candidate 1's tau is set from illustrative noise; a device whose ordinary qubits sit below tau would leave them out
  (the NOT READ rule bounds this).
- Ruler (d) adds 9 or 18 circuits with twice the layers of the test; its own SE is larger than (b)'s on the window.
- Not error correction, not post-selection: every shot counts; the rulers are declared before the data.
