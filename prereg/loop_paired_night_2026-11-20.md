# Declared: the paired loop, the incumbent and the candidate in one job, night of 2026-11-20 (second run)

Home Claude, 2026-11-20 evening, from the home VS's draft `prereg/drafts-2026-11-21/loop_paired_DRAFT.md` (9ba8f9c8) on
the owner's choices of 2026-11-20 20:5x JST: `climb_on_kept` on, K = 4, budget 240 s, the prediction LP-2 only, the
ledger passed as it is. The owner moved the run to the same evening ("今晩でもよい"). Declared when the commit that adds
this file is pushed, before the night's device record is fetched; the tools are as of that commit, psf-os branch
loop-paired-2026-11-21 at a164fc5 (the home VS's full tests 356 passed, 1 skipped). Tool `gpu/os_loop_paired.py`.
The ledger: a copy of `results/loop-night-2026-11-19/os-ledger_after.json` (its last line is 2026-11-19's, calibration
2026-11-19 10:59:49+01:00; used only on the same device and calibration time, as declared on 2026-11-19).

## Why

- 2026-11-20 loopvar (`results/loopvar-night-2026-11-20`): copies inside one job agree (the nine pooled, p 0.625).
  Jobs minutes apart moved beyond shot noise at L 2 (p 0.006, excess SD 0.014, g changed sign).
- The current loop reads each round's g against P0 inside its job. Its steps, though, are taken without comparing the
  step itself:
  - round 1 applies the diagnostics' pick;
  - RM adds M after a HELPS of the stack against P0;
  - R3 steps back on two NOT SHOWN in two jobs.
  2026-11-19 is an example: rounds 1 and 2 ran the same stack and read +0.006 then +0.018; the second read triggered
  RM.
- The receiver `between_job_sigma` widens the threshold. Re-judged on 2026-11-19, it removes that night's largest
  step (+M, g 0.047) (`notes/receivers_2026-11-20/rejudge_loop.md`).
- The paired loop puts the incumbent and the next candidate side by side in one job and decides by their difference
  there.

## The rule (psf_os.loop.next_stacks_paired)

Per L, an incumbent and a candidate.

1. **Round 1.** The incumbent is P0. The candidate is the diagnostics' base (gpu/os_night.py's rule, as 2026-11-19),
   or the ledger's stack on the same device with the same calibration time (the ledger as declared on 2026-11-19).
2. **One job per round.** Per L with a candidate, on the same qubits:
   - P0's three arms (g beside; it is the incumbent while the incumbent is P0);
   - the incumbent's ff;
   - the candidate's three arms;
   - the readout probe and the ring sentinel.
   The tags alternate who comes first by L.
3. **Decision**, per L inside the job: d = |P_incumbent - exact| - |P_candidate - exact|, with SE from both ff arms'
   shots.
   - CANDIDATE OVERSHOOTS (P > noiseless + 2 SE): not adopted.
   - d >= 2 SE: CANDIDATE ADOPTED.
   - d <= -2 SE: CANDIDATE NOT ADOPTED.
   - Otherwise: INCUMBENT KEPT. (These words; 2 SE.)
4. **Next candidate.** The next untried step on the incumbent:
   - B after an overshoot;
   - the base on P0;
   - Q on B (R2's conditions);
   - then M, then F (F only when Dr is against the base's frame).
   A step not adopted is not tried again that night. A key with no step left stops.
   The option `climb_on_kept` is **on** (the owner's choice): on INCUMBENT KEPT, the next candidate is built on the
   kept candidate (e.g. P1 + M against P0).
5. **Stops.**
   - Every key has stopped.
   - The round limit K = 4.
   - The budget, 240 s by the model with the diagnostics.
   - A check FAIL, a refused build, or a failed job: as declared on 2026-11-19.
6. **Beside, never in the decision.** Per round and L: g against P0 and os3's words (OVERSHOOT / PRESCRIPTION HELPS /
   NOT SHOWN); the compound rows.

## Size (2026-11-19 marrakesh record)

- 25 to 40 circuits per round, 30.9 to 47.6 s by the model.
- Diagnostics 55.2 s.
- Four rounds of 34 s: about 192 s.
- 4000 shots.

## Desk results (illustrative noise; `notes/loop_paired_2026-11-21/README.md`)

50 simulated nights per case, with a drift between jobs of loopvar's size:

- **Wrong steps per night.** Paired 0.06 to 0.56; current 2.2 to 3.1.
- **Strong noise (N1, N2).** Misses and final distance about the same for both.
- **Weak noise (N3).** The plain paired rule stops at P0 where the base alone does nothing: 1.34 L per night missed.
  With `climb_on_kept`: 0.26 missed, the best final distance, and fewer seconds than the current rule.

## Predictions (written before the data)

- LP-2 No candidate adopted in a round overshoots (CANDIDATE OVERSHOOTS or os3's OVERSHOOT on that stack) in the
  next round run. Counted per adopted step; a step adopted in the last round run has no next round and is not counted.
  The only prediction of the night (LP-1 and LP-3 depend on the night's device: not declared).
- Beside, not predictions: the steps tried and adopted per L; the final incumbents; g against P0 per round; the
  seconds.

## Verdict words

- The decision words of 3 (CANDIDATE ADOPTED / CANDIDATE NOT ADOPTED / INCUMBENT KEPT / CANDIDATE OVERSHOOTS).
- os3's words beside.

## Known limits (stated before the data)

- One step per round: a night of 4 rounds climbs at most 4 steps per L.
- Without `climb_on_kept`, an L whose base alone does nothing stops at P0 even if base + M would help (seen in the
  desk nights with weak noise).
- The incumbent's off and floor arms are not in the job (ff only, measured when it was a candidate). Its overshoot
  is therefore not re-tested.
- The drift in the desk nights is a type, not the device's. Its size was set from loopvar (one night, one device).

## Device procedure (home)

```
python gpu/os_loop_paired.py go OUT --zip ZIP --expect-psf-os a164fc5 \
    --declaration prereg/loop_paired_night_2026-11-20.md --ledger LEDGER --climb-on-kept --k-max 4 --budget 240
python gpu/os_loop_paired.py resume OUT        # after a resumable stop
python gpu/os_loop_paired.py verify OUT
```
