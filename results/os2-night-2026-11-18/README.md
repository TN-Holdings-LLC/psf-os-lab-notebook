# The compounding OS, first device night, 2026-11-18 on ibm_marrakesh (`prereg/os2_night_2026-11-18.md`)

- Declared with 16d14fc8 (pushed 11:12:46 CET; reflog as in `results/balanced-repeat-2026-11-18`). Run on the owner's
  machine by one command, `gpu/os2_run.py go`, from the declared checkout, nobody in between (`run_log.txt`). Preflight
  PASS (`versions.txt`; notes: qiskit-aer 0.17.2 and qiskit-ibm-runtime 0.49.0, not the workplace's 0.18.0 / 0.51.0,
  not a stop). The loop fetched its own record at 11:25:50 CET (queue marrakesh 1, fez 1, kingston 0 -> ibm_marrakesh;
  calibration 2026-11-18 10:40 CET) (`fetch_in/`).
  - Correction (2026-11-19, the workplace VS's check of 19c): the loop's own record says calibration
    2026-11-18 11:05:21+01:00 (`fetch_in/ibm_marrakesh/dev/device.json`, fetched 11:25:39 CET); 10:40 is the stamp of
    the record fetched at 11:17 for the other tests of the night. The scores are unchanged.
- `verify` on the owner's machine right after the run: SAME on every line (`verify_on_owner_pc.txt`). At home (the
  same qiskit 2.5.2): every score, rule and prediction SAME; the three jobs' circuits.qpy differ only in the four
  ring-sentinel circuits of each job (rebuilt and compared circuit by circuit; the sentinel's compiled bytes differ
  between environments; never judged).

| step | folder | job | created - finished (CET) | s model | s charged | execution / running |
|---|---|---|---|---|---|---|
| Dw | `dw/` | dbunqff82tmc73dto6eg | 11:26:05 - 11:26:52 | 27.6 | 26 | 0.52 |
| Dc | `dc/` | dbunr2v82tmc73dto75g | 11:27:24 - 11:27:59 | 27.6 | 26 | 0.71 |
| round 1 | `r1/` | dbunrf782tmc73dto7kg | 11:28:12 - 11:29:07 | 30.9 | 30 | 0.51 |

Queue right after each submission: marrakesh 1 every time (`queue_after_*.json`). 82 s charged in all.

## What the loop did

1. Diagnostics (`os_rule.txt`): Dc late-use loss at A and B (+0.066, +0.076, beyond 2 SE); Dw no unfired-conditional
   cost; Dr no readout gap on the output qubits (qubit 1: P(1 | |1>) 0.967, P(0 | |0>) 0.955, gap -0.013; qubits 3, 5
   within 2 SE). Rule: **P1 at L = 1, 2, 3** (hold flipped while waiting, read as it is). On 2026-11-17, with qubit 1
   reading |1> as 1 only 0.826 of the time, the same rule had picked P2 (read flipped).
2. Round 1 (`r1/score.txt`):
   ```
   L 1 [P1]: P 0.8403 (noiseless 0.8904) P0 0.8080 g +0.0323 (2 SE 0.0170) -> PRESCRIPTION HELPS
   L 2 [P1]: P 0.7288 (noiseless 0.7929) P0 0.7033 g +0.0255 (2 SE 0.0202) -> PRESCRIPTION HELPS
   L 3 [P1]: P 0.6400 (noiseless 0.7060) P0 0.5847 g +0.0553 (2 SE 0.0218) -> PRESCRIPTION HELPS
   ```
3. Rule for round 2 (`rule_r2.txt`): every L R4 keep -> **stop at a fixed point after round 1** (`stop.json`). Budget
   used 86.1 s of 240 by the model.

## Against the declaration

| prediction | numbers | |
|---|---|---|
| OS2-1 the rule changes at least one stack between round 1 and round 2 | no change (R4 keep at every L; fixed point) | failed |
| OS2-2 no L overshoots in the last round run | none (round 1: 0.840 / 0.729 / 0.640 against 0.890 / 0.793 / 0.706) | held |

The OS's own compounding (beside, numbers only): one round, G 0.038 (SE 0.006); a slope needs three rounds.

## Two numbers side by side

- Vanity: the loop ran end to end on the device with nobody in between, picked a prescription from the night's own
  diagnostics, helped at every L (+0.032 / +0.026 / +0.055) and stopped by its rule; the owner's machine and home
  verify the same scores and rules.
- Essence: it stopped after one round, so nothing compounded tonight; the prescription kept 0.94 / 0.92 / 0.91 of its
  noiseless value. What the loop showed is that it reads the night: a recalibrated device whose qubit-1 readout gap
  had reversed got P1, not last night's P2.

## Beside, never judged

- Dr in round 1's probes: qubit 9 shows a readout gap (+0.017, 2 SE 0.007); not an output qubit tonight.
- Diagnostics' own 2026-11-16 predictions printed by their scorers are not judged here.

## Independent check

The home VS applied the declared rules by hand to the raw diagnostic counts (`notes/verify_2026-11-18/`): P1 at L = 1,
2, 3; round 1's g and verdicts equal; R4 keeps every L and the loop stops at the fixed point. Its rebuild of the
sentinels matches the owner's machine byte for byte.

## Reproduce

`python reproduce.py --psf-os PATH_TO_PSF_OS_AT_0f57c76 os2-night-2026-11-18-dw os2-night-2026-11-18-dc
os2-night-2026-11-18-r1` (SAME, 2026-11-18); `python gpu/os2_run.py verify .` in the environment that built it.
