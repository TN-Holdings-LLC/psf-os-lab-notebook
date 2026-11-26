# Ohm rulers, the fourth night's draft: notes (workplace, 2026-11-26)

Draft: `prereg/drafts-2026-11-26/ohm_ruler4_night_DRAFT.md`. Tool: `gpu/ohm_ruler_night4.py` (build4, check4, score4).
Tests: `tests/test_ohm_ruler_night4.py`. All noise in the dry runs is ILLUSTRATIVE, written by hand, at positions
chosen by hand; none is fitted to a device.

## Files

- `tables4.py`, `tables4_spec.json`: the draft's workplace dry-run tables, written from the scores
  (`python notes/ohm_ruler4_2026-11-26/tables4.py ROOT notes/ohm_ruler4_2026-11-26/tables4_spec.json --check
  prereg/drafts-2026-11-26/ohm_ruler4_night_DRAFT.md` exits 0 when every row stands in the draft).
- `scores4_dryruns.tar.gz`: the workplace dry runs' scores3.json and scores4.json per (case, seed), under `seeds/`
  (ROOT for tables4.py is the folder that holds `seeds/` once unpacked). The raw counts of these runs travel in the
  take-home ZIP, not in git.
- `procedure_dry_workplace.txt`: rule 6, `tools/procedure_dry.py` on the draft (11-25 ibm_fez record, sealed 9-pair
  answers): PASS 3, FAIL 0, SKIPPED 3. The workplace VS got the same six lines on its desk.
- `vs_2026-11-26/`: the workplace VS's heavy dry runs (gate noise, damping, one-sided readout with gate noise; Aer
  MPS and GPU statevector, one pod, 85 min): its tables `tab4_t13.md`, `tab4_t4.md` as its `vs_ruler_table4.py`
  printed them, and its runner `vs_dry4_noise.py`. Its 59 runs' scores and raw counts travel in the take-home ZIP.

## How the workplace dry runs were made

- The job: `build4` on the 11-25 ibm_fez record (`results/ohm-ruler3-night-2026-11-25/fetch_in/ibm_fez/dev`, copy
  drow 4) with the sealed 9-pair answers and `--pairs-t 1:7 3:7 4:9`: 173 circuits, check4 ALL PASS.
- The counts: `notes/ohm_ruler3_2026-11-25/dry3.py` (11-25's, unchanged) samples every circuit of the job noise-free
  and applies the readout faults below to the measured bits, readout circuits included; then `score4`.
- Cases: none (no noise); ro1 (every position of the t = 4 cone, 12 to 33: a 1 read as 0 with 0.02, one-sided);
  ro2 (every measured bit flipped with 0.02, two-sided); bo04 (positions 14, 17, 18, outside the window at t = 3 and
  4: both ways with 0.4).

## What was fixed after the workplace VS's reading (2026-11-26)

- qubits.csv: values to 3 decimals (the notebook's rule on 4-digit decimals in records).
- R_LOW: the lower side only (r_q below the pooled r by more than 2 SE); score3's two-sided outlying positions stay
  in scores3.json.
- The draft names (e)'s SE: the per-qubit shot variances summed over the window, the qubits taken as independent.
