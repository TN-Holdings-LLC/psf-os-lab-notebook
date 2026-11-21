# DRAFT (not declared): phase estimation at n = 4, 5, 6 with the waiting target parked in |0> (psf-os 0.3.0's default)

Home VS Claude, 2026-11-21, on the home instruction `VSクロードへの指示_psf-os_0.3.0の追加_2026-11-21.md` (part C;
the owner chose to spend IBM's remaining time on this). **The plan, predictions, words, thresholds and reading table
marked [OWNER] are the owner's / home Claude's.**

- Tool: `gpu/qpe_parked_night.py` (table / build / check / dry / score). It reads the declared `gpu/qpe_repro_night.py`
  only (its check and dry run).
- psf-os: release-0.3.0. It uses `build(park=True)`, `park_skip` for the unparked twins, and `ff_only`.
- Notes: `notes/qpe_parked_2026-11-21/`.

## Why

- **The weekend's B** (`results/weekend-shared-night-2026-11-21`) ran IPE unparked, as 2026-11-19 sent it: 0.8957,
  0.8715 and 0.8451 at n = 4, 5, 6. The log drop per added bit was flat (+0.0274, +0.0308; acceleration +0.0034,
  2 SE 0.0077, FLAT).
- **The weekend's C** ran n = 4 parked (pk) beside unparked (pl) in one job: +0.0387 (2 SE 0.0045), KEEPS MORE.
  **This is the only device record behind psf-os 0.3.0's default.** It is IPE n = 4, one night, one device.
- This test asks two things:
  - whether parking keeps more at n = 5 and 6 too (the parked twin against the unparked one, inside one job);
  - whether, once the target is parked, the loss per added bit stays per round (the shape of B, parked).
- It is the first device run of psf-os 0.3.0's default.

## Design (one device record; rule C placement, as 2026-11-19 and the weekend's B and C; no mitigation)

- **Circuits:** B's own, IPE n = 4, 5, 6 at every phase (`AP.ipe(n, j)`).
  - `ipe{n}_{j}`: parked, by psf-os 0.3.0's default. The target is put in |0> at every read and every run of phase
    feedback. This is C's pk form, which `park_waits` reproduces exactly at n = 4.
  - `ipu{n}_{j}`: the same circuit, unparked (`park_skip`). It is the weekend's B form, C's pl.
- **Arms:** ff only, one sentinel per job (as the weekend). Every verdict pools ff successes; every ceiling C(n) is
  exact.
- **The comparison is read inside one job.** A parked phase and its unparked twin are in the same job, and a phase is
  never split across jobs (`score` refuses a split pair).

## Plans [OWNER] (`python gpu/qpe_parked_night.py table`; model seconds, 60 s per job at most)

| plan | shots | circuits | jobs | s (model) | 2 SE of d_n at n = 4 / 5 / 6 | 2 SE of the parked shape's acceleration | reads |
|---|---|---|---|---|---|---|---|
| 1 parked only | 1950 | 120 | 2 | 73.6 | — | 0.0066 | shape and ceiling, parked; against the weekend's unparked B only across nights (beside) |
| 2 both, every phase | 1950 | 236 | 3 | 141.8 | 0.0046 / 0.0036 / 0.0028 | 0.0066 | d_n at every n inside one job; shape |
| 3 parked every phase, unparked 8 phases per n | 1950 | 144 | 2 | 87.0 | 0.0064 / 0.0072 / 0.0078 | 0.0066 | d_n on 8 phases per n inside one job; shape |
| 4 the formula: both, every phase | 100 | 228 | 1 | 17.4 | 0.0201 / 0.0158 / 0.0123 | 0.0289 | d_n of 0.03 or more; the shape only coarsely |
| 4 + 1: parked only at 1950, plus the formula's job | 1950 / 100 | 348 | 3 | 91.0 | 0.0201 / 0.0158 / 0.0123 | 0.0066 | the shape as plan 1, d_n as plan 4 |

- The 2 SE are estimates: the weekend's unparked shares, with parked 0.03 higher.
- **The formula (plan 4):** the total shots per arm at n = 4, N = (2 + 0.84)^2 (p1 q1 + p2 q2) / 0.03^2, spread over
  n = 4's 16 phases. That sees d = 0.03 at 2 SE with about 80 % power, giving 100 shots per circuit.
- **Plan 1** reads parking only against the weekend's B, which is a different night and calibration (気づき 3: F16
  read 0.812 on 11-19 and 0.751 on 11-21). That difference would be beside only.
- **Seconds:** by the model. The device charged 0.935 of the model over 105 jobs, and no per-circuit term shows. At
  100 shots the model's per-circuit term (0.036 s) dominates, so plan 4's charge is likely well below 17.4 s.

## Dry runs (ILLUSTRATIVE noise, never fitted; `notes/qpe_parked_2026-11-21/dry/`)

Every plan was built on the 2026-11-21 marrakesh record with the dry Clifford sentinel. `qpe_repro_night.check` passed
on every job, and every park record is as meant (each ipe parked at every wait, each ipu skipped).

- noise a (`notes/qpe_repro_2026-11-19/noise/illus_a.json`): CZ 1 %, damping 2 % per read.
- noise c (`illus_c.json`): CZ 0.2 %, damping 2 %, dephasing 12 % per conditional.

