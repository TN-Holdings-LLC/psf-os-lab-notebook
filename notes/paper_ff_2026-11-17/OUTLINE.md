# Material for a paper on real-time control (home, 2026-11-17 night; an outline, not a draft text)

Working title: "Decisions no post-processing can reach: mid-circuit measurement and real-time control on IBM Heron,
declared before the data". Author TN Holdings. Which paper number it takes is the owner's call: the planned paper 10
(`notes/paper10/`, the cut of the 81-qubit chain, with the shot-by-shot MODE verdict) has not run.

## The claim, and its scope

- For a circuit that measures in the middle and acts on the result at once, the arm with the actions removed (off) has
  a ceiling: no processing of its recorded bits, and no after-the-fact correction of it, gets past that circuit's
  noiseless value (teleport: 3/4 by the best fixed rule; iterative phase estimation: the Bayes-best decoder; the
  neuron chain: the off arm's noiseless value). Real-time control on the device got past it, declared, every shot
  counted, on three devices.
- Not claimed: that no circuit without real-time control reaches the same answer. Writing the control coherently (no
  mid-circuit measurement) gives the same noiseless answer and can be corrected afterwards (T1, N1; textbook phase
  estimation).

## Evidence (all declared before the data; job ids in each results folder)

| night / device | test | result |
|---|---|---|
| 11-16 marrakesh | teleport k = 1, 2 (`results/feedforward-2026-11-16`) | ff 0.952 / 0.890 above 3/4 + 2 SE; the off arm also above at k = 1 (0.794): decay toward the success bit |
| 11-16 marrakesh | neuron, first design (`results/rus-neuron-2026-11-16`) | control fires as the circuit says; value lost (ff 0.599 / 0.629 / 0.551) |
| 11-16 marrakesh | wait and control diagnostics (`results/wait-diag-…`, `results/ctrl-diag-…`) | unfired conditionals free; the loss is time held in \|1> (0.98 -> 0.46 on q1 over five waits) |
| 11-16 marrakesh | second and third designs (`results/rus-neuron2-…`, `rus-neuron3-…`) | hold the likely 1 as \|0> while waiting (+0.11 to +0.18), read it as \|0> (+0.22 at L = 1) |
| 11-16 kingston | third design (`results/rus-neuron3-kingston-…`) | CLOSER at L = 1, 2, 3; device loss 0.04-0.06 |
| 11-17 fez | T1-T4 (`results/ff-night-2026-11-17`) | beyond the off arm's correction ceiling at L = 1 .. 5, margin growing (slope +0.024 / step); phase estimation beyond its ceiling at n = 2, 3, margin growing; long-range teleport k = 2 beyond, k = 4 not |
| 11-17 marrakesh | N1-N3 (`results/ff-night2-2026-11-17`) | phase estimation n = 4: 0.903 against the ceiling 0.471; early chain beyond at L = 2 .. 6, overshoot at L = 1, 7 |
| 11-17 marrakesh | the prescription loop (`results/os-night-2026-11-17`) | diagnostics -> fixed rule -> P2 picked; HELPS at L = 2, 3, overshoot at L = 1 |
| 11-17 marrakesh | the frame-balanced chain (`results/balanced-night-2026-11-17`) | no overshoot by construction; beyond the ceiling at L = 2 .. 5, margin growing (slope +0.031 / step); L = 1 not beyond (the nf frame reads its 1 on a qubit with a large readout gap) |
| 11-17 marrakesh | single against packed (`results/packing-night-2026-11-17`) | ten items in one circuit: 11 s against 41 s charged, but the control arm keeps 0.20 less on average (off arm unchanged): side-by-side conditionals cost |

Predictions over the two nights: 37 declared; 26 held, 11 failed (11-16: teleport P3; neuron P1, P2; wait P1. 11-17:
T3-3, T4-3, N2-1, N2-2, OS-2, B-2, PK-1). Each failure is reported as such in its folder.

## Two numbers side by side (to carry into the text)

- Vanity: beyond the ceiling, margin growing with depth. Essence: the device keeps 0.65-0.93 of the noiseless margin;
  the noiseless m = 2 gap to the exact value (0.04-0.11) is the design's own cost.

## What the paper must say about its weak points

- Decay toward \|0> is one-sided: any design that holds the likely value as \|0> leans toward success and can overshoot
  its noiseless value (observed: N2 L = 1, 7; OS L = 1). The guard set before the data took those cases out; the
  frame-balanced pair removes the lean by construction; it ran on 11-17 (marrakesh): no overshoot, beyond at L = 2 .. 5,
  COMPOUNDS, but the pool keeps only 0.77-0.87 of its noiseless value (the two frames 0.92-1.01 and 0.60-0.80).
- Different devices on different nights; no same-device repeat of the 11-17 tests yet.
- The sentinel was DEAD on marrakesh and fez on these nights (beside, never judged).
- Every noise model in the notes is illustrative and not fitted; none is used for a verdict.
- The early chain (CZ 42 -> 10 at L = 5) kept the same share as the third design on fez: CZ count and counted waits
  were not the limit there; the cost of its extra conditionals was not measured apart (home VS, task A).

## Still to run before writing (proposal)

1. (done 11-17, marrakesh) The frame-balanced chain, L = 1 .. 5.
2. A same-device repeat of T2 or the balanced chain on a second night.
3. Optionally the packed form (home VS, task B) as a declared single-against-packed test.
