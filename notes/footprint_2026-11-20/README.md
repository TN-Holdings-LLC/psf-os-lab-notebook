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
| IPE n = 2 .. 6 | 0 at every wait | 0 | 1, 2, 3, 4, 5 (the target in \|1>) |
| textbook QPE | no wait (final measurements only) | 0 | 0 |
| repetition code, 16 CZ (11-19) and 10 CZ | 3 | 3 | 1.50 |
| repetition code, F6P and F6 (the encoding undone before the read) | 1 | 1 | 0.50 (no error), 2.50 (error on d0: the syndrome 1, 1 waits on d1, d2) |

Read beside, not judged: the 11-16 / 11-17 diagnosis (holding the likely value as |0>, P1, recovered 0.11-0.22) is
the excited count, 1.68 -> 0.32 at L = 1 and 12.99 -> 4.51 at L = 3, with the carriers unchanged; IPE keeps no
carrier at any wait (one ancilla, read at once) while the textbook circuit has no wait but holds n + 1 qubits in
superposition to the end; the repetition code's forms differ in carriers (3 against 1). Whether a device's loss
follows the carriers, the excitations or the CZ count is a declared test's question (`gpu/repcode4_night.py`); the
footprint itself only counts.

## As sent: the compiled circuit, over the whole wait (added the same day, after the workplace VS's check)

The workplace VS found that the count above, on the circuit as written, can be smaller than on the circuit as sent:
the compiler merges one-qubit gates across a wait (IPE: the target's return to |1> and the next round's preparation
become one rotation, so the target waits in a superposition). Following the VS's opinion, psf-os after-2026-11-20
now counts:

- the wait unit and the branches as above (a measurement group; a carrier in the worst branch);
- **as sent first**: `build(..., footprint=True)` records each arm compiled, with `wait_footprint(qc, span=True)`:
  a waiting qubit counts if it is not in a basis state at the read or after any instruction up to the end of the
  conditionals that follow (the whole wait); the circuit as written beside (`written`);
- the number of conditionals as its own column, not folded into the footprint.

`sent.py` / `sent.txt` (the 2026-11-19 marrakesh record, rule C):

| circuit | written (span) max / total | sent | sent with `fence=True` |
|---|---|---|---|
| IPE n = 2 .. 6 | 0 / 0 | 1 / n (one carrier at every wait) | 0 / 0 (CZ the same, depth +2 to +3) |
| neuron P0 m 3, L = 2 / 3 | 3 / 9; 4 / 19 | 3 / 10; 5 / 24 | 2 / 6; 3 / 12 |
| neuron P1, P2 m 2, L = 3 | 4 / 16 | 5 / 24 | 4 / 16 |
| teleport k = 2 | 1 / 2 | 2 / 3 | 1 / 2 |
| repetition code, every form and error | 3 or 1 | as written | as written (F10 depth +3) |

`fence` (psf-os `footprint.fence_waits`, used by `build(fence=True)`; off by default): a barrier on every qubit
before each mid-circuit read and after each run of conditionals. It does not change the circuit's action.

What the fence costs and what does better (`notes/park_2026-11-20/`, illustrative noise only): with the fence the
IPE target waits in |1>: no carrier, but fully excited (exposed to decay). Under damping per read (noise a) the fence
alone loses (0.948 -> 0.918 at n = 4); under dephasing per conditional (noise c) it gains (0.731 -> 0.754 fenced at the reads, 0.790 at every wait).
Parking the target in |0> for the wait (X before, X after, inside the fence) removes both and is the best in both
noises (0.959 and 0.785). The principle "do not spread the state while a conditional waits" reads, as sent: no
carrier and nothing excited, i.e. waiting qubits in |0>.
