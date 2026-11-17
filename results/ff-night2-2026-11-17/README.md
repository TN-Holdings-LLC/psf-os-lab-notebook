# Second round of the night of 2026-11-17 on ibm_marrakesh (`prereg/ff_night2_2026-11-17.md`)

- Declaration pushed 11:26:27 CET (reflog "461e051c (origin/main, origin/HEAD) refs/remotes/origin/main@{2026-11-17
  11:26:27 +0100}: update by push"). Queue read 11:26:45 CET: marrakesh 2, fez 3, kingston 4 -> ibm_marrakesh (the
  first qualifying device in the declared order; the first round ran on fez). Device record fetched 11:26:51 CET
  (calibration 2026-11-13 18:22 CET; failed qubits 82, 94, 113, 119, 130; coupler 113-119) (`fetch_in/`). Chains on
  physical qubits 0-13.
- Built with `gpu/coh2_night.py`, `gpu/early2_night.py`, `gpu/apps2_night.py` (unchanged since the declaring commit),
  psf-os 301ac01 (checked on the owner's machine). Every pre-run check PASS; every job returned byte-identical.
- Jobs (submitted 11:33:48-11:34:01 CET; DD and twirling off, no mitigation, 4000 shots per circuit):

| test | folder | job | circuits | s model | s charged |
|---|---|---|---|---|---|
| N1 | `coh2/` | dbu2r38vv3fc73c0nfjg | 16 | 20.9 | 20 |
| N2 | `early2/` | dbu2r4ovv3fc73c0nfo0 | 25 | 30.9 | 31 |
| N3 | `apps2/` | dbu2r6k9po4c73cefjr0 | 52 | 61.0 | 59 |

Sentinel DEAD in all three (beside, never judged).

## Verdicts and predictions

| test | verdicts | predictions |
|---|---|---|
| N1 | coh2 CLOSER WITH CONTROL (d 0.1345, 2 SE_d 0.0207); rd2 CLOSER (0.1175, 0.0203); coh3 CLOSER (0.1542, 0.0219); rd3 CLOSER (0.1217, 0.0218) | N1-1 held, N1-2 held |
| N2 | L = 1 OVERSHOOT (ff 0.903, noiseless 0.890, +0.013 against 2 SE 0.009); L = 2 .. 6 BEYOND THE CORRECTION CEILING (g +0.146 / +0.194 / +0.210 / +0.196 / +0.229); L = 7 OVERSHOOT (ff 0.487, noiseless 0.444, +0.043 against 2 SE 0.016); slope +0.0264 (2 SE 0.0024) NOT SHOWN (overshoot at L = 1, 7) | N2-1 failed, N2-2 failed |
| N3 | n = 4, the 16 phases pooled: ff 0.9029 (2 SE 0.0023, 64000 shots) against the ceiling 0.4706: BEYOND THE CEILING (margin +0.432) | N3-1 held |

## Two numbers side by side

- N2 (vanity: g grows to +0.288 at L = 7; essence: at L = 1 and 7 the ff arm is above its own noiseless value, so its
  closeness to the exact value there is not the control's doing, and the guard set before the data takes those L out).
  ff against its noiseless value: +0.013 / -0.016 / -0.011 / -0.020 / -0.047 / -0.018 / +0.043. At L = 7 the device's
  off arm reads 0.399 against 0.199 noiselessly and the floor arm keeps all zeros in 0.750 of the shots: decay read
  flipped lifts both arms toward success there (the workplace VS desk's warning, now on the device).
- N3 (vanity: far beyond the ceiling; essence: all four bits right in 0.903 of the shots, against 1 noiselessly; per
  phase 0.866 to 0.990, the all-zero phase j = 0 highest).

## Beside, never judged

- N1: |rd - noiseless| - |coh - noiseless| = -0.017 (L = 2, 2 SE 0.019) and -0.010 (L = 3, 2 SE 0.021): the circuit
  without mid-circuit measurements and the third design kept the same within 2 SE on marrakesh (on fez at L = 1 in
  the first round: -0.032, beyond 2 SE).
- N3 against the first round's T3-A (another device): fez n = 2 0.861, n = 3 0.772; marrakesh n = 4 0.903. The device
  differs; no trend in n is read from these.
- N2 at L = 2 .. 6 against T4 / T2 of the first round (another device): marrakesh kept more of the noiseless value at
  L = 3, 4, 6 (-0.011, -0.020, -0.018) than fez did at L = 3, 4 (-0.063 / -0.053, -0.071 / -0.068).

## Reproduce

`python reproduce.py --psf-os PATH_TO_PSF_OS_AT_301ac01 ff-night2-2026-11-17-coh2 ff-night2-2026-11-17-early2
ff-night2-2026-11-17-apps2` (all SAME, 2026-11-17).
