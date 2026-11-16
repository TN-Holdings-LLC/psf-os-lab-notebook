# Declared: does real-time feed-forward on Heron give a success that no processing of the recorded bits can reach?

Home Claude, 2026-11-16 (owner 15:17 JST "進めて", on the proposal: run the teleport test once, k = 1 and 2, then
the repeat-until-success neuron). Declared with this commit, pushed before the device records of the run are fetched;
a change after the push is a new declared file. Desk work: `notes/feedforward_2026-11-16/` (design, noiseless check,
the workplace's psf-os job and noise illustration).

## Question

k one-bit teleports along a line, each followed at once by a conditional X on the next qubit, then a non-Clifford T
and H on the last qubit; the input is chosen so that every shot ideally ends with the last bit 0. Without the
conditional X, the X byproducts land before the T, and no fixed rule on the recorded bits (relabelling, flipping the
last bit by any function of the mid-circuit bits) gets the last bit right in more than 3/4 of the shots; the only way
above is to discard shots. Does the device, with real-time control, get above 3/4 with every shot counted?

## Circuits and job

psf-os branch `feedforward-2026-11-16` (commit 1ab062b; `psf_os/feedforward.py`): `teleport_test(k)` for k = 1, 2, 4,
built by `python gpu/ff_night.py build DEVDIR OUT --k 1 2 4`. One job: per k the arms ff (the circuit), off (the same
circuit without the conditional blocks) and floor (the compiled circuit without sx and x, ideal every bit 0); one ring
sentinel. Placement by rule C (coupling graph and failed marks only). 4000 shots, no mitigation, dynamical decoupling
and twirling off. 13 circuits, 17.5 s by the model (which leaves out the mid-circuit latency, microseconds per shot).

## Device

The night's device by the standing rule (`gpu/daily_fetch.py`: every device of ibm_marrakesh, ibm_fez, ibm_kingston
with at most 10 pending jobs, else the fewest); when several qualify, the first in that order. One device only.

## Pre-run check (before submission)

`python gpu/ff_night.py check OUT`: noiseless Aer of every arm but the sentinel: ff last bit 0 in every shot, off within
0.03 of 0.75 (k = 1) or 0.50 (k >= 2), floor all zeros in every shot. FAIL: the job is not run. On the 2026-11-15
marrakesh record (try-build): PASS (ff 1.000; off 0.741, 0.488, 0.488; floor 1.000).

## Answers

The ideal outcome is public (last bit 0 in every shot); the test does not rest on a sealed answer but on the bound,
which comes from the circuit, not from data.

## Verdict (`python gpu/ff_night.py score OUT`, unchanged after this commit)

Per k in {1, 2}: from the job's raw counts, every shot counted, none discarded, no corrected value used:
**ABOVE THE BOUND** when the ff arm's share of shots with the last bit 0 is at least
0.75 + 2 sqrt(0.75 x 0.25 / shots) (0.7637 at 4000 shots); otherwise **NOT ABOVE**. k = 4 is beside, never judged.

## Predictions (written before the data)

1. k = 1: ABOVE THE BOUND.
2. k = 2: ABOVE THE BOUND.
3. The off arm stays at or under its circuit value plus two SE (k = 1: 0.75 + 2 SE; k = 2: 0.50 + 2 SE): the
   control does what the circuit says.

Each prediction holds or fails as a whole; a failed one is reported as failed.

## Reported beside (never judged, never used to correct)

k = 4 (the workplace illustration puts it near the bound for long mid-circuit waits); the floor's all-zero share and
per-bit share of 1; the sentinel; the best fixed rule on the off arm's recorded bits chosen after seeing them
(optimistic: with 2^k patterns it rises above 0.75 by chance as k grows, which is why the bound is the circuit's 0.75,
not that number).
