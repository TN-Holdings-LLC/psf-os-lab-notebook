# The branch-cost test of IPE: desk preparation (home VS, 2026-11-22 night; home instruction part B; no device)

These are the desk records behind `prereg/drafts-2026-11-23/ipe_branch_cost_DRAFT.md`. The tool is
`gpu/ipe_branch_cost_night.py`, and it runs on psf-os 0.3.1 as released.

- **`table.json`:** the four plans (a, b, c, d), all under 60 s by the model. Their 2 SE are sized on the fez record of
  2026-11-22. The file also holds the phases k · a mod 2^n.
- **`checks/`:** `check` for every plan, built on the 2026-11-22 records of ibm_fez and ibm_kingston
  (`results/likely-park-night-2026-11-22/fetch_in`). All eight PASS.
- **`dry/`:** plan a under three ILLUSTRATIVE noise types (written by hand, never fitted), plus plans b and d under
  both:

  | file | noise |
  |---|---|
  | `noise_cond.json` | a dephasing at every conditional |
  | `noise_wait.json` | a damping and dephasing per wait unit (one conditional, or a delay of L) |
  | `noise_both.json` | both |

  The scores show the two differences separating as intended:

  | noise | SD − F | S − SD |
  |---|---|---|
  | cond | +0.092 | −0.001 |
  | wait | +0.000 | +0.130 |
  | both | +0.075 | +0.130 |

## Found while building

- **Delays survive only in dt.** qiskit 2.5.2's qpy keeps the unit dt only:
  - a delay in us comes back as the same number of dt;
  - a delay in s is refused when psf-os writes the job.

  The tool therefore writes delays in dt, with L in dt as [OWNER]. The device records hold no dt.
- **The forms carry the same gates.** psf-os parks the target at F's runs of corrections. S and SD carry the same
  parking pair behind their own fences, so the X and SX gates and the fences match F's at every phase (`check` (2)).
