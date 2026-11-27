# Paper 12: the numbers the text uses, and where each comes from (workplace, 2026-11-27)

One row per number. `source` is a file in the notebook at the stated ref (`HEAD` = this branch's base c32e1f56, which
equals home's main for these files; `calib` = the workplace VS's branch calib-compare2-2026-11-27 at 786ae051, now in
home's main). `literal` is a string that stands word for word in the source and carries the number;
`numbers_check.py` checks every literal (exit 1 on any miss). Rows marked `[NIGHT 5]` are filled after the fifth night.
Numbers from outside the notebook (the twirl dry runs) are marked `PENDING COMMIT` until home commits them.

| id | value | used in | ref | source | literal |
|---|---|---|---|---|---|
| ow-reads | 24 of 24 cells READS (11-23) | 3.1 | HEAD | results/ohm-window-night-2026-11-23/README.md | Window M and window W: **READS in all 24 cells.** |
| ow-ow1 | OW-1 held, 0.011 / 0.028 / 0.048 | 3.1 | HEAD | results/ohm-window-night-2026-11-23/README.md | **OW-1 (at t = 3, the window's M READS on F in all three arms): held** (0.011 / 0.028 / 0.048) |
| or1-w | W excess +0.142 .. +0.467 at t >= 3 (11-24) | 3.1 | HEAD | results/ohm-ruler-night-2026-11-24/README.md | \| A1 t = 4 \| 0.289 READS \| 0.286 READS \| 1.190 / 0.723 \| +0.467 (0.082) \| |
| or3-w | W excess +0.153 .. +0.337 at t >= 3 (11-25) | 3.1 | HEAD | results/ohm-ruler3-night-2026-11-25/README.md | \| A2 t = 4 \| 9 \| 0.401 READS \| 0.403 READS \| 0.649 / 0.312 \| +0.337 (0.161) \| |
| or4-a2t4 | A2 t = 4 raw M 0.529, W 0.526, DOES NOT READ (11-26) | 3.1 | HEAD | results/ohm-ruler4-night-2026-11-26/README.md | \| A2 t = 4 \| 0.529 DOES NOT READ \| 0.526 DOES NOT READ \| 0.684 / 0.312 \| +0.372 (0.197) \| |
| or4-reads | 17 of 18 raw cells READS (11-26) | 3.1 | HEAD | results/ohm-ruler4-night-2026-11-26/README.md | 17 of 18 raw cells READS |
| or1-a | (a) DIFFERS in every cell read (11-24) | 3.2 | HEAD | results/ohm-ruler-night-2026-11-24/README.md | Ruler (a) is below the exact value in every cell where it was read |
| or3-counts | (d) 5, (c) 5, (b) 3, (a) 2 of 6 at t >= 3 (11-25) | 3.2 | HEAD | results/ohm-ruler3-night-2026-11-25/README.md | At t >= 3: (d) AGREES in five of six cells, (c) in five, (b) in three |
| or4-counts | (de) 4 of 6, (a') 2 of 6 (11-26) | 3.2 | HEAD | results/ohm-ruler4-night-2026-11-26/README.md | At t >= 3: (de) AGREES in four of six cells |
| or4-de-d | (de)'s \|d\| below (d)'s in all six cells (11-26) | 3.3 | HEAD | results/ohm-ruler4-night-2026-11-26/README.md | (de)'s \|d\| is smaller than (d)'s in all six |
| or4-tpos | t = 3 d positive for every ruler and arm, +0.021 to +0.110 (11-26) | 3.4 | HEAD | results/ohm-ruler4-night-2026-11-26/README.md | d is positive at t = 3 for every ruler and arm (+0.021 to +0.110) |
| or3-dpos | (d) d positive at t >= 3, +0.02 to +0.05 (11-25, per-qubit (d)) | 3.4 | HEAD | results/ohm-ruler3-night-2026-11-25/README.md | its d stays positive at t >= 3 (+0.02 to +0.05) |
| dry4-ro1 | one-sided readout 0.02: (d) 43, (de) 93 of 96 (dry runs) | 3.3 | HEAD | prereg/ohm_ruler4_night_2026-11-26.md | \| every position: 1 read as 0 with 0.02 (one-sided) \| 91 (88) \| 91 (88) \| 5 (2) \| 5 (2) \| 5 (2) \| 43 (32) \| 94 (91) \| 93 (87) \| 88 \| |
| or42 | OR4-2 held (104, 102; third night) | 3.6 | HEAD | results/ohm-ruler4-night-2026-11-26/README.md | OR4-1 and OR4-2 held |
| q104 | 104 A0 t = 4: mirror 0.05, r 0.846, e 0.989 | 3.6 | HEAD | results/ohm-ruler4-night-2026-11-26/qubits.csv | ,28,104,False,0.05,0.027,0.846,0.989, |
| cc-memo | memo a11c510b, addendum cd698ebe, 191 snapshots | 3.7 | calib | notes/calib_compare_2026-11-26/result_2026-11-27.md | 191 snapshots, all `ok` in its index |
| cc-cz | CZ 2.29 x chance (mirror_low), 1.73 x (scan_listed) | 3.7 | calib | notes/calib_compare_2026-11-26/result_2026-11-27.md | held for mirror_low (cz 2.29 x chance |
| cc-ro | fez readout_error 2.48 x (mirror_low); T1 1.62 x | 3.7 | calib | notes/calib_compare_2026-11-26/result_2026-11-27.md | nor for readout_error on fez (mirror_low 2.48 x |
| cc-104 | fez 104 found 68 times, no IBM mark | 3.7 | calib | notes/calib_compare_2026-11-26/result_2026-11-27.md | fez mirror_low: **104 (68 times)** |
| cc-age | marrakesh 17 of 67 jobs on a map over 24 h old | 3.7 | calib | notes/calib_compare_2026-11-26/result_2026-11-27.md | on marrakesh 17 of 67 jobs ran on a map more than 24 h old |
| cc-day | readout error day-to-day 3.30 / 3.54 / 7.81 | 3.7 | calib | notes/calib_compare_2026-11-26/result_2026-11-27.md | 3.30 / 3.54 / 7.81 for readout_error |
| ver-1 | largest difference 3.3e-16 (11-24) | 3.8 | HEAD | results/ohm-ruler-night-2026-11-24/README.md | difference 3.3e-16 |
| ver-3 | largest difference 5.7e-14 (11-25) | 3.8 | HEAD | results/ohm-ruler3-night-2026-11-25/README.md | largest difference 5.7e-14 |
| ver-4 | largest difference 1.1e-16 (11-26) | 3.8 | HEAD | results/ohm-ruler4-night-2026-11-26/README.md | 1.1e-16; no word differs |
| pred | 73 declared, 53 held, 20 failed (to 11-26) | 5 | HEAD | results/ohm-ruler4-night-2026-11-26/README.md | 73 declared; 53 held, 20 failed |
| cost4 | 173 circuits, 48 s charged (11-26) | 2 | HEAD | results/ohm-ruler4-night-2026-11-26/README.md | \| job \| `or4/job/` \| dc40l0ls2omc738edlcg \| 173 \| 1000 \| 55.9 \| **48** \| |
| twirl | fixed ZZ: (de) -0.008 / -0.034; mirror twirl -0.009 / -0.039; full twirl (e) +0.083 | 3.4 | PENDING COMMIT | the workplace VS's twirl report, 2026-11-27 (take-home 27a, `VSから職場_2026-11-27/twirl空回し/`) | - |
| n5 | `[NIGHT 5]`: raw W, rulers' words, head-tail readout, OR5-1, OR5-2 | 3.1-3.6 | - | results/ohm-ruler5-night-YYYY-MM-DD/ | - |
