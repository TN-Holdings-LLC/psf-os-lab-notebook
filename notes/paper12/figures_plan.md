# Paper 12: figures and tables (a plan; no script yet; workplace, 2026-11-27)

Every plotted value is to be written into `notes/paper12/fig_data.csv` with its source, as paper 11 did.

## Figure 1. The raw window and its distance from the exact value

- Panels: t = 1, 3, 4; x: the three arms (A0, A1, A2); y: raw W (device) and W (exact), with 2 SE bars; one marker per
  night (11-24, 11-25, 11-26, `[NIGHT 5]`); a band for READS / DOES NOT READ by the ratio rule (beside, on a second
  row of small numbers).
- Records: `results/ohm-ruler-night-2026-11-24/README.md`, `results/ohm-ruler3-night-2026-11-25/README.md`,
  `results/ohm-ruler4-night-2026-11-26/README.md` (raw tables), their `scores*.json` for the SEs.
- Says: the window reads (vanity) while W stays 0.14 to 0.47 above exact at t >= 3 (essence); A2 t = 4 stops reading
  on 11-26.

## Table 1. Which ruler carries the shrink, night by night

- Rows: rulers (a), (b), (b'), (c), (d), (e), (de), (a'); columns: nights 11-24, 11-25, 11-26, `[NIGHT 5]`; cell: AGREES
  count of 6 at t >= 3, "-" where the ruler was not run that night, "beside" where it was not judged.
- Records: the three READMEs' ruler tables and `scores3.json` / `scores4.json`.

## Figure 2. The readout's half: (d) against (de)

- x: cell (A0 to A2, t = 1, 3, 4); y: d (ruler W minus exact W) with its t width; two markers per cell, (d) and (de);
  11-26 (and `[NIGHT 5]`). Inset: dry runs, AGREES share of (d) and (de) under readout faults (none, one-sided 0.02,
  two-sided 0.02, outside 0.4).
- Records: `results/ohm-ruler4-night-2026-11-26/or4/scores3.json` (d), `or4/scores4.json` (de, de_vs_d);
  `notes/ohm_ruler4_2026-11-26/scores4_dryruns.tar.gz` (inset).

## Figure 3. What no ruler carries at t = 3, and what a fixed rotation does

- Left: d at t = 3 for (b), (c), (d), (de), (a') on 11-25 and 11-26 (`[NIGHT 5]`), per arm, with t widths (all on
  the positive side on 11-26).
- Right: the twirl dry runs, d of (d) and (de) at t = 3 against theta (0, 0.05, 0.10) for no twirl, mirror-only twirl
  and full twirl, and (e)'s d for full twirl.
- Records: the nights' `scores3.json` / `scores4.json`; the workplace VS's twirl table and raw counts (2026-11-27;
  to be committed by home under `notes/twirl_dry_2026-11-27/` before the figure is made).

## Figure 4. The per-qubit record

- x: physical qubits on the t = 4 cone (92 to 121); y: nights (11-24, 11-25, 11-26, `[NIGHT 5]`); colour: the |0>
  mirror (lowest over arms); markers: MIRROR_LOW, R_LOW, R_HIGH. A side panel: for 104, the mirror, m_q, r_q and e_q
  per arm at t = 3 and 4 (the "mirror low but r fine" case).
- Records: `results/ohm-ruler4-night-2026-11-26/qubits.csv`; `tools/qubits_across.py` (tools6, 6d5abe83) for 11-24
  and 11-25 rebuilt from their raw counts.

## Table 2. The direction (r - rho) with rho_a and rho_a'

- Rows: cells at t >= 3; columns: nights; entries: LESS / MORE / NOT SEEN for rho_a (beside) and rho_a' (judged from
  11-26).
- Records: `results/ohm-ruler3-night-2026-11-25/README.md` (and notes/verify_2026-11-25/ for (a') after the record),
  `results/ohm-ruler4-night-2026-11-26/score.txt`.

## Table 3. Against IBM's calibration (beside)

- Rows: kinds (mirror_low, r_low, scan_listed, sentinel_dead); columns: readout_error, T1, T2, CZ, any; cell: hit rate
  / chance; plus IBM misses; a second small table with the map's age (median, share over 24 h) and day-to-day ratios.
- Records: `notes/calib_compare_2026-11-26/tables.md`, `tables.json`, `result_2026-11-27.md` (calib-compare2,
  786ae051).
