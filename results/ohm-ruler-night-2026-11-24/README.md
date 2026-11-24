# Ohm with rulers inside the circuit, 2026-11-24 on ibm_fez (`prereg/ohm_ruler_night_2026-11-24.md`)

- Declared in c4518f53 and pushed by the owner before the night's first fetch (the run's notebook clone, from GitHub,
  held c4518f53; the run script checked it out). Run on the owner's machine (`versions.txt`: Python 3.12.13, qiskit
  2.5.2, aer 0.17.2, runtime 0.49.0, numpy 2.5.3) with psf-os 0.3.3 as released (e652257), the sealed answers' sha256
  checked (59cbd7a0...).
- **Try 1 (12:15 CET), nothing sent** (`try1_argerror/`): the run script passed `--pairs 7 --ts 1 3 4 --forms L` to
  `build`, as the declaration's procedure line wrongly wrote; `build` takes no plan flags (the plan is fixed by the
  sealed answers) and stopped on the arguments, on both devices. Home's error in the declaration and the script; as
  with the paired loop of 11-20, the night ran without the flags, with the plan the declaration names. Home's try-build
  had been run without them (139 circuits).
- Queue read 12:16:54 CET (`fetch_in/queue.json`): marrakesh 0 (not used), fez 0, kingston 1 -> **ibm_fez**
  (`pick.txt`), calibration 2026-11-24 11:39:13 CET.
- Built as declared (`build.txt`, `or/build.json`): plan B, the light-cone circuits alone, 7 pairs, t = 1, 3, 4, a
  mirror per cell (9); 139 circuits; CZ at t = 3: 66 / 99 / 99, at t = 4: 120 / 180 / 180 (A0 / A1 / A2); nothing
  parked.
- Pre-run check (`check.txt`): **ALL PASS** (worst 9.9e-11; the circuits' total against T0 within 2.4e-13; mirrors
  within 3.8e-14).
- Scored by the declared tool on the owner's machine (`score.txt`, `or/scores.json`); re-scored at home with the tool of
  c4518f53: the same text. `*.qpy` gzipped.

| job | folder | id | circuits | shots | s model | s charged | RU | created - finished (CET) |
|---|---|---|---|---|---|---|---|---|
| job | `or/job/` | dc2n50ts2omc738c8od0 | 139 | 1000 | 45.5 | **39** | **0.636** | 12:18:27 - 12:19:16 |

The project's usual formula (2.6 s + 0.000269 s x circuits x shots), used in the declaration, gives 40.0 s; the column
is psf-os's own model.

## Results

Raw M and W (ratio = mean squared error ÷ mean square of the exact value; READS at 0.5 or below):

| cell | raw M | raw W | W device / exact | W excess (2 SE) |
|---|---|---|---|---|
| A0 t = 1 | 0.007 READS | 0.006 READS | 0.255 / 0.250 | +0.005 (0.027) |
| A0 t = 3 | 0.051 READS | 0.050 READS | 0.577 / 0.435 | +0.142 (0.072) |
| A0 t = 4 | 0.123 READS | 0.123 READS | 1.240 / 0.876 | +0.363 (0.078) |
| A1 t = 1 | 0.007 READS | 0.006 READS | 0.258 / 0.250 | +0.008 (0.028) |
| A1 t = 3 | 0.123 READS | 0.119 READS | 0.586 / 0.368 | +0.218 (0.059) |
| A1 t = 4 | 0.289 READS | 0.286 READS | 1.190 / 0.723 | +0.467 (0.082) |
| A2 t = 1 | 0.006 READS | 0.006 READS | 0.255 / 0.250 | +0.005 (0.026) |
| A2 t = 3 | 0.243 READS | 0.261 READS | 0.526 / 0.279 | +0.247 (0.081) |
| A2 t = 4 | 0.475 READS | 0.478 READS | 0.974 / 0.524 | +0.450 (0.080) |

