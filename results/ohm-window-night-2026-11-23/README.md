# Ohm on the wall's light-cone window, twins in one job, 2026-11-23 on ibm_kingston (`prereg/ohm_window_night_2026-11-23.md`)

- Declared in 42db25ae and pushed by the owner before the night's first fetch: the run's notebook clone, made from GitHub
  in the GitHub step, was at 42db25ae (checked by the run script). Run on the owner's machine (`versions.txt`: Python
  3.12.13, qiskit 2.5.2, aer 0.17.2, runtime 0.49.0, numpy 2.5.3) with psf-os 0.3.3 (a45c54a, from the release bundle;
  released 2026-11-24), the sealed answers' sha256 checked (216d6b96...).
- Queue read 14:52:40 CET (`fetch_in/queue.json`): marrakesh 1 (not used), fez 5, kingston 1 -> **ibm_kingston**
  (`pick.txt`), calibration 2026-11-23 14:21:41 CET; dt 4e-09 s.
- Built as declared (`build.txt`, `ow/build.json`): chain shape S1, F at copy drow 0, every L item on F's physical
  qubits; CZ as intended (t = 3: L 66 / 99, F 234 / 351; the same CZ layers); nothing parked; floor and mirror on A1 s00
  at each t and twin (4 items). The first build with every floor and mirror is kept unsent (`ow/unsent_first_build`,
  `ow/unsent_runs`).
- Pre-run check on the job's compiled circuits (`check.txt`): **ALL PASS** (worst 1.6e-10; mirrors within 1e-6; the
  twins' windows equal to 5.7e-11).
- Scored by the declared tool on the owner's machine (`score.txt`, `ow/scores.json`); re-scored at home: the same text.
- `*.qpy` files are gzipped (`gunzip` restores them byte for byte); the scorer reads the counts only.

| job | folder | id | circuits | shots | s model | s charged | RU | created - finished (CET) |
|---|---|---|---|---|---|---|---|---|
| job | `ow/job/` | dc24b7uq4uuc73a4mv60 | 180 | 1000 | 58.1 | **50** | **0.823** | 14:54:39 - 14:55:41 |

The project's usual formula (2.6 s + 0.000269 s x circuits x shots), used in the declaration, gives 51.0 s; the column is
psf-os's own model.

## Results (ratio = mean squared error ÷ mean square of the exact value; READS at 0.5 or below)

| arm | t | window M: L / F | window W: L / F | W device L / F (exact) | twins: F − L (SE) |
|---|---|---|---|---|---|
| A0 | 1 | 0.001 / 0.002 READS | 0.001 / 0.001 READS | 0.284 / 0.284 (0.286) | +0.0003 (0.0001) KEEPS MORE |
| A0 | 3 | 0.012 / 0.011 READS | 0.012 / 0.010 READS | 0.843 / 0.833 (0.750) | −0.0013 (0.0014) SAME |
| A1 | 1 | 0.001 / 0.002 READS | 0.001 / 0.001 READS | 0.282 / 0.282 (0.286) | +0.0002 (0.0002) SAME |
| A1 | 3 | 0.029 / 0.028 READS | 0.028 / 0.027 READS | 0.770 / 0.767 (0.655) | −0.0003 (0.0036) SAME |
| A2 | 1 | 0.002 / 0.002 READS | 0.001 / 0.001 READS | 0.277 / 0.282 (0.286) | −0.0000 (0.0001) SAME |
| A2 | 3 | 0.049 / 0.048 READS | 0.049 / 0.048 READS | 0.663 / 0.662 (0.527) | −0.0003 (0.0026) SAME |

- Window M and window W: **READS in all 24 cells.**
- Twins: SAME in five of six cells; A0 at t = 1, the light-cone circuit KEEPS MORE by +0.0003 (SE 0.0001), on a ratio
  of 0.001 against 0.002.
- Order of W at t = 3 (A0 > A1 > A2): **L yes, F yes.**
- Reading (the declared tables): per cell, "each circuit's transfer and the wall's transfer both read"; together at
  t = 3, **"the window reads; cutting the outside adds nothing at this size"** (window M READS on F in all three arms,
  twins SAME in all three at t = 3: F − L within 2 SE, whose ends are at most about ±0.007); order "the arms' order
  shows in both twins".

