# Running the compounding OS night: `gpu/os2_run.py` (workplace Claude, 2026-11-18)

Home instructions "複利の OS を今夜実機で" and its addendum; the workplace VS's review (`REVIEW_VS.md`, `audit_os2.py`,
`branch_noise.py`). Declaration text: `prereg/drafts-2026-11-18/os2_night_2026-11-18_READY.md`. psf-os 0f57c76,
unchanged (its tests with TOQB_DIR: 305 passed, 1 skipped, 2026-11-18 at the workplace).

## Commands

```
python gpu/os2_run.py preflight [--dry] [--out OUT] [--zip ZIPFILE]
python gpu/os2_run.py go OUT --zip ZIPFILE                        the night on the device
python gpu/os2_run.py go OUT --dry DEVDIR [--noise N.json] [--k-max K] [--budget S]     dry only
python gpu/os2_run.py resume OUT [--zip ZIPFILE]
python gpu/os2_run.py verify OUT [--resim]
```

- **preflight**: imports (qiskit, qiskit_aer, qiskit_ibm_runtime, psf_os); a missing qiskit_aer prints the line to
  install it (`python -m pip install "qiskit-aer==0.18.0"`, VPN OFF); versions other than those the workplace VS
  checked (qiskit 2.5.2, aer 0.18.0, runtime 0.51.0) are noted, not a stop; psf_os at 0f57c76 with psf_os/ unchanged;
  the notebook's HEAD is the commit that last changed `prereg/os2_night_2026-11-18.md`, no tracked file changed; the
  tools present; Python >= 3.11; (device runs) a saved IBM account file exists (looked for, never opened); OUT does
  not exist; the zip's folder is writable and the zip does not exist. `go` does not start unless it passes.
- **go**: fetch (gpu/daily_fetch.py) -> Dw, Dc (build, check, submit, queue after, collect, score) -> os_night rule
  -> RULE1 -> per round: budget (diagnostics + rounds built + this round's model seconds from a build in a temporary
  folder <= 240, else stop before building it) -> build -> check -> submit -> queue after -> collect (60 min) ->
  score -> rule -> RULE{k+1} -> stop when the rule says (fixed point, K_MAX 4) -> compound, predictions, job timing,
  zip. K_MAX and the budget can be overridden with --dry only.
- **Never twice**: a job folder with submission.json is not submitted again; resume continues from the files that
  exist (a collect that times out stops with resumable true).
- **Dry**: every job simulated by `branch_noise.noisy_run_local` (noiseless with no noise), the wide seeds (Dw B, Dc B
  + 500000, round k B + 1000000 k, circuit i + 10000 i; B = 20261118), the diagnostics with the Clifford sentinel.
- **verify**: rebuilds every job from the recorded device record and RULE files (circuits.qpy byte for byte; the
  manifest but for its write time), re-scores every job from its counts, re-applies os_night's rule, round 1 and
  every rule, re-reads the predictions, recomputes the stop reason; --resim (dry) simulates every job again with its
  recorded seed. SAME / DIFFERENT.
- **IBM is touched** only by `python -m psf_os submit`, `python -m psf_os collect`, gpu/daily_fetch.py and the queue
  read after each submission (saved account; `pending_jobs` only). No key is read; git runs only `rev-parse`,
  `status`, `log` on local checkouts (audit_os2.py lists every such line).

## Dry runs on the 2026-11-17 records (wide seeds; every one verify --resim SAME)

| night | record | noise (illustrative, never fitted) | round 1 | the rule's moves | stop | model s |
|---|---|---|---|---|---|---|
| m0 | marrakesh | none | P0 / P0 / P0 | none | fixed point after round 1 | 76.1 |
| f0 | fez | none | P0 / P0 / P0 | none | fixed point after round 1 | 76.1 |
| s6 | marrakesh | gamma 0.01 | P1 / P1 / P1 | round 2: R3 at L 1, 2, 3 -> P0 | fixed point after round 3 || 137.9 |
| s8 | marrakesh | gamma 0.02, P(1\|1) 0.83 on q3 | P1 / P2 / P1 | R1 L 2 -> P2 + B; R2 L 2 -> +Q2 (output q3 -> q5); R3 L 1 -> P0 | fixed point after round 3 || 151.2 |
| s5k3 | marrakesh | gamma 0.03, q1 0.83, --k-max 3 | P2 / P1 / P1 | R1 L 1; R2 L 1 -> +Q2 | fixed point after round 3 || 154.5 |
| s6k2 | marrakesh | gamma 0.01, --k-max 2 | P1 / P1 / P1 | R3 at round 2 | **round limit K = 2** || 117.0 |
| s1b | marrakesh | gamma 0.08, q1 0.83, --budget 150 | P2 / P1 / P1 | R1 at L 1, 2, 3; R2 L 1 -> +Q2 | **budget** before round 3 (127.0 + 40.9 > 150; not built) | 127.0 |
| fa | fez | gamma 0.05, q1 0.83 | P2 / P1 / P1 | R1 L 1, 3; R2 L 1 -> +Q2 | fixed point after round 3 || 161.3 |

Every stop and branch of the declaration happened inside `go`: R1, R2 (+Q), R3, a fixed point, the round limit (with
K 2, dry only) and the budget (150 s, dry only); with K 4 and 240 s neither can bind on these records (at most 55.2 +
4 x 40.9 = 218.8 s), unless the draw is unlucky (the workplace VS saw K 4 bind once under another seed formula).

## Stops and records tested by hand

- **resume**: round 3 submitted, its counts withheld: the run stops "not finished, resumable"; with the counts back,
  `resume` scores round 3 without simulating (submitting) it again, and RULE4.json and the round scores are identical
  to the uninterrupted night.
- **check FAIL**: round 3's circuits replaced by a round with another stack: check FAIL, the job moved to
  job_NOT_SENT, the night stops, nothing more is sent.
- **build refusal**: RULE2 naming another device: the estimate build refuses, the night stops before building.
- **verify**: SAME on every night above; DIFFERENT for a changed score (round_scores.json), a changed rule
  (RULE3.json; also its rebuilt job), a damaged circuits.qpy, and one changed count (re-score and re-simulation).

## A property to know

R1 adds +B after an overshoot, and R3 removes the last layer after two rounds NOT SHOWN; under a lean that comes and
goes, an L can move P2 -> P2 + B -> P2 within four rounds (seen once in a dry run). K_MAX bounds it; the declaration
does not forbid it.
