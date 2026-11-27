## 1. Counts, all devices together

| kind | device | sets | findings | column | IBM hit | hit rate | chance | hit / chance | IBM miss | our miss |
|---|---|---|---|---|---|---|---|---|---|---|
| mirror_low | all | 409 | 721 | T1 | 149 | 0.207 | 0.128 | 1.62 | 572 | 1545 |
| mirror_low | all | 409 | 721 | T2 | 65 | 0.090 | 0.128 | 0.71 | 656 | 1629 |
| mirror_low | all | 409 | 721 | any | 430 | 0.596 | 0.441 | 1.35 | 291 | 5380 |
| mirror_low | all | 409 | 721 | cz | 352 | 0.488 | 0.214 | 2.29 | 369 | 2416 |
| mirror_low | all | 409 | 721 | readout_error | 201 | 0.279 | 0.128 | 2.17 | 520 | 1502 |
| r_low | all | 12 | 14 | T1 | 0 | 0.000 | 0.171 | 0.00 | 14 | 12 |
| r_low | all | 12 | 14 | T2 | 6 | 0.429 | 0.171 | 2.50 | 8 | 6 |
| r_low | all | 12 | 14 | any | 7 | 0.500 | 0.443 | 1.13 | 7 | 23 |
| r_low | all | 12 | 14 | cz | 7 | 0.500 | 0.343 | 1.46 | 7 | 17 |
| r_low | all | 12 | 14 | readout_error | 6 | 0.429 | 0.171 | 2.50 | 8 | 6 |
| scan_listed | all | 62 | 539 | T1 | 65 | 0.121 | 0.118 | 1.02 | 474 | 273 |
| scan_listed | all | 62 | 539 | T2 | 85 | 0.158 | 0.118 | 1.33 | 454 | 253 |
| scan_listed | all | 62 | 539 | any | 314 | 0.583 | 0.458 | 1.27 | 225 | 968 |
| scan_listed | all | 62 | 539 | cz | 181 | 0.336 | 0.194 | 1.73 | 358 | 381 |
| scan_listed | all | 62 | 539 | readout_error | 70 | 0.130 | 0.119 | 1.09 | 469 | 269 |
| sentinel_dead | all | 109 | 794 | T1 | 66 | 0.083 | 0.125 | 0.66 | 728 | 479 |
| sentinel_dead | all | 109 | 794 | T2 | 95 | 0.120 | 0.125 | 0.96 | 699 | 450 |
| sentinel_dead | all | 109 | 794 | any | 430 | 0.542 | 0.460 | 1.18 | 364 | 1576 |
| sentinel_dead | all | 109 | 794 | cz | 222 | 0.280 | 0.216 | 1.29 | 572 | 721 |
| sentinel_dead | all | 109 | 794 | readout_error | 161 | 0.203 | 0.127 | 1.60 | 633 | 391 |
| sentinel_weak | all | 109 | 0 | T1 | 0 |  | 0.125 |  | 0 | 545 |
| sentinel_weak | all | 109 | 0 | T2 | 0 |  | 0.125 |  | 0 | 545 |
| sentinel_weak | all | 109 | 0 | any | 0 |  | 0.460 |  | 0 | 2006 |
| sentinel_weak | all | 109 | 0 | cz | 0 |  | 0.216 |  | 0 | 943 |
| sentinel_weak | all | 109 | 0 | readout_error | 0 |  | 0.127 |  | 0 | 552 |

## 2. Counts per device

