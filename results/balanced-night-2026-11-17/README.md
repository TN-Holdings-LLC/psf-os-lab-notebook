# The frame-balanced neuron chain, third round of 2026-11-17 on ibm_marrakesh (`prereg/balanced_night_2026-11-17.md`)

- Declaration pushed 12:50:42 CET (2b0148e7). Queue read 12:51:18 CET: marrakesh 3, fez 0, kingston 10 ->
  ibm_marrakesh (the first qualifying device in the declared order). Device record fetched 12:51:33 CET (calibration
  2026-11-13 18:22 CET; failed qubits 82, 94, 113, 119, 130; coupler 113-119) (`fetch_in/`). The same device and the
  same record date as the second round and the prescription loop of this night. psf-os 301ac01; the tools as of
  2b0148e7.
- Job dbu40l49po4c73ceh8h0 (submitted 12:53:54 CET; 34 circuits, 4000 shots each; DD and twirling off, no
  mitigation): 40.9 s by the model, 41 s charged. Pre-run check PASS; returned byte-identical. Sentinel DEAD (beside,
  never judged). Floor arms keep all zeros in 0.951-0.999 of the shots.

## Verdicts (`python gpu/balanced_night.py score .`)

```
L 1: rd 0.902  nf 0.647  pooled 0.775 (noiseless 0.890, -0.116)  g -0.019 (2 SE 0.009) -> NOT BEYOND
L 2: rd 0.744  nf 0.631  pooled 0.688 (noiseless 0.793, -0.105)  g +0.057 (2 SE 0.010) -> BEYOND THE CORRECTION CEILING
L 3: rd 0.660  nf 0.455  pooled 0.558 (noiseless 0.706, -0.148)  g +0.057 (2 SE 0.011) -> BEYOND THE CORRECTION CEILING
L 4: rd 0.580  nf 0.383  pooled 0.481 (noiseless 0.629, -0.147)  g +0.083 (2 SE 0.011) -> BEYOND THE CORRECTION CEILING
L 5: rd 0.528  nf 0.338  pooled 0.433 (noiseless 0.560, -0.127)  g +0.117 (2 SE 0.011) -> BEYOND THE CORRECTION CEILING
slope of the pooled g over L +0.0311 (2 SE 0.0032) -> COMPOUNDS
```

## Against the declaration

| prediction | numbers | |
|---|---|---|
| B-1 no L overshoots (the pool) | the pool is 0.105-0.148 below its noiseless value at every L | held |
| B-2 BEYOND at every L = 1 .. 5 | L = 1 NOT BEYOND (g -0.019); L = 2 .. 5 BEYOND | failed |
| B-3 COMPOUNDS | slope +0.0311 (2 SE 0.0032), no overshoot | held |

## Two numbers side by side

- Vanity: the pooled value is beyond the off arm's correction ceiling at L = 2 .. 5 and the margin grows with depth
  (+0.057 -> +0.117), with the one-sided decay lean removed by construction (no L overshoots).
- Essence: the pool keeps 0.87 / 0.87 / 0.79 / 0.77 / 0.77 of its noiseless value. The two frames are far apart:
  rd keeps 1.01 / 0.94 / 0.94 / 0.92 / 0.94 of the noiseless value, nf 0.73 / 0.80 / 0.64 / 0.61 / 0.60. At L = 1
  the pool is further from the exact value than the off circuit's noiseless value is (c 0.143).

## Beside, never judged

- Per item, CLOSER WITH CONTROL in all ten (d = |off - exact| - |ff - exact|): rd +0.069 / +0.104 / +0.069 / +0.109
  / +0.117, nf +0.057 / +0.084 / +0.088 / +0.103 / +0.102 (2 SE_d 0.015-0.022).
- rd alone against its noiseless value: +0.012 at L = 1 (above it again, as in N2 and the loop's L = 1), then -0.049
  / -0.046 / -0.049 / -0.032. The rd off arm also reads above its noiseless value at L = 1, 3, 4, 5 (0.834 / 0.592 /
  0.472 / 0.411 against 0.794 / 0.501 / 0.398 / 0.316); the nf off arm reads below it everywhere: the lean the
  balanced pair was built to cancel, seen in both arms.
- nf1 reads its output on physical qubit 1; the prescription loop's Dr an hour earlier on the same device and record
  gave P(read 1 | |1>) 0.826 on that qubit against P(read 0 | |0>) 0.9995. In the nf frame logical 1 is read as |1>,
  so that gap falls on success; in rd it falls on failure. The illustrative desk model had no readout asymmetry of
  this size; it predicted the pool's margin positive at every L.
- rd against the first round's T2 (the same circuits; fez, earlier this night): fez 0.869 / 0.738 / 0.653 / 0.562 /
  0.474, marrakesh 0.902 / 0.744 / 0.660 / 0.580 / 0.528 (+0.033 / +0.005 / +0.008 / +0.019 / +0.054, 2 SE 0.014 -
  0.022). Another device; no device comparison is read from these.
- Post-selected (beside, the tools' own `post` card): rd 0.941 / 0.814 / 0.748 / 0.584 / 0.497, nf 0.696 / 0.684 / 0.444
  / 0.328 / 0.231.

## Reproduce

`python reproduce.py --psf-os PATH_TO_PSF_OS_AT_301ac01 balanced-night-2026-11-17` (SAME, 2026-11-17).
