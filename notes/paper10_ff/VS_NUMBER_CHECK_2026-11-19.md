# Paper 10, draft 1: every number against its record (workplace VS Claude, 2026-11-19; home's hand-over 19b, VS item 3)

Checked: `notes/paper10_ff/paper10.tex` at 9af626e1, against the `results/` READMEs and score files that each sentence
names, and `notes/paper_ff_2026-11-17/OUTLINE.md` for the tally. The text is not changed. The figures
(`figures.py`) read the score files directly, so they were not checked number by number.

Result: about 130 numbers. All but the rows below agree with their records at the printed precision.

## Rows to look at

| line | the paper says | the record says | kind |
|---|---|---|---|
| 109 | design's noiseless value at L = 1: **0.892** (with 0.793, 0.706, 0.629, 0.560) | the m = 2 design's noiseless value at L = 1 is 0.890 in every score file (`compound_scores.json`, `early2_scores.json`, both `balanced_scores.json`: ff_noiseless, 0.890 to three decimals); line 157 of the paper uses 0.890. 0.892 is the 11-16 pre-run check's Aer sample (4000 shots, `rus-neuron3-2026-11-16`) | different |
| 132 | third design's noiseless value 0.892, 0.792, 0.708 | as written in `rus-neuron3-2026-11-16` (the pre-run check's 4000-shot Aer sample). The same design's exact noiseless value, used at lines 109, 157 and in every 11-17/18 record, is 0.890, 0.793, 0.706 | inside the paper: two values for one quantity |
| 133 | kingston L = 1: 0.853 | 0.8525 (3410 / 4000, `rus-neuron3-kingston-2026-11-16`); 0.853 rounds half up, 0.852 half to even | rounding at a tie |
| 289 | the noiseless design lies **0.04**-0.19 below the exact value (L = 1..7) | exact minus noiseless: 0.047 at L = 1 (0.937 against 0.890), 0.191 at L = 7; 0.047 rounds to 0.05 | rounding |
| 131 | the output qubit read \|1> as 1 in only about 0.8 of the shots | not in the folder cited there (`rus-neuron3-2026-11-16`). It is in `rus-neuron-2026-11-16` ("about 19 % of \|1> read as 0") and `ctrl-diag-2026-11-16` (control read 1 in 0.78) | source to name |
| 244-245 | no block qualifies for the low-latency path (each holds a CZ) | not in `results/parallel-night-2026-11-18/README.md`; it is in the declaration `prereg/parallel_night_2026-11-18.md` (line 15) | source to name |
| 302-305 | the entries of 11-16 to 11-18 re-scored the same on 2026-11-18, with psf-os at the commit named in each folder | each folder's README records SAME on its own night (11-16, 11-17 or 11-18) with the folder's commit. The one re-score of all 28 entries on 11-18 (28 of 28 SAME) was with the v0.2 prototype branch (`notes/v02_2026-11-18`, 995a749d) | two statements joined |

Wording, beside (no number is wrong):
- The abstract's "iterative phase estimation crossed its ceiling at n = 2, 3, 4" spans two devices: n = 2, 3 on fez,
  n = 4 on marrakesh. Section 4 says so; the abstract does not.

## Checked and agreeing (by section)

- **Abstract and tally.** 49 predictions, 33 held, 16 failed. Recounted from the READMEs:
  - declared: 11-16 15, 11-17 22, 11-18 12;
  - failed: 11-16 4, 11-17 7, 11-18 5;
  - the 16 match `OUTLINE.md` and table 2 (14 rows, two of them counting two).

  The other numbers in the abstract: slopes +0.024 / +0.031 / +0.053; 0.903 against 0.471; recovered 0.11-0.22;
  0.20 with ten items, 0.06 on the first of two; about 0.4 us; 0.61-0.87.
- **Method.** θ = 1.1. Exact 0.937, 0.878, 0.823, 0.771, 0.723. Noiseless 0.793, 0.706, 0.629, 0.560 (L = 2..5).
  c(L) 0.143, 0.247, 0.322, 0.373, 0.407, 0.426, 0.435 (the score files' c). 4000 shots.
- **Section 3.**
  - Try patterns within 0.012 (0.685 / 0.214 / 0.063 / 0.038 against 0.673 / 0.220 / 0.072 / 0.034).
  - ff 0.599, 0.629, 0.551 against 0.918, 0.850, 0.790; two of three failed.
  - D_cond +0.006 (2 SE 0.022); D_meas 0.23 on qubit 1.
  - Control 0.98 -> 0.46 (qubit 1) and 0.96 -> 0.72 (qubit 3); neighbours inside 2 SE.
  - Gains +0.113 / +0.179 / +0.182 (2 SE 0.021-0.022); +0.217 at L = 1.
  - ff 0.883 / 0.740 / 0.631, CLOSER at every L; kingston 0.749, 0.646, CLOSER at every L.
- **Section 4.**
  - T2: g +0.075 ... +0.158, 2 SE 0.011-0.016; slope +0.024 (2 SE 0.004); -0.021 to -0.086; 0.65-0.78.
  - T4: 10 CZ against 42, a third of the waits, the same within 2 SE, T4-3 failed.
  - N2: g up to +0.229; 0.903 against 0.890; 0.487 against 0.444; NOT SHOWN, both failed.
  - Balanced 11-17: g +0.057 to +0.117, -0.019 at L = 1, +0.031 (2 SE 0.003).
  - Balanced 11-18: +0.053 (2 SE 0.003); g -0.185 / -0.121 / -0.067 / -0.011 / +0.024; 0.61-0.68 against 0.77-0.87.
  - Phase estimation: 0.861 / 0.750, 0.772 / 0.588 (GROWS), 0.903 (2 SE 0.002) / 0.471.
  - Teleport: 0.952 / 0.890 on 11-16; 0.849 and 0.734 on 11-17 (T3-3 failed).
- **Section 5.** rd 0.92-1.01, nf 0.60-0.80 (11-17); qubit 1 at 0.83 (0.826); 0.967 against 0.955 after the
  recalibration; the pool never overshot.
- **Section 6.** T1 and N1 CLOSER as stated; 0.032 further on fez (8 CZ against 2 CZ and two measurements); the same
  within 2 SE on marrakesh.
- **Section 7.**
  - 11-17: P2 at L = 1, 2, 3; +0.043, +0.079; overshoot at L = 1; one of two failed.
  - 11-18: P1; +0.032 / +0.026 / +0.055 (2 SE 0.017-0.022); fixed point after round 1; 82 s; recalibrated at 10:40;
    OS2-1 failed, OS2-2 held; verify SAME.
- **Section 8.**
  - Packing 11-17: 41 s -> 11 s; -0.20 (2 SE 0.007), up to 0.43; off within 0.03.
  - P-A: +0.001 (2 SE 0.007); 16 circuits and 20.9 s against 34 and 40.9 s; same CLOSER verdicts.
  - P-B: -0.015, 0.060 / +0.012, -0.062; PB-3 failed; the loss on the first item's output bit.
  - Timing: 2.78 us; +0.32 (2 SE 0.42) NOT RESOLVED; 0.96 (0.19); 1.00 (0.22).
- **Table 2.** Every row matches its folder's "Against the declaration".
- **Section 10.** Sentinel DEAD on marrakesh and fez on most nights (kingston 11-16 and P-B 11-18 CLEAN).
- **Introduction and references.** The DOIs of papers 7, 8, 9 and psf-os match `notes/paper7`-`paper9`
  (ZENODO.md, paper9.tex).
