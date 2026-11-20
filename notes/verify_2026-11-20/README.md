# The night of 2026-11-20: the home VS's independent recount (decoy, loopvar, the paired loop)

Home VS Claude, from the home instruction `VSクロードへの指示_今夜の結果の独立検証_2026-11-20.md` (and, for the paired loop, `VSクロードへの指示_輪の同じジョブ比べの独立検証_2026-11-20.md`; report `VSから家へ_輪の同じジョブ比べの独立検証_2026-11-20.md`). The report to home is
`VSから家へ_今夜の結果の独立検証_2026-11-20.md` (psf_zero_project).

The scripts use qiskit, aer and numpy only, reading job/raw_counts.json, job/manifest.json and job/circuits.qpy. They
do not use psf-os or the notebook's scorers. The right output value and the noiseless reference come from noiseless
Aer sampling of the record's own circuits. The p values come from a series written here (no scipy).

| file | output | result |
|---|---|---|
| `decoy_indep.py RECORD OUT.json` | `decoy_indep.txt`, `decoy_indep.json` | Six conditional sub-items, Z beside and the bundle means equal the record. The words are equal. The reading table, rows in the declared order, gives row 2. 22 circuits, 4000 shots, A [0-3], B [5-8], Z [11-14]. Z's bits are first in D1 and last in D2. |
| `loopvar_indep.py RECORD OUT.json` | `loopvar_indep.txt`, `loopvar_indep.json` | g and SE per L and job, within-job and between-job differences, chi2 and p per L, the excess SD, the 6 df total (p 0.013) and the 9 df copies (p 0.625, SAME WITHIN ERROR) equal the record. L1 is SHOT NOISE ONLY (p 0.080); only L2 DRIFTS (p 0.006); L3 is SHOT NOISE ONLY. |
| `paired_indep.py RECORD OUT.json` (the evening's paired loop, `results/loop-paired-night-2026-11-20`) | `paired_indep.txt`, `paired_indep.json` | The diagnostics (Dc, Dw, Dr and their losses), the pick P2/P1/P2, every round's P of the incumbent and the candidate, SE, exact, d and 2 SE equal the record. The declared rule, written again here (climb_on_kept on), gives RULE2 and RULE3 and the stop as recorded. No candidate overshoots. LP-2: one row (L3's P2 as the incumbent in r2), held; the two steps adopted in r2 not counted. 110 s, 1.7941 RU. |

Beside:
- V1, V2 and V3 are byte-identical (circuits.qpy and manifest).
- The coupling distance from B to Z is 3.
- reproduce.py with psf-os 61869bb gives 2 of 2 SAME.
- Predictions: tonight 2, both held; in all, 59 declared, 39 held and 20 failed.
- The paired loop: reproduce.py with psf-os a164fc5 gives 2 of 2 SAME (dw, dc); `gpu/os_loop_paired.py verify` gives every step SAME; results/ unchanged after both.
