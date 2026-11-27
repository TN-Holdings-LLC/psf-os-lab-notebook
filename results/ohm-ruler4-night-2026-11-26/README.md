# Ohm with rulers inside the circuit, the fourth night, 2026-11-26 on ibm_fez (`prereg/ohm_ruler4_night_2026-11-26.md`)

- Declared in 346934e9 and pushed by the owner before the night's first fetch (the run's notebook clone, from GitHub,
  held 346934e9; the run script checked it out). Rule 6 applied before the push
  (`notes/ohm_ruler4_2026-11-26/procedure_dry_home.txt`); the declared procedure ran in one try. Run on the owner's
  machine (`versions.txt`) with psf-os 0.3.3 as released (e652257), the sealed 9-pair answers of 11-25 (sha256
  e581df9d...).
- Queue read 11:29:35 CET (`fetch_in/queue.json`): marrakesh 0 (not used), fez 0, kingston 0 -> **ibm_fez**
  (`pick.txt`), calibration 2026-11-26 11:11:49 CET; the chain on copy drow 4, as 11-24 and 11-25.
- Built as declared (`build.txt`, `or4/build.json`): the 11-25 job (7 pairs at t = 1, 3, 9 at t = 4; 9 |0> mirrors,
  18 string mirrors) and 4 readout circuits on the t = 4 cone (s00, c00, s01, c01); 173 circuits; nothing parked.
