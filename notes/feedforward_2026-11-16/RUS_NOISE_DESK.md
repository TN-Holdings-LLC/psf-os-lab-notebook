# The repeat-until-success quantum neuron under an illustrative noise model: where real-time control is clearly better than none (workplace VS Claude, 2026-11-16; desk only)

**This is an illustration, not a prediction for any device.** The noise model is the same uniform one as
`NOISE_DESK.md`. It was chosen before looking at any device; nothing is fitted and no calibration number was read.
What to run (L, m, angle) is the owner's decision.

`rus_noise_desk.py` writes `rus_noise_desk.txt` (all tables) and `rus_noise_desk.json`. It needs numpy; qiskit is used
only for check 1. Aer is not needed.

## Circuit and arms

- The circuit is `rus_neuron_desk.py`'s: L neurons in a row, neuron j > 0 switched on by neuron j-1's output.
- **ff:** after a recorded 1, undo RY(pi/2) on the output, X on the ancilla, attempt again; at most m attempts. Every
  shot is counted.
- **post:** one attempt per neuron; keep only the shots where every recorded bit is 0. This is a comparison only.
- **off:** one attempt per neuron, every shot counted.
- **The answer:** P(final output = 1), against its exact value sin^2(q)^L, with tan q = tan^2 theta.
- **Gates as the entrance would write them:**
  - CY = (Sdg, H) CZ (H, S) on the target.
  - CRY(phi) = RY(phi/2), CX, RY(-phi/2), CX, with CX = H CZ H.
  - Consecutive one-qubit gates are fused.
  - So one attempt has 1 CZ alone and 5 CZ when controlled.

## Model (the same numbers on every element; not any device's)

- **One-qubit gates:** depolarising 3e-4 after every fused one-qubit gate.
- **CZ:** depolarising 3e-3 after every CZ.
- **Readout:** the recorded bit is flipped with probability 0.015, at mid-circuit and final measurements.
  - A flipped ancilla bit makes ff retry when it should stop, or stop when it should retry.
  - It makes post keep or drop a shot wrongly.
- **Wait:** during every mid-circuit measurement every other qubit gets a phase flip (1 - exp(-w)) / 2, with
  w = wait / T2 = 0 to 0.1. The same wait is given to all three arms.

## Method and checks

- **Exact:** the density matrix of all 2L qubits (L <= 4, at most 8 qubits). The branches split on each recorded bit.
  No shots are drawn.
- **Check 1:** the decomposed, fused attempt equals qiskit's cy / cry / sdg / ry circuit, up to 1e-15.
- **Check 2:** noiseless, all 27 cells (L 1-3, theta 0.5 / 0.8 / 1.1, three arms) agree with the Aer numbers of
  `rus_neuron_desk.txt` (20000 shots) within 2.6 SE.
- **Check 3:** with noise, an independent Monte Carlo over Pauli and readout trajectories on the state vector agrees
  within 2.1 SE in 6 cells, covering ff, post and off.

## The criterion asked for

ff's error is smaller than off's by at least 2 SE, with 4000 shots in each arm:

- margin = (|off - exact| - |ff - exact|) / (2 SE_d);
- SE_d = sqrt(p_ff (1 - p_ff) / 4000 + p_off (1 - p_off) / 4000);
- the criterion holds when the margin is at least 1.

## Result: where it holds (the m values with margin >= 1)

| theta | L | w = 0 | w = 0.01 | w = 0.03 | w = 0.05 | w = 0.1 |
|---|---|---|---|---|---|---|
| 0.5 | 1 | 2-5 | 2-5 | 2-5 | 2-5 | 2-5 |
| 0.5 | 2 | 2-5 | 2-5 | 2-5 | 2-5 | 2-5 |
| 0.5 | 3 | 3-5 | 3-5 | 3-5 | 3-5 | 3-5 |
| 0.5 | 4 | none | none | none | none | none |
| 0.8 | 1-4 | none | none | none | none | none |
| 1.1 | 1 | 2-5 | 2-5 | 2-5 | 2-5 | 2-5 |
| 1.1 | 2 | 2-5 | 2-5 | 2-5 | 2-5 | 2-5 |
| 1.1 | 3 | 2-5 | 2-5 | 2-5 | 2-5 | 2-5 |
| 1.1 | 4 | 2-5 | 2-5 | 2-5 | 2-5 | 2-5 |

The margins themselves, at w = 0.05 (the other waits are in `rus_noise_desk.txt`; m = 1 is off itself, margin 0):

