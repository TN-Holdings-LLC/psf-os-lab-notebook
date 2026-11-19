# DRAFT (not declared): how much the loop's g moves between rounds at the same stack (night of 2026-11-20)

Home Claude, 2026-11-19 evening (owner's choice of 2026-11-19 21:38 JST: "1 and 2" of home's list, 2 = this test).
Thresholds, words and predictions marked [OWNER] are the owner's; the workplace builds the tool and fills the sizes.

## Why

- 2026-11-19 loop (`results/loop-night-2026-11-19`): rounds 1 and 2 ran the same stack (P1 at L = 1, 2, 3) and read
  L = 1 g +0.006 then +0.018 (2 SE 0.016 each), NOT SHOWN then PRESCRIPTION HELPS. The rule took that as a change and
  climbed (+M). If g moves between jobs by more than its shot-noise SE, the rule's 2 SE (shot noise only) lets the loop
  follow the night's drift instead of the prescription; LOOP-1 failed two nights running for a related reason (a first
  NOT SHOWN keeps the stack, so round 2 repeats round 1).
- This test only measures; it changes no rule. A rule change (a variance term in the threshold, round 1 run twice, or
  acting on a first NOT SHOWN) would be declared after it, with its own dry nights.

## Design

- One device record; the 2026-11-19 loop's round-1 circuits rebuilt by `gpu/os3_night.py build` with RULE1 =
  {1: P1, 2: P1, 3: P1} (the stacks every L had on 11-19; no diagnostics needed), on the night's record.
- Within a job: each L's ff, off and floor arms twice (copies a and b) in the same job.
- Between jobs: the same job submitted three times back to back (V1, V2, V3; nothing rebuilt between them).
- Numbers per L: g per copy and job with its SE; within-job difference (a - b) and between-job differences (V1 - V2,
  V2 - V3, V1 - V3), each against its own shot-noise 2 SE (sqrt of the summed variances).
- Pooled reading: the excess between-job variance s_b^2 = var(g across jobs) - mean(SE^2), with a bootstrap or the
  chi-square of the three jobs per L [workplace: the formula; the owner fixes the threshold]. 4000 shots; no
  mitigation; check as os3_night's.
- Size: one job about 2 x 30.9 s (copies) -> about 60 s by the model; three jobs about 180 s [workplace: exact].

## Verdict words [OWNER]

- Per L and job pair: SAME WITHIN ERROR (|difference| < 2 SE) or MOVES (>= 2 SE).
- Per L across the three jobs: SHOT NOISE ONLY (chi-square p >= 0.05) or DRIFTS (p < 0.05). [OWNER: test and level]

## Predictions [OWNER] (written before the data)

- LV-1 within a job, copies a and b: SAME WITHIN ERROR at every L. [OWNER]
- LV-2 between jobs: [OWNER: SHOT NOISE ONLY / DRIFTS, or no direction].

## Known limits

Three jobs on one night show drift over minutes, not across a recalibration; the loop's rounds on 11-19 were about
50 s apart, the three jobs here about the same. The 11-19 round-1 / round-2 difference (+0.012, 2 SE 0.023) was
itself inside shot noise; this test asks whether that holds when measured on purpose.
