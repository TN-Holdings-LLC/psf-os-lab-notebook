# Home PC environment for the compounding OS night (workplace VS Claude, 2026-11-18)

Environment: `psf_zero_wsl_env_fresh` (WSL). This lists what the night's tools import, the versions they were checked
with at the workplace, and what `gpu/os2_run.py preflight` is to look at.

## Packages

| package | needed by | checked at the workplace | requirement it declares |
|---|---|---|---|
| Python | all | 3.11+ | psf-os, qiskit-aer: >= 3.11 |
| qiskit | all | 2.5.2 | psf-os: >= 2.0; qiskit-aer 0.18.0: >= 1.1, < 3; qiskit-ibm-runtime 0.51.0: >= 2.3, < 3 |
| qiskit_aer | check of every build (wait_night, ctrl_night, os_night, os2_night), `FF.run_local` (dry) | 0.18.0 | qiskit < 3 |
| qiskit_ibm_runtime | psf-os submit / collect / fetch, gpu/daily_fetch.py, FakeMarrakesh lengths (ledger) | 0.51.0 | qiskit >= 2.3 |
| numpy, scipy | all | 2.4.6, 1.17.1 | - |
| psf_os | build, place, submit, collect | 0f57c76 (branch feedforward-2026-11-16) | - |

**qiskit_aer at home.** Last night's home run used submit / collect / daily_fetch only. Whether qiskit_aer is
installed is not known.
- If `python -c "import qiskit_aer"` fails, the owner types this, with VPN OFF, in the environment:

  ```
  python -m pip install "qiskit-aer==0.18.0"
  ```

- Any qiskit 2.x works with it.
- To read the versions first:

  ```
  python -c "import qiskit, qiskit_ibm_runtime; print(qiskit.__version__, qiskit_ibm_runtime.__version__)"
  ```

## What preflight is to check (from the workplace instruction)

1. qiskit, qiskit_aer, qiskit_ibm_runtime and psf_os import.
2. psf_os is at 0f57c76, read with `git rev-parse HEAD` in psf_os's own folder (no network).
3. The notebook's HEAD equals the declaration commit (the `git worktree add` folder).
4. Suggested additions:
   - The saved IBM account exists. Check that the file exists only; never read or print its contents.
   - `OUT` does not exist yet (daily_fetch refuses an existing folder too).
   - the psf_zero_project folder on the home PC is writable, for `res_os2_1118.zip`.
   - Python >= 3.11.

`go` does not start unless preflight passes.