| kind | device | sets | findings | column | IBM hit | hit rate | chance | hit / chance | IBM miss | our miss |
|---|---|---|---|---|---|---|---|---|---|---|
| mirror_low | ibm_fez | 211 | 530 | T1 | 114 | 0.215 | 0.128 | 1.67 | 416 | 744 |
| mirror_low | ibm_fez | 211 | 530 | T2 | 26 | 0.049 | 0.128 | 0.38 | 504 | 832 |
| mirror_low | ibm_fez | 211 | 530 | any | 337 | 0.636 | 0.443 | 1.44 | 193 | 2491 |
| mirror_low | ibm_fez | 211 | 530 | cz | 279 | 0.526 | 0.215 | 2.45 | 251 | 1125 |
| mirror_low | ibm_fez | 211 | 530 | readout_error | 169 | 0.319 | 0.128 | 2.48 | 361 | 689 |
| mirror_low | ibm_kingston | 138 | 160 | T1 | 33 | 0.206 | 0.126 | 1.64 | 127 | 627 |
| mirror_low | ibm_kingston | 138 | 160 | T2 | 38 | 0.237 | 0.126 | 1.89 | 122 | 622 |
| mirror_low | ibm_kingston | 138 | 160 | any | 79 | 0.494 | 0.458 | 1.08 | 81 | 2322 |
| mirror_low | ibm_kingston | 138 | 160 | cz | 59 | 0.369 | 0.203 | 1.81 | 101 | 1000 |
| mirror_low | ibm_kingston | 138 | 160 | readout_error | 24 | 0.150 | 0.128 | 1.17 | 136 | 644 |
| mirror_low | ibm_marrakesh | 60 | 31 | T1 | 2 | 0.065 | 0.129 | 0.50 | 29 | 174 |
| mirror_low | ibm_marrakesh | 60 | 31 | T2 | 1 | 0.032 | 0.129 | 0.25 | 30 | 175 |
| mirror_low | ibm_marrakesh | 60 | 31 | any | 14 | 0.452 | 0.395 | 1.14 | 17 | 567 |
| mirror_low | ibm_marrakesh | 60 | 31 | cz | 14 | 0.452 | 0.232 | 1.95 | 17 | 291 |
| mirror_low | ibm_marrakesh | 60 | 31 | readout_error | 8 | 0.258 | 0.130 | 1.99 | 23 | 169 |
| r_low | ibm_fez | 12 | 14 | T1 | 0 | 0.000 | 0.171 | 0.00 | 14 | 12 |
| r_low | ibm_fez | 12 | 14 | T2 | 6 | 0.429 | 0.171 | 2.50 | 8 | 6 |
| r_low | ibm_fez | 12 | 14 | any | 7 | 0.500 | 0.443 | 1.13 | 7 | 23 |
| r_low | ibm_fez | 12 | 14 | cz | 7 | 0.500 | 0.343 | 1.46 | 7 | 17 |
| r_low | ibm_fez | 12 | 14 | readout_error | 6 | 0.429 | 0.171 | 2.50 | 8 | 6 |
| scan_listed | ibm_fez | 9 | 121 | T1 | 11 | 0.091 | 0.118 | 0.77 | 110 | 39 |
| scan_listed | ibm_fez | 9 | 121 | T2 | 17 | 0.140 | 0.118 | 1.19 | 104 | 33 |
| scan_listed | ibm_fez | 9 | 121 | any | 70 | 0.579 | 0.448 | 1.29 | 51 | 120 |
| scan_listed | ibm_fez | 9 | 121 | cz | 38 | 0.314 | 0.189 | 1.66 | 83 | 43 |
| scan_listed | ibm_fez | 9 | 121 | readout_error | 22 | 0.182 | 0.118 | 1.54 | 99 | 28 |
| scan_listed | ibm_kingston | 44 | 385 | T1 | 44 | 0.114 | 0.119 | 0.96 | 341 | 194 |
| scan_listed | ibm_kingston | 44 | 385 | T2 | 61 | 0.158 | 0.119 | 1.33 | 324 | 177 |
| scan_listed | ibm_kingston | 44 | 385 | any | 221 | 0.574 | 0.478 | 1.20 | 164 | 710 |
| scan_listed | ibm_kingston | 44 | 385 | cz | 128 | 0.332 | 0.196 | 1.70 | 257 | 270 |
| scan_listed | ibm_kingston | 44 | 385 | readout_error | 42 | 0.109 | 0.119 | 0.92 | 343 | 196 |
| scan_listed | ibm_marrakesh | 9 | 33 | T1 | 10 | 0.303 | 0.118 | 2.57 | 23 | 40 |
| scan_listed | ibm_marrakesh | 9 | 33 | T2 | 7 | 0.212 | 0.118 | 1.80 | 26 | 43 |
| scan_listed | ibm_marrakesh | 9 | 33 | any | 23 | 0.697 | 0.369 | 1.89 | 10 | 138 |
| scan_listed | ibm_marrakesh | 9 | 33 | cz | 15 | 0.455 | 0.192 | 2.36 | 18 | 68 |
| scan_listed | ibm_marrakesh | 9 | 33 | readout_error | 6 | 0.182 | 0.119 | 1.52 | 27 | 45 |
| sentinel_dead | ibm_fez | 32 | 426 | T1 | 31 | 0.073 | 0.125 | 0.58 | 395 | 129 |
| sentinel_dead | ibm_fez | 32 | 426 | T2 | 62 | 0.146 | 0.125 | 1.16 | 364 | 98 |
| sentinel_dead | ibm_fez | 32 | 426 | any | 236 | 0.554 | 0.436 | 1.27 | 190 | 322 |
| sentinel_dead | ibm_fez | 32 | 426 | cz | 122 | 0.286 | 0.218 | 1.31 | 304 | 157 |
| sentinel_dead | ibm_fez | 32 | 426 | readout_error | 107 | 0.251 | 0.125 | 2.01 | 319 | 53 |
| sentinel_dead | ibm_kingston | 14 | 0 | T1 | 0 |  | 0.125 |  | 0 | 70 |
| sentinel_dead | ibm_kingston | 14 | 0 | T2 | 0 |  | 0.125 |  | 0 | 70 |
| sentinel_dead | ibm_kingston | 14 | 0 | any | 0 |  | 0.495 |  | 0 | 277 |
| sentinel_dead | ibm_kingston | 14 | 0 | cz | 0 |  | 0.225 |  | 0 | 126 |
| sentinel_dead | ibm_kingston | 14 | 0 | readout_error | 0 |  | 0.138 |  | 0 | 77 |
| sentinel_dead | ibm_marrakesh | 63 | 368 | T1 | 35 | 0.095 | 0.125 | 0.76 | 333 | 280 |
| sentinel_dead | ibm_marrakesh | 63 | 368 | T2 | 33 | 0.090 | 0.125 | 0.72 | 335 | 282 |
| sentinel_dead | ibm_marrakesh | 63 | 368 | any | 194 | 0.527 | 0.465 | 1.13 | 174 | 977 |
| sentinel_dead | ibm_marrakesh | 63 | 368 | cz | 100 | 0.272 | 0.213 | 1.27 | 268 | 438 |
| sentinel_dead | ibm_marrakesh | 63 | 368 | readout_error | 54 | 0.147 | 0.125 | 1.17 | 314 | 261 |
| sentinel_weak | ibm_fez | 32 | 0 | T1 | 0 |  | 0.125 |  | 0 | 160 |
| sentinel_weak | ibm_fez | 32 | 0 | T2 | 0 |  | 0.125 |  | 0 | 160 |
| sentinel_weak | ibm_fez | 32 | 0 | any | 0 |  | 0.436 |  | 0 | 558 |
| sentinel_weak | ibm_fez | 32 | 0 | cz | 0 |  | 0.218 |  | 0 | 279 |
| sentinel_weak | ibm_fez | 32 | 0 | readout_error | 0 |  | 0.125 |  | 0 | 160 |
| sentinel_weak | ibm_kingston | 14 | 0 | T1 | 0 |  | 0.125 |  | 0 | 70 |
| sentinel_weak | ibm_kingston | 14 | 0 | T2 | 0 |  | 0.125 |  | 0 | 70 |
| sentinel_weak | ibm_kingston | 14 | 0 | any | 0 |  | 0.495 |  | 0 | 277 |
| sentinel_weak | ibm_kingston | 14 | 0 | cz | 0 |  | 0.225 |  | 0 | 126 |
| sentinel_weak | ibm_kingston | 14 | 0 | readout_error | 0 |  | 0.138 |  | 0 | 77 |
| sentinel_weak | ibm_marrakesh | 63 | 0 | T1 | 0 |  | 0.125 |  | 0 | 315 |
| sentinel_weak | ibm_marrakesh | 63 | 0 | T2 | 0 |  | 0.125 |  | 0 | 315 |
| sentinel_weak | ibm_marrakesh | 63 | 0 | any | 0 |  | 0.465 |  | 0 | 1171 |
| sentinel_weak | ibm_marrakesh | 63 | 0 | cz | 0 |  | 0.213 |  | 0 | 538 |
| sentinel_weak | ibm_marrakesh | 63 | 0 | readout_error | 0 |  | 0.125 |  | 0 | 315 |

