# DRAFT (not declared): the distance-3 repetition code decoded in real time by a look-up, its result used at once by a T, night of 2026-11-19

Workplace Claude, 2026-11-19 (home handover 2026-11-19, section 4.2). Every verdict word, threshold and prediction
marked [OWNER] is the owner's; the declaration is written and pushed at home. Tool: `gpu/repcode_night.py` on psf-os
v0.2-proto-2026-11-18 (register conditions). Design, size and dry runs: `notes/repcode_2026-11-19/README.md`.

## Common

- Device and record as the night's other jobs (the standing rule; one record for the night). Rule C placement
  (coupling graph and failed marks only); no mitigation; DD and twirling off; 4000 shots [OWNER]; every shot counted.
  No calibration error number is read. `check` before submission; a FAIL means the job is not run. One job.

## What is run (one job: 40 circuits, 47.6 s by the model)

Line d0 a0 d1 a1 d2. d0 holds T^dag|+>, encoded into d0 d1 d2 through the ancillas (neighbour gates only); an X on
data e (e = none, 0, 1, 2); the parities a0 = d0 + d1 and a1 = d1 + d2 into a 2-bit register s; the look-up; the
ancillas reset by a conditional X on their own bit; decoded onto d0; T and H on d0; d0, d1, d2 read (c[0], c[1], c[2]).
Noiselessly every shot reads c = 000.

- lut3_e: the full look-up (s = 1 -> X d0, s = 3 -> X d1, s = 2 -> X d2; three tests on one register).
- lut1_e: one test only, the one for error e (no error: the test of s = 1, which never fires).
- lut5_e: lut3 and two tests that change nothing (s = 0 -> Z on an ancilla holding its measured value).
- Arms: ff; off (no look-up, the resets kept; given explicitly); floor. One ring sentinel.

`check` also requires: the register tests kept in the compiled ff arm (register s over clbits 0, 1; 3 / 1 / 5 tests),
and the manifest's broadcast record equal to the hand count (144 conditionals, 216 condition bits, 48 broadcasts, 72
broadcast bits).

## What is read (`score OUT`)

- p3: the share of lut3's shots with c[0] = 0, the four errors pooled; p1, p5 likewise.
- The ceiling C = 0.875: per item the best fixed rule on the off arm's other recorded bits (s, c[1], c[2]) that flips
  c[0], noiseless and exact (1, 1/2, 1, 1 for no error, d0, d1, d2), averaged.

## Verdicts (2 SE [OWNER])

1. Ceiling: **BEYOND THE CEILING** when p3 >= C + 2 SE, otherwise **NOT BEYOND** (the words of the earlier ceiling
   tests).
2. More tests inside one item [OWNER: which comparison is judged]:
   - (a) lut3 against lut1 (the control of the handover): d = p3 - p1. Note: under noise a syndrome can be wrong, and
     lut3 corrects what it reads while lut1 acts on one value only, so (a) mixes the number of tests with the decoder.
   - (b) lut5 against lut3 (the same decoder, two more tests): d = p5 - p3. The clean comparison.
   Words [OWNER]: **MORE TESTS KEEP LESS** (d <= -2 SE), **SAME WITHIN ERROR**, **MORE TESTS KEEP MORE** (d >= 2 SE).
   This separates a loss with more conditionals inside one item from the loss between items side by side of
   2026-11-17 / 18.

Beside, never judged: the comparison not judged in 2; per error; c[1], c[2] (the decoding's check bits); the off arm
as read and its best fixed rule after the fact; the floors; the broadcast record; the sentinel.

## Predictions [OWNER] (written before the data)

- RC-1 lut3 is BEYOND THE CEILING. [OWNER]
- RC-2 the judged comparison of 2: [OWNER: a direction or none]. On 2026-11-18 the decision latency was NOT RESOLVED
  (+0.32 us, 2 SE 0.42) and two conditionals did not wait for each other; a cost per extra test small against 2 SE
  would read SAME WITHIN ERROR.

Basis: dry runs on the 2026-11-17 marrakesh record with illustrative noises never fitted (none: BEYOND, SAME; a cost
per CZ and per read only: BEYOND, (b) SAME; a cost per conditional: NOT BEYOND, MORE TESTS KEEP LESS).

## Known limits

- Only the error on d0 makes the margin over the ceiling; the other items check that nothing else is lost.
- The look-up decodes one round of syndromes of a bit-flip code; it says nothing of phase errors or of repeated rounds.
- One device, one night, one placement.

## Reproduce

`python gpu/repcode_night.py score OUT` from the recorded job gives the same `repcode_scores.json`; `build` with the
recorded device record and shots gives the same circuits.
