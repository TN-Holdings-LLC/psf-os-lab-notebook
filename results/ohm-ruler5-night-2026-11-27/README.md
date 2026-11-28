# Ohm with rulers inside the circuit, the fifth night, 2026-11-27 on ibm_kingston (`prereg/ohm_ruler5_night_2026-11-27.md`)

- Declared in 75787d8c and pushed by the owner before the night's first fetch (the run's notebook clone, from GitHub,
  held 75787d8c; the run script checked it out). Rule 6 applied before the push
  (`notes/ohm_ruler5_2026-11-27/procedure_dry_home.txt`); the declared procedure ran in one try. Run on the owner's
  machine (`versions.txt`) with psf-os 0.3.3 as released (e652257), the sealed 9-pair answers of 11-25 (sha256
  e581df9d...); the answers by label of this job: `answers/ohm_ruler5_answers_by_label.json` (sha256 aeeef7ef...).
- Queue read 11:48:02 CET (`fetch_in/queue.json`): marrakesh 0 (not used), fez 1, kingston 0 -> **ibm_kingston** by the
  declared rule (the one of fez and kingston with fewer pending jobs; `pick.txt`), calibration 2026-11-27 11:31:58
  CET; the chain on copy drow 0. The first Ohm ruler night off ibm_fez: the cone's physical qubits are not those of
  11-24 to 11-26 (`qubits.csv`, column physical).
- Built as declared (`build.txt`, `or5/build.json`): the 11-25 job (7 pairs at t = 1, 3, 9 at t = 4; 9 |0> mirrors,
  18 string mirrors) and 6 readout circuits on the t = 4 cone, pubs 0 and 1 (head: s00, c00) and 171 to 174 (tail:
  s00, c00, s01, c01); 175 circuits; nothing parked.
