# Two packing tests, 2026-11-18 on ibm_marrakesh (`prereg/parallel_night_2026-11-18.md`)

- Declarations pushed 11:12:46 CET (16d14fc8; reflog as in `results/balanced-repeat-2026-11-18`). The same device
  record (`fetch_in/`, fetched 11:17:03 CET, marrakesh calibration 2026-11-18 10:40 CET). Built on the owner's machine
  (`versions.txt`), pre-run check PASS (`check.json`; B3's B starts 21.12 us after the start, A ends at 14.85 / 16.85
  us at latency 0 / 1 us). Rebuilt at home: every user, off and floor circuit byte-identical; only the four ring-
  sentinel circuits differ in their compiled bytes (environment; never judged).

| job | folder | id | circuits | s model | s charged | created - finished (CET) |
|---|---|---|---|---|---|---|
| P-A | `pa/` | dbunmmvf8rhs73bmk5i0 | 37 | 44.3 | 44 | 11:18:03 - 11:19:55 |
| P-B | `pb/` | dbunmon82tmc73dto28g | 19 | 24.2 | 24 | 11:18:10 - 11:20:17 |

## Verdicts (`python gpu/parallel_night.py score .`)

```
P-A  mean d over 10 items +0.0012 (2 SE 0.0066) -> SAME WITHIN ERROR
     (per item: nine SAME WITHIN ERROR; rd4 d -0.0262, 2 SE 0.0221, beside: PACKED KEEPS LESS)
P-B  b1a against sa: alone 0.5655  packed 0.5508  d -0.0147 (2 SE 0.0222)
     b2a against sa: alone 0.5655  packed 0.5052  d -0.0603 (2 SE 0.0223)
     b2b against sb: alone 0.6895  packed 0.7015  d +0.0120 (2 SE 0.0206)
     b3a against sa: alone 0.5655  packed 0.5035  d -0.0620 (2 SE 0.0223)
     b3b against sb: alone 0.6895  packed 0.6930  d +0.0035 (2 SE 0.0207)
     B1 mean d -0.0147 (2 SE 0.0222) -> SAME WITHIN ERROR
     B2 mean d -0.0241 (2 SE 0.0152) -> PACKED KEEPS LESS
     B3 mean d -0.0292 (2 SE 0.0152) -> PACKED KEEPS LESS
```

## Against the declaration

| prediction | numbers | |
|---|---|---|
| PA-1 P-A not PACKING KEEPS LESS | SAME WITHIN ERROR (mean d +0.0012) | held |
| PB-1 B2 PACKED KEEPS LESS | mean d -0.024 (2 SE 0.015) | held |
| PB-2 B1 SAME WITHIN ERROR | mean d -0.015 (2 SE 0.022) | held |
| PB-3 B3 SAME WITHIN ERROR | PACKED KEEPS LESS, mean d -0.029 (2 SE 0.015) | failed |

## Two numbers side by side

- Vanity (P-A): the ten off arms packed in one circuit read as they read alone (mean difference +0.001); the
  production form, the ff arms alone and the fixed circuits packed, needs 16 circuits and 20.9 s by the model against
  34 circuits and 40.9 s; the CLOSER WITH CONTROL verdict is the same with the packed and with the single off arm for
  all ten items (eight CLOSER; rd1 and rd2 NOT CLOSER tonight either way).
- Essence (P-B): one conditional neighbour costs the item on segment A 0.06 (b2a, b3a), each beyond 2 SE alone, while
  the item on segment B does not move (b2b +0.012, b3b +0.004). Delaying B past A's whole duration (as written) did
  not remove A's loss.

## Reading (the table fixed in the declaration; beside)

B1 same, B2 less, B3 less: "the loss needs two conditional items in one circuit, whatever their timing (or the delay
is not kept by the device as written)". Not fixed beforehand and only a description: the loss sits on A alone, the
item whose decisions come first on the written schedule; B, whose conditionals come later (B2) or only after A has
ended (B3), keeps what it keeps alone.

## Beside, never judged

- The share still failing after the second try barely moves (A: 0.193 alone, 0.184 / 0.180 in B2 / B3), unlike the
  ten-item pack of 2026-11-17 (0.106 -> 0.051 for rd1).
- B1's B (rd2's off arm packed beside a conditional item) 0.7278 against sb's off arm 0.7323 (d +0.005, 2 SE 0.020).
- P-A off arms read above their noiseless values for nine of ten items (all but ea2; e.g. rd1 0.858 against 0.794),
  alone and packed alike: the decay lean of the read-flipped frame, the same in both.
- Sentinels: P-A DEAD, P-B CLEAN.

## Reproduce

`python reproduce.py --psf-os PATH_TO_PSF_OS_AT_0f57c76 parallel-night-2026-11-18` (SAME, 2026-11-18).
