# The paired loop, 2026-11-20 on ibm_marrakesh (`prereg/loop_paired_night_2026-11-20.md`)

- Declared in 0aa31ca0, pushed by the owner before the night's first fetch (14:11:46 CET). Run unattended on the
  owner's machine (`run.json` build_env: Python 3.12.13, qiskit 2.5.2, aer 0.17.2, runtime 0.49.0, numpy 2.5.3) with
  `gpu/os_loop_paired.py go --expect-psf-os a164fc5 --declaration prereg/loop_paired_night_2026-11-20.md --ledger
  --climb-on-kept` on psf-os loop-paired-2026-11-21 (a164fc5) (preflight PASS; `run_log.txt`). Device record
  `fetch_in/` (queue marrakesh 0, fez 0, kingston 1 -> ibm_marrakesh; calibration 2026-11-19 23:09:26+01:00, the same
  as the decoy and loopvar jobs earlier on 11-20).
- **The procedure line of the declaration was wrong; the values were not.** The declaration's procedure gave
  `--k-max 4 --budget 240`. psf-os refuses these two flags on a device run ("noise, k_max and budget are for dry runs
  only"): the first attempt stopped after preflight, before any fetch, folder or job. The night was then started
  without the two flags; the experiment's own values are K 4 and 240 s (`gpu/os2_night.py` K_MAX, BUDGET_S), as
  declared. `run.json`: k_max 4, budget 240.0, climb_on_kept true.
- Ledger: the declared copy of `results/loop-night-2026-11-19/os-ledger_after.json` (sha256 8188f4bb..., checked
  before the run) was **not used**: "other calibration (2026-11-19 10:59:49+01:00 -> 2026-11-19 23:09:26+01:00): start
  from tonight's diagnostics" (the declared gate). The night appended its own line to the copy (`ledger_written`); the copy after the night, from the owner's machine, is `os-ledger_after.json` (sha256 396f9c8a...; the
  two earlier lines and tonight's, marked paired).
- `verify` on the owner's machine: every step SAME (`verify_on_owner_pc.txt`). At home (qiskit-aer 0.18.0): every step
  SAME by the test circuits' gates (bytes differ with the versions; the ring sentinel differs, beside).

| job | folder | id | circuits | s model | s charged | RU | created - finished (CET) |
|---|---|---|---|---|---|---|---|
| Dw | `dw/` | dc04ebmq4uuc73a21j3g | 22 | 27.6 | 26 | 0.425 | 14:12:14 - 14:12:52 |
| Dc | `dc/` | dc04enqnj2vs73ddeen0 | 22 | 27.6 | 26 | 0.430 | 14:13:03 - 14:13:39 |
| r1 | `r1/` | dc04f4eq4uuc73a21k90 | 25 | 30.9 | 30 | 0.486 | 14:13:53 - 14:14:31 |
| r2 | `r2/` | dc04fh2nj2vs73ddefog | 23 | 28.7 | 28 | 0.453 | 14:14:44 - 14:15:20 |

Charged 110 s, 1.79 resource units (budget 240 s with the diagnostics; the model's sum 114.8 s).

## Diagnostics and round 1 (`round1.txt`)

```
Dc A: D_late_nb +0.0692 (2 SE 0.0113) loss True;  Dw A: D_cond +0.0093 (2 SE 0.0112) loss False
Dc B: D_late_nb +0.0830 (2 SE 0.0113) loss True;  Dw B: D_cond +0.0008 (2 SE 0.0117) loss False
Dr L 1 (physical qubit 1): P(1|1) 0.9745, P(0|0) 0.9868, gap +0.0122 (2 SE 0.0062) loss True
Dr L 2 (physical qubit 3): P(1|1) 0.9922, P(0|0) 0.9948, gap +0.0025 (2 SE 0.0036) loss False
Dr L 3 (physical qubit 5): P(1|1) 0.9900, P(0|0) 0.9985, gap +0.0085 (2 SE 0.0034) loss True
pick: {1: 'P2', 2: 'P1', 3: 'P2'}  (rule 1 (Dc late-use loss); rule 2 per L (Dr))
```

On 11-19 no Dr gap was resolved and the pick was P1 everywhere; tonight the readout gap is resolved on L = 1 and 3,
so the base candidate there is P2.

## Rounds (`rK/round_scores.json`, `RULEk.json`)

Each round's job holds, per L, the incumbent's ff and the candidate's three arms; d = |P_inc - exact| - |P_cand -
exact| inside the job, 2 SE from the two ff arms.

| round | L | incumbent, P | candidate, P | exact | d (2 SE) | decision |
|---|---|---|---|---|---|---|
| r1 | 1 | P0, 0.8542 | P2, 0.8688 | 0.9371 | +0.0145 (0.0154) | INCUMBENT KEPT; climbing on the kept P2 |
| r1 | 2 | P0, 0.7598 | P1, 0.7372 | 0.8782 | -0.0225 (0.0194) | CANDIDATE NOT ADOPTED; no step left |
| r1 | 3 | P0, 0.6202 | P2, 0.6590 | 0.8230 | +0.0388 (0.0215) | CANDIDATE ADOPTED |
| r2 | 1 | P0, 0.8472 | P2+M, 0.8935 | 0.9371 | +0.0463 (0.0150) | CANDIDATE ADOPTED; no step left |
| r2 | 3 | P2, 0.6562 | P2+M, 0.6892 | 0.8230 | +0.0330 (0.0210) | CANDIDATE ADOPTED; no step left |

Stop: "the rule: no step left on any key: every key keeps its incumbent (after round 2)" (not resumable). Final
incumbents: L = 1 P2+M, L = 2 P0, L = 3 P2+M. No candidate overshot in any round (`cand_overshoot` false in every row).
Beside, never judged: g against P0 in the same job: L = 1 +0.0145, +0.0463; L = 2 -0.0225; L = 3 +0.0388, +0.0532
(`compound.json`). P0 between the two rounds' jobs: L = 1 0.8542 / 0.8472, L = 2 0.7598 / 0.7508, L = 3 0.6202 /
0.6360.

## Against the declaration

| prediction | numbers | |
|---|---|---|
| LP-2 no adopted candidate overshoots in the next round, where it runs as the incumbent | one row testable: L = 3, P2 adopted in r1, as the incumbent in r2 P 0.6562 against noiseless 0.7060 + 2 SE (SE 0.0075): no overshoot. The two steps adopted in r2 (the last round) are not counted, as declared | held |

Predictions over five nights (11-16 to 11-20): 60 declared; 40 held, 20 failed. LP-2 rests on one row tonight: it is held, and it is
thin.

## Two numbers side by side

- Vanity: two of three L end beyond the ceiling of the correction, L = 1 by +0.046 and L = 3 by +0.053 against P0 in the
  same job.
- Essence: every decision tonight was taken inside one job (the incumbent and the candidate side by side), so the
  between-job drift that loopvar found (L = 2, excess SD 0.014) could not be read as a prescription's effect. 110 s
  charged, two rounds, no person in the loop, verify SAME on the owner's PC.

## Reproduce

`python reproduce.py --psf-os <a164fc5> loop-paired-night-2026-11-20-dw loop-paired-night-2026-11-20-dc`; the whole
night (both rounds, the rule and LP-2): `python gpu/os_loop_paired.py verify results/loop-paired-night-2026-11-20` with
psf-os a164fc5 (rebuilds every job, re-scores, re-rules, re-reads the predictions).
