# The wait footprint: definition and the circuits of 2026-11-16 to 2026-11-19 (workplace Claude, 2026-11-20)

Home's added instruction 3, item 2. psf-os branch after-2026-11-20: `psf_os/footprint.py` (`wait_footprint`,
`python -m psf_os.footprint CIRCUITS.qpy`) and `feedforward.build(..., footprint=True)` (each record carries
`wait_footprint`, the build report `footprint_max` / `footprint_total`; off by default, every build as before).

## Definition (what counts as "holding")

- A **wait** is a group of consecutive top-level measurements with any non-measurement operation after it (a
  mid-circuit read); measurements at the end are not waits. While a wait is read and the conditionals after it
  are decided, every other qubit of the circuit waits.
- At each wait the circuit is followed **noiselessly and exactly**, branching over every earlier mid-circuit outcome
  (statevector per branch; conditional blocks applied in the branches where they fire). For each waiting qubit (not
  read in this group, touched by the circuit) its one-qubit reduced state rho is formed in every branch.
- **Carrier**: a waiting qubit whose rho is not |0><0| or |1><1| in at least one branch, i.e. |rho_01| >= 1e-9 or
  min(rho_00, rho_11) >= 1e-9 (a superposition, or entangled with other qubits: it can lose its phase while it
  waits). The per-wait count is the number of carriers; `max` and `total` (carrier-waits) summarise the circuit.
- **Excited** (beside): the expected number of waiting qubits in |1>, the population rho_11 summed over the waiting
  qubits and averaged over the branches with their probabilities: what can decay while it waits.
- It reads the circuit only (logical qubits, as written). No noise model, no calibration number, no device record.
  Up to 14 active qubits (exact).

## The circuits of the declared tests (`table.py`, `table.txt`)

| circuit | carriers per wait | carrier-waits | excited-waits |
|---|---|---|---|
| teleport k = 1, 2 (11-16) | 1; 1, 1 | 1; 2 | 0.50; 1.50 |
| neuron L = 1: P0 (m 3) / P1 hold flipped / P2 read flipped / NF | 1, 1 / 1, 1 / 1, 1 / 1 | 2 / 2 / 2 / 1 | **1.68 / 0.32 / 0.32 / 0.79** |
| neuron L = 3: P0 / P1 / P2 / NF | up to 3 | 15 / 12 / 12 / 9 | **12.99 / 4.51 / 4.51 / 7.69** |
| IPE n = 2 .. 6 | 0 at every wait | 0 | 1, 2, 3, 4, 5 (the target in |1>) |
| textbook QPE | no wait (final measurements only) | 0 | 0 |
| repetition code, 16 CZ (11-19) and 10 CZ | 3 | 3 | 1.50 |
| repetition code, F6P and F6 (the encoding undone before the read) | 1 | 1 | 0.50 (no error), 2.50 (error on d0: the syndrome 1, 1 waits on d1, d2) |

Read beside, not judged: the 11-16 / 11-17 diagnosis (holding the likely value as |0>, P1, recovered 0.11-0.22) is
the excited count, 1.68 -> 0.32 at L = 1 and 12.99 -> 4.51 at L = 3, with the carriers unchanged; IPE keeps no
carrier at any wait (one ancilla, read at once) while the textbook circuit has no wait but holds n + 1 qubits in
superposition to the end; the repetition code's forms differ in carriers (3 against 1). Whether a device's loss
follows the carriers, the excitations or the CZ count is a declared test's question (`gpu/repcode4_night.py`); the
footprint itself only counts.
