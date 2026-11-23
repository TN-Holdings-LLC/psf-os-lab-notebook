# Ohm circuits: idle time while probably |1> (home VS, 2026-11-23; desk, no device)

Home's instruction "オームの待ちの机上計算" (2026-11-23). The Ohm line was closed on 2026-11-13
(`notes/ohm_conclusion_2026-11-13.md`). psf-os's new rule (a probably-|1> qubit is held in |0> while it waits) acts on
mid-circuit waits only, and the Ohm circuits measure only at the end. This note counts, on the desk, how much time a
qubit of the sent Ohm circuits spends idle while probably |1>, whether parking it would leave the answer unchanged, and
an upper bound on what that could do for M. Nothing under `results/` is written. psf-os is not changed (0.3.3, a45c54a,
used only to read the fake backends' durations). The parking is a trial inside this folder.

**Lengths of time are the fake backends' values (qiskit-ibm-runtime 0.49.0: FakeFez for fez, FakeKingston for
kingston; durations only), not the devices' records.** The Ohm nights' device records hold no durations. No error
number is read.

| file | what it holds |
|---|---|
| `ohm_idle.py`, `idle.json` | every sent circuit (336: 2 devices x 3 arms x 2 cycle counts x 28 strings), ASAP and ALAP schedules, idle spans, noise-free P(\|1>) per span (MPS, bond 512, cutoff 1e-8) |
| `idle_check_chi256.json` | the same with bond 256, cutoff 1e-6 (check) |
| `summarize.py`, `summary.json`, `summary.txt` | (a), (b), (c) per device, arm and cycle count |
| `park_try.py`, `park_alap.json`, `park_alap.txt` | the X, delay, X trial and its checks |
| `shrink_bound.py`, `bound.json`, `bound.txt` | the upper bound (assumed model, a rough guide) |
| `window_M.py`, `window_M.json`, `window_M.txt` | beside: M summed over a window next to the wall (section 4) |

## How

- The circuits are the sent ones (`runs/p2d_<tag>.qpy.gz`), on the 40 chain qubits. Every CZ is between chain
  neighbours (checked), so a matrix product state along the chain holds the state exactly up to truncation.
- The device's own schedule is not recorded, so two are given:
  - ASAP: everything as early as possible, and each qubit measured when it is done;
  - ALAP: everything as late as possible, and all measured at the end.
  RZ is virtual (no duration) and does not break an idle span.
- An idle span is time with no x, sx or cz on that qubit, from 0 to the start of its measurement. Gates on other
  qubits do not change a qubit's reduced state, so P(|1>) is constant over the span.
- "Probably |1>" means P(|1>) > 1/2 + 1e-6. Many spans sit at exactly 1/2 (fSim(pi/4)).
- Accuracy: the final per-qubit <Z> of every circuit is compared with the sealed exact answers (`answers/`). The worst
  difference is 9.4e-8. Against the bond-256 run, (b) and (c) move by at most 0.2% of the idle time.

## 1. Idle time (`summary.txt`; ASAP / ALAP)

(a) idle share of all qubit-time. (b) share of the idle time with P(|1>) > 1/2. (c) idle time weighted by P(|1>), per
circuit, and as a share of all qubit-time. Lengths are the fake backends' values.

| device | arm | cycles | circuit length | (a) idle | (b) P > 1/2 | (c) per circuit | (c) / qubit-time |
|---|---|---|---|---|---|---|---|
| fez | A0 | 3 | 1.60 µs | 0.034 / 0.101 | 0 / 0 | 1.03 / 1.10 µs | 0.017 / 0.017 |
| fez | A0 | 6 | 3.16 µs | 0.045 / 0.099 | 0 / 0 | 2.71 / 2.90 µs | 0.023 / 0.023 |
| fez | A1 | 3 | 2.52 µs | 0.104 / 0.158 | 0.169 / 0.140 | 4.95 / 5.50 µs | 0.052 / 0.055 |
| fez | A1 | 6 | 5.00 µs | 0.114 / 0.153 | 0.214 / 0.187 | 10.9 / 11.2 µs | 0.057 / 0.056 |
| fez | A2 | 3 | 2.52 µs | 0.104 / 0.158 | 0.189 / 0.150 | 4.94 / 5.48 µs | 0.052 / 0.054 |
| fez | A2 | 6 | 5.00 µs | 0.114 / 0.153 | 0.217 / 0.189 | 10.9 / 11.2 µs | 0.057 / 0.056 |
| kingston | A0 | 3 | 1.68 µs | 0.057 / 0.158 | 0 / 0 | 1.70 / 1.38 µs | 0.028 / 0.021 |
| kingston | A0 | 6 | 3.31 µs | 0.077 / 0.158 | 0 / 0 | 4.66 / 4.22 µs | 0.039 / 0.032 |
| kingston | A1 | 3 | 2.69 µs | 0.139 / 0.229 | 0.166 / 0.114 | 6.72 / 7.05 µs | 0.070 / 0.066 |
| kingston | A1 | 6 | 5.33 µs | 0.152 / 0.223 | 0.209 / 0.165 | 14.9 / 15.4 µs | 0.076 / 0.072 |
| kingston | A2 | 3 | 2.69 µs | 0.139 / 0.229 | 0.185 / 0.123 | 6.71 / 7.02 µs | 0.070 / 0.065 |
| kingston | A2 | 6 | 5.33 µs | 0.152 / 0.223 | 0.212 / 0.166 | 14.9 / 15.4 µs | 0.076 / 0.072 |