- Pre-run check (`check.txt`): **ALL PASS** (declared check, string mirrors, readout).
- Scored by the declared tool on the owner's machine (`score.txt`, `or5/scores3.json`, `or5/scores5.json`,
  `or5/qubits.csv`, copied to `qubits.csv` as the declaration's procedure says); re-scored at home with the tool of
  75787d8c: the same text and the same three files. The sent
  circuits (`or5/job/circuits.qpy`, 12 MB) are kept unzipped (the sentinel's overlap is read from them); the other
  circuit files are gzipped (`*.qpy.gz`), as 11-26.

| job | folder | id | circuits | shots | s model | s charged | RU | created - finished (CET) |
|---|---|---|---|---|---|---|---|---|
| job | `or5/job/` | dc4m0jds2omc738fkhf0 | 175 | 1000 | 56.5 | **49** | **0.803** | 11:49:49 - 11:51:34 |

The project's usual formula (2.6 s + 0.000269 s x circuits x shots), used in the declaration, gives 49.7 s; the column
is psf-os's own model.

## Results

Raw M and W (ratio; READS at 0.5 or below):

| cell | raw M | raw W | W device / exact | W excess (2 SE) |
|---|---|---|---|---|
| A0 t = 1 | 0.002 READS | 0.002 READS | 0.262 / 0.250 | +0.012 (0.011) |
| A0 t = 3 | 0.033 READS | 0.033 READS | 0.565 / 0.435 | +0.130 (0.030) |
| A0 t = 4 | 0.037 READS | 0.037 READS | 0.673 / 0.526 | +0.147 (0.089) |
| A1 t = 1 | 0.003 READS | 0.001 READS | 0.257 / 0.250 | +0.007 (0.012) |
| A1 t = 3 | 0.068 READS | 0.067 READS | 0.531 / 0.368 | +0.162 (0.046) |
| A1 t = 4 | 0.087 READS | 0.085 READS | 0.606 / 0.388 | +0.218 (0.098) |
| A2 t = 1 | 0.002 READS | 0.002 READS | 0.262 / 0.250 | +0.012 (0.011) |
| A2 t = 3 | 0.109 READS | 0.118 READS | 0.448 / 0.279 | +0.169 (0.048) |
| A2 t = 4 | 0.193 READS | 0.191 READS | 0.537 / 0.312 | +0.224 (0.119) |

All 18 raw cells READ (11-26 on ibm_fez: A2 t = 4 did not, 0.529 / 0.526).

The judged rulers (d = the ruler's W minus the exact W; the t width in brackets; the 2 SE word is the same as the t
word in every cell):

| cell | (de) √(m_q e_q), window | (a') the total over the kept qubits | (de) against (d) | (e) readout alone (beside) |
|---|---|---|---|---|
| A0 t = 1 | +0.005 (0.010) AGREES | — | SMALLER | +0.007 (0.009) AGREES |
| A0 t = 3 | +0.023 (0.015) DIFFERS | 0.919; +0.022 (0.010) DIFFERS | SMALLER | +0.095 (0.026) DIFFERS |
| A0 t = 4 | −0.005 (0.033) AGREES | 0.902; −0.005 (0.018) AGREES | SMALLER | +0.109 (0.081) DIFFERS |
| A1 t = 1 | −0.001 (0.007) AGREES | — | NOT SMALLER | +0.002 (0.008) AGREES |
| A1 t = 3 | −0.004 (0.029) AGREES | 0.909; +0.034 (0.026) DIFFERS | SMALLER | +0.127 (0.046) DIFFERS |
| A1 t = 4 | −0.021 (0.048) AGREES | 0.880; +0.020 (0.038) AGREES | NOT SMALLER | +0.179 (0.091) DIFFERS |
| A2 t = 1 | +0.003 (0.010) AGREES | — | SMALLER | +0.007 (0.009) AGREES |
| A2 t = 3 | +0.003 (0.024) AGREES | 0.911; +0.037 (0.016) DIFFERS | SMALLER | +0.131 (0.045) DIFFERS |
| A2 t = 4 | −0.013 (0.031) AGREES | 0.881; +0.015 (0.031) AGREES | NOT SMALLER | +0.183 (0.111) DIFFERS |

- At t >= 3: (de) AGREES in five of six cells (DIFFERS at A0 t = 3, d +0.023 against the width 0.015), (a') in three
  (the three at t = 4), (e) in none (beside, as the dry runs foresaw). (de)'s |d| is smaller than (d)'s in four of six
  (NOT SMALLER at A1 t = 4 and A2 t = 4, where (d)'s d is 0.000 to three decimals).
- Table D (`or5/scores5.json`, cells): (de), EXPECTED TO AGREE at every t, reads "as the dry runs expect" in eight of
  nine cells and "against the dry runs: the device holds a fault that none of the dry runs' illustrative noises holds"
  at A0 t = 3. (a') at t = 3, EXPECTED TO DIFFER, DIFFERS in all three ("as the dry runs expect under gate noise or
  damping"); at t = 4, MIXED, AGREES in all three ("within what the dry runs allow").
- (a') leaves out no qubit in any cell at tau 0.3 (the smallest t = 4 |0> mirror value is 0.340, physical 34 in A1):
  (a') is ruler (a) tonight, and the direction with rho_a' is the direction with rho_a.
- The direction (judged with rho_a'; rho_a beside):

| cell | r − rho_a' (t width) | judged | with rho_a (beside) |
|---|---|---|---|
| A0 t = 3 | −0.013 (0.007) | WINDOW SHRINKS MORE | WINDOW SHRINKS MORE |
| A0 t = 4 | −0.006 (0.008) | NOT SEEN | NOT SEEN |
| A1 t = 3 | −0.026 (0.020) | WINDOW SHRINKS MORE | WINDOW SHRINKS MORE |
| A1 t = 4 | −0.007 (0.015) | NOT SEEN | NOT SEEN |
| A2 t = 3 | −0.025 (0.020) | WINDOW SHRINKS MORE | WINDOW SHRINKS MORE |
| A2 t = 4 | −0.011 (0.014) | NOT SEEN | NOT SEEN |

- Reading (the declared tables, `or5/scores5.json` tables): as the words above, ruler by ruler.

Beside, never judged:
- **The readout at the head and the tail** (`or5/scores5.json` readout_beside, 22 cone qubits): tail minus head lies
  within 2 SE on all 22 (largest −0.009, position 14; mean +0.0003). At the tail, s01 / c01 minus s00 / c00: largest
  −0.017 (position 17). e_q (mean of head and tail) lowest at positions 12 (0.933), 20 (0.953), 30 (0.956), physical
  12, 32, 22.
- The rulers of 11-25, scored again by score3 (`or5/scores3.json`), at t >= 3: (d) AGREES in five of six (all but
  A0 t = 3), (a) in three (t = 4), (b) and (b') in three (A0 t = 4, A1 t = 3, A2 t = 3), (c) in three (t = 4). At
  t = 3, d is positive for (a), (c), (d), (a') and (e) in every arm (+0.015 to +0.131); (de) is +0.023 / −0.004 /
  +0.003 and (b) +0.042 / −0.032 / +0.006 (A0 / A1 / A2). (On ibm_fez on 11-26 every ruler's d was positive at t = 3;
  on 11-24 ruler (a) and on 11-25 rulers (a) and (b) were negative in some arms there. Tonight's is another device, set
  beside. Corrected 2026-11-28 after the home VS's number check: the first text said 11-24 to 11-26.)
- tau 0.2 / 0.3 / 0.4: (a')'s words are the same at the three values in every cell; (b')'s are the same except at
  A1 t = 4 (DIFFERS at 0.2 and 0.3, AGREES at 0.4). The qubits left out: none at 0.2 and 0.3; position 18 at 0.4 in
  A1 t = 4 and A2 t = 4.
- qubits.csv (beside): MIRROR LOW on no row. R LOW on 9 rows (A1 t = 3: 23; A1 t = 4: 18, 19, 20, 21; A2 t = 3: 20;
  A2 t = 4: 18, 20, 23), R HIGH on 42; both tested at t >= 3 only, as 11-26. r / e at t >= 3: 0.848 to 0.996 over the
  111 rows with both; in the window, 0.872 (A1 t = 4, position 20, physical 32) to 0.954 (A1 t = 4, position 22,
  physical 30).
- One factor on the window (as 11-25): UNIFORM in A0 t = 3 and A0 t = 4 (p 0.74, 0.58), NOT UNIFORM in A1 t = 3
  (p 0.012), A1 t = 4 (p < 0.001), A2 t = 3 (p 0.003), A2 t = 4 (p 0.010). Pooled r: 0.906 / 0.881 / 0.895 at t = 3,
  0.898 / 0.872 / 0.874 at t = 4. Outlying positions: A1 t = 3 23; A1 t = 4 20, 21, 22; A2 t = 3 20; A2 t = 4 20, 23.
- smallest difference: the t widths in the judged ruler table; at t = 4, 0.03 to 0.05 for (de) and 0.02 to 0.04 for
  (a').
- order: A0 > A1 > A2 by every measure at t = 3 and t = 4. growth W(t) / W(1): raw 2.16 / 2.06 / 1.71 at t = 3 and
  2.57 / 2.35 / 2.05 at t = 4, against exact 1.74 / 1.47 / 1.11 and 2.11 / 1.55 / 1.25.
- sentinel: CLEAN; **ON USER QUBITS** (overlap 8 of the user circuits' 22 qubits: physical 21, 22, 23, 27, 28, 29, 36,
  41). On ibm_fez, 11-24 to 11-26, it was DEAD and NOT ON USER QUBITS. Placement is not wired to the sentinel (the
  decision of 11-06); this is a beside fact only.
- The raw W is above the exact value in every cell at t = 3 and 4, each beyond 2 SE (+0.130 to +0.224).

## Against the declaration

- **OR5-1 (the raw W READS at t = 3 in every arm): held** (0.033 / 0.067 / 0.118).
- **OR5-2 (on ibm_fez at copy drow 4, physical 101 to 104 below tau 0.3 on the t = 4 |0> mirror in every arm): NOT
  READ** (`or5/scores5.json` or5_2: another device or copy). The declared device rule chose ibm_kingston (fez had one
  pending job); the per-qubit record of 101 to 104 on fez is not tested tonight.
- Predictions over the nights of 11-16 to 11-27: 75 declared; 54 held, 20 failed, 1 not read.

## Two numbers side by side

- Vanity: OR5-1 held; all 18 raw cells READ; (de) AGREES in five of six cells at t >= 3, (d) in five of six.
- Essence: on ibm_kingston the raw W is 0.13 to 0.22 above the exact value at 3 and 4 cycles. Putting the readout's
  half back ((de)) brought the window to the exact value within the t width in five of six cells at t >= 3; at
  A0 t = 3 a shrink remains (+0.023, width 0.015), and the circuit's total (a') stays on the positive side at t = 3 in
  every arm (+0.022 to +0.037). OR5-2, the per-qubit prediction, did not get its device. 49 s charged.

## Limits

- One device-night, 7 or 9 pairs; t widths at t = 4 are 0.03 to 0.05 for (de).
- The first of these nights on ibm_kingston: its numbers are set beside the fez nights, not compared; a night on
  kingston alone does not say whether the fez nights' positive d at t = 3 belongs to fez.
- The head and tail readout pairs are under two minutes apart (created to finished, 1 min 45 s); a slower drift is not
  in them.
- The rulers' readings of the kind of shrink are readings of their directions; nothing here measures the noise.

## Independent check (home VS, 2026-11-27)

Re-counted from the raw counts, the sent circuits and the sealed answers with qiskit, Aer and numpy only (the home VS's
tool of 11-26, widened to the head and tail readout pairs, r / e and table D): every value and word of
`or5/scores3.json` and `or5/scores5.json` agrees (largest difference 7.1e-15 and 3.5e-18; no word differs), and all 126
rows of `or5/qubits.csv`; the sent circuits (175, the readout pubs at 0, 1 and 171 to 174), both sealed answers'
sha256, OR5-1 and OR5-2 agree; reproduce SAME for the three nights. Corrected here: `qubits.csv` was not copied to the
night's folder as the declared procedure says (only `or5/qubits.csv` was committed, and line 11 pointed at the missing
file); it is copied now, unchanged. Noted, not changed: position 12's e_q is 0.9325 (head 0.930, tail 0.935), written
0.933 here and 0.932 by the VS's rounding. Its tool and output: `notes/verify_2026-11-27/`.

## Reproduce

`python reproduce.py --psf-os <psf-os 0.3.3> ohm-ruler5-night-2026-11-27` (1 of 1 SAME at home; ohm-ruler3 and
ohm-ruler4 SAME again with the widened ignore set).
