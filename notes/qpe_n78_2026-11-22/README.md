# Phase estimation parked, n = 7 and 8: the plans, the ceilings, the expectation, dry runs (desk, 2026-11-22 night)

Home VS Claude, on the home instruction `VSクロードへの指示_位相推定を長くする試験の準備_2026-11-22.md`.

- Draft: `prereg/drafts-2026-11-22/qpe_n78_DRAFT.md`.
- Tool: `gpu/qpe_long_parked_night.py`, on psf-os 0.3.1 as released (v0.3.1).
- Report: `VSから家へ_位相推定を長くする準備_2026-11-22.md`.
- No device.

## Contents

- `table.json`: the four plans (circuits, model seconds, 2 SE of P per n, of the acceleration, of parked − unparked);
  the exact ceilings; the phases (a_6 41, a_7 79, a_8 159); the extrapolation.
- `run.txt`: every plan built on the ibm_fez and ibm_kingston records of 2026-11-22
  (`results/likely-park-night-2026-11-22/fetch_in`), and checked: PASS on both.
  - qpe_repro_night.check passes.
  - The sample's compiled CZ mean is within 0.12 of every phase's: 11.12 / 13.12 / 15.12 against 11.00 / 13.00 / 15.00.
  - Every parked item is fenced with its target and ancilla, and every twin is unparked.
  - psf_os_build is 0.3.1 with park and park_likely stated.
  - Plan b was also dry-run under illus_a and illus_c (below). Both devices give the same numbers.

## Dry runs, plan b (ILLUSTRATIVE noise, never fitted)

| noise | parked P n = 6 / 7 / 8 | margin over C(8) | log drops | shape | parked − unparked n = 6 / 7 / 8 |
|---|---|---|---|---|---|
| illus_a (CZ 1 %, damping 2 % per read) | 0.929 / 0.916 / 0.901 | +0.70 | 0.014, 0.016 | FLAT (+0.002, 2 SE 0.008) | +0.015 / +0.019 / +0.021, all KEEPS MORE |
| illus_c (+ dephasing 12 % per conditional) | 0.631 / 0.525 / 0.432 | +0.23 | 0.183, 0.195 | FLAT (+0.012, 2 SE 0.027) | +0.180 / +0.191 / +0.178, all KEEPS MORE |

Under illus_c, a loss per conditional, the shape still reads FLAT. With the share near 0.5, the acceleration's 2 SE
(0.027 at 16 phases) is wider than the acceleration this noise gives. At n = 4-6 over every phase it read ACCELERATES
(notes/qpe_parked_2026-11-21). So the shape at n = 6-8 sees a cost per conditional only if it is large against
0.03; a limit, in the draft.
