# Daily record (prereg/daily/standing_rules.md)

Raw values, no correction. AGREES: |M - M_exact| <= 0.05. BEATS: MSE below the better trivial guess. Every night and
device is a line, failures included.

| date (CET) | device | problem | RUNS | READS | AGREES | BEATS | M - M_exact | MSE / trivial guess | floor | sentinel | job |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-05 | ibm_marrakesh | FX-A (fixed) | yes | READS | AGREES | BEATS | -0.024 | 0.0023 / 0.0264 | 0.952 | CLEAN | dbm5hgd8mdtc73d7bang |
| 2026-11-05 | ibm_marrakesh | D02 | yes | READS | DIFFERS | BEATS | -0.111 | 0.0162 / 0.0482 | 0.954 | CLEAN | dbm5hgd8mdtc73d7bang |
| 2026-11-05 | ibm_fez | FX-A (fixed) | yes | READS | AGREES | BEATS | -0.043 | 0.0033 / 0.0264 | 0.968 | DEAD | dbm5hid8ft8s738u88g0 |
| 2026-11-05 | ibm_fez | D02 | yes | READS | DIFFERS | BEATS | -0.147 | 0.0354 / 0.0482 | 0.969 | DEAD | dbm5hid8ft8s738u88g0 |
| 2026-11-06 | ibm_marrakesh | FX-A (fixed) | yes (alone) | READS | AGREES | BEATS | -0.008 | 0.0016 / 0.0264 | 0.977 | DEAD | dbmqhbu74qds73dsrde0 |
| 2026-11-06 | ibm_marrakesh | D03 | REFUSED | - | - | - | - | - | - | - | (failed qubits 46, 73, 82 hit every copy; amendment 2026-11-06: FX-A run alone) |
| 2026-11-07 | ibm_fez | FX-A (fixed) | yes (copy drow 4) | READS | AGREES | BEATS | -0.038 | 0.0039 / 0.0264 | 0.966 | DEAD | dbn5ludt7fqc73aivq60 |
| 2026-11-07 | ibm_fez | D04 | yes | READS | AGREES | BEATS | +0.010 | 0.0030 / 0.2362 | 0.978 | DEAD | dbn5ludt7fqc73aivq60 |
| 2026-11-08 | - | - | not run | - | - | - | - | - | - | - | (no daily run under the standing rules; other declared tests ran) |
| 2026-11-09 | - | - | not run | - | - | - | - | - | - | - | (no daily run under the standing rules; other declared tests ran) |
| 2026-11-10 | - | - | not run | - | - | - | - | - | - | - | (no daily run under the standing rules; other declared tests ran) |
| 2026-11-11 | - | - | not run | - | - | - | - | - | - | - | (no daily run under the standing rules; other declared tests ran) |
| 2026-11-12 | - | - | not run | - | - | - | - | - | - | - | (no daily run under the standing rules; other declared tests ran) |
| 2026-11-13 | - | - | not run | - | - | - | - | - | - | - | (no daily run under the standing rules; other declared tests ran) |
| 2026-11-14 | ibm_marrakesh | FX-A (fixed) | yes | READS | AGREES | BEATS | -0.012 | 0.0013 / 0.0264 | 0.983 | DEAD | dbs3c7vv5hds73dignng |
| 2026-11-14 | ibm_marrakesh | D05 | yes | READS | AGREES | BEATS | +0.005 | 0.0010 / 0.0052 | 0.981 | DEAD | dbs3c7vv5hds73dignng |
| 2026-11-14 | ibm_fez | FX-A (fixed) | yes (copy drow 4) | READS | AGREES | BEATS | -0.042 | 0.0032 / 0.0264 | 0.965 | DEAD | dbs3c9ejjaos73ajnvu0 |
| 2026-11-14 | ibm_fez | D05 | yes (copy drow 4) | READS | AGREES | BEATS | -0.020 | 0.0017 / 0.0052 | 0.965 | DEAD | dbs3c9ejjaos73ajnvu0 |
| 2026-11-15 | ibm_marrakesh | FX-A (fixed) | yes | READS | AGREES | BEATS | -0.004 | 0.0073 / 0.0264 | 0.975 | DEAD | dbsqfm8k09pc73b0glq0 |
| 2026-11-15 | ibm_marrakesh | D06 | yes | READS | AGREES | BEATS | -0.050 | 0.0170 / 0.2229 | 0.974 | DEAD | dbsqfm8k09pc73b0glq0 |
| 2026-11-16 | ibm_marrakesh | FX-A (fixed) | yes | READS | AGREES | BEATS | -0.014 | 0.0044 / 0.0264 | 0.982 | DEAD | dbtddunq0h0s73bkkok0 |
| 2026-11-16 | ibm_marrakesh | D07 | yes | READS | DIFFERS | BEATS | -0.056 | 0.0140 / 0.1582 | 0.936 | DEAD | dbtddunq0h0s73bkkok0 |
| 2026-11-16 | ibm_kingston | FX-A (fixed) | yes | READS | AGREES | BEATS | -0.007 | 0.0012 / 0.0264 | 0.978 | CLEAN | dbtde0nq0h0s73bkkomg |
| 2026-11-16 | ibm_kingston | D07 | yes | READS | AGREES | BEATS | -0.014 | 0.0008 / 0.1582 | 0.986 | CLEAN | dbtde0nq0h0s73bkkomg |