- Across all cells, idle time is 3-23% of qubit-time, and its |1>-weighted part is at most 7.6%.
- In A0 no idle span is above 1/2.
- What parking could change, the sum of (2P - 1) x length over the spans above 1/2, is at most 1.6% of qubit-time
  (`park_gain_share_of_qubit_time`).

## 2. Parking with X, delay, X (`park_try.py`, ALAP)

- The trial parks every span above 1/2 that has room for the pair (length at least 2 x + 2 dt). The span becomes X,
  delay, X, placed before the instruction that ends it.
- ASAP leaves no span with room (x is 6 dt on FakeFez and 8 dt on FakeKingston, and the spans are shorter). So the
  trial uses ALAP.
- Parked spans per circuit:
  - fez: 5.1 at 3 cycles and 17.2-17.7 at 6 (at most 38);
  - kingston: 3.3-3.4 at 3 cycles and 15.7 at 6 (at most 36);
  - A0: none.
- One-qubit gates added: 2 per span, 7-35 per circuit, against 1063 / 2116 in the sent circuits.
- The parked spans hold 29-38% of the probably-|1> gain. The rest are too short.
- Noise-free checks, all 336 circuits:
  - the parked circuit's state overlaps the sent one's at 1.000000000000;
  - the final <Z> changes by at most 1.4e-14;
  - the ALAP length is unchanged.
- qiskit transpile with the fake target (levels 1-3), on the circuit with the most parked spans in each cell:
  - the CZ count is the same as the sent circuit's at every level, with and without a fence;
  - every delay stays.
- Without a fence, the transpiler merges the X into the neighbouring one-qubit gates. The qubit is still parked: P(|1>)
  during each delay is at most 0.34, read from the transpiled circuit.
- With a fence (a one-qubit barrier on each side), the X stay as X.
- So in this trial a fence is not needed for the answer or the CZ count. It is needed only to keep the X as X.

## 3. Upper bound (`shrink_bound.py`; assumed model, a rough guide, not measured)

- Assumption: each circuit's values split as z = r e + rest, as in `notes/noise_structure_2026-11-13`.
- Assumption: all of the uniform shrink 1 - r grows with qubit-time, so idle time in |1> carries at most the share
  phi = (c) / qubit-time. Parking removes at most that share: z' = z + phi (1 - r) e.
- The rest is left unchanged. Nothing is fitted to the device.
- This overstates what parking can do, because:
  - readout shrink does not grow with idle time;
  - X, delay, X only turns P into 1 - P;
  - only 29-38% of the gain has room for the pair.

| device | arm | cycles | M MSE / mean square, recorded | at phi = (c) | phi = (c) | phi needed for the line (0.5) | all uniform shrink gone |
|---|---|---|---|---|---|---|---|
| fez | A0 | 3 | 2.35 | 2.29 | 0.017 | 0.69 | 0.13 |
| fez | A0 | 6 | 1.57 | 1.52 | 0.023 | 0.58 | 0.11 |
| fez | A1 | 3 | 4.16 | 3.79 | 0.055 | 0.79 | 0.15 |
| fez | A1 | 6 | 4.13 | 3.75 | 0.057 | 0.80 | 0.16 |
| fez | A2 | 3 | 5.79 | 5.29 | 0.054 | 0.89 | 0.28 |
| fez | A2 | 6 | 7.21 | 6.56 | 0.057 | 0.93 | 0.32 |
| kingston | A0 | 3 | 0.68 | 0.65 | 0.028 | 0.17 | 0.02 |
| kingston | A0 | 6 | 0.375 (reads) | 0.35 | 0.039 | 0 | 0.005 |
| kingston | A1 | 3 | 1.47 | 1.29 | 0.070 | 0.47 | 0.05 |
| kingston | A1 | 6 | 1.38 | 1.18 | 0.076 | 0.42 | 0.03 |
| kingston | A2 | 3 | 1.80 | 1.57 | 0.070 | 0.52 | 0.06 |
| kingston | A2 | 6 | 2.27 | 1.96 | 0.076 | 0.58 | 0.06 |

- At most phi = 0.076 of the shrink could come from idle |1> time. Reaching the line needs 0.17-0.93 in the 11 cells
  that do not read.
- At the bound, M's error ratio falls by 3-14%. With the shares the trial actually parks (phi 0.004-0.005,
  `bound.json`), it falls by about 1%.
- In these records the uniform shrink carries 93-99% of M's squared error (the 60-86% of the 11-13 conclusion is the
  per-qubit Z error). If all of it were gone, every cell would read. Idle time is not where it comes from.

