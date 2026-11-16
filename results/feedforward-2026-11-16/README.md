# Feed-forward test, 2026-11-16 (ibm_marrakesh) (`prereg/feedforward_2026-11-16.md`)

- Declaration pushed 11:06:24 CET (reflog "a930033d (origin/main, origin/HEAD) refs/remotes/origin/main@{2026-11-16
  11:06:24 +0100}: update by push"); queue read 11:07:12 CET: marrakesh 0, fez 131, kingston 0 -> ibm_marrakesh (the
  first qualifying device in the declared order). Device record fetched 11:07:17 CET (calibration 2026-11-13 18:22 CET;
  failed qubits 82, 94, 113, 119, 130, coupler 113-119).
- Built with `python gpu/ff_night.py build DEVDIR OUT --k 1 2 4` (no dry-run flag), psf-os branch
  feedforward-2026-11-16 at 32dc3e5; 13 circuits, 4000 shots, 17.5 s by the model; circuits_sha256 93e05e25ee55...
  Pre-run check `python gpu/ff_night.py check OUT`: PASS. The job returned from the owner's run byte-identical to the
  one built (circuits.qpy compared).
- Job dbtde3req3sc73evm62g, submitted 11:12:31 CET, ran 11:12:32-11:12:53 CET, 16 s charged. Dynamical decoupling
  and twirling off, no mitigation.

## Scorer output (`python gpu/ff_night.py score OUT`, unchanged since the declaration's commit)

```
tp1: ff 0.9517 (2 SE 0.0068, threshold 0.7637) -> ABOVE THE BOUND; off 0.7935; floor all zero 0.9990; off best fixed rule after the fact 0.7935; sentinel DEAD
tp2: ff 0.8898 (2 SE 0.0099, threshold 0.7637) -> ABOVE THE BOUND; off 0.5175; floor all zero 0.9915; off best fixed rule after the fact 0.7455; sentinel DEAD
tp4: ff 0.8165 (2 SE 0.0122, threshold 0.7637) -> beside; off 0.5095; floor all zero 0.9627; off best fixed rule after the fact 0.7300; sentinel DEAD
```

Every shot counted, none discarded (`ff_scores.json`: counted 4000, discarded 0 in every arm).

## Against the declaration

| prediction | numbers | |
|---|---|---|
| 1. k = 1 ABOVE THE BOUND | ff 0.9517, threshold 0.7637 | held |
| 2. k = 2 ABOVE THE BOUND | ff 0.8898, threshold 0.7637 | held |
| 3. off arm at or under its circuit value + 2 SE | k = 1: 0.7935 against 0.7637; k = 2: 0.5175 against 0.5158 | failed (both k) |

## Beside, never judged: the success split by the mid-circuit bits (`branch.py`, `branch.json`)

Noiseless values of the off arm per pattern from Aer on the same compiled circuits (200000 shots).

| k | mid bits | ff on the device | off on the device | off noiseless |
|---|---|---|---|---|
| 1 | 0 | 0.946 (n 2002) | 0.992 (n 1950) | 1.000 |
| 1 | 1 | 0.957 (n 1998) | 0.605 (n 2050) | 0.500 |
| 2 | 00 | 0.892 (n 1252) | 0.894 (n 1278) | 1.000 |
| 2 | 01 | 0.832 (n 1179) | 0.114 (n 1182) | 0.000 |
| 2 | 10 | 0.938 (n 804) | 0.521 (n 801) | 0.496 |
| 2 | 11 | 0.924 (n 765) | 0.507 (n 739) | 0.505 |

(k = 4: 16 patterns in `branch.json`; the off arm follows its noiseless pattern values 1 / 0 / 0.5 in the same way,
the ff arm stays between 0.72 and 0.89 in every pattern.)

ff minus off: k = 1 0.158 (2 SE of the difference 0.014), k = 2 0.372, k = 4 0.307.

## Reading (an interpretation beside the verdict, not a judgement)

- Prediction 3 failed because the off arm's branches where the circuit gives 1/2 come out above 1/2 at k = 1 (0.605),
  and because mid bits that should read 1 read 0 more often than half the time at k = 2 (patterns with the second mid
  bit 1: 1540 of 4000 shots, where the circuit gives 2000). Both move shots toward the success outcome, which is the
  last bit 0: the ground state. Decay toward |0> during the mid-circuit wait and the readout, on the output qubit and
  on the mid bits, fits both; this record does not separate the two.
- What this means for the verdict: the bound 0.75 is the circuit's, for a noiseless run without real-time control.
  Tonight the off arm, which has no real-time control, also lies above 0.7637 at k = 1. The declared verdict stands
  as written (ABOVE THE BOUND at k = 1 and 2), but by itself it does not show feed-forward at k = 1: the device's bias
  toward 0 lifts a run without control over the line too.
- What carries the feed-forward reading tonight: the ff arm is above the off arm by many SE at every k, and its
  success is nearly the same in every branch (0.946 / 0.957 at k = 1), while the off arm splits the way the circuit
  says (1 / 0 / 0.5 pulled toward 0). Real-time correction is what makes the branches equal.
- For a next declaration (owner's decision): alternate the success bit (half the inputs with success = last bit 1,
  so decay toward 0 cannot help), or judge ff against the off arm of the same job directly, with the margin declared.

## Files

`job/` (circuits.qpy, manifest.json, raw_counts.json, submission.json), `runs/` (per-circuit QPY and records),
`build.json`, `ff_scores.json` (the scorer's output), `branch.py` / `branch.json` (beside).

## Reproduce

`python reproduce.py --psf-os PATH_TO_PSF_OS_AT_feedforward-2026-11-16 feedforward-2026-11-16` (SAME, 2026-11-16).
