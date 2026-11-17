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

## Schedule pass (workplace VS Claude, 2026-11-17; the request 17e; desk only, not declared)

Tool: `schedule_pass.py` (reads the same build outputs; psf-os unchanged, at 301ac01). Recorded:
`schedule_pass_latency0us.txt / .json` and `schedule_pass_latency1us.txt / .json`, over the 58 ff and off circuits of
the four builds above (coh_night, compound_night, apps_night, seqcmp; 11-16 13:11 CET marrakesh record). The lengths
are the ledger's FakeMarrakesh medians, which are illustrative. No device error number is used.

### What it does

1. **Four ledger cells.** It computes ASAP and ALAP, each as built and with the barriers removed.
   - A barrier-free cell is a candidate only when the barriers pin a schedule and nothing else.
   - Barriers that stand between two one-qubit gates on one qubit belong to the design. In the third neuron design
     they are the outputs' X before and after each ancilla measurement: the outputs are held flipped during it, and
     the X pairs are kept from cancelling in the off arm. Once compiled, those X are partly fused into the
     neighbouring gates.
   - The rd items keep their barriers. No other circuit here has barriers.
2. **The choice.** It chooses the smallest wait.
3. **Pinning.** It writes the chosen schedule into the circuit: the instructions in start order, with barriers that
   hold each instruction at the edge of another instruction. An as-soon-as-possible executor cannot then start it
   earlier, and an as-late-as-possible executor cannot end it later.
4. **The checks:**
   - Identity, noiselessly: `coherent.branch_distribution` gives a total variation of at most 1e-12 where qubits plus
     measurements are at most 24. That covers 50 of 58 circuits. The sequential teleport at distance 12 and 16 and lr6
     / lr8 do not fit in memory.
   - Structural identity for every circuit: barriers left out, the same operations in the same order on every qubit
     and clbit.
   - The pinned circuit's ledger, recounted under both executors.
5. **Beside:** the smallest wait that a pinned circuit guarantees under either executor. This comes from every allowed
   cell, pinned exactly or "snapped": an instruction that no edge can hold is held at the next edge after it instead.

### Results (latency 0; wait in qubit-microseconds)

- **Identity:** OK for all 58 (TVD at most 9e-16 where simulated; the same DAG everywhere).

| item | as built ASAP | as built ALAP | chosen | pinned (both executors) | guaranteed |
|---|---|---|---|---|---|
| coh1 (T1) | 0.036 | 0.000 | ALAP 0.000 | yes | 0.000 |
| rd1 (T1, T2) | 5.168 | 5.168 | ASAP 5.168 | yes | 5.168 |
| rd2 (T2) | 25.840 | 18.052 | ALAP 18.052 | no (ASAP executor 20.672) | 18.088 (snapped) |
| rd3 | 56.848 | 36.104 | ALAP 36.104 | no (41.344) | 36.176 |
| rd4 | 98.192 | 59.324 | ALAP 59.324 | no (67.184) | 59.432 |
| rd5 | 149.872 | 87.712 | ALAP 87.712 | no (98.192) | 87.856 |
| ipe n 2 (T3-A, phases 1-3) | 2.548-2.584 | 5.132 | ASAP | phase 2 yes; 1, 3 snapped | 2.548-2.584 |
| ipe n 3 (phases 1-7) | 5.096-5.132 | 5.132-7.716 | ASAP | snapped | 5.096-5.132 |
| lr2 / lr4 (T3-B) | 2.584 | 2.620 / 2.872 | ASAP 2.584 | yes | 2.584 |
| seq4 / 8 / 12 / 16 | 25.8 / 93.0 / 201.6 / 351.4 | 10.3 / 20.7 / 31.0 / 41.3 | ALAP | yes | as chosen |

The off arms follow their ff arms. At latency 0, 32 of 58 circuits are pinned exactly, and 50 of 58 are guaranteed
at the chosen value. At latency 1 us it is 28 and 50. There the sequential teleport is held by snapping at its ALAP
value, and the decision intervals give the phase-estimation items their edges.

### What could not be pinned, and why

- **rd2 to rd5 (ff and off arms):** they cannot be pinned exactly.
  - ALAP starts parts of each later neuron's preparation before the previous measurement ends, at a time where no
    other instruction starts or ends (4 / 7 / 9 / 11 such instructions for L = 2 / 3 / 4 / 5). A barrier only holds an instruction at another instruction's edge, so an
    ASAP executor moves the preparation into the measurement (+2.6 q.us per neuron).
  - Snapping holds it at the measurement's end instead. That guarantees the ALAP value plus 0.036 to 0.144 q.us (at
    most 0.2 %), at a T longer by 0.1 to 0.25 us.
- **Phase estimation (before the zero-length-first order):** an ALAP executor pushed the target's last one-qubit gate
  (the target is never measured) under the final measurement, doubling its wait.
  - Emitting zero-length instructions first at equal times, plus snapping, holds it.
  - All 28 apps circuits are now guaranteed at the chosen value.
- **The barrier-free cells of rd are not used.** Without the barriers, rd5's ALAP wait would be 74.0 (ff) and 22.6
  (off), but the outputs would no longer be held flipped during the waits. That is a design change, not a schedule.

### What this adds to the proposal "a schedule pass in the OS"

- **A pass needs both executors.** ASAP pinned in the circuit is exact only when the device starts instructions as soon
  as possible. What the device's own scheduler does is not in any record we keep.
- **Barriers fix order, not time.** Sub-gate offsets need snapping, which costs a little time and almost no wait, or
  explicit delays. Delays would count as busy time in the ledger, so they need a ledger change, and they are not
  proposed here.
- **Using the pass on a device is a declared condition** (as in the README above).

## Correction (2026-11-17, later the same morning): a third schedule, JIT, changes two readings above

ALAP pushes not only a qubit's preparation late but also its last measurement (when no later conditional reads it),
so ALAP overstates the wait of qubits that finish early. The ledger now also computes **JIT**: ASAP, then every gate
other than measurements and conditionals pushed as late as the next operation on its qubits allows (prepared just in
time, read as early as possible). JIT is the smallest or within 0.1 q.us of it in every item counted here.

- **Neuron chain**: under JIT the wait grows **linearly**, not as L^2: 5.2 / 15.5 / 25.8 / 36.2 / 46.5 q.us as built
  (L = 1 .. 5), 2.5 / 8.2 / 13.9 / 19.6 / 25.3 without barriers. The L^2 growth above belongs to ASAP (fresh qubits
  prepared at the start, waiting through every earlier step) and is partly kept by ALAP. Withdrawn: "scheduling halves
  it at L = 5; it does not change the L^2 shape" (JIT cuts 149.9 to 46.5, a factor 3.2, and makes it linear).
- **Constant-depth teleport with a 1 us decision latency**: JIT lr8 18.6 q.us against seq16 57.3, not "92.9 against
  57.3". Withdrawn: that the conditional stack makes the constant-depth form wait more than the sequential one; it
  makes it wait more than at latency 0 (2.6), still 3x less than the sequential form.
- Iterative phase estimation: JIT 5.2 (ASAP 5.1, ALAP 7.7).

The device's own schedule is not known to us; that it matters this much is the reason to pin one (the schedule pass).
