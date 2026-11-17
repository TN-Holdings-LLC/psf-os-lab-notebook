# Computations where the real-time decision is the computation: two prototypes (workplace, 2026-11-17; desk only, not declared)

Owner: "試作作って" (after "which computations live on this use?"). Two prototypes in the form of the compound prototype
(exact values, a ceiling for after-the-fact processing, build, dry run, score). Tool: `apps.py` (ideal / build / score);
output `ideal.json`. psf-os unchanged (branch feedforward-2026-11-16, 301ac01). No device job, no IBM, no push.

## A. Iterative phase estimation (the margin compounds with the number of bits)

Two qubits on a line: an ancilla and a target in |1> (eigenstate of U = P(2 pi phi)), phi = j / 2^n for every j.
One bit per round, least significant first: H, controlled U^(2^m) (written with CZ), a conditional phase on the ancilla
for every bit already read (the feedback), H, measure, reset by a conditional X. The off arm keeps the reset and drops
the feedback. Ceiling: the best fixed decoder from the off arm's recorded bits to phi, averaged over phi,
C(n) = 2^-n sum_bits max_phi P_off(bits | phi), computed exactly (branching simulation, no sampling).

| n | ff (noiseless) | off as read | ceiling C(n) | margin ff - C |
|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 0 |
| 2 | 1 | 0.750 | 0.750 | +0.250 |
| 3 | 1 | 0.500 | 0.588 | +0.412 |
| 4 | 1 | 0.324 | 0.471 | +0.529 |

Each bit's correction depends on every bit read before it, so what the off arm loses grows with n: the margin is the
compounding the compound prototype measured on the neuron chain, here in a computation with a known answer.

## B. Long-range teleport in constant quantum depth (the merit is depth, not a growing margin)

T^dag|+> on q0 carried to q_{2k}: k Bell pairs made at once, k Bell measurements at once, the byproduct removed on the
last qubit, then T and H (every shot ideally reads 0). Ceiling 3/4 for every k (as the 11-16 teleport test).
IBM's conditionals test one bit and do no arithmetic, so each parity is applied as one conditional per bit.

Size on the 11-16 13:11 CET marrakesh record (rule C chain, psf-os compiler; depth counts a conditional as one layer),
against the sequential teleport test of 11-16 over the same distance:

| distance | sequential CZ / depth | constant-depth CZ / depth | mid-circuit measurements (both) |
|---|---|---|---|
| 4 | 4 / 31 | 4 / 20 | 4 |
| 8 | 8 / 55 | 8 / 24 | 8 |
| 12 | 12 / 79 | 12 / 28 | 12 |
| 16 | 16 / 103 | 16 / 32 | 16 |

The sequential form grows by about 6 layers per qubit of distance; this form by 1, and that 1 is the stack of
single-bit conditionals on the last qubit (a parity test would make it constant). The measurements happen in one
layer, so the device waits for feed-forward once instead of k times.

## The prototype job

`apps.py build DEVDIR OUT` on the same record: A for n = 2, 3 (all 12 phases), B for k = 2, 4; each item with ff, off
and floor arms, one ring sentinel. **46 circuits, 54.3 s by the model**, 4000 shots. Per item: A n 2 CZ 0-4, depth
10-28, 1 mid-circuit measurement, 2 conditionals; A n 3 CZ 0-6, depth 20-45, 2 and 5; B k 2 CZ 4, depth 20, 4 and 4;
B k 4 CZ 8, depth 24, 8 and 8. (phi = 0 has no controlled phase at all; phi = 1/2 loses its U^2, U^4 rounds.)

Dry run (`--dry-clifford-sentinel`, `feedforward.run_local`, `apps.py score`): every group ff 1.000 against the ceiling
-> BEYOND THE CEILING, off as read 0.750 / 0.501 / 0.500 / 0.499, sentinel CLEAN. The tool reads the noiseless values
back.

## What the ceilings do and do not cover

- A: the ceiling covers any processing of the off arm's bits (the Bayes-best decoder is the best of all of them). It
  does not cover a different fixed circuit: textbook phase estimation with n ancillas and a coherent inverse QFT also
  reads phi exactly without noise. What the feedback buys is doing it with one ancilla (2 qubits for any n) and without
  the controlled rotations of the inverse QFT. A fair comparison with that circuit is a separate test.
- B: the corrections could be made coherent (deferred measurement), but that needs gates from every pair to the last
  qubit: long-range, so the depth grows with k again. The ceiling 3/4 covers processing of the recorded bits only.
- The ceilings are noiseless numbers; nothing here is declared; the 11-16 record is used for placement only (coupling
  graph and failed marks), no error numbers.

## Draft predictions (forms for the owner; numbers to fix)

1. A, per n (2, 3): the ff average over all phases is BEYOND THE CEILING C(n) (ff >= C + 2 SE), every shot counted.
2. A, compounding: the device margin ff - C(n) is larger at n = 3 than at n = 2 by >= 2 SE.
3. B, per k (2, 4): BEYOND 3/4; beside: the ff success at k = 4 against k = 2 (a flat line is what constant depth
   predicts; the sequential test's fall over the same distance is the comparison, from its own record).
