# Ohm with rulers inside the circuit: tool, try-builds and dry runs (workplace Claude, 2026-11-24; desk, no device)

Home's instruction "オームの「回路の中の物差し」の晩" (f bundle), on `prereg/README.md` rule 3 and
`notes/ohm_window_beside_2026-11-24`. Tool `gpu/ohm_ruler_night.py`; draft
`prereg/drafts-2026-11-24/ohm_ruler_night_DRAFT.md`. psf-os 0.3.3 (e652257). No file under `results/` and no
declaration is written; no device was used.

| file | what it holds |
|---|---|
| `dry.py` | dry runs of a built job: every circuit sampled noise-free on its active qubits (Aer). Optional bit flips with probability q on every measured bit, ILLUSTRATIVE and written by hand. The sentinel is not sampled (all-zero counts, marked) |
| `seeds.py`, `seeds.txt` | how often each word fires on dry runs over seeds |

## Strings (bits only; seed 20261124; |T0| >= 6 on each t >= 3 cone, >= 8 on the chain with F)

| plan | regions | pairs kept | draws | \|T0\| on the cones (t = 3 / t = 4) |
|---|---|---|---|---|
| L, t 1 3 4 (A, B, C) | cone t 3, cone t 4 | 7 (A: 9) | 26 (A: 31) | 6 to 12 / 6 to 12 (A adds -8 / -6 and +6 / +8) |
| L and F (D) | the cones and the chain | 7 | 33 | 6 to 12 / 6 to 14; the chain 8 to 14 |

On the 11-12 strings the chain's |T0| was 2 to 8, which made the total ruler poorly conditioned
(`notes/ohm_window_beside_2026-11-24`).

## Try-builds and checks on the 11-23 kingston record (`results/ohm-window-night-2026-11-23/fetch_in/ibm_kingston/dev`)

| plan | circuits | shots | seconds (2.6 + 0.000269 x c x s) | psf-os model | check |
|---|---|---|---|---|---|
| A: L, t 1 3 4, 9 pairs, 9 mirrors | 175 | 1000 | 49.7 | 56.5 | ALL PASS (4.9 s) |
| B: L, t 1 3 4, 7 pairs, 9 mirrors | 139 | 1000 | 40.0 | 45.5 | ALL PASS (3.9 s) |
| C: L, t 3 4, 7 pairs, 6 mirrors | 94 | 1000 | 27.9 | 31.8 | ALL PASS (3.7 s) |
| D: L and F, t 1 3 4, 7 pairs, 18 mirrors | 274 | 600 | 46.8 | 57.3 | ALL PASS (33.9 s) |

The chain was shape S1 at copy (0, 0), and every L item sat on F's physical qubits. CZ per form at t = 4: L 120
(A0) and 180 (A1, A2), at 16 and 24 CZ layers; F 312 and 468. At t = 1 and 3 the counts equal 11-23's. In every item
the noise-free per-qubit <Z> were within 1e-10 of the answers, the totals equal to T0 within 1e-12, and every mirror
all |0>.

## Dry runs (plan B; the sentinel not sampled)

- Without noise: ruler (a) and ruler (b) AGREES in every read cell; the raw W READS everywhere.
- Bit flips q = 0.065 shrink every <Z> by 0.87, once, in the circuits and the mirrors alike:
  - the raw W at t = 3 and 4 is above the exact value by +0.17 to +0.30;
  - ruler (a) brings it back (d within 0.015);
  - ruler (b) does not: sqrt(mirror) is 0.93, because the mirror took the flips once, not twice.
  - This is the case where the two rulers part: a readout-like shrink. Gate noise, which accrues with the layers, is
    asked of the workplace VS (その1).
- Words over seeds (`seeds.txt`, 16 seeds each, `seeds.py` on the scratch scores):
  - without noise, ruler (a) DIFFERS 12 of 96, ruler (b) 16 of 144, NOT UNIFORM 4 of 96: all false, near the 9 % of
    2 SE with 7 pairs (t, 6 degrees of freedom) and the 5 % level of the chi2;
  - with flips q = 0.065, ruler (a) 9 of 96, ruler (b) 104 of 144, NOT UNIFORM 5 of 96; the raw W READS in every cell.
