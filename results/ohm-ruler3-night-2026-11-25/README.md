# Ohm with rulers inside the circuit, the third night, 2026-11-25 on ibm_fez (`prereg/ohm_ruler3_night_2026-11-25.md`)

- Declared in ec67e8a6 and pushed by the owner before the night's first fetch (the run's notebook clone, from GitHub,
  held ec67e8a6; the run script checked it out). Rule 6 had been applied before the push
  (`notes/ohm_ruler3_2026-11-25/procedure_dry_home.txt`); the night ran the declared procedure as written, in one try.
  Run on the owner's machine (`versions.txt`: Python 3.12.13, qiskit 2.5.2, aer 0.17.2, runtime 0.49.0, numpy 2.5.3)
  with psf-os 0.3.3 as released (e652257), the sealed 9-pair answers' sha256 checked (e581df9d...).
- Queue read 11:33:50 CET (`fetch_in/queue.json`): marrakesh 4 (not used), fez 0, kingston 0 -> **ibm_fez**
  (`pick.txt`; the tie goes to fez as the rule reads), calibration 2026-11-25 11:07:06 CET. The chain on copy drow 4
  (copies 0 and 2 passed over: qubits 32, 33 suspect and coupler (32, 33), qubit 72 failed), as 11-24.
- Built as declared (`build.txt`, `or3/build.json`): plan B, the light-cone circuits alone, 7 pairs at t = 1 and 3,
  9 at t = 4, a |0> mirror per cell (9) and the two string mirrors per cell (s00, c00: 18); 169 circuits; nothing
  parked.
- Pre-run check (`check.txt`): **ALL PASS** (declared check worst 9.9e-11; string mirrors worst 3.8e-14).
- Scored by the declared tool on the owner's machine (`score.txt`, `or3/scores3.json`); re-scored at home with the
  tool of ec67e8a6: the same text and the same JSON. The sent circuits (`or3/job/circuits.qpy`, 10 MB) are kept
  unzipped, because the sentinel's overlap is read from them; the other `*.qpy` are gzipped.

| job | folder | id | circuits | shots | s model | s charged | RU | created - finished (CET) |
|---|---|---|---|---|---|---|---|---|
| job | `or3/job/` | dc3bju5hdvas73bni4og | 169 | 1000 | 54.7 | **47** | **0.768** | 11:35:36 - 11:37:55 |

The project's usual formula (2.6 s + 0.000269 s x circuits x shots), used in the declaration, gives 48.1 s; the column
is psf-os's own model.

## Results

Raw M and W (ratio = mean squared error ÷ mean square of the exact value; READS at 0.5 or below):

| cell | pairs | raw M | raw W | W device / exact | W excess (2 SE) |
|---|---|---|---|---|---|
| A0 t = 1 | 7 | 0.010 READS | 0.010 READS | 0.246 / 0.250 | −0.004 (0.035) |
| A0 t = 3 | 7 | 0.060 READS | 0.059 READS | 0.588 / 0.435 | +0.153 (0.080) |
| A0 t = 4 | 9 | 0.102 READS | 0.102 READS | 0.746 / 0.526 | +0.219 (0.167) |
| A1 t = 1 | 7 | 0.008 READS | 0.007 READS | 0.260 / 0.250 | +0.010 (0.029) |
| A1 t = 3 | 7 | 0.111 READS | 0.109 READS | 0.570 / 0.368 | +0.202 (0.071) |
| A1 t = 4 | 9 | 0.217 READS | 0.214 READS | 0.724 / 0.388 | +0.336 (0.164) |
| A2 t = 1 | 7 | 0.007 READS | 0.007 READS | 0.260 / 0.250 | +0.010 (0.029) |
| A2 t = 3 | 7 | 0.225 READS | 0.243 READS | 0.515 / 0.279 | +0.236 (0.083) |
| A2 t = 4 | 9 | 0.401 READS | 0.403 READS | 0.649 / 0.312 | +0.337 (0.161) |

The rulers (rho; d = the ruler's W minus the exact W, with the t width (t quantile x SE, rule 4) in brackets; the word
at the t width as declared, the 2 SE word in square brackets where it differs):

