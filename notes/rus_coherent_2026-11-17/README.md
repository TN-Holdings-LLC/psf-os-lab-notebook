# Repeat-until-success without waiting: the coherent form (workplace design, 2026-11-17; desk only, not declared)

Owner 2026-11-16 23:14 JST: "make the tries seamless, zero waiting, no gaps for noise; drop the intermediate results,
keep only the entrance and the exit". Handover of 2026-11-16 night, items 2 and 2b. Scripts: `coherent.py` (forms,
exact check, sizes, times; output `coherent.json`), `coh_job.py` (draft tool of the first test). psf-os branch
`feedforward-2026-11-16`: `feedforward.build` takes an explicit off arm (`spec["off_circuit"]`), tested.

## The circuit

Each try r has its own fresh ancilla a_r; try r runs coherently only when a_{r-1} is |1> (the previous try failed):
the undo RY(pi/2) on the output, the ancilla rotation, the controlled -iY onto the output, the ancilla's rotation back.
No mid-circuit measurement, no reset, no conditional; every qubit is measured once at the end. a_r's final bit is
the record of try r, so the measured bits are those of `psf_os.feedforward.rus_chain` (ancilla bits, then the last
output).

Two facts of this circuit make it cheap:
- an untried ancilla is |0>, so the controlled -iY and the S-dagger of try r need no control (they do nothing on |0>);
- within neuron j >= 2, a_{r-1} = 1 implies the previous output was 1 (with the previous output 0 the first rotation
  is off, the first try "succeeds" and no retry runs), so a retry needs no control by the previous output: no
  doubly controlled gate anywhere.

## Correctness (exact, no sampling)

The joint distribution of (all ancilla bits, last output) of each coherent form, by statevector, against the
measure-and-feed-forward circuit `rus_chain(L, 1.1, m)`, by an exact branching simulation of the dynamic circuit:
L = 1, 2, 3 and m = 2, 3, three forms each (18 cases): largest total variation distance 1.05e-15. So the coherent
forms give exactly the distribution of tonight's circuits (the third design rd reads the same distribution with its
declared relabelling).

## Size on Heron (the 11-16 13:11 CET ibm_marrakesh record, rule C chain, psf-os's map-free compiler, no routing pass)