(Recount against the tool's score.json: 65 rows, 0 differ.)

## 3. Our misses: which IBM column marks them (one column alone, or several)

| kind | readout_error | T1 | T2 | cz | several |
|---|---|---|---|---|---|
| mirror_low | 879 | 823 | 780 | 1489 | 1409 |
| r_low | 0 | 3 | 3 | 2 | 15 |
| scan_listed | 215 | 160 | 130 | 277 | 186 |
| sentinel_dead | 245 | 229 | 237 | 481 | 384 |
| sentinel_weak | 364 | 258 | 268 | 648 | 468 |

## 4. IBM misses: physical qubits found most often with no IBM mark on any column (top 5 per kind and device)

| kind | device | qubit: times |
|---|---|---|
| mirror_low | ibm_fez | 104: 68, 106: 33, 121: 20, 105: 14, 116: 12 |
| mirror_low | ibm_kingston | 45: 26, 44: 24, 47: 14, 42: 13, 84: 2 |
| mirror_low | ibm_marrakesh | 24: 7, 85: 2, 103: 2, 55: 2, 30: 1 |
| r_low | ibm_fez | 109: 3, 111: 3, 110: 1 |
| scan_listed | ibm_fez | 45: 4, 25: 4, 42: 4, 3: 2, 4: 2 |
| scan_listed | ibm_kingston | 4: 18, 3: 15, 27: 14, 49: 13, 50: 13 |
| scan_listed | ibm_marrakesh | 37: 2, 38: 1, 27: 1, 6: 1, 7: 1 |
| sentinel_dead | ibm_fez | 56: 32, 42: 31, 36: 24, 21: 21, 47: 19 |
| sentinel_dead | ibm_marrakesh | 36: 20, 41: 20, 22: 18, 65: 17, 63: 17 |

## 5. Age of the map (job time minus the snapshot's last_update_date, hours; one per job)

| device | jobs | median | min | max | over 24 h |
|---|---|---|---|---|---|
| ibm_fez | 35 | 0.56 | 0.19 | 89.85 | 4 |
| ibm_kingston | 34 | 0.41 | 0.12 | 69.46 | 2 |
| ibm_marrakesh | 67 | 0.63 | 0.09 | 93.01 | 17 |

## 6. Day to day: one snapshot per (device, day), that of the day's earliest job; per qubit of our sets, the largest over the smallest value across days (median over qubits), and how often a qubit in the device's worst eighth on one day is outside it on another

| device | days | column | median max/min | worst-eighth turnover |
|---|---|---|---|---|
| ibm_fez | 15 | readout_error | 3.30 | 0.203 |
| ibm_fez | 15 | T1 | 2.18 | 0.364 |
| ibm_fez | 15 | T2 | 1.97 | 0.107 |
| ibm_kingston | 13 | readout_error | 3.54 | 0.268 |
| ibm_kingston | 13 | T1 | 2.29 | 0.425 |
| ibm_kingston | 13 | T2 | 2.27 | 0.183 |
| ibm_marrakesh | 16 | readout_error | 7.81 | 0.357 |
| ibm_marrakesh | 16 | T1 | 2.36 | 0.333 |
| ibm_marrakesh | 16 | T2 | 3.55 | 0.330 |

## 7. Headline (median over all qubits / all cz edges of the device) against the median over our set, per job and kind; shown: the median over jobs of (our set / headline)

| kind | device | jobs | readout_error | T1 | T2 | cz |
|---|---|---|---|---|---|---|
| mirror_low | ibm_fez | 48 | 0.84 | 1.02 | 0.89 | 1.02 |
| mirror_low | ibm_kingston | 23 | 0.95 | 0.95 | 0.89 | 0.99 |
| mirror_low | ibm_marrakesh | 24 | 0.95 | 0.96 | 1.03 | 0.94 |
| r_low | ibm_fez | 4 | 0.74 | 0.91 | 0.71 | 0.98 |
| scan_listed | ibm_fez | 9 | 1.17 | 1.08 | 0.94 | 0.98 |
| scan_listed | ibm_kingston | 44 | 0.98 | 1.02 | 1.02 | 0.93 |
| scan_listed | ibm_marrakesh | 9 | 0.98 | 1.01 | 1.05 | 0.97 |
| sentinel_dead | ibm_fez | 32 | 1.56 | 1.09 | 0.89 | 0.93 |
| sentinel_dead | ibm_kingston | 14 | 0.87 | 1.11 | 0.86 | 1.00 |
| sentinel_dead | ibm_marrakesh | 63 | 0.93 | 0.97 | 0.94 | 0.99 |
| sentinel_weak | ibm_fez | 32 | 1.56 | 1.09 | 0.89 | 0.93 |
| sentinel_weak | ibm_kingston | 14 | 0.87 | 1.11 | 0.86 | 1.00 |
| sentinel_weak | ibm_marrakesh | 63 | 0.93 | 0.97 | 0.94 | 0.99 |

