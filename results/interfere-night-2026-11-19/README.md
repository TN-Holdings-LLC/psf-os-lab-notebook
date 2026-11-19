# Where the 0.06 loss of P-B sits (interference tests E1-E3), 2026-11-19 on ibm_marrakesh (`prereg/interfere_night_2026-11-19.md`)

- Declared in be3147c7. Built on the owner's machine (`versions.txt`) from the loop's device record of the night
  (`results/loop-night-2026-11-19/fetch_in/ibm_marrakesh/dev`, calibration 10:59:49 CET); pre-run check PASS
  (`check.txt`). Job dbvct3ff8rhs73bnn73g, 22 circuits, 27.6 s by the model, 27 s charged, 11:25:17 - 11:25:51 CET.
- The score (`python gpu/interfere_night.py score .`, `score.txt`) prints numbers only; its last line still points at
  the draft for the words. The words below are the declaration's, applied by home to those numbers (d <= -2 SE PACKED
  KEEPS LESS, d >= 2 SE PACKED KEEPS MORE, otherwise SAME WITHIN ERROR; per sub-item and per bundle).

```
noiseless ff of rd2 (exact, read flipped): 0.7929; singles sa 0.7345, sb 0.7340, sc 0.5787
  e1b against sb: alone 0.7340  packed 0.7243  d -0.0097 (2 SE 0.0199)     SAME WITHIN ERROR
E1: mean d -0.0097 (2 SE 0.0199)                                            SAME WITHIN ERROR
  e2a against sa: alone 0.7345  packed 0.7163  d -0.0182 (2 SE 0.0200)     SAME WITHIN ERROR
  e2b against sc: alone 0.5787  packed 0.5762  d -0.0025 (2 SE 0.0221)     SAME WITHIN ERROR
E2: mean d -0.0104 (2 SE 0.0149)                                            SAME WITHIN ERROR
  e3a against sa: alone 0.7345  packed 0.7488  d +0.0143 (2 SE 0.0196)     SAME WITHIN ERROR
  e3b against sb: alone 0.7340  packed 0.6975  d -0.0365 (2 SE 0.0202)     PACKED KEEPS LESS
E3: mean d -0.0111 (2 SE 0.0140)                                            SAME WITHIN ERROR
beside: E1's A (fixed, rd2's off arm) packed 0.6420 against sa's off arm 0.6110 (noiseless 0.6308): d +0.0087 (2 SE 0.0216)
```

## Against the declaration

| prediction | numbers | |
|---|---|---|
| IF-1 E3: A loses and B does not (the loss follows the place) | A (qubits 0-3, bits now after B) d +0.014 SAME; B (bits now first) d -0.037 (2 SE 0.020) PACKED KEEPS LESS | failed |
| IF-2 E2: A's loss remains with three sites between | A d -0.018 (2 SE 0.020) SAME WITHIN ERROR | failed |
| IF-3 E1: SAME WITHIN ERROR for B | B d -0.010 (2 SE 0.020) | held |

## Reading (the declared table, beside)

E3's row "B (bits now first) loses, A not": the loss follows the bit order (the register's first bits: how the
controller serves conditionals), not the place. With 2026-11-18's P-B (A in the first bits lost -0.060 / -0.062,
B +0.012 / +0.004) the direction agrees on two nights: the conditional sub-item whose bits come first loses.
Limits, as stated before the data: one night, one device; the size tonight (-0.037, and E2's A -0.018 inside 2 SE)
is smaller than P-B's -0.06; E2 does not separate nearness from night-to-night variation. Whether the controller keeps
the register's bit order in serving conditionals is not in IBM's public documentation (not claimed).

## Two numbers side by side

- Vanity: one sub-item of six reads PACKED KEEPS LESS; the three bundles are SAME WITHIN ERROR.
- Essence: for anyone packing conditional items, the item placed in the register's first bits is the one at risk
  (two nights agree); psf-os v0.2 refuses such bundles by default (`allow_conditional_neighbours`), which stays right.

## Reproduce

`python reproduce.py interfere-night-2026-11-19`
