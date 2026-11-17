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

## Why the early chain did not pay on fez: a decision latency in an illustrative model (home VS Claude, 2026-11-17 evening)

**An illustration, not a prediction for any device.** The noise model is uniform and was not fitted; no calibration
or error number was read. Tools: `latency_desk.py` (grid), `latency_gate_only.py`, `latency_sep.py` (extra cases);
outputs `latency_desk.txt` / `.json`, `latency_gate_only.json`, `latency_sep.json`.

- Circuits: the compiled circuits that ran tonight on ibm_fez (T2 `compound/job`, T4 `early/job`), barriers kept.
- Timing: the time-budget ledger (FakeMarrakesh medians; ASAP as built); a decision latency LAT per conditional held on
  the conditional's qubits (0 / 0.5 / 1 / 2 us, examples).
- Noise: sx / x depolarising 3e-4, CZ two-qubit depolarising 3e-3 (0.3 %), readout flip 0.015 (mid-circuit and
  final), idle amplitude damping and dephasing with T1 = T2 = 150 us or an effective 50 us (the control test of
  2026-11-16 lost |1> as if T1 were 20-45 us during measurement waits).
- Engine: noise trajectories (16000 shots per circuit) on the state vector of the touched qubits, conditionals per
  shot; scored by the declared T4 scorer (`gpu/early_night.py score --rd`) on copies of tonight's job folders with the
  user cells replaced (sentinel rows as the device returned them). Check: noiseless, ff = the ideal.json values within
  the shot error (rd 0.887 / 0.797 / 0.707 / 0.636 / 0.562 against 0.890 / 0.793 / 0.706 / 0.629 / 0.560).

d = |rd - noiseless| - |early - noiseless| (positive: the early chain kept more), 2 SE 0.008-0.011; L = 1 is the same
circuit in both (d = 0).

| model | L 2 | L 3 | L 4 | L 5 |
|---|---|---|---|---|
| T1 150 us, LAT 0 | -0.002 | +0.003 | +0.005 | -0.002 |
| T1 150 us, LAT 0.5 us | -0.006 | +0.009 | +0.002 | -0.018 |
| T1 150 us, LAT 1 us | +0.001 | +0.009 | -0.001 | -0.003 |
| T1 150 us, LAT 2 us | +0.004 | +0.022 | +0.002 | +0.001 |
| T1 50 us, LAT 0 | +0.018 | +0.022 | +0.014 | +0.001 |
| T1 50 us, LAT 0.5 us | +0.023 | +0.026 | +0.012 | -0.012 |
| T1 50 us, LAT 1 us | +0.021 | +0.030 | +0.012 | -0.012 |
| T1 50 us, LAT 2 us | +0.018 | +0.014 | +0.006 | -0.035 |
| gates and readout only (no decay), CZ 0.3 % | -0.006 | -0.002 | -0.011 | -0.006 |
| gates and readout only, CZ 1 % | +0.005 | +0.009 | +0.003 | +0.004 |
| CZ 1 % only (no readout error, no decay) | +0.007 | +0.018 | +0.025 | +0.022 |
| readout 0.015 only (no gate error, no decay) | -0.003 | -0.009 | -0.020 | -0.014 |
| tonight on fez (device, T4-3) | between -0.010 and +0.011 at every L (2 SE 0.015-0.022) | | | |

ff at L = 5 (rd / early, noiseless 0.560): T1 150 us LAT 0 0.541 / 0.539, LAT 2 us 0.510 / 0.511; T1 50 us LAT 0
0.562 / 0.562, LAT 2 us 0.523 / 0.488; tonight on fez 0.474 / 0.479 (the device lost more than any cell of the model).

Reading (in the model):

- **The two effects that cancel are the CZ and the extra reads, not the latency.** Alone, the 32 CZ fewer at L = 5
  (CZ 1 %, nothing else) let the early chain keep +0.018 to +0.025 more at L = 3-5; alone, the readout error of its
  extra mid-circuit reads (the L - 1 early reads, and the conditionals that act on them) costs it -0.009 to -0.020.
  Together (gates and readout, no decay) d stays within 2 SE at every L, at CZ 0.3 % and at 1 %: the reading "the
  added conditionals offset the saving" holds, with the offsetting cost carried by the reads those conditionals need.
- **With weak decay (T1 150 us) the latency does not change the picture:** d within 2 SE at every L for LAT 0 to
  2 us (one cell, L = 3 at 2 us, reads +0.022). So on this model the device's "the same at every L" is met by any
  latency from 0 to 2 us.
- **With strong decay (T1 50 us) the early chain's shorter waits pay at L = 2-4** (+0.012 to +0.030 for LAT 0 to
  1 us), which the device did not show; and at L = 5 the latency turns against it (-0.012 at 0.5-1 us, -0.035 at
  2 us), because the early chain has 9 conditionals against 5. The device's equality at every L fits this branch only
  near LAT 2 us at L = 2-4 together with a smaller loss at L = 5 than the model gives.
- So the range asked for: in the weak-decay model, any latency from 0 to 2 us gives "no difference" (the
  cancellation is CZ against reads); in the strong-decay model none of 0-2 us gives "no difference at every L". The
  model's losses (about -0.02 to -0.05 at L = 5) are smaller than the device's (-0.08), so the model does not explain
  the size of the device's loss; it only says which way each piece pushes.

Not modelled: a latency that holds every qubit of the circuit (the ledger holds only the conditional's qubits),
measurement-induced effects on neighbours beyond the uniform idle decay, leakage, crosstalk.
