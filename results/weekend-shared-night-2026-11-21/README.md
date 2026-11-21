# The weekend's three tests in one night, 2026-11-21 on ibm_marrakesh (`prereg/weekend_shared_night_2026-11-21.md`)

- Declared in c6184ec3, pushed by the owner before the night's first fetch (01:52:12 CET). Run on the owner's machine
  (`versions.txt`: Python 3.12.13, qiskit 2.5.2, aer 0.17.2, runtime 0.49.0, numpy 2.5.3) from a fresh worktree at
  c6184ec3 with psf-os a164fc5, both checked clean before anything started (PRE_OK). Device record `fetch_in/` (queue
  marrakesh 0, fez 0, kingston 2 -> ibm_marrakesh; calibration 2026-11-21 01:34:04+01:00).
- Built as declared (`A/`: `--cands A --shots 4000 --ff-only --layout own`; `BC/`: `--cands BC --b-n4-from-c --ff-only
  --layout own`); every candidate's own check PASS on every job (`A/check.txt`, `BC/check.txt`). The compiler's CZ
  counts below the written ones at some IPE phases (e.g. phase 0: 0 CZ) are recorded in `checks.json` (record only,
  as every night since 11-20); they are the same for pl, fe and pk at each phase.
- Scored by the declared tool on the owner's machine (`A/score.txt`, `BC/score.txt`, `scores/`); re-scored at home
  (aer 0.18.0): the same words and numbers (B's ceilings differ in the 16th digit).

| job | folder | id | circuits | shots | s model | s charged | RU | created - finished (CET) |
|---|---|---|---|---|---|---|---|---|
| A | `A/job0/` | dc0emu5s2omc73896pgg | 20 | 4000 | 25.3 | 24 | 0.388 | 01:53:12 - 01:53:43 |
| BC0 | `BC/job0/` | dc0emvuq4uuc73a2gmjg | 76 | 1950 | 45.8 | 44 | 0.721 | 01:53:19 - 01:54:30 |
| BC1 | `BC/job1/` | dc0en1ls2omc73896pl0 | 76 | 1950 | 45.8 | 43 | 0.714 | 01:53:26 - 01:55:11 |

Charged 111 s, 1.82 resource units (the model 116.9 s).

## A: the repetition code's four forms (lut3, the four errors pooled; ceiling 0.875)

| form | CZ | carriers | p (2 SE) | ceiling | per error n / d0 / d1 / d2 |
|---|---|---|---|---|---|
| F16 | 16 | 3 | 0.7511 (0.0068) | NOT BEYOND (-0.124) | 0.639 / 0.665 / 0.867 / 0.834 |
| F10 | 10 | 3 | 0.8364 (0.0058) | NOT BEYOND (-0.039) | 0.847 / 0.870 / 0.835 / 0.794 |
| F6P | 10 | 1 | 0.8518 (0.0056) | NOT BEYOND (-0.023) | 0.869 / 0.894 / 0.822 / 0.823 |
| F6 | 6 | 1 | 0.8741 (0.0052) | NOT BEYOND (-0.001) | 0.892 / 0.874 / 0.874 / 0.857 |

- footprint (F6P - F10): +0.0153 (2 SE 0.0081) KEEPS MORE.
- CZ (F6 - F6P): +0.0224 (2 SE 0.0077) KEEPS MORE.
- Reading (the declared table): **both: fewer carriers and fewer CZ each keep more.**
- Beside: F10 - F16 +0.0854 (2 SE 0.0090) KEEPS MORE. F16 reads 0.751 tonight against 0.812 on 2026-11-19 (another
  calibration; tonight's F16 carries a barrier). F6 stands at the ceiling within its 2 SE (0.8741 against 0.875) but
  not beyond it.
- Known limit (declared): the forms differ in depth too; a loss in proportion to time is part of both differences.

## B: phase estimation at n = 4, 5, 6 (plan shape; n = 4 is C's pl)

| n | IPE p (2 SE, shots) | ceiling C(n) | |
|---|---|---|---|
| 4 | 0.8957 (0.0035, 31200) | 0.4706 | BEYOND THE CEILING (+0.425) |
| 5 | 0.8715 (0.0027, 62400) | 0.3792 | BEYOND THE CEILING (+0.492) |
| 6 | 0.8451 (0.0020, 124800) | 0.3065 | BEYOND THE CEILING (+0.539) |

- Log drop per added bit: +0.0274 (4 -> 5), +0.0308 (5 -> 6); acceleration +0.0034 (2 SE 0.0077) **FLAT**. Beside, on
  the share: drops +0.0242, +0.0264, acceleration +0.0022 (2 SE 0.0067) FLAT.
- Reading (the declared table, FLAT and BEYOND at n = 6): **the classical record stays cheap to n = 6: the loss per
  added bit is per round**, not per conditional (20 conditionals at n = 6 against 9 at n = 4). The sensitivity
  declared: about 1 % of the log share per conditional.
- Known limit (declared): the shape is read from two jobs (n = 5 and 40 phases of n = 6 in BC0; the rest in BC1).

## C: where the target waits (IPE n = 4, every phase; all in job BC1)

| form | the target during each wait | p (2 SE) | ceiling 0.4706 |
|---|---|---|---|
| pl | superposition (as sent on 2026-11-19) | 0.8957 (0.0035) | BEYOND |
| fe | \|1> | 0.8914 (0.0035) | BEYOND |
| pk | \|0> | 0.9344 (0.0028) | BEYOND |

- park (pk - pl): +0.0387 (2 SE 0.0045) KEEPS MORE.
- fence (fe - pl): -0.0042 (2 SE 0.0049) SAME WITHIN ERROR.
- Beside: pk - fe +0.0429 (2 SE 0.0045) KEEPS MORE.
- Reading (the declared table): **waiting in |0> keeps more; |1> neither more nor less than the superposition.**

## Against the declaration

| prediction | numbers | |
|---|---|---|
| RC4-1 F16 NOT BEYOND THE CEILING | 0.7511 against 0.875 + 2 SE | held |
| QL-1 IPE BEYOND THE CEILING at n = 4 | 0.8957 against 0.4706 + 2 SE | held |

Every other question was read by its table only (no direction declared). Predictions over the nights of 11-16 to
11-21: 62 declared; 42 held, 20 failed.

## Two numbers side by side

- Vanity: IPE beyond its ceiling at n = 6 by +0.54; the parked IPE reads 0.934 at n = 4.
- Essence: three questions answered on one calibration in 111 s charged, each with the rule it gives psf-os:
  a waiting qubit is parked in |0> (+0.039 on IPE; the fence alone, |1>, gains nothing); the footprint and the CZ
  count both cost (+0.015 and +0.022 on the code); the feedback's classical record does not grow costlier per bit up to
  n = 6. The repetition code's best form still does not pass its ceiling (F6, -0.001).

## Reproduce

`python reproduce.py --psf-os <a164fc5> weekend-shared-night-2026-11-21-A weekend-shared-night-2026-11-21-B
weekend-shared-night-2026-11-21-C` (re-scores each candidate from the raw counts; 3 of 3 SAME at home).

## Independent check (home VS, 2026-11-21)

Re-counted from `job/raw_counts.json` and `job/manifest.json` with qiskit, aer and numpy only (no psf-os, no notebook
scorer; `notes/verify_2026-11-21/weekend_indep.py`): every p, 2 SE and per-error value of A, B and C, the three
comparisons of A and C, B's log drops, acceleration and its declared SE, every word and every reading row agree with
this record. B's n = 4 is read from C's pl (16 items; no item tagged ipe4 in the jobs, nothing counted twice). Sent
as declared: shots 4000 and 1950, 20 / 76 / 76 circuits (each 4 of them the sentinel), no off or floor arm, A on
[0-4], B and C on [0, 1]. C's compiled CZ is the same for pl, fe and pk at every phase, so C's comparisons carry no
CZ difference. Charges 111 s, 1.8223 RU, model 116.9 s. Reproduce 3 of 3 SAME.
