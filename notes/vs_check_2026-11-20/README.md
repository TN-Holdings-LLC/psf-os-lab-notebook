# The workplace VS's independent check of tonight's two tools (2026-11-20; copied from the VS's return)

Report `報告_今夜の道具2本の独立の点検_2026-11-20.md`, scripts and outputs as returned (SHA256SUMS). In short:

- decoy, checked with qiskit and numpy only: Z's bits 0..4 in D1 and 10..14 in D2; A [0-3], B [5-8], Z [11-14],
  B to Z coupling distance 3; every packed sub-item the same instruction sequence as its single; noiseless ff 0.7934,
  off 0.6306 (the tool: 0.7929, 0.6308).
- loopvar: V1-V3 byte-identical (78 files); copies a, b twice each, every one gate-identical to the 11-19 r1; chi2,
  p and the excess variance as the tool's.
- psf-os night-2026-11-20 (61869bb), full suite on a Pod with the notebook as TOQB_DIR: 328 passed, 2 skipped (quimb
  absent), 20 min 05 s; with quimb, 336 tests collected (0.2.0's 335 and the new one).
- Noiseless decoy dry, 20 seeds: 0 of 120 sub-item words LESS / MORE. Not the 4.6 % the workplace asked about: with no
  noise both values sit near the exact v, so d = |s - v| - |p - v| folds and spreads 0.60 of what the 2 SE formula
  assumes (0.21 % beyond 2 SE). On a device night s sits about 0.06 below v and the threshold works as declared.
- Noiseless loopvar dry, 20 seeds: copies' (a - b) / SE SD 0.95; three-job p about uniform (mean 0.49).
- Aer seeds: confirmed (seed s + 1 is seed s shifted by one shot); tonight's tools' strides do not overlap.
- Beside: the ring sentinel overlaps A's qubit 3 and B's 5-7 only; A 0-2, B 8 and Z are not covered (candidate 4).

## Added by the VS for the owner's decisions (その3)

- The new decoy reading table recounted from the draft's text alone (`coverage_decoy_v2.py`): 729 outcomes, each on
  exactly one row, the same counts per row as the workplace's. The reading "D1's A and B lose, D2's A keeps -> row 6"
  agreed (reasons in the report).
- The 9-df chi2 p of loopvar against scipy: equal to 4e-15 (`chi2_vs_scipy.txt`). The pooled LV-1 on 20 noiseless
  seeds: 1 MOVES in 20, as expected at p < 0.05 (`loopvar_lv1_pooled_20seeds.txt`).
