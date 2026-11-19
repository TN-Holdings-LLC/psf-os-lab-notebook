# DRAFT (not declared): does a fixed item in the register's first bits take the packing loss? (night of 2026-11-20)

Home Claude, 2026-11-19 evening (owner's choice of 2026-11-19 21:38 JST: "1 and 2" of home's list, 1 = this test).
Thresholds, words and predictions marked [OWNER] are the owner's; the workplace builds the tool and fills the sizes.

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
  Z (fixed) against sz's off arm, beside. Words as P-B / E1-E3 [OWNER]: PACKED KEEPS LESS (d <= -2 SE),
  PACKED KEEPS MORE (d >= 2 SE), SAME WITHIN ERROR; per sub-item and per bundle (mean of its conditional sub-items).
- psf-os v0.2 at the commit of the night (`build_bundle(..., allow_conditional_neighbours=True, bit_order=...)`);
  4000 shots; rule C placement; no mitigation, DD and twirling off; check before submission as interfere_night, plus:
  Z's bits first in D1, last in D2; Z's qubits on no coupler within two steps of B.
- Size (workplace, 2026-11-20, on the 2026-11-19 marrakesh record): 3 bundles x 3 arms + 3 singles x 3 arms +
  the sentinel's 4 = 22 circuits, 27.6 s by the model. Placement: A [0, 1, 2, 3], B [5, 6, 7, 8] in every bundle
  (as E3 / P-B), Z [11, 12, 13, 14]. Tool `gpu/decoy_night.py` (build / check / score; dry for illustrative noise).
- Z's place [OWNER]: the check "Z's qubits on no coupler within two steps of B" is read as a coupling distance >= 3
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

## Reading table (fixed before the data) [OWNER]

| D0 (control) | D1 (Z first) | D2 (Z last) | reading |
|---|---|---|---|
| A loses | A and B keep | A loses | the loss sits on the register's first bits; a fixed first item shields |
| A loses | A loses | A loses | the loss belongs to the first conditional item, whatever stands before it |
| A loses | B loses | - | the loss moves to the item right after the first bits' owner (order, not first place) |
| A does not lose | - | - | the control did not repeat 11-18 / 11-19 on this night; D1, D2 not read for the mechanism |

## Predictions [OWNER] (written before the data)

- DC-1 D0: A PACKED KEEPS LESS (the control repeats). [OWNER]
- DC-2 D1: A SAME WITHIN ERROR (a fixed first item shields). [OWNER: direction or none]
- DC-3 D2: A PACKED KEEPS LESS. [OWNER: direction or none]

## Known limits

One night, one device; sizes of -0.04 to -0.06 need about 2 SE 0.020 per sub-item (4000 shots); a control that does
not repeat leaves D1 / D2 unread for the mechanism. How IBM's controller serves conditionals in register order is not
in its public documentation and is not claimed.
