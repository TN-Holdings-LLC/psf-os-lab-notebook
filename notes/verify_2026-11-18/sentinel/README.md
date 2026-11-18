# Part 5: the sentinel bytes (home VS Claude, 2026-11-18)

sentinel_check.py -> sentinel_check.txt / .json.

- Environment here: python 3.12.13, qiskit 2.5.2, qiskit-aer 0.17.2, qiskit-ibm-runtime 0.49.0, numpy 2.5.5, scipy
  1.18.1, rustworkx 0.18.1.
- The balanced repeat and both timing jobs, rebuilt from the recorded device records, are byte-identical to the jobs
  built on the owner PC: file by file and the assembled job/circuits.qpy, the four ring-sentinel circuits included
  (numpy 2.5.5 here against 2.5.3 there).
- So the difference home found lies with home Claude's environment. Per-circuit sentinel hashes are recorded for a
  circuit-by-circuit comparison; the function of home Claude's differing circuits could not be compared here (their
  bytes are not in the record).
