# The distance-3 repetition code decoded in real time, its result used at once by a T, 2026-11-19 on ibm_marrakesh (`prereg/repcode_night_2026-11-19.md`)

- Declared in be3147c7. Built on the owner's machine (`versions.txt`) from the loop's device record of the night;
  pre-run check PASS (40 circuits; conditionals 144, broadcasts 48, at most 7 conditionals per circuit). Job
  dbvct57f8rhs73bnn760, 4000 shots, 47.6 s by the model, 45 s charged, 11:25:24 - 11:26:38 CET.
- `python gpu/repcode_night.py score .` (`score.txt`, `repcode_scores.json`):

```
ceiling: lut3 c[0] right 0.8121 (2 SE 0.0062, 16000 shots) against C 0.8750 -> NOT BEYOND (margin -0.0629); off as read 0.7204
within: lut3 0.8121 - lut1 0.8224 = -0.0102 (2 SE 0.0086) -> MORE TESTS KEEP LESS        (beside, not judged)
padded: lut5 0.8090 - lut3 0.8121 = -0.0031 (2 SE 0.0088) -> SAME WITHIN ERROR           (beside, not judged)
   added_tests_never_fire (e = 0, 1, 2) = (b0): +0.0021 (2 SE 0.0097) -> SAME WITHIN ERROR
   added_tests_fire (e = n)            = (b1): -0.0187 (2 SE 0.0192) -> SAME WITHIN ERROR
per error: n: lut3 0.765 lut1 0.786 lut5 0.747 off 0.774; 0: lut3 0.847 lut1 0.864 lut5 0.856 off 0.456;
           1: lut3 0.839 lut1 0.836 lut5 0.837 off 0.850; 2: lut3 0.797 lut1 0.804 lut5 0.796 off 0.801; sentinel CLEAN
```

## Against the declaration

| prediction | numbers | |
|---|---|---|
| RC-1 lut3 is BEYOND THE CEILING | 0.8121 against C 0.875 + 2 SE: NOT BEYOND (margin -0.063) | failed |
| RC-2 (b0), the added tests never fire: SAME WITHIN ERROR | +0.0021 (2 SE 0.0097) | held |
| (b1), they fire: no direction declared | -0.0187 (2 SE 0.0192), SAME WITHIN ERROR | read, not a prediction |

## Two numbers side by side

- Vanity: decoding in real time and acting at once on the T lifts the right answer from 0.720 (off arm as read) to
  0.812; with X on data qubit 0 (where the off arm reads 0.456 against its ceiling 0.5) to 0.847.
- Essence: the ceiling (the best a later decoder could do with the off arm's record, noiseless) is 0.875, and the
  device's real-time version stays 0.063 below it: on this night the code's own noise (14-16 CZ, two mid-circuit
  measurements, five conditionals) costs more than real-time decoding gains. Unfired conditionals cost nothing
  measurable ((b0)); one test inside an item is read 0.010 better than three (beside).

## Reproduce

`python reproduce.py repcode-night-2026-11-19`
