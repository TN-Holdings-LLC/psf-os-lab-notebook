# The branch cost in IPE, 2026-11-22 on ibm_fez (`prereg/ipe_branch_cost_night_2026-11-22.md`)

- Declared in 61344ac6, pushed by the owner before the night's first fetch (12:55:54 CET). Run on the owner's machine
  (`versions.txt`: Python 3.12.13, qiskit 2.5.2, aer 0.17.2, runtime 0.49.0, numpy 2.5.3) from a fresh worktree at
  61344ac6 with psf-os 0.3.1 as released (v0.3.1, 7caedaa), both checked clean and the version checked (PRE_OK).
- Device: pending marrakesh 0, fez 0, kingston 2 -> **ibm_fez**, calibration 2026-11-22 12:28:21+01:00. **dt
  (`dt.txt`, the backend's configuration): 4e-09 s, so L = 4500 dt = 18 µs per conditional.**
- Built as declared (`--plan d --L-dt 4500`); check PASS (`bc/check.txt`): noiseless all bits right in every item; CZ,
  X/SX outside conditionals and fences equal in F, S, SD, SD(2L); conditionals F 20 / 35, S 5 / 7 (the resets) at
  n = 6 / 8; SD's delays kept; `psf_os_build` 0.3.1 with park and park_likely stated. IBM accepted the delays.
- Scored by the declared tool on the owner's machine (`bc/score.txt`, `bc/branch_scores.json`); re-scored at home: the
  same text.

| job | folder | id | circuits | shots | s model | s charged | RU | created - finished (CET) |
|---|---|---|---|---|---|---|---|---|
| job0 | `bc/job0/` | dc1dh1lhdvas73bkmnn0 | 68 | 2950 | 59.6 | **112** | **1.863** | 12:56:54 - 12:59:01 |

**The charge was 1.9 times the model.** psf-os's model counts no delay; the SD circuits idled 270 µs (n = 6) to
540 µs (n = 8, 2 L) each, and the device charges the time.

## Results

| n | F (feedback) | S (fixed corrections) | SD (S + L per conditional) | SD (2 L) |
|---|---|---|---|---|
| 6 | 0.7981 | 0.8047 | 0.1177 | 0.0504 |
| 8 | 0.7192 | 0.7216 | 0.0494 | 0.0163 |

- SD − F, mean of the two n: −0.6751 (2 SE 0.0047) -> **FEEDBACK GAINS**; S − SD: +0.6796 (2 SE 0.0046) -> **WAIT
  COSTS**.
- **Reading (the declared table): "F keeps more than S + delay although the wait costs: the delay overstates F's wait
  (L too long)"; 0.4 tries: "none before reading plan d's two lengths".** The table foresaw this row: L, a placeholder,
  turned out to be 18 µs per conditional once dt was read.
- Beside: SD(L) − SD(2 L) +0.0502 (2 SE 0.0030), the wait's cost per further L (18 µs per conditional).
- Beside, never judged (not a declared difference): **S − F, removing every phase conditional with its real wait:
  +0.0067 (2 SE 0.0073) at n = 6, +0.0023 (2 SE 0.0083) at n = 8, mean +0.0045 (2 SE 0.0055).** The feedback with
  its real latency costs, at most, a few thousandths here; F and S differ by 15 and 28 conditionals per circuit.

## What went wrong, and what it tells

- L was declared as a placeholder (4500 dt) while dt was unknown; read at run time, dt is 4 ns and L is 18 µs, far
  longer than the device's own wait for a conditional (F lost almost nothing against S). The split into "the branch"
  and "its wait" is therefore not read from this night: the SD arms measure idling of 0.3 to 0.5 ms.
- Home Claude recommended keeping 4500 dt without checking dt first; the cost is this night's split and 112 s.
- What the night still shows (beside): the feedback and its real wait cost little (S − F within 2 SE at both n);
  the IPE's loss lies elsewhere than in the conditionals. The anatomy's angle-bound peak and the CZ per phase remain
  the candidates (after the declarations, hypotheses).

## Against the declaration

No prediction declared. Predictions over the nights of 11-16 to 11-22: 68 declared; 48 held, 20 failed.

## Two numbers side by side

- Vanity: none to claim; the declared split read the "L too long" row.
- Essence: removing every phase conditional changes P by +0.005 (2 SE 0.006): on fez, the feedback with its real wait
  costs a few thousandths at n = 6 and 8. 112 s charged, 1.9 times the model, because delays are charged and not
  modelled.

## Reproduce

`python reproduce.py --psf-os <psf-os 0.3.1> ipe-branch-cost-night-2026-11-22` (1 of 1 SAME at home).
