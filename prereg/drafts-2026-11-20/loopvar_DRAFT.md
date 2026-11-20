# DRAFT (not declared): how much the loop's g moves between rounds at the same stack (night of 2026-11-20)

Home Claude, 2026-11-19 evening (owner's choice of 2026-11-19 21:38 JST: "1 and 2" of home's list, 2 = this test).
Thresholds, words and predictions: the owner's decision of 2026-11-20 morning (below); the workplace built the tool and filled the sizes.

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
- Pooled reading (workplace; the level 0.05 is the owner's, 2026-11-20): per job g_j = (g_a + g_b) / 2 with
  SE_j = sqrt(SE_a^2 + SE_b^2) / 2; the weighted mean gbar = sum w_j g_j / sum w_j (w_j = 1 / SE_j^2);
  chi2 = sum_j (g_j - gbar)^2 / SE_j^2 with 2 degrees of freedom, p = exp(-chi2 / 2) (closed form for 2 df); the
  excess between-job variance s_b^2 = var(g_j, ddof 1) - mean(SE_j^2) (a moment estimate; <= 0 means none seen);
  beside, chi2 summed over L (6 df, p = exp(-x/2)(1 + x/2 + x^2/8)). 4000 shots; no mitigation.
- check (workplace): every circuit's noiseless value against the exact one (as os3_night's, TOL 0.03); copies a and
  b of every item the same gates (psf_os.gatehash) on the same qubits; V1, V2, V3 byte-identical (circuits.qpy and
  manifest); each job within 60 s by the model. The P0 and P1 circuits are gate-identical to the 2026-11-19 loop's
  round 1 (results/loop-night-2026-11-19/r1, checked by digest, all three arms, L = 1, 2, 3). The readout probe of
  round 1 is left out (no rule is applied).
- Size (workplace, 2026-11-20, on the 2026-11-19 marrakesh record): 12 items (P0 and P1 at L = 1, 2, 3, two copies)
  x 3 arms + the sentinel's 4 = 40 circuits, 47.6 s per job by the model; three jobs 142.8 s. Tool
  `gpu/loopvar_night.py` (build makes V1-V3 from one build; check / score; dry for illustrative noise).

## Verdict words (the owner's decision of 2026-11-20 morning)

- Copies (LV-1): the nine within-job differences (a - b) / SE (3 L x 3 jobs, SE = sqrt(SE_a^2 + SE_b^2)) pooled in one
  chi-square with 9 degrees of freedom: SAME WITHIN ERROR (p >= 0.05) or MOVES (p < 0.05). Per L and job pair beside
  (SAME WITHIN ERROR |d| < 2 SE / MOVES >= 2 SE).
- Per L across the three jobs: SHOT NOISE ONLY (chi-square, 2 df, p >= 0.05) or DRIFTS (p < 0.05); per job pair
  beside, as above.
- Why pooled: nine separate 2 SE tests read MOVES somewhere about 34 % of the time on shot noise alone (workplace VS,
  workplace Claude); the pooled test at p < 0.05 does so 5 % of the time.

## Predictions (written before the data; the owner's decision of 2026-11-20 morning)

- LV-1 copies a and b: SAME WITHIN ERROR (the pooled chi-square, p >= 0.05).
- LV-2 between jobs: no direction declared (read and reported per L, not counted as a prediction).

## Reading beside (the workplace VS's table, 2026-11-20; per L; not judged, it does not change the test)

| copies a - b | three jobs | reading |
|---|---|---|
| every pair SAME | SHOT NOISE ONLY | the shot-noise SE explains the variation; 11-19's round 1 -> round 2 change (+0.012, 2 SE 0.023) is within it |
| every pair SAME | DRIFTS | the device moves between jobs (tens of seconds to minutes); the rule's threshold would need a between-job term |
| some pair MOVES | SHOT NOISE ONLY | the copies in one job disagree: the SE of g is underestimated, or order inside a job matters; between jobs not read |
| some pair MOVES | DRIFTS | the SE is underestimated overall; review the SE formula before the rule's threshold |
| L differ | - | read each L by the rows above; whether one L DRIFTS is enough to say "the rule can follow drift" is open |

## Known limits

Three jobs on one night show drift over minutes, not across a recalibration; the loop's rounds on 11-19 were about
50 s apart, the three jobs here about the same. The 11-19 round-1 / round-2 difference (+0.012, 2 SE 0.023) was
itself inside shot noise; this test asks whether that holds when measured on purpose.
