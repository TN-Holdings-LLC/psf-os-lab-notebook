# Early measurement: finished outputs kept in classical bits (workplace prototype, 2026-11-17; desk only, not declared)

Owner: the 1950s were saved by a memory that keeps its contents; "早いほうが作って". A device with mid-circuit
measurements already has such a memory: the classical register. Tool: `early.py` (identity / build / ledger / score);
outputs `identity.json`, `ledger_early_vs_rd.json`. psf-os unchanged (feedforward-2026-11-16, 301ac01); the ledger is
`notes/timebudget_2026-11-17/ledger.py` (with the JIT schedule added this morning).

## The rule (exact)

The principle of deferred measurement read the other way: a qubit that from some point on is only a control can be
measured at that point, and every later controlled gate becomes a gate conditioned on the bit; every other measured
bit keeps its distribution. In the neuron chain the output of neuron j-1 is, after its neuron, only the control of
neuron j's input rotations. The early chain reads it (flipped, as the third design reads outputs) in the same layer as
its own last ancilla measurement, into an extra bit, and runs neuron j's first attempt in one single-bit conditional
(output 1). The retries need no condition on that bit: a try fails only if the rotation ran. No conditional is nested;
`feedforward.analyse` (IBM's rules, form "blocks") passes.

**Identity**: the joint distribution of all tries and the last output equals the third design's (exact branching
simulation, no sampling): total variation 0, 1.1e-15, 2.2e-15 at L = 1, 2, 3.

## Size and time budget (11-16 13:11 CET marrakesh record, rule C, the same line of qubits)

| L | third design CZ / conditionals | early CZ / conditionals | third design wait ASAP / JIT (q.us) | early wait ASAP / JIT | T JIT (us) third / early |
|---|---|---|---|---|---|
| 1 | 2 / 1 | 2 / 1 | 5.2 / 5.2 | 5.2 / 5.2 | 8.2 / 8.2 |
| 2 | 12 / 2 | 4 / 3 | 25.8 / 15.5 | 7.8 / 7.8 | 14.9 / 13.9 |
| 3 | 22 / 3 | 6 / 5 | 56.8 / 25.8 | 10.3 / 10.3 | 21.5 / 19.6 |
| 4 | 32 / 4 | 8 / 7 | 98.2 / 36.2 | 12.9 / 12.9 | 28.1 / 25.3 |
| 5 | 42 / 5 | 10 / 9 | 149.9 / 46.5 | 15.5 / 15.5 | 34.7 / 31.0 |

- CZ: 2 per neuron instead of 2 + 10 (L - 1): the controlled input rotations (2 CZ each, twice per try) become
  rotations conditioned on a bit (no CZ).
- Wait: 2.6 q.us per neuron (the output held flipped during its own ancilla's measurement, nothing else), a third of
  the third design's under JIT and a tenth of it under ASAP at L = 5. **Early's ASAP equals its JIT**: each neuron's
  qubits start only after the conditional on the previous output, so the wait no longer depends on the device's
  scheduler.
- Cost: more conditionals (2 per neuron after the first instead of 1) and the mid-circuit reads they wait for. With a
  hypothetical 1 us decision latency the early chain's T equals the third design's (40.0 against 39.7 us at L = 5) and
  its wait stays about half (33.5 against 60.5).

## The off arm and the ceiling

The off arm given to the build is the third design's off arm (no retries, coherent input rotations, the same qubits),
widened to the same bits (earlier outputs read at the end into the extra bits). So the compound prototype's ceiling
c(L) applies unchanged and the early chain can stand in T2's place: the dry run (noiseless, Clifford sentinel) reads
g = +0.094 / +0.163 / +0.202 / +0.224 / +0.232, every L beyond the ceiling, slope +0.037 (2 SE 0.004). 19 circuits,
24.2 s by the model (the same as T2).

## What it does not say

- Fewer CZ and less waiting are counts, not a device result; a declared test (the early chain against the third
  design, the same night, the same line) is what would show it.
- The off arm keeps the controlled rotations (a fair "without control" for the ceiling); the early chain's own reads
  are real-time decisions, so it stays on the real-time side of the ceiling argument.
- The decision latency is not in our records; the comparison is given at 0 and at a hypothetical 1 us.
- Next: reuse the two qubits for every neuron (a conditional X resets each read qubit), so the chain needs 2 qubits
  for any L, as iterative phase estimation does.

## Reproduce

```
python notes/early_2026-11-17/early.py identity
python notes/early_2026-11-17/early.py build DEV OUT [--dry-clifford-sentinel]
python gpu/compound_night.py build DEV RD_OUT
python notes/early_2026-11-17/early.py ledger OUT RD_OUT
python -c "from psf_os import feedforward as F; F.run_local('OUT')"; python notes/early_2026-11-17/early.py score OUT
```
DEV = results/rus-neuron3-2026-11-16/fetch_in/ibm_marrakesh/dev.
