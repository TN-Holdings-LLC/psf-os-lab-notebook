# Neuron chain, third design, on ibm_kingston, 2026-11-16 (`prereg/rus_neuron3_kingston_2026-11-16.md`)

- Declaration pushed 13:22:10 CET (reflog "9d26de98 (origin/main, origin/HEAD) refs/remotes/origin/main@{2026-11-16
  13:22:10 +0100}: update by push"); queue read 13:22:27 CET: marrakesh 1, fez 138, kingston 0 -> kingston at most 10
  pending: run. Kingston record fetched 13:22:37 CET (calibration 2026-11-13 15:57 CET; failed qubits 112, 113, 121,
  146; couplers 112-113, 130-131, 145-146, 146-147) (`fetch_in/`).
- Built with `python gpu/rus3_night.py build DEVDIR OUT` (unchanged since 1c9ada0f), psf-os feedforward-2026-11-16 at
  32dc3e5 (checked on the owner's machine); chains on physical qubits 0-1, 0-3, 0-5; 22 circuits, 4000 shots, 27.6 s
  by the model; gate hash 4993730e0630 (the same as the try-build, and as the marrakesh job: the same layout on the
  same coupling graph). Pre-run check: PASS. The job returned byte-identical to the one built (the owner attached the
  result ZIP; the link to the PC had dropped).
- Job dbtfc07asvbs73b9m6cg, submitted 13:24:32 CET, ran 13:24:34-13:25:05 CET, 26 s charged. Dynamical decoupling and
  twirling off, no mitigation. Sentinel CLEAN.

## Scorer output (`python gpu/rus3_night.py score OUT`)

```
rd1: exact 0.9371; ff 0.8525 (still failed after 2 0.1130); off 0.8047; d 0.0478 (2 SE_d 0.0168) -> CLOSER WITH CONTROL; post 0.9174 (kept 0.6570); floor all zero 0.9910; sentinel CLEAN
rd2: exact 0.8782; ff 0.7490 (still failed after 2 0.1948); off 0.6375; d 0.1115 (2 SE_d 0.0205) -> CLOSER WITH CONTROL; post 0.8123 (kept 0.4555); floor all zero 0.9845; sentinel CLEAN
rd3: exact 0.8230; ff 0.6462 (still failed after 2 0.2682); off 0.5032; d 0.1430 (2 SE_d 0.0219) -> CLOSER WITH CONTROL; post 0.6669 (kept 0.3407); floor all zero 0.9825; sentinel CLEAN
flip1: exact 0.9371; ff 0.8260 (still failed after 2 0.1140); off 0.7665; d 0.0595 (2 SE_d 0.0180) -> beside (CLOSER WITH CONTROL); post 0.8486 (kept 0.6770); floor all zero 0.9915; sentinel CLEAN
flip2: exact 0.8782; ff 0.7047 (still failed after 2 0.1965); off 0.6178; d 0.0870 (2 SE_d 0.0211) -> beside (CLOSER WITH CONTROL); post 0.7495 (kept 0.4770); floor all zero 0.9832; sentinel CLEAN
flip3: exact 0.8230; ff 0.6340 (still failed after 2 0.2682); off 0.5208; d 0.1132 (2 SE_d 0.0219) -> beside (CLOSER WITH CONTROL); post 0.6765 (kept 0.3485); floor all zero 0.9795; sentinel CLEAN
L 1: ff error read back -0.1111, read flipped -0.0846; gain +0.0265 (2 SE 0.0164)
L 2: ff error read back -0.1734, read flipped -0.1292; gain +0.0443 (2 SE 0.0199)
L 3: ff error read back -0.1890, read flipped -0.1767; gain +0.0122 (2 SE 0.0215)
predictions: {'1 L = 1: read gain positive and >= 2 SE': 'held', '2 L = 1, 2, 3 (rd): CLOSER WITH CONTROL': 'held'}
```

The "predictions" line is the marrakesh declaration's; for this run only the verdicts and the one prediction below
are judged (as declared).

## Against the declaration

| | numbers | |
|---|---|---|
| verdict L = 1 (rd) | d 0.0478, 2 SE_d 0.0168 | CLOSER WITH CONTROL |
| verdict L = 2 (rd) | d 0.1115, 2 SE_d 0.0205 | CLOSER WITH CONTROL |
| verdict L = 3 (rd) | d 0.1430, 2 SE_d 0.0219 | CLOSER WITH CONTROL |
| prediction 1: CLOSER at L = 1, 2, 3 | | held |

Two numbers side by side: the verdict holds at every L on a second device; ff against the noiseless value of the same
circuit (0.892 / 0.792 / 0.708) is -0.039 / -0.043 / -0.062, against the exact value -0.085 / -0.129 / -0.177.

## Beside, never judged

| L | exact | marrakesh rd (13:15) | kingston rd (13:24) | marrakesh flip | kingston flip | noiseless m = 2 |
|---|---|---|---|---|---|---|
| 1 | 0.937 | 0.883 | 0.853 | 0.666 | 0.826 | 0.892 |
| 2 | 0.878 | 0.740 | 0.749 | 0.741 | 0.705 | 0.792 |
| 3 | 0.823 | 0.631 | 0.646 | 0.642 | 0.634 | 0.708 |

Read gain on kingston: +0.027 / +0.044 / +0.012 (2 SE 0.016 / 0.020 / 0.022), against +0.217 / -0.001 / -0.011 on
marrakesh: on kingston no single qubit's readout dominates, and reading flipped helps a little at L = 1 and 2.

## Reading (an interpretation beside the declaration, not a judgement)

- The third design carries to a second device: CLOSER WITH CONTROL at every L, with the device's own loss 0.04-0.06
  (marrakesh 0.01-0.08). What remains between ff and the exact value is mostly the noiseless cost of m = 2.
- Kingston's sentinel was CLEAN (as in its daily line of the same day); marrakesh's was DEAD all night.

## Files

`job/`, `runs/`, `build.json`, `rus3_scores.json` (the scorer's output), `fetch_in/`.

## Reproduce

`python reproduce.py --psf-os PATH_TO_PSF_OS_AT_feedforward-2026-11-16 rus-neuron3-kingston-2026-11-16` (SAME,
2026-11-16).
