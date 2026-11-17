# Does real-time control compound? A prototype (workplace, 2026-11-17; desk only, not declared)

Owner: a fixed circuit earns "simple interest" (its error is read once, at the end, where after-the-fact methods work
on one number); a feed-forward chain earns "compound interest" (each step's real-time decision is the next step's
start). How to make the compounding count, and show it. Tool: `compound.py` (ideal / build / check / score / retro);
outputs `ideal.json`, `retro.json`. psf-os unchanged (branch feedforward-2026-11-16, 301ac01).

## The measure

For the neuron chain (third design of 2026-11-16: m = 2, outputs held flipped while waiting, the last output read
flipped and relabelled; theta 1.1):
- the circuit without control (the off arm) has its own noiseless value P_off,0. Any after-the-fact method that
  estimates the noiseless value of the circuit that ran (rescaling, zero-noise extrapolation, probabilistic error
  cancellation) can at best bring the off arm to P_off,0. So **c(L) = |P_off,0 - exact|** is the ceiling of what
  correction can reach without real-time control;
- the device with control: **e(L) = |P_ff - exact|**, every shot counted;
- **g(L) = c(L) - e(L)**: positive means the device with real-time control is closer to the exact value than any
  corrected run without control could be. SE from the ff arm's binomial spread (c is a noiseless number).
- Compounding: g grows with L. Read as the weighted least-squares slope of g over L, with its SE.

What the ceiling does not cover: recomputing the target classically (that is not a correction of the run), and a
"without control" arm other than the one used here (the same circuit with the conditional blocks removed).

## Noiseless values (exact branching simulation, no sampling)

| L | exact | ff noiseless | off noiseless | ceiling c | noiseless margin g0 |
|---|---|---|---|---|---|
| 1 | 0.9371 | 0.8904 | 0.7943 | 0.1429 | +0.0962 |
| 2 | 0.8782 | 0.7929 | 0.6308 | 0.2473 | +0.1620 |
| 3 | 0.8230 | 0.7060 | 0.5010 | 0.3219 | +0.2049 |
| 4 | 0.7712 | 0.6286 | 0.3980 | 0.3733 | +0.2307 |
| 5 | 0.7227 | 0.5597 | 0.3161 | 0.4066 | +0.2437 |

Even without noise the margin grows with L, and flattens by L = 4-5 (two tries leave more failures as the chain
lengthens). On a device each step also loses, so g may peak and turn: where it does is the useful length of the chain.

## The recorded jobs of 2026-11-16, read this way (exploratory, after the fact)

| L | marrakesh ff | g (2 SE) | kingston ff | g (2 SE) |
|---|---|---|---|---|
| 1 | 0.883 | +0.089 (0.010) | 0.853 | +0.058 (0.011) |
| 2 | 0.740 | +0.109 (0.014) | 0.749 | +0.118 (0.014) |
| 3 | 0.631 | +0.130 (0.015) | 0.646 | +0.145 (0.015) |
| slope per step | | +0.020 (2 SE 0.009) | | +0.045 (2 SE 0.009) |

On both devices every L is beyond the correction ceiling and g grows with L. The device keeps a falling share of the
noiseless margin (marrakesh 0.93, 0.67, 0.63 of g0), so the growth comes from the circuit's margin outrunning the
device's loss, not from the device getting better. Also seen: marrakesh's off arm at L = 1 read 0.845, above its
noiseless 0.794 (decay toward |0> read through the relabelling moves it up); the measure uses the noiseless ceiling,
never the device's off value, for that reason. These readings were chosen after the data: a declared test is needed.

## The prototype job (L = 1 .. 5, one job)

`compound.py build DEVDIR OUT` on the 11-16 13:11 CET marrakesh record: chains on qubits 0-1 .. 0-9, CZ 2 / 12 / 22 /
32 / 42 (off 1 / 6 / 11 / 16 / 21), mid-circuit measurements 2 / 4 / 6 / 8 / 10; **19 circuits, 24.2 s by the
model**. Pre-run check (noiseless Aer of every arm against the exact values, 0.03): PASS. Dry run (noiseless, sentinel
at its Clifford point): g = +0.094 / +0.172 / +0.195 / +0.234 / +0.237, each beyond the ceiling, slope +0.038 (2 SE
0.004): the tool reads the noiseless margins back.

## Draft predictions (forms for the owner; numbers to fix)

1. Per L = 1 .. 5: BEYOND THE CORRECTION CEILING (g >= 2 SE).
2. COMPOUNDS: the slope of g over L = 1 .. 5 >= 2 SE.
3. Beside: the L where g peaks (if it peaks inside 1 .. 5), and the share of g0 the device keeps per L.
Basis: the 11-16 jobs above (L 1-3 on two devices), stated as after the fact.

## Making the compounding count (what the levers are)

- **Per-step loss down** (the "rate"): the 11-16 diagnostics put the loss in the waits (a |1> decays during
  mid-circuit measurements). Held-flipped outputs and the flipped final read already cut it; placing the outputs on
  qubits that keep |1> in the night's own whole-device floor is the next lever (a special condition, recorded).
- **Settle errors at each step**: a retry undoes a detected failure; the same idea extended (a parity check measured
  mid-circuit, a conditional fix) would stop other errors from carrying into the next step.
- **Count every shot**: post-selection withdraws principal at each step (kept 0.67 -> 0.20 from L 1 to 5 in the dry
  run) and is biased in the chain.
- **Keep the decisions real-time** where the claim is "beyond correction": the coherent form (no mid-circuit
  measurement) is a fixed circuit, open to extrapolation, so it belongs to the "simple interest" side.