Forms (no search anywhere):
- **naive**: the retry block as a generic controlled gate (Qiskit `.control`, the previous output's control kept),
  per neuron on the line [a_0 .. a_{m-1}, o]; two-qubit gates on non-neighbours routed by a fixed rule (move the first
  qubit along the line until it touches the second).
- **zipper (2b-1)**: the line a_0, o, a_1, a_2, ... per neuron, next neuron's block right after; before try r the
  output steps one place along the line onto the fresh ancilla's site, so every gate of the try acts on neighbours;
  exact gates (controlled RY = 2 CZ, step = SWAP of 3 CZ). This is the zipper of the fold rule applied to the tries:
  the line never needs a qubit of degree 3.
- **zipper+ (2b-1 + 2b-2)**: the same line with gates that use what is known: the controlled preparation of a fresh
  |0> is RY(a) CX RY(-a), a = (pi - phi)/2 (1 CZ, exact on |0>); the ancilla's last controlled rotation is followed
  only by its measurement and its use as a control, so a controlled RY up to a diagonal phase is enough (1 CZ); the
  output's step onto a fresh |0> is a move of 2 CX, not a SWAP of 3. The undo on the output stays an exact controlled
  RY (2 CZ: the output is still live).

CZ / CZ layers / depth (naive: in brackets the routing SWAPs; first column the naive circuit's CZ with all-to-all
connectivity, as home's desk count); tonight's third design (rd, mid-circuit measurements) beside with its
mid-circuit measurements:

| L | m | naive all-to-all CZ | naive on the line | zipper | zipper+ | rd: CZ / mid-circuit measurements |
|---|---|---|---|---|---|---|
| 1 | 2 | 19 | 34 / 34 / 106 (5) | 11 / 11 / 50 | 8 / 8 / 41 | 2 / 2 |
| 1 | 3 | 37 | 88 / 86 / 243 (17) | 21 / 21 / 90 | 15 / 15 / 72 | 3 / 3 |
| 2 | 2 | 70 | 151 / 145 / 380 (27) | 26 / 24 / 103 | 18 / 17 / 80 | 12 / 4 |
| 2 | 3 | 134 | 344 / 316 / 807 (70) | 46 / 44 / 183 | 32 / 31 / 142 | 18 / 6 |
| 3 | 2 | 121 | 268 / 227 / 577 (49) | 41 / 37 / 156 | 28 / 26 / 119 | 22 / 6 |
| 3 | 3 | 231 | 600 / 517 / 1294 (123) | 71 / 67 / 276 | 49 / 47 / 212 | 33 / 9 |

zipper+ costs 1 + 3 (L - 1) + 7 L (m - 1) CZ (try 0: the controlled -iY, plus for L >= 2 the preparation and the
rotation back controlled by the previous output; each retry: undo 2, step 2, preparation 1, -iY 1, rotation back 1).
Against home's desk count (L = 1: 16 / 32 for m = 2 / 3, generic controls): 8 / 15. Qubits: L (m + 1) against 2L for
rd. The rd row's layers and depth are not comparable (a conditional block counts as one instruction there), so the
time below is the comparison.

## Time (illustrative: durations from Qiskit's FakeMarrakesh snapshot, not the device record)

The psf-os device record keeps the coupling graph and the failed marks only, by policy, so it holds no gate or
measurement length; the handover's "only the record's lengths" cannot be met from it. As an illustration only, the
lengths in qiskit-ibm-runtime's FakeMarrakesh snapshot (a public file of that package, backend version 1.0.7; CZ 68
ns, SX / X 36 ns, measurement 2.584 us; no error number used) give the longest path in microseconds, the final
measurement included; rd without the feed-forward latency, which the snapshot does not give and IBM's guide calls
longer than a two-qubit gate:

| L | m | naive | zipper | zipper+ | rd (mid-circuit) |
|---|---|---|---|---|---|
| 1 | 2 | 6.2 | 4.0 | 3.7 | 8.2 + 2 latencies |
| 1 | 3 | 11.7 | 5.2 | 4.6 | 11.1 + 3 latencies |
| 2 | 2 | 17.4 | 5.6 | 4.9 | 14.9 + 4 latencies |
| 2 | 3 | 35.1 | 8.0 | 6.7 | 21.1 + 6 latencies |
| 3 | 2 | 25.7 | 7.2 | 6.0 | 21.5 + 6 latencies |
| 3 | 3 | 55.6 | 10.8 | 8.7 | 31.0 + 9 latencies |

So zipper+ trades each mid-circuit measurement (2.6 us plus the latency, during which tonight a |1> decayed: q1 0.98
-> 0.46 over five measurements' wait) for about 5-7 CZ: at L = 1, m = 2, 8 CZ in 3.7 us against 2 CZ and 2
mid-circuit measurements in 8.2 us plus latencies. Whether that is a gain on the device is what the test below asks.

## Draft of the first test (not declared; numbers and verdict words are the owner's)

One job, ibm_marrakesh (the night's device by the standing rule), theta 1.1, L = 1, m = 2, 4000 shots, no
mitigation, DD and twirling off, built by `coh_job.py build DEVDIR OUT`:
- **coh1**: the coherent form (zipper+, 8 CZ on 3 qubits); off arm: the same line with try 0 only (given explicitly);
  floor: sx and x removed.
- **rd1**: the third design of 11-16, unchanged (`gpu/rus3_night.chain(1, 1.1, 2)`), read with its declared
  relabelling; its off and floor as there.
- one ring sentinel; 10 circuits, 14.2 s by the model.
Dry run (noiseless, sentinel at its Clifford point): coh1 ff 0.886 (still failed 0.107), off 0.801, post 0.942 (kept
0.679); rd1 ff 0.889, off 0.791; both against the exact 0.937 and the noiseless two-try value 0.892; floors all zero.
Possible forms of the verdict (to choose): per item, CLOSER WITH CONTROL as declared on 11-16 (d = |P_off - exact| -
|P_ff - exact| >= 2 SE_d); between the items, "coh1 closer to the noiseless two-try value than rd1 by at least 2 SE".
Basis to quote: rd1 on 11-16 marrakesh ff 0.883, kingston 0.853.

## A caution for the theme of 11-16

The coherent form is a fixed circuit: nothing is decided during the run, so its output can be raised by
after-the-fact methods (zero-noise extrapolation, probabilistic error cancellation) like any expectation value. It
does not belong to the 11-16 claim "a success that no processing of the recorded bits can reach", which needs the
mid-circuit decisions of the feed-forward test. It answers a different question: whether removing the waits beats
the gates it costs.
