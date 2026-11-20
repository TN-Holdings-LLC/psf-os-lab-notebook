# DRAFT (not declared): where should a qubit wait? IPE sent three ways (weekend candidate C)

Workplace Claude, 2026-11-20, after the workplace VS's check of the weekend candidates: the footprint as sent differs
from the footprint as written. Compiled, IPE's target waits in a superposition, because the compiler merges its
return to |1> with the next round's preparation across the wait. Words, the reading table and predictions marked
[OWNER] are the owner's; the workplace built the tool, sized it and dry-ran it. Tool: `gpu/ipe_park_night.py`.
Notes: `notes/park_2026-11-20/`, `notes/footprint_2026-11-20/` (sent.txt). Needs psf-os after-2026-11-20
(`fence_waits`, `build(footprint=True)` as sent).

## Why

- 2026-11-16 / 11-17: holding the neuron's likely value as |0> (P1) recovered 0.11-0.22. That is the excited count
  at the wait.
- 2026-11-20: the wait footprint (carriers: waiting qubits not in a basis state) separates the repetition code's
  forms. As sent, IPE has one carrier at every wait (as written: none).
- Two ways to remove the carrier, with the same action and CZ:
  - fence the wait: the target waits in |1> (no carrier, excited);
  - fence and park: the target waits in |0> (X before the wait, X after; no carrier, not excited).
- This asks the device which of dephasing and decay costs more while a conditional waits, and whether "wait in
  |0>" is the rule to build into psf-os.

## Design (one device record; rule C placement as 2026-11-19; no mitigation; DD and twirling off; every shot counted)

IPE n = 4 (every phase 0-15, 1950 shots), three forms, the same off arm (the plain off arm; ceiling C(4) = 0.4706):

| form | the target during each wait (as sent) | carriers | excited | CZ | depth |
|---|---|---|---|---|---|
| pl (plain, as 2026-11-19) | superposition | 1 | 1/2 | 0-8 | 31-63 |
| fe (fence) | \|1> | 0 | 1 | 0-8 | 32-72 |
| pk (fence + park) | \|0> | 0 | 0 | 0-8 | 31-72 |

Every wait means every read and every run of phase-feedback conditionals (the workplace VS's その6). Fenced at the
reads only, the target still waited in a superposition at 6 of the 9 conditionals. The tool now fences and parks at
every wait by default [OWNER]; `--reads-only` builds the forms the VS checked in その6 (depth to 66). As sent, with
every read and conditional counted: pl carries 1 at every wait; fe and pk 0; excited (n = 4, phase 5) 3.5, 6.0, 0.0.

Two jobs (phases 0-7 and 8-15, every form in both), 76 circuits and 45.8 s by the model each. `check`: noiseless,
every ff arm success 1, every off arm at its exact value, floors zero: PASS on both jobs (the 2026-11-19 marrakesh
record). The footprint as sent is in every record.

## Verdicts [OWNER]

- Ceiling per form: BEYOND THE CEILING / NOT BEYOND (2026-11-19's words).
- Comparisons (n = 4, every phase pooled), d = p(x) - p(y), SE from the shots of both:
  - **park**: pk - pl;
  - **fence**: fe - pl;
  - beside: pk - fe.
  Words for each: KEEPS MORE (d >= 2 SE), SAME WITHIN ERROR, KEEPS LESS (d <= -2 SE).

## Reading table (fixed before the data) [OWNER]

| park (pk - pl) | fence (fe - pl) | reading |
|---|---|---|
| KEEPS MORE | KEEPS LESS | decay while waiting: \|1> loses, \|0> keeps |
| KEEPS MORE | KEEPS MORE | dephasing while waiting: any basis state keeps, \|0> at least as well |
| KEEPS MORE | SAME WITHIN ERROR | waiting in \|0> keeps more; \|1> neither more nor less than the superposition |
| SAME WITHIN ERROR | SAME WITHIN ERROR | where the target waits is not seen at this night's shot noise |
| any other pair (5) | | against the expectation: not read for the mechanism |

All 9 outcomes fall on exactly one row (3 + 1 + 5).

## Predictions [OWNER]

- PK-1 [OWNER: e.g. pk KEEPS MORE than pl]
- PK-2 [OWNER: e.g. fe KEEPS LESS (decay dominates), or no direction]

## Dry runs (illustrative noise, never fitted; each job its own seed 20261122 + 5,000,000 x job)

| noise | pl | fe | pk | park | fence | row |
|---|---|---|---|---|---|---|
| qpe a (CZ 1 %, damping 2 % per read) | 0.9449 | 0.9179 | 0.9579 | KEEPS MORE | KEEPS LESS | decay |
| qpe c (+ dephasing 12 % per conditional) | 0.7378 | 0.7909 | 0.8215 | KEEPS MORE | KEEPS MORE | dephasing |
| damping 6 % per read only | 0.9672 | 0.8776 | 1.0000 | KEEPS MORE | KEEPS LESS | decay |
| dephasing 5 % per conditional only | 0.8839 | 0.9280 | 0.9260 | KEEPS MORE | KEEPS MORE | dephasing |

The forms fence and park at every wait (the tool's default since the VS's その6; `notes/park_2026-11-20/dry_all_waits/`).
With the reads only (`dry/`) the damping rows are the same, and under dephasing fe and pk keep less (qpe c: 0.7562,
0.7854; cond only: 0.9094, 0.9076), on the same rows. The workplace VS's その6 grid (reads-only forms, 15 noises x 20
seeds) gave the same one-to-one map: gates only -> not seen, damping -> decay, dephasing -> dephasing. Each noise lands on the row of its mechanism (`notes/park_2026-11-20/dry/`).

## Known limits

- The extra X pair adds two one-qubit gates per wait (pk). Fe and pk add barriers (synchronisation, depth +1 to +3).
- One n, one device. Each form's share includes everything else in the circuit. Only the differences are read.
- The plain form is 2026-11-19's circuit as sent, so the comparison with 2026-11-19 stays.
- During the last read and after it, the target may sit in |1>, unread (once per item); the result does not change.
  (最後の読み出しの間とその後、目標は読まれないまま |1> にいることがある（1 項目に 1 回）。結果は変わらない。) pk's last
  instruction, the target's return X, stands after the last fence (the home VS's check of 2026-11-21,
  `notes/verify_2026-11-21/`); the circuit is left as built (owner, 2026-11-21).

## Decisions at home before declaring ([OWNER] list)

1. Whether to run it (it can share a night with candidate A or B: 2 x 45.8 s).
2. n = 4 (proposed: 2026-11-19 has n = 4) or another n (`--n`).
3. The words and the reading table above.
4. Predictions PK-1, PK-2.

## Device procedure (home)

```
# psf-os at the declared commit (after-2026-11-20 or later); notebook at the declaring commit
python gpu/ipe_park_night.py build DEV OUT0 --job 0        # 76 circuits, 45.8 s; per form CZ, depth, footprint as sent
python gpu/ipe_park_night.py check OUT0                    # PASS
(the same for OUT1 --job 1)
python -m psf_os submit OUT0 ; python -m psf_os collect OUT0   # then OUT1, as every night
python gpu/ipe_park_night.py score OUT0 OUT1
```