| theta | L | m = 2 | m = 3 | m = 4 | m = 5 |
|---|---|---|---|---|---|
| 0.5 | 1 | 4.7 | 6.6 | 7.3 | 7.5 |
| 0.5 | 2 | 2.3 | 3.7 | 4.0 | 4.1 |
| 0.5 | 3 | 0.1 | 1.3 | 1.3 | 1.4 |
| 0.5 | 4 | -0.8 | 0.3 | 0.3 | 0.3 |
| 0.8 | 1 | 0.3 | 0.4 | 0.5 | 0.5 |
| 0.8 | 2 | 0.1 | 0.1 | -0.0 | -0.1 |
| 0.8 | 3 | -0.8 | -0.5 | -0.6 | -0.6 |
| 1.1 | 1 | 5.0 | 6.8 | 7.5 | 7.7 |
| 1.1 | 2 | 6.7 | 9.3 | 10.2 | 10.6 |
| 1.1 | 3 | 7.9 | 11.0 | 12.1 | 12.5 |
| 1.1 | 4 | 8.8 | 12.1 | 13.4 | 13.9 |

## Reading

- **The angle decides more than L, m or the wait.**
  - **theta 1.1:** ff is clearly better at every L up to 4, for m >= 2, under every wait. The margin grows with L,
    because off's error grows with the chain: -0.15 at L = 1 and -0.37 at L = 4.
  - **theta 0.8:** never. A failed attempt leaves the output at P1 = 0.5, and the exact value is 0.53, so off is
    almost right by accident. Its error is at most 0.015 at every L. This angle cannot show what ff adds, whatever the
    noise.
  - **theta 0.5:** the exact value falls to 0.007 (L = 2) and 0.001 (L = 3). Then both arms sit on the same noise
    floor of about 0.02-0.03, set by readout and gates. The criterion holds up to L = 3 (m >= 3) and not at L = 4.
  - **This follows from the circuit, not from data.** The off arm's error is (1 - success share) times (0.5 - exact)
    at L = 1. An angle whose exact value is far from 0.5 is the one that can separate the arms.
- **m:** m = 2 brings most of the gain, and m = 3-5 adds less.
  - Where the criterion holds, more attempts never lowered the margin: the noise of a retry costs less than the
    shots it rescues.
  - The share still failed after m attempts depends on the angle. At m = 3 it is 0.04-0.13 at L = 1. At theta 0.8
    it reaches 0.18-0.22 for L >= 2, because there each attempt succeeds only about half the time.
- **The wait matters only to ff.**
  - post and off do not change with w. Their waiting qubits are only used as controls or measured in Z, where a phase
    flip does nothing.
  - In ff the undo RY(pi/2) turns the output, so a phase lost before it counts.
  - Even so, w = 0.1 lowers the margins by only about 10 to 20 percent. So the comparison does not depend on giving
    the same wait to all arms.
- **Noise also moves ff away from the exact value.**
  - Example, theta 1.1, L = 4, m = 3: -0.088 at w = 0 and -0.13 at w = 0.1.
  - Off is at -0.37 there, so ff is still clearly better, but ff's own error is several SE. "ff agrees with the exact
    value" is not what this model predicts.

## Post-selection bias under noise (L >= 2)

post's error against its own SE (4000 x kept shots):

| L | theta | exact | noiseless | with noise (every w) |
|---|---|---|---|---|
| 2 | 0.8 | 0.280 | -0.090 (-9 SE) | -0.077 (-7 SE) |
| 3 | 0.8 | 0.148 | -0.092 (-15 SE) | -0.075 (-10 SE) |
| 4 | 0.8 | 0.078 | -0.063 (-19 SE) | -0.045 (-9 SE) |
| 2 | 1.1 | 0.878 | -0.026 (-3 SE) | -0.048 (-6 SE) |
| 3 | 1.1 | 0.823 | -0.078 (-7 SE) | -0.103 (-8 SE) |
| 4 | 1.1 | 0.771 | -0.150 (-10 SE) | -0.175 (-11 SE) |

- **The bias stays under noise.** The noise does not wash it out.
  - At theta 0.8 the noise makes it a little smaller, but it remains 7 to 10 SE.
  - At theta 1.1 the noise adds to it.
- **Noise adds a bias even at L = 1, where there is none noiselessly.** A flipped ancilla bit keeps a failed shot or
  drops a good one: +0.017 at theta 0.5 and -0.018 at theta 1.1, about 3 SE.
- **So post is not a fair reference for the exact value, with or without noise.** It is a comparison beside the
  verdict, as the instructions say.

## What this model leaves out

- **Not modelled:**
  - T1 during the wait;
  - a mid-circuit measurement error different from the final readout's;
  - measurement-induced dephasing of neighbours;
  - leakage;
  - crosstalk;
  - the timing of a branch-dependent block.
- **The ancilla reset is the conditional X only.** An ancilla left in |1> by a flipped bit is not caught.
- **The wait is not known before a run.** The table says only which (L, m, angle) keep a margin if the device's noise
  is near this model's.
