# The feed-forward job in psf-os (workplace, 2026-11-16; desk only, nothing sent to a device)

psf-os branch `feedforward-2026-11-16`: `psf_os/feedforward.py` (new), `psf_os/ibm.py` (the pre-submit check now also
reads inside control-flow blocks; for circuits without control flow it gives exactly what it gave before),
`tests/test_feedforward.py` (6 tests). `user2d.py`, `compile.py` and the other modules are not changed; user2d still
refuses any gate after a measurement.

## What it accepts and does

- Form (anything else is refused with the reason): qubits 0 .. n-1 on a line, CZ between neighbours only, one-qubit
  gates, measurements anywhere into one classical register (each bit written once), `if_test` on one bit already
  written holding only X or Z on one qubit, no else branch.
- Placement: rule C (`chain.place`: the coupling graph and the failed marks, no error number), logical k on chain[k].
- Compilation: the map-free Target plus the control-flow op `if_else` (no property, no duration), level-1 pass
  manager, layout fixed, no routing. The build refuses if the compiler drops a conditional.
- Arms per item in one job, one ring sentinel per job:
  - **ff**: the circuit;
  - **off**: the same circuit without its conditional blocks (ideal 0.75 at k = 1, 0.50 beyond for the teleport test;
    0.75 is the bound for any fixed rule on the recorded bits);
  - **floor**: the compiled ff circuit with every sx and x removed, also inside the blocks; CZ, RZ, the mid-circuit
    measurements and the conditionals stay; ideal: every bit 0.
- Answer card: every shot counted (none discarded), success share and binomial 2 SE, the stated bound and
  (share - bound) / SE, the off arm's share, the floor's all-zero share and per-bit share of 1, the sentinel; beside,
  the best fixed rule on the off arm's recorded bits chosen after seeing them (optimistic; see below). No verdict words.

## Why no mirror, and what off and floor cover

A mirror is U, then U^-1, then readout; a mid-circuit measurement has no inverse, so a feed-forward circuit has no
mirror. What the mirror gave elsewhere is split here: the floor carries the same CZ and the same mid-circuit
measurements and conditionals with every bit ideally 0 (readout loss, idle loss over the same schedule, and
measurement-induced damage to the neighbours, which a mirror without mid-circuit measurements never saw); the off arm
carries the same pulses as ff except the conditionals, so ff - off isolates what the real-time control adds. What
neither covers: an error in the conditional X itself shows only in ff (as it should: that is what is tested).

## Noiseless check (Aer, the 11-15 ibm_marrakesh record, 4000 shots, sentinel at its Clifford point for the local run)

| k | chain | CZ | depth | ff | off | off, best fixed rule after the fact | floor all zero | discarded |
|---|---|---|---|---|---|---|---|---|
| 1 | 0-1 | 1 | 15 | 1.000 | 0.755 | 0.755 | 1.000 | 0 |
| 2 | 0-2 | 2 | 19 | 1.000 | 0.504 | 0.758 | 1.000 | 0 |
| 4 | 0-4 | 4 | 31 | 1.000 | 0.501 | 0.761 | 1.000 | 0 |
| 8 | 0-8 | 8 | 55 | 1.000 | 0.489 | 0.800 | 1.000 | 0 |

The after-the-fact rule grows with k because it is chosen on 2^k groups of the same data (k = 8: 256 groups): an
overfit, not a better classical method. A declaration should take the bound 0.75 from the circuit (any fixed rule on
the recorded bits), or fix the rule (the Pauli-frame parity) before the run; never the best rule found on the data.
The existing psf-os tests are unchanged (results in the report); the 6 new ones pass.

## Does IBM's submission take it as it is?

Checked in qiskit-ibm-runtime 0.51.0 (installed here) and offline, without sending anything:
- `SamplerV2.run` validates before sending (base_primitive): `validate_no_dd_with_dynamic_circuits` (dynamical
  decoupling must be off with dynamic circuits: psf-os sets it off), `validate_isa_circuits`, whose helper recurses into
  control-flow blocks (`utils/utils.py`, `_is_isa_circuit_helper`), and `validate_classical_registers` (register names
  must be identifiers: ours is `c`). Twirling stays off (psf-os options).
- `service.backend(name)` keeps control-flow instructions (`use_fractional_gates=False` by default; the 0.51 docstring
  says fractional gates and dynamic circuits can now be used together). The fake Heron targets list `if_else`.
- psf-os's own pre-submit check (`ibm.problems`) read only the top level; it now walks into the blocks, so a
  conditional gate on a failed element or a non-coupler is caught (test).
- Offline run of `psf_os.ibm.submit` on a built feed-forward job with a stand-in service whose backend is the runtime's
  FakeMarrakesh (renamed): problems() empty, `is_isa_circuit` empty for every circuit, SamplerV2 accepted and ran it in
  local mode; the result has the one data field `c` with k + 1 bits per shot, which `collect` (join_data) stores as is.
- Not checked: the real service's server side and the latency of feed-forward on ibm_marrakesh; the time model leaves
  out the microseconds of mid-circuit measurement and feed-forward per shot.

## Device time (the project's time model, 4000 shots, the 11-15 marrakesh record)

| job | circuits | seconds |
|---|---|---|
| one k (ff, off, floor + sentinel 4) | 7 | 10.8 |
| k = 1, 2, 4, 8 in one job | 16 | 20.9 |

## Not yet

Verdict words and numbers (a declaration, at home). Longer forms (two-qubit corrections, other bases, branching on
several bits) are refused for now. A CLI command is not added (the module's functions are the interface).
