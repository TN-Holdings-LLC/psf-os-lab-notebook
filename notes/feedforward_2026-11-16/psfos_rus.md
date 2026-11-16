# Repeat-until-success in the psf-os feed-forward job (workplace, 2026-11-16 evening; desk only, nothing sent)

psf-os branch `feedforward-2026-11-16` (on 1ab062b): `psf_os/feedforward.py` extended, `tests/test_feedforward.py`
(10 tests, 4 new). Outputs here: `psfos_rus_noiseless.json`, `psfos_rus_table.json`. Tonight's teleport job is built
exactly as before (the same gate hash 591a929f0cce1112 on the 11-15 marrakesh record before and after the change).

## One change from the instructions, because of IBM's rules

IBM's guide "Execute dynamic circuits" (read 2026-11-16): "Nested conditionals are not allowed" and "Having reset or
measurements inside conditionals is not supported". The desk circuit (`rus_neuron_desk.py`) measures inside its
conditional blocks, so it would not run on the device as written. The psf-os form therefore is:

- a conditional block holds gates only (one-qubit gates and neighbour CZ): undo RY(pi/2) on the output, reset the
  ancilla by X (it was just measured 1), the next attempt;
- each try's measurement sits after its block, unconditionally, in every shot (after a success the ancilla is |0> and
  reads 0 again, so nothing further fires; noiselessly the circuit equals the desk's);
- blocks are sequential, never nested; each classical bit is written once.

The entrance refuses a measurement, a reset or a conditional inside a block, quoting those rules (form "blocks").
The narrow form of the teleport test (form "pauli", the default) is unchanged.

## What was added

- **Form "blocks"** (`analyse(qc, form="blocks")`): conditional blocks with fixed sub-circuits of one-qubit gates and
  neighbour CZ; the rules above.
- **CY and CRY at the entrance** (`lower`, also inside blocks; exact identities checked with Operator.equiv):
  CY(c, t) = Sdg(t) H(t) CZ(c, t) H(t) S(t); CRY(theta)(c, t) = RY(theta/2)(t) CX RY(-theta/2)(t) CX, each
  CX(c, t) = H(t) CZ(c, t) H(t).
- **`rus_chain(L, theta, m)`**: L neurons on a line a0, o0, a1, o1, ... (neuron j's ancilla angle switched on by output
  j-1), m tries, one register (tries of neuron j in c[jm .. jm+m-1], the last output in c[Lm]); exact value of
  P(last output 1) when every neuron succeeds, (sin^2 q)^L with tan q = tan^2 theta, also by statevector
  (`rus_exact_statevector`): equal to 1e-12 for L 1-3 and theta 0.8, 1.1.
- **Arms**: ff (the circuit); off (the conditional blocks removed; the try measurements stay); floor (sx and x removed,
  also inside blocks; ideal all zero). **post** is the off arm's counts read post-selected (shots whose first try
  succeeded for every neuron): the same circuit as off, so no extra circuit is sent; the card shows the shots
  discarded and the share kept, and post is never a verdict.
- **Card** (`rus_card`): P(last output 1) for ff, off and post against the exact value, binomial 2 SE and the
  difference in SE; ff's share still failing after m tries; post's kept share and discarded shots; the floor.
- `ibm.problems` already walks into blocks at any depth (it recurses); a test with a non-coupler CZ two levels down
  now covers it.

## Noiseless check (Aer, the 11-15 marrakesh record, 4000 shots, m = 3)

| L | theta | exact | ff (still failed) | post (kept) | off | floor |
|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.529 | 0.530 (0.127) | 0.535 (0.492) | 0.508 | 1.000 |
| 1 | 1.1 | 0.937 | 0.918 (0.034) | 0.933 (0.668) | 0.791 | 1.000 |
| 2 | 0.8 | 0.280 | 0.278 (0.176) | 0.195 (0.364) | 0.272 | 1.000 |
| 2 | 1.1 | 0.878 | 0.850 (0.065) | 0.872 (0.469) | 0.643 | 1.000 |
| 3 | 0.8 | 0.148 | 0.152 (0.207) | 0.055 (0.335) | 0.140 | 1.000 |
| 3 | 1.1 | 0.823 | 0.789 (0.094) | 0.730 (0.337) | 0.491 | 1.000 |

Equal to the desk table (20000 shots) within the 4000-shot spread; the one larger gap, post at L 2 / theta 1.1 (0.872
against 0.851), is sampling: 40000 shots of the same circuit give 0.8512 lowered and not lowered. Even noiselessly
ff misses the exact value by the share still failing after 3 tries (theta 1.1: -0.02 to -0.03), and at theta 0.8
off is close to the exact value by accident (failed attempts leave the output near the same value), so theta 1.1 is
where ff, post and off separate.

## Size and device time (the project's time model, 4000 shots, the 11-15 marrakesh record, real sentinel)

| L | qubits | CZ (in blocks) | CZ off | depth | mid-circuit measurements | conditionals |
|---|---|---|---|---|---|---|
| 1 | 2 | 3 (2) | 1 | 14 | 2 | 2 |
| 2 | 4 | 18 (12) | 6 | 41 | 5 | 4 |
| 3 | 6 | 33 (22) | 11 | 68 | 8 | 6 |

| job | circuits | seconds by the model |
|---|---|---|
| one (L, theta) | 7 | 10.8 |
| L 1-3 at theta 1.1 | 13 | 17.5 |
| L 1-3 at theta 0.8 and 1.1 | 22 | 27.6 |

The model leaves out mid-circuit measurement and feed-forward time; IBM's guide says these "typically have longer
execution time than two-qubit gates". Every if_test here tests one bit (the guide's limit is 32 bits per operand, and
about 2400 one-bit broadcasts per job).

## For the declaration (home, owner)

The verdict should count every shot (ff and off); post only beside. theta 1.1 separates the arms; the noiseless ff
value with 3 tries is not the exact value (still failing 3-9 %), so a declared line should be against the exact value
with the noiseless 3-try gap stated, or against the noiseless ff value. Nothing here is a verdict.

## Tonight's scoring tool, run end to end (item 1a)

`gpu/ff_night.py build` (13 circuits, 17.5 s), `check` (PASS: ff 1.000; off 0.741 / 0.488 / 0.488; floor all zero),
`run_local`, `score` (tp1, tp2 ABOVE THE BOUND, tp4 beside; off 0.755 / 0.504 / 0.501; sentinel read) all pass on the
11-15 marrakesh record. What was slow at home is only the local simulation of the ring sentinel (h = 0.6, 40 qubits,
not Clifford): it did not finish in 18 minutes here either. It does not touch the device run, whose sentinel counts come
from the device. Changes: `psf_os.feedforward.run_local` now refuses such a circuit at once (stabilizer for Clifford
circuits, statevector up to 24 touched qubits, otherwise a refusal naming the dry-run sentinel), and
`gpu/ff_night.py build --dry-clifford-sentinel` builds a dry-run job whose sentinel is at its Clifford point (the whole
chain then runs in 17 s). The device job is unchanged without the flag (gate hash 591a929f0cce1112 on the 11-15
record); the declaration's text and the verdict are not touched.
