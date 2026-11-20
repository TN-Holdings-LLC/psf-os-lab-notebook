# The paired loop: the incumbent and the candidate in one job (home VS Claude, 2026-11-21; desk only)

Home instruction `VSクロードへの指示_輪の改造_同じジョブで比べる_2026-11-21.md` (the owner's decision of 2026-11-20 20:05
JST). Not declared, no device. **Every noise here is an illustration** (branch_noise.py's form, written by hand, never
fitted to a device). The drift between jobs is a TYPE (the shape loopvar showed on 2026-11-20); its size is set to give
loopvar's excess between-job SD of g (0.007 - 0.014), and the values are written below.

## What was built

- **psf-os**, branch `loop-paired-2026-11-21` (from after-2026-11-20 = d4fb614):
  - `psf_os/loop.py`:
    - `paired_decision`: within one job, d = |P_inc - exact| - |P_cand - exact|. Adopted at d >= 2 SE; not adopted at
      d <= -2 SE or when the candidate overshoots; the incumbent is kept between.
    - `paired_next_candidate`: the next untried step. B after an overshoot, the diagnostics' base on P0, R2's Q on
      B, then the rungs M and F. A step that was not adopted is not tried again that night.
    - `next_stacks_paired`: the next rule. A key with no step left stops; the night stops when every key has stopped,
      or at the round limit or the budget.
    - `paired_rule1`: round 1. Every incumbent is P0; the candidate is the ledger's stack (same device and
      calibration time) or the diagnostics' stack.
    - `Night` with cfg `paired` and `verify` (re-rules round 1 and every rule). Both are off by default, so recorded
      nights rule and verify as before.
    - Option `climb_on_kept` (default off; see below).
  - `psf_os/feedforward.py`: `build(ff_only=...)`, for the incumbent's ff without its off and floor arms. The default
    is byte-identical to before.
  - `tests/test_loop_paired.py`: 9 tests. They cover every branch of the decision and of the next step, the stops,
    round 1 with the ledger, the climb option, a fake night run to its stop, verify SAME and then DIFFERENT after a
    change of counts or of a rule, resume without a second submission, paired off by default, and ff_only.
- **Notebook**: `gpu/os_loop_paired.py`. It is the experiment for the paired night; the declared os_loop / os3_night /
  os2_night are imported read only.
  - Per L that has a candidate, the job holds P0's three arms, the incumbent's ff (none while the incumbent is P0) and
    the candidate's three arms. The tags alternate who comes first by L.
  - Commands: `go` / `resume` / `verify` / `size`.

## One job's size (2026-11-19 marrakesh record, `size`)

| round | circuits | model seconds |
|---|---|---|
| round 1 (incumbent P0, candidate P1 at every L) | 25 | 30.9 |
| incumbent P1, candidate P1+M at every L | 28 | 34.2 |
| incumbent P2+B, candidate P2+B+Q2 at every L (largest) | 40 | 47.6 |

Every round is under 60 s. The night's budget of 240 s, with the diagnostics' 55.2 s, holds 4 to 5 rounds.

## Dry nights end to end (`go --dry`, then `verify --resim`: every line SAME)

- **N1** (gamma 0.05, q1 P(1|1) 0.83):
  - r1: L1 P2 OVERSHOOTS, L2 P1 ADOPTED, L3 P1 OVERSHOOTS.
  - r2: L1 P2+B ADOPTED, L2 P1+M ADOPTED, L3 P2+B ADOPTED.
  - r3: L1 P2+B+Q2 ADOPTED.
  - It stops after round 3 with no step left; 154.6 s with the diagnostics.
- **N3** (gamma 0.02) with `--climb-on-kept`:
  - r1: L1 and L2 P1 KEPT (within error), so the next candidate climbs on P1; L3 P1 ADOPTED.
  - r2: P1+M ADOPTED at every L. It stops after round 2.

## Simulated nights: the current rule against the paired one (`sim_compare.py`; 50 nights each, the same seeds)

`catalog.py` gives the exact share of every circuit a stack can use, under each noise, on a grid of damping
(`cat_N*.json`). `sim_compare.py` draws each job's damping from gamma (1 + eps) with eps ~ Normal(0, s), samples
4000 shots per circuit, and applies psf-os's own `next_stacks` and `next_stacks_paired`.

**Truth** is decided without drift and without shot noise: the distance to exact. A share above the stack's noiseless
value by more than 2 SE (the rules' OVERSHOOT, an artifact of the noise) is credited as P0's. The literal distance is
in the json too.

- **Wrong step**: a change of stack not truly better by more than 0.005. The first step from P0 counts.
- **Missed**: an L whose final stack has a one-step neighbour truly better by more than 0.005.

The drift is s = 0.07 (N1), 0.05 (N2), 0.15 (N3). It gives between-job SDs of g at L = 1 / 2 / 3 of 0.005 / 0.011 /
0.013 (N1), 0.007 / 0.012 / 0.013 (N2) and 0.005 / 0.010 / 0.014 (N3). Twice s is beside.

| noise, drift | rule | wrong steps / night | missed L / night | final distance | seconds | rounds |
|---|---|---|---|---|---|---|
| N1, s 0.07 | current | 2.24 | 0.00 | 0.0962 | 162.2 | 3.06 |
| | paired | **0.42** | 0.04 | 0.0982 | 154.1 | 3.00 |
| | paired + climb | 0.42 | 0.04 | 0.0982 | 154.1 | 3.00 |
| N2, s 0.05 | current | 3.08 | 0.00 | 0.1751 | 128.3 | 2.08 |
| | paired | **0.56** | 0.08 | 0.1762 | 128.1 | 2.08 |
| | paired + climb | 0.56 | 0.08 | 0.1762 | 128.1 | 2.08 |
| N3, s 0.15 | current | 2.96 | 1.12 | 0.0613 | 158.9 | 3.42 |
| | paired | **0.06** | 1.34 | 0.0731 | 104.5 | 1.64 |
| | paired + climb | **0.06** | **0.26** | **0.0387** | 119.6 | 2.04 |

Every case, without drift and with twice the drift, is in `sim/summary.txt`; the per-night paths are in
`sim/N*_s*.json`.

Reading:

- **Fewer wrong steps.** The paired rule takes far fewer wrong steps under every noise. The current rule's wrong
  steps are mostly untested steps: round 1 applies the diagnostics' pick without a comparison, and RM adds M after
  a HELPS of the stack against P0 without comparing M with the stack itself.
- **The drift barely moves either rule.** At loopvar's size the numbers hardly change. Both rules read g inside one
  job (P0 sits in every job), so the drift reaches them only through verdicts near the threshold.
- **Weak noise and the plain paired rule.** When the base alone does nothing and base + M does (N3), the plain paired
  rule stops at P0 and misses: more misses than the current rule and a worse final distance.
- **Weak noise with `climb_on_kept`.** When the base is kept within error, the next candidate climbs on it (P1 + M
  against P0). This brings N3's misses from 1.34 to 0.26 L per night and gives the best final distance, with fewer
  seconds than the current rule. Under N1 and N2 it changes nothing.
- **Wrong steps that are left.** The paired rule's remaining wrong steps (0.4 - 0.7 under N1 and N2) are adoptions of
  a stack whose true share sits within 2 SE above its noiseless value (credited as P0 by the truth used here). Under
  the literal distance they count 0.

## Files

- `catalog.py`, `cat_N1.json`, `cat_N2.json`, `cat_N3.json`, `noise_N*.json`
- `sim_compare.py`, `sim/` (summary.txt, one json per noise and drift)