| plan, noise | d_4 (2 SE) | d_5 | d_6 | parked shape |
|---|---|---|---|---|
| 2 both, a | +0.0103 (0.0035) KEEPS MORE | +0.0137 (0.0028) KEEPS MORE | +0.0189 (0.0022) KEEPS MORE | FLAT (+0.0001, 2 SE 0.0049) |
| 2 both, c | +0.0898 (0.0066) KEEPS MORE | +0.1262 (0.0053) KEEPS MORE | +0.1613 (0.0039) KEEPS MORE | ACCELERATES (+0.0199, 2 SE 0.0119) |
| 3 subset, a | +0.0083 (0.0046) KEEPS MORE | +0.0163 (0.0046) KEEPS MORE | +0.0158 (0.0048) KEEPS MORE | FLAT |
| 3 subset, c | +0.0878 (0.0093) KEEPS MORE | +0.1296 (0.0105) KEEPS MORE | +0.1457 (0.0111) KEEPS MORE | ACCELERATES |
| 4 formula, a | +0.0138 (0.0159) SAME | +0.0106 (0.0118) SAME | +0.0206 (0.0096) KEEPS MORE | FLAT (2 SE 0.0213) |
| 4 formula, c | +0.1012 (0.0289) KEEPS MORE | +0.1247 (0.0233) KEEPS MORE | +0.1528 (0.0174) KEEPS MORE | FLAT (+0.0365, 2 SE 0.0520) |
| 1 parked, a / c | — | — | — | FLAT / ACCELERATES |

- **Plan 4 is sized for 0.03.** Under noise a the parking gain at n = 4 is +0.010, below what 100 shots can see, so it
  read SAME WITHIN ERROR there. The device's C gave +0.039 at n = 4.
- **Under noise c (a loss per conditional) the parked shape ACCELERATES.** Parking takes the target out of the
  dephasing, but the ancilla's conditionals still cost per bit. So the shape word separates the two noises with the
  target parked too.

## Verdicts [OWNER]

- Ceiling per n, parked: BEYOND THE CEILING / NOT BEYOND (2026-11-19's words).
- Parking per n (plans 2, 3, 4): d_n = parked − unparked on the paired phases, SE from both: KEEPS MORE (d ≥ 2 SE),
  SAME WITHIN ERROR, KEEPS LESS (d ≤ −2 SE). These are C's words.
- Shape, parked: the weekend's B measure (log drops, a = D_6 − D_5, SE = sqrt(t4^2 + 4 t5^2 + t6^2)): ACCELERATES /
  FLAT / SLOWS.

## Reading table [OWNER] (proposed; plans 2 to 4)

| parking at n = 4, 5, 6 | parked shape | reading |
|---|---|---|
| KEEPS MORE at every n | FLAT | parking keeps more at every n, and the parked loss per added bit is per round |
| KEEPS MORE at every n | ACCELERATES | parking keeps more; a cost per conditional remains (not on the target) |
| KEEPS MORE at some n, SAME at others | (any) | parking's gain is seen at some n only: not read as growing or shrinking with n |
| SAME at every n | (any) | parking's gain not seen at this night's shot noise (against the weekend's C) |
| KEEPS LESS at any n | (any) | against the default's evidence: read for the default before any other row |
| (any) | SLOWS | the parked loss per added bit shrinks: not read for the mechanism |

Rows are read in order; the first that fits is the reading. Every outcome falls on one row.

## Predictions [OWNER] (written before the data)

- QP-1 [OWNER: e.g. parking KEEPS MORE at n = 4 (the weekend's C: +0.0387)]
- QP-2 [OWNER: e.g. parking KEEPS MORE at n = 5 and 6, or no direction]
- QP-3 [OWNER: e.g. parked IPE BEYOND THE CEILING at n = 6]
- The only device record behind any prediction is the weekend's C (n = 4, +0.0387). The dry runs are expectations.

## Known limits

- One night, one device, one circuit family (IPE). Parking's other users in the notebook have nothing to park, so this
  does not test the default on them.
- **Depth:** the parked form is deeper by up to +10 (n = 4) to +16 (n = 6), from its fences and X pairs. The
  difference d_n holds that cost too.
- **Plans 2 to 4 hold B's unparked circuits again.** They were run on the weekend at another calibration, and that
  night's numbers are not pooled with these.
- Plan 3's unparked phases are 0, step, 2 step, … (step = 2^n / 8). d_n there is read on those phases only.
- The shape is read from 2 or 3 jobs (as the weekend's B, from 2). A drift between jobs enters the acceleration.

## Decisions before declaring ([OWNER] list)

1. The plan (1, 2, 3, 4, or 4 + 1).
2. Shots: 1950, or the formula's 100 (plan 4); the formula's target d (0.03).
3. The words, the reading table, predictions QP-1 …
4. psf-os: release-0.3.0 at its declared commit. The tool says `park=True` explicitly, so the safety guard does not
   apply.

## Device procedure (home)

```
# psf-os release-0.3.0 at the declared commit; the notebook at the declaring commit
python gpu/qpe_parked_night.py build DEV OUT --plan P          # [--shots S]
python gpu/qpe_parked_night.py check OUT                       # PASS on every job; park records as meant
python -m psf_os submit OUT/jobK ; python -m psf_os collect OUT/jobK     # every job, as every night
python gpu/qpe_parked_night.py score OUT
```
