# Independent review of the compounding OS tools (workplace VS Claude, 2026-11-18; for the workplace Claude)

**What was reviewed:**
- `gpu/os2_night.py` at af5d6471 (the draft), read and run through `branch_noise.py loop` on the 11-17 marrakesh
  record.
- The checks that need `gpu/os2_run.py` wait for that file. Those are resume without a double submission, the stops on
  FAIL and refusal, verify, preflight, and the network / key / IBM lines. `audit_os2.py` is ready for the IBM, network
  and key lines.

## Found, to fix in the tools

1. **The budget does not count what the instruction says.**
   - `round1` starts `model_seconds_so_far` at 0, so Dw and Dc are left out.
   - `rule()` passes `next_cost = last_rule["qpu_seconds_model"]`, the last round's cost, not the next round's
     estimate.
   - The next round can cost more (30.9 s -> 40.9 s when +B is added).
   - The rule in the instruction: Dw + Dc + rounds run + the next round's estimate > 240 -> stop before that round.
     `branch_noise.loop` does it this way: build, read its qpu_seconds_model, check the budget, and only then run.
2. **The budget cannot bind at K_MAX 4.**
   - A night is at most 55.2 + 4 x 40.9 = 218.8 s on the 11-17 marrakesh record.
   - To see the budget stop in a dry run, `go --dry` needs a budget override (dry only, never the device run).
3. **K_MAX 4 rarely binds**, because the ladder has three moves.
   - The round limit was seen only with K_MAX 3 in a dry run.
   - A `--k-max` override for dry runs only is suggested.
4. **The diagnostics in `go --dry`.**
   - `wait_night.py` / `ctrl_night.py build` write the h = 0.6 sentinel (40 qubits, not Clifford), which `run_local`
     refuses.
   - The dry path must build them with `sentinel_spec=dict(kind="echo_clifford", D=24)`, as `branch_noise.loop` does.
5. **OS2-3 often has no L to judge.**
   - `compound_rows` credits only the L credited in every round, and an L that overshoots in round 1 never is.
   - Under decay this was the usual case (s1, s5, s8).
   - The declaration should state the wording for "no L credited in every round" (the owner's decision).

## Checked, no change needed

1. **+Q placement:**
   - The offsets 0, 2 and 4 for L = 1, 2, 3 on the 11-17 records of marrakesh, fez and kingston are all on usable
     qubits and couplers (rule C's own check), and never on a failed mark.
   - With a failed qubit added by hand (5, 9 or 12 on marrakesh), rule C reroutes the probe's chain and the shifted
     chains the same way, so nothing lands on the failed qubit.
2. **+B with +Q:** both frames (xr, xn) get the same shifted chain in every case.
3. **Determinism:**
   - Recomputing the rule from the recorded round_scores gives byte-identical RULE files, twice (s5, s6, s8).
   - The rule, scores and compound read no time, random number or calibration value (audit: no line in os2_night.py
     or os_night.py).
4. **P0 is the same every round:** in s5, s6 and s8 the P0 circuits (ff, off, floor) are byte-identical in qpy across
   rounds.
5. **IBM lines outside os2_run:** `gpu/daily_fetch.py` touches IBM only through the saved account, the queue read
   (`pending_jobs`) and `psf_os fetch`.

## To run when os2_run.py exists

- `python notes/os2_2026-11-18/audit_os2.py gpu/os2_run.py`. Expect only psf-os submit / collect, daily_fetch and
  the one queue line, with no key and no git network operation.
- `go --dry` with the settings of `branches.md` (s6 for R3, s8 for R1 / R2 / R3, s5 with K 3, s1 with budget 150).
- Stop after the first submission, then `resume`. It must not submit again, and the result must match the run
  without a stop.
- A check FAIL (one tampered circuit) and a build refusal (a rule from another device) must stop the run, with nothing
  submitted after.
- `verify` must give SAME on a dry output and DIFFERENT after one file is changed.
