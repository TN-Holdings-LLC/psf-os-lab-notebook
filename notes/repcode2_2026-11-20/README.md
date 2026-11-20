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
adjacent a parity costs 3, with the data apart the encoding costs 3 per link. The line of five fits any rule-C chain
(no degree-3 site needed; placement unchanged, [0-4] on the 2026-11-19 record). **Correction (the workplace VS,
2026-11-20): 10 is not the least.** The argument assumed the code is kept while its syndrome is measured; undoing
the encoding first leaves the syndrome on d1, d2, and one CX each copies it to the ancillas: 2 + 2 + 2 = 6 (below).

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

## Addendum: without the two reset conditionals (2026-11-20, after the owner asked whether improvement can reach it)

In this arrangement the ancillas are not used after their measurement (the decoding runs on the data alone), so the
two conditional-X resets do nothing for the answer; `no_resets.py` (desk only) drops them in every arm: lut3 holds 3
conditionals instead of 5 (lut1 1, lut5 5). Noiselessly the same: c = 000 for every ff item, ceiling 0.8750.

| noise | 2026-11-19 arrangement | fewer CZ | fewer CZ, no resets | loss ratio to 2026-11-19 |
|---|---|---|---|---|
| a (per gate and read) | 0.920 | 0.944 | 0.944 | 0.70 |
| c (+ 5 % dephasing per conditional) | 0.813 NOT BEYOND | 0.869 NOT BEYOND | **0.888 BEYOND (+0.013)** | 0.60 |

Carried over to 11-19's 0.812 (not a fit): x 0.70 gives about 0.87, x 0.60 about 0.89, against the 0.881 needed.
So reaching the ceiling is possible only if the device's loss is like noise c (a cost per conditional, which the
resets add), and then by a thin margin. Dropping the resets changes a property of the 2026-11-19 design ("both
versions hold the two reset conditionals") and the conditional counts the (b) comparison was built on: the owner's
decision, not made here.

## The workplace VS's check (2026-11-20, the VS's return `繰り返し符号の組み方/`, in the take-home 20d)

- Noiselessly the same as 2026-11-19 in all 36 item arms (c[0] within 4e-15; the relabeling c2 = c1 xor c2 is the
  only one that matches); ceiling 0.875; CZ recounted by other means (logical 16 -> 10, compiled 14-16 -> 8-10).
- Three seeds per noise: the loss ratio of this arrangement to 2026-11-19's is 0.675 (0.66-0.69) under noise a and
  0.703 (0.69-0.71) under noise c: the 0.70 does not move with the seed.
- **Six CZ** (the VS's sketch `repcode6_vs.py`, not in this notebook): encode 2, (error), undo 2, copy the syndrome
  from d1, d2 to the ancillas 2; the same line, ancillas, three register tests and two resets. Noiselessly the same
  distributions and ceiling as 2026-11-19. Illustrative noise: lut3 0.981 (a) and 0.967 (c), loss 0.23 and 0.18 of
  2026-11-19's. The VS's reading: in the 10- and 16-CZ forms the logical state is spread over three qubits during the
  conditional wait, and the wait's dephasing acts about three times; here d0 alone holds it. But the code is undone
  before the look-up (the correction acts on d0 alone): whether that is "the same test" is home's and the owner's.
- **The compiler cancels CX pairs with no error X between them.** In the declared 2026-11-19 circuits the items other
  than error 0 went 16 -> 14 CZ (the items are not equally heavy; worth one line in the record or the paper). In the
  six-CZ form the no-error item compiles to 2 CZ (the code vanishes), error 1 to 4, errors 0 and 2 to 6; keeping six
  needs something that stops the cancellation (a barrier; whether psf-os's build keeps barriers is not checked). The
  error-0 item (6 CZ, nothing cancelled) still reads 0.966 under noise c.
