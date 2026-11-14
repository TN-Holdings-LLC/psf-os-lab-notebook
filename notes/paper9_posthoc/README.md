# Dividing by the kept share after the fact (desk, 2026-11-14, for paper 9 section 8)

Computed beside the results, never used for a verdict. `rescale.py` (output `rescale.txt`) asks what is left if raw
values are divided by a scale s: MSE / mean square becomes (rest + (r - s)^2) / s^2, so even s = r leaves rest / r^2.

- Oracle (s = r from the exact answer, not available to a user): 179 results, reads 160 -> 170 (11 gained, 1 lost);
  nine still do not read, including Hubbard at 6 steps (rest / r^2 = 1.0 to 11.2).
- pi/2 ruler of the same chain, depth and job (XX size test and repeat, 30 pi/4 circuits): 27 -> 28; better on
  marrakesh, worse on fez at 81 qubits (0.539 -> 0.723, 0.658 -> 1.429), where the ruler kept less than pi/4.
- Clifford twin (11-13, 6 pairs): no verdict changed; XX better, Hubbard at 4 and 6 steps worse.

A problem statement, not a method: a scale a user can measure is the share of another circuit, and no scale removes the
rest.
