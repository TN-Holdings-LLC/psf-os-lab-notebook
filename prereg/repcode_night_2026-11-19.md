# Declared: the distance-3 repetition code decoded in real time by a look-up, its result used at once by a T, night of 2026-11-19

Home Claude, 2026-11-19, from the draft `prereg/drafts-2026-11-19/repcode_DRAFT.md` (workplace 19b, after the workplace VS's check); the owner's choices of
2026-11-19 (every recommended value). Declared when the commit that adds this file is pushed, before the device records of
the night are fetched; the tools are as of that commit, psf-os branch v0.2-proto-2026-11-18 at 5e4a936. The night's four
declarations are in one commit: `os_loop_night_2026-11-19.md`, `interfere_night_2026-11-19.md`,
`repcode_night_2026-11-19.md`, `qpe_repro_night_2026-11-19.md`. The loop runs first and fetches the night's device record;
the three single jobs are built on that same record. Tool: `gpu/repcode_night.py`
(register conditions). Design, size and dry runs: `notes/repcode_2026-11-19/README.md`.

## Common

- Device and record as the night's other jobs (the standing rule; one record for the night). Rule C placement
  (coupling graph and failed marks only); no mitigation; DD and twirling off; 4000 shots; every shot counted.
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

## Verdicts (2 SE)

1. Ceiling: **BEYOND THE CEILING** when p3 >= C + 2 SE, otherwise **NOT BEYOND** (the words of the earlier ceiling
   tests).
2. More tests inside one item, judged by (b0) and (b1) apart (the owner's choice); (a) and (b) pooled are beside:
   - (a) lut3 against lut1 (the control of the handover): d = p3 - p1. lut1 is a decoder told where the error is: under
     noise it never acts on a wrong syndrome and never corrects an error elsewhere, so (a) mixes the number of tests
     with the decoder.
   - (b) lut5 against lut3 (the same decoder, two more tests): d = p5 - p3. The added tests (s == 0) fire noiselessly
     for e = none only and never for e = d0, d1, d2 (the workplace VS's check), and on 2026-11-16 an unfired
     conditional cost nothing measurable; so (b) is also scored per group: (b0) e = d0, d1, d2 pooled (the added tests
     never fire) and (b1) e = none (they fire).
   Words, for (b0) and for (b1): **MORE TESTS KEEP LESS** (d <= -2 SE), **SAME WITHIN ERROR**, **MORE TESTS KEEP MORE** (d >= 2 SE).
   This separates a loss with more conditionals inside one item from the loss between items side by side of
   2026-11-17 / 18.

Beside, never judged: (a) lut3 - lut1 and (b) pooled; per error; c[1], c[2] (the decoding's check bits); the off arm
as read and its best fixed rule after the fact; the floors; the broadcast record; the sentinel.

## Predictions (written before the data)

- RC-1 lut3 is BEYOND THE CEILING.
- RC-2 (b0), the added tests never fire: SAME WITHIN ERROR (on 2026-11-16 an unfired conditional cost nothing
  measurable). (b1), they fire: no direction declared (read and reported, no prediction). On 2026-11-18 the decision latency was NOT RESOLVED
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
