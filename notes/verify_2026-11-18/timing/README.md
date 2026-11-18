# Part 3: decision timing re-scored independently (home VS Claude, 2026-11-18)

verify_timing.py (qiskit to read the circuits, numpy; no home tool) -> verify_timing.txt / .json. Clocks read from the
ruler circuits (physical qubits 0 and 8, the record's sites 0 and 8); ruler waits from the delays in the R circuits.

- Declared reading: every slope and SE equal to home's tmA/timing_scores.json (largest difference 4.4e-16 us).
- T-1 NOT RESOLVED (+0.317 us, 2 SE 0.417); T-2 IN PARALLEL (0.961, 2 SE 0.192); T-3 IN PARALLEL (1.003, 2 SE 0.221).
- Robustness (three other ruler readings: one tau line, a saturating exponential, piecewise linear on raw loss):
  s_C - s_M +0.302 to +0.325 us (2 SE 0.35-0.43), s_D / s_C 0.97-1.01, s_DK / s_K 0.96-1.05; the verdicts are the same
  in all four.
