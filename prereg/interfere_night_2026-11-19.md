# Declared: what the 0.06 loss of P-B follows (interference tests E1-E3), night of 2026-11-19

Home Claude, 2026-11-19, from the draft `prereg/drafts-2026-11-19/interfere_DRAFT.md` (home VS, 2026-11-18; built and checked on v0.2 by the workplace); the owner's choices of
2026-11-19 (every recommended value). Declared when the commit that adds this file is pushed, before the device records of
the night are fetched; the tools are as of that commit, psf-os branch v0.2-proto-2026-11-18 at 5e4a936. The night's four
declarations are in one commit: `os_loop_night_2026-11-19.md`, `interfere_night_2026-11-19.md`,
`repcode_night_2026-11-19.md`, `qpe_repro_night_2026-11-19.md`. The loop runs first and fetches the night's device record;
the three single jobs are built on that same record. Common rules as in
`prereg/parallel_night_2026-11-18.md` (placement by the coupling map and failed marks only; no mitigation, DD and
twirling off; 4000 shots; every shot counted; `check` before submission, a FAIL means the job is not submitted). Tool:
`gpu/interfere_night.py` (build, check, score), with psf-os's build_bundle `allow_conditional_neighbours=True`, `gap` and
`bit_order`.

## Background

`results/parallel-night-2026-11-18` (P-B; the home VS's independent check confirmed the reading): next to a fixed item
the conditional item on qubits 0-3 did not lose (B1); next to a conditional item, the item on qubits 0-3 (A, whose bits
come first in the register) lost 0.06, on its output bit alone, while B (qubits 5-8, bits after A's) did not move (B2);
B delayed past A's whole length did not remove A's loss (B3). Three things went together in A: its qubits (0-3), its
bits first, and a conditional neighbour one site away.

## What is run (one job, 22 circuits, 27.6 s by the model)

rd2 (`gpu/rus3_night.chain(2, 1.1, 2)`, the item of P-B) in three bundles, each sub-item against the same item alone on
the same qubits in the same job:

| bundle | A | B | sites between | bit order | separates |
|---|---|---|---|---|---|
| E1 | rd2's off arm (fixed) | rd2 (conditional) | 1 | A, B | B1 reversed: does a conditional item on B's qubits lose next to a fixed A |
| E2 | rd2 | rd2 | 3 | A, B | nearness: does A's loss remain when B is three sites further |
| E3 | rd2 | rd2 | 1 | **B, A** | bit order: does the loss stay with A's qubits or move with the bits that come first |

Singles: sa on E1/E3's (and E2's) A qubits, sb on E1/E3's B qubits, sc on E2's B qubits. On the 2026-11-18 marrakesh
record: A [0, 1, 2, 3], B [5, 6, 7, 8], E2's B [7, 8, 9, 10].

## Checks before submission (`check OUT`)

Independence of every bundle arm; per packed sub-item the same instructions per wire and the same exact distribution
as its single reference (E1's A against sa's off arm); the same physical qubits; the recorded acceptance of every arm,
no sx / x in a floor, no conditional in an off arm, conditionals kept; E2's sites skipped >= 3; E3's bits of A after
B's; the manifest records `allow_conditional_neighbours` per bundle; the job within 30 s by the model. Try-build on the
2026-11-18 marrakesh record: PASS. Noiseless end to end: every d within 0.009 (2 SE 0.018).

## What is measured (`score OUT`)

Per conditional sub-item d = |s - v| - |p - v| (s its single's ff, p its ff packed, v rd2's noiseless ff computed from
the single circuit; positive: packed kept more), per bundle the mean over its conditional sub-items with 2 SE (E1: B
only; E2, E3: A and B). Beside: E1's A (fixed) against sa's off arm; per sub-item the share still failing after the
second try; the floors; the per-bit shares of A's and B's bits packed against alone.

## Verdicts

Per sub-item and per bundle, as P-B: PACKED KEEPS LESS (d <= -2 SE) / PACKED KEEPS MORE (d >= 2 SE) / SAME WITHIN
ERROR (the same words, per sub-item and per bundle).

## Reading table (fixed before the data, beside)

| E3 (bits swapped) | E2 (wider) | reading |
|---|---|---|
| A (qubits 0-3) loses, B not | A loses | the loss follows the place (qubits 0-3 or their readout), not the bit order nor nearness |
| B (bits now first) loses, A not | — | the loss follows the bit order (the register's first bits: how the controller serves conditionals) |
| neither loses | — | P-B's loss needs both A's place and A's bits first, or was the night's (P-B repeated beside would tell) |
| A loses | A does not lose | nearness: the neighbour's conditionals one site away (crosstalk) |

E1: a conditional item on B's qubits losing next to a fixed A says the loss is not tied to qubits 0-3 alone; not
losing agrees with B1 (a fixed neighbour costs nothing).

## Predictions (written before the data)

- IF-1 E3: A loses and B does not (the loss follows the place).
- IF-2 E2: A's loss remains with three sites between.
- IF-3 E1: SAME WITHIN ERROR for B.

## Known limits (stated before the data)

- One night, one device; the place and the qubits' readout cannot be told apart by these three bundles.
- E2's B sits on other qubits (7-10) than B2's B (5-8); its single sc is on the same qubits, so d compares like with
  like, but B's own quality differs from P-B's B.
- Whether the device keeps the bit order of the register in its handling of conditionals is not in IBM's public
  documents we read; E3 asks it of the data.
