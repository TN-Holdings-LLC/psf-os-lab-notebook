# Next steps taken over at home from the workplace VS (2026-11-17, owner 17:18 JST; desk only, not declared)

The owner asked home to take over the workplace VS's open tasks: the T2 next step (N2), fixing the least-wait schedule
with delays, and the estimate of device seconds saved by packing independent items into one circuit. Lengths are
FakeMarrakesh medians (illustrative); no device error number is used anywhere.

## N2: the early chain over L = 1 .. 7 (`gpu/early2_night.py`)

The workplace's early chain (`notes/early_2026-11-17/`) holds the least-wait schedule without pinning: its waits are
the same under an as-soon-as-possible executor and under JIT (ledger; confirmed here: ea1..ea5 ff arms, ASAP = JIT).
So the VS task "a chain with the least-wait schedule fixed, L = 1 .. 7" is met by the early chain itself, and N2 runs
it over L = 1 .. 7 with T4's verdicts (ceiling, overshoot guard, slope). Exact ideals for L = 1 .. 7 (third design,
exact branching; L = 1 .. 5 equal to `notes/compound_2026-11-17/ideal.json`): `ideal7.json`. The noiseless margin
c - e peaks near L = 6 (0.2474) and is 0.2444 at L = 7.

25 circuits, 30.9 s by the model. Try-build on the 2026-11-16 13:11 CET marrakesh record: check PASS (chains up to 14
qubits, CZ 14 and 13 conditionals at L = 7). Noiseless run end to end: BEYOND at every L, slope +0.024 (2 SE 0.003),
COMPOUNDS. Draft declaration: `prereg/drafts-2026-11-17/next_N2_DRAFT.md`.

## Fixing the JIT schedule with delays (`pin_delay.py`)

For each top-level instruction, a delay on each of its qubits holds it at its JIT start, so that an
as-soon-as-possible executor reproduces JIT (delays rounded up to multiples of 16 dt, an assumption). Recorded:
`pin_delay_latency0us.json` over the ff and off arms of tonight's T1, T2 and T4 builds.

| item | wait ASAP | wait JIT | pinned, recounted ASAP | delays |
|---|---|---|---|---|
| rd2 / rd3 / rd4 / rd5 (T2) | 25.84 / 56.85 / 98.19 / 149.87 | 15.50 / 25.84 / 36.18 / 46.51 | 15.52 / 25.86 / 36.19 / 46.53 | 8 / 14 / 20 / 26 |
| ea2 .. ea5 (T4) | 7.75 / 10.34 / 12.92 / 15.50 | the same | 7.80 / 10.44 / 13.09 / 15.74 | 4 .. 10 |
| coh1 / rd1 (T1) | 0.04 / 5.17 | 0.04 / 5.17 | 0.02 / 5.17 | 7 / 2 |

- Structure: with the delays removed, every pinned circuit has the same instructions in the same order on every qubit
  and clbit as the original (a delay is the identity noiselessly, so the noiseless distribution is the same).
- Recount: within 0.25 q.us of JIT everywhere (the rounding of the delays).
- Not usable on a device as it stands: psf-os's feed-forward entrance refuses `delay` (its accepted one-qubit set),
  and whether IBM's dynamic circuits honour top-level delays exactly around mid-circuit measurements and conditionals
  has not been checked here (unverified). A device use needs both and a declaration.
- For the third design the delays give what the workplace VS's barrier pinning could not give exactly (rd2..rd5).

## Packing independent items into one circuit (estimate)

The project's time model (`psf_os.job.qpu_seconds`: 0.036 s per circuit + 0.00027 s per shot + 3 s per job; the
charged seconds of 2026-11-16 were the model minus about 1 s) depends on the number of circuits, not on their width.
Packing every item of one arm side by side (rule-C chains with one free qubit between items) on tonight's builds:

| job | items | qubits incl. gaps | circuits now | s now | circuits packed | s packed |
|---|---|---|---|---|---|---|
| T1 | 2 | 6 | 10 | 14.2 | 7 | 10.8 |
| T2 | 5 | 34 | 19 | 24.2 | 7 | 10.8 |
| T3 | 14 | 51 | 46 | 54.3 | 7 | 10.8 |
| T4 | 5 | 34 | 19 | 24.2 | 7 | 10.8 |
| all four in one job | 26 | 128 | 94 | 116.9 | 7 | 10.8 |

(7 = ff, off, floor plus the job's 4 sentinel circuits.) About 2.7x less with packing per job, about 11x with
everything in one job (128 of 156 qubits, failed marks avoided by rule C; not placed here).

What packing changes, and why it needs its own declared test (single against packed on the same night):
- Each packed circuit lasts as long as its longest item; items that end early must be measured at their own end
  (JIT), or they wait and lose |1> (the control diagnostic of 2026-11-16).
- Neighbouring items can disturb each other (crosstalk); the one-qubit gap is a geometric rule, not a measurement.
- Many conditionals run at once; whether the controller serialises them is not known here.
- One sentinel then watches the whole device region, not each item.
