# Every branch of the compounding OS's rule, under an illustrative noise (workplace VS Claude, 2026-11-18; desk only)

**The noise here is an illustration.** It is uniform and written by hand. It was not fitted to any device, and no
calibration number was read. Its only job is to make every branch of `gpu/os2_night.py`'s rule happen inside a run
before the night. Noiselessly the os_night rule picks P0 (or, from a recorded pick, the rule only steps back by R3).

- **Tool:** `branch_noise.py`.
  - `noisy_run_local(OUT, noise)` is a drop-in for `psf_os.feedforward.run_local`.
  - `loop` runs the night's order: Dw, Dc, the os_night rule, then os2_night rounds, with every job run under that
    noise.
- **Summary:** `branches_summary.json`.
- **Record:** the 11-17 ibm_marrakesh record (`results/balanced-night-2026-11-17/fetch_in/ibm_marrakesh/dev`).
- **Environment:** psf-os 0f57c76; the notebook at af5d6471 plus the 17f merge.

## The noise

- **gamma:** amplitude damping |1> -> |0> with probability gamma.
  - It acts on every other touched qubit during each mid-circuit measurement.
  - Consecutive measurements count as one simultaneous read, because IBM runs measurements on disjoint qubits in one
    block. So the damping falls once, after the group.
- **p11 per physical qubit:** P(read 1 | 1). For example, one qubit at 0.83, the size of the 2026-11-17 q1 readout gap,
  as an example only.
- **Sentinel:** the diagnostics are built with the Clifford sentinel, which runs noiselessly. Their own tools have no
  dry flag, and run_local refuses the 40-qubit h = 0.6 sentinel.

## Which setting makes which branch happen

| run | noise | os_night pick (L 1/2/3) | rounds (stacks -> rule) | stop | model s |
|---|---|---|---|---|---|
| s0 | none | P0/P0/P0 | 1: NO PRESCRIPTION everywhere | fixed point | 76.1 |
| s6 | gamma 0.01 | P1/P1/P1 | 1, 2: NOT SHOWN everywhere -> **R3** to P0; 3: P0 | fixed point | 137.9 |
| s8 | gamma 0.02, q3 p11 0.83 | P1/P2/P1 | 1: L2 OVERSHOOT -> **R1** P2+B; 2: L2 nf share below rd, Dr on q3 -> **R2** +Q2; L1 NOT SHOWN twice -> **R3** P0; 3: no change | fixed point | 151.2 |
| s5 | gamma 0.03, q1 p11 0.83 | P2/P1/P1 | 1: R1 at L1, L3; 2: R2 +Q2 at L1; L3 NOT SHOWN (first); 3: L3 NOT SHOWN again -> R3 P2+B -> P2; 4: no change | fixed point | 195.5 |
| s5k3 | as s5, K_MAX 3 (dry only) | as s5 | as s5, rounds 1-3 | **round limit** | 161.3 |
| s1b | gamma 0.08, q1 p11 0.83, budget 150 s (dry only) | P2/P1/P1 | 1: R1 at L1, L3; 2: R2 +Q2 at L1 | **budget** before round 3 (123.7 + 37.6 > 150; not run) | 123.7 |
| s1 | gamma 0.08, q1 p11 0.83 | P2/P1/P1 | 1: R1; 2: R2 +Q2; 3: no change | fixed point | 161.3 |

## What the runs show about the declared values

**The budget cannot bind at K_MAX 4.**
- On this record a round costs at most 40.9 s (every L with +B: 34 circuits). Dw and Dc cost 55.2 s together.
- So a night is at most 55.2 + 4 x 40.9 = 218.8 s, below 240.
- The budget stop happens only with a lower budget, which is for dry runs only.

**K_MAX 4 rarely binds.**
- The ladder has at most three moves: base -> +B -> +Q, then R3 or a fixed point.
- Every setting found stops at a fixed point by round 4.
- The round limit happened with K_MAX 3 (dry only).

