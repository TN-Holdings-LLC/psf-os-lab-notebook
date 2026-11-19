# DRAFT (not declared): the compounding loop on psf-os v0.2 with the rungs +M, +F and the ledger, night of 2026-11-19

Workplace Claude, 2026-11-19 (home handover 2026-11-19, sections 3 and 4.1). Every threshold, verdict word, limit and
prediction marked [OWNER] is the owner's; the declaration is written and pushed at home. Tool: `gpu/os_loop.py` on
psf-os branch v0.2-proto-2026-11-18 (`psf_os/loop.py`). Design and dry nights: `notes/os_loop_2026-11-19/README.md`.

## Common

- psf-os at [OWNER: the commit of the v0.2 branch tonight]; the notebook at the declaring commit (preflight checks
  both once `DECLARATION` is set in gpu/os_loop.py).
- Device by the standing rule (gpu/daily_fetch.py, the first chosen in the order ibm_marrakesh, ibm_fez, ibm_kingston);
  one device record for the night. Rule C placement (coupling graph and failed marks only); no mitigation; DD and
  twirling off; 4000 shots; every shot counted. No calibration error number is read; the ledger reads the record's
  calibration time stamp only.
- Each job's `check` before submission; a FAIL stops the night. The next round's rule is written (RULE{k+1}.json)
  before that round is built; nothing is re-chosen after a job's data.

## The night (as 2026-11-18's os2, with the rungs and the ledger)

1. Diagnostics Dw and Dc (gpu/wait_night.py, gpu/ctrl_night.py), round 1 by gpu/os_night.py's rule (as os2).
2. The ledger [OWNER: the ledger file, e.g. `results/os-ledger.json`, written by the 2026-11-18 night's entry or empty]:
   round 1 starts from the ledger's last stacks only on the same device with the same calibration time, and per L only
   where tonight's pick is of the same family (P1 and P2 one family); otherwise tonight's pick. Every decision is in
   RULE1.json.
3. Rounds k = 1, 2, ...: the rule per L, first match wins, each threshold 2 SE [OWNER]: R1 overshoot -> P2 + B; R2
   frames -> + Q; RM (PRESCRIPTION HELPS, no B, no M) -> + M (one more try); RF (no B, no F, Dr on the output qubit
   against the base's read frame) -> switch P1 <-> P2 + F; R3 stop-loss; R4 keep. The rungs in the order +M, +F
   [OWNER].
4. Stops: a fixed point, K_MAX = 4 [OWNER], the budget 240 s by the model including the diagnostics, estimated before a
   round is built [OWNER], a check FAIL, a refused build.
5. Scores as os2 / os3 (g = |P0 - exact| - |P(stack) - exact|; OVERSHOOT / PRESCRIPTION HELPS / NOT SHOWN).

## Predictions [OWNER] (written before the data)

- LOOP-1 The rule changes at least one stack between round 1 and round 2 (on 2026-11-18 it did not: OS2-1 failed).
- LOOP-2 No L overshoots in the last round run.
- Beside, never judged: whether the ledger was used and why; the rungs climbed; the OS's own compounding (G per round,
  slope); the model seconds spent; the jobs' times.

Each prediction holds or fails as a whole; a failed one is reported as failed. Basis: the dry nights (the 2026-11-18
marrakesh record, illustrative noises never fitted): with noise N1 the rule climbed R1, RM, R2 over three rounds; with
the ledger the second night started where the first ended and stopped after one round.

## Reproduce

`python gpu/os_loop.py verify OUT` rebuilds every job (circuits.qpy byte for byte, the manifest but for its time),
re-scores every job, re-derives round 1 (the diagnostics' stacks and the ledger line kept in RULE1.json) and re-rules
every round: SAME / DIFFERENT.
