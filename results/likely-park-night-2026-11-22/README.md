# psf-os 0.3.1's candidate (park_likely, MP) against 0.3.0's default, 2026-11-22 on ibm_kingston (`prereg/likely_park_night_2026-11-22.md`)

- Declared in 42c24b11, pushed by the owner before the night's first fetch (03:46:38 CET). Run on the owner's machine
  (`versions.txt`: Python 3.12.13, qiskit 2.5.2, aer 0.17.2, runtime 0.49.0, numpy 2.5.3) from a fresh worktree at
  42c24b11 with psf-os 0.3.1 (candidate; likely-park-2026-11-22 at a6170e5), both checked clean and the version
  checked (PRE_OK).
- Device: `fetch_in/queue.json` pending marrakesh 2, fez 3, kingston 2; the rule (not marrakesh; the shorter queue of
  fez and kingston) -> **ibm_kingston**, calibration 2026-11-22 03:26:22+01:00. The third device of these tests
  (marrakesh 11-20 to 11-21, fez 11-21).
- Built as declared (`--plan B`); check PASS (`lp/check.txt`): `psf_os_build` 0.3.1, park True, park_likely naming
  the 28 L items; per item the twins' distributions equal, CZ equal (33 / 33; P3 22 / 22), every parked wait fenced
  with a qubit of its wait; the IPE control's declared check PASS.
- Scored by the declared tool on the owner's machine (`lp/score.txt`, `lp/likely_scores.json`); re-scored at home
  (aer 0.18.0): the same text.

| job | folder | id | circuits | shots | s model | s charged | RU | created - finished (CET) |
|---|---|---|---|---|---|---|---|---|
| job0 | `lp/job0/` | dc15fjdhdvas73bkdmag | 68 | 1950 | 41.2 | 40 | 0.652 | 03:47:41 - 03:48:38 |

## Results

| item (copies) | D, 0.3.0's default | L, park_likely (MP) | noiseless (D, L) | exact | L - D (2 SE) | |
|---|---|---|---|---|---|---|
| NF m3 L3 (4) | 0.5672 | 0.6644 | 0.7834, 0.7834 | 0.8230 | +0.0972 (0.0155) | KEEPS MORE |
| P0 L3 (14) | 0.5458 | 0.5705 | 0.7834, 0.7834 | 0.8230 | +0.0247 (0.0085) | KEEPS MORE |
| P3 L3 (10) | 0.5684 | 0.5778 | 0.7060, 0.7060 | 0.8230 | +0.0094 (0.0100) | SAME WITHIN ERROR |

- No OVERSHOOT: every P is below its noiseless value, so all three items are counted.
- **IPE control: parked 0.9200 - unparked 0.8677 = +0.0523 (2 SE 0.0098) KEEPS MORE; the gate is open.**
- **The rule for the default (counted: NF, P0, P3): no counted item KEEPS LESS, at least one KEEPS MORE -> `park_likely`
  the default in psf-os 0.3.1.**
- Beside, never judged: on ibm_fez (2026-11-21) the full fence plus parking against the default read NF +0.079, P0
  -0.031, P3 -0.022; tonight's partial fence (MP) against the default reads NF +0.097, P0 +0.025, P3 +0.009. Another
  device; nothing is compared across nights.

## Against the declaration

| prediction | numbers | |
|---|---|---|
| LP-1 the IPE control KEEPS MORE | +0.0523 (2 SE 0.0098) | held |
| LP-2 NF's L - D KEEPS MORE | +0.0972 (2 SE 0.0155) | held |

P0 and P3: no direction declared (KEEPS MORE, SAME). Predictions over the nights of 11-16 to 11-22: 67 declared;
47 held, 20 failed.

## Two numbers side by side

- Vanity: parking the likely value keeps +0.097 on NF; the parked IPE reads 0.920 at n = 4 on kingston.
- Essence: psf-os 0.3.1's candidate, sent as it would build by default, keeps more than 0.3.0 on two of three RUS
  items and less on none, on a third device, in one job of 40 s; the always-|1> park keeps more for the fourth night
  and on the third device (+0.052). One night for MP; the RUS chains and IPE only.

## Reproduce

`python reproduce.py --psf-os <psf-os 0.3.1 candidate, a6170e5> likely-park-night-2026-11-22` (1 of 1 SAME at home).

## Independent check (home VS, 2026-11-22)

Re-counted from `job/raw_counts.json` and `job/manifest.json` with qiskit, aer and numpy only (no psf-os, no notebook
scorer; `notes/verify_2026-11-22/lp_indep.py`): every P, L - D and 2 SE, the words, no OVERSHOOT (the noiseless values
by Aer, 0.7848 and 0.7061, agree with the tool's exact ones within its sampling), the IPE control and the rule's row
agree with this record. Sent as declared: 68 circuits (64 user, 4 sentinel), 1950 shots, `psf_os_build` 0.3.1 with
park_likely naming exactly the 28 L items; every parked wait held by barriers with a measured qubit of its wait. The
device rule: pending marrakesh 2, fez 3, kingston 2 -> kingston, where the job ran. Charges 40 s, 0.6518 RU, model
41.2 s. Reproduce 1 of 1 SAME.

## After the night (the owner, 2026-11-22 14:0x JST)

psf-os 0.3.1 was released on 2026-11-22 with `park_likely` on by default (v0.3.1 at release commit 7caedaa on a6170e5;
doi:10.5281/zenodo.24438701), the bundle paths
included, as for park in 0.3.0. Because the candidate (a6170e5, park_likely off) and the release (7caedaa, on) both
say "0.3.1", every later declaration on 0.3.1 states `park_likely` explicitly.
