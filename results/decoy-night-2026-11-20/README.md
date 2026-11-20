# Does a fixed item in the register's first bits take the packing loss? (decoy D0-D2), 2026-11-20 on ibm_marrakesh (`prereg/decoy_night_2026-11-20.md`)

- Declared in ecde2114, pushed by the owner before the night's fetch (GitHub main 3c33b08e..b9c7f01a; the fetch at
  11:38:14 CET). Built on the owner's machine (`versions.txt`: Python 3.12.13, qiskit 2.5.2, aer 0.17.2, runtime
  0.49.0, numpy 2.5.3) with psf-os night-2026-11-20 at 61869bb from the night's record (`fetch_in/`: queue marrakesh 0,
  fez 3, kingston 0 -> ibm_marrakesh; calibration 2026-11-19 23:09:26+01:00). Pre-run check PASS (`check.txt`): A
  [0-3], B [5-8], Z [11-14] (coupling distance 3 from B); Z's bits first in D1 and last in D2.
- Job dc026jinj2vs73ddbbdg, 22 circuits, 4000 shots, 27.6 s by the model, 27 s charged, 11:39:10 - 11:39:44 CET.
- `python gpu/decoy_night.py score .` (`score.txt`, `decoy_scores.json`):

```
noiseless ff of rd2 (exact, read flipped): 0.7929; off 0.6308; singles sa 0.7492, sb 0.5813, sz 0.7312
  d0a against sa: alone 0.7492  packed 0.6927  d -0.0565 (2 SE 0.0200) -> PACKED KEEPS LESS
  d0b against sb: alone 0.5813  packed 0.5958  d +0.0145 (2 SE 0.0220) -> SAME WITHIN ERROR
  d1a against sa: alone 0.7492  packed 0.6925  d -0.0567 (2 SE 0.0200) -> PACKED KEEPS LESS
  d1b against sb: alone 0.5813  packed 0.5842  d +0.0030 (2 SE 0.0221) -> SAME WITHIN ERROR
  d2a against sa: alone 0.7492  packed 0.6643  d -0.0850 (2 SE 0.0203) -> PACKED KEEPS LESS
  d2b against sb: alone 0.5813  packed 0.6028  d +0.0215 (2 SE 0.0220) -> SAME WITHIN ERROR
  beside: Z (fixed) against sz's off arm: D1 d -0.0200, D2 d -0.0208 (2 SE 0.0214)
bundles (beside): D0 -0.0210, D1 -0.0269, D2 -0.0318 (2 SE 0.0149), PACKED KEEPS LESS
reading: row 2: the loss belongs to the first conditional item, whatever stands before it
```

## Against the declaration

| prediction | numbers | |
|---|---|---|
| DC-1 D0: A PACKED KEEPS LESS (the control repeats) | -0.0565 (2 SE 0.0200) | held |
| DC-2 D1, DC-3 D2: no direction declared | D1 A -0.057, D2 A -0.085: read by the table | read, not predictions |

## Reading

Row 2 of the declared table: a fixed item in the register's first bits (D1) did not shield A, which lost as much as in
the control (-0.057 both); with Z last (D2) A lost more (-0.085). On three nights now (11-18 P-B, 11-19 E3, 11-20 D0-D2)
the conditional sub-item whose bits come first among the conditional items lost, the one behind it did not. psf-os's
default refusal of conditional neighbours stays; the receiver `behind_fixed_first` (psf-os after-2026-11-20) is not
used. One device; whether the controller's service order is the cause is not in IBM's public documentation and is not
claimed.

## Two numbers side by side

- Vanity: the control repeated (A -0.057, 2.8 x 2 SE) and the decoy changed nothing.
- Essence: for anyone packing conditional items: the first conditional item loses about 0.06 whatever is put in front
  of it; keep conditional items in separate circuits (psf-os's default).

## Reproduce

`python reproduce.py decoy-night-2026-11-20`

## Independent check (home VS, 2026-11-20)

Re-counted from `job/raw_counts.json` with qiskit, aer and numpy only (no psf-os, no notebook scorer;
`notes/verify_2026-11-20/decoy_indep.py`): the six conditional sub-items (alone, packed, d, 2 SE), Z's beside values
and the bundle means agree; the table read in the declared order gives row 2; DC-1 held; 22 circuits, 4000 shots, the
qubits, Z's bit positions and its coupling distance 3 as declared; reproduce SAME.
