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

## Packing T2 and T4 into one circuit per arm (`packing.py`; home VS Claude, 2026-11-17 evening)

Built on the 2026-11-17 fez record (`results/ff-night-2026-11-17/fetch_in/ibm_fez/dev`) with psf-os 301ac01
unchanged. Output: `packing.txt`, `packing.json`.

- Placement (coupling map and failed marks only): one rule-C chain of N = 69 sites (start [1, 0, 0]); rd1..rd5 and
  ea1..ea5 laid on it in order, each on consecutive sites, one site skipped after each item (no extra skip was needed:
  no coupler joins two items). Physical qubits: rd1 0-1, rd2 3-6, rd3 8-11 18 31, rd4 29..22, rd5 36 41-49, ea1 51-52,
  ea2 54 55 59 75, ea3 73 79 93-95 99, ea4 114..107, ea5 105..101 116 121-124.
- Packed arms, compiled as the entrance compiles (map-free target, routing none): acceptance PASS for ff, off and
  floor; CZ ff 140, off 110, floor 140.
- Independence: 0 instructions (blocks included) touch the qubits or bits of two items; 0 barriers span two items.
- Per item against the item compiled alone: the same instructions on every qubit and bit (ff and off; the global
  listing order differs only where the packed chain runs downwards in physical labels), exact distributions equal
  (total variation 0 to 5.8e-16, branching simulation).
- Ledger (FakeMarrakesh lengths, latency 0 and 1 us, ASAP as built and JIT): every item's wait and the start of its
  last measurement are the same packed as alone (e.g. JIT, latency 0: rd5 46.51 q.us, ea5 15.50 q.us; last
  measurement under ASAP at 32.08 and 28.46 us); the packed circuit lasts 34.7 us (40.0 us at latency 1 us), the
  longest item's length. So no item waits for another.
- Time model: T2 + T4 as run, 38 circuits in 2 jobs, 48.4 s; packed, 3 arms + 4 sentinel circuits in 1 job, 10.8 s.

### The entrance (psf-os feedforward, 301ac01)

- With one classical register per item (the natural form) `analyse` refuses: "one classical register holding every
  measured bit (got 10)".
- With the ten items' bits in one register (offsets), `analyse` accepts (69 qubits, 80 bits, 40 conditionals) and
  `build` accepts it as one item (7 circuits, 10.8 s; placed on the same rule-C chain). The circuit side is therefore
  already possible: the packed circuit is a 1D chain with idle gap sites.
- What is missing is the item side: one item has one spec (one success rule or one rus spec: one out_bit, its tries,
  one exact value) and gives one card, so the ten items cannot be scored apart, and the off arm and the floor are
  built for the whole.

### Bundled items: a short design (not implemented; psf-os unchanged)

- `build(dev, items, out, bundle=True)` (or an item of kind "bundle": `(tag, [(sub_tag, qc, spec), ...])`):
  1. each sub-item is analysed and lowered as now (its own spec, its own off arm);
  2. placement: one rule-C chain of N sites and the segment rule above (one site skipped, more while a coupler joins
     two items), N the smallest that fits; refused if none;
  3. the packed ff / off circuits: each sub-item on its segment, its bits at an offset in one register (the IBM form
     the entrance already checks); floor_of(ff) as now;
  4. new acceptance: the independence check (no instruction across two sub-items, no barrier across two), and per
     sub-item the per-wire equality with the sub-item compiled alone;
  5. records: one run per arm for the whole bundle, with a map {sub_tag: (segment, bit offset, bit count, spec)}; the
     sub-item's counts are the marginal over its bits;
  6. cards: `cards(out)` returns one card per sub-item, computed from the marginal counts exactly as for a single item
     (ff, off, post, floor all-zero on its own qubits, the job's sentinel), so every scorer (compound_night,
     early_night) runs unchanged on the sub-item cards.
- Tests to add with it: a bundle of two copies of one item gives two cards equal in distribution to the item alone
  (noiseless local run); a bundle with an instruction across two segments is refused; the time model counts 3 + 4
  circuits for any number of sub-items.

## Delays through the entrance (home VS Claude, 2026-11-17 evening; psf-os feedforward-2026-11-16 at 871d9e6)

- psf-os 871d9e6 (on 301ac01): the feed-forward entrance accepts a top-level one-qubit `delay` (not counted as a gate,
  nor as an operation after the last measurement), keeps it through lowering, compilation (level 1) and the off and
  floor arms, and refuses a delay inside a conditional block (its timing would depend on the branch), in both forms.
  Three tests added; the whole suite with TOQB_DIR set: 300 passed, 1 skipped. Bundle
  `psf-os_301ac01..871d9e6.bundle`.
- `pin_check.py` (outputs `pin_check_out.txt`, `pin_check.json`; `pinned_check_out.txt` keeps only the last 12 lines of
  the noiseless check): tonight's T2 try-built on the 2026-11-17 fez record, each item's ff and off arms pinned by
  `pin_delay.py` (latency 0), mapped back to logical qubits and built again through the changed entrance (the pinned
  off arm as the explicit off arm): PASS for rd1..rd5. Delays kept (2 / 8 / 14 / 20 / 26 per arm, also in the floor),
  the same instructions per qubit and bit as the pinned circuit (delays aside), CZ unchanged (2 / 12 / 22 / 32 / 42),
  exact distributions equal to the unpinned ones (difference 0.0); waits, original JIT against rebuilt ASAP: 5.17 /
  15.50 / 25.84 / 36.18 / 46.51 against 5.17 / 15.52 / 25.86 / 36.19 / 46.53 q.us; the rebuilt job 19 circuits,
  24.2 s, as the original; `compound_night.py check` on it PASS.
- IBM's public documents (read 2026-11-17): **not known** whether a top-level delay is kept exactly around mid-circuit
  measurements and if_else. Found: the runtime scheduling notes for dynamic circuits (fast-path one-qubit blocks
  conditioned on the same qubit's last measurement; parallel blocks padded to the longest; the user adds delays to
  align; a barrier between measurement and branch disables the fast path)
  https://quantum.cloud.ibm.com/docs/en/api/qiskit-ibm-runtime/0.29/transpiler-passes-scheduling ; the current page
  warns not to mix IBM's dynamic-circuit scheduling with Qiskit's scheduling_method, and says nothing about delays
  already in the circuit https://quantum.cloud.ibm.com/docs/en/api/qiskit-ibm-runtime/transpiler-passes-scheduling ;
  the stretch guide (durations resolved at compile time after scheduling; DD on idle qubits during a conditional
  block; stretch still experimental) https://quantum.cloud.ibm.com/docs/en/guides/stretch ; the feed-forward guide
  refers to "Execute dynamic circuits" for limits
  https://quantum.cloud.ibm.com/docs/en/guides/classical-feedforward-and-control-flow (that page returned 404 here).
  A device use of pinned delays still needs a declaration and, ideally, a test that the delays are honoured.