| cell | (a) the circuit's total | (b) √(\|0> mirror), circuit | (c) √(\|0> mirror), window | (d) √(string mirrors' odd part), window |
|---|---|---|---|---|
| A0 t = 1 | — | 0.910; −0.015 (0.034) AGREES | 0.959; −0.009 (0.039) AGREES | 0.948; −0.010 (0.038) AGREES |
| A0 t = 3 | −0.003 (0.038) AGREES | 0.890; +0.005 (0.062) AGREES | 0.902; +0.023 (0.068) AGREES | 0.900; +0.021 (0.066) AGREES |
| A0 t = 4 | −0.212 (0.096) DIFFERS | 0.781; −0.148 (0.092) DIFFERS | 0.868; +0.019 (0.103) AGREES | 0.874; +0.030 (0.106) AGREES |
| A1 t = 1 | — | 0.891; −0.002 (0.022) AGREES | 0.937; +0.003 (0.027) AGREES | 0.939; +0.003 (0.028) AGREES |
| A1 t = 3 | +0.024 (0.037) AGREES | 0.849; −0.015 (0.051) AGREES | 0.885; +0.043 (0.057) AGREES | 0.874; +0.027 (0.052) AGREES |
| A1 t = 4 | −0.189 (0.114) DIFFERS | 0.715; −0.195 (0.165) DIFFERS | 0.842; +0.085 (0.087) AGREES [DIFFERS] | 0.821; +0.045 (0.082) AGREES |
| A2 t = 1 | — | 0.885; −0.003 (0.021) AGREES | 0.925; +0.002 (0.026) AGREES | 0.925; +0.002 (0.026) AGREES |
| A2 t = 3 | +0.038 (0.026) DIFFERS | 0.867; +0.040 (0.047) AGREES [DIFFERS] | 0.888; +0.076 (0.056) DIFFERS | 0.872; +0.049 (0.049) DIFFERS |
| A2 t = 4 | −0.199 (0.139) DIFFERS | 0.711; −0.234 (0.205) DIFFERS | 0.827; +0.044 (0.058) AGREES | 0.831; +0.051 (0.052) AGREES [DIFFERS] |

- Ruler (a) has no word at t = 1, as 11-24 (the window is the whole light cone there). Ruler (d) at A2 t = 3: d and
  the t width are 0.0489 and 0.0486.
- At t >= 3: (d) AGREES in five of six cells, (c) in five, (b) in three (all at t = 3), (a) in two (A0 t = 3, A1
  t = 3).
- The direction (r − rho_a, t width; table B):

| cell | r − rho_a (t width) | direction | ruler (a) | table B |
|---|---|---|---|---|
| A0 t = 3 | −0.024 (0.029) | NOT SEEN | AGREES | the window and the total shrink alike |
| A0 t = 4 | +0.059 (0.043) | WINDOW SHRINKS LESS | DIFFERS | the total overstates the window's shrink |
| A1 t = 3 | −0.038 (0.036) | WINDOW SHRINKS MORE | AGREES | the window loses more than the total, within what ruler (a)'s word can see |
| A1 t = 4 | +0.053 (0.031) | WINDOW SHRINKS LESS | DIFFERS | the total overstates the window's shrink |
| A2 t = 3 | −0.048 (0.056) | NOT SEEN | DIFFERS | no lean is seen, yet the total does not carry the window's shrink: read with the one-factor word |
| A2 t = 4 | +0.069 (0.029) | WINDOW SHRINKS LESS | DIFFERS | the total overstates the window's shrink |

- One factor on the window: NOT UNIFORM in five of six cells (p ≤ 0.003); UNIFORM at A2 t = 3 (p 0.197), as 11-24.
  Pooled r: 0.874 / 0.849 / 0.839 at t = 3, 0.826 / 0.788 / 0.811 at t = 4.
- Reading (the declared tables): table A as the words above, ruler by ruler; table B as the last column.

Beside, never judged (`or3/scores3.json`, beside):
- order: A0 > A1 > A2 by W, W_a, W_b, W_b', W_c, W_d and the exact W, at t = 3 and at t = 4 (11-24: the raw W at t = 3
  did not keep it).
- growth W(t) / W(1): raw 2.39 / 2.19 / 1.98 at t = 3 and 3.03 / 2.79 / 2.50 at t = 4, against exact 1.74 / 1.47 /
  1.11 and 2.11 / 1.55 / 1.25.
