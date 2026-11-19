# The compounding loop on psf-os v0.2, 2026-11-19 on ibm_marrakesh (`prereg/os_loop_night_2026-11-19.md`)

- Declared in be3147c7, pushed by the owner before the night's first fetch (11:17:49 CET). Run unattended on the
  owner's machine (`versions.txt`: Python 3.12.13, qiskit 2.5.2, aer 0.17.2, runtime 0.49.0, numpy 2.5.3) with
  `gpu/os_loop.py go --expect-psf-os 5e4a936 --declaration prereg/os_loop_night_2026-11-19.md --ledger` (preflight PASS;
  `run_log.txt`). Device record `fetch_in/` (queue marrakesh 1, fez 1, kingston 3 -> ibm_marrakesh; calibration
  2026-11-19 10:59:49+01:00).
- Ledger: the declared seed (11-18, calibration 11:05:21) was **not used**: "other calibration (2026-11-18
  11:05:21+01:00 -> 2026-11-19 10:59:49+01:00): start from tonight's diagnostics" (the declared gate). The night
  appended its own line to the copy (`ledger_written`), never to the committed seed.
- `verify` on the owner's machine: every step SAME (`verify_on_owner_pc.txt`). At home (qiskit-aer 0.18.0): every step
  SAME by the test circuits' gates (bytes differ with the versions; the ring sentinel differs, beside).

| job | folder | id | circuits | s model | s charged | created - finished (CET) |
|---|---|---|---|---|---|---|
| Dw | `dw/` | dbvcps7f8rhs73bnn0m0 | 22 | 27.6 | 26 | 11:18:24 - 11:18:58 |
| Dc | `dc/` | dbvcq86ps3fc73bk8rlg | 22 | 27.6 | 26 | 11:19:12 - 11:19:45 |
| r1 | `r1/` | dbvcqklarooc73flbu7g | 25 | 30.9 | 30 | 11:20:03 - 11:20:41 |
| r2 | `r2/` | dbvcr17f8rhs73bnn2fg | 25 | 30.9 | 30 | 11:20:52 - 11:21:29 |
| r3 | `r3/` | dbvcrd782tmc73dur2lg | 19 | 24.2 | 23 | 11:21:40 - 11:22:09 |

Charged 135 s (budget 240 s with the diagnostics; the model's sum 141.2 s).

## Diagnostics and round 1 (`round1.txt`)

```
Dc A: D_late_nb +0.0603 (2 SE 0.0105) loss True;  Dw A: D_cond +0.0032 (2 SE 0.0107) loss False
Dc B: D_late_nb +0.0445 (2 SE 0.0099) loss True;  Dw B: D_cond +0.0092 (2 SE 0.0107) loss False
Dr L 1 (physical qubit 1): P(1|1) 0.9732, P(0|0) 0.9795, gap +0.0063 (2 SE 0.0068) loss False
Dr L 2 (physical qubit 3): P(1|1) 0.9928, P(0|0) 0.9955, gap +0.0028 (2 SE 0.0034) loss False
Dr L 3 (physical qubit 5): P(1|1) 0.9828, P(0|0) 0.9825, gap -0.0002 (2 SE 0.0058) loss False
pick: P1 / P1 / P1
```

## Rounds (`rK/round_scores.json`, `RULEk.json`)

| round | L = 1 | L = 2 | L = 3 | rule after the round |
|---|---|---|---|---|
| r1 | P1, g +0.0062 (SE 0.0056) NOT SHOWN | P1, g -0.0282 NOT SHOWN | P1, g -0.0270 NOT SHOWN | R4 keep, keep, keep |
| r2 | P1, g +0.0182 (SE 0.0055) PRESCRIPTION HELPS | P1, g -0.0175 NOT SHOWN | P1, g -0.0255 NOT SHOWN | L1 RM: one more try (m 3) + M; L2, L3 R3 stop-loss -> P0 |
| r3 | P1 + M, g +0.0470 (SE 0.0049) PRESCRIPTION HELPS | P0 (no prescription) | P0 (no prescription) | R4 keep, keep, keep |

Stop: "the rule: fixed point: every L keeps its stack, none overshoots, none NOT SHOWN for the first time (after round
3)" (not resumable). No L overshot in any round. RF never fired (no Dr gap). Rungs climbed: M.

## Against the declaration

| prediction | numbers | |
|---|---|---|
| LOOP-1 the rule changes at least one stack between round 1 and round 2 | RULE2 = RULE1 (R4 keep everywhere: every L NOT SHOWN for the first time) | failed |
| LOOP-2 no L overshoots in the last round run | r3: none | held |

Beside, never judged (numbers only, as declared): OS compounding on the L common to every round (L = 1): G +0.0062,
+0.0182, +0.0470 over rounds 1-3, slope +0.0206 (SE 0.0055). Rounds 1 and 2 ran the same stack (P1) and read
+0.006 and +0.018: part of the rise is round-to-round variation, not the rule; round 3 is the first device round with
a rung (+M).

## Two numbers side by side

- Vanity: the loop's last round puts L = 1 0.047 beyond the correction ceiling.
- Essence: unattended, the loop stopped spending on the two L that never helped (R3 after two NOT SHOWN) and spent one
  more try only where the prescription helped; 135 s charged, no person in the loop, verify SAME on the owner's PC.

## Reproduce

`python reproduce.py loop-night-2026-11-19-dw loop-night-2026-11-19-dc loop-night-2026-11-19-r1
loop-night-2026-11-19-r2 loop-night-2026-11-19-r3`; the whole night: `python gpu/os_loop.py verify
results/loop-night-2026-11-19` (rebuilds every job, re-scores, re-rules).
