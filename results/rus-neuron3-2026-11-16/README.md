# Repeat-until-success neuron chain, third design, 2026-11-16 (ibm_marrakesh) (`prereg/rus_neuron3_2026-11-16.md`)

- Declaration pushed 13:11:13 CET (reflog "1c9ada0f (origin/main, origin/HEAD) refs/remotes/origin/main@{2026-11-16
  13:11:13 +0100}: update by push"); queue read 13:11:29 CET: marrakesh 1, fez 130, kingston 2 -> ibm_marrakesh.
  Device record fetched 13:11:35 CET (calibration 2026-11-13 18:22 CET; failed qubits 82, 94, 113, 119, 130, coupler
  113-119) (`fetch_in/`).
- Built with `python gpu/rus3_night.py build DEVDIR OUT` (the tool unchanged since 1c9ada0f), psf-os
  feedforward-2026-11-16 at 32dc3e5 (checked on the owner's machine); chains on physical qubits 0-1, 0-3, 0-5; 22
  circuits, 4000 shots, 27.6 s by the model; gate hash 4993730e0630, the same as the try-build. Pre-run check: PASS.
  The job returned byte-identical to the one built.
- Job dbtf7ihvvpic738mtee0, submitted 13:15:06 CET, ran 13:15:08-13:15:41 CET, 27 s charged. Dynamical decoupling and
  twirling off, no mitigation. Sentinel DEAD.

## Scorer output (`python gpu/rus3_night.py score OUT`)

```
rd1: exact 0.9371; ff 0.8832 (still failed after 2 0.1170); off 0.8453; d 0.0380 (2 SE_d 0.0153) -> CLOSER WITH CONTROL; post 0.9426 (kept 0.6750); floor all zero 0.9970; sentinel DEAD
rd2: exact 0.8782; ff 0.7398 (still failed after 2 0.2110); off 0.6550; d 0.0847 (2 SE_d 0.0205) -> CLOSER WITH CONTROL; post 0.8454 (kept 0.4545); floor all zero 0.9785; sentinel DEAD
rd3: exact 0.8230; ff 0.6307 (still failed after 2 0.2968); off 0.5395; d 0.0912 (2 SE_d 0.0219) -> CLOSER WITH CONTROL; post 0.7107 (kept 0.3352); floor all zero 0.9627; sentinel DEAD
flip1: exact 0.9371; ff 0.6663 (still failed after 2 0.1040); off 0.6338; d 0.0325 (2 SE_d 0.0213) -> beside (CLOSER WITH CONTROL); post 0.7186 (kept 0.6857); floor all zero 0.9962; sentinel DEAD
flip2: exact 0.8782; ff 0.7410 (still failed after 2 0.2200); off 0.6472; d 0.0938 (2 SE_d 0.0205) -> beside (CLOSER WITH CONTROL); post 0.8079 (kept 0.4645); floor all zero 0.9830; sentinel DEAD
flip3: exact 0.8230; ff 0.6420 (still failed after 2 0.2875); off 0.5317; d 0.1103 (2 SE_d 0.0219) -> beside (CLOSER WITH CONTROL); post 0.6922 (kept 0.3257); floor all zero 0.9623; sentinel DEAD
L 1: ff error read back -0.2709, read flipped -0.0539; gain +0.2170 (2 SE 0.0180)
L 2: ff error read back -0.1372, read flipped -0.1384; gain -0.0012 (2 SE 0.0196)
L 3: ff error read back -0.1810, read flipped -0.1922; gain -0.0113 (2 SE 0.0215)
predictions: {'1 L = 1: read gain positive and >= 2 SE': 'held', '2 L = 1, 2, 3 (rd): CLOSER WITH CONTROL': 'held'}
```

The rd values are read with the declared relabelling of the last bit (1 - bit); every shot of ff and off counted.

## Against the declaration

| | numbers | |
|---|---|---|
| verdict L = 1 (rd) | d 0.0380, 2 SE_d 0.0153 | CLOSER WITH CONTROL |
| verdict L = 2 (rd) | d 0.0847, 2 SE_d 0.0205 | CLOSER WITH CONTROL |
| verdict L = 3 (rd) | d 0.0912, 2 SE_d 0.0219 | CLOSER WITH CONTROL |
| prediction 1: read gain at L = 1 >= 2 SE | +0.217, 2 SE 0.018 | held |
| prediction 2: CLOSER at L = 1, 2, 3 | | held |

Two numbers side by side: the verdict holds at every L; ff against the noiseless value of the same circuit (m = 2:
0.892 / 0.792 / 0.708) is -0.009 / -0.052 / -0.077, and against the exact value -0.054 / -0.138 / -0.192 (the rest is
the shots still failing after 2 tries).

## Beside, never judged

ff P(last output 1) on the same chains, the same night (other jobs except the last two columns):

| L | exact | first design (m = 3) | second design (12:58) | second design again (flip, 13:15) | third design (rd, 13:15) | noiseless m = 2 |
|---|---|---|---|---|---|---|
| 1 | 0.937 | 0.599 | 0.672 | 0.666 | 0.883 | 0.892 |
| 2 | 0.878 | 0.629 | 0.734 | 0.741 | 0.740 | 0.792 |
| 3 | 0.823 | 0.551 | 0.626 | 0.642 | 0.631 | 0.708 |

The flip items repeat the second design within 2 SE at every L (17 minutes apart).

## Reading (an interpretation beside the declaration, not a judgement)

- At L = 1 reading flipped removes almost all of the device loss: ff 0.883 against 0.892 noiseless. What was left
  there after the second design was the final readout of |1> on physical qubit 1; its |0> reads cleanly.
- At L = 2 and 3 (outputs on qubits 3 and 5, whose readout of |1> is good) reading flipped changes nothing beyond
  2 SE, as expected. The device loss there stays 0.05-0.08; the larger part of the remaining distance to the exact
  value is the noiseless cost of m = 2 (0.04 / 0.09 / 0.11).
- The night's sequence, each step declared before its data: first design (control fires, value lost) -> wait
  diagnostic (unfired conditionals free; neighbour measurements costly on qubit 1) -> control diagnostic (the loss is
  time, toward |0>) -> second design (hold the likely value as |0> during waits: +0.11 to +0.18) -> third design (read
  it as |0> too: +0.22 at L = 1).

## Files

`job/`, `runs/`, `build.json`, `rus3_scores.json` (the scorer's output), `fetch_in/`.

## Reproduce

`python reproduce.py --psf-os PATH_TO_PSF_OS_AT_feedforward-2026-11-16 rus-neuron3-2026-11-16` (SAME, 2026-11-16).
