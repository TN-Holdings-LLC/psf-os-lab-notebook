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
- The two-qubit form (next section) was built the same morning.

## Two qubits for any L (`chain_reuse`, items eb{L}, `build --reuse`)

After neuron j has been read, each read qubit is set back to |0> by an X conditioned on its own bit (the output on
e_j, the ancilla on its last try's bit; two single-bit conditionals, gates only), and neuron j + 1 runs on the same two
qubits, as iterative phase estimation does. Identity against the third design: total variation 0, 1.1e-15, 2.2e-15 at
L = 1, 2, 3; IBM's rules pass.

| L | qubits | CZ | conditionals | wait JIT, latency 0 / 1 us (q.us) | T JIT, latency 0 / 1 us |
|---|---|---|---|---|---|
| 1 | 2 | 2 | 1 | 5.2 / 7.2 | 8.2 / 9.2 |
| 3 | 2 | 6 | 9 | 10.3 / 24.3 | 19.7 / 26.7 |
| 5 | 2 | 10 | 17 | 15.5 / 41.5 | 31.2 / 44.2 |

(third design at L = 5: 10 qubits, 42 CZ, 5 conditionals, wait 46.5 / 60.5, T 34.7 / 39.7; the early chain: 10
qubits, 10 CZ, 9 conditionals, wait 15.5 / 33.5.) At latency 0 the two-qubit chain waits as little as the early chain;
its price is two resets per neuron, which a decision latency makes visible. What it buys: the chain sits on one pair of
qubits (the best pair by rule C, a floor arm of two qubits), so its length no longer asks for a longer line, and
several chains can share a device side by side (the workplace VS's packing estimate). The off arm here is the default
(conditionals removed): it is beside only and reads nothing meaningful (0.21 / 0.79 alternating in the dry run); the
margin g uses the ceiling c(L), a noiseless number of the third design's off circuit, as before. Dry run: the same g as
the early chain (+0.094 .. +0.232, slope +0.037, 2 SE 0.004). A possible saving: the output's reset and the next first
try conditioned on the same bit (one if / else; the exact simulator here handles no else yet).

## Reproduce

```
python notes/early_2026-11-17/early.py identity
python notes/early_2026-11-17/early.py build DEV OUT [--reuse] [--dry-clifford-sentinel]
python gpu/compound_night.py build DEV RD_OUT
python notes/early_2026-11-17/early.py ledger OUT RD_OUT
python -c "from psf_os import feedforward as F; F.run_local('OUT')"; python notes/early_2026-11-17/early.py score OUT
```
DEV = results/rus-neuron3-2026-11-16/fetch_in/ibm_marrakesh/dev.
