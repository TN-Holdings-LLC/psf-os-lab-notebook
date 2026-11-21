# Phase estimation at n = 4, 5, 6 parked: the plans, their seconds, dry runs (desk, 2026-11-21)

Home VS Claude, on the home instruction `VSクロードへの指示_psf-os_0.3.0の追加_2026-11-21.md`, part C. The draft is
`prereg/drafts-2026-11-21/qpe_parked_DRAFT.md`. The tool is `gpu/qpe_parked_night.py`, which needs psf-os
release-0.3.0 (`park_skip`, `ff_only`). No device.

- `table.txt`, `table.json`: the plans and their model seconds, with the 2 SE estimates (the weekend's unparked
  shares, parked +0.03). The formula's shots are 100 per circuit.
- `dry/<plan>_<noise>/`: every plan built on the 2026-11-21 marrakesh record with the dry Clifford sentinel.
  `check.txt` holds `qpe_repro_night.check` (PASS on every job) and the park records (as meant). `score.txt` holds the
  scores under ILLUSTRATIVE noise a (`illus_a`) and c (`illus_c`). `run.txt` is the whole run.

| plan | s | d_n under noise a (n = 4 / 5 / 6) | d_n under noise c | parked shape a / c |
|---|---|---|---|---|
| parked | 73.6 | — | — | FLAT / ACCELERATES |
| both | 141.8 | +0.010 / +0.014 / +0.019, all KEEPS MORE | +0.090 / +0.126 / +0.161, all KEEPS MORE | FLAT / ACCELERATES |
| subset | 87.0 | +0.008 / +0.016 / +0.016, all KEEPS MORE | +0.088 / +0.130 / +0.146, all KEEPS MORE | FLAT / ACCELERATES |
| formula (100 shots) | 17.4 | +0.014 SAME / +0.011 SAME / +0.021 KEEPS MORE | +0.10 / +0.12 / +0.15, all KEEPS MORE | FLAT / FLAT (2 SE 0.05) |

The formula is sized for d = 0.03, the size of the device's C. The illustrative noise a gains only about 0.01, so it is
not seen at n = 4 and 5 with 100 shots.
