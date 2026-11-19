# The compounding loop on psf-os v0.2 (workplace Claude, 2026-11-19; desk only, not declared)

Home handover 2026-11-19, section 4.1: move the loop into psf-os. psf-os branch v0.2-proto-2026-11-18 now holds
`psf_os/loop.py` (the rule with the rungs +M then +F, the ledger, the night runner: fetch, diagnostics, rounds with the
budget checked before a round is built, check, submit, collect, score, rule, finish, resume, verify). This notebook
holds the experiment: `gpu/os_loop.py` (the RUS chain: diagnostics Dw and Dc, round 1 by gpu/os_night.py's rule as
os2_night's round1, rounds built, checked and scored by gpu/os3_night.py, R2's offset choice, compound, predictions).
gpu/os2_run.py, gpu/os2_night.py, gpu/os3_night.py, gpu/os3_run.py are unchanged.

## Dry nights (the 2026-11-18 marrakesh record; `dry/`; noises written by hand, never fitted)

| night | noise | ledger | rounds | what happened |
|---|---|---|---|---|
| n0 | none | none | 1 | P0 everywhere (os_night's rule), fixed point at once |
| n1 | N1 (gamma 0.05, qubit 1 reads 1 as 1 in 0.83) | written | 3 | R1 at L1 and L3 (P2+B), RM at L2 (P1+M, g +0.108 -> +0.149), then R2 at L1 (+Q2, g +0.102 -> +0.142), fixed point |
| n2 | N1 | read (n1) | 1 | the ledger used (same device and calibration time, families agree): starts at P2+B+Q2 / P1+M / P2+B, fixed point after one round (3 rounds saved) |
| n3 | F3 (also qubit 3 reads 1 as 1 in 0.80) | none | 3 | R1 everywhere, then R2 at L1 and L2; the rung F did not fire (an overshoot comes first). F is covered by the unit tests of psf-os (`tests/test_loop.py`), not by a dry night here |

`verify --resim` on n1: every job rebuilt SAME, every round re-scored SAME, every RULE re-ruled SAME, every job
re-simulated SAME, predictions SAME. On n2 the round 1 is re-derived from the records (the diagnostics' stacks and the
ledger line kept in RULE1.json): SAME. A copy of n2 with 50 counts moved in r1: `DIFFERENT r1 re-scored`.

## The device path

`python gpu/os_loop.py go OUT --zip ZIP [--ledger LEDGER.json]`: fetch by gpu/daily_fetch.py (the declared order
marrakesh, fez, kingston), `python -m psf_os submit` / `collect`, the queue read after each submission, zip at the end;
`resume OUT` never sends a job holding a submission.json again; `verify OUT`. Not run on a device here.

## Placement and the build rules of v0.2

Every round item sits on its given rule-C chain, as in os2 (the offsets of +Q and the probe's positions need it), so
the fixed arms are not packed (pack_fixed places items itself); no conditional item shares a circuit with another (single
builds); every manifest records the build environment.

## After the review of 2026-11-19 (psf-os 069463b; this notebook's gpu/os_loop.py)

- **verify across machines**: circuits.qpy byte for byte; when the bytes differ (another qiskit / numpy / Python) the
  gates (gatehash.circuits_digest), the test circuits and the ring sentinel apart (the sentinel beside). A copy of a dry
  night with dw's and r1's circuits rewritten in QPY format 13: `SAME dw job rebuilt (test circuits' gates (the bytes
  differ: other versions))`, the night SAME.
- **collect by value**: psf-os's collect writes the job's state (collect_status.json); the loop reads DONE / WAIT /
  FAILED / UNKNOWN from it; UNKNOWN is not taken for a pending job.
- **preflight for a device run**: `go` needs `--expect-psf-os SHA --declaration PREREG.md`; preflight fails unless
  psf-os HEAD starts with SHA and its psf_os/ is unchanged, the notebook HEAD is the declaration's last commit and the
  checkout unchanged, and a saved account file exists (not read). Tried with a wrong SHA and a draft: every one of
  these lines FAIL, nothing started.
- **ledger seed**: `ledger-seed NIGHT LEDGER` makes a ledger line from a recorded night. From
  results/os2-night-2026-11-18 (`ledger_seed_from_2026-11-18.json`): ibm_marrakesh, calibration 2026-11-18 11:05:21+01:00,
  last stacks P1 / P1 / P1. A dry night on that record with it (noise F3): the ledger used, then RM at L1 and L2
  (P1+M), RF at L1 and L2 (P2+M+F: Dr against the P1 frame), R1 (P2+B), R2 (+Q4, +Q2), stop at K = 4
  (`dry/night_n5.txt`). The rung F fires when a night starts from P1, as the workplace VS found. Tonight the ledger
  is used only if the device's calibration time is still 2026-11-18 11:05:21+01:00.
