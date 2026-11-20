# The repetition code with fewer CZ: a desk estimate (workplace Claude, 2026-11-20; not for the night, not declared)

Home's added instruction of 2026-11-20. Tool `gpu/repcode2_night.py` (draft): gpu/repcode_night.py (declared for
2026-11-19) read only, with another arrangement swapped in; the test (four error items, T then readout, the ceiling,
the pooling) is unchanged.

## Where the CZ go, and the arrangement by formula

| step | 2026-11-19, line d0 a0 d1 a1 d2 | here, line a0 d1 d0 d2 a1 |
|---|---|---|
| encode | 6 (each link through an ancilla, 3 CX) | 2 (d0 next to both) |
| parity | 4 (each ancilla next to both data of its pair) | 6 (3 per pair, through the datum next to the ancilla) |
| decode | 6 | 2 |
| logical total | 16 | 10 |
| compiled per item (lut1 / lut3 / lut5, ff) | 14-16 | 8-10 |
| depth (compiled) | 53-58 | 31-37 |
| conditionals (lut3 / lut1 / lut5), circuits, seconds | 5 / 3 / 7; 40 circuits; 47.6 s | the same |

Heavy-hex is bipartite (no triangles), so no ancilla can neighbour both data of an adjacent pair: with the data
adjacent a parity costs 3, with the data apart the encoding costs 3 per link. 10 is the smaller of the two; the line
of five fits any rule-C chain (no degree-3 site needed; placement unchanged, [0-4] on the 2026-11-19 record).

## Checks

- Noiseless: every ff item c = 000; the ceiling 0.8750 (`ideal.txt`); check PASS on the 2026-11-19 marrakesh record
  (`check_marrakesh_1119.txt`).
- Against the 2026-11-19 arrangement, per item and arm, exact (`same.txt`): c[0] the same; the check bits are
  decoded against d0 here (c1 = d0 + d1, c2 = d0 + d2) and along the line there (c2 = d1 + d2), so 2026-11-19's c2
  is c1 + c2 here; after that relabeling every distribution is the same (total variation <= 1e-15). The syndromes
  differ by definition (s1 = d0 + d2 here), and the table reads s == 3 -> X d0, s == 1 -> X d1, s == 2 -> X d2.

## Illustrative noise (notes/repcode_2026-11-19/noise; written by hand, never fitted), lut3 pooled

| noise | 2026-11-19 arrangement | here | loss (1 - p) ratio here / there |
|---|---|---|---|
| a: CZ 1 %, damping 2 % per read | 0.920 BEYOND | 0.944 BEYOND | 0.70 |
| c: CZ 0.2 %, damping 2 %, dephasing 5 % per conditional | 0.813 NOT BEYOND | 0.869 NOT BEYOND (-0.006) | 0.70 |
| f: 50 % dephasing per fired conditional (extreme) | 0.646 | 0.723 | 0.78 |

## Reading, and where it stops (the instruction's stop rule)

The device's 11-19 lut3 was 0.812 (loss 0.188); beyond the ceiling needs about 0.881 (0.875 + 2 SE), a loss near
0.12, i.e. 0.64 of 11-19's. Both milder illustrative noises cut the loss to 0.70 of the old arrangement's; carried
over to 0.812 that is about 0.87, short of 0.88 (a carry-over, not a fit; no noise here is the device's). By the
instruction ("no prospect of 0.88 -> stop, numbers only"), this stops here. What it does show: fewer CZ (16 -> 10)
and depth (55 -> 34) buy about 30 % of the loss under noises that cost per gate and per wait; the conditional count
is unchanged, and a cost per conditional (noise c) keeps the new arrangement just under the ceiling.
