# Phase estimation parked by psf-os 0.3.1 at n = 6, 7, 8, 2026-11-22 on ibm_fez (`prereg/qpe_n78_night_2026-11-22.md`)

- Declared in 86f9a37c, pushed by the owner before the night's first fetch (11:56:49 CET). Run on the owner's machine
  (`versions.txt`: Python 3.12.13, qiskit 2.5.2, aer 0.17.2, runtime 0.49.0, numpy 2.5.3) from a fresh worktree at
  86f9a37c with psf-os 0.3.1 as released (v0.3.1, 7caedaa), both checked clean and the version checked (PRE_OK).
- Device: `fetch_in/queue.json` pending marrakesh 0, fez 0, kingston 2; the rule -> **ibm_fez**, calibration
  2026-11-22 11:14:37+01:00.
- Built as declared (`--plan b`); check PASS (`qn/check.txt`): `psf_os_build` 0.3.1, park and park_likely stated;
  C(6) 0.3065, C(7) 0.2480, C(8) 0.2007; the 16 phases' compiled CZ mean 11.12 / 13.12 / 15.12 against every phase's
  11.00 / 13.00 / 15.00; every parked item fenced with its target and ancilla, every twin unparked.
- Scored by the declared tool on the owner's machine (`qn/score.txt`, `qn/qpe78_scores.json`); re-scored at home
  (aer 0.18.0): the same text.

| job | folder | id | circuits | shots | s model | s charged | RU | created - finished (CET) |
|---|---|---|---|---|---|---|---|---|
| job0 | `qn/job0/` | dc1clr6q4uuc73a3opi0 | 64 | 1950 | 39.0 | 37 | 0.604 | 11:58:52 - 11:59:40 |

## Results

| n | parked, 16 phases (2 SE) | C(n) | | 4 twin phases: parked - unparked (2 SE) | |
|---|---|---|---|---|---|
| 6 | 0.5785 (0.0056) | 0.3065 | BEYOND THE CEILING (+0.272) | +0.0499 (0.0158) | KEEPS MORE |
| 7 | 0.5097 (0.0057) | 0.2480 | BEYOND THE CEILING (+0.262) | +0.0108 (0.0159) | SAME WITHIN ERROR |
| 8 | 0.4236 (0.0056) | 0.2007 | BEYOND THE CEILING (+0.223) | -0.0117 (0.0152) | SAME WITHIN ERROR |

- **Reading (the declared table): n = 8 BEYOND, n = 7 BEYOND, parking at n = 8 SAME WITHIN ERROR -> "the range
  reaches n = 8; parking's gain is not seen at n = 8 at this shot noise."**
- The tool's own "reading" line (`qn/score.txt`) follows the draft's table, which was keyed on the shape; the
  declaration made the shape beside and replaced that table. The declared row above holds.
- Beside, never read for the row: the shape on the log of the share: drops +0.1266 (6 -> 7), +0.1851 (7 -> 8),
  acceleration +0.0584 (2 SE 0.0276), the word ACCELERATES. The loss per added bit grew from n = 6 to n = 8 on this
  night, larger than the dry runs' accelerations.
- Beside, never judged: the declared expectation (an extrapolation from marrakesh 2026-11-21) put P(8) near 0.72;
  tonight reads 0.42 on another device and calibration. Parking at n = 6 keeps +0.050, as on marrakesh at n = 4 to 6
  (+0.031 to +0.039), and is not seen at n = 7 and 8 on 4 phases.

## Against the declaration

| prediction | numbers | |
|---|---|---|
| QN-1 the parked IPE BEYOND THE CEILING at n = 6 | 0.5785 against 0.3065 + 2 SE | held |

n = 7 and 8 and the shape: no direction declared. Predictions over the nights of 11-16 to 11-22: 68 declared; 48
held, 20 failed.

## Two numbers side by side

- Vanity: phase estimation beyond its ceiling at n = 8 (0.424 against 0.201), the longest n run so far.
- Essence: the range reaches n = 8 above the ceiling, but the share falls from 0.58 to 0.42 between n = 6 and 8 and
  the loss per added bit grows (beside); parking's gain, clear at n = 6, is not seen at n = 7 and 8 on four twin
  phases. Widening the range further on this device would pay more per bit; 37 s charged.

## Reproduce

`python reproduce.py --psf-os <psf-os 0.3.1> qpe-n78-night-2026-11-22` (1 of 1 SAME at home).
