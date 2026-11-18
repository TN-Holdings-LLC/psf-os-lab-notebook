# The time a feed-forward decision costs, 2026-11-18 on ibm_marrakesh (`prereg/timing_night_2026-11-18.md`)

- Declared with 81ea6357 (pushed with the night's main push, 11:12:46 CET; reflog as in
  `results/balanced-repeat-2026-11-18`). The night's device record (`fetch_in/`, fetched 11:17:03 CET; marrakesh
  calibration 2026-11-18 10:40 CET). dt read from the device at home: 4 ns (`dt.json`). Built on the owner's machine
  from the declared checkout (`versions.txt`); pre-run check PASS for both jobs (fast-path shape: C, D, F 4 / 8 / 16
  of their conditionals; K and DK none, every block holds a CZ).

| job | folder | id | circuits | s model | s charged | created - finished (CET) |
|---|---|---|---|---|---|---|
| A (ruler, M, C, F, D) | `tmA/` | dbunp0nf8rhs73bmk81g | 43 | 51.0 | 52 | 11:22:58 - 11:24:03 |
| B (ruler, MK, K, DK) | `tmB/` | dbunp2darooc73fk9f00 | 37 | 44.3 | 45 | 11:23:05 - 11:25:10 |

## Verdicts (`python gpu/timing_night.py score tmA tmB --dt-file dt.json`; written to `tmA/timing_scores.json`)

```
job A ruler, clock 0 (us, loss): 0.0 0.003, 8.1 0.127, 16.0 0.214, 32.0 0.358, 48.0 0.418, 64.0 0.455
job A ruler, clock 1 (us, loss): 0.0 0.001, 8.1 0.068, 16.0 0.117, 32.0 0.181, 48.0 0.242, 64.0 0.297
  s_M 2.780 us per step (SE 0.142)   s_C 3.098 (0.153)   s_F 3.070 (0.279)   s_D 2.978 (0.258)
job B ruler, clock 0 (us, loss): 0.0 0.009, 8.1 0.138, 16.0 0.246, 32.0 0.362, 48.0 0.432, 64.0 0.456
job B ruler, clock 1 (us, loss): 0.0 0.004, 8.1 0.058, 16.0 0.104, 32.0 0.182, 48.0 0.252, 64.0 0.297
  s_MK 2.609 (0.122)   s_K 2.874 (0.161)   s_DK 2.882 (0.274)
fast-path decision latency s_C - s_M +0.317 us (2 SE 0.417) -> NOT RESOLVED
two fast-path actors s_D / s_C 0.96 (2 SE 0.19) -> IN PARALLEL
two actors with a CZ s_DK / s_K 1.00 (2 SE 0.22) -> IN PARALLEL
```

## Against the declaration

| prediction | numbers | |
|---|---|---|
| T-1 the fast-path latency RESOLVED | +0.32 us, 2 SE 0.42 | failed |
| T-2 two fast-path actors IN PARALLEL | ratio 0.96, 2 SE 0.19 | held |
| T-3 two actors with a CZ WAIT FOR EACH OTHER | ratio 1.00, 2 SE 0.22: IN PARALLEL | failed |

## Two numbers side by side

- Vanity: the clocks read a measurement step as 2.78 us (job A) and 2.61 us (job B), and both kinds of conditional
  pair ran side by side with no sign of waiting.
- Essence: the instrument resolves about 0.4 us (2 SE); a decision cost below that, fast path or CZ, is not seen.
  Waiting between two decisions on this scale (a ratio of 2 if fully serial) is ruled out for both kinds.

## Beside, never judged

- CZ-path latency s_K - s_M +0.27 us (2 SE 0.40); s_K - s_C -0.22 us (2 SE 0.44, two jobs); fired minus unfired
  (F - C) -0.03 us (2 SE 0.64).
- With P-B of the same night (`results/parallel-night-2026-11-18`): two conditional items side by side cost the
  first item 0.06 in success, while the clocks see no waiting between two conditional actors. The packing loss is not
  explained by the decisions waiting for each other at this resolution.

## Independent check

The home VS fitted the ruler with its own code (`notes/verify_2026-11-18/`): every slope equal (4e-16 us); T-1 to T-3
the same under four fit forms.

## Reproduce

`python reproduce.py --psf-os PATH_TO_PSF_OS_AT_0f57c76 timing-night-2026-11-18` (SAME, 2026-11-18).
