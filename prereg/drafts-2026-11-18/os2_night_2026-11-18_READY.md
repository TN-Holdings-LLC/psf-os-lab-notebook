# Declared: the prescription loop with compounding, run end to end on the device, night of 2026-11-18

Workplace Claude, 2026-11-18 (home instruction "複利の OS を今夜実機で"; the owner's choices of 08:5x JST). READY text:
moved to `prereg/os2_night_2026-11-18.md` and committed at home; declared when that commit is pushed, before the
device records of the night are fetched. The tools are as of that commit: `gpu/os2_run.py` (runs the night),
`gpu/os2_night.py` (rule, build, check, score, compound), `gpu/os_night.py`, `gpu/wait_night.py`, `gpu/ctrl_night.py`
(round 1 and its diagnostics, unchanged), `gpu/job_timing.py`. "Compounding" here: one round's result is an input of
the next round's choice, and the choices stack up (the owner, 2026-11-18).

## Common

- psf-os branch feedforward-2026-11-16 at 0f57c76 (checked by `os2_run.py preflight`). The notebook checkout is this
  declaration's commit (preflight: HEAD = the commit that last changed this file, no tracked file changed).
- Device by the standing rule (`gpu/daily_fetch.py`: every device of ibm_marrakesh, ibm_fez, ibm_kingston with at most
  10 pending jobs, else the fewest), the first chosen in that order; one device record for the whole night (every job).
- Rule C placement (coupling graph and failed marks only); no mitigation; dynamical decoupling and twirling off; 4000
  shots per circuit; every shot counted in every verdict; no calibration number is read by any rule.
- **Items with conditional operations are not packed** into one circuit (2026-11-17, fifth round: the packed control
  arm kept 0.20 less; until the mechanism is known). Every item is its own circuit.
- Every job's `check` (noiseless Aer of every arm but the sentinel) before it is submitted; a FAIL stops the night and
  nothing more is submitted.
- One command runs the night without a person in between (`python gpu/os2_run.py go OUT --zip ZIPFILE`): device
  record, diagnostics, round 1, then score -> rule -> next round until a stop. The next round's rule output
  (`RULE{k+1}.json`) is written from the recorded scores before that round's job is built; nothing is re-chosen after a
  job's data. A job folder with a submission is never submitted again (`resume` continues a stopped night).

## Step 1: diagnostics (unchanged tools of 2026-11-16 / 17)

Dw (`gpu/wait_night.py` items, 22 circuits, 27.6 s by the model) and Dc (`gpu/ctrl_night.py` items, 22 circuits,
27.6 s). Only the numbers the rule of 2026-11-17 reads are used; their tools' own prediction lines are not judged.

## Step 2: round 1 = the rule of 2026-11-17 (`gpu/os_night.py rule`, unchanged)

P0 the circuit as written (rus_chain m = 3), P1 hold flipped, P2 P1 + read flipped, P3 fewer tries; the order and
thresholds of `prereg/os_night_2026-11-17.md`.

## Step 3: the rounds (`gpu/os2_night.py`)

Each round's job, per L = 1, 2, 3: p0_L (P0; the same circuits in every round), the stack's item(s) (one circuit, or
the two frames rd and nf for +B), and the readout probe "dr" (X then read at once on chain positions 1, 3, 5, 7, 9;
P(0|0) from its floor arm); ff, off and floor arms; one ring sentinel. 16 circuits / 20.9 s (every L at P0) to 34
circuits / 40.9 s (every L with +B) by the model, on the 2026-11-17 records of marrakesh, fez and kingston.

The ladder (layers added only in this order, removed only from the end): base (round 1's pick) -> +B (frame balance:
the P2 circuit and its complementary frame nf, pooled P = (P_rd + P_nf) / 2; the base becomes P2) -> +Q (both frames
placed on the rule-C chain shifted by 2 or 4 sites, the offset whose output qubit has the smallest readout gap Dr from
this round's probe; ties: the smaller offset; offset 0 means no change).

**The rule for round k + 1, per L, first match wins (every threshold: the quantity >= 2 SE of itself):**
1. R1 overshoot: round k's stack OVERSHOOT and has no +B -> P2 + B.
2. R2 frames: the stack has +B and no +Q; the nf frame keeps a smaller share of its noiseless value than rd; and the
   Dr gap (P(0|0) - P(1|1)) on nf's output qubit is >= 2 SE -> add +Q.
3. R3 stop-loss: NOT SHOWN in round k and in round k - 1 with the same stack -> remove the last layer (a bare base
   other than P0 goes to P0).
4. R4: otherwise keep.

**Stops:**
- after round k when every L keeps its stack, none overshoots in round k and none is NOT SHOWN for the first time (a
  fixed point);
- after round K_MAX = 4;
- before round k is built, when the diagnostics + the rounds built + round k's model seconds would pass 240 s (round
  k's seconds: psf-os's time model on a build of RULE{k}.json in a temporary folder); round k is then not built and
  nothing more is sent;
- at a check FAIL (that job is not sent) or a refused build or submission.
K_MAX and the budget are fixed for the device run (os2_run.py accepts overrides only with --dry). The reason is
written to `OUT/stop.json`. (On the 2026-11-17 records of marrakesh, fez and kingston a night takes 76.1 s at least,
every L at P0 and a fixed point after round 1, and 218.8 s at most, four rounds with +B at every L; the 240 s budget
cannot bind with K_MAX 4 on those records.)

## Verdicts (`gpu/os2_night.py score`, per round, per L with a stack other than P0)

g = |P_ff(P0) - exact| - |P(stack) - exact|, SE of the difference (binomial, every shot of both). **OVERSHOOT** when
P(stack) > its noiseless value + 2 SE (one-sided decay toward |0> read through a flipped frame can lift it);
**PRESCRIPTION HELPS** when g > 0 and g >= 2 SE; otherwise **NOT SHOWN**. P0 alone: **NO PRESCRIPTION**. The primary
verdicts are those of the last round run.

**The OS's own compounding, beside (not a prediction; the owner, 2026-11-18 09:3x JST):** G_k = the mean of g over
the L credited (no overshoot) in every round run, its SE, and with three rounds or more the weighted least-squares
slope of G_k over k (with two rounds their difference), reported as numbers only.

## Predictions (written before the data)

1. OS2-1 Between round 1 and round 2 the rule changes the stack of at least one L. (Fails also when the night stops
   before round 2 has run.)
2. OS2-2 In the last round run, no L overshoots.

Each prediction holds or fails as a whole and names its round(s); a prediction about "any round" or "the best round" is
not made. `os2_run.py` writes them, read from the records only, to `OUT/predictions.json`. Basis: the desk trial on
2026-11-17's records (round 1 = the loop's main job: L 1 OVERSHOOT, L 2, 3 HELPS; the rule changes L 1 to P2 + B; the
frame-balanced job an hour later, read as round 2: L 1 HELPS, then +Q4) and dry runs under example noises
(`notes/os2_2026-11-18/README.md`).

