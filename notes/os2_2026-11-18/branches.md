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
