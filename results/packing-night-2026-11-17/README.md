# Single against packed, fourth round of 2026-11-17 on ibm_marrakesh (`prereg/packing_night_2026-11-17.md`)

- Declaration pushed 15:21:04 CET (reflog "5b965be8 refs/remotes/origin/main@{2026-11-17 15:21:04 +0100}: update by
  push"); psf-os 0f57c76 pushed just before it. Queue read with the device record: marrakesh 0, fez 0, kingston 37 ->
  ibm_marrakesh. Device record fetched 15:21:43 CET (calibration 2026-11-13 18:22 CET; failed qubits 82, 94, 113, 119,
  130; coupler 113-119) (`fetch_in/`). Tools as of 5b965be8 with psf-os 0f57c76.
- Pre-run check PASS (checks 1-5, `check.json`). Both jobs returned byte-identical. DD and twirling off, no mitigation,
  4000 shots per circuit. Sentinel DEAD in both (beside).

| job | folder | id | submitted | circuits | s model | s charged |
|---|---|---|---|---|---|---|
| single | `single1/` | dbu66povv3fc73c0rtc0 | 15:23:35 CET | 34 | 40.9 | 41 |
| packed | `packed/` | dbu66rae8crs738b4i5g | 15:23:42 CET | 7 | 10.8 | 11 |

The device finished the single job at 15:32:58 and the packed job at 15:33:25 CET (the declared order).

## Verdict (`python gpu/packing_night.py score .`)

```
rd1: single 0.8520  packed 0.4265  noiseless 0.8904  d -0.4255 (2 SE 0.0193) -> beside: PACKED KEEPS LESS
rd2: single 0.7345  packed 0.4510  noiseless 0.7929  d -0.2835 (2 SE 0.0210) -> beside: PACKED KEEPS LESS
rd3: single 0.7052  packed 0.4333  noiseless 0.7060  d -0.2720 (2 SE 0.0213) -> beside: PACKED KEEPS LESS
rd4: single 0.5155  packed 0.2510  noiseless 0.6286  d -0.2645 (2 SE 0.0209) -> beside: PACKED KEEPS LESS
rd5: single 0.6678  packed 0.6713  noiseless 0.5597  d -0.0035 (2 SE 0.0210) -> beside: SAME WITHIN ERROR
ea1: single 0.8635  packed 0.6070  noiseless 0.8904  d -0.2565 (2 SE 0.0189) -> beside: PACKED KEEPS LESS
ea2: single 0.6558  packed 0.4852  noiseless 0.7929  d -0.1705 (2 SE 0.0218) -> beside: PACKED KEEPS LESS
ea3: single 0.6478  packed 0.4620  noiseless 0.7060  d -0.1858 (2 SE 0.0218) -> beside: PACKED KEEPS LESS
ea4: single 0.6020  packed 0.4988  noiseless 0.6286  d -0.1032 (2 SE 0.0221) -> beside: PACKED KEEPS LESS
ea5: single 0.5528  packed 0.5523  noiseless 0.5597  d -0.0005 (2 SE 0.0222) -> beside: SAME WITHIN ERROR
mean d over 10 items -0.1966 (2 SE 0.0067) -> PACKING KEEPS LESS
```

## Against the declaration

| prediction | numbers | |
|---|---|---|
| PK-1 the verdict is not PACKING KEEPS LESS | mean d -0.197 (2 SE 0.007): PACKING KEEPS LESS | failed |
| PK-2 packed charged below a third of single | 11 s against 41 s (0.27) | held |

## Two numbers side by side

- Vanity: packing cut the charged device time from 41 s to 11 s for the same ten items.
- Essence: the packed control arm kept 0.20 less on average, up to 0.43 less (rd1); eight of ten items lost beyond
  2 SE. As built and on this night, packing feed-forward items saves time by giving up most of what the control does.

## Beside, never judged

- The large change is in the control (ff) arm only. The off arm (no conditionals) agrees packed and single within
  0.03 for every item (rd1 0.885 / 0.889); its post-selected view within 0.03 except rd4 (0.570 / 0.503) and ea5
  (0.571 / 0.509); the floors within 0.01 except ea2, ea4, ea5 (0.401 / 0.319, 0.782 / 0.874, 0.917 / 0.948). The
  cost is tied to the conditionals running side by side in one circuit, not to the mid-circuit measurements or the
  gates, which the off arm also holds.
- In the packed ff arm the share of shots still failing after the second try is lower than in the single ff arm for
  most items (rd1 0.051 against 0.106; ea1 0.054 against 0.120; ea4 0.134 against 0.222): the second try does not
  behave as it does alone.
- rd5 and ea5, the longest item of each kind, did not move. In the single job rd5 already reads above its noiseless
  value (0.668 against 0.560) and below its own off arm (0.805).
- ea2 (physical qubits 46-49) keeps all zeros in its floor in only 0.401 (single) and 0.319 (packed) of the shots.
- Execution time reported by the device: 38.6 s for the single job (34 circuits), 9.1 s for the packed job (7
  circuits).
- Not known from these records: how the device's controller schedules independent conditionals in one circuit
  (whether a decision on one item holds the others, or something else). The ledger assumed it does not; the data say
  the packed ff arm differs. Which mechanism it is needs its own declared test.

## Reproduce

`python reproduce.py --psf-os PATH_TO_PSF_OS_AT_0f57c76 packing-night-2026-11-17` (SAME, 2026-11-17).
