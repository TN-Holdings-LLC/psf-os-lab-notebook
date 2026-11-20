# DRAFT (not declared): does the repetition code lose to its CZ count or to what waits during the conditional? (weekend candidate A)

Workplace Claude, 2026-11-20 (home's added instruction 3, item 3; the principle "do not spread the quantum state while
a conditional waits"). Words, thresholds, predictions and the reading table marked [OWNER] are the owner's; the
workplace built the tool, sized it and dry-ran it. Tool: `gpu/repcode4_night.py`. Notes: `notes/repcode4_2026-11-20/`.

## Why

- 2026-11-19 (`results/repcode-night-2026-11-19`): lut3 0.812 against the ceiling 0.875, NOT BEYOND.
- Desk (illustrative noise, never fitted): 10 CZ instead of 16 cuts the loss to 0.70; the workplace VS's six-CZ form
  (the encoding undone before the syndrome is read, the logical state on d0 alone during the wait) to about 0.2.
  The six-CZ form changes two things at once: the CZ count (6) and the qubits that carry the state during the
  conditional wait (1 instead of 3, `psf_os.footprint`).
- This test separates them, in one night, without a noise model.

## Design (one device record; rule C placement; no mitigation; DD and twirling off; every shot counted)

Four arrangements of the 2026-11-19 test, lut3 only (the full look-up on register s, three tests, and the two
single-bit ancilla resets: five conditionals in every form), each with the four error items (none, d0, d1, d2), T and
H on d0, every data qubit read, c[0] judged:

| form | line | CZ (written = compiled) | carriers during the wait | what it is |
|---|---|---|---|---|
| F16 | d0 a0 d1 a1 d2 | 16 | 3 | 2026-11-19's circuit, with a barrier after the error |
| F10 | a0 d1 d0 d2 a1 | 10 | 3 | d0 next to both data (`repcode2_night`) |
| F6P | a0 d1 d0 d2 a1 | 10 | 1 | F6 plus two CZ pairs that cancel: one on d0-d1 before the read, one on d0-d2 after the look-up, where F10 has its extra CZ (F10: 6 before the read, 2 after; F6: 4 and 0); a barrier inside each pair keeps it |
| F6 | a0 d1 d0 d2 a1 | 6 | 1 | encode, (error), undo the encoding, copy the syndrome from d1, d2 to the ancillas |

- A barrier after the error in every form keeps the compiler from cancelling a CX pair (on 2026-11-19 three of the
  four items went 16 -> 14 CZ; `notes/repcode_2026-11-19_cz.md`). `check` refuses any arm whose compiled CZ differs
  from its form's count.
- The ceiling is 0.875 in every form (the best fixed rule on the off arm's other recorded bits, noiseless and exact,
  computed per form; the off arm keeps the resets and drops the look-up).
- Size (the 2026-11-19 marrakesh record): one job of 52 circuits (16 items x 3 arms + the sentinel's 4), 61.0 s by the
  model at 4000 shots; or two jobs (`--part 1`: errors none, d0; `--part 2`: d1, d2; every form in both), 28
  circuits and 34.2 s each, 68.4 s in all [OWNER: one job if no 60 s limit applies, else two]. Depth per form 62,
  43, 35, 29. Every comparison is read inside each job and pooled over the four errors.

## Verdicts [OWNER]

- Ceiling, per form: BEYOND THE CEILING (p >= 0.875 + 2 SE) / NOT BEYOND (the words of 2026-11-19).
- Comparisons (lut3, the four errors pooled), d = p(x) - p(y), SE from the shots of both:
  - **footprint**: F6P - F10 (1 against 3 carriers, 10 CZ each);
  - **CZ**: F6 - F6P (6 against 10 CZ, 1 carrier each);
  - beside: F10 - F16 (10 against 16 CZ, 3 carriers each).
  Words for each: KEEPS MORE (d >= 2 SE), SAME WITHIN ERROR, KEEPS LESS (d <= -2 SE).

## Reading table (fixed before the data) [OWNER]

| footprint (F6P - F10) | CZ (F6 - F6P) | reading |
|---|---|---|
| KEEPS MORE | KEEPS MORE | both: fewer carriers and fewer CZ each keep more |
| KEEPS MORE | SAME WITHIN ERROR | the footprint: fewer carriers during the wait keep more at equal CZ |
| SAME WITHIN ERROR | KEEPS MORE | the CZ count: fewer CZ keep more; the footprint adds nothing seen |
| SAME WITHIN ERROR | SAME WITHIN ERROR | neither seen at this night's shot noise |
| either KEEPS LESS | (any) / (any) | against the expectation: not read for the mechanism |

All 9 outcomes of the two words fall on exactly one row (counted in `notes/repcode4_2026-11-20/README.md`).

## Predictions [OWNER] (written before the data)

- RC4-1 [OWNER: e.g. F6 BEYOND THE CEILING]
- RC4-2 [OWNER: e.g. footprint KEEPS MORE, or no direction]
- RC4-3 [OWNER: e.g. CZ SAME WITHIN ERROR / KEEPS MORE, or no direction]

## Dry runs (illustrative noise, never fitted; two parts; `notes/repcode4_2026-11-20/dry/`)

[filled below by the workplace]

## Known limits

- **F6 and F6P undo the code while the conditional waits.** The test injects one error and corrects it before a T;
  for that the forms are equivalent (the same noiseless distributions and ceiling). A real error-correcting memory
  must keep the code during the syndrome read (errors during the wait are then corrected too); F6 cannot be used
  there. What this test asks is narrower: what costs the most in real-time control on today's device.
- F6P's cancelling pairs add gate errors but act on qubits in basis states for d1, d2; they match F10's CZ count and
  rough timing, not every detail of F10's exposure. The barriers add synchronisation points (every form has the one
  after the error and one after the look-up).
- One night, one device. Whether the effect is dephasing during the wait (carriers) or decay (excited qubits, which
  F6 raises for the error-on-d0 item: the syndrome 1, 1 waits on d1, d2) is not separated by this design.

## Decisions at home before declaring ([OWNER] list)

1. One job (61.0 s) or two (`--part 1`, `--part 2`, 34.2 s each).
2. The words of the comparisons and the reading table (above, as proposed or changed).
3. Predictions RC4-1 .. RC4-3, each a direction or "none".
4. Whether F6 / F6P count as "the same test" in the paper (they share the ceiling and the scoring).

## Device procedure (home)

```
# psf-os at the declared commit (branch after-2026-11-20 or later); notebook at the declaring commit
python gpu/repcode4_night.py ideal                                   # every form: ceiling 0.8750, carriers 3 3 1 1
python gpu/repcode4_night.py build DEV OUT1 --part 1                 # or --part all for one job
python gpu/repcode4_night.py check OUT1                              # PASS: c = 000, CZ 16/10/10/6, ceiling 0.875
python -m psf_os submit OUT1 ; python -m psf_os collect OUT1         # as every night
(the same for OUT2 --part 2)
python gpu/repcode4_night.py score OUT1 OUT2
```
