# A comprehensive paper over the series: outline (home, 2026-11-28; a long shot, kept apart from paper 12)

The owner, 2026-11-28: make a comprehensive paper over the whole series, as a try, beside paper 12 (whose plan in
`notes/paper12/` is not changed). Read again from paper 1 first: `papers_read.md`. Aim: one paper an outside reader
(and an arXiv endorser) can judge on its own. Not a review of our own preprints: a research paper whose results are
new analyses across all the records, with the eleven papers as its sources.

## The question

What can a layer on the user's side of a cloud quantum device find out and do, if it reads no calibration quality
number, applies no error mitigation, and declares every test before its data exist? Answered for IBM's devices:
papers 1 to 4 on compiler benchmarks, noise-model twins and a few device jobs; papers 5 to 11 and after on the Heron r2
devices ibm_fez, ibm_marrakesh and ibm_kingston; 2026-09 to 2026-11.

## The claim, in three parts (each with its vanity and its essence number)

1. **Placement by formula, with no map, gives circuits that read.** Raw, unmitigated, against answers sealed before
   the run: 22 of 22 practice circuits READ on two devices, up to 153 qubits (paper 7); the dual-unitary chain at
   N = 91 within 0.0037 of cos 2h to 2,205 CZ (paper 8); readable depth 30-73 steps beyond the folded ring and blind
   search on one circuit family (paper 5). Essence: theta 0.4 misses by 0.04-0.07; Fermi-Hubbard does not read at 6 steps; a 46 %
   CZ cut came farther from the answer on one lattice; formula placement did not beat search on a trained classifier
   (paper 3).
2. **Checks made of the user's own circuit, in the same job, say whether a result can be trusted, and see what the
   calibration does not.** The floor, the mirror, the sentinel, the rulers; the share kept r and its line at 0.293
   (paper 9); an 18-site dead run the calibration did not show (paper 5); scan-then-avoid widened a ring from 22 to
   40 usable sites (paper 6); against IBM's own calibration over 191 jobs, our mirror findings sit on its CZ column at
   2.29 x chance, while it marks no column for 291 of 721 of them (calibration comparison, 11-27). Essence: dividing
   by a measured share does not correct (paper 9); the t = 3 residue no ruler carries on fez (11-24 to 11-26).
3. **Every claim can be re-checked by anyone, including the failures.** Declarations locked in git before the data;
   sealed answers; raw counts; `reproduce.py` (98 entries); every failed prediction kept. Essence: 20 of 75
   predictions of 11-16 to 11-27 failed (all on paper 10's nights), plus the declared noise model, parity volumes and
   expectations that failed in papers 5 and 8.

## New analyses (the paper's own results; none done yet)

Each is computed from the committed records by a script in this folder, declared here before it is run (rule: the
question and the reading are written first; the script is run once on the records; the result is reported as it
comes).

- **A. The prediction ledger, paper 1 to 11-27.** Every declared prediction, one row each: date, paper, device,
  kind (direction, threshold, per-qubit, null), held / failed / not read, and the record. Questions: which kinds fail;
  whether failures cluster in new designs (first night of a design) or on repeats; how often a declared noise model
  held. Source: `prereg/`, every `results/*/README.md` "Against the declaration", papers 1 to 6's declaration
  tables. (Papers 1 to 4's pre-registrations live in psf-zero; read there.)
- **B. Paper 9's line, tested out of sample.** Paper 9 drew r >= 0.293 on 179 results assembled after the fact.
  Every result with an exact answer recorded after 2026-11-16 (the Ohm nights, the real-time nights' uncontrolled
  arms where a mean-square reading applies) is a new test. Declared reading: the line holds if, among the new results
  with r >= 0.293, the share that reads is at least the 160 / 166 of paper 9 minus its binomial 2 SE; and no result
  below 0.293 reads (true by construction; checked as a code test).
- **C. What the calibration sees and what it misses** (the 191-job comparison; done at the workplace on 11-27,
  `notes/calib_compare_2026-11-26/`), with the map's age and the day-to-day turnover; set beside papers 5 and 6's
  defects.
- **D. The same circuit on different days.** The daily record (11-05 to 11-16), the balanced pair (0.61-0.87 on two
  nights, paper 10), the ruler nights on fez (three nights, same copy) and kingston: how far a raw value moves day
  to day against its shot error. Declared reading: the day-to-day spread is reported against the within-job spread
  of copies (paper 11's rule 4).
- **E. The re-score census.** `python reproduce.py` over all 98 entries on one machine; the count SAME / DIFFERENT /
  FAILED, with the reasons for any not SAME (e.g. entries needing a psf-os branch).

## Sections (draft)

1. Introduction: the user's position (no map they can trust, no mitigation they can audit); the question; what is
   new here (A to E) and what comes from the series.
2. Methods common to the series: placement by formula (ring rule, translation, chain rule round failed elements);
   the checks (floor, mirror, sentinel, Clifford twin, rulers); the verdict words (READS, AGREES, the t width);
   declaration, sealing, re-scoring. One figure: one job, its parts.
3. Results I, what reads (claim 1): practice circuits, dual-unitary chains to N = 91, 3D lattices, utility
   observables, Fermi-Hubbard; with what did not read.
4. Results II, what the checks see (claim 2): r and its line, B out of sample; defects the calibration does not show
   (papers 5, 6) and C; the rulers inside the circuit (11-23 to 11-27, short; paper 12 is the full account).
5. Results III, control during the run (papers 10, 11): the ceiling and the rules for waits, in brief.
6. Results IV, the record (claim 3): A and E; D.
7. Discussion: what a user-side layer can and cannot do; where search would do better (paper 3, the 3D prototype at
   several times a router's cost, paper 5's untested level 3).
8. Limits: one device family; every answer classically computable (no advantage claimed); most results one night
   and one device; post hoc tables named as such; **the work was done by the owner with AI assistants (Claude), and
   the independent checks of 11-18 to 11-27 were made by a separate AI instance with separately written code, not by
   another human team.**
9. Records and code: notebook, psf-os, psf-zero; DOIs of papers 1 to 11.

## Titles (options)

1. What a User-Side Layer Can Know Without the Calibration Map: Declared Tests on IBM Heron Devices, 2026
2. No Map, No Mitigation, Declared Before the Data: What Raw Results on IBM Heavy-Hex Devices Can Be Trusted For
3. Reading Raw Quantum Results from the User's Side: Placement, Self-Checks and a Public Record of Failed Predictions

## Open before writing

- Papers 1 to 4 are compiler papers on models, not device tests of this layer: keep them as the origin (one
  paragraph and A's rows), or leave them out of the results? (Home's view: origin only.)
- Category for a later arXiv try: quant-ph, with cs.ET as cross-list; endorsement not in hand (2026-11-28 notes in
  the conversation; nothing here depends on it).
- Paper 12 stays as planned; this paper cites it once published.
