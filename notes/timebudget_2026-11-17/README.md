# Time-budget ledger: where a feed-forward circuit spends its waits (workplace prototype, 2026-11-17; desk only, not declared)

Owner: "成功のカギは時間予算の圧倒的な削減？ … OSに組み込んでしまう？" then "プロトタイプ作って". Tool: `ledger.py`
(reads a `psf_os.feedforward.build` output; psf-os unchanged). No device error number is used: the ledger counts the
circuit's shape, with gate lengths from Qiskit's FakeMarrakesh snapshot as illustration (sx / x 36 ns, cz 68 ns,
measure 2.584 us; the psf-os device record keeps no lengths). The decision latency of a conditional is not in any
record we keep: it is a parameter (0 below unless stated; 0 makes the ledger a lower bound).

## What it counts

- `meas depth`: mid-circuit measurements in a row on the longest dependency path (waits that cannot overlap).
- `dec depth`: conditionals in a row (each may cost a decision latency; IBM tests one bit per conditional, so a parity
  stacks one conditional per bit).
- `wait`: idle time of qubits carrying information that lies under another qubit's measurement or a decision latency,
  qubit-microseconds. This is the exposure the 2026-11-16 diagnostics point at (|1> lost while waiting).
- Each under ASAP (gates as early as possible) and ALAP (qubits prepared just in time), for the circuit as built and
  with its barriers removed. The device's own schedule is not known to us; these cells show what a scheduling choice
  of the OS could save without changing what the circuit computes.

Check on a hand-made circuit (prepare q1, measure q0, conditional, CZ): ASAP wait 2.584 q.us (q1 under q0's
measurement), ALAP 0; with a 1 us latency the conditional's own qubit waits 1 us. As expected.

## Tonight's jobs and the teleport comparison (11-16 13:11 CET marrakesh record, latency 0)

Neuron chain, third design (T2), ff arm, wait in q.us:

| L | meas depth | T (us) | as built ASAP | as built ALAP | no barriers ASAP | no barriers ALAP |
|---|---|---|---|---|---|---|
| 1 | 1 | 8.3 | 5.2 | 5.2 | 2.6 | 2.5 |
| 2 | 2 | 14.9 | 25.8 | 18.1 | 13.8 | 12.6 |
| 3 | 3 | 21.5 | 56.9 | 36.1 | 31.7 | 27.9 |
| 4 | 4 | 28.1 | 98.2 | 59.3 | 56.0 | 48.4 |
| 5 | 5 | 34.7 | 149.9 | 87.7 | 87.0 | 74.0 |

The wait grows about as L^2 (each step waits once, and more qubits carry information at each wait). Scheduling alone
(just in time, barriers removed) halves it at L = 5; it does not change the L^2 shape.

Teleport over the same distance (T3-B and the 11-16 sequential test), ff arm:

| distance | sequential: meas depth / T / wait ASAP / wait ALAP | constant depth: meas depth / T / wait ASAP / wait ALAP |
|---|---|---|
| 4 | 4 / 13.6 / 25.8 / 10.3 | 1 / 5.5 / 2.6 / 2.6 |
| 8 | 8 / 24.5 / 93.0 / 20.7 | 1 / 5.6 / 2.6 / 2.9 |
| 12 | 12 / 35.3 / 201.6 / 31.0 | 1 / 5.7 / 2.6 / 3.3 |
| 16 | 16 / 46.2 / 351.4 / 41.3 | 1 / 5.7 / 2.6 / 3.8 |

At distance 16 the constant-depth form waits about 1/100 of the sequential form scheduled ASAP and about 1/11 of it
scheduled just in time. This is the "overwhelming" reduction: it comes from the structure (one layer of measurements),
not from the schedule. Its weak point is the conditional stack: with a 1 us decision latency (hypothetical) lr8's 16
conditionals in a row take T to 21.7 us and its ALAP wait to 92.9 q.us (seq16: 62.2 us, 57.3); a parity test in one
conditional would remove it.

Iterative phase estimation (T3-A): 1 (n = 2) and 2 (n = 3) waits in a row, T 5.3-8.6 us, wait 0-5.1 q.us ASAP, but
ALAP is worse here (5.1-7.7): the target holds |1> through every round, and moving the ancilla's gates late lengthens
its wait. Just in time is not always better: the OS should compute both and take the smaller.

## What this says about the owner's question

- What can be cut overwhelmingly is the number of waits in a row and the qubits exposed during them (structure:
  constant-depth forms, measurements in one layer), by 10-100x in the teleport example; the schedule gives up to about
  8x (sequential teleport, ASAP to ALAP) and 2x (the neuron chain); the length of one measurement cannot be cut.
- The neuron chain's L^2 growth is the reason compounding flattens: each step adds a wait for every qubit already
  carrying information. A chain that parks finished outputs (held flipped, or measured early when the design allows)
  turns that into a linear growth.

## Into the OS (proposal; nothing changed in psf-os)

1. The ledger in `feedforward.build`'s report, beside CZ and depth (counts from the circuit; lengths illustrative and
   labelled; no error numbers).
2. A schedule pass: compute ASAP and ALAP (and, where barriers are only there to pin a schedule, the barrier-free
   ones), pin the one with the smaller wait by placing barriers, check the identity noiselessly.
3. Measurement layering: move mid-circuit measurements into one layer where the dependencies allow.
4. A rule for "measure or write coherently" per step: one wait against the CZ that replace it, counts only, fixed in
   the declaration.
Each pass changes the schedule, so its use on a device is a declared condition and its effect a declared test.

## Reproduce

```
python gpu/coh_night.py build DEV OUT1; python gpu/compound_night.py build DEV OUT2; python gpu/apps_night.py build DEV OUT3
python notes/timebudget_2026-11-17/seqcmp.py DEV OUT4
python notes/timebudget_2026-11-17/ledger.py OUT1 OUT2 OUT3 OUT4 [--latency-us 1] [--json FILE]
```
DEV = results/rus-neuron3-2026-11-16/fetch_in/ibm_marrakesh/dev. Recorded: `ledger_latency0us.json`,
`ledger_latency1us.json`.
