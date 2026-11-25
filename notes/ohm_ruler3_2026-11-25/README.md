# Ohm rulers, the third night's candidates: tool, try-builds and dry runs (workplace Claude, 2026-11-25; desk, no device)

Home's instruction "オームの物差し、次の晩の宣言の下書き" (2026-11-25), after `results/ohm-ruler-night-2026-11-24`. Tool
`gpu/ohm_ruler_night3.py` (new; `gpu/ohm_ruler_night.py` and `gpu/ohm_ruler_night2.py` imported read only); draft
`prereg/drafts-2026-11-25/ohm_ruler3_night_DRAFT.md`. psf-os 0.3.3 (e652257), qiskit 2.5.2, qiskit-aer 0.17.2. No
file under `results/` and no declaration is written; no device was used.

| file | what it holds |
|---|---|
| `dry3.py` | dry runs of a built job (as `notes/ohm_ruler_2026-11-24/dry.py`), with ILLUSTRATIVE readout-like faults written by hand: symmetric flips on every bit, or flips on chosen chain positions (1 -> 0 with q10, 0 -> 1 with q01) |
| `seeds3.py`, `seeds3.txt` | score3's words over 16 seeds per case |

## Try-builds (11-23 ibm_fez record; `check3` ALL PASS each)

| plan | string mirrors | circuits | seconds (2.6 + 0.000269 x c x 1000) | psf-os model |
|---|---|---|---|---|
| B (`--smirrors none`) | 0 | 139 | 40.0 | 45.5 |
| B + d1 (`s`) | 9 | 148 | 42.4 | 48.3 |
| B + d (`sc`) | 18 | 157 | 44.8 | 51.0 |

- `build3 --smirrors none` writes the declared tool's job byte for byte (circuits.qpy equal, same build record).
- Every string mirror returned its string noise-free (worst 3.8e-14); every |0> mirror all |0>; every total equal to T0.
- On a noise-free dry run, score3's (a), (b), raw W and one-factor p equal the declared `score` exactly (difference 0).
- The draft's device procedure was run word for word by the workplace VS's `tools/procedure_dry.py` (its tools3
  branch): pick, build3 and check3 PASS. Its score line was run too, because the runner skips lines holding " score "
  and not " score3 "; a note for the runner (`\sscore\d*\s`).

## Dry runs (plan B + d, 16 seeds per case, t >= 3, 96 cells per row; words at the t quantile, 2 SE in brackets)

| case (ILLUSTRATIVE) | (a) | (b) | (c) | (d) | (d1) | (d) with tau 0.3 |
|---|---|---|---|---|---|---|
| no noise | 92 (87) | 92 (87) | 92 (87) | 92 (87) | 92 (87) | 92 (87) |
| positions 15, 18, 22 read 1 as 0 with 0.4 | 73 (68) | 30 (26) | 30 (26) | 61 (57) | 30 (26) | 61 (57) |
| the same with 0.8 | 69 (66) | 31 (27) | 31 (27) | 60 (52) | 31 (27) | 31 (27) |
| positions 14, 17, 18 (outside the window) flip both ways with 0.4 | 67 (62) | 0 (0) | 92 (87) | 92 (87) | 92 (87) | 92 (87) |
| every bit flips with 0.02 | 91 (89) | 2 (0) | 3 (1) | 1 (0) | 1 (0) | 1 (0) |

With the faults outside the window, ruler (b) with tau 0.3 (candidate 1) AGREES in 91 of 96 cells (86 at 2 SE), against
0 without: positions 17 and 18 were left out of its mean in all 96 t >= 3 cells, 14 in 95 (rho_b 0.933 -> 1.000). The window
rulers are untouched. The direction reads WINDOW SHRINKS LESS in 34 of 96 cells, NOT SEEN in 62.

- No noise: every DIFFERS is false; 4 of 96 at the t quantile (4 %), 9 of 96 at 2 SE (9 %): rule 4 halves the false
  words. Direction: 7 of 96 false (NOT SEEN 89). One factor: 9 of 96 NOT UNIFORM.
- A fault that a |1> suffers and a |0> does not is invisible to the |0> mirror (rho_b = rho_c = 1.000) and to the s00
  mirror alone when s00's bits there are 0 (rho_d1 = 1.000); the odd part of the two string mirrors sees it
  (rho_d 0.965 at q10 0.4) and (d) AGREES in 61 of 96 cells against 30.
- Candidate 1 at tau 0.3: at q10 0.8 the faulty window qubit (position 22) has m_q = 0.2 and is left out of (d)'s mean
  in all 96 cells, and (d) falls back to 31 of 96: the window's W carries that qubit's shrink, so leaving it out of a
  window ruler leaves the ruler short of the shrink. In the two 1 -> 0 cases no |0> mirror value fell below tau.
- So in these cases candidate 1 serves the ruler averaged over the whole circuit (b) and harms the window ruler (d): a
  rule that leaves out only qubits outside the window would keep the first and avoid the second (a further candidate
  for the owner; not built).
- Uniform readout flips (q 0.02) hit each mirror once, so every mirror ruler's square root misses them (as 11-24's dry
  runs): (b), (c), (d) DIFFER in nearly every cell; (a) AGREES in 91 of 96.

## 2026-11-25 b (home's proposals): (b'), 9 pairs at t = 4, the VS's gate-noise runs read again

- `score3` gives (b') as `b_out`: low |0> mirror qubits outside the window left out of (b)'s mean (tau 0.3; NOT READ
  below half). `seeds3b.txt`: the five readout cases again, same seeds (101 to 116), raw counts kept this time. (b')
  equals the 11-25 a `b_tau` in these cases; (d) is untouched by it.
- `vs2_rescored.txt`: the workplace VS's その2 raw counts (gate noise, T2, damping, 3-qubit faults; its build rebuilt
  from the 11-24 ibm_fez record with `build3 --smirrors sc`, 157 circuits) read again by this score3. Its (b), (c),
  (d) agree with the VS's own table (e.g. p2 0.02: 22, 29, 28 of 30); its t >= 3 rows include the t = 4 cells the VS
  did not run (counts all zero), so the draft quotes t = 3 alone. (b'): p2 0.02 9 of 30 against (b) 22; the 3-qubit
  depolarizing 10 against 22.
- Try-build with 9 pairs at t = 4 (`--pairs-t 1:7 3:7 4:9`; 9-pair answers sha256 e581df9d..., made again here): 169
  circuits with the string mirrors (48.1 s, psf-os model 54.7 s), 151 without (43.2 s, 49.2 s); check3 ALL PASS;
  noise-free score3 reads K 9 and t 2.306 at t = 4.
- The VS's damping rerun (5 seeds each, its pod p3) read again the same way: (d) 15 of 15 in each damping row; (c) 6
  and 5; (b') 5 against (b) 10 under the 3-qubit damping.

## The tables from the scores (`tables3.py`, `tables3_spec.json`, `scores3_dryruns.tar.gz`)

The draft's two dry-run tables are written by `tables3.py` from the score3 files themselves (packed in
`scores3_dryruns.tar.gz`: the workplace's 80 readout runs and the 79 VS runs read again; no raw counts, no answers).
`--check` finds every row of the spec word for word in the draft (2026-11-25: 13 of 13):

    mkdir /tmp/t && tar -C /tmp/t -xzf notes/ohm_ruler3_2026-11-25/scores3_dryruns.tar.gz
    python notes/ohm_ruler3_2026-11-25/tables3.py /tmp/t notes/ohm_ruler3_2026-11-25/tables3_spec.json \
        --check prereg/drafts-2026-11-25/ohm_ruler3_night_DRAFT.md
