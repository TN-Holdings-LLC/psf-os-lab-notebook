# Declared: the frame-balanced neuron chain again, L = 1 .. 5, night of 2026-11-18 (a repeat on the same device)

Home Claude, 2026-11-18 (owner about 10:50 JST: "出し惜しみはしない", run the repeat the paper outline asks for, "A
same-device repeat of T2 or the balanced chain on a second night", `notes/paper_ff_2026-11-17/OUTLINE.md`). Declared
with the commit that carries this file, pushed before the device record of the run is fetched.

## What is run

Exactly `prereg/balanced_night_2026-11-17.md`: `gpu/balanced_night.py` unchanged (build, check, score as of this
commit; it has not changed since 2026-11-17), rd{L} and nf{L} for L = 1 .. 5, 34 circuits, 40.9 s by the model, 4000
shots, psf-os 0f57c76 (its single builds are those of 301ac01: every 2026-11-17 verdict reproduces SAME with it). Common
rules as on 2026-11-17 (device by the standing rule, the first qualifying in the order ibm_marrakesh, ibm_fez,
ibm_kingston; rule C placement; no mitigation, DD and twirling off; every shot counted; `check` before submission, a
FAIL means the job is not run).

**Same device.** This is a same-device repeat only if the night's device is ibm_marrakesh (the device of 2026-11-17's
run). If the standing rule chooses another device, the job is still run and scored with the same verdicts, and the
record says plainly that it is not a same-device repeat.

## Verdicts (as 2026-11-17)

Per L on the pooled value P = (P_rd + P_nf) / 2: **BEYOND THE CORRECTION CEILING** when g = c(L) - |P - exact| >= 2 SE
and P <= noiseless + 2 SE; **OVERSHOOT** when P > noiseless + 2 SE; otherwise **NOT BEYOND**. Slope of g over L:
**COMPOUNDS** when >= 2 SE and no L overshoots; otherwise **NOT SHOWN**.

Beside, never judged: per L the pooled P, rd and nf against 2026-11-17's (difference and its 2 SE); whether the
physical qubits are the same as on 2026-11-17 (rule C on the night's record); the device record's calibration date
against 2026-11-17's.

## Predictions (written before the data)

1. R-1 No L overshoots (the pool).
2. R-2 BEYOND THE CORRECTION CEILING at L = 2, 3, 4, 5.
3. R-3 COMPOUNDS.

Basis: 2026-11-17 on marrakesh (no overshoot; beyond at L = 2 .. 5, g +0.057 to +0.117; L = 1 not beyond, g -0.019,
with the nf frame reading its 1 on qubit 1, whose readout gap was +0.17 that night; slope +0.031, 2 SE 0.003). L = 1 is
not predicted. Each prediction holds or fails as a whole; a failed one is reported as failed.
