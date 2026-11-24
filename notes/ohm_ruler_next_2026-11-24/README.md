# Ohm rulers, the next night's candidates: ruler (c), two widths, tests (workplace Claude, 2026-11-24; desk, no device)

Home's instruction "オームの物差しの、次の晩の準備" (i bundle). The night of 2026-11-24 was declared by home from plan B
(`prereg/ohm_ruler_night_2026-11-24.md`, c4518f53) and its tool `gpu/ohm_ruler_night.py` is not changed. Nothing here
is declared, and no file under `results/` is written.

| file | what it holds |
|---|---|
| `gpu/ohm_ruler_night2.py` | `score2 OUT ANS`: ruler (c), the mirror on the window alone, rho_c = sqrt(mean <Z> of the cell's mirror over the window's qubits), with the mirror's window shot noise in its SE; the words of (a), (b), (c) at 2 SE and at the t quantile side by side. It imports the declared tool read only, checks its (a) and (b) against the declared `scores.json` (1e-12) and writes `scores2.json` beside it |
| `tests/test_ohm_ruler_night.py` | 16 tests on the declared tool and on `score2` (a synthetic job with known <Z>; no device, no sealed answers) |
| `widths.py`, `widths.txt` | the dry runs' DIFFERS at 2 SE and at the t quantile (7 pairs: 2.447), from the declared scores of the 16 + 16 seeds of `notes/ohm_ruler_2026-11-24` |
| `seeds_c.py`, `seeds_c.txt` | the same count for (a), (b), (c) on dry runs scored by `score2` (seeds 101 to 116, noise-free and flips q 0.065) |

## Two widths (7 pairs, plan B; `widths.txt`)

Without noise every DIFFERS is false. The nominal rates are 9.2 % at 2 SE (t, 6 degrees of freedom) and 5 % at the t
quantile.

| noise | ruler | t | cells | DIFFERS at 2 SE | DIFFERS at the t quantile |
|---|---|---|---|---|---|
| none | (a) | 3, 4 | 96 | 12 (12 %) | 6 (6 %) |
| none | (b) | 1 | 48 | 4 (8 %) | 1 (2 %) |
| none | (b) | 3, 4 | 96 | 12 (12 %) | 6 (6 %) |
| flips q 0.065 | (a) | 3, 4 | 96 | 9 (9 %) | 6 (6 %) |
| flips q 0.065 | (b) | 1 | 48 | 8 (17 %) | 6 (12 %) |
| flips q 0.065 | (b) | 3, 4 | 96 | 96 (100 %) | 96 (100 %) |

Ruler (b)'s SE adds the mirror's shot noise, so its word is not exactly a t test; the t quantile is applied as written.
With flips, ruler (b) at t = 3 and 4 DIFFERS at both widths (the readout-like shrink, d 0.09 to 0.16): the wider
width does not hide it. At t = 1 the flips move ruler (b) by less, and the two widths differ there.

## The tests (`python -m pytest tests/test_ohm_ruler_night.py`: 16 passed, 1.2 s)

- The string rule: plan B's strings by hash (26 draws), the pairs complementary, each cone |T0| >= 6; 9 pairs extend
  the same draws (31).
- total = T0: free fermions on the 40-qubit chain at t = 1, 3, 4; the light-cone circuit (quimb) at t = 1, A1 and A2.
- The words, on a synthetic job (psf-os's job reader replaced by a stub; per-qubit <Z> known exactly):
  - no noise: the ruled W equals the exact W (|d| < 1e-9);
  - one uniform factor (0.85) with a small pair-dependent shift: (a) and (b) AGREES, table 2 "both rulers read";
  - a mirror shrunk once (readout-like): (a) AGREES, (b) DIFFERS.
- The uniformity test: the declared survival function equals scipy's chi2 (1e-12); r per position, its SE, the pooled
  r, chi2 and p equal a hand computation.
- `score2`: (c) equals (b) on a uniform mirror, and (a), (b) equal the declared scores; on a mirror shrunk on the window
  alone, (c) AGREES and (b) DIFFERS; the t table equals scipy to 5e-4.
- Documented, not changed: on data with no scatter at all (not a device case) the declared tool reads d = 0, SE = 0 as
  DIFFERS (the rule is |d| < 2 SE), and window qubits at exactly |<Z>| = 1 give shot SE 0, a NaN chi2 and NOT UNIFORM.

## Ruler (c) on the dry runs (`seeds_c.txt`; seeds 101 to 116, the same samples as `notes/ohm_ruler_2026-11-24`)

- Every one of the 32 `score2` runs found (a) and (b) equal to the declared `scores.json`.
- Without noise all three rulers have rho = 1, so (a), (b), (c) read the same words: (c) DIFFERS 12 of 96 at t = 3, 4
  at 2 SE, 6 of 96 at the t quantile, all false.
- With flips q 0.065 (a readout-like shrink, the same on every qubit) the mirror's window mean equals its whole mean
  (sqrt(window mirror) - sqrt(mirror) +0.0002 at t = 3, 4; -0.0011 at t = 1): (c) DIFFERS as (b) does, 96 of 96 at
  t = 3, 4 at both widths.
- Where (c) and (b) part needs a shrink that differs by place (gate noise): asked of the workplace VS (その2).

## The workplace VS's その2 (2026-11-24; its report, scripts and tables travel beside this folder, outside the notebook)

ILLUSTRATIVE noise, not fitted to a device; plan B; t = 3, 30 cells per row unless noted.

- Gate noise (p2 per CZ, flips q): ruler (c) follows the window's shrink more closely than (b). At p2 0.02, q 0:
  (c) AGREES 29 of 30, (b) 18, (a) 0 (r - sqrt(window mirror) -0.006, r - sqrt(mirror) -0.018, r - rho_a -0.084).
  A readout share moves (c) by about -0.02, as (b).
- t = 4, p2 0.01, 3 seeds (9 cells): r - sqrt(mirror) +0.019, r - sqrt(window mirror) +0.012, the other sign from
  t = 3; (c) AGREES 5 of 9, (b) 3 of 9.
- Amplitude damping per CZ (gamma 0.005, 0.01; 5 seeds, 15 cells; GPU statevector): every ruler's rho above r, and (c)
  farther from r than (b) (r - sqrt(window mirror) -0.011, -0.026; r - sqrt(mirror) -0.004, -0.016), the other order
  from gate noise. Ruler (a) moves as under depolarizing (r - rho_a -0.024, -0.047).
- 9 pairs, no noise (16 seeds): (a) DIFFERS 11 of 96 at both widths (t 2.306), against 12 and 6 with 7 pairs.
- `widths.py` now writes the nominal 2 SE rate of K - 1 degrees of freedom (it wrote 6's for every K).
