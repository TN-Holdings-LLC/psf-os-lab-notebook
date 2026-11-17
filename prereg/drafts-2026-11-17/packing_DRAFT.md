# DRAFT (not declared): single against packed on the same night (home VS Claude, 2026-11-17 evening)

**Numbers, thresholds and verdict words marked [OWNER] are the owner's to set.** Everything else follows the common
rules of `prereg/ff_night_2026-11-17.md` (no mitigation, DD and twirling off, 4000 shots per circuit, the declared
device order, the device record fetched after this file is pushed, placement by the coupling map and failed marks
only).

## Question

Does running independent items side by side in one circuit (packing) change what each item keeps, against running
each item in its own circuit (single), on the same device on the same night?

## Items and arms

- Items: the third design rd1..rd5 (T2 of 2026-11-17, `notes/compound_2026-11-17/compound.items`) and the early chain
  ea1..ea5 (T4, `notes/early_2026-11-17/early.items`, off arm the third design's), theta 1.1, m = 2, read flipped and
  relabelled as declared there.
- Single job(s) (owner, 2026-11-17 evening: the same physical qubits as packed, so that the effect of packing is not
  mixed with the quality of the qubits): each item built as T2 and T4 build it (`gpu/compound_night.py`,
  `gpu/early_night.py`: per item ff, off and floor circuits) but placed on the qubits the packed job gives it
  (psf-os `feedforward.build(..., chains=...)`, a given chain checked as rule C's are: a joined line of usable qubits
  on working couplers); one ring sentinel per job; as many items per job as fit in 60 s by the time model. On the
  2026-11-17 fez and marrakesh records: one job, 34 circuits, about 41 s.
- Packed job: one rule-C chain of N sites; the ten items laid on it in the order above, each on consecutive sites,
  one site skipped after each item and further sites skipped until no coupler joins the next item to an earlier one
  (psf-os `feedforward.build_bundle`; on the 2026-11-17 fez record N = 69, the ten items on physical qubits 0-124;
  on the marrakesh record N = 69, qubits 0-92).
  One ff, one off and one floor circuit hold all ten items; one ring sentinel. 7 circuits in 1 job, about 11 s.
- Both jobs submitted back to back on the same device, the single job(s) first [OWNER: order, or alternating].
- Tool: `gpu/packing_night.py` (build: the packed job, then the single job(s) on the packed qubits; check: the checks
  below; score: the numbers of "What is measured", no verdict line until the owner sets the words).

## Checks before submission (each must pass; otherwise nothing is submitted)

1. Independence: no instruction (blocks included) acts on qubits of two items or reads or writes bits of another item.
2. Per item, the packed compiled circuit restricted to the item has the same instructions on every qubit and bit as
   the item's circuit in the single job, and the same exact distribution (total variation below 1e-12).
3. Ledger: per item, the start of its last measurement and its wait are the same packed as alone (ASAP as built and
   JIT); no barrier spans two items.
4. The usual feed-forward checks of each item (acceptance, conditionals kept, floor and off arms as declared).
5. Per item, the same physical qubits in the single and the packed job.

## What is measured

Per item i: s_i = ff_i(single) and p_i = ff_i(packed), each read as declared (P(last output 1)), with the noiseless
value v_i (`notes/compound_2026-11-17/ideal.json`, the same for rd and ea at the same L).

- Per item: d_i = |s_i - v_i| - |p_i - v_i| (positive: packed kept more), with 2 SE from the two binomial errors.
- Over the ten items: the mean of d_i and its 2 SE [OWNER: or a paired sign count].

## Verdicts [OWNER: words and thresholds]

- Per item: PACKED LOSES if d_i <= -2 SE [OWNER: or a margin m]; PACKED KEEPS MORE if d_i >= 2 SE; otherwise SAME
  WITHIN ERROR.
- Overall: PACKING IS FREE if no item reads PACKED LOSES and the mean of d_i is within 2 SE of 0 [OWNER].
- Beside, never judged: the floor of each item packed and single; the sentinel of each job; the device seconds
  charged for each job.

## Predictions [OWNER]

- PK-1: no item reads PACKED LOSES.
- PK-2: the charged seconds of the packed job are below one third of the single jobs'.

## Known limits (stated before the data)

- One skipped site is a geometric rule, not a crosstalk measurement; items may still disturb each other through the
  lattice or through shared readout lines.
- A packed circuit lasts as long as its longest item; the shorter items are measured at their own end (checked by the
  ledger under ASAP), but how the device's control system schedules independent conditionals in one circuit (for
  example whether a decision on one item holds others) is not in our records.
- The packed and single circuits run at different times on the same night; drift between them is part of d_i.