Beside, never judged, never used to correct:
- The device's W at t = 3 is above the exact value in every arm and twin: +0.083 to +0.135, 2 SE 0.034 to 0.052 over
  the 7 pairs, each separated from 0 (11 to 26 % of the exact value); at t = 1 it is within 2 SE of the exact value
  (−0.001 to −0.009). W(3) / W(1): device 2.35 to 2.97 against exact 1.85 to 2.63. Guess (not measured), as the 11-12
  declaration warned: noise mixes spins and looks like extra transport. The ratio rule reads the excess as small against
  the exact mean square; READS does not say there is no bias.
  Read again at the desk after the night (workplace, `notes/ohm_window_beside_2026-11-24`, re-run at home: the same
  output): the excess is, in this record, almost all a uniform shrink of the odd part of <Z> (a factor 0.86 to 0.89
  per cell at t = 3, the same in L and F within SE), not an extra transport; the even part's shift on the window at t = 3 is
  -0.006 to +0.009 (2 SE 0.003 to 0.008), three of six within 2 SE. Beside; no value is corrected.
- S = mean of M_w(s) + M_w(c): −0.005 to −0.021 at t = 1; at t = 3 +0.028 / +0.005 (A0), −0.040 / −0.026 (A1), −0.131 /
  −0.168 (A2), L / F (A2's exact S is not 0).
- Floor (A1 s00): 0.963 / 0.983 (t = 1, L / F), 0.978 / 0.983 (t = 3). Mirror: 0.868 / 0.899 (t = 1), 0.720 / 0.723
  (t = 3). Ring sentinel CLEAN.

## Against the declaration

- **OW-1 (at t = 3, the window's M READS on F in all three arms): held** (0.011 / 0.028 / 0.048).
- Predictions over the nights of 11-16 to 11-23: 69 declared; 49 held, 20 failed.

## Two numbers side by side

- Vanity: 24 of 24 cells READS, and the arms' order at t = 3 in both twins.
- Essence: summed over the wall's light-cone window, the transfer across the wall reads on raw kingston at 1 and 3
  cycles on a 40-qubit chain (error ratios 0.011 to 0.048 at t = 3), where the whole right half did not read on 11-12
  at 3 cycles (kingston's A0 read at 6); the device's W at t = 3 is 11 to 26 % above the exact value (each 2 SE away
  from 0), and the transport exponent is not read by this test. Cutting the circuit to the window's light cone (16
  instead of 40 qubits, 28 % of the CZ, the same layers) changed nothing beyond 2 SE at t = 3 (2 SE up to about 0.007).
  50 s charged.

## Limits

- One device-day, 7 pairs. The window idea came after the 11-12 records were seen; this night repeats it on a new day
  and another calibration (F at t = 3 repeats 11-12's circuits).
- t = 1 is equal across the arms by construction. Values on other nights are set beside, not compared.
- The twins share their physical qubits and layers; they differ in qubits measured, CZ and spectators, and a difference
  would not say which. Here none was seen at t = 3.

## The psf-os it ran with

The night ran with a45c54a, the commit tagged v0.3.3 on 2026-11-23. Before the release (2026-11-24), the workplace
reading corrected 0.3.3's documents and one function, `feedforward.version_key` (a bare `.devN` now sorts before the
pre-releases); the release is e652257. The two differ in no step of a build; re-scored with e652257: SAME.

## Reproduce

`python reproduce.py --psf-os <psf-os 0.3.3> ohm-window-night-2026-11-23` (1 of 1 SAME at home).

## Independent check (home VS, 2026-11-23)

Re-counted from `ow/job/raw_counts.json`, the sent circuits and the sealed answers with qiskit, Aer and numpy only (no
psf-os, no notebook scorer; the qubit-to-chain map read from the circuits' measure instructions, not from build.json):
the 24 cells' ratios and words, the six twins (A0 t = 1 KEEPS MORE, +0.00032, SE 0.00014; the rest SAME), the order
(yes, yes), OW-1 held, and the beside values agree with this record. Sent as declared: 180 circuits (sha256 equal to the
manifest's), 1000 shots per pub, the first 7 pairs (the 11-12 strings), every L item on F's physical qubits at the same
chain positions, CZ and CZ layers as declared, floor and mirror on the 4 A1 s00 items only, 4 sentinel pubs, the device
picked by the rule (fez 5, kingston 1), no delay and no gate after a measurement. The sealed answers' sha256 is the
declared 216d6b96...; the answers by label (sha256 3b7d22a5...) equal them; the sent circuits' noise-free values are
within 1.6e-10 of them. Reproduce 1 of 1 SAME. Not checked independently: the sentinel's CLEAN (psf-os's rule; the
960-CZ noise-free run was stopped). Corrected at its notes: the twins' 2 SE ends, the 2 SE of the W excess, the guess
marked as a guess, the 11-12 comparison limited to 3 cycles, and 28 % (not about a third) of the CZ. Its tool:
`notes/verify_2026-11-23/ow_independent_check.py` and its output.
