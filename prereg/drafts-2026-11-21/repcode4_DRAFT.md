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

Two parts on the 2026-11-19 marrakesh record (`--part 1`, `--part 2`, the dry Clifford sentinel), each part's dry with
its own seed (20261120 + 5,000,000 x part), pooled by `score`. Noises in `notes/repcode4_2026-11-20/noise/` (written
by hand, never fitted): gate = depolarizing 1 % on every CZ; wait = amplitude damping 6 % on every other qubit at each
mid-circuit read; cond = dephasing 5 % on every qubit after each conditional; a = gate 1 % + damping 2 %; c = gate
0.2 % + damping 2 % + dephasing 5 % per conditional.

| noise | F16 | F10 | F6P | F6 | footprint F6P - F10 | CZ F6 - F6P | beside F10 - F16 | row of the reading table |
|---|---|---|---|---|---|---|---|---|
| gate | 0.927 | 0.957 | 0.959 | 0.978 | +0.001 SAME | +0.020 KEEPS MORE | +0.030 KEEPS MORE | the CZ count |
| wait | 0.957 | 0.953 | 0.985 | 0.985 | +0.032 KEEPS MORE | -0.000 SAME | -0.004 SAME | the footprint |
| cond | 0.842 | 0.839 | 0.939 | 0.941 | +0.100 KEEPS MORE | +0.002 SAME | -0.003 SAME | the footprint |
| a | 0.915 | 0.942 | 0.954 | 0.974 | +0.012 KEEPS MORE | +0.020 KEEPS MORE | +0.027 KEEPS MORE | both |
| c | 0.820 | 0.824 | 0.927 | 0.933 | +0.103 KEEPS MORE | +0.006 SAME | +0.004 SAME | the footprint |

(2 SE of the comparisons 0.003-0.009; every form's per-error values in `dry/<noise>.txt`.) Each single-mechanism
noise lands on its own row: gates only on "the CZ count", waits only and conditionals only on "the footprint", the mix
a on "both". So the design tells the mechanisms apart when one dominates. Under cond and c, F16 and F10 fall below the
ceiling (NOT BEYOND) while F6P and F6 stay beyond it: in those noises the footprint alone decides the ceiling verdict.

The decay count (`excited`, the expected waiting qubits in |1>) pooled over the four errors is 1.50 in every form
(F16, F10: 1.5 per error; F6P, F6: 0.5, 2.5, 1.5, 1.5 for none, d0, d1, d2), so the pooled footprint comparison is
at equal excited count; only the carriers differ.

## Known limits

- **F6 and F6P undo the code while the conditional waits.** The test injects one error and corrects it before a T;
  for that the forms are equivalent (the same noiseless distributions and ceiling). A real error-correcting memory
  must keep the code during the syndrome read (errors during the wait are then corrected too); F6 cannot be used
  there. What this test asks is narrower: what costs the most in real-time control on today's device.
- F6P's cancelling pairs add gate errors but act on qubits in basis states for d1, d2; they match F10's CZ count and
  rough timing, not every detail of F10's exposure. The barriers add synchronisation points (every form has the one
  after the error and one after the look-up).
- One night, one device. Dephasing during the wait (carriers) and decay (excited qubits) are not separated item by
  item: F6 raises the excited count for the error-on-d0 item (the syndrome 1, 1 waits on d1, d2: 2.5 against 1.5)
  and lowers it for the no-error item (0.5). Pooled over the four errors the excited count is 1.50 in every form, so
  the pooled footprint comparison holds decay fixed to first order; the per-error values are beside, not read.

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
