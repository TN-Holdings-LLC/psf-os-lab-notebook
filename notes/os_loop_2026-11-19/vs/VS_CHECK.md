# The compounding loop on psf-os v0.2: independent check by the workplace VS Claude (2026-11-19, "その2", item 1)

psf-os v0.2-proto-2026-11-18 at 11f07b0 (`psf_os/loop.py`) and the notebook's `gpu/os_loop.py` at 65c7d3fa, both
unchanged. Desk only. No IBM: every night here is a dry night on the marrakesh record of 2026-11-18, with the
hand-written illustrative noises of `notes/os_loop_2026-11-19/noise/` (N1, F3), never fitted. Environment: qiskit
2.5.2, qiskit-aer 0.18.0, Windows; the psf-os test suite on a pod (Linux, Python 3.12, the same qiskit / aer).

| file | what |
|---|---|
| `vs_recount.py` | round 1 counted again from raw_counts, manifest and the run records' out_bit; noiseless value by Aer; qiskit only |
| `vs_rule.py` | `next_stacks` on hand-made rounds: the order of the rules, R3, the stops (14 checks) |
| `vs_scenarios.py` | copies of a finished dry night cut back or damaged, driven by `os_loop.py go / resume / verify` |
| `vs_out/` | the outputs (decimals rounded to three places and JSON floats written as %.3e, for the leak check; the scripts print four) |

## Results

**Scenarios** (`vs_scenarios.py` on copies of dry night a1; `vs_out/vs_scenarios_*.json`): 12 of 12.

