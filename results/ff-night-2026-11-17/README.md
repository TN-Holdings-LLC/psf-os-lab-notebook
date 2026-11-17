# Feed-forward night of 2026-11-17 on ibm_fez (`prereg/ff_night_2026-11-17.md`, `prereg/ff_night_2026-11-17_T4.md`)

- Declarations pushed 11:13:45 CET (reflog "0b0a38b0 (origin/main, origin/HEAD) refs/remotes/origin/main@{2026-11-17
  11:13:45 +0100}: update by push"); psf-os branch feedforward-2026-11-16 pushed at 301ac01. Queue read 11:14:17 CET:
  marrakesh 1170, fez 1, kingston 5 -> ibm_fez (the first qualifying device in the declared order; first use of fez
  in these tests). Device record fetched 11:14:23 CET (calibration 2026-11-13 17:28 CET; failed qubits 72, 148, 149;
  coupler 32-33) (`fetch_in/`). All chains on physical qubits 0-9.
- Built with `gpu/coh_night.py`, `gpu/compound_night.py`, `gpu/apps_night.py`, `gpu/early_night.py` (unchanged since
  their declaring commits), psf-os at 301ac01 (checked on the owner's machine before submission). Every pre-run check
  PASS. Every job returned byte-identical to the one built.
- Jobs (submitted 11:18:46-11:19:07 CET; DD and twirling off, no mitigation, 4000 shots per circuit):

| test | folder | job | circuits | s model | s charged |
|---|---|---|---|---|---|
| T1 | `coh/` | dbu2k1ie8crs738avoqg | 10 | 14.2 | 13 |
| T2 | `compound/` | dbu2k38vv3fc73c0n4p0 | 19 | 24.2 | 23 |
| T3 | `apps/` | dbu2k51jbrss73a7668g | 46 | 54.3 | 51 |
| T4 | `early/` | dbu2k6qe8crs738avovg | 19 | 24.2 | 23 |

Sentinel DEAD in all four jobs (reported beside, never judged).

## Verdicts and predictions

| test | verdicts | predictions |
|---|---|---|
| T1 | coh1 CLOSER WITH CONTROL (d 0.0787, 2 SE_d 0.0178); rd1 CLOSER WITH CONTROL (d 0.0900, 2 SE_d 0.0168) | T1-1 held, T1-2 held |
| T2 | BEYOND THE CORRECTION CEILING at L = 1 .. 5 (g +0.075 / +0.107 / +0.152 / +0.164 / +0.158, 2 SE 0.011-0.016), no overshoot; slope +0.0240 (2 SE 0.0042) COMPOUNDS | T2-1 held, T2-2 held |
| T3 | A n = 2: ff 0.8609 against the ceiling 0.7500, BEYOND; A n = 3: 0.7722 against 0.5884, BEYOND; A margin growth +0.0730 (2 SE 0.0072) GROWS; B k = 2: 0.8488 against 0.7500, BEYOND; B k = 4: 0.7335 against 0.7500, NOT BEYOND | T3-1 held, T3-2 held, T3-3 failed |
| T4 | BEYOND at L = 1 .. 5 (g +0.072 / +0.118 / +0.142 / +0.160 / +0.163), no overshoot; slope +0.0241 (2 SE 0.0042) COMPOUNDS; against T2's third design: NOT SHOWN at every L (d between -0.010 and +0.011, 2 SE 0.015-0.022) | T4-1 held, T4-2 held, T4-3 failed |

## Two numbers side by side

- T2 / T4 (vanity: beyond the ceiling at every L, the margin grows; essence: what the device kept). ff against its
  own noiseless value: third design -0.021 / -0.055 / -0.053 / -0.068 / -0.086; early chain -0.023 / -0.044 / -0.063 /
  -0.071 / -0.081. The device kept 0.65-0.78 of the noiseless margin. The margin's growth slows at L = 4, 5 (g +0.164
  then +0.158 in T2).
- T3-A (vanity: beyond the ceiling, growing; essence: the full 2- or 3-bit phase right in 0.861 / 0.772 of the shots,
  against 1 noiselessly).
- T1 (vanity: both CLOSER; essence: ff 0.839 (coh1) and 0.871 (rd1) against 0.892 noiselessly).

## Beside, never judged

- T1: |rd1 - noiseless| - |coh1 - noiseless| = -0.032 (2 SE 0.016): on fez tonight, removing the mid-circuit waits
  did not pay for the CZ it adds at L = 1 (coh1 8 CZ against rd1 2 CZ and two mid-circuit measurements).
- T4 against T2: the early chain has CZ 10 against 42 and about a third of the counted waits at L = 5, and kept the
  same share within 2 SE at every L. Neither the CZ count nor the counted waits are what limits the chain on fez
  tonight; the early chain's extra conditionals (9 against 5 at L = 5) are its cost and were not measured apart.
- T3-B: k = 4 fell by 0.115 from k = 2 (2 SE 0.018), below the 3/4 ceiling. Success there is the last bit 1 (the home
  change against decay bias), so decay worked against success.
- Off arms as read: T2 / T4 off at L = 4, 5 came out above their noiseless values (0.426 / 0.373 and 0.411 / 0.360
  against 0.398 / 0.316); the verdicts use the noiseless off values (the ceiling), not the device's off arm.

## Reproduce

`python reproduce.py --psf-os PATH_TO_PSF_OS_AT_301ac01 ff-night-2026-11-17-coh ff-night-2026-11-17-compound
ff-night-2026-11-17-apps ff-night-2026-11-17-early` (all SAME, 2026-11-17).
