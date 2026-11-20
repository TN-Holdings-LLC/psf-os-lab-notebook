# Decoy test: the tool and its desk check (workplace Claude, 2026-11-20; not declared, no device)

Draft `prereg/drafts-2026-11-20/decoy_DRAFT.md` (words, reading table and predictions [OWNER]). Tool
`gpu/decoy_night.py` (build / check / score; dry for illustrative noise). Needs psf-os with the per-pair gap of
build_bundle (psf-os branch night-2026-11-20 on 0.2.0: `gap=[1, 2]`; `gap=[1, 1]` is byte-identical to `gap=1`,
test `test_bundle_gap_per_pair`).

## The job (one job, 22 circuits, 27.6 s by the model; `marrakesh_1119/`, the 2026-11-19 loop's record)

| bundle | items on the chain | bits | qubits |
|---|---|---|---|
| D0 | A rd2, B rd2 (gap 1) | A 0-4, B 5-9 | A [0-3], B [5-8] |
| D1 | A, B, Z = rd2's off arm (gaps 1, 2) | Z 0-4, A 5-9, B 10-14 | Z [11-14] |
| D2 | A, B, Z (gaps 1, 2) | A 0-4, B 5-9, Z 10-14 | Z [11-14] |
| singles | sa [0-3], sb [5-8], sz [11-14] | | |

check: PASS (`marrakesh_1119/check.txt`). Z sits two sites past B so that it is at coupling distance 3 from B (no
coupler within two steps, the draft's check read as distance >= 3). With `--z-gap 1` (Z [10-13], the draft's first
table) the distance is 2 and that check fails (`check_zgap1.txt`); A and B are two couplers apart too. [OWNER]

## Dry runs (`dry/`; noise files `noise/`: ILLUSTRATIVE, written by hand, never fitted)

| noise (seed) | D0 A | D0 B | D1 A | D2 A | row printed |
|---|---|---|---|---|---|
| none (7) | +0.000 SAME | +0.004 SAME | -0.002 SAME | +0.001 SAME | 4 (the control did not repeat) |
| first_bits: the part holding bit 0 pays (900000007) | -0.095 LESS | -0.002 SAME | -0.011 SAME | -0.081 LESS | 1 (the first bits; a fixed first item shields) |
| first_conditional: the first conditional part pays (900000007) | -0.095 LESS | -0.002 SAME | -0.094 LESS | -0.081 LESS | 2 (the first conditional item) |
| first_bits / first_conditional (7) | -0.083 LESS | **-0.026 LESS** | | | 4: D0's B lost by shot noise |

Each illustrative mechanism lands on its own row. With seed 7, D0's B read PACKED KEEPS LESS (-0.026, 2 SE 0.019)
without paying anything (shot noise at 2 SE, about 2 % per sub-item), and under the owner's table that voids the
night's mechanism reading (row 4). (Seed 11 repeated the same draw: Aer seeds shot by shot, so seeds 7 and 11 are
the same shots shifted by four.)

## Reading table (the owner's decision of 2026-11-20 morning)

Rows 1-6 in `gpu/decoy_night.py` (READING, reading_row) and the draft. `coverage_decoy.py` (the workplace VS's
script, rewritten for the new table; it calls the tool's own reading_row): 729 outcomes, every one on exactly one
row (row 1: 24, 2: 18, 3: 36, 4: 567, 5: 48, 6: 36), none on no row, none on two as stand-alone conditions.

## Found while building (for the owner)

- (Done, the owner's decision of 2026-11-20.) The first table had no row for "A keeps in D1 and in D2" and its
  row 3 named B; the workplace VS counted 108 of 729 outcomes on no row and 9 on two.
- Dry-run seeds: Aer seeds a circuit with mid-circuit measurements shot by shot from seed_simulator, so seeds s and
  s + 1 give the same shots shifted by one. Dry runs that seed circuit k with seed + k (psf-os run_local: seed + k,
  parts seed + 1000 k) compare nearly the same shots between circuits, and a noiseless d reads about 0 instead of
  shot noise. This tool's dry seeds with strides above the shot count (10^6 per circuit, 10^4 per part). Device runs
  are not affected.
