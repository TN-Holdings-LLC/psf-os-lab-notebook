# Interference tests: the tool and its desk check (home VS Claude, 2026-11-18 evening; not declared, no device)

Home instruction "試作3点", part A. Tool `gpu/interfere_night.py`; draft `prereg/drafts-2026-11-19/interfere_DRAFT.md`
(predictions, words and reading table marked [OWNER]). psf-os branch v0.2-proto-2026-11-18: `build_bundle` gained
`gap` (sites skipped between items, default 1) and `bit_order` (the sub-items' order in the register, default the items'
order); at their defaults every bundle is byte-identical to before (test `test_bundle_gap_and_bit_order`; tonight's jobs
rebuilt byte for byte, `notes/v02_2026-11-18/rebuild_check.txt`).

## The job (one job, 22 circuits, 27.6 s by the model)

| bundle | A | B | sites between | bits | on the 2026-11-18 marrakesh record |
|---|---|---|---|---|---|
| E1 | rd2's off arm (fixed) | rd2 | 1 | A then B | A [0, 1, 2, 3], B [5, 6, 7, 8] |
| E2 | rd2 | rd2 | 3 | A then B | A [0, 1, 2, 3], B [7, 8, 9, 10] |
| E3 | rd2 | rd2 | 1 | **B then A** | A [0, 1, 2, 3] (bits 5-9), B [5, 6, 7, 8] (bits 0-4) |
| singles | sa on A, sb on B, sc on E2's B | | | | |

Every bundle is built with `allow_conditional_neighbours=True`; the job's manifest records, per bundle, the flag, the
conditionals per item, the gap and the bit order (`interfere_bundles`).

## Desk check (`marrakesh_1118/`: plan.json, check.txt, score.txt, interfere_scores.json)

- check on the 2026-11-18 marrakesh record (`results/parallel-night-2026-11-18/fetch_in/ibm_marrakesh/dev`): PASS
  (independence; per sub-item the same instructions per wire and exact distribution as its single, total variation 0;
  the same qubits; acceptance; floors without sx / x; offs without conditionals; conditionals kept; E2 three sites
  skipped; E3 A's bits after B's; the flag recorded).
- Noiseless end to end (run_local, score): rd2's noiseless ff 0.7929; d e1b +0.0090, e2a -0.0002, e2b +0.0088, e3a
  +0.0088, e3b +0.0000 (2 SE 0.018 each); E1's fixed A against sa's off arm -0.0021 (2 SE 0.022). Shot noise of two
  noiseless samplings only (the exact distributions are equal).
