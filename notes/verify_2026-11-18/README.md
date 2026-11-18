# Independent check of the night of 2026-11-18 (home VS Claude, 2026-11-18; desk only)

Home Claude's instruction "今夜の結果の独立検証" on the notebook at db78ee19 (psf-os 0f57c76). Every number here is
read from the recorded `job/raw_counts.json`, `job/manifest.json` and `runs/*.qpy` by code written for this check with
qiskit and numpy only (`vlib.py`); none of home Claude's scorers (`gpu/*_night.py` score, `psf_os.feedforward.cards`)
is imported. Noiseless values, exact values and ceilings are computed here from the recorded circuits (exact
branching over every mid-circuit measurement), not read from `ideal7.json` or any table. Output bits and physical
qubits are read from the circuits and compared with the records afterwards.

| part | files | result |
|---|---|---|
| 1 balanced repeat | `v1_balanced.py`, `out/v1_balanced.txt / .json` | every number equal to home's (largest difference 6.4e-15) |
| 2 parallel (P-A, P-B) | `v2_parallel.py`, `out/v2_parallel.txt / .json` | every number equal; bits and qubits as recorded |
| 3 decision timing | `timing/` | every slope equal (4.4e-16 us); verdicts the same under four ruler readings |
| 4 compounding OS | `v4_os2.py`, `out/v4_os2.txt / .json` | rule by hand: P1 at L = 1, 2, 3; round 1 g and verdicts equal; R4 keep, fixed point |
| 5 sentinel bytes | `sentinel/` | here byte-identical to the owner PC's build; the difference lies with home Claude's environment |

## 1. Balanced repeat

- Output bits read from the circuits (2, 4, 6, 8, 10) and chains (0..2L-1) equal the records. exact (statevector of
  the ideal chain) equals the closed form; the off arms' noiseless values are the same for rd and nf (0.7943 / 0.6308 /
  0.5010 / 0.3980 / 0.3161), so c(L) is the same from either frame (0.1429 / 0.2473 / 0.3219 / 0.3733 / 0.4066).
- rd, nf, pooled P, noiseless pool, c(L), g, 2 SE, verdicts and the slope (+0.0528, 2 SE 0.0033, COMPOUNDS) equal home's.
- Against 2026-11-17 (same chain): pooled -0.1657 / -0.1780 / -0.1235 / -0.0940 / -0.0934, rd -0.1492 / -0.1920 /
  -0.1370 / -0.1138 / -0.0935, nf -0.1822 / -0.1640 / -0.1100 / -0.0742 / -0.0933. Home's README has rd L 2 -0.193, nf
  L 1 -0.183 and nf L 4 -0.075: 0.001 from these (the third decimal; home's other entries agree when rounded).

## 2. Parallel

- Packed circuits were cut into items from their instructions alone (qubits and bits joined by any instruction); 10
  parts in P-A's bundle, 2 in each P-B bundle, no barrier joining two parts. Each part's qubits, bits and output bit
  equal the record's table (P-A: ord1..ord5, oea1..oea5; P-B: b1a..b3b).
- P-A: all ten single and packed off values, repeats, noiseless values, d_off and 2 SE equal home's; mean d_off
  +0.0012 (2 SE 0.0066), SAME WITHIN ERROR.
- P-B: A is on physical qubits [0, 1, 2, 3] (output bit 4 on qubit 3), B on [5, 6, 7, 8] (output bit 9 on qubit 8),
  read from the circuits, as recorded. b1a -0.0147, b2a -0.0603, b2b +0.0120, b3a -0.0620, b3b +0.0035; B1 -0.0147
  (2 SE 0.0222) SAME, B2 -0.0241 (0.0152) LESS, B3 -0.0292 (0.0152) LESS: equal to home's.
- **"Only the first item (A) loses 0.06" is not a misreading.** Reading A with B's bit layout (and B with A's) would
  give 0.7015 / 0.5052, i.e. the swap would move the loss to B; the bits are read the right way round. Per bit, A's
  loss sits entirely on its output bit (P(bit 1) 0.434 -> 0.495 in B2, 0.434 -> 0.496 in B3, +0.06, 2 SE 0.022), while
  its four try bits do not move (|change| <= 0.015, within 2 SE) and every bit of B stays within 2 SE.
- Beside: in the off arms (no conditionals, packed against sa / sb's off arms) B2's A does not move (every bit within
  2 SE) while two of B2's B try bits drop by 0.025 and 0.031 (2 SE 0.021); B3's A output bit moves the other way
  (0.434 -> 0.388, -0.046, 2 SE 0.022) and B3's B stays within 2 SE. B3's off arm differs from B2's only by B's delay.

## 3, 5

See `timing/README.md` and `sentinel/README.md`.

## 4. Compounding OS

- Dc (control and target read from the circuits: q1 / q2 at A, q3 / q4 at B): D_late_nb +0.0660 (2 SE 0.0116) and
  +0.0755 (0.0114), both losses -> rule 1 holds. Dw: D_cond +0.0117 (0.0145), +0.0025 (0.0136), no loss. Dr: q1 gap
  -0.0128 (0.0087), q3 +0.0022 (0.0035), q5 +0.0030 (0.0057), none a loss -> P1 at L = 1, 2, 3 (rule 2 gives P2 nowhere),
  as RULE1.json.
- Round 1: P 0.8403 / 0.7288 / 0.6400, P0 0.8080 / 0.7033 / 0.5847, g +0.0323 / +0.0255 / +0.0553 (2 SE 0.0170 / 0.0202
  / 0.0218), no overshoot, PRESCRIPTION HELPS at every L; output bits as recorded; G_1 0.0377.
- Round 2 by R1-R4: no overshoot (not R1), no +B (not R2), one round only (not R3) -> R4 keep at every L; every L keeps,
  none overshoots, none NOT SHOWN: the stop at a fixed point after round 1, as `stop.json`.
