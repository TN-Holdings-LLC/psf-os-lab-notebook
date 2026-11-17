# Draft: what every result README records about the queue and the job's time (workplace Claude, 2026-11-18)

Home handover 2026-11-17 night, section 2 (the fifth round: the queue read 0 before submission, 11 right after it, the
two jobs "running" for about 9.5 minutes while the device executed their circuits for 38.6 s and 9.1 s). A draft for
the owner; nothing here touches a service. Only the home machine talks to IBM.

## Three things every result README states from now on (proposal)

1. **The queue**: pending jobs per device as read before submission (`fetch_in/queue.json`, already written by
   `gpu/daily_fetch.py`) and right after it (`queue_after.json`, the new line below).
2. **Each job's created / running / finished** (CET), from the runtime's own metrics already saved in
   `job/raw_counts.json`.
3. **Executing time against wall-clock time**: the device's `circuits_execution_time_ns` against finished - running,
   and the charged seconds.

`python gpu/job_timing.py RESULT_DIR ... --md` prints 1 (before; after when recorded), 2 and 3 as a table from the
recorded files; `--json FILE` writes them. Today's five rounds: `job_timing_2026-11-17.md / .json` here.

## The one line for the send procedure (VPN OFF, home only, right after the submit command)

```bash
python -c "import json, datetime as d; from qiskit_ibm_runtime import QiskitRuntimeService as S; s = S(); json.dump(dict(read=d.datetime.now(d.timezone.utc).isoformat(), pending={n: s.backend(n).status().pending_jobs for n in ['ibm_marrakesh', 'ibm_fez', 'ibm_kingston']}), open('OUT/queue_after.json', 'w'), indent=1)"
```

It uses the saved account, as `gpu/daily_fetch.py` does, and reads no key and no quality number. OUT is the night's
result folder. It runs once, right after the last job of a round is submitted. A second read when the jobs finish is
optional (`queue_done.json`, the same line).

## Today's five rounds, read this way (from the records only)

| round | queue before (marrakesh / fez / kingston) | jobs: wait in queue (s) | running -> finished (s) | executing (s) | share |
|---|---|---|---|---|---|
| 1 fez, 11:14 | 1170 / 1 / 5 | 1-2 | 17 / 33 / 78 / 90 | 10.5 / 20.5 / 48.4 / 20.6 | 0.62 / 0.62 / 0.62 / 0.23 |
| 2 marrakesh, 11:26 | 2 / 3 / 4 | 2 | 25 / 49 / 103 | 17.5 / 28.7 / 57.0 | 0.70 / 0.58 / 0.55 |
| 3 marrakesh, 11:59 | 1 / 0 / 2 | 1-3 | 35 / 53 / 33 | 23.8 / 24.0 / 24.3 | 0.68 / 0.45 / 0.75 |
| 4 marrakesh, 12:51 | 3 / 0 / 10 | 269 | 49 | 38.3 | 0.77 |
| 5 marrakesh, 15:21 | 0 / 0 / 37 | 1-2 | 562 / 582 | 38.6 / 9.1 | **0.07 / 0.02** |

- On every other job of the day, the device executed for 0.45-0.77 of the running time (one 0.23: round 1's fourth
  job). The fifth round's two jobs executed for 0.07 and 0.02 of it, while both were reported as running from the first
  two seconds. So the long time was not a queue wait (that is the created-to-running time, 1-2 s here). It was time
  spent "running" without executing our circuits.
- The records do not say whether other users' circuits ran in between (interleaving), or whether the controller waited
  for something else. With queue_after.json and a second read at the end, the next such night shows whether the
  pending count rose with our submission.
- Effect on the verdicts: the off arms of the same jobs agree single against packed within 0.03 (README of the
  fifth round). Whatever filled the 9.5 minutes, it did not move the arms without conditionals. That it did not move
  the ff arms is not shown either; the packing test's own control is the single job, which shared the same window.
