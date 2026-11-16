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
