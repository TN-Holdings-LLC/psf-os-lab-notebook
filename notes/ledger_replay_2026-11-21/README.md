# The ledger's path checked by replaying recorded nights (desk, 0 s on the device; 2026-11-21)

Home VS Claude, from the home instruction `VSクロードへの指示_台帳の道を記録の再生で確かめる_2026-11-21.md`. The report
is `VSから家へ_台帳の再生_2026-11-21.md` (psf_zero_project).

The path under test: on the same device with the same calibration time, the previous night's stacks become round 1's
stacks (paired: candidates). The device has never run it. On 11-18, 11-19 and 11-20 the calibration times differed.

## The tools

- psf-os branch `ledger-replay-2026-11-21` (from a164fc5):
  - `start(..., replay_from=RECORD)`: dry runs only. Each job is answered from the record's raw counts, cell by cell
    (cell name and gates). The ring sentinel is matched by its name only.
  - A circuit not in the record stops the night: "記録にない", not resumable. There is no simulation in its place.
  - `replay.json` per job names the recorded job of every cell.
  - A broken ledger is not used, and the reason is written (`why`).
- `gpu/ledger_replay.py WORK` (new; `gpu/os_loop.py` and `gpu/os_loop_paired.py` are imported read only) runs every
  case below. Its output is in `summary.txt` and `summary.json` (copied here).
- The device record of each night is its own `fetch_in/` record. The hand-made ledger line has that record's device
  and calibration time, and the final stacks from that night's own `os-ledger_after.json`.

## Results

| case | ledger | round 1 | the night | against the record |
|---|---|---|---|---|
| (d) paired 11-20, the ledger it read | not used: other calibration (as recorded) | incumbents P0; candidates P2 / P1 / P2 (base) | two rounds, stop "no step left on any key" | RULE1-3 **bytes SAME**, stop SAME, every job from its own recorded job, verify SAME |
| (d) 11-19 (no pairs), the ledger it read | not used: other calibration (as recorded) | P1 / P1 / P1 | three rounds, fixed point | RULE1-4 **bytes SAME**, stop SAME, verify SAME |
| (a) paired 11-20 + a ledger line (11-19 23:09:26, P2+M / P0 / P2+M) | **used** (`ledger_used` true) for L1, L3; L2: the diagnostics disagree (P1 against P0), the diagnostics win | incumbents P0; candidates P2+M (step ledger) / P1 (base) / P2+M (ledger): as the declared rule | r1 replayed from cells of r1 and r2. L1 P2+M ADOPTED (+0.0463), L3 P2+M ADOPTED (+0.0532), L2 P1 INCUMBENT KEPT (−0.0135) -> climbing: P1+M | **stops at r2: 記録にない** (P1+M at L2: `ff_y2ac` and its off and floor were never run) |
| (b) 11-19 + a ledger line (11-19 10:59:49, P1+M / P0 / P0) | **used** for L1; L2, L3: the diagnostics disagree (P1 against P0) | P1+M / P1 / P1 | r1, r2 from cells of their own job and r3 (L1's P1+M). R3 stop-loss at L2, L3 -> P0, then a fixed point after round 3 | ran to its end; verify SAME |
| (c) other device (ibm_fez) | not used: "other device (ibm_fez -> ibm_marrakesh)" | the diagnostics' | as (d) | RULE2-3 bytes SAME; RULE1 the same but for the ledger's fields |
| (c) other calibration (11-19 10:59:49) | not used: "other calibration (...)" | the diagnostics' | as (d) | as above |
| (c) broken file (not JSON) | not used: "ledger unreadable (the file is not JSON (JSONDecodeError))" | the diagnostics' | as (d) | as above |
| (c) broken line (last_stacks a list) | not used: "ledger unreadable (its last_stacks is not a table of keys (list))" | the diagnostics' | as (d) | as above |
| (c) a line without L3 | used for L1; L3: "no stack for this key in the ledger" (the diagnostics' P2); L2: the diagnostics disagree | candidates P2+M (ledger) / P1 / P2 | two rounds, stop "no step left on any key" | another night by design |

## What the replay cannot tell

- **Cells from two recorded jobs.** In (a), round 1 takes L2's P1 from recorded r1 and L2's P0 from recorded r2 (the
  primary source). The paired decision for L2 then compares two jobs. That is the comparison the paired design
  avoids: the record had −0.0225 (NOT ADOPTED) inside r1, and the replay gives −0.0135 (KEPT). The same happens in
  (b), where L1's P1+M comes from r3 and P0 from r1 / r2. `replay.json` lists these cells (`one_recorded_job` false).
  The decisions on such keys show the software's path, not a device result.
- **A circuit never run.** It cannot be replayed. (a) stops at round 2 for P1+M at L2.
- Before this branch, a broken ledger stopped the night with a Python error. It now goes unused, and the reason is
  written.
