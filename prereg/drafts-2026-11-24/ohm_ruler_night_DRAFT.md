# DRAFT (not declared): Ohm with rulers inside the circuit, raw (Heron)

Workplace Claude, 2026-11-24, on home's instruction "オームの「回路の中の物差し」の晩" and `prereg/README.md` rule 3
(the owner, 2026-11-24 10:30 JST). Words, reading tables and predictions marked [OWNER] are the owner's; the
workplace built the tool, sized it, try-built it and dry-ran it. Tool `gpu/ohm_ruler_night.py`, with psf-os 0.3.3
(e652257, tag v0.3.3). Notes `notes/ohm_ruler_2026-11-24/`. When declared, this file moves to `prereg/` by home; the
tools are as of the declaring commit.

## Why (after the 11-23 record: the ideas below came after its data were seen)

- 2026-11-23 (`results/ohm-window-night-2026-11-23`, kingston): the window's raw M and W READS in all 24 cells. At t = 3
  the device's W was above the exact value by 11 to 26 % in every arm and twin.
- `notes/ohm_window_beside_2026-11-24` (beside, that record only): the excess was almost all a uniform shrink of the
  odd part of <Z>, O = (Z_s - Z_c) / 2.
  - One factor r of 0.86 to 0.89 per cell; after scaling by r, 10 to 16 % of the odd part's squared error is left.
  - r was the same in the light-cone circuit and the 40-qubit circuit.
  - Two rulers inside the job came near r, but both were poorly conditioned on the 11-12 strings:
    - the mirror's square root: 0.85 against 0.87, on one string;
    - the conserved total: 0.83 to 0.88 on the pair mean, but 0.59 to 1.19 per pair.
- Rule 3 allows a ruler that the circuit or its job carries in itself to be declared as part of the test. This test
  declares two, chooses strings whose own ruler is well conditioned, adds a mirror per cell, and asks whether the
  ruled window reads the transfer that the raw W overstates.

## Question

On the 11-12 Ohm circuits, with strings chosen by a rule on their bits alone, at t = 1, 3 and 4 cycles:
- does the window's transfer, divided by a ruler carried inside the circuit or its job, agree with the exact value?
- is the shrink one factor across the window's positions?
The raw M, W and S are read and reported as on 11-23.

## Circuits (`gpu/ohm_ruler_night.py`, on `gpu/ohm_answers.py` and `gpu/ohm_window_night.py`, both read only)

- **The circuits.** As 11-23: 40-qubit chain, fSim(pi/4, phi) brickwork from a weakly polarised wall (m 0.5).
  - A0: phi 0.
  - A1: phi pi/2.
  - A2: phi pi/2 with RZ(H p_k) after each cycle.
  - L is the light-cone circuit of the window (positions 20 .. 20 + 2t - 2), F the 40-qubit circuit. L sits on F's
    physical qubits at the same chain positions (pinned in the tool, as 11-23).
- **Strings, by the bits alone** (`strings`): the 11-12 generator (left half |1> with probability 0.75, right half
  0.25), seed **20261124**, drawn in order.
  - A string is kept when |T0| (the initial sum of Z, 1 - 2 b, over a region) is at least **6 on the window's light cone
    at each t >= 3** (16 qubits at t = 3, 22 at t = 4) and, when F is built, **8 or more on the whole chain**.
  - The first K kept strings and their complements are the test's strings. [OWNER: K and the thresholds]
  - On the 11-12 strings |T0| was 2 to 8 on the chain. Here, for K = 7 and L alone, |T0| is 6 to 12 on the cones, kept
    from 26 draws.
- **Cycles** t = 1, 3, 4. [OWNER]
- **Mirrors.** One per (arm, t, form), on string s00 of the cell: psf-os's user-entrance mirror, the compiled circuit
  and its inverse, ideal every qubit |0>. [OWNER: one per cell (proposed), or none]
- No floors (`--floors` adds them).
- No mid-circuit measurement and no delay: no qubit to park (the build checks and records it).

## The rulers (rule 3; written before the data)

Per pair k (string s_k and its complement c_k) and chain position q, the odd part is O_kq = (Z_s - Z_c) / 2. The raw W
of the pair is W_k = -sum_{q in window} O_kq / 2 + const_k. This is an identity of 11-23's definition
(W = (M_s - M_c) / 2), and const_k comes from the initial bits.

- **Ruler (a), the circuit's own total.** fSim and RZ keep the number of 1s, so on the circuit's measured qubits the
  exact total T_k = sum_q O_kq equals its initial value T0_k (from the bits).
  - rho_a,k = T_device,k / T0_k.
  - W_a,k is W_k with O_device replaced by O_device / rho_a,k.
  - Read where the string rule bounds |T0|: L at t >= 3, F at every t. L at t = 1 has 4 qubits and is not read.
