# Analyses A (second part) and D: results (home VS, 2026-11-28)

Run on the committed records (branch synthesis-vs-2026-11-28 from 00889d3f). Nothing under `results/`, `prereg/`,
psf-os or psf-zero is changed. Times CET.

## A2. Predictions declared up to 2026-11-15

`python notes/synthesis_2026-11-28/ledger_a2.py --psf-zero <psf-zero with its full history>` (rows in
`ledger_a2.json`; tables in `ledger_a2_tables.txt` and `.json`).

- 1,419 rows: held 1,052, failed 163, not read 67, unclear 137. Every declared_in place found (1,419 / 1,419); every
  verdict_source found but 26, all `unclear` rows whose reason is that no result exists.
- The rows were read by hand from three sources, in three parts. **The parts are not on one unit**:
  - notebook 10-08 to 10-31 (139) and 11-01 to 11-15 (73): one row per declared prediction with a stated expected
    outcome; rules that only define verdict words (WIN / LOSS, READS, ...) without an expected outcome are left out
    (about 30 and 27 such criteria; the latter listed in `ledger_a2_broader_nov.json`, beside).
  - psf-zero (2026-09-14 to 10-30; 1,207): one row per labelled hypothesis of each preregistration and addendum,
    correctness checks with a stated pass condition included ("byte-identical", "0 fallbacks", a duration bound).
    So its cost, timing, null and beyond-a-bound rows are many; its rates are not to be added to the notebook's.
  - psf-zero's 41 rows of papers 3 and 4 (TOQB declarations as the papers cite them) are left out: the same
    declarations are in the notebook's October part, cited from the declaring files.
- Paper by paper (paper 1 / 2 in psf-zero assigned by addendum range, a judgement; the notebook rows by the paper
  that reports the record):

| paper | declared | held | failed | not read | unclear |
|---|---|---|---|---|---|
| 1 (psf-zero) | 158 | 103 | 24 | 8 | 23 |
| 2 (psf-zero) | 75 | 59 | 6 | 0 | 10 |
| 3 | 26 | 12 | 10 | 1 | 3 |
| 4 | 11 | 10 | 0 | 0 | 1 |
| 5 | 27 | 4 | 19 | 2 | 2 |
| 6 | 3 | 3 | 0 | 0 | 0 |
| 7 | 13 | 2 | 2 | 1 | 8 |
| 8 | 14 | 8 | 2 | 0 | 4 |
| 9 | 22 | 11 | 11 | 0 | 0 |
| none, notebook | 96 | 54 | 14 | 10 | 18 |
| none, psf-zero | 974 | 786 | 75 | 45 | 68 |

- The notebook's 212 by kind (the kinds of `ledger_a.py`, read by hand, and "declared model" added):

| kind | declared | held | failed | not read | unclear |
|---|---|---|---|---|---|
| direction between arms | 63 | 30 | 12 | 7 | 14 |
| declared model | 43 | 15 | 20 | 1 | 7 |
| other | 38 | 24 | 4 | 2 | 8 |
| beyond a bound | 31 | 16 | 11 | 1 | 3 |
| null (no difference) | 26 | 12 | 10 | 1 | 3 |
| cost | 5 | 4 | 0 | 1 | 0 |
| trend over size | 4 | 1 | 1 | 1 | 1 |
| timing | 2 | 2 | 0 | 0 | 0 |

- `ledger_a.py`'s pattern rules give the hand kind on 260 of 1,419 rows: they were written for the night READMEs'
  verdict words (11-16 on) and do not fit the earlier files' sentences; the hand kind is the column used.
- Unclear (137): the record says AMBIGUOUS / NOT DECIDED / PARTLY (psf-zero 36 + about 20 mixed readings;
  notebook 4); an addendum or result gives no verdict for that label (27 psf-zero; notebook about 15); no result
  found (draft never declared or not run: HW3 D1-D3, P3D A1-A4 / C1 / C2 whose results file is not on this disk, W13,
  T2-placement draft); a two-branch prediction matching neither branch (du91r-3); a criterion changed later.
- Not read (67): harness gate failed or "not scored" (30, psf-zero); withdrawn or cancelled (C55-VAL 8, T2*/ZZ 5,
  heisC / heisD 3, loop-long N1-N6); declared "reported, not judged" (test 2, test 3, QELM Q3b).
- Checks: 20 rows drawn at random (12 notebook, 8 psf-zero) read against their cited lines: every verdict as the
  record states it; one line number corrected (schw), two verdict sources found by hand (C49-VAL V2, C61-VAL T7).

## D. The same circuit from day to day

`python notes/synthesis_2026-11-28/spread_d.py --json notes/synthesis_2026-11-28/spread_d.json`. The counting is the
one fixed in home's instruction before the run. Shot SEs from the raw counts (per-shot sums over the qubits, their
correlations included); the circuits as sent checked equal gate by gate.

