# More rungs and a nightly ledger (home VS Claude, 2026-11-18 night; not declared, no device, illustrative noise only)

Home instruction "試作3点", parts B and C. Tools `gpu/os3_night.py` (ladders A / B, the rule) and `gpu/os3_run.py`
(nights run locally, the ledger). `gpu/os2_night.py` and `gpu/os2_run.py` (declared) are imported read-only and
unchanged. The noise is notes/os2_2026-11-18/branch_noise.py's, ILLUSTRATIVE, never fitted to a device: N1
`{"gamma": 0.05, "p11": {"1": 0.83}}` (a readout gap on qubit 1), N2 `{"gamma": 0.1}`.

## B: two ladders (the rule and its rungs: os3_night.py's docstring)

- ladder A, "+F": frame by readout direction (the instruction's P4): switch P1 <-> P2 when the round's Dr shows the
  gap against the base's read frame.
- ladder B, "+M": one more try (m 2 -> 3) after PRESCRIPTION HELPS without +B.

Simulated on the 2026-11-18 marrakesh record (`{A,B}_N{1,2}.log`; G = mean g over L per round, os2's
compounding verdict):

| ladder | noise | rounds | G per round | verdict |
|---|---|---|---|---|
| A | N1 | 3 | 0.1085, 0.1053, 0.1080 | NOT SHOWN (slope -0.0003) |
| A | N2 | 3 | (round 1 overshoots) | NOT JUDGEABLE |
| B | N1 | 4 | 0.1085, 0.1492, 0.1480, 0.1465 | OS COMPOUNDS (slope +0.011) |
| B | N2 | 2 | 0.1188, 0.1605 | NOT JUDGEABLE (2 rounds) |

Under these noises, RA (ladder A) never fired: the Dr gap on the stacks' output qubits was not against the base's frame.
RB (ladder B) fired on every L that helped without +B and raised G by about 0.04 in the next round. Ladder B is the one
that grows g here. This is a property of the illustrative noise, not of the device.

Dry-run on the recorded round 1 of 2026-11-18 (`dryrule_2026-11-18.json`; os2-night-2026-11-18): the three verdicts
were PRESCRIPTION HELPS. The Dr gap was significant on qubit 9 only (+0.017, 2 SE 0.0065) and not on the stacks'
output qubits. Ladder A therefore keeps P1 everywhere (R4: a fixed point, as os2). Ladder B moves every L to P1+M,
which would be round 2.

## C: the ledger (os3_run.py)

`ledger_sim.py` runs four nights with one ledger file (ladder B, N1). Results are in `ledger_sim.txt` / `.json`:

| night | record | ledger | rounds | G per round |
|---|---|---|---|---|
| 1 | 2026-11-18 marrakesh, calibration 11-18 11:05:21 | none, from scratch | 4 | 0.1085, 0.1492, 0.1480, 0.1465 |
| 2 | the same record (same device, same time) | used: round 1 = night 1's last stacks (P2+B+Q2+M / P1+M / P2+B) | 1 (fixed point at once) | 0.124 |
| 3 | the same record, only the calibration time changed (11-19 10:40) | not used (other calibration) | 4 | 0.0995, 0.1548, 0.1502, 0.1520 |
| 4 | 2026-11-17 marrakesh (calibration 11-13 18:22:56) | not used (other calibration) | 4 | (round 1 overshoots) |

`pair_check.py` / `.txt` (PASS) runs `ledger_start` directly:

- 2026-11-17 -> 2026-11-18 and back: the ledger is not used.
- Same calibration time, but tonight's pick (P2) disagrees with the ledger (P0) on L1: the diagnostics win for L1; the
  ledger is used for L2 and L3.

Every decision (used / not used and why, per L) is written into RULE1.json, the night record and the ledger entry.