- Pre-run check (`check.txt`): **ALL PASS** (declared check, string mirrors, readout).
- Scored by the declared tool on the owner's machine (`score.txt`, `or4/scores3.json`, `or4/scores4.json`,
  `qubits.csv`); re-scored at home with the tool of 346934e9: the same text and the same three files. The sent
  circuits (`or4/job/circuits.qpy`, 10 MB) are kept unzipped (the sentinel's overlap is read from them).

| job | folder | id | circuits | shots | s model | s charged | RU | created - finished (CET) |
|---|---|---|---|---|---|---|---|---|
| job | `or4/job/` | dc40l0ls2omc738edlcg | 173 | 1000 | 55.9 | **48** | **0.785** | 11:31:30 - 11:32:28 |

The project's usual formula (2.6 s + 0.000269 s x circuits x shots), used in the declaration, gives 49.1 s; the column
is psf-os's own model.

## Results

Raw M and W (ratio; READS at 0.5 or below):

| cell | raw M | raw W | W device / exact | W excess (2 SE) |
|---|---|---|---|---|
| A0 t = 1 | 0.014 READS | 0.008 READS | 0.258 / 0.250 | +0.008 (0.032) |
| A0 t = 3 | 0.074 READS | 0.071 READS | 0.616 / 0.435 | +0.180 (0.068) |
| A0 t = 4 | 0.120 READS | 0.118 READS | 0.771 / 0.526 | +0.244 (0.175) |
| A1 t = 1 | 0.015 READS | 0.010 READS | 0.273 / 0.250 | +0.023 (0.031) |
| A1 t = 3 | 0.167 READS | 0.158 READS | 0.615 / 0.368 | +0.247 (0.076) |
| A1 t = 4 | 0.260 READS | 0.250 READS | 0.753 / 0.388 | +0.365 (0.175) |
| A2 t = 1 | 0.013 READS | 0.008 READS | 0.266 / 0.250 | +0.016 (0.029) |
| A2 t = 3 | 0.297 READS | 0.313 READS | 0.547 / 0.279 | +0.268 (0.094) |
| A2 t = 4 | 0.529 DOES NOT READ | 0.526 DOES NOT READ | 0.684 / 0.312 | +0.372 (0.197) |

A2 t = 4 is the first cell of the four Ohm ruler nights whose raw M and W do not read (11-24: 0.475 / 0.478; 11-25:
0.401 / 0.403); OR4-1 asks only t = 3.

The judged rulers (d = the ruler's W minus the exact W; the t width in brackets; the 2 SE word in square brackets where
it differs):

| cell | (de) √(m_q e_q), window | (a') the total over the kept qubits | (de) against (d) | (e) readout alone (beside) |
|---|---|---|---|---|
| A0 t = 1 | −0.005 (0.026) AGREES | — | NOT SMALLER | +0.000 (0.031) AGREES |
| A0 t = 3 | +0.022 (0.042) AGREES | 0.888; +0.021 (0.027) AGREES | SMALLER | +0.143 (0.072) DIFFERS |
| A0 t = 4 | +0.011 (0.096) AGREES | 0.841; +0.009 (0.055) AGREES | SMALLER | +0.204 (0.180) DIFFERS |
| A1 t = 1 | +0.010 (0.018) AGREES | — | SMALLER | +0.017 (0.028) AGREES |
| A1 t = 3 | +0.038 (0.038) DIFFERS | 0.861; +0.043 (0.036) DIFFERS | SMALLER | +0.210 (0.082) DIFFERS |
| A1 t = 4 | +0.031 (0.092) AGREES | 0.807; +0.080 (0.064) DIFFERS | SMALLER | +0.325 (0.180) DIFFERS |
| A2 t = 1 | +0.004 (0.020) AGREES | — | SMALLER | +0.009 (0.026) AGREES |
| A2 t = 3 | +0.048 (0.045) DIFFERS | 0.868; +0.061 (0.019) DIFFERS | SMALLER | +0.228 (0.101) DIFFERS |
| A2 t = 4 | +0.016 (0.052) AGREES | 0.806; +0.051 (0.048) DIFFERS | SMALLER | +0.329 (0.201) DIFFERS |

- At t >= 3: (de) AGREES in four of six cells (DIFFERS at A1 t = 3, d 0.0383 against the width 0.0382, and at A2
  t = 3), (a') in two (A0 t = 3, A0 t = 4). (de)'s |d| is smaller than (d)'s in all six. (e) DIFFERS in all six, as
  the dry runs foresaw.
- (a') leaves out positions 28 to 31 (physical 104, 103, 102, 101) at t = 4 in every arm, and nothing at t = 3.
- The direction (judged with rho_a'; rho_a beside):

| cell | r − rho_a' (t width) | judged | with rho_a (beside) |
|---|---|---|---|
| A0 t = 3 | −0.042 (0.034) | WINDOW SHRINKS MORE | WINDOW SHRINKS MORE |
| A0 t = 4 | −0.038 (0.032) | WINDOW SHRINKS MORE | NOT SEEN (+0.036) |
| A1 t = 3 | −0.043 (0.034) | WINDOW SHRINKS MORE | WINDOW SHRINKS MORE |
| A1 t = 4 | −0.042 (0.051) | NOT SEEN | WINDOW SHRINKS LESS (+0.039) |
| A2 t = 3 | −0.051 (0.031) | WINDOW SHRINKS MORE | WINDOW SHRINKS MORE |
| A2 t = 4 | −0.028 (0.039) | NOT SEEN | WINDOW SHRINKS LESS (+0.055) |

- Reading (the declared tables, `or4/scores4.json` tables): as the words above, ruler by ruler.

Beside, never judged:
- The rulers of 11-25, scored again by score3 (`or4/scores3.json`), at t >= 3: (d) AGREES in four of six (A0 t = 3,
  A0 t = 4, A1 t = 4, A2 t = 4), (c) in one (A0 t = 4), (b) in one (A0 t = 3), (b') in four, (a) in one (A0 t = 3).
  d is positive at t = 3 for every ruler and arm (+0.021 to +0.110).
- tau 0.2 / 0.3 / 0.4: (a')'s and (b')'s words are the same at the three values in every cell; the qubits left out at
  t = 4 are 28 to 31 at 0.3 and 0.4, and three or two of them at 0.2 (A0: 28, 30, 31; A2: 28, 30).
- Readout (`or4/scores4.json` readout_pairs): e_q of the 22 cone qubits from s00/c00 and from s01/c01 differ by
  0.027 at the largest (physical 102: 0.847 and 0.820). (Corrected after the home VS's check: the first text gave the
  largest signed difference, 0.020.) The three lowest e_q: physical 93 (0.786), 113 (0.797), 102 (0.847).
- qubits.csv (beside): MIRROR LOW on 104, 103, 102, 101 at t = 4 in every arm; R LOW and R HIGH are two further
  columns (R HIGH added by the owner's choice of 2026-11-26). At t = 4, 104's mirror is low in every arm, while its
  r_q is high in A0 (0.846, R HIGH) and low in A1 and A2 (0.757, 0.669, R LOW): two facts in two columns, which go
  their own ways by arm. R LOW and R HIGH are written at t >= 3 only: the tool tests r_q against the window's pooled
  r, which score3 gives at t >= 3 (at t = 1 the window is one position), so every t = 1 row reads False in both; the
  declaration's text names no such limit (the home VS's check counts 7 flags at t = 1 with its own reading).
- One factor on the window (as 11-25): NOT UNIFORM in all six cells at t >= 3 (p ≤ 0.002; at A2 t = 3 p 0.0015,
  where 11-24 and 11-25 read UNIFORM). Pooled r: 0.854 / 0.822 / 0.818 at t = 3, 0.810 / 0.777 / 0.791 at t = 4.
  Outlying positions: A0 t = 3 21, 22, 24; A0 t = 4 20, 22, 24, 25, 26; A1 t = 3 23, 24; A1 t = 4 22, 24, 25, 26;
  A2 t = 3 23, 24; A2 t = 4 20, 23, 24, 26. (Added after the home VS's check: the declaration names them beside, as
  11-25, and the first text left them out.)
- smallest difference: the t widths in the judged ruler table; at t = 4, 0.05 to 0.10 for (de) and 0.05 to 0.06 for
  (a'). (Added 2026-11-27 after the workplace VS's new beside check.)
- second readout pair (s01 / c01): see readout above (its largest difference from s00 / c00, 0.027).
- order: A0 > A1 > A2 by every measure at t = 3 and t = 4. growth W(t) / W(1): raw 2.39 / 2.25 / 2.05 at t = 3 and
  2.99 / 2.76 / 2.57 at t = 4, against exact 1.74 / 1.47 / 1.11 and 2.11 / 1.55 / 1.25.
- sentinel: DEAD; NOT ON USER QUBITS (overlap 0), as 11-24 and 11-25.
- The raw W is above the exact value in every cell at t = 3 and 4, each beyond 2 SE (+0.180 to +0.372).

## Against the declaration

- **OR4-1 (the raw W READS at t = 3 in every arm): held** (0.071 / 0.158 / 0.313).
- **OR4-2 (on ibm_fez at copy drow 4, physical 104 and 102 below tau 0.3 on the t = 4 |0> mirror in every arm):
  held** (104: 0.050 / −0.102 / −0.118; 102: 0.166 / 0.120 / −0.010).
- Predictions over the nights of 11-16 to 11-26: 73 declared; 53 held, 20 failed.

## Two numbers side by side

- Vanity: OR4-1 and OR4-2 held; 17 of 18 raw cells READS; (de) AGREES in four of six cells at t >= 3, and its |d| is
  smaller than (d)'s in all six.
- Essence: the raw W is 0.18 to 0.37 above the exact value at 3 and 4 cycles, and A2 t = 4 no longer reads by the
  ratio rule. Putting the readout's half back ((de)) brought the window to the exact value within the t width in four
  of six cells, but at t = 3 every ruler stays on the positive side (+0.02 to +0.11 for (de), (a') and the rulers of 11-25;
  +0.14 to +0.23 for (e), beside), so a shrink no ruler here
  carries remains at t = 3 in A1 and A2. (a') read two of six cells. 48 s charged.

## Limits

- One device-day, 7 or 9 pairs; t widths at t = 4 are 0.05 to 0.10 for (de).
- The rulers' readings of the kind of shrink are readings of their directions; nothing here measures the noise. Values
  on other nights are set beside, not compared.
- OR4-2 rests on two earlier nights and the same placement; it says nothing about another device or copy.

## Independent check (home VS, 2026-11-26)

Re-counted from the raw counts, the sent circuits and the sealed answers with qiskit, Aer and numpy only (the home VS's
tool of 11-25, widened): every value and word of `or4/scores3.json` and `or4/scores4.json` agrees (largest difference
1.1e-16; no word differs); the sent circuits, the sealed answers (e581df9d...), OR4-1 and OR4-2 agree; reproduce SAME.
Corrected here: the readout pairs' largest difference; the uniformity words and outlying positions added; 104's R
columns by arm; the essence's range. Noted, not changed: qubits.csv's R LOW and R HIGH are written at t >= 3 only
(above); `tools/declaration_check.py beside` read no item from this declaration, whose heading has no colon. Its tool
and output: `notes/verify_2026-11-26/`.

## Reproduce

`python reproduce.py --psf-os <psf-os 0.3.3> ohm-ruler4-night-2026-11-26` (1 of 1 SAME at home).
