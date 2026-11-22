# DRAFT (not declared): phase estimation parked, stretched to n = 7 and 8 (one night, off marrakesh)

Home VS Claude, 2026-11-22 night, on the home instruction `VSクロードへの指示_位相推定を長くする試験の準備_2026-11-22.md`
(the owner's decision of 19:19 JST: "ノイズが減ったので計算の範囲を広げる。まず位相推定"). **The plan, predictions, words,
thresholds and reading table marked [OWNER] are the owner's / home Claude's.**

- Tool: `gpu/qpe_long_parked_night.py` (table / pick / build / check / dry / score). It reads the declared
  `gpu/qpe_repro_night.py` (check, dry, words) and `gpu/rus_fence_night.py` (the device rule) only.
- psf-os: **0.3.1 as released** (v0.3.1, 7caedaa). Its defaults are stated explicitly: park=True, park_likely=True.
  The tool passes the declared version "0.3.1".
- Notes: `notes/qpe_n78_2026-11-22/`.

## Why (the device records at hand only)

- **marrakesh, 2026-11-21** (`results/qpe-parked-night-2026-11-21`):
  - parked − unparked in one job, on 8 phases: +0.035, +0.031, +0.039 at n = 4, 5, 6;
  - parked over every phase: 0.874, 0.839, 0.801; log drops 0.041, 0.047, FLAT.
- **kingston, 2026-11-22:** the IPE control (n = 4, 4 phases) parked kept +0.052.
- **The home's expectation:** at n = 6 the loss falls from 0.148 to 0.109 (about 26 % less). If the loss is the same
  share per wait, the same correctness allows about 35 % more waits (n ≈ 8). That is an extrapolation; n ≥ 7 has never
  run.

## Design (one job; rule C placement; no mitigation; ff arms only; one sentinel)

- **Circuits:** IPE (apps.ipe) at n = 6, 7, 8, parked by psf-os 0.3.1. The target waits in |0> at every read and every
  run of phase feedback.
- **Phases:** 16 per n, by the formula j_k = k · a_n mod 2^n, k = 1 … 16, with a_n the odd integer nearest
  2^n (√5 − 1)/2. That gives a_6 = 41, a_7 = 79, a_8 = 159.
  - An odd a_n keeps each phase's trailing zero bits equal to k's. That number decides how many CZ the compiler keeps,
    so the 16 phases carry every phase's mix.
  - Compiled on the kingston record, the sample's mean CZ matches every phase's (`check`, `cz` lines):

    | n | every phase | the sample | equal spacing from 0 | equal spacing + an odd offset |
    |---|---|---|---|---|
    | 6 | 11.00 | 11.12 | 8.00 | 12.00 |
    | 7 | 13.00 | 13.12 | 8.00 | 14.00 |
    | 8 | 15.00 | 15.12 | 8.00 | 16.00 |

    Equal spacing would be biased to one side.
- **Ceilings (exact, apps.ipe_ideal):** C(6) 0.3065, C(7) 0.2480, C(8) 0.2007.
- **`check`:**
  - qpe_repro_night.check: noiseless, every ff arm has all n bits right;
  - the ceilings;
  - the sample's compiled CZ against every phase compiled the same way (within 0.5);
  - every parked item fenced with its target and ancilla, and every twin unparked;
  - psf_os_build: 0.3.1, park and park_likely stated explicitly.
- **The device (the rule of 2026-11-21):** not ibm_marrakesh. Of ibm_fez and ibm_kingston, the one with fewer pending
  jobs in queue.json; ties go by queue.json's order. Both records build and check.

## Plans [OWNER] (model seconds; 60 s per job at most)

| plan | content | shots | circuits | s | 2 SE of P at n = 6 / 7 / 8 | 2 SE of the acceleration | 2 SE of parked − unparked (4 phases) |
|---|---|---|---|---|---|---|---|
| a | parked, 16 phases per n | 1950 | 52 | **32.2** | 0.0045 / 0.0048 / 0.0051 | 0.016 | — |
| a64 | as a, n = 6 at every phase (as on 2026-11-21) | 1950 | 100 | **59.2** | 0.0023 / 0.0048 / 0.0051 | 0.015 | — |
| **b** | a, plus unparked twins (`park_skip`) at 4 phases per n | 1950 | 64 | **39.0** | 0.0045 / 0.0048 / 0.0051 | 0.016 | 0.013 / 0.014 / 0.014 |
| c | b at the formula's shots (+0.035 seen at 2 SE, ~80 % power, on 4 phases) | 650 | 64 | **16.5** | 0.0078 / 0.0084 / 0.0088 | 0.027 | 0.022 / 0.024 / 0.025 |

The 2 SE are estimates from the extrapolated P below.

## Expectation (an extrapolation from the record, not a measurement)

From the parked shares of 2026-11-21 (every phase, marrakesh): D5 = ln(0.874/0.839) = 0.041, D6 = 0.047.

| assumption | P(7) | P(8) | margin over C(8) |
|---|---|---|---|
| a constant log drop (the mean, 0.044) | 0.766 | 0.733 | +0.53 |
| a log drop growing by D6 − D5 per bit | 0.759 | 0.716 | +0.52 |

The device, the calibration and the phases differ from 2026-11-21, so these are only a scale.

## Dry runs (ILLUSTRATIVE noise, never fitted; `notes/qpe_n78_2026-11-22/dry/`)

Plan b on the fez and kingston records, under `notes/qpe_repro_2026-11-19/noise/illus_a.json` (CZ 1 %, damping 2 %
per read) and `illus_c.json` (plus dephasing 12 % per conditional). check passed on both devices for every plan,
and both give the same numbers.

| noise | parked P n = 6 / 7 / 8 | margin over C(8) | shape | parked − unparked n = 6 / 7 / 8 |
|---|---|---|---|---|
| illus_a | 0.929 / 0.916 / 0.901 | +0.70 | FLAT (+0.002, 2 SE 0.008) | +0.015 / +0.019 / +0.021, KEEPS MORE |
| illus_c | 0.631 / 0.525 / 0.432 | +0.23 | FLAT (+0.012, 2 SE 0.027) | +0.180 / +0.191 / +0.178, KEEPS MORE |

## Verdicts [OWNER]

- **Ceiling per n:** BEYOND THE CEILING (p ≥ C(n) + 2 SE) / NOT BEYOND. p is the share of shots with all n bits right,
  pooled over that n's parked phases.
- **Shape:** on the log of the share, D7 = ln p6 − ln p7, D8 = ln p7 − ln p8, a = D8 − D7,
  SE = sqrt(t6² + 4 t7² + t8²) with t_n = SE(p_n)/p_n. The words are ACCELERATES (a ≥ 2 SE), FLAT and SLOWS
  (a ≤ −2 SE).
- **Plans b and c, parking per n:** parked − unparked on the twin phases, in the same job. The words are KEEPS MORE,
  SAME WITHIN ERROR and KEEPS LESS (2 SE).

## Reading table [OWNER] (proposed; every pair on one row)

| ceiling at n = 8 | shape | reading |
|---|---|---|
| BEYOND | FLAT | parked IPE beyond its ceiling to n = 8, the loss per added bit per round |
| BEYOND | ACCELERATES | parked IPE beyond its ceiling to n = 8, the loss per added bit growing (a cost per conditional) |
| NOT BEYOND | FLAT | the ceiling is not passed at n = 8 with a loss per round: the range ends before n = 8 |
| NOT BEYOND | ACCELERATES | the ceiling is not passed at n = 8 and the loss per added bit grows |
| (either) | SLOWS | the parked loss per added bit shrinks: not read for the mechanism |

Beside, plans b and c: parking per n, also whether its word or size changes with n. This is not read for a row.

## Predictions [OWNER]

- QN-1 [OWNER: e.g. parked IPE BEYOND THE CEILING at n = 7 and 8]
- QN-2 [OWNER: e.g. the shape FLAT, or no direction]
- QN-3 (plans b, c) [OWNER: e.g. parking KEEPS MORE at n = 8, or no direction]
- The device records behind them are the ceiling passed at n ≤ 6 (three nights) and parking (four nights, three
  devices). n = 7 and 8 have never run.

## Known limits

- **Phases are thinned:** 16 per n (n = 6 at every phase in plan a64). The formula keeps the compiled CZ mix of every
  phase (checked), but the share is that of the 16 phases.
- **No comparison with earlier nights.** n = 6 is run to join the shape inside the job, not to compare with 2026-11-21
  (another device, another calibration, other phases).
- **The device may change** (fez or kingston, by the rule). The parked form has run on marrakesh, the IPE control on
  fez and kingston.
- **The shape's sensitivity.** Under a loss per conditional (illus_c) the shape reads FLAT. With the share near 0.5,
  the acceleration's 2 SE at 16 phases (0.027) is wider than the acceleration that noise gives (+0.012). The shape
  sees a cost per conditional only if its acceleration is large against about 0.02-0.03.
- n = 8 holds up to 16 CZ and 35 conditionals per circuit (2, 5, 9, 14, 20 at n = 2 … 6; 27 at n = 7); parked depth grows with n.
- Illustrative noise only; the expectation is an extrapolation from one night.

## Device procedure (home)

```
# psf-os v0.3.1 (7caedaa), checked clean; the notebook at the declaring commit
python gpu/daily_fetch.py fetch_in
DEV=$(python gpu/qpe_long_parked_night.py pick fetch_in)
python gpu/qpe_long_parked_night.py build fetch_in/$DEV/dev OUT --plan P
python gpu/qpe_long_parked_night.py check OUT                         # PASS
python -m psf_os submit OUT/job0 ; python -m psf_os collect OUT/job0
python gpu/qpe_long_parked_night.py score OUT
```
