# DRAFT (not declared): the paired loop, the incumbent and the candidate in one job (weekend)

Home VS Claude, 2026-11-21, on the home instruction "輪の改造: 比べる 2 つの積み方を同じジョブに入れる" (the owner's
decision of 2026-11-20 20:05 JST). **Predictions, thresholds, words, shots, the round limit and the options marked
[OWNER] are the owner's / home Claude's.** Tool: `gpu/os_loop_paired.py` (go / resume / verify / size). psf-os branch
loop-paired-2026-11-21 (`psf_os.loop.next_stacks_paired`, Night with `paired`, `feedforward.build(ff_only=...)`).
Notes and simulated nights: `notes/loop_paired_2026-11-21/`.

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
   - Otherwise: INCUMBENT KEPT. [OWNER: the words; 2 SE.]
4. **Next candidate.** The next untried step on the incumbent:
   - B after an overshoot;
   - the base on P0;
   - Q on B (R2's conditions);
   - then M, then F (F only when Dr is against the base's frame).
   A step not adopted is not tried again that night. A key with no step left stops.
   [OWNER: the option `climb_on_kept`: on INCUMBENT KEPT, build the next candidate on the kept candidate instead
   (e.g. P1 + M against P0).]
5. **Stops.**
   - Every key has stopped.
   - The round limit K. [OWNER: 4, or 5.]
   - The budget, 240 s with the diagnostics. [OWNER]
   - A check FAIL, a refused build, or a failed job: as declared on 2026-11-19.
6. **Beside, never in the decision.** Per round and L: g against P0 and os3's words (OVERSHOOT / PRESCRIPTION HELPS /
   NOT SHOWN); the compound rows.

## Size (2026-11-19 marrakesh record)

- 25 to 40 circuits per round, 30.9 to 47.6 s by the model.
- Diagnostics 55.2 s.
- Four rounds of 34 s: about 192 s.
- 4000 shots. [OWNER: shots]

## Desk results (illustrative noise; `notes/loop_paired_2026-11-21/README.md`)

50 simulated nights per case, with a drift between jobs of loopvar's size:

- **Wrong steps per night.** Paired 0.06 to 0.56; current 2.2 to 3.1.
- **Strong noise (N1, N2).** Misses and final distance about the same for both.
- **Weak noise (N3).** The plain paired rule stops at P0 where the base alone does nothing: 1.34 L per night missed.
  With `climb_on_kept`: 0.26 missed, the best final distance, and fewer seconds than the current rule.

## Predictions [OWNER]

- LP-1 [OWNER: e.g. at least one candidate ADOPTED in round 1 or 2.]
- LP-2 [OWNER: e.g. no adopted candidate overshoots in the next round.]
- LP-3 [OWNER: e.g. the night stops before the round limit (every key out of steps).]
- Beside, not predictions: the steps tried and adopted per L; the final incumbents; g against P0 per round; the
  seconds.

## Verdict words [OWNER]

- The decision words of 3 (CANDIDATE ADOPTED / CANDIDATE NOT ADOPTED / INCUMBENT KEPT / CANDIDATE OVERSHOOTS).
- os3's words beside.

## Known limits (stated before the data)

- One step per round: a night of 4 rounds climbs at most 4 steps per L.
- Without `climb_on_kept`, an L whose base alone does nothing stops at P0 even if base + M would help (seen in the
  desk nights with weak noise).
- The incumbent's off and floor arms are not in the job (ff only, measured when it was a candidate). Its overshoot
  is therefore not re-tested.
- The drift in the desk nights is a type, not the device's. Its size was set from loopvar (one night, one device).

## Decisions before declaring ([OWNER] list)

1. Run it, and when (one night: the diagnostics and up to K rounds).
2. `climb_on_kept` on or off.
3. The round limit K (4 or 5) and the budget (240 s).
4. Shots (4000), the 2 SE threshold, and the words.
5. Predictions LP-1 ...
6. The ledger: use the 2026-11-20 night's line, or start empty. (11-20 had no loop; the last line is 11-19's, whose
   calibration time differs, so it is not used.)

## Device procedure (home)

```
python gpu/os_loop_paired.py go OUT --zip ZIP --expect-psf-os <loop-paired commit> \
    --declaration prereg/<declared file> [--ledger ~/os-ledger.json] [--climb-on-kept]
python gpu/os_loop_paired.py resume OUT        # after a resumable stop
python gpu/os_loop_paired.py verify OUT
```
