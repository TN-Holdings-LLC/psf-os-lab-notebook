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

| noise | D0 A | D1 A | D2 A | reading printed |
|---|---|---|---|---|
| none | +0.000 SAME | -0.002 SAME | +0.001 SAME | "the control did not repeat" |
| first_bits (the part holding bit 0 pays, when two or more conditional parts share a circuit) | -0.083 LESS | -0.001 SAME | -0.074 LESS | "the loss sits on the register's first bits; a fixed first item shields" |
| first_conditional (the first conditional part pays) | -0.083 LESS | -0.083 LESS | -0.074 LESS | "the loss belongs to the first conditional item" |

Every word is reached; each illustrative mechanism lands on its own row. In both noisy runs D0's B also reads PACKED
KEEPS LESS (-0.026, 2 SE 0.019) without paying anything: shot noise at 2 SE (about one sub-item in 40 per side).

## Found while building (for the owner)

- The reading table has no row for "A keeps in D1 and in D2" (a third item present shields, whatever its bits); the
  tool prints "no row matches" then. Row 3 names B, but in D1 the item right after the first bits' owner (Z) is A.
  (The workplace VS found the same and counted 108 of 729 outcomes without a row.)
- Dry-run seeds: Aer seeds a circuit with mid-circuit measurements shot by shot from seed_simulator, so seeds s and
  s + 1 give the same shots shifted by one. Dry runs that seed circuit k with seed + k (psf-os run_local: seed + k,
  parts seed + 1000 k) compare nearly the same shots between circuits, and a noiseless d reads about 0 instead of
  shot noise. This tool's dry seeds with strides above the shot count (10^6 per circuit, 10^4 per part). Device runs
  are not affected.