- **Ruler (b), the same-layer mirror.** rho_b = sqrt(mean <Z> of the cell's mirror). W_b,k is W_k with O_device
  replaced by O_device / rho_b.
  - Why the square root: the mirror holds the layers twice.
  - Guess (not measured): rho_b follows r when the shrink accrues with the layers. A readout-like shrink, which hits the
    mirror once, leaves rho_b above r (the dry runs below).
- Without noise, rho_a = rho_b = 1 and W_a = W_b = W_exact. The sealed answers hold the exact window odd part, T0 and
  T_exact per pair.

## Job and seconds (the project's formula 2.6 s + 0.000269 s x circuits x shots; psf-os's model beside)

| plan [OWNER] | forms | t | pairs | mirrors | circuits | shots | seconds (formula) | psf-os model | try-build and check (11-23 kingston record) |
|---|---|---|---|---|---|---|---|---|---|
| A | L | 1, 3, 4 | 9 | 9 | 175 | 1000 | **49.7** | 56.5 | PASS |
| B | L | 1, 3, 4 | 7 | 9 | 139 | 1000 | 40.0 | 45.5 | PASS |
| C (smaller) | L | 3, 4 | 7 | 6 | 94 | 1000 | 27.9 | 31.8 | PASS |
| D (twins) | L and F | 1, 3, 4 | 7 | 18 | 274 | 600 | 46.8 | 57.3 | PASS (check 33.9 s) |

Each plan includes the ring sentinel's 4 circuits. Plan D's strings differ from A to C (the chain's |T0| enters the
rule). Proposed: A, because more pairs lower the SE that the words rest on (see the limits).

## Device and placement (no quality number)

- As 11-23: of ibm_fez and ibm_kingston, the one with fewer pending jobs (`pick`); not ibm_marrakesh. The chain by
  `gpu/hub_build.py`'s rule.
- The device record's lengths of time are read by psf-os 0.3.3; no error number is read.

## Answers (sealed)

`answers OUT --pairs K --ts ... --forms ...`:
- per-qubit <Z> of every item: A0 F by free fermions, the rest by quimb CircuitMPS (chi 2048, cutoff 1e-10);
- the rulers' exact values per pair.

Kept outside the notebook until the scores, with its sha256 written here at declaration. The try-build answers'
sha256 (to be made again at home with the same rule):
- A: e581df9d4fbb99ca...;
- B: 59cbd7a0c102f650...;
- D: 31e2f92a31fe4a56....

## Pre-run check (before submission): `check OUT ANS`

On the job's compiled circuits, noise-free (Aer statevector up to 12 qubits, MPS above):
- every item's per-qubit <Z> within 1e-6 of the answers;
- every mirror all |0> within 1e-6;
- every item's total <Z> equal to T0 within 1e-5 (the conservation the ruler rests on);
- the rulers' exact totals equal to T0;
- with F, the twins' windows equal within 1e-6;
- CZ as intended (the build refuses otherwise).

ALL PASS or no run.

## Verdicts (`score OUT ANS`) [OWNER]

Per cell (arm, t, form), over the K pairs, with SE from the pairs' scatter:

- **Raw** (as 11-23): window M and W, READS when the mean squared error is half the exact mean square or less.
  Beside: W excess (device - exact) with 2 SE, and S.
- **Ruler (a)**: d_a = mean_k (W_a,k - W_exact,k).
  - AGREES when |d_a| < 2 SE, DIFFERS otherwise.
  - Beside: 2 SE (the smallest difference this cell could see).
- **Ruler (b)**: d_b likewise. Its SE adds the mirror's shot noise, propagated through the square root. Words AGREES /
  DIFFERS.
- **One factor on the window** (t >= 3).
  - Per window position q: r_q = sum_k O_device,kq O_exact,kq / sum_k O_exact,kq^2, with its shot-noise SE
    (var Z = (1 - Z^2) / shots).
  - Positions with sum_k O_exact,kq^2 below 0.05 K take no part (decided by the answers alone).
  - chi2 of r_q around their weighted mean, with n - 1 degrees of freedom. UNIFORM when p >= 0.05, NOT UNIFORM when
    p < 0.05, NOT READ with fewer than 2 positions.
- Beside, never judged:
  - the order of W, W_a and W_b at t = 3 and 4 (A0 > A1 > A2);
  - W(t) / W(1), raw and ruled, against the exact ratio;
  - with F, the 11-23 twins' word (MSE F - MSE L);
  - the sentinel.

## Reading tables (fixed before the data; every combination on one row) [OWNER]

Table 1, per cell at t >= 3 (one factor x ruler (a): 3 x 2 = 6 rows):

| one factor | ruler (a) | reading |
|---|---|---|
| UNIFORM | AGREES | the shrink is one factor on the window, and the circuit's own total carries it: the transfer reads through ruler (a) |
| UNIFORM | DIFFERS | one factor on the window, but the circuit's total carries another (the outside of the window shrinks differently): ruler (a) not read for the transfer |
| NOT UNIFORM | AGREES | the total carries the window's mean shrink, but the window's positions differ: the transfer reads on the mean, not per position |
| NOT UNIFORM | DIFFERS | neither one factor nor the total's: ruler (a) not read |
| NOT READ | AGREES | too few window positions to test one factor; ruler (a) agrees |
| NOT READ | DIFFERS | too few window positions to test one factor; ruler (a) differs |

Table 2, per cell with a mirror where ruler (a) is read (2 x 2 = 4 rows):

| ruler (a) | ruler (b) | reading |
|---|---|---|
| AGREES | AGREES | both rulers read the transfer |
| AGREES | DIFFERS | the circuit's total reads it; the mirror's square root does not |
| DIFFERS | AGREES | the mirror's square root reads it; the circuit's total does not |
| DIFFERS | DIFFERS | neither ruler reads it |

The raw words keep 11-23's meaning and are read on their own line. A cell where ruler (a) is not read (L at t = 1)
reads ruler (b) and the raw words.

## Predictions [OWNER] (candidates, each grounded on the 11-23 record; written after that record was seen)

- OR-1: the raw W READS at t = 3 in every arm. 11-23: every cell READS, ratios 0.010 to 0.049.
- OR-2: at t = 3 the raw W is above the exact value in every arm. 11-23: +0.083 to +0.135, each beyond 2 SE.
- OR-3: ruler (a) AGREES at t = 3 in every arm. Ground: 11-23's uniform shrink (beside). The 11-12 strings did not allow
  a well-conditioned ruler (a), so this is the weakest ground. The VS's gate-noise dry runs (above) speak against it:
  with any p2 >= 0.005, ruler (a) DIFFERS at t = 3 in 29 or 30 of 30 cells.
- OR-4: the pooled r of the window at t = 3 lies in 0.86 to 0.89. 11-23 beside: r 0.863 to 0.891; another day and other
  strings.
- No prediction is proposed for t = 4 or for ruler (b): no record reads them. Ruler (b)'s ground is one string at
  t = 1 and 3.

## Dry runs (no device; `notes/ohm_ruler_2026-11-24/`)

Plan B, built on the 11-23 kingston record. The sentinel is not sampled. `dry.py` samples every other circuit
noise-free, then, optionally, flips each measured bit with probability q (ILLUSTRATIVE, written by hand).

| noise | raw W at t = 3, 4 | ruler (a) | ruler (b) | one factor |
|---|---|---|---|---|
| none | READS everywhere, excess within 2 SE | AGREES 6 of 6 | AGREES 6 of 6 | UNIFORM 4 of 6 (2 NOT UNIFORM at p 0.011, 0.049) |
| bit flips q 0.065 (r = 0.87, once) | READS (ratios 0.058 to 0.221), excess +0.17 to +0.30 | AGREES 5 of 6 (A1 t = 3 DIFFERS, d -0.014, 2 SE 0.010) | DIFFERS 6 of 6 (sqrt(mirror) 0.93) | UNIFORM 6 of 6 |

How often the words fire over seeds (`notes/ohm_ruler_2026-11-24/seeds.txt`, plan B, 16 seeds each):

| noise | ruler (a) DIFFERS | ruler (b) DIFFERS | NOT UNIFORM | raw W DOES NOT READ |
|---|---|---|---|---|
| none | 12 of 96 (12 %) | 16 of 144 (11 %) | 4 of 96 (4 %) | 0 of 144 |
| bit flips q 0.065 | 9 of 96 (9 %) | 104 of 144 (72 %) | 5 of 96 (5 %) | 0 of 144 |

Without noise every DIFFERS is false; the rate is near the 9 % that 2 SE from 7 pairs gives (t, 6 degrees of
freedom). NOT UNIFORM fires near its 5 % level.

The workplace VS (その1, 2026-11-24, on bd19d464; its report and scripts travel beside this draft, outside the
notebook) re-computed the rulers independently (largest difference from `score` 0, plans B and B9) and ran plan B with
gate noise: two-qubit depolarizing p2 per CZ and readout flips q, ILLUSTRATIVE, not fitted to a device; Aer MPS
trajectories, 10 seeds, t = 1 and 3 (t = 4 with gate noise was not run: over 2 hours per seed). At t = 3, 30 cells
per row:

| p2 | q | ruler (a) AGREES | ruler (b) AGREES | UNIFORM | raw W excess (mean) | r - sqrt(mirror) (mean) | r - rho_a (mean) |
|---|---|---|---|---|---|---|---|
| 0 | 0 | 26 (87 %) | 26 (87 %) | 28 (93 %) | -0.000 | +0.000 | +0.000 |
| 0 | 0.02 | 24 (80 %) | 2 (7 %) | 28 (93 %) | +0.056 | -0.020 | +0.000 |
| 0.005 | 0 | 1 (3 %) | 26 (87 %) | 26 (87 %) | +0.111 | -0.000 | -0.025 |
| 0.005 | 0.02 | 1 (3 %) | 7 (23 %) | 27 (90 %) | +0.163 | -0.019 | -0.023 |
| 0.01 | 0 | 0 (0 %) | 26 (87 %) | 25 (83 %) | +0.212 | -0.004 | -0.048 |
| 0.01 | 0.02 | 0 (0 %) | 10 (33 %) | 25 (83 %) | +0.261 | -0.021 | -0.045 |
| 0.02 | 0 | 0 (0 %) | 18 (60 %) | 24 (80 %) | +0.392 | -0.018 | -0.084 |
| 0.02 | 0.02 | 0 (0 %) | 7 (23 %) | 23 (77 %) | +0.433 | -0.031 | -0.081 |

- Under gate noise the window shrinks more than the circuit's total: r - rho_a is negative and grows with p2, and
  ruler (a) DIFFERS in nearly every cell. Guess (not measured): the window sits in the middle of the light cone and
  passes more CZ than the cone's edges, and depolarizing does not keep the number of 1s.
- Under gate noise alone, sqrt(mirror) follows r up to p2 0.01; a readout share moves it by about -0.02.
- The two rulers part in opposite ways: (a) holds under a readout-like shrink, (b) under a layer-accumulated one.
- The false rates with 9 pairs (B9, 16 seeds): ruler (a) 11 of 96, ruler (b) 16 of 144, NOT UNIFORM 5 of 96, against
  12, 15 and 9 with 7 pairs on the VS's seeds; within the seeds' scatter (about 3 points).

## Device procedure (home)

```
python gpu/ohm_ruler_night.py strings --pairs 9 --ts 1 3 4 --forms L        # the kept strings (bits only)
python gpu/ohm_ruler_night.py answers ANS.json --pairs 9 --ts 1 3 4 --forms L   # sealed, outside the notebook; sha256 here
python gpu/ohm_ruler_night.py pick fetch_in/queue.json                        # fez or kingston
python gpu/ohm_ruler_night.py build DEV OUT ANS.json ANS_BY_LABEL.json        # 175 circuits, 49.7 s (plan A)
python gpu/ohm_ruler_night.py check OUT ANS_BY_LABEL.json                     # ALL PASS or no run
python -m psf_os submit OUT/job ; python -m psf_os collect OUT/job
python gpu/ohm_ruler_night.py score OUT ANS_BY_LABEL.json
```

## Limits

- **The words rest on K pairs.** With 7 pairs, "2 SE" from the pairs' scatter fires falsely about 9 % of the time
  (t with 6 degrees of freedom), and the dry runs show such single DIFFERS. More pairs (plan A, 9) narrow this.
  [OWNER: 2 SE as the project's rule, or the t quantile]
- The one-factor test assumes the positions scatter by shot noise around one factor. Other scatter between pairs
  (e.g. place-dependent noise) reads as NOT UNIFORM. Without noise, a false NOT UNIFORM came 4 times in 96 cells over
  16 seeds (one per seed or none); in the first dry run, on another seed, 2 of 6.
- Ruler (a) assumes the conservation holds on the device's measured qubits, as it does exactly for the circuits.
  Leakage or a one-sided shift (decay) moves the total too. The even part is not divided by the ruler.
  It also assumes the window shrinks as the circuit's total does; under gate noise it does not (the VS's dry runs:
  the window shrinks more, r - rho_a -0.025 to -0.084 for p2 0.005 to 0.02).
- Ruler (b) assumes the shrink doubles with the layers. A readout share does not double (the dry runs; about -0.02 in
  r - sqrt(mirror) for q 0.02).
- One device night. The ideas came after the 11-23 record was seen. The strings are new, by a bits-only rule.
- Not error correction, not post-selection: every shot counts, and the rulers are declared before the data (rule 3).
