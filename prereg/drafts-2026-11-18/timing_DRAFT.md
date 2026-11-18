# DRAFT (not declared): the time a decision costs, read by clock qubits on a ruler of delays (workplace Claude, 2026-11-18)

A draft for the owner: numbers, verdict words and predictions marked [OWNER]; the declaration is written and pushed at
home. Tool: `gpu/timing_night.py`; design and planted checks: `notes/timing_2026-11-18/README.md`.

## Common

As the other feed-forward nights: psf-os 0f57c76; the device by the standing rule, one record; rule C placement; no
mitigation; DD and twirling off; 4000 shots; every shot counted; `check` before submission (a FAIL means the job is
not run); `score` as of the declaring commit. No device error number is read. Conditional items are not packed with
others (the job holds only this test's items, each its own circuit).

## What is run (one job, 43 circuits, 51.0 s by the model)

Two clocks (chain sites 0 and 6) in |+> with an echo X halfway, read at the end (ideal 0; the loss is reading 1).
While they wait, the actor (site 2; and site 4 for D) does, per half: R(d) a delay of d = 0, 1008, 2000, 4000, 6000,
8000 dt (dt taken as 4 ns [OWNER: or the device's own dt, recorded at home]); C(n) n = 2, 4, 8 times a measurement
followed by a conditional X that never fires (its off arm: the measurements alone); F(n) n = 4, 8 the same with the
conditional firing every time; D(n) n = 2, 4 C(n) on two actors side by side. ff, off and floor arms; one ring
sentinel.

## What is read (estimates with SE; `score`)

Each clock's ruler (its losses in R(d), made non-decreasing, read piecewise linearly on tau = -ln(1 - 2 (loss -
loss0))) turns every item's loss into an equivalent wait; the two clocks are averaged with inverse-variance weights.
Per step (weighted least squares against the number of steps): s_M (a measurement; the off arms of C), s_C, s_F, s_D.
Reported: the decision latency s_C - s_M; fired - unfired s_F - s_C; two actors / one s_D / s_C; with their SEs.

## Verdicts [OWNER: words and thresholds]

- **DECISION LATENCY RESOLVED** when s_C - s_M >= 2 SE; otherwise **NOT RESOLVED** (the latency is then below what
  this job can see, about 0.5 us at a clock decay time of 100 us).
- **DECISIONS WAIT FOR EACH OTHER** when s_D / s_C - 1 >= 2 SE of the ratio (two actors take longer per step than one);
  **IN PARALLEL** when |s_D / s_C - 1| < 2 SE and s_D / s_C - 2 <= -2 SE; otherwise **NOT SHOWN**.
- Beside, never judged: s_M itself (a measurement's length as the clocks see it, crosstalk included), fired - unfired,
  each clock's ruler, the job's own execution time from the runtime's metrics.

## Predictions [OWNER]

Forms only: T-1 the decision latency is RESOLVED. T-2 decisions on two qubits WAIT FOR EACH OTHER (the mechanism the
packing loss of 2026-11-17 suggests). Whether to make them, and with which words: the owner's.

## Planted checks (before the declaration; dry, no device)

Synthetic counts (six seeds) and the real circuits under a planted dephasing (`planted-run`) read the planted lengths
back: measurement 2.66 us (2.6), latency +0.99 (2 SE 0.47; 0.9), fired - unfired +0.34 (0.3), two actors per step
6.13 (7.0).
