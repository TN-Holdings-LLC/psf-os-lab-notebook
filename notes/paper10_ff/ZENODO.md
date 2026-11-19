# Paper 10, version 1: Zenodo input (home, 2026-11-19; from the workplace's draft ZENODO_DRAFT.md)

Published by the owner on 2026-11-19: **doi:10.5281/zenodo.24367001** (version 1.0; all versions
10.5281/zenodo.24367000). The description was first pasted from the PDF (first sentence lost, spaces lost at line ends)
and replaced the same evening with the plain text below; the title was set to the PDF's full title (record page read by
the owner, 21:06 JST). psf-os 0.2.0 was released on GitHub and archived by Zenodo the same evening: doi:10.5281/zenodo.24367846.

- Upload: `TN-Holdings_Paper10_v1_Decisions-No-Correction-Can-Reach.pdf` (the same bytes as
  `notes/paper10_ff/paper10_v1.pdf`, built from `notes/paper10_ff/paper10.tex` in the commit that adds this file).
- Title: Decisions No Correction of the Uncontrolled Circuit Can Reach: Real-Time Control on IBM Heron, Declared Before
  the Data
- Creator: TN Holdings (no personal name; no e-mail in the record).
- Resource type: Publication / Preprint. Language: English. Licence: as papers 1-9.
- Keywords: quantum computing; IBM Heron r2; dynamic circuits; mid-circuit measurement; feed-forward; real-time
  control; correction ceiling; pre-registration; reproducibility; repeat-until-success; iterative phase estimation;
  repetition code.
- Related identifiers:
  - is supplemented by https://github.com/TN-Holdings-LLC/psf-os-lab-notebook (URL);
  - is supplemented by 10.5281/zenodo.24367846 (DOI; psf-os 0.2.0);
  - continues 10.5281/zenodo.24278888 (DOI; paper 9).
- Description (the abstract as plain text):

A circuit that measures in the middle and acts on the result at once has a natural comparison: the same circuit with the actions removed. Whatever is done to that uncontrolled circuit after the run, including error mitigation at any shot cost, returns at best its own noiseless value; the distance from that value to the exact answer is a correction ceiling c. We ask whether real-time control on today's cloud devices gets closer to the exact answer than c, with every shot counted, no mitigation, and every test declared in git before the device record of its run was fetched. Over four nights on IBM Heron devices (57 declared predictions: of the 49 of 11-16 to 11-18, 33 held and 16 failed; of the 8 of 11-19, 4 held and 4 failed; every failed one is reported as failed), chains of repeat-until-success (RUS) neurons crossed the ceiling and the margin grew with the chain length (slope +0.024 per neuron on ibm_fez; +0.031 and, after a recalibration, +0.053 for a frame-balanced pair on ibm_marrakesh); iterative phase estimation crossed its ceiling at n = 2, 3 on ibm_fez and n = 4 on ibm_marrakesh (0.903 against 0.471 at n = 4). Getting there needed a diagnosis on the device: the first neuron design lost its value not to the conditionals, which cost nothing measurable when they did not fire, but to time spent in |1> during mid-circuit measurement waits; holding the likely value as |0> recovered 0.11-0.22. That one-sided decay can also push a design above its own noiseless value; a guard declared beforehand took those cases out, and a frame-balanced pair removes the lean by construction. Two limits are measured: fixed circuits can share a circuit with no loss (halving device time), but two items with conditionals in one circuit cost the control arm (0.20 on average with ten items; 0.06 on the first of two), which a delay did not remove and which is not explained by decisions waiting for each other (no decision latency above about 0.4 us was resolved). Finally, a prescription loop that diagnoses the device, applies a fixed rule and runs the chosen circuit ran unattended on the device and picked a different prescription after the device was recalibrated. On a fourth night, the loss between two conditional items followed the register's bit order, not the qubits: the item whose bits came first lost (-0.037, 2 SE 0.020), as on 11-18. Two more tests inside one item cost nothing measurable when they did not fire (repetition code), though the code decoded in real time stayed below its ceiling (0.812 against 0.875). Phase estimation crossed its ceiling again at n = 2, 3, 4 on one device and night, and, as a separate yardstick, was right per shot more often than the textbook circuit by +0.03, +0.07, +0.17. The loop, run from the package, refused the previous night's ledger after a recalibration, stopped spending where its prescription never helped, added one try where it did, and reached a fixed point. What the device keeps of the noiseless value varies by night (0.61-0.87 for the same balanced pair on two nights); no quantum advantage is claimed.

## Checks done before upload

- `pdftotext paper10_v1.pdf - | grep -c PENDING` gives 0; 12 pages.
- The numbers of 11-16 to 11-18: the workplace VS's check of draft 1 (seven points corrected in draft 1c). The numbers
  of 11-19: transcribed from the committed score files, which the home VS re-counted from the raw counts; a mechanical
  match of every decimal in the 11-19 sections against the records' score files and READMEs left none unmatched.
