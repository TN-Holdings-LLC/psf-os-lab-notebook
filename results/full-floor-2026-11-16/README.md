# full-floor-2026-11-16 (ibm_marrakesh) (prereg/full_floor_2026-11-13.md)

- Declaration pushed 2026-11-16T11:06:24+01:00 (reflog "update by push"); queue read 2026-11-16T10:07:12.324554+00:00 (pending {'ibm_marrakesh': 0, 'ibm_fez': 131, 'ibm_kingston': 0}).
- Job floor: 2 circuits, 5.2 s by the model, circuits_sha256 e5d1adac0895..., no pre-run check declared (measurement record); job id dbtde27q0h0s73bkkoog; job files returned byte-identical.
- Files over 50 MB are gzipped (`gunzip` restores them).

## Scorer output

### floor

```
151 qubits: 1 - z(|0>) median 0.0170, worst 1.438; 1 + z(|1>) median 0.0460, worst 0.829
```

## Against the declaration

A measurement record, no prediction (`prereg/full_floor_2026-11-13.md`). Night 4 of the record, on the same
calibration of the device record as nights 2 and 3. Nothing here is used for placement; the quirk-ledger check is its
own declaration, written before it is scored.

Beside, never used to correct (per physical qubit, 151 qubits each night, from the four `full_floor.json`):

| | night 1 (11-13) | night 2 (11-14) | night 3 (11-15) | night 4 (11-16) |
|---|---|---|---|---|
| calibration of the device record | 11-13 11:10 CET | 11-13 18:22 CET | the same | the same |
| 1 - z(\|0>), median / worst | 0.0180 / 0.909 (q59) | 0.0150 / 0.560 (q48) | 0.0145 / 0.562 (q81) | 0.0170 / 1.438 (q48) |
| 1 + z(\|1>), median / worst | 0.0390 / 0.599 (q59) | 0.0455 / 0.406 (q41) | 0.0470 / 1.012 (q31) | 0.0460 / 0.829 (q10) |

Correlation per qubit with night 4 (Pearson / Spearman): 1 - z(|0>) night 1 0.17 / 0.51, night 2 0.85 / 0.75,
night 3 0.37 / 0.80; 1 + z(|1>) night 1 0.19 / 0.60, night 2 0.48 / 0.73, night 3 0.38 / 0.69. q48 read |0> as |1>
in most shots tonight (1 - z = 1.438); it was also the worst on night 2 (0.560); without q48 the night 2-4
Pearson value is 0.60. q31, which read |1> as |0> almost always on night 3 (1.012), is at 0.285 tonight.

## Reproduce

`python reproduce.py full-floor-2026-11-16-floor`.
