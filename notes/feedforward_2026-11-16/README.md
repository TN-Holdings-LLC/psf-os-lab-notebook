# A feed-forward test: correctness that only real-time control can give (desk design, 2026-11-16)

Owner 2026-11-16 ("進めて", stage 3). `ff_desk.py` (output `ff_desk.txt`): k one-bit teleports along a line, each
followed at once by a conditional X on the next qubit (mid-circuit measurement and feed-forward, supported on Heron;
IBM's guide "Classical feedforward and control flow"), the input chosen so that, after a non-Clifford T at the end, every
shot ideally ends in 0.

| k hops | success with feed-forward | without (conditional X removed) | without, plus the best fix of the last bit from the recorded mid-circuit bits |
|---|---|---|---|
| 1 | 1.000 | 0.751 | 0.751 |
| 2 | 1.000 | 0.501 | 0.752 |
| 3 | 1.000 | 0.501 | 0.750 |
| 4 | 1.000 | 0.501 | 0.757 |

(noiseless Aer, 20000 shots; the last column's 0.757 at k = 4 is the best rule chosen after seeing 16 groups of data,
an optimistic estimate of 0.75.) The X byproducts land before the non-Clifford T, so a classical Pauli frame cannot
repair them: without real-time control no processing of the recorded bits gets above 3/4 (only discarding shots,
which the verdict forbids). A device success clearly above 0.75 (4000 shots: 2 SE about 0.014) shows correctness that
after-the-fact processing cannot produce.

Needed in psf-os (it now refuses any gate after a measurement): a declared "feed-forward" job kind that accepts
mid-circuit measurements and if_test blocks, places the line by the chain rule, carries its own controls (the same
circuit with the conditionals removed: the 0.75 arm; the floor without the non-diagonal gates, ideal all zeros), and
an answer card per shot (success share, 2 SE, the 0.75 bound). Instructions for the workplace:
`職場への指示書_2026-11-16.md` in the handover package.

## Noise desk (workplace VS Claude, 2026-11-16)

`noise_desk.py` and `NOISE_DESK.md`: the success with feed-forward per k under an illustrative uniform noise model (not
fitted to any device), and the margin above 0.75 in units of 2 SE of a 4000-shot job.

## Next: a quantum neuron by repeat-until-success (desk, 2026-11-16 afternoon)

`rus_neuron_desk.py` (output `rus_neuron_desk.txt`): the repeat-until-success circuit of Cao, Guerreschi and
Aspuru-Guzik (arXiv:1711.11240) turns an output qubit by RY(2 q(theta)), tan q = tan^2 theta, when its ancilla reads 0;
when it reads 1 the output was turned by a known RY(-pi/2) (checked numerically), which is undone before a retry. L
neurons in a row, neuron j+1's angle switched on by neuron j's output (the state is carried forward). Noiseless Aer,
P(final output 1) against the exact value:

| L | theta | exact | real time, 3 tries (still failed) | one try, keep only all-success shots (kept) | no control, nothing discarded |
|---|---|---|---|---|---|
| 1 | 1.1 | 0.937 | 0.919 (0.034) | 0.935 (0.673) | 0.793 |
| 2 | 0.8 | 0.280 | 0.271 (0.181) | 0.188 (0.372) | 0.263 |
| 2 | 1.1 | 0.878 | 0.849 (0.064) | 0.851 (0.473) | 0.634 |
| 3 | 0.8 | 0.148 | 0.144 (0.206) | 0.052 (0.336) | 0.136 |
| 3 | 1.1 | 0.823 | 0.781 (0.091) | 0.741 (0.343) | 0.502 |

Two things the chain shows that a single step does not:
- discarding shots is not only costly (kept 0.34 at L = 3) but biased: whether a neuron's attempt succeeds depends on
  the state the previous neuron left, so keeping only the all-success shots over-weights some branches (L = 3,
  theta 0.8: 0.052 against 0.148). Real-time retries keep every branch and land within the share still failing after
  three tries;
- without control the error grows with the chain (L = 3, theta 1.1: 0.502 against 0.823).
What psf-os needs for it (instructions to the workplace): conditional blocks holding a fixed sub-circuit (RY, the
controlled-Y written with CZ, a reset by conditional X, a measurement), nested to a fixed number of tries.

## Noise desk for the quantum neuron (workplace VS Claude, 2026-11-16)

`rus_noise_desk.py` and `RUS_NOISE_DESK.md`: ff, post and off of `rus_neuron_desk.py` under the same illustrative
uniform noise model as `NOISE_DESK.md` (not fitted to any device), exact by density matrix for L = 1-4, m = 1-5,
theta 0.5 / 0.8 / 1.1. Where ff's error is smaller than off's by at least 2 SE (4000 shots per arm), and whether
post's bias survives noise.

## Decay during the waits: three designs and the form without mid-circuit measurements (workplace VS, 2026-11-17)

`rus_decay_desk.py` and `RUS_DECAY_DESK.md`: the model of `RUS_NOISE_DESK.md` with amplitude damping on every waiting
qubit during each mid-circuit measurement (uniform examples, not fitted; the control test of 2026-11-16 beside), for D1,
D2, D3 as compiled on 2026-11-16 and the workplace form without mid-circuit measurements (zipper+). Error against the
exact value and loss against each circuit's own noiseless value, side by side.