| | scenario | result |
|---|---|---|
| S1 | r2 cut back to "submitted, no result" (raw_counts moved away), resume | stops resumable ("not finished"); r2's submission.json unchanged (equal to the uninterrupted night's); no new local run of r2 |
| S1 | the result put back, resume | finishes with every RULE, round score, prediction, compound and the stop the same as the uninterrupted night; r2 run once in all |
| S2 | r2 cut back to "built, not checked", one ff arm's conditionals removed | stops on "check FAIL", job_NOT_SENT, no submission, no RULE3 |
| S3 | r2 not built yet, RULE2's L1 stack replaced by "P9" | stops "build refused (ValueError: P9)", no r2 job |
| S4 | a new night with --k-max 1 | stops "round limit K = 1" after round 1, no r2 |
| S5 | a new night with --budget 90 | stops before round 2: "86.1 s ... round 2 would add 37.6" (86.1 + 37.6 > 90); only r1 built |
| S5 | estimate against build (night a1) | r1 30.9 / 30.9, r2 37.6 / 37.6, r3 37.6 / 37.6 |
| S6 | ledger of another calibration time / another device / a family that disagrees at L2 (P0 against tonight's P1) | not used (the first two), "diagnostics disagree ... the diagnostics win" at L2 (the third); each reason in RULE1.json |
| S7 | verify on night a1 / on a copy with 50 counts moved in r1 | SAME / "DIFFERENT r1 re-scored: /rows/1/g" |

S1's first run read FAIL. My test also wanted the log line "already submitted"; the runner writes it only from
`submit()`, which resume does not call when submission.json exists. The rerun with the test on the submission file
and the run count passes (`vs_scenarios_s1_rerun.json`). Nothing of the runner was wrong there.

**Round 1 counted again** (`vs_recount.py` on night a1, noise N1).
- p, p0, g, 2 SE and the verdict at L = 1, 2, 3 are the recorded ones exactly:
  - L1 OVERSHOOT g +0.216;
  - L2 PRESCRIPTION HELPS g +0.108;
  - L3 OVERSHOOT g +0.145.
- The noiseless values from Aer (200000 shots) agree with the recorded exact ones within 2 SE.
- The probe's Dr is the recorded one at every probe qubit (q1 P(1|1) 0.840, the others 1).
- Night a1 repeats the workplace's dry night n1 (the same noise and record): the same stacks, the same g, and the same
  stop after round 3.

**The rule** (`vs_rule.py`, 14 of 14), each expectation written from the module text:
- R1 comes before the rungs: an overshoot with a gap against the frame gets P2+B, not F.
- R2 adds +Q on a balanced stack.
- With a gap, HELPS gives +M first, then +F (the base switched P1 -> P2). With the rungs given as ("F", "M"), F comes
  first.
- F on P2 needs the reversed gap. There is no F without a gap, and no rung with B.
- R3 takes F off with the base switched back (P2+M+F -> P1+M), and takes M off (P1+M -> P1).
- A first NOT SHOWN does not stop the night; then the fixed point, the round limit and the budget stop it.

**+F on a dry night** (night b1, noise F3, reading the ledger written by night a1 with noise N1; both on the same
record, so the same calibration time):
- L2 starts from the ledger's P1+M. Tonight's diagnostics pick P2, the same family, so the ledger is used.
- After round 1, RF fires: "Dr on q3 gap +0.192 (2 SE 0.013) against the P1 frame -> P2 + F". So L2 goes to
  P2+M+F.
- Round 2 overshoots -> R1, P2+B (M and F dropped). Then R2 adds +Q2, and the night reaches a fixed point after
  round 4.
- Why F never fired on the workplace's nights: round 1's rule (os_night) already picks P2 where Dr shows a gap. P2
  then tends to overshoot, R1 adds B, and no rung climbs with B. F needs a P1 or P2 stack without B whose output
  qubit shows a gap against its frame. That arises when the stack does not come from tonight's Dr (the ledger), or
  when the gap is too small for round 1's rule and large enough for RF.
- The two noises are the workplace's hand-written ones; only their order through the ledger is new. A dry night like
  this tests the mechanism only.

## Points for the workplace Claude and the owner (not changed here)

1. RF does not look at the verdict. It can fire on a round whose verdict is NOT SHOWN, and so comes before R3 when a
   key is NOT SHOWN twice. This follows the module text (RF is listed before R3), but it means "NOT SHOWN twice"
   does not always end in a stop-loss.
2. `start(..., k_max=0 / budget=0)` falls back to the defaults (`k_max or exp.k_max`), as os2_run did (reported
   2026-11-18).
3. In a dry night a missing result stops as "not finished after 60 min", though nothing waited (dry runs never
   wait); the words could say so.
4. The dry nights' `now()` stamps say "CET" with the Europe/Zurich time. That is right in winter; in summer it would
   be CEST.

**The psf-os test suite at 11f07b0** (on a pod: Linux, Python 3.12, qiskit 2.5.2, qiskit-aer 0.18.0,
qiskit-ibm-runtime 0.51.0, 11 workers; `vs_out/pod_pytest_tail.txt`):
- **295 passed, 30 skipped, 0 failed** in 17 min 38 s.
- The 30 skips are environmental: the notebook was not on the pod (TOQB_DIR); quimb and cotengra were not installed;
  PSF_OS_HEAVY was not set.

The tests that need the notebook were then run on this Windows machine with TOQB_DIR set: 13 passed, 2 failed.
- `test_entrance::test_chain_of_equals_the_notebook_builder_on_every_record`: the notebook's
  `notes/hubbard_2026-11-11/hub_cost.py` imports `resource`, which exists only on Unix. This is the machine, not
  psf-os; it needs a Linux run.
- `test_feedforward::test_pack_fixed_on_tonights_pa_record_gives_the_same_ff_bytes`: the QPY format byte is the same
  (17), but the bytes differ. All ten items have the same gates (psf_os.gatehash) and the same metadata.
  - The instructions (names, qubits, order, blocks) are the same in all ten. What differs is the last bits of a few
    angles (3 to 23 per circuit, at most 1.8e-15 apart) and the global phase (2 to 20 ulp apart, and 0 against 2 pi
    for rd2). The record was built on the owner's machine (Python 3.12, numpy 2.5.3); this build is on Python 3.11
    with numpy 2.4.6.
  - The test assumes that the same format byte means the same bytes. That does not hold across numpy / Python
    versions. Comparing the gates, the angles and the global phase (modulo 2 pi) to about 1e-12 whenever the bytes differ would keep the test
    meaningful (not changed here).
