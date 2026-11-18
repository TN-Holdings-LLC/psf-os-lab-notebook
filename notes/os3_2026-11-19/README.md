# More rungs and a nightly ledger for the prescription loop (home VS Claude, 2026-11-18 night; desk prototype)

Home Claude's instruction "試作3点", parts B and C. Not declared, no device. The declared tools (`gpu/os2_night.py`,
`gpu/os2_run.py`, `gpu/os_night.py`, ...) are unchanged; `gpu/os3_night.py` imports os2_night read-only and adds to it,
`gpu/os3_run.py` runs nights locally with a ledger. **Every noise here is an illustration** (branch_noise.py's form:
amplitude damping per mid-circuit wait and a readout probability per qubit, written by hand), never fitted to a
device; no calibration error number is read (the ledger reads the calibration *time* only).

## B. Two ladders (`gpu/os3_night.py --ladder A|B`)

- **A, "+F" frame by readout direction** (the instruction's P4): per L, the round's own probe Dr on the stack's output
  qubit; if the gap runs against the base's read frame (P1 / NF read logical 1 as |1>, P2 as |0>), the base switches
  P1 <-> P2 and the layer F is added.
- **B, "+M" one more try**: per L, PRESCRIPTION HELPS (no overshoot), no +B, no M -> tries m 2 -> 3 (noiseless value
  closer to the exact one; one more wait per neuron).
- Both keep os2's R1 (overshoot -> P2 + B), R2 (+Q), R3 (stop-loss) and stops; the new rung sits between R2 and R3.
  Noiseless values are computed exactly from each circuit (m = 3 leaves ideal.json).

### Simulated nights (2026-11-18 marrakesh record, K_MAX 4, budget 240 s; `night_*.json`)

| noise (illustrative) | ladder | rounds | g per round (L1 / L2 / L3) | G_k (L credited every round) |
|---|---|---|---|---|
| N1 gamma 0.05, q1 P(1\|1) 0.83 | A | 3 | r1 +0.216 OV / +0.109 / +0.145 OV; r2 +0.102 / +0.105 / +0.055; r3 +0.142 / +0.108 / +0.059 | 0.109, 0.105, 0.108 (slope -0.000, NOT SHOWN) |
| N1 | B | 4 | r2 L2 P1+M +0.149; r4 L1 P2+B+Q2+M +0.177 | 0.109, 0.149, 0.148, 0.147 (slope +0.011, OS COMPOUNDS) |
| N2 gamma 0.1 | A | 3 | r1 +0.119 / OV / OV; r2 L1 OV (same stack); r3 +0.038 / +0.095 / +0.142 | none credited every round |
| N2 | B | 2 | r2 L1 P1+M +0.161 (from +0.119), L2 / L3 P2+B +0.098 / +0.139 | 0.119, 0.161 (two rounds) |

- The frame rung of ladder A never fired: tonight's diagnostics (os_night's rule 2) already pick the frame that matches
  the readout direction in round 1, and the probe's Dr did not turn against it later. A adds nothing over os2 here.
- The extra try of ladder B fired wherever a stack helped and raised g by +0.035 to +0.042 at that L (L2 under N1, L1
  under N2 and under N1 after +Q2): the stack keeps climbing over rounds, and G grows (N1: slope +0.011 per round, OS
  COMPOUNDS over four rounds).
- Dry run of the rule on the recorded round 1 of 2026-11-18 (`dryrule_2026-11-18.json`): ladder A keeps P1 at every L
  (q1's gap -0.0105, 2 SE 0.0093, runs the other way: P1 is already the right frame) and stops at the fixed point, as
  os2 did; ladder B picks **P1 + M at L = 1, 2, 3** (all three helped) and goes on to round 2.

## C. The ledger (`gpu/os3_run.py night ... --ledger LEDGER.json`)

- Each night appends: device, calibration time (device record source.calibration_time), ladder, per L the last stack,
  g and verdict, rounds run, whether the ledger was used and why.
- Round 1 starts from the ledger's last stacks only when the last night is on the same device with the same calibration
  time, and per L only when tonight's diagnostics pick a base of the same family (P1 / P2 "hold flipped"; P0; P3);
  otherwise the diagnostics win for that L. Every decision is written to RULE1.json and the night record.
- Simulation (`ledger_sim.py`, ladder B, noise N1; `ledger_sim.txt / .json`, `ledger_sim_ledger.json`):

| night | record | ledger | round 1 | rounds | stop |
|---|---|---|---|---|---|
| 1 | 2026-11-18 | empty | P2 / P1 / P1 | 4 | fixed point (G 0.109 -> 0.147) |
| 2 | same record, other seeds | **used** (same device and calibration time; families agree) | P2+B+Q2+M / P1+M / P2+B | **1** | fixed point at once (G 0.124) |
| 3 | same record, calibration time changed | not used (other calibration) | P2 / P1 / P1 | 4 | fixed point |
| 4 | 2026-11-17 record (calibration 2026-11-13) | not used (other calibration) | P2 / P1 / P1 | 4 | fixed point |

  Night 2 saved three rounds (92.8 s by the model against 198.9 s). `ledger_1117_vs_1118.txt`: between the real records
  of 2026-11-17 (calibration 2026-11-13 18:22) and 2026-11-18 (calibration 2026-11-18 11:05), the ledger is not used
  in either direction.

`pair_check.py` / `.txt` (PASS) calls ledger_start directly: 2026-11-17 <-> 2026-11-18 not used in either direction;
with the same calibration time but tonight's pick P2 against the ledger's P0 on L1, the diagnostics win for L1 and the
ledger is used for L2 and L3.

## Not done

- `os3_run.py` runs dry nights only; the device path (fetch, submit, collect, zip, verify, resume as in os2_run.py) is
  left for the port into psf-os.
- No draft declaration for os3 was written.
