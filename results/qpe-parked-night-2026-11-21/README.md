# Phase estimation with the waiting target parked, 2026-11-21 on ibm_marrakesh (`prereg/qpe_parked_night_2026-11-21.md`)

- Declared in 4babc421, pushed by the owner before the night's first fetch (10:59:06 CET). Run on the owner's machine
  (`versions.txt`: Python 3.12.13, qiskit 2.5.2, aer 0.17.2, runtime 0.49.0, numpy 2.5.3) from a fresh worktree at
  4babc421 with psf-os 0.3.0 (release-0.3.0 at cedd90d), both checked clean and the version checked before anything
  started (PRE_OK). Device record `fetch_in/` (queue marrakesh 1, fez 5, kingston 0 -> ibm_marrakesh; calibration
  2026-11-21 10:39:07+01:00, not the weekend night's 01:34:04).
- The first device run of psf-os 0.3.0's default. Built as declared (`--plan subset`); every manifest records
  `psf_os_build` version 0.3.0, park True, park_set explicit. Check PASS on both jobs, "park records as meant"
  (`qp/check.txt`). Compiled CZ below the written at some phases is recorded in `checks.json` (record only); it is
  the same for a parked phase and its unparked twin.
- Scored by the declared tool on the owner's machine (`qp/score.txt`, `qp/parked_scores.json`); re-scored at home
  (aer 0.18.0): the same text.

| job | folder | id | circuits | parked / unparked | shots | s model | s charged | RU | created - finished (CET) |
|---|---|---|---|---|---|---|---|---|---|
| job0 | `qp/job0/` | dc0mngqnj2vs73de7trg | 72 | 51 / 17 | 1950 | 43.5 | 41 | 0.678 | 11:00:36 - 11:01:26 |
| job1 | `qp/job1/` | dc0mnkts2omc7389grg0 | 72 | 61 / 7 | 1950 | 43.5 | 42 | 0.688 | 11:00:51 - 11:02:06 |

Charged 83 s, 1.37 resource units (the model 87.0 s). Each job holds one sentinel (4 circuits).

## Results

| n | parked, every phase (2 SE) | ceiling C(n) | | 8 paired phases: parked - unparked (2 SE) | |
|---|---|---|---|---|---|
| 4 | 0.8742 (0.0038) | 0.4706 | BEYOND THE CEILING (+0.404) | 0.9037 - 0.8688 = +0.0349 (0.0072) | KEEPS MORE |
| 5 | 0.8391 (0.0029) | 0.3792 | BEYOND THE CEILING (+0.460) | 0.8990 - 0.8678 = +0.0312 (0.0073) | KEEPS MORE |
| 6 | 0.8006 (0.0023) | 0.3065 | BEYOND THE CEILING (+0.494) | 0.8908 - 0.8522 = +0.0386 (0.0076) | KEEPS MORE |

- Parked shape (every phase): log drops +0.0410 (4 -> 5), +0.0469 (5 -> 6); acceleration +0.0059 (2 SE 0.0087)
  **FLAT**.
- Reading (the declared table, row 1): **parking keeps more at every n, and the parked loss per added bit is per
  round.**
- Beside, never judged: the parked form reads higher on the paired phases (0, step, 2 step, ...) than on every phase
  (0.904 against 0.874 at n = 4; 0.845 on the other phases). Many paired phases are cut to fewer CZ by the compiler:
  phase 0 to none, 6.0 CZ on average against 8.0, 10.0 and 11.7 on the other phases at n = 4, 5, 6 (at n = 4, phases
  2, 6, 10 and 14 keep their 8). A phase and its twin have the same compiled CZ, so no verdict carries it.
  Tonight's parked IPE over every phase (0.874 at n = 4) reads below the weekend's unparked over every phase
  (0.896). That is another calibration; inside tonight's jobs the parked form
  keeps more at every n. Across nights nothing is compared.

## Against the declaration

| prediction | numbers | |
|---|---|---|
| QP-1 parking KEEPS MORE at n = 4 | +0.0349 (2 SE 0.0072) on the 8 paired phases | held |
| QP-3 the parked IPE BEYOND THE CEILING at n = 4, 5 and 6 | +0.404, +0.460, +0.494 beyond | held |

QP-2 (parking at n = 5, 6) and the parked shape: no direction declared; read by the table (KEEPS MORE at both, FLAT).
Predictions over the nights of 11-16 to 11-21: 64 declared; 44 held, 20 failed.

## Two numbers side by side

- Vanity: the parked IPE beyond its ceiling at n = 6 by +0.49.
- Essence: psf-os 0.3.0's default, sent as it now builds, keeps +0.031 to +0.039 at n = 4, 5, 6 against the same
  circuit unparked in the same job (two nights, two calibrations: the weekend's C +0.0387 at n = 4 and tonight). 83 s
  charged. One device and one circuit family (IPE) still.

## Reproduce

`python reproduce.py --psf-os <psf-os 0.3.0> qpe-parked-night-2026-11-21` (1 of 1 SAME at home).

## Independent check (home VS, 2026-11-21 evening)

Re-counted from `job/raw_counts.json` and `job/manifest.json` with qiskit, aer and numpy only (no psf-os, no notebook
scorer; `notes/verify_2026-11-21/parked_indep.py`): every p, 2 SE, paired difference, ceiling, log drop and the
acceleration with its declared SE, every word and the reading row agree with this record. The 24 pairs are on the
declared phases and each pair is inside one job, with equal compiled CZ. Sent as declared: 1950 shots, 72 + 72
circuits, ff only, `psf_os_build` 0.3.0 / park True / explicit; followed branch by branch, the n = 4 parked circuits
hold the target in |0> at every wait and are the weekend C's 16 pk circuits exactly. Charges 83 s, 1.3656 RU, model
87.0 s. Reproduce 1 of 1 SAME with psf-os 0.3.0. One wording corrected: the paired phases' CZ (above; the first text
said every paired phase is cut, and four at n = 4 are not).