## Records and reproduction

`OUT` holds: run.json, run_log.txt, fetch_in/ (queue.json, the device records), dw/, dc/, os_rule.json, RULE{k}.json,
r{k}/ (build.json, rule.json, job/, runs/, round_scores.json, queue_after.json), queue_after_*.json, compound.json,
budget_r{k}.json, predictions.json, job_timing.json, stop.json; zipped to ZIPFILE. `python gpu/os2_run.py verify OUT` rebuilds every job from the
recorded device record and rule files (circuits.qpy byte for byte; manifest.json but for its write time), re-scores
every job from its recorded counts, re-applies every rule, re-reads the predictions, recomputes the stop reason: SAME
/ DIFFERENT.

Dry runs (`go OUT --dry DEVDIR [--noise NOISE.json]`, never the device) simulate every job locally (the workplace VS's
`notes/os2_2026-11-18/branch_noise.noisy_run_local`) with a fixed seed per job, the "wide" formula: Dw 20261118, Dc
20261118 + 500000, round k 20261118 + 1000000 k, circuit i of a job at that seed + 10000 i (Aer seeds shot j at seed +
j, so no two circuits of a night share a shot's seed); recorded in each job's submission.json; `verify --resim`
simulates again with the same seeds. An example noise is an illustration only, never fitted to a device.

Suggested entry for `reproduce.py` (the folder name at home's choice):

```python
    # needs psf-os at the branch feedforward-2026-11-16, 0f57c76 (--psf-os PATH)
    "os2-night-2026-11-18": ("results/os2-night-2026-11-18", ["."],
        ["gpu/os2_run.py", "verify", "{T}"], None),
```

(`verify` prints SAME / DIFFERENT itself and compares every scores and rule file; if reproduce.py needs a scores file
to compare, `compound.json` can be named in place of None.)