The rulers (d = the ruler's W minus the exact W; words at 2 SE as declared):

| cell | ruler (a), the circuit's total | ruler (b), √(mirror) | table 2 |
|---|---|---|---|
| A0 t = 1 | NOT READ | 0.911; −0.005 (0.019) AGREES | — |
| A0 t = 3 | −0.116 (0.025) DIFFERS | 0.901; +0.009 (0.045) AGREES | the mirror reads it; the total does not |
| A0 t = 4 | −0.250 (0.100) DIFFERS | 0.777; −0.080 (0.100) AGREES | the mirror reads it; the total does not |
| A1 t = 1 | NOT READ | 0.909; −0.002 (0.020) AGREES | — |
| A1 t = 3 | −0.083 (0.028) DIFFERS | 0.869; +0.037 (0.022) DIFFERS | neither ruler reads it |
| A1 t = 4 | −0.293 (0.134) DIFFERS | 0.737; −0.102 (0.111) AGREES | the mirror reads it; the total does not |
| A2 t = 1 | NOT READ | 0.919; −0.004 (0.016) AGREES | — |
| A2 t = 3 | −0.067 (0.037) DIFFERS | 0.861; +0.043 (0.039) DIFFERS | neither ruler reads it |
| A2 t = 4 | −0.401 (0.174) DIFFERS | 0.738; −0.195 (0.091) DIFFERS | neither ruler reads it |

- One factor on the window: NOT UNIFORM in five of six cells (χ² p ≤ 0.008); UNIFORM at A2 t = 3 (p 0.309). The
  pooled factor r: 0.874 / 0.840 / 0.833 at t = 3, 0.800 / 0.761 / 0.796 at t = 4.
- Order (A0 > A1 > A2): raw W at t = 3 no (A1 0.586 above A0 0.577); W by ruler (a) and by ruler (b) at t = 3 yes; all
  three at t = 4 yes.
- Reading (the declared tables): table 1, "neither one factor nor the total's" in five cells and "one factor on the
  window, but the circuit's total carries another" at A2 t = 3; table 2, "the mirror's square root reads it; the
  circuit's total does not" at A0 t = 3, A0 t = 4 and A1 t = 4, and "neither ruler reads it" at A1 t = 3, A2 t = 3 and
  A2 t = 4.

Beside, never judged:
- The raw W is above the exact value in every cell at t = 3 and 4, each beyond 2 SE (+0.142 to +0.467); W(t) / W(1)
  raw 2.26 / 2.27 / 2.06 at t = 3 against exact 1.74 / 1.47 / 1.11. The raw W READS by the ratio rule even so; READS
  does not say there is no bias.
- Ruler (a) is below the exact value in every cell where it was read. The dry runs foresaw DIFFERS, but with the
  opposite sign: there the window's factor r was below the circuit total's rho_a (r - rho_a -0.024 to -0.084, gate noise
  and damping alike), which puts d_a above zero. On the record r is above rho_a (the mean of the 7 pairs) in all six
  cells: +0.048 / +0.040 / +0.032 at t = 3, +0.091 / +0.089 / +0.119 at t = 4 (2 SE of rho_a 0.014 to 0.044), so the
  window shrinks less than the circuit's total, and d_a falls below zero. Table 2's third row names the dry runs' gate
  noise as its reading; tonight's r and rho_a run the other way (the declaration calls that text a reading, not a
  measurement of the noise). Corrected after the home VS's check.
- The sentinel (declared beside): DEAD (`or/scores.json`, beside.sentinel; signal below 0.12 at ring positions 24 to
  34, physical qubits 47, 57, 67, 66, 65, 64, 63, 56, 43, 42, 41). Its ring (40 qubits, 3 to 67) shares no qubit with
  tonight's user circuits (22 qubits, 92 to 121: the copy moved to drow 4 after passing over copies 0 and 2), so it
  says nothing about the user's qubits tonight. On 11-23, 15 of the ring's qubits were the user's. Added after the home
  VS's check.

## Against the declaration

- **OR-1 (the raw W READS at t = 3 in every arm): held** (0.050 / 0.119 / 0.261).
- Predictions over the nights of 11-16 to 11-24: 70 declared; 50 held, 20 failed.

