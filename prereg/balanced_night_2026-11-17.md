# Declared: the frame-balanced neuron chain, L = 1 .. 5, night of 2026-11-17 (third round)

Home Claude, 2026-11-17 (owner 20:49 JST "今日でもよいよ", on the proposal to run the frame-balanced chain; the pair is
two fixed circuits pooled by a fixed rule, not the runtime twirling option, which stays off). Declared with the commit
that carries this file, pushed before the device record of the run is fetched. Common rules as in
`prereg/ff_night_2026-11-17.md` (device by the standing rule, the first qualifying in the order ibm_marrakesh, ibm_fez,
ibm_kingston; rule C placement; psf-os 301ac01; no mitigation, DD and twirling off; every shot counted; `check` before
submission, a FAIL means the job is not run; `score` as of this commit is the verdict tool). Design and desk check:
`notes/next_2026-11-17/BALANCED.md`.

## What is run (`gpu/balanced_night.py`)

Per L = 1 .. 5 (theta 1.1, m = 2): rd{L}, the third design (logical 1 held and read as |0>; the same circuits as test
T2 of the first round), and nf{L}, its complementary frame (the same barriers and waits, no flips, logical 1 held and
read as |1>); ff, off and floor arms; one ring sentinel; 34 circuits, 40.9 s by the model, 4000 shots per circuit.
Exact ideals `notes/next_2026-11-17/ideal7.json`. Try-build on the 2026-11-17 marrakesh record: check PASS.

## Verdicts

On the pooled value P = (P_rd + P_nf) / 2, every shot of both items counted, SE of the pool:
per L **BEYOND THE CORRECTION CEILING** when g = c(L) - |P - exact| >= 2 SE and P <= noiseless + 2 SE; **OVERSHOOT**
when P > noiseless + 2 SE; otherwise **NOT BEYOND**. Slope of g over L: **COMPOUNDS** when >= 2 SE and no L
overshoots; otherwise **NOT SHOWN**. Beside, never judged: rd and nf alone; rd alone against the first round's T2 (a
repeat of the same circuits, on this night's device).

## Predictions (written before the data)

1. B-1 No L overshoots (the pool).
2. B-2 BEYOND THE CORRECTION CEILING at every L = 1 .. 5.
3. B-3 COMPOUNDS.

Basis: the illustrative decay model (pool at or below noiseless everywhere; pooled margin positive at gamma 0.05) and
the first round (rd's g +0.075 to +0.164 on fez). Each prediction holds or fails as a whole; a failed one is reported
as failed.