**Conclusion: M does not reach the line (届かない).** Even under the generous assumption, the share is 5 to 40 times
smaller than needed in every cell that did not read.

Runs: `ohm_idle.py idle.json --chi 512 --cutoff 1e-8` and `--chi 256 --cutoff 1e-6` (check); `park_try.py
park_alap.json --schedule alap`; `summarize.py idle.json summary.json idle_check_chi256.json`; `shrink_bound.py
summary.json park_alap.json bound.json`. Each needs `PYTHONPATH=<psf-os 0.3.3>:.` and runs from the notebook root.

## 4. Beside: M over a window next to the wall (`window_M.py`, `window_M.json`, `window_M.txt`; never judged)

Owner's follow-up the same day ("縮みそのものを扱う"). This changes the measure, not the records. Raw counts are used,
no shot is discarded, nothing is corrected, and the declared verdicts stay those of `scores.json`.

What M_w is:
- M_w sums the right half's (1 - z) / 2 over the w sites next to the wall only. w = 20 is the declared M; it matches
  `scores.json` exactly.
- M_w is **a different quantity**: the window also exchanges 1s through its far edge, by the right half's own dynamics.
  Its exact value therefore comes from the sealed per-qubit answers.
- The wall's light cone after t cycles reaches 2t - 1 sites (5 at 3 cycles, 11 at 6). The width follows from the
  circuit's structure; it was not tuned on the data.
- Even so, the idea came after the records were seen. Any verdict on it needs a new declaration before a new run.

| device | arm | cycles | ratio, light-cone window | ratio, declared M | exact M_w against exact M (corr.) | W window: device / exact | W half: device / exact |
|---|---|---|---|---|---|---|---|
| fez | A0 | 3 | **0.014** | 2.35 | 0.92 | 0.84 / 0.76 | 1.94 / 0.71 |
| fez | A0 | 6 | **0.259** | 1.57 | 0.92 | 2.36 / 1.38 | 3.28 / 1.39 |
| fez | A1 | 3 | **0.034** | 4.16 | 0.94 | 0.78 / 0.68 | 1.95 / 0.60 |
| fez | A1 | 6 | 0.679 | 4.13 | 0.92 | 2.13 / 0.99 | 3.01 / 0.95 |
| fez | A2 | 3 | **0.061** | 5.79 | 0.96 | 0.70 / 0.57 | 1.93 / 0.52 |
| fez | A2 | 6 | 1.444 | 7.21 | 0.93 | 1.92 / 0.74 | 2.77 / 0.71 |
| kingston | A0 | 3 | **0.015** | 0.68 | 0.92 | 0.85 / 0.76 | 1.38 / 0.71 |
| kingston | A0 | 6 | **0.027** | 0.375 | 0.92 | 1.69 / 1.38 | 2.29 / 1.39 |
| kingston | A1 | 3 | **0.034** | 1.47 | 0.94 | 0.80 / 0.68 | 1.39 / 0.60 |
| kingston | A1 | 6 | **0.125** | 1.38 | 0.92 | 1.46 / 0.99 | 2.12 / 0.95 |
| kingston | A2 | 3 | **0.049** | 1.80 | 0.96 | 0.69 / 0.57 | 1.30 / 0.52 |
| kingston | A2 | 6 | **0.269** | 2.27 | 0.93 | 1.23 / 0.74 | 1.85 / 0.71 |

Bold: at or below the line (0.5). The ratio is the M MSE divided by the mean square of the exact value.

- On the light-cone window, 10 of the 12 cells read. The two that do not are fez A1 and A2 at 6 cycles.
- The window keeps the transport:
  - its exact M_w moves with the exact declared M (correlation 0.92-0.96);
  - its exact W is about the size of the half's (0.57-1.38 against 0.52-1.39).
- At 3 cycles the device's W on the window is close to the exact W (0.70-0.85 against 0.57-0.76). On the half it is
  1.3-1.9.
- Limit: the exponent log2(W(6) / W(3)) over the windows does not read.
  - fez: 1.50 / 1.45 / 1.47 (A0 / A1 / A2); the order A1 > A2 is not kept.
  - kingston: 0.99 / 0.88 / 0.83; the order is kept.
  - exact: 0.86 / 0.55 / 0.39.
  - At 6 cycles the window is wider and the circuit has more layers, so the device's W grows more than the exact W.
- Narrower windows read more easily; w = 1 is a single qubit's Z, which already read. The light-cone width is the
  narrowest window that holds all of the wall's influence.
- Guess (not measured): this is where the shrink lever is. A declared measure on the light-cone window would read M at
  3 cycles on both devices, and at 6 cycles on a kingston-like day. The transport exponent would still not read at
  these sizes.

## Computers and time

The home PC's CPU (WSL, 10 processes) did all of it. The POD and the RTX 4070 were not used.

| step | wall time |
|---|---|
| `ohm_idle.py`, bond 512 | 334 s |
| `ohm_idle.py`, bond 256 (check) | 119 s |
| `park_try.py` | 346 s |
| `shrink_bound.py` | seconds |
