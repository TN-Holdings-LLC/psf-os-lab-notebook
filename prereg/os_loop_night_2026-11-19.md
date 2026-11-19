# Declared: the compounding loop on psf-os v0.2 with the rungs +M, +F and the ledger, night of 2026-11-19

Home Claude, 2026-11-19, from the draft `prereg/drafts-2026-11-19/os_loop_DRAFT.md` (workplace 19d); the owner's choices of
2026-11-19 (every recommended value). Declared when the commit that adds this file is pushed, before the device records of
the night are fetched; the tools are as of that commit, psf-os branch v0.2-proto-2026-11-18 at 5e4a936. The night's four
declarations are in one commit: `os_loop_night_2026-11-19.md`, `interfere_night_2026-11-19.md`,
`repcode_night_2026-11-19.md`, `qpe_repro_night_2026-11-19.md`. The loop runs first and fetches the night's device record;
the three single jobs are built on that same record. Tool: `gpu/os_loop.py`
(`psf_os/loop.py`). Design and dry nights: `notes/os_loop_2026-11-19/README.md`.

## Common

- psf-os at 5e4a936 (branch v0.2-proto-2026-11-18); the notebook at the declaring commit. `go` runs with
  `--expect-psf-os 5e4a936 --declaration prereg/os_loop_night_2026-11-19.md` and refuses without them; its preflight
  checks the psf-os HEAD and a clean psf_os/, the notebook HEAD at this file's last commit and a clean checkout, the file
  directly in prereg/, and a saved account file (not read).
- Device by the standing rule (gpu/daily_fetch.py, the first chosen in the order ibm_marrakesh, ibm_fez, ibm_kingston);
  one device record for the night. Rule C placement (coupling graph and failed marks only); no mitigation; DD and
  twirling off; 4000 shots; every shot counted. No calibration error number is read; the ledger reads the record's
  calibration time stamp only.
- Each job's `check` before submission; a FAIL stops the night. The next round's rule is written (RULE{k+1}.json)
  before that round is built; nothing is re-chosen after a job's data.

## The night (as 2026-11-18's os2, with the rungs and the ledger)

1. Diagnostics Dw and Dc (gpu/wait_night.py, gpu/ctrl_night.py), round 1 by gpu/os_night.py's rule (as os2).
2. The ledger: `notes/os_loop_2026-11-19/ledger_seed_from_2026-11-18.json` (sha256 0806f02a...7c10fa), the line
   `gpu/os_loop.py ledger-seed results/os2-night-2026-11-18` writes for the 2026-11-18 night (ibm_marrakesh, calibration
   time 2026-11-18 11:05:21+01:00 from the loop's own record, last stacks P1 / P1 / P1; checked by the workplace VS). It is copied
   into the night's folder before `go`; the night appends its own line to the copy, never to the committed seed:
   round 1 starts from the ledger's last stacks only on the same device with the same calibration time, and per L only
   where tonight's pick is of the same family (P1 and P2 one family); otherwise tonight's pick. Every decision is in
   RULE1.json.
3. Rounds k = 1, 2, ...: the rule per L, first match wins, each threshold 2 SE: R1 overshoot -> P2 + B; R2
   frames -> + Q; RM (PRESCRIPTION HELPS, no B, no M) -> + M (one more try); RF (no B, no F, Dr on the output qubit
   against the base's read frame) -> switch P1 <-> P2 + F; R3 stop-loss; R4 keep. The rungs in the order +M, +F.
   RF as built: it reads Dr only, not the verdict, so on an L NOT SHOWN twice it can act before R3's stop-loss (the
   workplace VS's point; the owner's choice of 2026-11-19: kept as built and dry-tested).
4. Stops: a fixed point, K_MAX = 4, the budget 240 s by the model including the diagnostics, estimated before a
   round is built, a check FAIL, a refused build.
5. Scores as os2 / os3 (g = |P0 - exact| - |P(stack) - exact|; OVERSHOOT / PRESCRIPTION HELPS / NOT SHOWN).

## Predictions (written before the data)

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
