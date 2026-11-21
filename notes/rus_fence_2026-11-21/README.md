# The RUS chains' fence and parking the likely value: the device test prepared (desk, 2026-11-21 night)

Home VS Claude, on the home instruction `VSクロードへの指示_RUSの鎖の柵の実機試験の準備_2026-11-21.md` and its additions
1 and 2. The draft is `prereg/drafts-2026-11-21/rus_fence_DRAFT.md`, the tool `gpu/rus_fence_night.py` (psf-os 0.3.0
as released). The report is `VSから家へ_RUSの柵の準備_2026-11-21.md`. No device.

- `table.json`: the three plans' circuits and model seconds (alpha 36.8 s; beta 70.8 s in two jobs; gamma 50.2 s).
- `alloc.py`, `alloc.txt`: copies per form for a smallest difference worth taking (80 % power at 2 SE).
- `expect.py`, `expect.txt`, `expect.json`: per RUS item, under the three ILLUSTRATIVE noises, the fence (F − D) and
  parking (M − F). Also the excited count while waiting as compiled, per form (kingston record; record only).
- `dry/`: every plan built on the ibm_fez and ibm_kingston records of 2026-11-21 (`results/qpe-parked-night-2026-11-21/
  fetch_in/`):
  - `build_check.txt`: check PASS on every job of every plan on both. The three forms' compiled distributions and CZ
    are equal; the fences and M's X survive compiling; the controls' own checks pass; psf_os_build is 0.3.0 /
    park True / explicit.
  - `<device>_alpha_<noise>.txt`: plan alpha dry-run and scored under each noise. The two devices give the same numbers:
    rule C places the items alike, so the compacted circuits are the same.

| noise | P0 fence | NF parking | row of the reading table | P2 fence | IPE control | repetition code |
|---|---|---|---|---|---|---|
| wait (damping per read) | −0.053 KEEPS LESS | +0.319 KEEPS MORE | 1 (damping) | +0.053 KEEPS MORE | +0.032 KEEPS MORE | footprint +0.035 MORE, CZ SAME |
| cond (dephasing per conditional) | +0.048 KEEPS MORE | +0.010 SAME | 2 (dephasing) | +0.048 KEEPS MORE | +0.039 KEEPS MORE | footprint +0.111 MORE, CZ SAME |
| phase (coherent, while reading) | −0.000 SAME | −0.034 KEEPS LESS | 3 (coherent phase) | +0.010 SAME | +0.015 KEEPS MORE | footprint +0.013 MORE, CZ SAME |

Each noise type lands on its own row.
