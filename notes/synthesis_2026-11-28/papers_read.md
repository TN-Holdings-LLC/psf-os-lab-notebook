# Papers 1 to 11, read again from the start (home, 2026-11-28)

The owner's request of 2026-11-28: read every paper again from paper 1 and build a comprehensive paper, kept apart
from paper 12's plan (`notes/paper12/`, unchanged). Each digest below is taken from the paper's abstract, limits and
conclusion as published (the PDF named), with its numbers copied, not re-derived. "Failed or open" lists what the
paper itself reports as failed, withdrawn or open.

Sources read: papers 1 and 2 `papers_v2/*.pdf` (version 2, 2026-09-26); papers 3, 4 (v1.3) and 5 (v1.1) of
2026-10-31; paper 6 the draft of 2026-11-02 with appendix A, checked against its Zenodo input (v1.0; the final
numbers below are the Zenodo input's where the two differ); papers 7 to 11 `notes/paperN/paperN_v1.pdf` (paper 10:
`notes/paper10_ff/paper10_v1.pdf`). DOIs as in psf-zero's README (8769aa5) and psf-os's README (42617f4).

## Act I: the compiler (papers 1 to 4, PSF-Zero)

**Paper 1, Ordering Sensitivity in Subgraph-Isomorphism Layout Search (v2, 10.5281/zenodo.22977930).**
- Qiskit's VF2Layout has a sharp failure region on interaction graphs that saturate the device's maximum matching:
  median time 34.1 ms to 9,236 ms (x271), ending in "no solution" where one exists.
- A fixed-order `rustworkx.vf2_mapping` call found an embedding in 26 of 26 at a median 0.0292 ms.
- Failed or open: no graph feature explains more than 4.5 % of the outcome variance; isomorphic instances diverge on
  placement alone; which instances fail is not predicted. Pre-registered.

**Paper 2, PSF-Zero: An Analytic Two-Qubit Gate Synthesizer ... (v2, 10.5281/zenodo.22978090).**
- KAK synthesis in Rust: fidelity 1.000000000000 against Qiskit's output at small scale; 7.0-9.3x faster than
  Qiskit's optimization_level 3 synthesis path; layout search 26 of 26 saturated instances (from 0 of 26 before a
  defect was fixed).
- Failed or open: a 34-54x drop in timing variance between two sessions, cause not found; two of its own earlier
  reports corrected; (v2) a defect inherited from Qiskit's CX-basis synthesis, found and fixed.

**Paper 3, When a Quantum Compiler Looks Like a Better Learner (v1.3, 10.5281/zenodo.23826596).**
- Four confounds can each name a winner without any difference in learning (answer at the untrained start; readout
  offset; output scale against fixed shots; the twin's scale off by up to 2.3x).
- With the confounds controlled, the zipper (336 CZ, 11.7 µs) and Qiskit (506 CZ, 48.2 µs) gave classifiers the
  declared tests could not tell apart. A classifier without training on ibm_kingston (30 October): the placement
  that kept more signal gave the more accurate classifier (0.810 against 0.715, McNemar p = 0.007).
- Failed or open: formula placement did not beat the search; one preliminary job's inversion has no known cause.

**Paper 4, Folding a Ring onto Heavy-Hex (v1.3, 10.5281/zenodo.23826764).**
- Three formula schedules (zipper, holes, pendants) with gate counts; the pendant count proved least in a stated
  routing model. Against Qiskit level 2 on the same twin the rule kept 0.61-0.82 of the signal against -0.05-0.64.
- Device: the pendant schedule kept what its day's twin predicted (0.90 +- 0.12 against 0.77; 0.50 +- 0.10 against
  0.59), two jobs of 7 s.
