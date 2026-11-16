# Repeat-until-success neuron chain, second design, 2026-11-16 (ibm_marrakesh) (`prereg/rus_neuron2_2026-11-16.md`)

- Declaration pushed 12:55:21 CET (reflog "e2407c6c (origin/main, origin/HEAD) refs/remotes/origin/main@{2026-11-16
  12:55:21 +0100}: update by push"); queue read 12:55:45 CET: marrakesh 4, fez 130, kingston 0 -> ibm_marrakesh.
  Device record fetched 12:55:51 CET (calibration 2026-11-13 18:22 CET; failed qubits 82, 94, 113, 119, 130, coupler
  113-119) (`fetch_in/`).
- Built with `python gpu/rus2_night.py build DEVDIR OUT` (the tool unchanged since e2407c6c), psf-os
  feedforward-2026-11-16 at 32dc3e5 (checked on the owner's machine); chains on physical qubits 0-1, 0-3, 0-5; 22
  circuits, 4000 shots, 27.6 s by the model; gate hash 86306c83e464, the same as the try-build. Pre-run check: PASS.
  The job returned byte-identical to the one built.
- Job dbtevhjeq3sc73evnv3g, submitted 12:57:59 CET, ran 12:58:00-12:58:33 CET, 27 s charged. Dynamical decoupling and
  twirling off, no mitigation. Sentinel DEAD.

## Scorer output (`python gpu/rus2_night.py score OUT`)

```
flip1: exact 0.9371; ff 0.6717 (still failed after 2 0.1105); off 0.6292; d 0.0425 (2 SE_d 0.0213) -> CLOSER WITH CONTROL; post 0.7097 (kept 0.6907); floor all zero 0.9980; sentinel DEAD
flip2: exact 0.8782; ff 0.7338 (still failed after 2 0.2115); off 0.6680; d 0.0657 (2 SE_d 0.0204) -> CLOSER WITH CONTROL; post 0.8215 (kept 0.4635); floor all zero 0.9830; sentinel DEAD
flip3: exact 0.8230; ff 0.6262 (still failed after 2 0.2923); off 0.5357; d 0.0905 (2 SE_d 0.0220) -> CLOSER WITH CONTROL; post 0.7114 (kept 0.3170); floor all zero 0.9640; sentinel DEAD
m2_1: exact 0.9371; ff 0.5585 (still failed after 2 0.1080); off 0.5070; d 0.0515 (2 SE_d 0.0223) -> beside (CLOSER WITH CONTROL); post 0.5837 (kept 0.6840); floor all zero 0.9982; sentinel DEAD
m2_2: exact 0.8782; ff 0.5550 (still failed after 2 0.1953); off 0.4873; d 0.0678 (2 SE_d 0.0223) -> beside (CLOSER WITH CONTROL); post 0.5838 (kept 0.4985); floor all zero 0.9830; sentinel DEAD
m2_3: exact 0.8230; ff 0.4447 (still failed after 2 0.2470); off 0.3588; d 0.0860 (2 SE_d 0.0218) -> beside (CLOSER WITH CONTROL); post 0.4302 (kept 0.3852); floor all zero 0.9607; sentinel DEAD
L 1: ff error without flip -0.3786, with flip -0.2654; gain +0.1132 (2 SE 0.0216)
L 2: ff error without flip -0.3232, with flip -0.1444; gain +0.1787 (2 SE 0.0210)
L 3: ff error without flip -0.3782, with flip -0.1967; gain +0.1815 (2 SE 0.0219)
predictions: {'1 L = 2: CLOSER WITH CONTROL': 'held', '2 L = 3: CLOSER WITH CONTROL': 'held', '3 flip gain positive and >= 2 SE at L = 2 and L = 3': 'held'}
```

Every shot of ff and off counted (4000 each); post is beside and discards shots.

## Against the declaration

| | numbers | |
|---|---|---|
| verdict L = 1 (flip) | d 0.0425, 2 SE_d 0.0213 | CLOSER WITH CONTROL |
| verdict L = 2 (flip) | d 0.0657, 2 SE_d 0.0204 | CLOSER WITH CONTROL |
| verdict L = 3 (flip) | d 0.0905, 2 SE_d 0.0220 | CLOSER WITH CONTROL |
| prediction 1: L = 2 CLOSER | | held |
| prediction 2: L = 3 CLOSER | | held |
| prediction 3: flip gain >= 2 SE at L = 2 and 3 | +0.179 and +0.182 (2 SE 0.021, 0.022) | held |

Two numbers side by side: the verdict holds at every L, and the flip moves ff toward the exact value by 0.11-0.18.
The ff arm is still 0.27 / 0.14 / 0.20 below the exact value; of that, 0.04 / 0.09 / 0.11 is the noiseless cost of
m = 2 (shots still failing after 2 tries), so the device's own loss is 0.22 / 0.06 / 0.09.

## Beside, never judged

The same night, ff P(last output 1) against exact (different jobs; first design without barriers, m = 3):

| L | exact | first design (m = 3, 11:40 CET) | m2, barriers, no flip (12:58) | flip (12:58) | flip noiseless |
|---|---|---|---|---|---|
| 1 | 0.937 | 0.599 | 0.559 | 0.672 | 0.892 |
| 2 | 0.878 | 0.629 | 0.555 | 0.734 | 0.792 |
| 3 | 0.823 | 0.551 | 0.445 | 0.626 | 0.708 |

The flip also raises the off arm (0.629 / 0.668 / 0.536 against 0.507 / 0.487 / 0.359 without it): the off arm keeps
the X pairs and waits through the same measurements.

## Reading (an interpretation beside the declaration, not a judgement)

- Holding the likely value as |0> during the waits recovers most of the device loss at L = 2 and 3: the remaining
  device loss there is 0.06-0.09 beyond the noiseless m = 2 value.
- L = 1 keeps a large loss (0.22 beyond noiseless). Its output is read on physical qubit 1, whose readout of |1> was
  0.78 at 12:39 CET while a neighbour saw its |1> at 0.98 (`results/ctrl-diag-2026-11-16`); the final readout of
  qubit 1 fits most of it. The flip cannot help a final readout as written (the output is flipped back before it is
  measured).
- The barriers that keep the X pairs cost on their own: m2 with barriers is below the first design without barriers
  at every L (0.559 / 0.555 / 0.445 against 0.599 / 0.629 / 0.551, an hour apart). They hold the outputs idle in step
  with every measurement; without them the compiler's schedule was kinder. The flip more than pays for them.
- Next questions (owner's decision): m = 3 with the flip (fewer failing shots, more waits); reading the final output
  flipped as well (a declared relabelling of the last bit, which would take qubit 1's |1> readout out of L = 1); the
  same on another device.

## Files

`job/`, `runs/`, `build.json`, `rus2_scores.json` (the scorer's output), `fetch_in/`.

## Reproduce

`python reproduce.py --psf-os PATH_TO_PSF_OS_AT_feedforward-2026-11-16 rus-neuron2-2026-11-16` (SAME, 2026-11-16).
