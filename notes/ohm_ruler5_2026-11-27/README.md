# Ohm rulers, the fifth night's draft: notes (workplace, 2026-11-27)

Draft: `prereg/drafts-2026-11-27/ohm_ruler5_night_DRAFT.md`. Tool: `gpu/ohm_ruler_night5.py` (build5, check5, score5).
Tests: `tests/test_ohm_ruler_night5.py`. All noise in the dry runs is ILLUSTRATIVE, written by hand, at positions chosen
by hand; none is fitted to a device.

## Files

- `expect5.py`: the draft's table of expected words per (ruler, t), from the fourth night's dry runs
  (`notes/ohm_ruler4_2026-11-26/scores4_dryruns.tar.gz` and the VS's `vs_2026-11-26/tab4_*.md`), with the class rule
  and `--check DRAFT`; `--json` prints the classes that `gpu/ohm_ruler_night5.py`'s EXPECT must equal (tested).
- `tables5.py`, `tables5_spec.json`: the fifth night's own dry-run rows, written from the scores, with `--check DRAFT`.
- `scores5_dryruns.tar.gz`: those runs' scores3.json and scores5.json (raw counts in the take-home ZIP, not in git).
- `procedure_dry_workplace.txt`: rule 6 on the draft (the 11-26 ibm_fez record, the sealed 9-pair answers).
- `run_ohm_ruler5_night_DRAFT.sh`: the device part of the night as a script (VPN OFF, no git), written from the 11-26
  record's files; home compares it with its 11-26 script before use.

## How the fifth night's dry runs were made

- The job: `build5` on the 11-26 ibm_fez record (`results/ohm-ruler4-night-2026-11-26/fetch_in/ibm_fez/dev`, copy
  drow 4), the sealed 9-pair answers, `--pairs-t 1:7 3:7 4:9`: 175 circuits, the readout pubs at 0, 1 and 171 to 174,
  check5 ALL PASS.
- The counts: `notes/ohm_ruler3_2026-11-25/dry3.py` (unchanged) samples every circuit noise-free and applies the
  readout faults to the measured bits, readout circuits included; then `score5`.
- Cases: none (no noise), ro1 (every position of the t = 4 cone: a 1 read as 0 with 0.02), bo04 (positions 14, 17,
  18, outside the window at t = 3 and 4: both ways with 0.4). These check the job and the tool; the rulers' behaviour
  under gate noise and damping is the fourth night's (the job's gates are unchanged).
