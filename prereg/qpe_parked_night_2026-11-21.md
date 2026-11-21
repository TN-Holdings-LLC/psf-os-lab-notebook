# Declared: phase estimation at n = 4, 5, 6 with the waiting target parked in |0> (psf-os 0.3.0's default)

Home Claude, 2026-11-21, on the owner's choices of 2026-11-21 (11:3x JST: spend IBM's remaining time on this; 13:2x
JST: plan 3 "subset", park_skip in 0.3.0, declarations from 0.3.0 on name the version; 13:3x JST: the fills below
confirmed, "この内容で宣言する"). Declared when the commit that adds this file is pushed, before the night's device record
is fetched. The tools are as of that commit; psf-os 0.3.0 = branch release-0.3.0 at cedd90d (to be tagged v0.3.0;
`psf_os.__version__` 0.3.0; every manifest records `psf_os_build` version 0.3.0, park True, park_set explicit).

The home VS's draft at this commit (`prereg/drafts-2026-11-21/qpe_parked_DRAFT.md`) is declared as written, with its
[OWNER] items filled as below. Where this file and the draft differ, this file holds. Its Why, Design, Verdicts,
Reading table and Known limits are copied here unchanged.

## The [OWNER] items

1. **Plan 3 (subset)**: every phase parked (`ipe{n}_{j}`), the unparked twin (`ipu{n}_{j}`, `park_skip`) at 8 phases
   per n (0, step, 2 step, ..., step = 2^n / 8); 1950 shots; ff arm only; one sentinel per job. Two jobs of 72
   circuits, 43.5 s each, 87.0 s by the model. A phase and its twin are never split across jobs. Home dry build on the
   2026-11-21 marrakesh record: job0 parked 51 / unparked 17, job1 61 / 7; check PASS, "park records as meant".
   d_n is read on the 8 paired phases (2 SE by the dry runs: 0.0064 / 0.0072 / 0.0078 at n = 4 / 5 / 6); the parked
   shape on every phase (2 SE of the acceleration 0.0066).
2. **Shots**: 1950 (not the formula's 100).
3. **Words and reading table**: as in the draft (copied below).
4. **Predictions** (each from a device record; the dry runs are expectations only):
   - **QP-1** parking KEEPS MORE at n = 4 (the weekend's C: +0.0387, 2 SE 0.0045, on all 16 phases; tonight on the 8
     paired phases).
   - QP-2: no direction declared (parking at n = 5 and 6 has no device record).
   - **QP-3** the parked IPE BEYOND THE CEILING at n = 4, 5 and 6 (the weekend's B unparked: +0.425, +0.492, +0.539
     beyond; the weekend's C parked at n = 4: 0.9344). One prediction, held only if all three n are beyond.
   - The parked shape: no direction declared.
5. **psf-os**: 0.3.0 at cedd90d. The tool passes `park=True` explicitly, so the safety guard does not apply.

## Device procedure (home)

GitHub first (VPN ON), then the device (VPN OFF), as every night. The device step:
```
python gpu/daily_fetch.py OUT/fetch_in ; DEV=<the chosen device's dev folder>
python gpu/qpe_parked_night.py build $DEV OUT --plan subset
python gpu/qpe_parked_night.py check OUT                          # PASS, or stop
python -m psf_os submit --job OUT/job0/job ; python -m psf_os submit --job OUT/job1/job
python -m psf_os collect --job <each> --wait-min 20
python gpu/qpe_parked_night.py score OUT
```

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

## Verdicts

- Ceiling per n, parked: BEYOND THE CEILING / NOT BEYOND (2026-11-19's words).
- Parking per n (plans 2, 3, 4): d_n = parked − unparked on the paired phases, SE from both: KEEPS MORE (d ≥ 2 SE),
  SAME WITHIN ERROR, KEEPS LESS (d ≤ −2 SE). These are C's words.
- Shape, parked: the weekend's B measure (log drops, a = D_6 − D_5, SE = sqrt(t4^2 + 4 t5^2 + t6^2)): ACCELERATES /
  FLAT / SLOWS.

## Reading table (proposed; plans 2 to 4)

| parking at n = 4, 5, 6 | parked shape | reading |
|---|---|---|
| KEEPS MORE at every n | FLAT | parking keeps more at every n, and the parked loss per added bit is per round |
| KEEPS MORE at every n | ACCELERATES | parking keeps more; a cost per conditional remains (not on the target) |
| KEEPS MORE at some n, SAME at others | (any) | parking's gain is seen at some n only: not read as growing or shrinking with n |
| SAME at every n | (any) | parking's gain not seen at this night's shot noise (against the weekend's C) |
| KEEPS LESS at any n | (any) | against the default's evidence: read for the default before any other row |
| (any) | SLOWS | the parked loss per added bit shrinks: not read for the mechanism |

Rows are read in order; the first that fits is the reading. Every outcome falls on one row.

## Known limits

- One night, one device, one circuit family (IPE). Parking's other users in the notebook have nothing to park, so this
  does not test the default on them.
- **Depth:** the parked form is deeper by up to +10 (n = 4) to +16 (n = 6), from its fences and X pairs. The
  difference d_n holds that cost too.
- **Plans 2 to 4 hold B's unparked circuits again.** They were run on the weekend at another calibration, and that
  night's numbers are not pooled with these.
- Plan 3's unparked phases are 0, step, 2 step, … (step = 2^n / 8). d_n there is read on those phases only.
- The shape is read from 2 or 3 jobs (as the weekend's B, from 2). A drift between jobs enters the acceleration.
