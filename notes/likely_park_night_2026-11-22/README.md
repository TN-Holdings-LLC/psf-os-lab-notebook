# psf-os 0.3.1's candidate (park_likely, MP) prepared for a device night (desk, 2026-11-22)

Home VS Claude, on the home instruction `VSクロードへの指示_0.3.1候補の実機試験の準備_2026-11-22.md`.

- Draft: `prereg/drafts-2026-11-22/likely_park_DRAFT.md`.
- Tool: `gpu/likely_park_night.py`.
- psf-os: likely-park-2026-11-22 at version 0.3.1 (candidate).
- Report: `VSから家へ_0.3.1候補の準備_2026-11-22.md`.
- No device.

## Contents

- `table.json`: plan B, 68 circuits and 41.2 s by the model (A: 44, 27.8 s).
- `run.txt`: plan B on the ibm_fez and ibm_kingston records of 2026-11-21 (`results/rus-fence-night-2026-11-21/fetch_in`).
  It holds the build, the check (PASS on both) and the dry runs under the three ILLUSTRATIVE noises of
  gpu/rus_fence_night.py. The two devices give the same numbers: rule C places the items alike.

## L − D (g, nearer to exact is better)

| noise | NF m3 L3 | P0 L3 | P3 L3 | IPE control | the rule's row |
|---|---|---|---|---|---|
| wait (damping per read; the type the fez night read) | +0.265 KEEPS MORE | +0.014 KEEPS MORE | +0.016 KEEPS MORE | +0.040 MORE | the default |
| cond (dephasing per conditional) | +0.010 SAME | +0.002 SAME | +0.002 SAME | +0.047 MORE | opt-in (no item MORE) |
| phase (a coherent phase while reading) | +0.006 SAME | +0.030 KEEPS MORE* | +0.022 KEEPS MORE* | +0.019 MORE | the default* |

(*) Under the coherent phase, D overshoots exact on P0: P 0.871 against exact 0.823. L's lower P (0.841) is nearer
exact, so g reads KEEPS MORE although L keeps no more in any direct sense. This comes from reading |P − exact|, not from
parking. A device night whose D reads above exact would carry the same artifact; the draft lists it among the limits.
