# psf-os 0.3.2 (candidate): time units and the charge for delays, checked (home VS, 2026-11-23; desk)

The psf-os branch is `units-and-charge-2026-11-23` (53ef048, from v0.3.1). It is not tagged and not released.

| file | what it holds |
|---|---|
| `branch_night_priced.py`, `priced.txt` | the 2026-11-22 branch-cost job (plan d) rebuilt with the candidate on the night's device record and its dt (4 ns) |
| `reproduce_0.3.2.txt` | `reproduce.py --psf-os <0.3.2 candidate>`: 93 of 93 SAME |
| `verify_loop_1119_0.3.2.txt`, `verify_loop_1120_0.3.2.txt` | `os_loop.py verify` and `os_loop_paired.py verify` with the candidate: every step SAME (16 and 13) |

## The branch-cost job rebuilt

- **The limit refuses it.** Without `allow_long_delay`, the candidate refuses the job: 32 circuits hold delays over
  100 µs, the longest 1008 µs.
- **With `allow_long_delay=True`:**
  - per-circuit delays: 270, 504, 540 and 1008 µs (as in the README of the night);
  - delay seconds: 54.8 s;
  - `qpu_seconds_model`: 59.6 + 54.8 = 114.4 s, against 112 s charged (+2.4 s, +2.1 %).
- **The 105-job relation** (2.6 s + 0.000269 s per circuit-shot) with the same delay term gives 111.4 s.

## Why the earlier records rebuild unchanged

The records before 0.3.2 hold no dt. Delays in dt (11-18 parallel and timing nights, 11-22 branch-cost night) are
then recorded in dt only, neither limited nor priced, and the job files are the same.
