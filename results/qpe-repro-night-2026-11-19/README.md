# Iterative phase estimation reproduced at n = 2, 3, 4, with the textbook circuit beside, 2026-11-19 on ibm_marrakesh (`prereg/qpe_repro_night_2026-11-19.md`)

- Declared in be3147c7. Built on the owner's machine (`versions.txt`) from the loop's device record of the night;
  pre-run checks PASS. 1950 shots per circuit.

| job | folder | id | n | circuits | s model | s charged | created - finished (CET) |
|---|---|---|---|---|---|---|---|
| A | `qA/` | dbvct6tarooc73flc3cg | 2, 3 | 76 | 45.8 | 42 | 11:25:31 - 11:27:18 |
| B | `qB/` | dbvct8v82tmc73dur6tg | 4 | 100 | 59.2 | 55 | 11:25:39 - 11:28:14 |

`python gpu/qpe_repro_night.py score qA qB` (`score.txt`; `qpe_scores.json` in both folders):

```
n 2: IPE 0.9553 (2 SE 0.0047, 7800 shots) against the ceiling 0.7500 -> BEYOND THE CEILING (margin +0.2053); off as read 0.7490
     textbook 0.9263 (2 SE 0.0059); IPE - textbook +0.0290 (2 SE 0.0075) -> IPE RIGHT MORE OFTEN; replicate arm 0.9287; sentinel CLEAN
n 3: IPE 0.9154 (2 SE 0.0045, 15600 shots) against the ceiling 0.5884 -> BEYOND THE CEILING (margin +0.3271); off as read 0.5021
     textbook 0.8452 (2 SE 0.0058); IPE - textbook +0.0703 (2 SE 0.0073) -> IPE RIGHT MORE OFTEN; replicate arm 0.8524; sentinel CLEAN
n 4: IPE 0.8799 (2 SE 0.0037, 31200 shots) against the ceiling 0.4706 -> BEYOND THE CEILING (margin +0.4093); off as read 0.3318
     textbook 0.7105 (2 SE 0.0051); IPE - textbook +0.1694 (2 SE 0.0063) -> IPE RIGHT MORE OFTEN; replicate arm 0.7184; sentinel DEAD
```

## Against the declaration

| prediction | numbers | |
|---|---|---|
| Q-1 BEYOND THE CEILING at each n = 2, 3, 4 | margins +0.205, +0.327, +0.409 | held |
| Q-2 per shot against the textbook circuit: no direction declared | IPE RIGHT MORE OFTEN at every n (+0.029, +0.070, +0.169) | read, not a prediction |

- Two yardsticks, kept apart (the declaration): the ceiling (no later correction of the uncontrolled circuit reaches
  it) and the per-shot comparison with the textbook circuit, whose own ceiling is 1 (noiseless it is always right; its
  shortfall is noise, which later correction can approach at a cost in shots). The second is not a ceiling claim.
- The ring sentinel of job B read DEAD (beside; it enters no verdict). Job A's read CLEAN.
- Against earlier nights (beside): 2026-11-17 fez n = 2 0.861, n = 3 0.772; marrakesh n = 4 0.903.

## Two numbers side by side

- Vanity: BEYOND THE CEILING at n = 2, 3, 4 with margins growing to +0.41.
- Essence: per shot, on the same device and night, the 2-qubit iterative circuit is right more often than the
  5-qubit textbook circuit, and the gap grows with n (+0.03, +0.07, +0.17): CZ 0-8 against 36-80 at n = 4.

## Reproduce

`python reproduce.py qpe-repro-night-2026-11-19`

## Independent check (home VS, 2026-11-19)

Re-counted from the raw counts with qiskit, aer and numpy only: BEYOND THE CEILING at n = 2, 3, 4 and the per-shot
differences +0.029 / +0.070 / +0.169 agree; reproduce SAME. Job B's ring sentinel read DEAD on physical qubits 70-74,
which do not overlap the test circuits' qubits 0-4; the qubits 0-2 that carried the iterative circuits lay outside the
sentinel's ring in both jobs (so the sentinel says nothing about them either way).
