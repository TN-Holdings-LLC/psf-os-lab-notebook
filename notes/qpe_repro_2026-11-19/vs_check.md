# Phase estimation reproduction: independent check by the workplace VS Claude (2026-11-18, about 05:00-06:00 CET)

Instruction: "VSクロードへの指示_位相推定の再現の点検_2026-11-18" (workplace Claude). Branch `qpe-repro-2026-11-19`
(67e74050) as received; the tool `gpu/qpe_repro_night.py` was not changed. Desk only (Aer). No IBM, no calibration
number read, illustrative noises only (the four hand-written files of `noise/`). Environment: qiskit 2.5.2,
qiskit-aer 0.18.0, numpy 2.4.6, scipy 1.17.1, Python 3.11.9, psf-os 0f57c76 (Windows).

The independent code is in `vs/`, and its outputs are in `vs_out/` (floats as %.3e). It imports qiskit and qiskit_aer only: not the tool, apps, coherent, or psf-os.
- `vs_ceiling.py`: the ceiling.
- `vs_bits.py`: the bit order on the compiled circuits.
- `vs_score.py`: the score, from `raw_counts.json` and `manifest.json` only.
- `vs_mutate.py`: the mutation test. It runs the unchanged tool's `check` on damaged copies.

## V1. Build: agrees (one difference: the QPY bytes)

| record | part A | part B | check A / B |
|---|---|---|---|
| marrakesh | 76 circuits, 46.8 s | 100 circuits, 60.6 s | PASS / PASS |
| fez | 76, 46.8 | 100, 60.6 | PASS / PASS |
| kingston | 76, 46.8 | 100, 60.6 | PASS / PASS |

`circuits_sha256` (SHA-256 of the QPY bytes) and the psf-os gate hash (`psf_os.gatehash.qpy_hash`):

| build | circuits_sha256 | gate hash |
|---|---|---|
| marrakesh A | `febee21af6583ea4…` | `0d61c81111d85f1a…` |
| marrakesh B | `6836cf2705c68039…` | `31bc87ad3692dcf3…` |
| fez A | `2dfe36c43a938e46…` | `56c074f3e5b640f5…` |
| fez B | `77d84ad7313b981f…` | `ddb3b0ede8b81caa…` |
| kingston A / B | the same as marrakesh A / B | the same as marrakesh A / B |

- The workplace's marrakesh A starts `8d00aee4e3b5e0b3…`; here it is `febee21a…`.
  - Rebuilding here gives the same bytes again.
  - The dry runs under noises a to d agree with the workplace's outputs character for character (V3). So the
    circuits are the same and only the QPY encoding differs.
  - QPY's bytes change with the qiskit version (psf-os gatehash docstring). This file's header is QPY format 17
    written by qiskit 2.5.2. The workplace's qiskit version is not in the bundle.
  - To compare without the version, run `python -c "from psf_os.gatehash import qpy_hash; print(qpy_hash('OUT/job/circuits.qpy'))"`
    at the workplace and compare it with the gate hashes above.
  - Note: the gate hash writes the parameters of an `if_else` (its blocks) as `str()` of the block circuit, a text
    drawing. For circuits with conditionals it may therefore also change with the qiskit version.
- Kingston's builds equal marrakesh's byte for byte (the same placement there); fez's differ.

## V2. Ceiling and bit order, by other methods: agree

**Ceiling.** The off arm keeps the conditional-X reset and the target is an eigenstate, so the n rounds are
independent: P(bit m = 1 | j) = sin^2(pi j 2^m / 2^n). C(n) = 2^-n sum_k max_j P(k | j). Two methods:
- (1) the product formula;
- (2) the deferred-measurement circuit (one fresh ancilla per round), built from qiskit gates, its statevector.

| n | workplace (README, to 3 decimals) | (1) analytic | (2) statevector |
|---|---|---|---|
| 2 | 0.750 | 0.750 (exactly 3/4) | 0.750 |
| 3 | 0.588 | 0.588 | 0.588 |
| 4 | 0.471 | 0.471 | 0.471 |

The two methods' distributions differ by at most 1.3e-15.

**Bit order on the compiled device circuits** (`circuits.qpy`, all six builds). The expected readout is taken from
the algorithms, not from the tool's success maps:
- textbook: the integer j, clbit k = bit k of j;
- IPE: clbit m = phi_{m+1} = bit (n-1-m) of j.

