# The 2026-11-19 repetition code: CZ per item as written and as compiled (a note for the record; `results/` unchanged)

Workplace Claude, 2026-11-20, from the workplace VS's finding of the same day. Read from the record's own run files
(`results/repcode-night-2026-11-19/runs/ff_*.json`: `logical_cz` as written, `cz` as compiled and sent).

| item | conditionals | CZ written | CZ sent (ff, off, floor alike) |
|---|---|---|---|
| lut1_0, lut3_0, lut5_0 (error on d0) | 3, 5, 7 | 16 | 16 |
| lut1/lut3/lut5 _n, _1, _2 (no error, error on d1, on d2) | 3, 5, 7 | 16 | **14** |

Why: the encoding's last CX(d0, a0) (returning a0 to 0) and the parity's first CX(d0, a0) stand next to each other
once the other link's gates (on d1, a1, d2) are commuted past; the compiler (preset pass manager, level 1) cancels the
pair unless an X on d0 (the injected error on d0) stands between them. The sent circuits are equivalent to the written
ones (noiselessly the same distributions; the check of 11-19 passed on them), but the items are not equally heavy:
the error-on-d0 item, the one item whose ceiling is 1/2 and which makes the margin over C, carried 2 CZ more than
the other three. Device shares of lut3 (`score.txt`): no error 0.765, d0 0.847, d1 0.839, d2 0.797: the heavier item
was not the lowest.

What it changes: no verdict (every item was compared with its own off arm and floor, compiled alike, and the
ceiling is a noiseless number). The pooled lut3 mixes items of 14 and 16 CZ, which a sentence in the record or the
paper can say. From 2026-11-20 on, psf-os after-2026-11-20 can refuse a build whose compiled CZ differ from the
written ones (`strict_cz`), and the four-form test (`gpu/repcode4_night.py`) puts a barrier after the error so that
nothing is cancelled.
