# README numbers against the records (home VS, 2026-11-23; home instruction C)

`tools/check_readme_numbers.py results` was run on notebook 73b33a21. Its output is in `check.txt` and `check.json`;
nothing under `results/` was written.

- **Checked:** 51 night folders, those with a README and at least one job record (`job/raw_counts.json` with a job
  id). The other 138 folders have no psf-os job record (TOQB-era records, zips, dry runs) and are not checked.
- **Job tables, charge, RU, circuits, shots, model seconds and delays: 0 mismatches.** The 1008 µs was corrected in
  73b33a21; "18 µs per conditional" is a single delay instruction (L) and is accepted as one.
- **4-decimal values not found in the night's score files: 13.** Each was checked by hand, and none is a mistake:

| night | value(s) | what it is |
|---|---|---|
| ipe-branch-cost-night-2026-11-22 | +0.0067 (0.0073), +0.0023 (0.0083) | S − F per n, beside. Computed for the README, not by the declared scorer; the independent recount (`notes/ipe_branch_cost_2026-11-22/night_check/recount.txt`) gives the same values |
| qpe-parked-night-2026-11-21 | 0.4706, 0.3792, 0.3065 | the ceilings C(4), C(5), C(6). Recomputed with `apps.ipe_ideal`: 0.4706, 0.3792, 0.3065 |
| os-night-2026-11-17 | 0.9009 | 0.8915 + 2 SE 0.0094, written out in the line |
| feedforward-2026-11-16 | 0.5158 | the off arm's circuit value 0.5 + its 2 SE (0.0158); likewise 0.7637 = 0.75 + 0.0137 |
| device-d4-2026-10-28, hub-dt-2026-11-12 | 0.0223, 0.0282; 0.0009 (0.0005), 0.0172 (0.0010) | TOQB-era nights whose numbers sit in a zip or another format; not checked by machine |

## What the tool cannot see

- Numbers written in words.
- Values quoted from another night.
- Tables without a job id.
- The wording around a number. That is for a reader, against `notes/style_beside.md`.
