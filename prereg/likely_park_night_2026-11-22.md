# Declared: should psf-os 0.3.1 park the likely value by default? (one night, off marrakesh)

Declared by home Claude on 2026-11-22 when the commit that adds this file is pushed, before the night's device record
is fetched; the home VS's draft (`prereg/drafts-2026-11-22/likely_park_DRAFT.md`, b2777d1c) moved here unchanged but
for this title, this paragraph and the submit line of the procedure. The tools are as of the declaring commit.

Home VS Claude, 2026-11-22, on the home instructions `VSクロードへの指示_0.3.1候補の実機試験の準備_2026-11-22.md` and
`VSクロードへの指示_0.3.1候補のOVERSHOOTと書き足し_2026-11-22.md`. The owner's choices, 2026-11-22:

- 0:4x JST: MP as the 0.3.1 candidate, plan B, the IPE control, and psf-os at 0.3.1 (candidate) with the declaration
  naming "0.3.1".
- 11:3x JST: the home's rule for the default; items with an OVERSHOOT not counted; predictions LP-1 and LP-2 only;
  psf-os a6170e5.

Declared when home Claude moves this file to `prereg/` and the commit is pushed, before the night's first fetch.

- Tool: `gpu/likely_park_night.py` (table / pick / build / check / dry / score), at the declaring commit. It reads the
  declared `gpu/rus_fence_night.py` only, for its items, device rule and noises.
- psf-os: **0.3.1 (candidate), branch likely-park-2026-11-22 at a6170e5.** `build(park_likely=...)` is off by default
  there; the tool names its L items. The tool passes the declared version "0.3.1" to the safety guard.
- Notes: `notes/likely_park_2026-11-22/` (the desk design) and `notes/likely_park_night_2026-11-22/` (the dry runs).

## Why

- **The night of 2026-11-21 on ibm_fez** (`results/rus-fence-night-2026-11-21`):
  - parking the likely value on top of the full fence: M − F NF +0.0877, P0 +0.0140;
  - the full fence itself: F − D P0 −0.0453, P3 −0.0243;
  - so the form sendable then: M − D NF +0.079, P0 −0.031, P3 −0.022.
- **The desk** (`notes/likely_park_2026-11-22`): a partial fence keeps the pair without the full fence's effects. It
  is a barrier on the parked qubits and the wait's own qubits, at the parked waits only (MP). Under illustrative
  damping, MP − D is NF +0.268, P0 +0.009, P3 +0.011.
- **MP itself has never run on a device.**

## Design (one device record; rule C placement; no mitigation; ff arms only; 1950 shots; one sentinel)

| form | content |
|---|---|
| D | psf-os's default (0.3.0's): the RUS chains have nothing to park |
| L | `build(park_likely=...)`: every waiting qubit with P(\|1>) > 0.5 gets an X pair behind a partial fence (MP) |

- **Plan B:** NF m3 L3 × 4, P0 L3 × 14, P3 L3 × 10, each copy as a D and L twin in one job.
- **The IPE control:** n = 4 at phases 2, 6, 10, 14, parked and unparked (`park_skip`).
- **Size:** 68 circuits, 41.2 s by the model.
- **`check` (PASS before anything is sent):**
  - per item, D and L with equal compiled noiseless distributions and CZ (33 / 33; P3 22 / 22);
  - every parked wait in L's record fenced on the device by barriers holding its parked qubits and a qubit of the
    wait, at least two per wait (the pair can neither fold nor leave the wait);
  - L with more one-qubit gates on the parked qubits than D;
  - the IPE control by qpe_repro_night.check;
  - psf_os_build: version 0.3.1, park True, park_likely naming every L item, declared 0.3.1.
- **The device (the rule of 2026-11-21):** not ibm_marrakesh. Of ibm_fez and ibm_kingston, the one with fewer pending
  jobs in queue.json; ties go by queue.json's order. Both records build and check.

## Verdicts

- **Per item (NF, P0, P3):** L − D as the loop reads g (|P − exact|, nearer is better; P read as declared), SE from
  both: KEEPS MORE (g ≥ 2 SE), SAME WITHIN ERROR, KEEPS LESS (g ≤ −2 SE).