## Two numbers side by side

- Vanity: 18 of 18 raw cells READS; OR-1 held; the order at t = 4 by every measure.
- Essence: the raw W reads by the loose ratio rule, but it is 0.14 to 0.47 above the exact value at 3 and 4 cycles;
  dividing by the same-layer mirror (ruler b) brought it to the exact value within 2 SE in three of six cells at t = 3
  and 4 (at t = 4 with 2 SE about 0.10: d −0.080, ends −0.180 to +0.020; d −0.102, ends −0.213 to +0.009), and the
  circuit's own total (ruler a) in none. 39 s charged.

## Limits

- One device-day, 7 pairs. The words use 2 SE on the scatter of 7 pairs, which the dry runs show gives false DIFFERS in
  about 9 to 12 % of noise-free cells (rule 4 now asks for the t quantile in later declarations; this one keeps 2 SE).
- The rulers' readings of the kind of shrink are readings of their directions, from the dry runs with illustrative
  noise; nothing here measures the noise. Values on other nights are set beside, not compared.

## Independent check (home VS, 2026-11-24)

Re-counted from `or/job/raw_counts.json`, the sent circuits and the sealed answers with qiskit, Aer and numpy only (no
psf-os, no notebook scorer; the qubit-to-bit map read from the circuits' measure instructions; the strings regenerated
from the declared rule, 26 drawn for 7 pairs): the 18 raw words, rulers (a) and (b) with their d, 2 SE and words, the
uniformity r, chi2 and p, the rows of tables 1 and 2, the order and the beside values agree with this record (largest
difference 3.3e-16). Sent as declared: 139 circuits (126 items, 9 mirrors, 4 sentinel pubs; sha256 equal to the
manifest's), 1000 shots per pub, every L item on F's placement at the same chain positions, CZ and CZ layers as
declared, the device picked by the rule, no delay and no gate after a measurement; `results/` byte-equal to the run's
raw output. The sealed answers' sha256 is the declared 59cbd7a0...; the answers by label differ from it by 0. Try 1:
no `or/` and no job folder in the raw output, so nothing was assembled to send (IBM's job list not looked at).
Reproduce 1 of 1 SAME. Corrected here: the direction of ruler (a) (beside), the sentinel added (beside), the 2 SE ends
of ruler (b) at t = 4 (two numbers). Noted, not changed: the tool's table-1 text for "NOT UNIFORM x AGREES" reads "on
the mean only" where the declaration reads "on the mean, not per position" (the row did not occur tonight). Its tool and
output: `notes/verify_2026-11-24/`.

After the record, never judged (`notes/verify_2026-11-24/or_score2_output.txt`, the workplace's
`gpu/ohm_ruler_night2.py score2`): ruler (c), the square root of the window's own mirror, DIFFERS on the positive side
in five of six cells at t = 3 and 4 (AGREES at A0 t = 3, +0.014, SE 0.024); with the t quantile (2.447) in place of
2 SE, the only word that changes is ruler (b) at A2 t = 3 (DIFFERS to AGREES). By position (`notes/verify_2026-11-24/or_beside_positions.txt`):
the window's √(mirror) is above its r at 32 of 36 window positions; at t = 4 the same-layer mirror's <Z> on physical
qubits 101, 102 and 104 is near 0 (0.022 / 0.080 / 0.014 in A0; down to −0.044 in A2), while at t = 3, where they lie
outside the cone, nothing of the kind shows; position 25 (physical 107) has a low r at t = 4 in all three arms (0.668 /
0.659 / 0.764) but a mirror like the others (√ 0.85 to 0.88). Guess (not measured): those qubits pull down the
circuit's total and the mirror's mean at t = 4, which would account for r above rho_a and for ruler (b)'s sign at
t = 4. Not read from the calibration; seen in the sent circuits' own mirrors.

## Reproduce

`python reproduce.py --psf-os <psf-os 0.3.3> ohm-ruler-night-2026-11-24` (1 of 1 SAME at home).
