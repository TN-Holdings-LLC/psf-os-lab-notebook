# Declared: does a fixed item in the register's first bits take the packing loss? (decoy test D0-D2), night of 2026-11-20

Home Claude, 2026-11-20, from the draft `prereg/drafts-2026-11-20/decoy_DRAFT.md` as the workplace finished it on the owner's
decisions of 2026-11-20 morning (workplace 20a-20c, checked by the workplace VS). Declared when the commit that adds this file is pushed,
before the night's device record is fetched; the tools are as of that commit, psf-os branch night-2026-11-20 at 61869bb (0.2.0 plus
`gap` per pair; the workplace VS's full tests 328 passed, 2 skipped for quimb). The night's two declarations are in one commit:
`decoy_night_2026-11-20.md` and `loopvar_night_2026-11-20.md`; one device record for both (decoy first, then V1, V2, V3).

Home Claude, 2026-11-19 evening (owner's choice of 2026-11-19 21:38 JST: "1 and 2" of home's list, 1 = this test).
Thresholds, words, reading table and predictions: the owner's decision of 2026-11-20 morning (below); the workplace built the tool and filled the sizes.

## Why

- 2026-11-18 P-B: of two conditional items in one circuit, A (bits first) lost -0.060 / -0.062, B did not.
- 2026-11-19 E3 (bits swapped): B (bits now first) lost -0.037 (2 SE 0.020), A did not; E2 (wider) A -0.018 inside
  2 SE (`results/interfere-night-2026-11-19`; the declared reading: the loss follows the bit order).
- Open: is it "the register's first bits" or "the first conditional item's bits"? If a fixed item placed in the first
  bits takes the place, the conditional items behind it may keep, and psf-os v0.2's "no conditional neighbours" rule
  could be relaxed to "conditional items behind a fixed first item". If A (now second) still loses, the loss belongs
  to the first conditional item, whatever stands before it.

## Design (one job, as interfere_night; rd2 = gpu/rus3_night.chain(2, 1.1, 2); Z = rd2's off arm, fixed)

| bundle | items on the chain (gap 1) | bit order | role |
|---|---|---|---|
| D0 | A rd2 [0-3], B rd2 [5-8] | A, B | control: E3 / P-B again, A expected to lose |
| D1 | A rd2 [0-3], B rd2 [5-8], Z fixed [10-13] | **Z, A, B** | the decoy's bits first, Z on the far qubits (place unchanged for A, B) |
| D2 | A rd2 [0-3], B rd2 [5-8], Z fixed [10-13] | A, B, Z | a third item present but last (separates "a third item" from "its bits first") |
| sa, sb, sz | rd2 alone on A's and B's qubits; Z alone on its qubits | - | singles, same qubits |

- Each conditional sub-item judged against its single on the same qubits, d = |s - v| - |p - v| (as interfere_night);
  Z (fixed) against sz's off arm, beside. Words as P-B / E1-E3: PACKED KEEPS LESS (d <= -2 SE),
  PACKED KEEPS MORE (d >= 2 SE), SAME WITHIN ERROR; per sub-item and per bundle (mean of its conditional sub-items).
- psf-os night-2026-11-20 at 61869bb (0.2.0 and gap per pair; `build_bundle(..., allow_conditional_neighbours=True, bit_order=...)`);
  4000 shots; rule C placement; no mitigation, DD and twirling off; check before submission as interfere_night, plus:
  Z's bits first in D1, last in D2; Z's qubits on no coupler within two steps of B.
- Size (workplace, 2026-11-20, on the 2026-11-19 marrakesh record): 3 bundles x 3 arms + 3 singles x 3 arms +
  the sentinel's 4 = 22 circuits, 27.6 s by the model. Placement: A [0, 1, 2, 3], B [5, 6, 7, 8] in every bundle
  (as E3 / P-B), Z [11, 12, 13, 14]. Tool `gpu/decoy_night.py` (build / check / score; dry for illustrative noise).
- Z's place (the owner's decision of 2026-11-20: two sites past B, `--z-gap 2`, Z [11-14]; the check stays "coupling
  distance >= 3"): the check "Z's qubits on no coupler within two steps of B" is read as a coupling distance >= 3
  (no path of one or two couplers, working or failed). With gap 1 after B (Z [10-13], as first written) the distance
  is 2 (through qubit 9) and that check fails; the tool puts Z two sites past B (`--z-gap 2`, psf-os build_bundle
  gap=[1, 2], added 2026-11-20 on psf-os night-2026-11-20, gap=[1, 1] byte-identical to gap=1): distance 3. A and B
  are also two couplers apart (through qubit 4), as on 11-18 and 11-19. If the owner reads "within two steps" as
  "no direct coupler" instead, `--z-gap 1` gives Z [10-13]; the check line is then changed to distance >= 2.
- check (workplace): independence of every bundle arm; per packed sub-item the same instructions per wire and the
  same exact distribution as its single (Z against sz's off arm); the same physical qubits; recorded acceptance;
  floors without sx / x; offs without conditionals; conditionals kept; Z without conditionals; the manifest records
  allow_conditional_neighbours; A and B on D0's qubits in D1 and D2; Z's bits first in D1 (offset 0) and last in D2;
  Z at coupling distance >= 3 from B; one job within 30 s by the model.

## Reading table (fixed before the data; the owner's decision of 2026-11-20 morning, on the workplace VS's proposal)

"loses" = PACKED KEEPS LESS for that sub-item; "keeps" = SAME WITHIN ERROR or PACKED KEEPS MORE. The table reads the
sub-items D0 A, D0 B, D1 A, D1 B, D2 A; bundle words and Z (against sz's off arm) are beside. Rows are read in the
order below; every outcome falls on exactly one row (`notes/decoy_2026-11-20/coverage_decoy.py`: 729 of 729, none on
no row, none on two). `gpu/decoy_night.py score` prints the row.

| row | D0 | D1 (Z, A, B) | D2 (A, B, Z) | reading |
|---|---|---|---|---|
| 4 | A keeps, or B loses too | - | - | the control did not repeat 11-18 / 11-19 on this night; D1, D2 not read for the mechanism |
| 2 | A loses, B keeps | A loses (B either) | A loses | the loss belongs to the first conditional item, whatever stands before it |
| 6 | A loses, B keeps | A loses (B either) | A keeps | A loses with Z first and keeps with Z last: against the order reading; not read |
| 3 | A loses, B keeps | A keeps, B loses | - | the loss moves to the conditional item that is not first (B) |
| 1 | A loses, B keeps | A and B keep | A loses | the loss sits on the register's first bits; a fixed first item shields |
| 5 | A loses, B keeps | A and B keep | A keeps | a third item present shields, wherever its bits stand |

The owner's priority "D1's A and B both lose -> row 2, B alone -> row 3" is read with D2's A losing (as row 2 was
written); with D1's A and B both losing and D2's A keeping, the outcome falls on row 6 (confirmed by the owner,
2026-11-20 09:5x JST, and by the workplace VS).

## Predictions (written before the data; the owner's decision of 2026-11-20 morning)

- DC-1 D0: A PACKED KEEPS LESS (the control repeats; basis: 2026-11-18 P-B and 2026-11-19 E3).
- DC-2 (D1) and DC-3 (D2): no direction declared; read by the table only, not counted as predictions.

## Known limits

One night, one device; sizes of -0.04 to -0.06 need about 2 SE 0.020 per sub-item (4000 shots); a control that does
not repeat leaves D1 / D2 unread for the mechanism. How IBM's controller serves conditionals in register order is not
in its public documentation and is not claimed.