**The OS-compounding verdict often has no L.**
- An L that overshoots in round 1 (common under decay) is never credited "in every round".
- In s1, s5 and s8 the compounding verdict was NOT SHOWN, with few or no common L.
- How a night with no common L is worded is for the declaration to state.

**Not exercised here:** a check FAIL and a build refusal inside a run.
- These are `gpu/os2_run.py`'s stops. They are to be run through `go --dry` once it exists.
- The rule's own refusal of a +Q offset off the probe's chain never happened on the three 11-17 records (see the
  review).

## Seeds per round (home addendum, 2026-11-18)

**The ask:** round k at 20261118 + k; Dw at 20261118 and Dc at 20261118 + 100; the seed recorded per job.
`branch_noise.loop --seed-scheme` now writes `seed.json` into every job folder (and the seed into submission.json),
so verify can rebuild the counts. The same seeds can be passed to `FF.run_local(out, seed=...)`.

**What was found: these formulas barely change the counts.**
- Aer gives shot j of a run the seed seed_simulator + j. This was checked with qiskit-aer 0.18.0 on a circuit with a
  mid-circuit read, at 4000 shots:
  - seeds 0, 1, 10 and 100 apart gave 2730 / 2730 / 2728 / 2730 counts of the same outcome;
  - 10000 apart gave 2699.
- So 20261118 + k, + 10 k and the earlier + 100 k share almost all the per-shot seeds from round to round.
- The circuits within one job (seed + i, as in run_local) share them too. P0 and the pick then move together, and g
  hardly moves (about 1e-4 between rounds, against about 7e-3 of shot noise).
- **The "wide" formulas keep the seed ranges apart:**
  - Dw at B; Dc at B + 500000; round k at B + 1000000 k; circuit i at seed + 10000 i.
  - B = 20261118 ("wide") or B + 70000000 ("wide_alt", the chance check).
  - `wide` is the loop's default now.

**Branches by formula** (event@round and L; the same settings as the table above; `seed_compare.json`):

| run | same / + k / + 10 k (all three alike) | wide | wide_alt |
|---|---|---|---|
| s0 (none) | fixed point at round 1 | same | same |
| s6 (gamma 0.01) | R3@r2 for L1-3; fixed point at r3 | same | R1@r1 L2; R3@r2 L1, L3; R3@r3 L2; fixed point at r4 |
| s8 (gamma 0.02, q3 0.83) | R1@r1 L2; R3@r2 L1; R2@r2 L2; fixed point at r3 | same | same |
| s5 (gamma 0.03, q1 0.83) | R1@r1 L1, L3; R2@r2 L1; R3@r3 L3; fixed point at r4 | R1@r1 L1; R2@r2 L1; **no R3**; fixed point at r3 | R1@r1 L1, L2; R2@r2 L1; R1@r2 L3; R3@r3 L2; R3@r4 L3; **round limit K = 4** |
| s5k3 (K 3, dry only) | as s5 to r3; round limit | fixed point at r3 | round limit at r3 |
| s1b (budget 150, dry only) | R1@r1 L1, L3; R2@r2 L1; budget before r3 | R1@r1 L1-3; R2@r2 L1; budget before r3 | as wide |

**Reading:**
- With the overlapping formulas, the branch history is the same under all three. What a dry run shows is then one
  draw, repeated.
- With independent seeds:
  - R3 at a clear NOT SHOWN (s6, g near 0) happens every time.
  - Where g lies near its 2 SE line (s5 L3, s6 L2), R3 and R1 appear or vanish with the seed: wide removes s5's R3,
    and wide_alt adds two.
- So the overlap did not make R3 more likely in general. It froze one draw. Whether R3 happens near the line is
  chance, in a dry run as on the device.
- The round limit at K = 4 does happen (s5, wide_alt). "K_MAX 4 rarely binds" above is to be read as: it depends on
  the draw.
- **For noiseless dry runs:** `FF.run_local` (psf-os, unchanged) seeds circuit i at seed + i, so the circuits of one
  job overlap in it whatever the job seed. `noisy_run_local(out, {}, seed, 10000)` writes the same files, noiselessly,
  with the wide spacing.
