# Tonight's T2 and T3-A under the decay model (workplace VS Claude, 2026-11-17; desk only)

**This is an illustration, not a prediction for any device.**

- The model is the uniform one of `RUS_DECAY_DESK.md`. It was not fitted, and no calibration or error number was read.
- The decay strengths are examples: gamma = 0.05 and 0.1 per wait, with 0 beside.
- What to run, and whether anything changes, is the owner's decision.

`night17_decay_desk.py` writes `night17_decay_desk.txt` and `night17_decay_desk.json`. It runs in about 6 minutes, with
numpy and qiskit only.

## Model

These are the same numbers as `RUS_DECAY_DESK.md`:

- one-qubit gates 3e-4 and CZ 3e-3;
- the recorded bit flipped with 0.015;
- during every mid-circuit measurement, every other live qubit gets amplitude damping gamma and a phase flip of 0.024.

## The circuits

- **T2** is the third design (`gpu/rus3_night.chain`, m = 2, theta 1.1), modelled as compiled on 2026-11-16. It is
  scored as `gpu/compound_night.py` scores it:
  - c from `notes/compound_2026-11-17/ideal.json`;
  - the OVERSHOOT guard P_ff > P_ff,noiseless + 2 SE;
  - the slope from `compound.slope`.
- **T3-A** is `apps.ipe(n, j, feedback)` as written, walked gate by gate with one density matrix per classical record.
  - The `if_test` reads the recorded bit.
  - Success means all n bits are right, pooled over the phases.
  - It is compared against the declared noiseless ceiling: 0.750 for n = 2 and 0.588 for n = 3.

## Checks

Both passed.

1. **Noiseless:**
   - T2's ff and off equal `ideal.json` for L = 1 to 5, to 6e-15.
   - T3-A's ff is 1. Its off arm and the best decoder of the off bits equal `apps.ipe_ideal` (a separate engine), to
     3e-15.
2. **With decay:** T3-A agrees with a Monte Carlo over Kraus trajectories within 0.8 SE (3 cases, 20000 shots each).

## T2

The table gives ff, then g with its 2 SE, then the verdict, for each gamma.

| L | exact | noiseless ff | c | gamma 0 | gamma 0.05 | gamma 0.1 |
|---|---|---|---|---|---|---|
| 1 | 0.937 | 0.890 | 0.143 | 0.867, +0.073 (0.011), BEYOND | 0.873, +0.079 (0.011), BEYOND | 0.879, +0.085 (0.010), BEYOND |
| 2 | 0.878 | 0.793 | 0.247 | 0.761, +0.130 (0.013), BEYOND | 0.782, +0.152 (0.013), BEYOND | 0.802, +0.171 (0.013), BEYOND |
| 3 | 0.823 | 0.706 | 0.322 | 0.670, +0.169 (0.015), BEYOND | 0.712, +0.211 (0.014), BEYOND | 0.749, +0.248 (0.014), OVERSHOOT |
| 4 | 0.771 | 0.629 | 0.373 | 0.592, +0.194 (0.016), BEYOND | 0.659, +0.261 (0.015), OVERSHOOT | 0.713, +0.315 (0.014), OVERSHOOT |
| 5 | 0.723 | 0.560 | 0.407 | 0.525, +0.209 (0.016), BEYOND | 0.617, +0.301 (0.015), OVERSHOOT | 0.688, +0.372 (0.015), OVERSHOOT |
| slope | | | | +0.035 (0.004), COMPOUNDS | +0.057 (0.004), NOT SHOWN | +0.073 (0.004), NOT SHOWN |

- **In this model the guard decides T2 at L = 4 and 5.**
  - At gamma 0.05, ff lies above its noiseless value by +0.030 at L = 4 and +0.058 at L = 5. That is 4 to 8 SE, so
    OVERSHOOT.
  - At gamma 0.1 the overshoot starts at L = 3.
  - Then the slope verdict is NOT SHOWN, so T2-1 and T2-2 would both fail as declared.
  - The cause is the one in `RUS_DECAY_DESK.md`: a logical 0 held as |1> decays into a logical 1. g then grows for
    the wrong reason (kept 1.13 to 1.53 of the noiseless margin), and the guard is there for exactly that.
- **Without decay, everything holds.**
  - Every L is BEYOND, and the slope is COMPOUNDS.
  - The device keeps 0.76 to 0.86 of the noiseless margin.
- **The model is not the device.** On 2026-11-16 the third design stayed below its noiseless value at L = 1 to 3
  (marrakesh 0.883 / 0.740 / 0.631 against 0.890 / 0.793 / 0.706; kingston 0.853 / 0.749 / 0.646).
  - `RUS_DECAY_DESK.md` already found this uniform model too optimistic for D2 / D3 at L >= 2.
  - So these cells say only that overshoot at L = 4 and 5 is possible when decay dominates the other losses. They do
    not say that it is likely.

## T3-A

The table gives ff (lowest phase) and the margin against the declared ceiling, with 2 SE pooled over 4 or 8 circuits.

| gamma | n = 2 | n = 3 | margin(3) - margin(2) |
|---|---|---|---|
| 0 | 0.960 (0.959), +0.210 (0.003), BEYOND | 0.939 (0.938), +0.351 (0.003), BEYOND | +0.141 (0.004), GROWS |
| 0.05 | 0.937 (0.912), +0.187 (0.004), BEYOND | 0.883 (0.849), +0.295 (0.004), BEYOND | +0.108 (0.005), GROWS |
| 0.1 | 0.913 (0.865), +0.163 (0.004), BEYOND | 0.829 (0.764), +0.240 (0.004), BEYOND | +0.077 (0.006), GROWS |

- The margin above the ceiling is large in every cell (40 times its 2 SE or more), and it grows from n = 2 to 3.
- Decay of the target's |1> during the waits takes away the phase kickback. It costs the phases with the most
  controlled rotations most, hence the lowest-phase column.
- The growth shrinks with gamma, from +0.141 to +0.077, but it stays above 12 times its 2 SE here.
- Beside, the off arm as read is 0.725 / 0.478 at gamma 0 and 0.702 / 0.444 at gamma 0.1. The best decoder of the
  modelled off bits stays under the noiseless ceiling.
- There is no overshoot mechanism here: success needs every bit right, and decay only removes information.

## What this model leaves out

- **Not modelled:**
  - decay that differs per qubit (the control test of 2026-11-16: about 0.14 and 0.06 per wait);
  - the decision latency;
  - measurement-induced dephasing;
  - leakage;
  - crosstalk;
  - routing on the night's device.
- **T3-A's gates** are taken as written (h, p, x, cz), not as compiled.
