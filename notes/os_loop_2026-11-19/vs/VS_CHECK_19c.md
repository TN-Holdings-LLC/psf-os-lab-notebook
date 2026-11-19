# 19c: verify across machines, preflight, collect, ledger-seed (workplace VS Claude, 2026-11-19, instruction "その3")

psf-os v0.2-proto at 069463b and the notebook at c806f8a0, both unchanged. Desk only; no IBM (collect is tested
with fakes). Two machines:
- this Windows machine: Python 3.11.9, qiskit 2.5.2, qiskit-aer 0.18.0, numpy 2.4.6;
- a pod with the owner's versions (from `results/balanced-repeat-2026-11-18/versions.txt`): Linux, Python 3.12.3,
  qiskit 2.5.2, qiskit-aer 0.17.2, numpy 2.5.3.

| file | what |
|---|---|
| `vs_cross.py` | two records of one night, job by job: bytes, test gates and sentinel gates apart (a digest written here, qiskit only), every manifest / run-record path that differs |
| `vs_patched_verify.py` | verify with the smallest change applied in memory (the file is not changed) |
| `vs_preflight.py` | preflight cases on temporary clones (the real checkouts are never touched) |
| `vs_collect.py` | `ibm.job_state`, `ibm.collect` and `Night.collect` / `run_job` with IBM replaced by fakes |
| `vs_out/` | outputs (decimals rounded to three places for the leak check) |

## 1. verify across machines: a false DIFFERENT remains

The same dry night (`go OUT --dry results/os2-night-2026-11-18/fetch_in/ibm_marrakesh/dev --noise N1`) was built on
each machine.

| verify of | on | result |
|---|---|---|
| the pod's night | the pod | SAME on every line |
| the Windows night | Windows | SAME on every line |
| the Windows night | the pod | DIFFERENT: dw, dc, r1, r2, r3 "job rebuilt: /cells[0]/run_sha256 ..."; every re-score, rule, prediction SAME |
| the Windows night, --resim | the pod | the same five DIFFERENT; every job re-simulated SAME (qiskit-aer 0.17.2 against 0.18.0) |
| the pod's night | Windows | the same five DIFFERENT, the other way round |

- **Cause.** `vs_cross.py` shows that in all five jobs the bytes differ while the test circuits' gates are the same,
  and so are the sentinel's here (the dry nights use the Clifford sentinel).
- **What differs in the manifest:**
  - the top-level `written`, `env/*`, `circuits_sha256` and `qpy_sha256`, which verify already leaves out when the
    bytes differ;
  - and inside the cells, `cells[*].qpy_sha256` and `cells[*].run_sha256`, which it does not leave out.
  - In the run records only `export/sha256` differs.
- **The smallest change** (`vs_patched_verify.py`, applied in memory only): when the bytes differ, also leave out
  `cells[*].qpy_sha256` and `cells[*].run_sha256`. Then the pod's night verifies SAME on Windows on every line ("test
  circuits' gates (the bytes differ: other versions)").
- **A real change is still caught.** A copy of the pod's night with one rz angle in r1 moved by 0.01 gives
  "DIFFERENT r1 job rebuilt: test circuits differ (gates)".
- A proposed patch is in psf-os `vs_check/v02_2026-11-19/verify_cells_19c.patch` (not applied).

## 2. preflight: one hole

`vs_preflight.py`, 9 cases on clones; the saved-account item is left aside (this machine has none).
- PASS: everything as declared passes.
- These fail on the right item:
  - another expected SHA;
  - psf_os/ changed;
  - a commit after the declaration;
  - a changed checkout.
- `go` without `--expect-psf-os` / `--declaration` is refused, and `go` with a preflight FAIL starts nothing. Neither
  makes OUT.
- **FAIL (a hole):** a draft given as the declaration (`prereg/drafts-2026-11-19/os_loop_DRAFT.md`) passes when HEAD
  is the commit that last touched it. The instruction expected a FAIL. Preflight checks only that HEAD is the
  declaration file's last commit, not that the file is a declaration (directly under `prereg/`, not in `drafts-*`).
  A fix: require `os.path.dirname(declaration) == "prereg"`, or refuse a path containing `drafts`.
- Beside: an untracked new file in psf_os/ is not seen (`--untracked-files=no`). A new module there could change
  what is imported.

## 3. collect as values: as written (13 of 13), with one design point

- `job_state` maps 16 status forms as written: enums, `JobStatus.X`, lower case, `INITIALIZING` / `VALIDATING` as
  WAIT, `CANCELED` / `FAILED` as FAILED, and anything else (`COMPLETED`, empty, None) as UNKNOWN.
- `ibm.collect` with a fake service writes collect_status.json with the right state for DONE (raw counts written),
  QUEUED, ERROR, CANCELLED and an unknown status; DONE with a failing result fetch writes DONE and no raw counts.
- `Night.collect` / `run_job`:
  - WAIT -> a resumable stop;
  - FAILED -> a stop;
  - UNKNOWN, DONE without raw counts, and no collect_status.json -> a stop that is **not resumable**.

  Nothing is ever sent again in any case.
- **Design point (for tonight).** A collect that fails for a moment (the network, or the result fetch after DONE)
  ends the night: the stop is not resumable, `go` refuses to resume, and the finish step zips the night. The job
  holds a submission.json and is never sent again, so a resumable stop would be safe for UNKNOWN, for DONE without
  raw counts and for a missing status file. Only FAILED needs to stop for good.
- Also: collect_status.json is not checked for freshness. If a later collect crashed before writing, an earlier WAIT
  would be read again (harmless: it stays resumable).

## 4. ledger-seed: as written

- From `results/os2-night-2026-11-18`, the line matches a hand reading of the records and equals the workplace's
  `ledger_seed_from_2026-11-18.json`:
  - device ibm_marrakesh;
  - calibration time 2026-11-18 11:05:21+01:00;
  - 1 round run;
  - the last stacks P1 / P1 / P1, each PRESCRIPTION HELPS.
- A second seed of the same night is refused ("already in", exit 1).

## 5. Found beside: two calibration times on 2026-11-18

The marrakesh records of 2026-11-18 carry two calibration time stamps (the stamp only; no error number read):
- 10:40:17 in the records fetched at 11:17 (balanced-repeat, parallel-night, timing-night);
- 11:05:21 in the record the loop fetched itself at 11:25 (`results/os2-night-2026-11-18/fetch_in`).

The loop's README (line 7: "calibration 2026-11-18 10:40 CET") and paper 10 (section 7: "recalibrated at 10:40")
say 10:40. The loop's own record says 11:05. Its diagnostics and round 1 ran under the 11:05 calibration. The ledger
seed carries 11:05:21, so tonight's ledger matches only a record with that stamp.
