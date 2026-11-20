# How much the loop's g moves within a job and between jobs at the same stack (loopvar), 2026-11-20 on ibm_marrakesh (`prereg/loopvar_night_2026-11-20.md`)

- Declared in ecde2114. Built on the owner's machine (`versions.txt`) with psf-os 61869bb from the night's record (the
  same as the decoy test: `results/decoy-night-2026-11-20/fetch_in/ibm_marrakesh/dev`, calibration 2026-11-19
  23:09:26+01:00). The 2026-11-19 loop's round 1 (P1 / P1 / P1), two copies per arm in one job; the job sent three times
  without rebuilding (V1-V3 byte-identical, `check.txt`). 40 circuits, 4000 shots.

| job | id | s model | s charged | created - finished (CET) |
|---|---|---|---|---|
| V1 | dc026l2nj2vs73ddbbig | 47.6 | 46 | 11:39:17 - 11:40:37 |
| V2 | dc026n5hdvas73birfi0 | 47.6 | 46 | 11:39:25 - 11:41:17 |
| V3 | dc026panj2vs73ddbbpg | 47.6 | 46 | 11:39:33 - 11:42:06 |

`python gpu/loopvar_night.py score .` (`score.txt`, `loopvar_scores.json`):

```
L 1: g V1 +0.0369, V2 +0.0232, V3 +0.0189 (SE 0.006); three jobs chi2 5.06 (2 df) p 0.080 SHOT NOISE ONLY; excess SD 0.0073
L 2: g V1 +0.0215, V2 -0.0042, V3 -0.0076 (SE 0.007); three jobs chi2 10.23 (2 df) p 0.006 DRIFTS; excess SD 0.0143
L 3: g V1 +0.1616, V2 +0.1510, V3 +0.1570 (SE 0.0077); three jobs chi2 0.95 (2 df) p 0.623 SHOT NOISE ONLY
between jobs pooled over L (beside): chi2 16.24 (6 df), p 0.013
copies, the nine (a - b) / SE pooled (LV-1): chi2 7.11 (9 df), p 0.625 -> SAME WITHIN ERROR
```

## Against the declaration

| prediction | numbers | |
|---|---|---|
| LV-1 copies within a job: SAME WITHIN ERROR (pooled chi-square, 9 df) | p 0.625 | held |
| LV-2 between jobs: no direction declared | L 1 SHOT NOISE ONLY, L 2 DRIFTS, L 3 SHOT NOISE ONLY | read, not a prediction |

## Reading

Within one job the two copies agree at every L; between jobs about 40-50 s apart, L 2 moved beyond shot noise (g
+0.022 then -0.004 and -0.008: the sign changed between V1 and V2; excess SD 0.014, twice its SE) and L 1 sat near the
threshold (p 0.08; V1 - V3 +0.018 against 2 SE 0.017). The loop's rule judges g by its shot-noise SE alone; on a night like
this it can read a job-to-job move as the prescription's effect (as on 11-19 rounds 1 -> 2). The receiver
`between_job_sigma` (psf-os after-2026-11-20) adds such a term; whether and with which value is the owner's decision
(this night: 0.007-0.014 by L). One night; three jobs show drift over minutes, not across a recalibration. Beside: L 3's
g (+0.15 to +0.16) is far from 11-19's (-0.027 with the same stack): the night, not the copies, sets the level.

## Two numbers side by side

- Vanity: copies inside a job agree (p 0.63).
- Essence: the same circuit sent again a minute later can read a g that differs by twice its error bar; a loop that
  climbs on one round's difference should carry a between-job term.

## Reproduce

`python reproduce.py loopvar-night-2026-11-20`
