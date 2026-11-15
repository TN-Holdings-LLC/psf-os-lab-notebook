# full-floor-2026-11-15 (ibm_marrakesh) (prereg/full_floor_2026-11-13.md)

- Declaration pushed 2026-11-15T13:33:52+01:00 (reflog "update by push"); queue read 2026-11-15T12:34:18.867685+00:00 (pending {'ibm_marrakesh': 0, 'ibm_fez': 61, 'ibm_kingston': 257}).
- Job floor: 2 circuits, 5.2 s by the model, circuits_sha256 e5d1adac0895..., no pre-run check declared (measurement record); job id dbsqfnok09pc73b0glrg; job files returned byte-identical.
- Files over 50 MB are gzipped (`gunzip` restores them).

## Scorer output

### floor

```
151 qubits: 1 - z(|0>) median 0.0145, worst 0.562; 1 + z(|1>) median 0.0470, worst 1.012
```

## Against the declaration

A measurement record, no prediction (`prereg/full_floor_2026-11-13.md`). Night 3 of the record; with it the three
nights the quirk-ledger check waits for are in hand. That check is its own declaration, written before it is scored;
nothing here is used for placement.

Beside, never used to correct (per physical qubit, 151 qubits each night; `notes`-free, computed from the three
`full_floor.json`):

| | night 1 (11-13) | night 2 (11-14) | night 3 (11-15) |
|---|---|---|---|
| calibration of the device record | 11-13 11:10 CET | 11-13 18:22 CET | 11-13 18:22 CET (the same) |
| 1 - z(\|0>), median / worst | 0.0180 / 0.909 (q59) | 0.0150 / 0.560 (q48) | 0.0145 / 0.562 (q81) |
| 1 + z(\|1>), median / worst | 0.0390 / 0.599 (q59) | 0.0455 / 0.406 (q41) | 0.0470 / 1.012 (q31) |

Correlation per qubit (Pearson / Spearman): 1 - z(|0>) night 1-2 0.27 / 0.57, night 2-3 0.53 / 0.80, night 1-3
0.26 / 0.55; 1 + z(|1>) night 1-2 0.33 / 0.61, night 2-3 0.44 / 0.71, night 1-3 0.24 / 0.58. The two nights on the
same calibration agree more with each other than either does with night 1. q31 read |1> as |0> almost every time
tonight (1 + z = 1.012); on nights 1 and 2 it was not among the worst three.

## Reproduce

`python reproduce.py full-floor-2026-11-15-floor`.
