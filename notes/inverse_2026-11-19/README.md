# Removing noise by running it backwards: a desk test (workplace Claude, 2026-11-19; not declared)

The owner's question: if the tensor analysis of the core were run backwards, could the noise be removed? Here the
"backwards" is the inverse of each gate's noise channel, contracted on the state (`infinite_shots.py`) or sampled as
probabilistic error cancellation (`inverse_desk.py`); this is what tensor-network error mitigation and PEC do. Desk
only: no device, no device record, no calibration number. **Every noise here is illustrative, written by hand, and
never fitted to a device**; the numbers say how the methods behave, not what a device does.

## Set-up

- Circuit: a kicked brickwork chain, n = 8, L layers of rx(theta) rz(phi) on every qubit (theta in [0.2, 0.6], phi in
  [-pi, pi], seeded per L) then cz on even and odd pairs (7 cz per layer); |0...0> in; <Z> on qubit 4. Exact value by
  statevector. L = 2, 4, 8, 12, 20, 30 (14 to 210 cz). At L = 12 and 20 the exact value is small (0.19, -0.18).
- Truths (the "device"): A two-qubit depolarizing p = 0.01 after every cz (Aer's convention: Pauli fidelity 1 - p) and
  a symmetric readout flip q = 0.02; B as A, the model assumes 0.8 p; C as A plus a coherent ZZ over-rotation of 0.05
  rad after every cz, not in the model; D as A plus one-qubit depolarizing 0.002 on every rx, not in the model.
- Methods: raw (as read); mirror (model-free: raw divided by the square root of U U^-1's <Z>, half the shots each); the
  inverse (the model's inverse channel after every cz, the readout divided out by 1 - 2 q).

## Infinite shots (`infinite_n8.txt`: the bias alone, error = estimate - exact)

| L (cz) | exact | A raw | A mirror | A inverse | B inverse (model 20 % weak) | C inverse (coherent error unknown) | C raw | D inverse (1q noise unknown) |
|---|---|---|---|---|---|---|---|---|
| 2 (14) | +0.853 | -0.066 | -0.013 | 0.000 | -0.007 | -0.008 | -0.074 | -0.003 |
| 4 (28) | +0.726 | -0.089 | -0.011 | 0.000 | -0.013 | +0.008 | -0.082 | -0.008 |
| 8 (56) | +0.712 | -0.130 | +0.017 | 0.000 | -0.023 | +0.054 | -0.090 | -0.012 |
| 12 (84) | +0.189 | -0.053 | +0.014 | 0.000 | -0.011 | +0.242 | +0.113 | -0.006 |
| 20 (140) | -0.178 | +0.127 | +0.082 | 0.000 | +0.035 | -0.102 | +0.071 | +0.028 |
| 30 (210) | +0.306 | -0.191 | +0.060 | 0.000 | -0.055 | -0.233 | -0.254 | -0.038 |

- With the model exactly right (A), the inverse returns the exact value at every depth (to 1e-15): running the noise
  backwards works, in principle.
- With the model's strength 20 % off (B), a bias remains and grows with depth (-0.055 at 210 cz); more shots do not
  remove it. Errors the model does not know stay (D, -0.038 at 210 cz), and a coherent error it does not know (C) is
  not removed and at L = 12 is made worse than raw (+0.242 against +0.113): the inverse amplifies what it misreads.
- The model-free mirror rescale needs no model and is within 0.02 up to 84 cz, 0.06-0.08 at 140-210 cz, and is badly off
  with the coherent error (+0.465 at L = 12).

## Finite shots (`inverse_n8.txt`, `summary_n8.md`: 40 000 shots per method and point)

Stopped by the owner at L = 20 (L = 30 not run): the infinite-shot table had answered the question, and chasing a
better noise model has no end. `inverse_n8.txt` / `.json` hold L = 2 to 20. The inverse's 2 SE (40 000 shots, 100 per
sampled circuit) is 0.05-0.25, against 0.006-0.010 for raw; one point (L = 8, C: +0.989, 2 SE 0.157, against the
infinite-shot +0.767) is 2.8 SE off, not looked into. `summary.py` makes the table.

## The cost (gamma^2, the factor of shots the inverse needs over raw, for this model)

| two-qubit p | 14 cz | 56 cz | 140 cz | 210 cz | 1 000 cz | 5 000 cz | 10 000 cz |
|---|---|---|---|---|---|---|---|
| 0.01 | 1.69 | 8.2 | 191 | 2 640 | 2.0e16 | 3e81 | 9e162 |
| 0.003 | 1.17 | 1.88 | 4.8 | 10.6 | 7.7e4 | 2.7e24 | 7.4e48 |
| 0.001 | 1.05 | 1.23 | 1.69 | 2.2 | 43 | 1.4e8 | 1.9e16 |

(gamma per cz from the inverse's quasi-probabilities for Aer's depolarizing convention; the 0.003 and 0.001 rows are
illustrative values too, not any device's.)

## What it says

1. Running the noise backwards removes it exactly, but only with the noise known exactly, and at a shot cost that grows
   exponentially with the number of gates times the error per gate. That is the deep-computation wall: at 1 000 cz
   and p = 0.003 the inverse needs ~8e4 times the shots, at 5 000 cz ~3e24.
2. Knowing the noise exactly means fitting a noise model to the device, which this project does not do (calibration
   numbers are not read; noise is not fitted). With a model off by 20 % or missing an error, a bias remains that no
   number of shots removes, and a coherent error can be amplified.
3. Where the inverse can be contracted exactly as a tensor (here n = 8), the noiseless answer can be computed the same
   way without the device; this is why psf-os uses its light-cone tensor networks as answer keys.
4. It sits under the correction ceiling of paper 10: any processing after the run, the inverse included, returns at
   best the circuit's noiseless value; to go beyond it takes decisions inside the circuit (and, at depth, error
   correction).

What could be tried on a device later, if the owner wants it (a declaration would be needed, and the rule on fitted
noise would have to be decided first): the model-free mirror rescale beside the raw value on a declared circuit with a
light-cone exact value, as a separate yardstick from the ceiling.

## Reproduce

```
python inverse_desk.py inverse_n8.json --layers 2,4,8,12,20 --shots 40000 --per 100   # seed 7
python infinite_shots.py infinite_n8.json
python summary.py inverse_n8.json > summary_n8.md
```
qiskit 2.6.1, qiskit-aer 0.18.2, numpy, 2 cores (the sampled run about 20 min).
