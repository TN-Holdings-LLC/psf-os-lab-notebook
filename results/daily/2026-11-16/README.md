# Daily record, day 6 (2026-11-16; standing rules and the amendment of 11-06; notice `prereg/night_2026-11-16.md`)

- Notice pushed 11:06:24 CET; queue read 11:07:12 CET: marrakesh 0, fez 131, kingston 0 -> ibm_marrakesh and
  ibm_kingston. Problems FX-A (fixed) and D07 (pool order). psf-os 0.1.1.
- marrakesh record (fetched 11:07:17 CET; calibration 2026-11-13 18:22 CET, the same as days 4 and 5): failed qubits
  82, 94, 113, 119, 130, coupler 113-119. kingston record (fetched 11:07:22 CET; calibration 2026-11-13 15:57 CET):
  failed qubits 112, 113, 121, 146, couplers 112-113, 130-131, 145-146, 146-147. FX-A and D07 at copy (0, 0) on both.
  The two jobs have the same circuits (circuits_sha256 6a138c236750... on both: the same layout on the same coupling
  graph, no failed mark in its way).
- Jobs: marrakesh dbtddunq0h0s73bkkok0 (submitted 11:12:11 CET), kingston dbtde0nq0h0s73bkkomg (11:12:19 CET); 10
  circuits, 4000 shots, 14.2 s by the model, 13 s charged each. Built here from the fetched records before the run; the
  jobs returned byte-identical to the ones built.

| device | problem | READS | AGREES | BEATS | M - M_exact | MSE / guess | floor | retention | slope | sentinel |
|---|---|---|---|---|---|---|---|---|---|---|
| marrakesh | FX-A | READS | AGREES | BEATS | -0.014 | 0.0044 / 0.0264 | 0.982 | 0.915 | 0.917 | DEAD |
| marrakesh | D07 | READS | DIFFERS | BEATS | -0.056 | 0.0140 / 0.1582 | 0.936 | 0.907 | 0.912 | DEAD |
| kingston | FX-A | READS | AGREES | BEATS | -0.007 | 0.0012 / 0.0264 | 0.978 | 0.956 | 0.939 | CLEAN |
| kingston | D07 | READS | AGREES | BEATS | -0.014 | 0.0008 / 0.1582 | 0.986 | 0.977 | 0.979 | CLEAN |

D07 on marrakesh: M - M_exact = -0.0563 against the bound 0.05 (two SE 0.004): DIFFERS. The same circuits on kingston
give -0.014. FX-A on marrakesh: -0.024 (11-05), -0.008 (11-06), -0.012 (11-14), -0.004 (11-15), -0.014 (tonight).
Kingston's first daily line; its sentinel is CLEAN. The marrakesh sentinel was CLEAN on 11-05 and has been DEAD since.

## Reproduce

`python reproduce.py daily-2026-11-16-marrakesh daily-2026-11-16-kingston` (SAME, 2026-11-16).
