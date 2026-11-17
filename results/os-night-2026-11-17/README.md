# The first run of the prescription loop (seed of an AI OS), 2026-11-17 on ibm_marrakesh (`prereg/os_night_2026-11-17.md`)

- Declaration pushed 11:58:15 CET (reflog "83dd106e (origin/main, origin/HEAD) refs/remotes/origin/main@{2026-11-17
  11:58:15 +0100}: update by push"). Queue read 11:59:50 CET: marrakesh 1, fez 0, kingston 2 -> ibm_marrakesh. One
  device record for the night, fetched 11:59:55 CET (calibration 2026-11-13 18:22 CET; failed qubits 82, 94, 113, 119,
  130; coupler 113-119) (`fetch_in/`). psf-os 301ac01 (checked on the owner's machine). The tools as of 83dd106e.
- The workplace VS checked the loop independently before the run (the rule on the 11-16 diagnostics and the dry run:
  the same numbers) and named three weak points in the matching (device name not compared, bit positions written in,
  a refused build leaving job files). They do not change the pick or a verdict; tonight they were checked by hand: both
  diagnostics and the main job on ibm_marrakesh; the last outputs on physical qubits 1, 3, 5 as Dr measured; no
  refusal. The fixes went in after the run (a later commit).

## Step 1: diagnostics

| | folder | job | circuits | s charged |
|---|---|---|---|---|
| Dw | `dw/` | dbu38a0vv3fc73c0o1f0 | 22 | 26 |
| Dc | `dc/` | dbu38cc9po4c73ceg5ug | 22 | 26 |

Numbers the rule reads (the tools' own "predictions" lines belong to the 11-16 declarations and are not judged):
Dc D_late_nb +0.0728 (A, 2 SE 0.0114), +0.0750 (B, 2 SE 0.0112); Dw D_cond -0.0052 (A), -0.0020 (B); Dr (P(1|1) against
P(0|0)): qubit 1 0.8257 / 0.9995 (gap +0.174), qubit 3 0.9880 / 0.9940 (+0.006, 2 SE 0.004), qubit 5 0.9938 / 0.9992
(+0.0055, 2 SE 0.0026).

## Step 2: the rule (`rule.json`, written before the main job was built)

Rule 1 (Dc late-use loss at A and B) and rule 2 (Dr gap at every L): **pick P2 at L = 1, 2, 3** (hold flipped while
waiting, and read flipped). Reproduced from the recorded diagnostics: identical `rule.json`.

## Step 3: the main job

Job dbu3acae8crs738b0p6g (submitted 12:06:25 CET, 22 circuits, 27.6 s by the model, 27 s charged). Pre-run check PASS;
returned byte-identical. Sentinel DEAD (beside).

```
p0_1 (P0): exact 0.9371; ff 0.7183; off 0.6438; d 0.0745 (2 SE_d 0.0208) -> CLOSER WITH CONTROL
p0_2 (P0): exact 0.8782; ff 0.6945; off 0.6202; d 0.0743 (2 SE_d 0.0212) -> CLOSER WITH CONTROL
p0_3 (P0): exact 0.8230; ff 0.5780; off 0.4825; d 0.0955 (2 SE_d 0.0222) -> CLOSER WITH CONTROL
x1 (P2): exact 0.9371; ff 0.9025; off 0.8315; d 0.0710 (2 SE_d 0.0151) -> CLOSER WITH CONTROL
x2 (P2): exact 0.8782; ff 0.7372; off 0.6440; d 0.0932 (2 SE_d 0.0206) -> CLOSER WITH CONTROL
x3 (P2): exact 0.8230; ff 0.6565; off 0.5577; d 0.0988 (2 SE_d 0.0217) -> CLOSER WITH CONTROL
L 1: |P0 - exact| - |P2 - exact| = +0.1842 (2 SE 0.0170) -> OVERSHOOT  (P2 ff 0.9025, noiseless 0.8915; P0 ff 0.7183)
L 2: |P0 - exact| - |P2 - exact| = +0.0427 (2 SE 0.0201) -> PRESCRIPTION HELPS  (P2 ff 0.7372, noiseless 0.7924)
L 3: |P0 - exact| - |P2 - exact| = +0.0785 (2 SE 0.0217) -> PRESCRIPTION HELPS  (P2 ff 0.6565, noiseless 0.7077)
```

## Against the declaration

| prediction | numbers | |
|---|---|---|
| OS-1 a prescription picked for every L | P2, P2, P2 | held |
| OS-2 PRESCRIPTION HELPS at L = 1, 2, 3 | L = 1 OVERSHOOT (P2 0.9025 against the line 0.8915 + 2 SE 0.0094 = 0.9009); L = 2, 3 HELPS | failed |

## Two numbers side by side

- Vanity: the picked prescription is closer to the exact value than the circuit as written at every L, by +0.184 /
  +0.043 / +0.079. Essence: at L = 1 the picked circuit reads above its own noiseless value (+0.011, the line exceeded
  by 0.0016), so that L is not credited to the prescription; at L = 2, 3 it keeps 0.93 / 0.93 of its noiseless value
  and the circuit as written 0.82 / 0.73 of its own (0.850 / 0.790).
- At L = 1 the circuit as written loses most (0.718 against 0.918 noiselessly): its output is read on qubit 1, whose
  |1> reads as 1 in 0.826 of the shots (Dr). Reading flipped removes that, and with decay toward |0> during the waits
  also counted as success, the picked arm goes slightly past its noiseless value.

## Reading (beside the verdicts)

The loop ran end to end on the device for the first time: two diagnostic jobs, a fixed rule written down before the
main job, one main job; 79 s charged. The diagnostics on this night were far milder than on 2026-11-16 (late-use loss
0.07 against 0.54 on qubit 1), and the rule still picked the same entry; whether a night exists on which it picks
otherwise is open.

## Reproduce

`python reproduce.py --psf-os PATH_TO_PSF_OS_AT_301ac01 os-night-2026-11-17-dw os-night-2026-11-17-dc
os-night-2026-11-17-main` (all SAME), and `python gpu/os_night.py rule results/os-night-2026-11-17/dw
results/os-night-2026-11-17/dc RULE.json` gives the recorded `rule.json` (identical, 2026-11-17).
