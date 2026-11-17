# Declared: single against packed (ten independent items in one circuit), night of 2026-11-17 (fourth round)

Home Claude, 2026-11-17 (owner about 23:00 JST: verdict words "KEEPS LESS / KEEPS MORE / SAME WITHIN ERROR", the overall
verdict read from the mean, the single job first; earlier "書いて": each item on the same physical qubits in both
jobs). Made from `prereg/drafts-2026-11-17/packing_DRAFT.md` (home VS). Declared with the commit that carries this
file, pushed before the device record of the run is fetched. Common rules as in `prereg/ff_night_2026-11-17.md`
(device by the standing rule, the first qualifying in the order ibm_marrakesh, ibm_fez, ibm_kingston; placement by the
coupling map and failed marks only; no mitigation, DD and twirling off; 4000 shots; every shot counted). Tools as of
this commit: `gpu/packing_night.py` with psf-os feedforward-2026-11-16 at 0f57c76 (single builds unchanged from
301ac01: tonight's twelve recorded verdicts reproduce SAME with it).

## Question

Does running independent items side by side in one circuit (packed) change what each item keeps, against running each
item in its own circuit (single), on the same device, the same physical qubits, the same night?

## What is run (`python gpu/packing_night.py build DEVDIR OUT`)

- Items: rd1..rd5 (the third design, T2 of 2026-11-17) and ea1..ea5 (the early chain, T4; its off arm is the third
  design's, so the packed off circuit holds the same off circuit twice per L, on different qubits), theta 1.1, m = 2,
  read flipped and relabelled as declared there.
- Packed job: one rule-C chain, the ten items on consecutive sites with one site skipped after each item and more while
  a coupler would join two items (psf-os `build_bundle`); one ff, one off and one floor circuit holding all ten items;
  one ring sentinel. 7 circuits, 10.8 s by the model.
- Single job: each item's ff, off and floor circuits on the physical qubits the packed job gives it (psf-os
  `build(..., chains=...)`); one ring sentinel; as many items per job as fit in 60 s (on the 2026-11-17 records: one
  job, 34 circuits, 40.9 s).
- Submitted back to back on the same device, the single job first.

## Checks before submission (`check OUT`; a FAIL means nothing is submitted)

1. No instruction or barrier of a packed arm (blocks included) spans two items.
2. Per item and arm (ff, off), the packed circuit restricted to the item has the same instructions on every qubit and
   bit as the single job's circuit, and the same exact distribution (total variation below 1e-12).
3. Ledger (latency 0 and 1 us, ASAP and JIT): per item, the start of its last measurement and its wait are the same
   packed as single.
4. The feed-forward checks of every arm (acceptance, conditionals kept in ff, none in off, no sx / x in floor).
5. Per item, the same physical qubits in both jobs.
Try-build on the 2026-11-17 fez and marrakesh records: PASS; noiseless end to end mean d +0.0002 (2 SE 0.0062).

## What is measured and the verdict (`score OUT`)

Per item i: s_i = ff(single), p_i = ff(packed) (P(last output 1), relabelled), v_i the noiseless value
(`notes/compound_2026-11-17/ideal.json`); d_i = |s_i - v_i| - |p_i - v_i| (positive: packed kept more), 2 SE from the
two binomial errors. Over the ten items: the mean of d_i, 2 SE from the per-item errors.

- **Verdict, on the mean:** PACKING KEEPS LESS when mean <= -2 SE; PACKING KEEPS MORE when mean >= 2 SE; otherwise SAME
  WITHIN ERROR.
- Beside, never judged: the same three words per item (PACKED KEEPS LESS / PACKED KEEPS MORE / SAME WITHIN ERROR; with
  ten items, one of them beyond 2 SE by chance is expected about one time in five); the floor of each item in both
  jobs; each job's sentinel; the charged seconds of each job.

## Predictions (written before the data)

1. PK-1 The verdict is not PACKING KEEPS LESS.
2. PK-2 The charged seconds of the packed job are below one third of the single job's.

Basis: the checks (no item waits for another in the ledger; the same circuits per item); the time model (10.8 against
40.9 s). Each prediction holds or fails as a whole; a failed one is reported as failed.

## Known limits (stated before the data)

- One skipped site is a geometric rule, not a crosstalk measurement; items may still disturb each other through the
  lattice or shared readout lines.
- How the device's control system schedules independent conditionals in one circuit (whether a decision on one item
  holds the others) is not in our records; the ledger assumes it does not. This is part of what d measures.
- The two jobs run minutes apart; drift between them is part of d_i.
