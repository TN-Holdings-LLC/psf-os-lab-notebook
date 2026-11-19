# The loop's round-to-round variation: the tool and its desk check (workplace Claude, 2026-11-20; not declared)

Draft `prereg/drafts-2026-11-20/loopvar_DRAFT.md` (words, level and predictions [OWNER]). Tool `gpu/loopvar_night.py`.

## The jobs (`plan_marrakesh_1119.json`, `check_marrakesh_1119.txt`: PASS)

The 2026-11-19 loop's round 1 (P1 at L = 1, 2, 3; P0 the control), each item twice (copies a, b), no readout probe:
12 items x 3 arms + 4 sentinel = 40 circuits, 47.6 s per job by the model; built once, copied to V1, V2, V3
(byte-identical), 142.8 s for the three. The P0 and P1 circuits are gate-identical (psf_os.gatehash) to the record's
round 1 (`results/loop-night-2026-11-19/r1`), every arm and L. Chains as on 11-19: L1 [0, 1], L2 [0-3], L3 [0-5].

## Dry runs (`dry/`, noises `noise/`: ILLUSTRATIVE, written by hand, never fitted)

| noise | within a - b (9 pairs) | between jobs (9 pairs) | three jobs, per L (p) |
|---|---|---|---|
| none (independent seeds) | 2 MOVES (L1 V3 +0.020, L3 V2 -0.041) | 0 MOVES | 0.26, 0.12, 0.44: SHOT NOISE ONLY |
| CZ noise x3 in V3 | 1 MOVES | 1 MOVES | 0.31, 0.13, 0.14: SHOT NOISE ONLY |
| mid-circuit damping x4 in V3 | 1 MOVES | 6 MOVES | 0.000 x3: DRIFTS |

- Every word is reached. A drift that both items feel alike (CZ noise) moves the shares (P0 0.74 -> 0.70 at L2) but
  not g, the difference the loop's rule reads; a drift that P1 (holding flipped) feels less than P0 (damping at the
  reads) moves g by 0.07-0.21. The test asks about g, the rule's quantity; the shares are printed beside.
- Under shot noise alone, 2 of 9 within-job pairs read MOVES here. At 2 SE each pair has about 4.6 % to read MOVES,
  so "SAME at every L in every job" (LV-1 over 9 pairs) fails about 34 % of the time with nothing but shot noise
  (13 % over 3 pairs if each L pools its jobs). [OWNER: one pooled test, e.g. chi2 of the nine (a - b) / SE, 9 df]
- Dry seeds: strides above the shot count (see notes/decoy_2026-11-20/README.md: Aer seeds shot by shot; psf-os
  run_local's consecutive seeds give near-identical shots, so a noiseless difference reads about 0 there).

## Formula (in the draft)

g_j = (g_a + g_b) / 2, SE_j = sqrt(SE_a^2 + SE_b^2) / 2; chi2 = sum_j (g_j - gbar)^2 / SE_j^2 (gbar weighted by
1 / SE_j^2), 2 df, p = exp(-chi2 / 2); s_b^2 = var(g_j) - mean(SE_j^2). Pooled over L beside (6 df).
