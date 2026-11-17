# DRAFT (not declared): the prescription loop with compounding, a night of up to four rounds (workplace Claude, 2026-11-18)

Home handover 2026-11-17 night, section 3. A draft: every threshold, verdict word, limit and prediction marked [OWNER]
is the owner's; the declaration is written and pushed at home. Tool: `gpu/os2_night.py` (round1 / build / check /
score / rule / compound / trial). Design notes and the desk trial: `notes/os2_2026-11-18/README.md`.

## What "compounding" means here (to confirm with the owner)

Home's reading, used in this draft: one round's result is an input of the next round's choice, and the choices stack
up. If the owner meant something else, this draft is to be redone before anything is declared.

## Common

As `prereg/os_night_2026-11-17.md`: psf-os feedforward-2026-11-16 at [OWNER: commit, 0f57c76 needed for the placement
from outside]; device by the standing rule, one device record for the whole night (every round); rule C placement;
no mitigation; DD and twirling off; 4000 shots; every shot counted; each job's `check` before it is submitted (a FAIL
stops the night); the next round's rule output written (`RULE{k+1}.json`) before that round's job is built; nothing is
re-chosen after a job's data. No calibration number is read by the rule.

**Conditional items are not packed** (the fifth round of 2026-11-17: the packed control arm kept 0.20 less; until the
mechanism is known).

## The list and the ladder (fixed; no search)

- Base (round 1, gpu/os_night.py's rule and diagnostics unchanged): P0 the circuit as written (rus_chain m = 3); P1 hold
  flipped; P2 P1 + read flipped; P3 fewer tries.
- +B frame balance: the P2 circuit and its complementary frame (no flips) pooled, P = (P_rd + P_nf) / 2 (as
  `prereg/balanced_night_2026-11-17.md`); the base becomes P2.
- +Q output-qubit choice: the item placed on the night's rule-C chain shifted by an offset o in {0, 2, 4}, o the
  candidate whose last output qubit has the smallest readout gap Dr; ties: the smaller o.
- Layers are added only in this order (base, +B, +Q) and removed only from the end.

## Each round's job

Per L = 1, 2, 3: p0_L (P0, the same circuits in every round), the picked stack (one item, or the two frames for +B),
and one probe item "dr" (X then read at once on chain positions 1, 3, 5, 7, 9; P(0|0) from its floor arm). ff, off,
floor arms; one ring sentinel. Size on the 2026-11-17 marrakesh record: 25 circuits, 30.9 s (P2 at every L) to 31
circuits, 37.6 s (two L with +B); 16 circuits, 20.9 s when every L is P0.

## Verdicts per round (as gpu/os_night.py; [OWNER])

Per L with a stack other than P0: g = |P_ff(P0) - exact| - |P(stack) - exact|, SE of the difference. **OVERSHOOT**
when P(stack) > its noiseless value + 2 SE; **PRESCRIPTION HELPS** when g >= 2 SE [OWNER: 2 SE, or 2.5 SE when more
than one round's verdict enters one prediction]; otherwise **NOT SHOWN**. P0: NO PRESCRIPTION.

## The rule between rounds (fixed order, first match wins; thresholds 2 SE of the quantity itself [OWNER])

1. R1 overshoot: the stack OVERSHOOT in round k and has no +B -> P2 + B.
2. R2 frames: the stack has +B and no +Q, the nf frame keeps a smaller share of its noiseless value than rd (>= 2 SE),
   and the Dr gap on nf's output qubit is >= 2 SE -> add +Q (the offset by Dr).
3. R3 stop-loss: NOT SHOWN in round k and in round k - 1 with the same stack -> remove the last layer (a bare base
   other than P0 goes to P0).
4. R4: otherwise keep.

Inputs the rule reads: the rounds' own `round_scores.json` (verdicts, overshoot flags, the frames' shares, P0) and Dr
from the round's probe (round 1: the os_night diagnostics' Dr). Nothing else.

## Stopping and the number of looks

- Stop after round k when every L keeps its stack, none overshoots in round k and none is NOT SHOWN for the first time
  (a fixed point); or k = K_MAX [OWNER: 4]; or the next round would pass BUDGET [OWNER: 240 s by the model, all
  rounds]; or a check FAILs or a build refuses.
- Every round's verdict is formed on that round's own new job, and the stack it judges was chosen from earlier rounds
  only, so no verdict reuses the data that chose it. The family of looks: each prediction names the round(s) it is
  about; a prediction about "any round" or "the best round" is not allowed; the primary is the last round [OWNER].

## Across nights (what the rule may read from an earlier night; [OWNER] to fix before use)

Proposed: the earlier night's final stacks as round 1's start (in place of the diagnostics' pick) and its probe's Dr
per physical qubit, only when the device and the device record's calibration date are the same. Not read: any
calibration error number; any earlier verdict as a threshold.

## The OS's own compounding

Per round G_k = mean of g over the L credited (no overshoot) in every round compared; weighted least-squares slope of
G_k over k. **OS COMPOUNDS** [OWNER] when the slope >= 2 SE and no L overshoots in the last round; otherwise NOT SHOWN.
With two rounds only a difference is formed (beside). Caution, from the trial: G can only grow where the rule changes a
stack; an L that keeps its stack contributes a repeat, not a step.

## Predictions [OWNER]

Forms only: OS2-1 the rule changes at least one stack between round 1 and round 2. OS2-2 no L overshoots in the last
round. OS2-3 OS COMPOUNDS (needs three rounds with credited g). Numbers and whether each is made: the owner's.

## The desk trial on 2026-11-17's records (`python gpu/os2_night.py trial`)

Round 1 = the loop's main job (P2 at L = 1, 2, 3): L 1 OVERSHOOT, L 2, 3 HELPS. Rule -> round 2: L 1 P2 + B, L 2, 3
keep P2. Round 2 'as if' = the frame-balanced job an hour later, which held exactly those circuits (g against round 1's
P0, another job): L 1 +0.057 HELPS (no overshoot; rd share 1.013, nf 0.727), L 2 +0.049, L 3 +0.083 HELPS. Rule ->
round 3: L 1 P2 + B + Q4 (nf's output qubit 1 has the Dr gap +0.174; offset 4 puts it on qubit 5, gap +0.0055), L 2, 3
keep. OS compounding over L = 2, 3 (the L credited in both): +0.061 -> +0.066, a difference +0.005 (2 SE 0.021), NOT
SHOWN, as expected for stacks that did not change.
