# The repetition code with a look-up decoder before a T (workplace Claude, 2026-11-19; desk only, not declared)

Home handover 2026-11-19, section 4.2. Tool `gpu/repcode_night.py`; draft `prereg/drafts-2026-11-19/repcode_DRAFT.md`;
psf-os with register conditions (v0.2-proto-2026-11-18).

## The circuit

Line d0 a0 d1 a1 d2; d0 holds T^dag|+>, encoded into d0 d1 d2 through the ancillas; an X on data e; parities into
register s; the look-up corrects; the ancillas reset by a conditional X on their own bit; decoded onto d0; T and H on
d0; every data qubit read. Noiselessly c = 000 in every shot (`ideal`, an exact branching simulator that reads
register tests; it equals notes/rus_coherent_2026-11-17's on the teleport test, difference 0).

The correction is used at once by the T: an X left on d0 before the T leaves c[0] at 1/2, and no rule on the recorded
bits can repair that afterwards. A memory test would not show this (a decoder run afterwards does as well).

## Items, size, check

| version | tests on s | what it is |
|---|---|---|
| lut3 | 3 (s = 1, 3, 2) | the full look-up |
| lut1 | 1 (the one for the injected error) | the control the home handover asked for: one test |
| lut5 | 3 + 2 that change nothing (s = 0 -> Z on an ancilla holding its measured value) | the same decoder with two more tests |

Each for e = none, 0, 1, 2, with off (no look-up, resets kept) and floor arms: 40 circuits, **47.6 s** by the model at
4000 shots (marrakesh, fez, kingston records of 2026-11-17: the same). Per item CZ 14-16, depth 53-58, mid-circuit
reads 2. `check`: PASS on all three records (ff c = 000 in every shot, the off arm's c[0] at its exact value, floors all
zero, the register tests kept in the compiled circuit on clbits 0 and 1, the broadcast record equal to the hand count:
144 conditionals, 216 condition bits, 48 broadcasts, 72 broadcast bits).

**Ceiling** C = 0.875: per item the best fixed rule on the off arm's other bits flipping c[0] (1, 1/2, 1, 1 for no
error, d0, d1, d2), averaged. Only the error on d0 makes the margin; the others check that nothing else is lost.

## lut1 against lut3 is not only the number of tests

Under noise a syndrome can come out wrong; lut3 then corrects what it reads, lut1 only acts on its one value. So lut1
and lut3 differ in decoding as well as in the number of tests. The dry run with an illustrative noise that has no cost
per conditional (noise a) read lut3 - lut1 = +0.0067 (2 SE 0.0062) once and +0.0072 / +0.0031 / -0.0001 with other
seeds (`dry/dry_a_other_seeds.txt`). lut5 against lut3 is the clean comparison (the same decoder, two more tests): with
noise a it reads -0.0031 (2 SE 0.0061), SAME. Both are scored; which one is judged is the owner's choice (the draft).

## Dry runs (marrakesh record, Clifford sentinel; `dry/`; noises written by hand, never fitted)

| noise | lut3 c[0] right (C 0.875) | lut3 - lut1 | lut5 - lut3 |
|---|---|---|---|
| none | 1.000 BEYOND | 0 SAME | 0 SAME |
| a: CZ 1 %, damping 2 % per read | 0.920 BEYOND | +0.007 MORE | -0.003 SAME |
| c: + dephasing 5 % per conditional | 0.813 NOT BEYOND | -0.068 LESS | -0.049 LESS |
| d: dephasing 60 % per conditional | 0.501 NOT BEYOND | -0.012 LESS | -0.002 SAME |

Every verdict word is reached.

## After the workplace VS's check (2026-11-19, `vs/VS_CHECK.md`; every check passed)

lut5's two added tests (s == 0) fire noiselessly for e = none only and never for e = d0, d1, d2; on 2026-11-16 an
unfired conditional cost nothing measurable, while the dry noise here costs every test, fired or not. `score` now gives
lut5 - lut3 per group beside the pooled d: added tests never fire (e = d0, d1, d2) and fire (e = none). Dry runs: noise
a -0.003 / -0.003 (SAME / SAME); noise c -0.047 / -0.057 (KEEP LESS / KEEP LESS). The circuits are unchanged (the
same build and check). lut1 is a decoder told where the error is (the VS's wording, now in the draft).