Results:
- Textbook ff and replicate arms: the statevector of each circuit without its final reads gives P(read = j) = 1
  (within 1e-9) for every j, n = 2, 3, 4, on all three records.
- IPE ff: noiseless Aer, 2000 shots, every shot reads the expected bits.
- Every floor reads all zero.
- IPE off arms: within total variation 0.026 of the product formula (2000 shots).

So 72 (A) and 96 (B) arms per record are as expected.

## V3. Independent score against the tool's dry runs: agree

Commands as in the instruction: marrakesh, `--dry-clifford-sentinel`, `dry OUT noise/illus_?.json`, seed 20261119.

| noise | the tool's score on these runs vs `dry/dry_?.txt` | VS score vs `dry/dry_?.txt` (13 fields x 3 n) |
|---|---|---|
| a | identical | all agree but one: n 2 margin +0.2322 / +0.2323 (see below) |
| b | identical | all agree |
| c | identical | all agree |
| d | identical | all agree |
| none | see below | all agree, with the runs made by `psf_os.feedforward.run_local` |

- **The noise a margin.** IPE n = 2 is 7858 / 8000, so the margin is exactly 0.23225, on the rounding boundary.
  The tool's C(2) from the branch simulation is 0.7499999999999987; here it is exactly 0.75. Only the fourth
  decimal of the printed margin differs. No verdict changes.
- **`dry_0.txt` (no noise).** It is not the output of `dry` with an empty noise file. That run gives the same IPE
  and textbook numbers and words, but other off-arm samples: the off arm as read differs from the file in the third
  decimal for each n, both within sampling of the exact values 0.75 / 0.5 / 0.325; `vs_out/vs_score_0.json` is the VS score of the `run_local` reproduction.
  `dry_0.txt` is reproduced character for character by `psf_os.feedforward.run_local(OUT, seed=20261119)`.
  The README's table does not say which command made the "none" row.
- **Verdicts reached** (VS score): BEYOND THE CEILING under none, a, b and c. Per shot: IPE RIGHT MORE OFTEN under
  a and b, TEXTBOOK RIGHT MORE OFTEN under c, and NOT SEPARATED with no noise. Under d: NOT BEYOND x3, TEXTBOOK RIGHT MORE OFTEN x3.

## V4. Mutations: check stops every damage that changes a result

| damage | marrakesh A (n 2, 3) | marrakesh B (n 4) |
|---|---|---|
| textbook ff: clbits of bits 0 and 1 swapped (every j) | FAIL on 6 of 12 | FAIL on 8 of 16 |
| IPE ff: sign of every rz in the conditional blocks reversed (every j) | FAIL on 8 of 12 | FAIL on 14 of 16 |
| one X left before a read in a floor arm (ipe?_3, tqpe?_3) | FAIL on 2 of 2 | FAIL on 2 of 2 |

- Check exits 1 every time, and no undamaged arm fails.
- The arms that do not fail are exactly the ones whose noiseless output the damage cannot change:
  - swap: j whose bits 0 and 1 agree (n 2: j = 0, 3; n 3: 0, 3, 4, 7; n 4: 0, 3, 4, 7, 8, 11, 12, 15);
  - sign: j whose lower bits are all 0, so no feedback ever fires (n 2: 0, 2; n 3: 0, 4; n 4: 0, 8).
- No noiseless check can see these. Every j is in the job, so each kind of damage is caught by some arm of the job.

## Points for the tool (not changed here; for the workplace Claude and the owner)

1. Record which command made the "none" row of the dry-run table (`run_local`, not `dry`). Otherwise a rerun with
   `dry` gives other off-arm numbers.
2. Record the qiskit version beside `circuits_sha256` in the README, or quote the gate hash.
   `circuits_sha256` cannot be compared between machines with different qiskit versions.
3. Check's success maps come from the tool's own `items()`. A bit-order error made the same way in the builder and
   in the map would pass check. V2 above confirms the order from the algorithms, so there is no such error now.
4. Harmless: the tool's C(n) sits about 1e-15 below the exact value (the branch simulation). It changes only a
   printed fourth decimal at an exact tie.

Time: `TZ=Europe/Zurich date` printed GMT on this machine (no zone data in Git Bash). Times here are the machine
clock minus 8 h (CET).