| unit | days | chi2 (df) | p | SD / median s | word |
|---|---|---|---|---|---|
| FX-A ibm_marrakesh (M - M_exact; same circuit, same qubits) | 11-05, 06, 14, 15, 16 | 29.1 (4) | 7e-6 | 2.71 | LARGER THAN SHOT NOISE |
| FX-A ibm_fez (same circuit, copy drow 4) | 11-05, 07, 14 | 2.10 (2) | 0.35 | 1.03 | WITHIN SHOT NOISE |
| FX-A ibm_kingston | 11-16 | - | - | - | beside (one day) |
| Ohm rulers, raw W per cell, 11-25 / 11-26 (165 of 165 user circuits equal) | 2 | 1.3 to 19.7 (1) | | 1.1 to 4.4 | 8 of 9 LARGER (A2 t1 within) |
| Ohm rulers, ruler (d)'s d per cell, 11-25 / 11-26 | 2 | 0.00 to 2.9 (1) | 0.09 to 0.96 | 0.05 to 1.7 | 0 of 9 LARGER |
| Ohm rulers, raw W, 11-24 / 25 / 26 on the 7 shared pairs (135 of 135 equal) | 3 | 4.1 to 52.9 (2) | | 1.4 to 5.2 | 7 of 9 LARGER (A0 t1, A2 t1 within) |
| balanced chain, pooled per L, 11-17 / 11-18 (30 of 30 equal; a recalibration between) | 2 | 150 to 585 (1) | < 1e-30 | 12 to 24 | 5 of 5 LARGER |
| beside: copies inside one job (loopvar 11-20, LV-1) | 2 copies | 0.02 to 3.4 (1) | 0.07 to 0.90 | 0.13 to 1.8 | 0 of 9 LARGER |
| beside: three jobs a minute apart (loopvar 11-20) | 3 jobs | 0.95 to 10.2 (2) | | 0.7 to 2.3 | 1 of 3 LARGER (L 2) |

- Summary: across days, the raw value moved beyond shot noise in 14 of 16 primary units (FX-A 1 of 2, raw W 8 of
  9, balanced 5 of 5); copies inside one job in 0 of 9. On the ruler nights the raw W of 11-26 is above 11-25's in
  all nine cells (+0.006 to +0.045), and ruler (d)'s d moves within its SE in all nine.
- Limits: two days give one degree of freedom; (d)'s SE carries the string mirrors' shot noise as well, so it is
  larger than raw W's (SD / median s still at most 1.7); FX-A's SE from the per-shot mean agrees with psf-os's two_se
  (0.0056 against 0.0054 at 2 SE on 11-14 marrakesh); the balanced values and SEs are the record's, the others
  re-counted (each equal to the record's value).

## A, all periods on the notebook's unit (home, 2026-11-28, after the merge)

The notebook's rows only (one row per declared prediction with a stated expected outcome): `ledger_a2.json` parts
"notebook 10-08 to 10-31" and "notebook 11-01 to 11-15" with `ledger_a.json` (11-16 to 11-27). psf-zero's 1,207 rows
count hypotheses and correctness checks on another unit and are reported apart, never added to these. Kinds: by hand
up to 11-15 (the VS), by `ledger_a.py`'s rules from 11-16.

| period | declared | held | failed | not read | unclear | failed / (held + failed) |
|---|---|---|---|---|---|---|
| 10-08 to 10-31 | 139 | 70 | 38 | 9 | 22 | 0.35 |
| 11-01 to 11-15 | 73 | 34 | 20 | 5 | 14 | 0.37 |
| 11-16 to 11-19 (paper 10's nights) | 57 | 37 | 20 | 0 | 0 | 0.35 |
| 11-20 to 11-27 (grounded predictions only) | 18 | 17 | 0 | 1 | 0 | 0.00 |
| all | 287 | 158 | 78 | 15 | 36 | 0.33 |

| kind | declared | held | failed | failed / (held + failed) |
|---|---|---|---|---|
| declared model (a noise model, a volume, an expected number) | 43 | 15 | 20 | 0.57 |
| direction between arms | 78 | 40 | 17 | 0.30 |
| beyond a bound | 62 | 40 | 18 | 0.31 |
| null (no difference) | 40 | 23 | 13 | 0.36 |
| other kinds (trend, timing, loop, cost, per-qubit, other) | 64 | 40 | 10 | 0.20 |

- For six weeks about a third of the decided predictions failed, period after period (0.35, 0.37, 0.35); then, once
  only grounded predictions were declared, none of 17 decided did. The second number is a change in what was
  predicted (said in `results_ab.md`), not a better model of the device: the declared models themselves failed most
  often (20 of 35 decided).
- Unclear (36) and not read (15) stay out of the rates and are listed with their reasons in the ledgers.
