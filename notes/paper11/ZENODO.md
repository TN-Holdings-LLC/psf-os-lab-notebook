# Paper 11, version 1: Zenodo input (home, 2026-11-24)

- Upload (two files):
  - `TN-Holdings_Paper11_v1_Where-a-Qubit-Waits.pdf`：the same bytes as `notes/paper11/paper11_v1.pdf`, built from
    `notes/paper11/paper11.tex` in the commit that adds this file.
  - `fig_data.csv`：every plotted value with its source (`notes/paper11/fig_data.csv`).
- Title: Where a Qubit Waits: Rules for Real-Time Control from Declared Device Tests on IBM Heron
- Creator: TN Holdings (no personal name; no e-mail in the record).
- Resource type: Publication / Preprint. Language: English. Licence: as papers 1-10.
- Keywords: quantum computing; IBM Heron r2; dynamic circuits; mid-circuit measurement; feed-forward; real-time
  control; idle qubits; qubit parking; pre-registration; reproducibility; iterative phase estimation;
  repeat-until-success; repetition code.
- Related identifiers:
  - is supplemented by https://github.com/TN-Holdings-LLC/psf-os-lab-notebook (URL);
  - is supplemented by 10.5281/zenodo.24496267 (DOI; psf-os 0.3.3);
  - is supplemented by 10.5281/zenodo.24438701 (DOI; psf-os 0.3.1);
  - is supplemented by 10.5281/zenodo.24416958 (DOI; psf-os 0.3.0);
  - continues 10.5281/zenodo.24367001 (DOI; paper 10).
- Description (the abstract as plain text):

A circuit that measures in the middle and acts on the result at once loses part of what it keeps while it waits. Paper 10 of this series showed that such real-time control on IBM Heron devices can get closer to the exact answer than any correction of the uncontrolled circuit. This paper asks what an operating layer should do with the waits. Every test was declared in git before its device record was fetched; every comparison that decides a rule was made inside one job; every shot was counted, and no error mitigation, post-selection or fitted noise model was used. Nine declared runs (eleven tests; the decoy and loopvar tests shared one session) were sent in eight charged sessions on three devices (ibm_marrakesh, ibm_fez, ibm_kingston; 706 s charged; 11 declared predictions, all held; a prediction was declared only where an earlier device record grounded it, and over the series 20 of 68 failed, all on paper 10's nights). Four rules came out. (1) A qubit that waits in |1> keeps more if it is turned to |0> for the wait and back after: +0.039 (2 SE 0.005) on iterative phase estimation (IPE) at n=4, +0.031 to +0.039 at n = 4,5,6 on another calibration, +0.029 and +0.052 on two further devices; fencing it so that it waits in |1> instead of a superposition read SAME WITHIN ERROR (-0.004, 2 SE 0.005) on the one night it was sent. On one night and one device, parking a qubit that is only more likely in |1>, behind a fence around it and its wait, kept +0.097 and +0.025 more than the previous default on two of three chains of repeat-until-success (RUS) neurons (the third SAME WITHIN ERROR). (2) Fewer qubits holding a superposition during a wait, and fewer CZ, each keep more (repetition code, whose forms also differ in depth: +0.015 and +0.022; on a second device +0.028 and +0.011, where the best form passed its ceiling, 0.929 against 0.875). (3) Two conditional items side by side cost the first of them 0.057, and 0.085 with a fixed item's bits last. (4) The same circuits drift between jobs sent seconds apart (one of three chain lengths, p = 0.006) while copies inside one job agree; a loop that decides inside one job keeps that drift out. Phase estimation, parked, stayed beyond its ceiling to n = 8 (0.424 against 0.201), with a loss per added bit that grew from n = 6 to 8 on that night. Replacing every phase conditional by its right correction, unconditional, changed the share by +0.005 (2 SE 0.006). The operating layer, psf-os, now parks by default (releases 0.3.0 and 0.3.1) and, from 0.3.3, checks at every build that a parked qubit stays parked in the circuit as sent. No quantum advantage is claimed.

## Checks done before upload

- `pdftotext paper11_v1.pdf - | grep -c PENDING` gives 0; 8 pages; latexmk: no overfull box, no undefined reference.
- Every decimal in the text was found in the records (score files, READMEs, declarations); the home VS and the
  workplace read the drafts independently and their points are applied (`workplace_reading_2026-11-24.md`).
