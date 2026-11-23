# Try-builds of the Ohm window night (home VS, 2026-11-23; desk, no device)

For `prereg/drafts-2026-11-23/ohm_window_night_DRAFT.md` and `gpu/ohm_window_night.py`, on the newest device records in
this notebook (`results/ipe-branch-cost-night-2026-11-22/fetch_in/<device>/dev`, 11-22 12:56 CET), psf-os 0.3.3.

| file | what it holds |
|---|---|
| `answers_checks.txt` | `answers`: the checks it prints (no values) and the answers file's sha256 (the file is held outside the repository, sealed) |
| `ibm_fez/build.json`, `ibm_kingston/build.json` | `build`: chain, F's copy, every item's chain positions and physical qubits, CZ, CZ layers, parking, floors, circuits, seconds |
| `ibm_fez/check.json`, `check.txt` (and kingston) | `check`: ALL PASS on both |

- Both build: 180 circuits, 1000 shots, 51.0 s (2.6 + 0.000269 x circuits x shots); psf-os's model 58.1 s.
- Chain shape S1 on both; F's copy is drow 4 on fez and drow 0 on kingston.
- Every light-cone item sits on F's physical qubits at the same chain positions. Without the tool's pin, psf-os placed
  the 4-qubit cone at drow -4, dcol -8 on fez (the build stopped and said so).
- CZ is as intended on every item, and A1 = A2. No delay and no gate after a measurement in any sent circuit: nothing to
  park.
- Check, on both devices:
  - per-qubit <Z> against the answers: worst 1.6e-10 (168 circuits);
  - the 4 mirrors: 2.6e-14;
  - the twins' windows: 5.7e-11.
  The two devices give the same numbers: the compiled gates are the same up to the physical qubit numbers.
- `score` was run on synthetic counts (independent bits drawn from the answers, 1000 shots) to test the code path. It
  gave every cell READS, every twin SAME and the order yes on both twins. Its output is not kept, because it would show
  answer values.