- smallest difference: the t widths are in the ruler table (at t = 4, 0.05 to 0.21).
- candidate 1, ruler (b'): AGREES in all six cells at t >= 3. At t = 3 it leaves nothing out and equals (b); at t = 4
  it leaves out positions 28 to 31 in every arm (physical qubits 104, 103, 102, 101; the copy at drow 4 is the labels
  + 80) and keeps 18 of 22: rho 0.845 / 0.775 / 0.775 against (b)'s 0.781 / 0.715 / 0.711, d −0.021 (0.091) /
  −0.051 (0.101) / −0.072 (0.105).
- outlying positions (beyond 2 shot-noise SE of the pooled r): A0 t = 3 positions 21 to 24; A0 t = 4 23 to 26; A1
  t = 3 21, 24; A1 t = 4 21, 22, 24, 25, 26; A2 t = 4 23 to 26; none at A2 t = 3.
- sentinel: DEAD; NOT ON USER QUBITS (its ring, 40 qubits, shares none of the user's 22), so it says nothing about the
  user's qubits tonight, as 11-24.
- The raw W is above the exact value in every cell at t = 3 and 4, each beyond 2 SE (+0.153 to +0.337). READS does not
  say there is no bias.
- The qubits (b') leaves out at t = 4 sit where the 11-24 record (same device, same copy) showed its low values: there
  the same-layer mirror's <Z> at t = 4 was near 0 on 104 and 102 in every arm (−0.044 to 0.080) and on 101 in A0
  (0.022; 0.24 and 0.30 in A1, A2), while on 103 it was 0.45 to 0.51 and 103 showed a low r instead (0.42); tonight
  103's mirror is 0.16 to 0.18 and all four fall below tau 0.3. Set beside, not compared. (Corrected after the home
  VS's check: the first text said all four had shown mirrors near 0.)

## Against the declaration

- **OR3-1 (the raw W READS at t = 3 in every arm): held** (0.059 / 0.109 / 0.243).
- Predictions over the nights of 11-16 to 11-25: 71 declared; 51 held, 20 failed.

## Two numbers side by side

- Vanity: 18 of 18 raw cells READS; OR3-1 held; ruler (d) AGREES in five of six cells at t >= 3; the order kept by
  every measure at t = 3 and 4.
- Essence: the raw W is still 0.15 to 0.34 above the exact value at 3 and 4 cycles; dividing by the string mirrors'
  odd part over the window (ruler d) brought it to the exact value within the t width in five of six cells, but at
  t = 4 that width is 0.05 to 0.11, so an AGREES there leaves room of that size; the circuit's own total (ruler a)
  did so in the two t = 3 cells of A0 and A1. 47 s charged.

## Limits

- One device-day, 7 or 9 pairs. Rule 4's t width halves the false words of 2 SE in the dry runs (4 of 96 without
  noise); three judged words change between the two widths
  tonight (A1 t = 4 (c), A2 t = 3 (b), A2 t = 4 (d)).
- The rulers' readings of the kind of shrink are readings of their directions, from the dry runs with illustrative
  noise; nothing here measures the noise. Values on other nights are set beside, not compared.
- (b') and the outlying positions are beside; they were not judged.

## Independent check (home VS, 2026-11-25)

Re-counted from `or3/job/raw_counts.json`, the sent circuits and the sealed answers with qiskit, Aer and numpy only
(the home VS's own tool of 11-24, widened; not psf-os, not the notebook's scorers): the raw words; rulers (a), (b),
(c), (d) and (b') with rho, d, the t width, 2 SE and the words; the direction; the one-factor p and the outlying
positions; the rows of tables A and B; the order and the growth agree with this record (largest difference 5.7e-14;
no word differs). Sent as declared: 169 circuits; 7, 7, 9 pairs (the rule drew 31 strings for 9 pairs, the first 7
those of 11-24); the 9 |0> mirrors and 18 string mirrors return to their ideal values without noise; CZ counts; no
parking; fez picked by the rule (level with kingston, the queue's order); the sentinel's overlap 0. The sealed
answers' sha256 is the declared e581df9d...; the answers by label differ from it by 0. (b')'s left-out positions
28 to 31 are physical 104, 103, 102, 101, each with a mirror below 0.3 tonight. Reproduce SAME. Corrected here: the
sentence on the 11-24 mirrors (beside). Its tool and output: `notes/verify_2026-11-25/`.

## Reproduce

`python reproduce.py --psf-os <psf-os 0.3.3> ohm-ruler3-night-2026-11-25` (1 of 1 SAME at home).
