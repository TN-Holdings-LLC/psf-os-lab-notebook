# Daily record, day 5 (2026-11-15; standing rules and the amendment of 11-06; notice `prereg/night_2026-11-15.md`)

- Notice pushed 13:33:52 CET; queue read 13:34:18 CET: marrakesh 0, fez 61, kingston 257 -> ibm_marrakesh only.
  Problems FX-A (fixed) and D06 (pool order). psf-os 0.1.1.
- marrakesh record (fetched 13:34:24 CET; calibration 2026-11-13 18:22 CET, the same as day 4): failed qubits 82, 94,
  113, 119, 130, coupler 113-119; FX-A and D06 at (0, 0). Job dbsqfm8k09pc73b0glq0, 10 circuits, 4000 shots,
  14.2 s by the model, submitted 13:38:49 CET. The job was built at 13:36 CET in a work folder and rebuilt here from
  the same device record after the run: circuits.qpy byte-identical (circuits_sha256 1a1a27913ad1...); the manifest
  is the submitted one.

| device | problem | READS | AGREES | BEATS | M - M_exact | MSE / guess | floor | retention | slope | sentinel |
|---|---|---|---|---|---|---|---|---|---|---|
| marrakesh | FX-A | READS | AGREES | BEATS | -0.004 | 0.0073 / 0.0264 | 0.975 | 0.973 | 0.958 | DEAD |
| marrakesh | D06 | READS | AGREES | BEATS | -0.050 | 0.0170 / 0.2229 | 0.974 | 0.891 | 0.882 | DEAD |

D06's AGREES is at the line: M - M_exact = -0.04992 against the bound 0.05 (two SE 0.005). FX-A on marrakesh:
M - M_exact -0.024 (11-05), -0.008 (11-06), -0.012 (11-14), -0.004 (tonight). The marrakesh sentinel was CLEAN on
11-05 and has been DEAD since.