- **OVERSHOOT (the loop's rule):** a form's P above that form's noiseless value + 2 SE (its own SE). The noiseless value
  is the compiled circuit's, exact; for P0 L3 and NF m3 L3 it is 0.7834, for P3 L3 0.7060. An item whose D or L
  overshoots has its word recorded, but **it is not counted for the rule for the default**. The row says so.
- **The gate:** the IPE control, parked − unparked, in the same words. It is open when it reads KEEPS MORE. When it is
  closed, every number and word is read and recorded (as on the RUS fence night), but no default is decided:
  `park_likely` stays opt-in.

## The rule for the default (the owner's decision of 2026-11-22; one row per outcome)

Among the counted items, the items with no OVERSHOOT in D or L:

| counted items' words | gate | 0.3.1 |
|---|---|---|
| no KEEPS LESS, at least one KEEPS MORE | open | **`park_likely` the default** |
| any KEEPS LESS | open | opt-in (chosen when wanted); the item and its size recorded |
| no KEEPS MORE, no KEEPS LESS (all SAME) | open | opt-in; not seen at this night's shot noise |
| no item counted (every item overshoots) | open | opt-in; the numbers recorded |
| (any) | closed | opt-in; 0.3.0's default kept; the numbers recorded |

Every outcome of the three words, the three OVERSHOOT flags and the gate falls on one row. In the tool's score, the
branches are tested in `notes/likely_park_night_2026-11-22/test_score.py`.

## Predictions (written before the data)

- **LP-1:** the IPE control KEEPS MORE. Three nights so far: marrakesh +0.0387 and +0.0349; fez +0.0291.
- **LP-2:** NF's L − D KEEPS MORE.
- P0 and P3: no direction declared; they are read by the rule.
- The device records behind them are the fez night's M − F (on the full fence) and the always-|1> park's three nights.
  MP itself has never run.

## Dry runs (ILLUSTRATIVE noise, never fitted; `notes/likely_park_night_2026-11-22/`)

Plan B was built on the 2026-11-21 records of ibm_fez and ibm_kingston, and check PASSed on both. Both devices give
the same numbers.

| noise | NF | P0 | P3 | IPE control | the rule |
|---|---|---|---|---|---|
| damping per read (the type the fez night read) | +0.265 KEEPS MORE | +0.014 KEEPS MORE | +0.016 KEEPS MORE | +0.040 MORE | the default |
| dephasing per conditional | +0.010 SAME | +0.002 SAME | +0.002 SAME | +0.047 MORE | opt-in (no counted item MORE) |
| a coherent phase while reading | +0.006 SAME, OVERSHOOT | +0.030 MORE, OVERSHOOT | +0.022 MORE, OVERSHOOT | +0.019 MORE | opt-in (no item counted) |

Under the coherent phase, P0's D reads 0.871, above its noiseless value 0.783. A lower L then reads nearer exact, so
g says KEEPS MORE without L keeping more. OVERSHOOT takes that item, and the other two, out of the count. On the fez
night every P of these items was below its noiseless value (P0 and NF 0.61-0.70 against 0.783; P3 0.61-0.63
against 0.706).

## Known limits

- **The partial fence is local.** It stops the compiler's merging at the parked waits only, and only on the parked
  qubits and the wait's own qubits; elsewhere the compiler is free as in D. L − D therefore holds the pair and that
  local change of schedule.
- **The device may differ from the first night's** (the rule: fez or kingston). If the night falls on kingston, the
  device differs from the fez night the test rests on. The judged comparison, L − D inside one job, holds there too,
  but a comparison with fez's +0.088 (M − F) is not possible.
- **P0's and P3's sizes are uncertain.** The illustrative damping overstated P0's parking at the desk (+0.098 against
  the device's +0.014, both on the full fence).
- **No qubit near 0.5 is parked.** The rule uses noiseless probabilities (P(|1>) > 0.5), but on these three items every
  parked qubit is well away from 0.5: NF 0.675-0.922, P0 0.85-0.922, P3 0.79-0.89.
- **Chance outcomes.** With no effect at all, one of the three items reads KEEPS LESS by chance with a probability of
  about 7 % (2.3 % per item at 2 SE, one side); KEEPS MORE by chance is about as likely. The rule is cautious on the
  side of a loss.
- **g reads distance to exact.** An item whose D or L overshoots is not counted (above). One that reads above exact
  but within its noiseless value + 2 SE is counted.
- One night, one device, one family of circuits (the RUS chains); illustrative noise only.

## Device procedure (home)

```
# psf-os at a6170e5 (0.3.1, candidate), checked clean; the notebook at the declaring commit
python gpu/daily_fetch.py fetch_in                                    # as every night: fetch_in/ with queue.json
DEV=$(python gpu/likely_park_night.py pick fetch_in)                  # not marrakesh; the shorter queue of fez, kingston
python gpu/likely_park_night.py build fetch_in/$DEV/dev OUT --plan B
python gpu/likely_park_night.py check OUT                             # PASS
python -m psf_os submit --job OUT/job0/job ; python -m psf_os collect --job OUT/job0/job --wait-min 20
python gpu/likely_park_night.py score OUT                             # the words, OVERSHOOT, the gate, the rule's row
```
