# Four forms of the repetition code: the CZ count against the wait footprint (workplace Claude, 2026-11-20; desk and dry runs, not declared)

Tool `gpu/repcode4_night.py`; draft `prereg/drafts-2026-11-21/repcode4_DRAFT.md` (weekend candidate A; home's added
instruction 3, item 3).

## The forms (every form: lut3, the four error items n, 0, 1, 2; T and H on d0; c[0] judged)

| form | line | CZ written = compiled (ff / off / floor) | carriers at the wait | excited at the wait (n, 0, 1, 2; mean) | depth |
|---|---|---|---|---|---|
| F16 | d0 a0 d1 a1 d2 | 16 | 3 | 1.5, 1.5, 1.5, 1.5; 1.50 | 62 |
| F10 | a0 d1 d0 d2 a1 | 10 | 3 | 1.5, 1.5, 1.5, 1.5; 1.50 | 43 |
| F6P | a0 d1 d0 d2 a1 | 10 | 1 | 0.5, 2.5, 1.5, 1.5; 1.50 | 35 |
| F6 | a0 d1 d0 d2 a1 | 6 | 1 | 0.5, 2.5, 1.5, 1.5; 1.50 | 29 |

- carriers and excited: `psf_os.footprint.wait_footprint` (psf-os after-2026-11-20) of each item as written; one wait
  per item (the syndrome read before the look-up).
- F6P = F6 + two CZ pairs that cancel, placed where F10 has its extra CZ: one pair on d0-d1 before the syndrome read
  (F10 has 6 CZ there, F6 4), one on d0-d2 after the look-up (F10 2, F6 0). A barrier inside each pair keeps it
  through the level-1 compiler (without a barrier the pair is removed: the 2026-11-19 cancellation,
  `notes/repcode_2026-11-19_cz.md`). `check` compares every arm's compiled CZ with the form's count.
- Every form has a barrier after the error and one after the look-up (the same synchronisation points in all four).
- Ceiling 0.875 in every form (computed per form, exact; per error 1, 0.5, 1, 1).

## Reading table: every outcome on one row

The two words (footprint F6P - F10, CZ F6 - F6P), three values each, 9 outcomes: "both" 1, "the footprint" 1,
"the CZ count" 1, "neither" 1, "against the expectation" 5 (any KEEPS LESS). 1 + 1 + 1 + 1 + 5 = 9
(`repcode4_night.reading`, counted by enumeration).

## Dry runs (`dry/*.txt`; noises `noise/*.json`, written by hand, never fitted)

See the draft's table. gate -> the CZ count; wait, cond, c -> the footprint; a -> both. Each part dry-run with its own
seed 20261120 + 5,000,000 x part (Aer seeds shot i with seed + i; seeds closer than the shots give the same shots
shifted).

## Size

One job of 52 circuits, 61.0 s by the model at 4000 shots (above a 60 s job), or two jobs of 28 circuits, 34.2 s each
(`--part 1`: errors n, 0; `--part 2`: 1, 2; every form in both parts).
