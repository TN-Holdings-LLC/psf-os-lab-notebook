# Measuring the time a decision costs: a clock qubit and a ruler of delays (workplace Claude, 2026-11-18; desk only, not declared)

Owner: of the four things still missing for an OS on this machine, "3": the time specification. The device records
keep no decision latency and no measurement length, and how the controller orders conditionals on separate qubits is
not in any record; the packing loss of 2026-11-17 and the "running without our circuits" minutes point there. Tool:
`gpu/timing_night.py` (build / check / score / planted / planted-run); declaration draft
`prereg/drafts-2026-11-18/timing_DRAFT.md`. psf-os unchanged (0f57c76; top-level delays accepted since 871d9e6).

## The idea

Time cannot be read off a clock on the device, but it can be read off a qubit: two "clock" qubits in |+> with an echo
X halfway lose phase while they wait, so the longer the wait the more often they read 1 at the end (ideal 0). In the
same job a **ruler** of known delays (0 to 32 us per half, in dt) gives the loss against time; every other item's loss
is read on that ruler as an equivalent wait. The items differ only in what the actor qubit does while the clocks wait:

| item | per half | what it isolates |
|---|---|---|
| R(d) | a delay of d dt on the actor | the ruler (d = 0, 1008, 2000, 4000, 6000, 8000) |
| C(n) | n x (measure, conditional X that never fires) | measurement + an unfired decision |
| C(n) off arm | n x measure | measurement alone (the off arm comes for free) |
| F(n) | n x (X, measure, conditional X that fires) | measurement + a fired decision |
| D(n) | C(n) on two actors side by side | whether decisions on two qubits wait for each other |

Per step: the measurement s_M, measure + decide s_C, fired s_F, two actors s_D (weighted least squares of the
equivalent wait against the number of steps). **Decision latency = s_C - s_M**: a measurement's crosstalk on the
clocks is in both and cancels. Two actors / one = s_D / s_C: 1 in parallel, 2 one after the other.

No device error number is read: the ruler is our own delays in the same job, read piecewise linearly between its
points on the scale tau = -ln(1 - 2 (loss - loss0)) (monotone, so no decay shape is assumed; it only straightens the
pieces), made non-decreasing first. Placement by rule C: a chain of 7 sites, clocks on sites 0 and 6, actors on 2 and
4, so no actor is a clock's neighbour. The conversion from dt to us assumes dt = 4 ns (the record keeps no dt; home can
record `backend.dt`, a time, not a quality number). Barriers fence the halves so the clocks idle while the actors work.

## Size

On the 2026-11-17 records of marrakesh, fez and kingston: 13 items, ff / off / floor, one ring sentinel: **43
circuits, 51.0 s by the model**, 4000 shots. Pre-run check (noiseless Aer: both clocks read 0 in every shot of every
ff and off arm; floors all zero): PASS on marrakesh.

## Does the estimator read time back? (planted checks)

- **Synthetic counts** (no circuit; `planted_synthetic.txt`): clocks with T = 100 and 160 us, planted measurement
  2.6 us, unfired decision 0.9 us, fired +0.3 us, two actors in series; six seeds. Mean over seeds: measurement 2.60,
  latency 0.90 (2 SE about 0.5), fired - unfired +0.18 (2 SE about 0.85), two actors / one 2.12. The latency is
  resolved (beyond 2 SE) in five of six seeds; fired - unfired is not resolvable at this size.
- **The real circuits** (`planted-run` on the built job with the Clifford sentinel, then `score`;
  `planted_circuits.txt`): the clocks dephase per half for the planted elapsed time. Read back: measurement 2.66 us
  (planted 2.6), latency +0.99 (2 SE 0.47; planted 0.9), fired - unfired +0.34 (planted 0.3), two actors per step
  6.13 us (planted 7.0, 1.4 SE low). The bits, the arms (the off arm as the measurement alone) and the ruler work
  end to end on the circuits that would run.

A first try with a straight-line ruler was biased (the loss saturates; items outside the ruler's range): the
piecewise ruler and the step counts chosen so every item stays inside the ruler's 64 us fixed it.

## What it cannot say

- Precision depends on the clocks' own decay: with T = 100 us the latency's 2 SE is about 0.5 us; with a slower decay
  (a better qubit) the same shots give a larger SE. A latency much under 0.5 us would read "not resolved".
- It reads what the clocks experience: the elapsed time while they idle, plus anything the actor's activity does to
  them that the ruler does not (measurement crosstalk cancels in s_C - s_M, not in s_M itself).
- It measures one device, one night, one placement; it says nothing about how IBM's controller is built.

## What it would tell the OS

- **The ledger's missing number**: the decision latency (the ledger takes it as a parameter, 0 or a hypothetical 1 us).
- **The packing loss**: if two actors / one is near 2, decisions on separate qubits wait for each other, which would put
  every conditional of a packed circuit on one clock and explain why only the control arm lost.
- **The fast path**: the conditionals here are a measurement followed at once by a single-qubit X on the measured qubit,
  with no barrier between: the shape the workplace VS's FASTPATH note lists for IBM's fast path; the neuron chains'
  conditionals are not. A follow-up item with a CZ in the block (the neuron's shape) would show the difference.