- Failed or open: the twin of a 13-day-old snapshot overstated the lead (1.5-8.2x against 1.07-1.28x on a real
  day's twin); error-product estimates did not rank the schedules; "count-optimal is not signal-optimal".

## Act II: placement without the map, and the readable depth (papers 5 and 6)

**Paper 5, Readable Depth Without the Calibration Map (v1.1, 10.5281/zenodo.23827536).**
- Map-free placement (coupling graph, basis, failed elements only). The rule kept more of a conserved charge than the
  zipper and blind Qiskit in 24 of 24 comparisons; readable depth L* 56-57 steps (marrakesh) and 81-90 (kingston)
  against 15-26. Second day: 71 wins, 11 ties, no loss in 144 comparisons (62 not judged).
- A run of 18 sites on ibm_kingston's n = 40 ring near random or inverted, the same in three runs over three hours,
  while the calibration showed nothing; gate twirling turned the inverted part random (the cause is on the device).
- Failed or open: the declared noise model did not hold (one depolarizing rate did not describe the decay); the
  zipper's penalty (3.5-3.7x) exceeded the 2.2-2.4 its gates predict; the first-day penalty did not carry over;
  the declared parity volumes were too optimistic. Qiskit level 3 and commuting-gate routers not tested.

**Paper 6, What Sets the Readable Depth of a Placed Ring ... (v1.0, 10.5281/zenodo.23883938).**
- A self-checking layer: scan by mirror echo, a dated registry (listed after two jobs, expired after seven days),
  place around it, frame-flip repair for mirror circuits, sentinel.
- Width: kingston n = 40, 22 to 40 usable sites (three days in v1.0); WIDER in 6 of 6 declared comparisons; fez and
  marrakesh widened too. Accuracy on fully usable rings: +0.040 and +0.045 in mean site signal, all of it on the
  replaced qubits.
- Failed or open: at n = 72 the avoiding ring fell about two layers short of the n = 20 depth, cause unknown; repair
  weak at D = 24; the registry's thresholds are chosen, not fitted.

## Act III: the operating layer through the user's entrance (papers 7 to 9, psf-os)

**Paper 7, Exact Answers, No Map, No Mitigation (v1, 10.5281/zenodo.24046673).**
- 22 practice circuits written in plain Qiskit, answers sealed: all READ on both devices; 19 and 18 AGREE. IBM's
  dual-unitary chain at N = 51 and 71: decay rates within 0.0045 and 0.0017 of cos 2h; every depth to t = 24 (1,715
  CZ) readable. One script re-scores all 13 device results to the same numbers.
- An absolute criterion |M - M_exact| <= c is biased both ways, so retention is printed beside every verdict.
- Failed or open: a correction from the job's own controls reduced the error but did not agree across problems; an
  outside comparison not in our favour (P6 on fez against IBM's tutorial); the queue rule chose a device with a low
  floor once.

**Paper 8, Readable Quantum Dynamics Without Error Mitigation (v1.0, 10.5281/zenodo.24136512).**
- Dual-unitary chain at N = 91 on ibm_marrakesh: rates within 0.0037 of cos 2h, every depth to t = 24 (2,205 CZ).
  3D: kicked Ising on 4 x 4 x 3 read at every angle and depth; Heisenberg XXX on 4 x 2 x 2 read. Schwinger pair
  creation read in 16 of 18. 23 of 23 device results re-score the same.
- The main measure changed, from retention to a normalised per-site error, because noise that slows the dynamics can
  raise retention.
- Failed or open: a light-cone test failed as predicted (every front late); a 46 % CZ cut came farther from the
  answer on one lattice; a twirled second mirror could not resolve a planted 0.02; a coherent-CZ hypothesis
  withdrawn after a computing error; three mirrors fail at t >= 2.

**Paper 9, What Makes Raw Quantum Dynamics Readable? (v1, 10.5281/zenodo.24278888).**
- MSE / e^2 = (1 - r)^2 + rest; r < 0.293 means "does not read" by construction. Across 179 results: 160 of the 166
  with r >= 0.293 read. Utility observables read raw to 8 steps; Fermi-Hubbard at U = 4 read from 40 to 120 qubits
  at 4 Trotter steps, at neither size at 6.
- r is not set by CZ depth alone: at equal depth an 81-qubit XX chain kept up to 0.18 less than a 33-qubit one, the
  loss opening where the longer chain continues.
- Failed or open: the yardstick table was assembled after the results (20 cells tested under a declaration);
  dividing by a measured share cannot undo what is not a shrink and made some results worse.

## Act IV: real-time control (papers 10 and 11)

**Paper 10, Decisions No Correction of the Uncontrolled Circuit Can Reach (v1, 10.5281/zenodo.24367001).**
- The correction ceiling c. RUS neuron chains crossed it with a margin growing per neuron (+0.024 fez; +0.031 and
  +0.053 marrakesh); iterative phase estimation crossed it (0.903 against 0.471 at n = 4). Holding the likely value
  as |0> during waits recovered 0.11-0.22. A prescription loop ran unattended and chose differently after a
  recalibration.
- 57 declared predictions: 37 held, 20 failed, every failure reported.
- Failed or open: packing two conditional items costs the first (0.20 with ten items); a delay did not remove it; no
  decision latency above about 0.4 µs resolved; what the device keeps varies by night (0.61-0.87).

**Paper 11, Where a Qubit Waits (v1, 10.5281/zenodo.24496368).**
- Four rules from 11 declared predictions, all held: park a waiting |1> as |0> (+0.029 to +0.052 on three devices);
  fewer superposed qubits and fewer CZ during a wait keep more; two conditional items cost the first 0.057; the same
  circuits drift between jobs seconds apart while copies inside one job agree. IPE parked stayed beyond its ceiling
  to n = 8 (0.424 against 0.201).
- Over the series to 11-22: 68 declared, 20 failed, all on paper 10's nights.
- psf-os parks by default (0.3.0, 0.3.1) and checks the parking in the circuit as sent (0.3.3).

## After paper 11 (records, not yet in a paper; paper 12's material)

- Ohm window and ruler nights, 11-23 to 11-27 (`results/ohm-window-night-2026-11-23`, `results/ohm-ruler*-night-*`):
  rulers carried inside the circuit; (de) AGREES in four of six cells at t >= 3 on fez (11-26) and five of six on
  kingston (11-27); a positive residue at t = 3 on fez in every ruler, on kingston in A0 only for (de).
- Calibration comparison (`notes/calib_compare_2026-11-26/result_2026-11-27.md`): 191 jobs; our mirror_low findings
  sit on IBM's CZ column at 2.29 x chance; IBM marks no column for 291 of 721 mirror_low findings; fez 104 found 68
  times with no IBM mark.
- Predictions over the nights of 11-16 to 11-27: 75 declared; 54 held, 20 failed, 1 not read
  (`results/ohm-ruler5-night-2026-11-27/README.md`).