FX-A before the record (the same circuit as the practice test's p4_b0.485_t12, 2026-11-04 13:32 / 13:57 CET):
marrakesh -0.022, fez -0.041.

## Reported beside the judgements (added 2026-11-05 evening by the owner's decision; the judgements are unchanged)

R = M / M_exact; slope = per-qubit fit of measured on exact through 0; "after scale": MSE left after that one scale;
decay per CZ layer = -ln(slope) / (CZ layers of the compiled circuit).

| date | device | problem | R | slope | MSE -> after scale | CZ layers | decay / layer |
|---|---|---|---|---|---|---|---|
| 2026-11-05 | ibm_marrakesh | FX-A | 0.846 | 0.838 | 0.0023 -> 0.0016 | 25 | 0.0070 |
| 2026-11-05 | ibm_marrakesh | D02 | 0.860 | 0.860 | 0.0162 -> 0.0036 | 40 | 0.0038 |
| 2026-11-05 | ibm_fez | FX-A | 0.732 | 0.723 | 0.0033 -> 0.0013 | 25 | 0.0130 |
| 2026-11-05 | ibm_fez | D02 | 0.816 | 0.811 | 0.0354 -> 0.0125 | 40 | 0.0052 |
| 2026-11-06 | ibm_marrakesh | FX-A | 0.949 | 0.957 | 0.0016 -> 0.0016 | 25 | 0.0017 |
| 2026-11-07 | ibm_fez | FX-A | 0.763 | 0.739 | 0.0039 -> 0.0021 | 25 | 0.0121 |
| 2026-11-07 | ibm_fez | D04 | 1.022 | 1.014 | 0.0030 -> 0.0030 | 26 | -0.0005 |
| 2026-11-14 | ibm_marrakesh | FX-A | 0.923 | 0.900 | 0.0013 -> 0.0011 | 25 | 0.0042 |
| 2026-11-14 | ibm_marrakesh | D05 | None (exact below 0.1) | 0.976 | 0.0010 -> 0.0010 | 21 | 0.0012 |
| 2026-11-14 | ibm_fez | FX-A | 0.732 | 0.716 | 0.0032 -> 0.0011 | 25 | 0.0134 |
| 2026-11-14 | ibm_fez | D05 | None (exact below 0.1) | 0.610 | 0.0017 -> 0.0009 | 21 | 0.0235 |
| 2026-11-15 | ibm_marrakesh | FX-A | 0.973 | 0.958 | 0.0073 -> 0.0072 | 25 | 0.0017 |
| 2026-11-15 | ibm_marrakesh | D06 | 0.891 | 0.882 | 0.0170 -> 0.0139 | 46 | 0.0027 |
| 2026-11-16 | ibm_marrakesh | FX-A | 0.915 | 0.917 | 0.0044 -> 0.0042 | 25 | 0.0035 |
| 2026-11-16 | ibm_marrakesh | D07 | 0.907 | 0.912 | 0.0140 -> 0.0111 | 31 | 0.0030 |
| 2026-11-16 | ibm_kingston | FX-A | 0.956 | 0.939 | 0.0012 -> 0.0011 | 25 | 0.0025 |
| 2026-11-16 | ibm_kingston | D07 | 0.977 | 0.979 | 0.0008 -> 0.0006 | 31 | 0.0007 |
