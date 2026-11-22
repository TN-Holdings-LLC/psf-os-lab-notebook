# DRAFT (not declared): should psf-os 0.3.1 park the likely value by default? (one night, off marrakesh)

Home VS Claude, 2026-11-22, on the home instruction `VSクロードへの指示_0.3.1候補の実機試験の準備_2026-11-22.md`. The
owner chose, 2026-11-22 0:4x JST: MP as the 0.3.1 candidate, plan B, the IPE control, and psf-os at 0.3.1 (candidate)
with the declaration naming "0.3.1". **The predictions, words, thresholds, reading table and the rule for the default
marked [OWNER] are the owner's / home Claude's.**

- Tool: `gpu/likely_park_night.py` (table / pick / build / check / dry / score). It reads the declared
  `gpu/rus_fence_night.py` only, for its items, device rule and noises.
- psf-os: branch likely-park-2026-11-22, version 0.3.1 (candidate). `build(park_likely=...)` is off by default; the
  tool says it per item.
- Notes: `notes/likely_park_2026-11-22/` (the desk design) and `notes/likely_park_night_2026-11-22/` (this draft's dry
  runs).

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
- **`check`:**
  - per item, D and L with equal compiled noiseless distributions and CZ (33 / 33; P3 22 / 22);
  - every parked wait in L's record fenced on the device by barriers holding its parked qubits and a qubit of the
    wait, at least two per wait (the pair can neither fold nor leave the wait);
  - L with more one-qubit gates on the parked qubits than D;
  - the IPE control by qpe_repro_night.check;
  - psf_os_build: version 0.3.1, park True, park_likely naming every L item, declared 0.3.1.
- **The device (the rule of 2026-11-21):** not ibm_marrakesh. Of ibm_fez and ibm_kingston, the one with fewer pending
  jobs in queue.json; ties go by queue.json's order. Both records build and check.

## Verdicts [OWNER]

- Per item (NF, P0, P3): L − D as the loop reads g (|P − exact|, nearer is better; P read as declared), SE from both:
  KEEPS MORE (g ≥ 2 SE), SAME WITHIN ERROR, KEEPS LESS (g ≤ −2 SE).
- The IPE control: parked − unparked, the same words. **The gate is open when it reads KEEPS MORE.**
- When the gate is closed: every number and word is read and recorded (as on the RUS fence night), but no default is
  decided; `park_likely` stays opt-in.

## The rule for the default [OWNER] (the home's proposal; one row per outcome)

| the three items' words | gate | 0.3.1 |
|---|---|---|
| no KEEPS LESS, at least one KEEPS MORE | open | **`park_likely` the default** |
| any KEEPS LESS | open | opt-in (chosen when wanted); the item and its size recorded |
| no KEEPS MORE, no KEEPS LESS (all SAME) | open | opt-in; not seen at this night's shot noise |
| (any) | closed | opt-in; 0.3.0's default kept; the numbers recorded |

Every outcome of 3 words × 3 values × the gate falls on one row.

An alternative for the owner to weigh, not the home's: require NF KEEPS MORE (the item the device's night supports)
instead of "at least one". Under the home's rule a lone P0 KEEPS MORE, with NF SAME, would also make it the default.

## Predictions [OWNER]

- LP-1 [OWNER: e.g. the IPE control KEEPS MORE (three nights: marrakesh +0.0387, +0.0349; fez +0.0291)]
- LP-2 [OWNER: e.g. NF L − D KEEPS MORE, or no direction]
- The device records behind them are the fez night's M − F (on the full fence) and the always-|1> park's three nights.
  MP itself has never run.

## Dry runs (ILLUSTRATIVE noise, never fitted; `notes/likely_park_night_2026-11-22/`)

Plan B was built on the 2026-11-21 records of ibm_fez and ibm_kingston: check PASS on both. Both devices give the same
numbers.

| noise | NF | P0 | P3 | IPE control | the rule |
|---|---|---|---|---|---|
| damping per read (the type the fez night read) | +0.265 KEEPS MORE | +0.014 KEEPS MORE | +0.016 KEEPS MORE | +0.040 MORE | the default |
| dephasing per conditional | +0.010 SAME | +0.002 SAME | +0.002 SAME | +0.047 MORE | opt-in |
| a coherent phase while reading | +0.006 SAME | +0.030 MORE* | +0.022 MORE* | +0.019 MORE | the default* |

(*) Under the coherent phase, D overshoots exact on P0 (0.871 against 0.823). L's lower P reads nearer exact, so g reads
KEEPS MORE without L keeping more. This is an artifact of the |P − exact| reading (see the limits).

## Known limits

- The partial fence stops the compiler's merging at the parked waits only, and only on the parked qubits and the wait's
  own qubits. Elsewhere the compiler is free as in D. L − D therefore holds the pair and that local change of schedule.
- The night may fall on a device other than the first night's (the rule): fez or kingston.
- P0's and P3's expected sizes are uncertain. The illustrative damping overstated P0's parking at the desk (+0.098
  against the device's +0.014, both on the full fence).
- The rule uses noiseless probabilities (P(|1>) > 0.5). A qubit near 0.5 may be parked the wrong way.
- **g reads distance to exact.** When D overshoots exact (P above it, as a coherent phase can make it), a lower L reads
  KEEPS MORE although it keeps no more. On the fez night every RUS P was below exact (0.60-0.71 against 0.823). If D
  reads above exact on the night, the item's word is recorded with this note. [OWNER: whether such an item counts for
  the rule]
- One night, one device, one family of circuits (the RUS chains); illustrative noise only.

## Device procedure (home)

```
python gpu/daily_fetch.py fetch_in                                    # as every night: fetch_in/ with queue.json
DEV=$(python gpu/likely_park_night.py pick fetch_in)                  # not marrakesh; the shorter queue of fez, kingston
python gpu/likely_park_night.py build fetch_in/$DEV/dev OUT --plan B  # psf-os 0.3.1 (likely-park-2026-11-22)
python gpu/likely_park_night.py check OUT                             # PASS
python -m psf_os submit OUT/job0 ; python -m psf_os collect OUT/job0
python gpu/likely_park_night.py score OUT                             # the words, the gate, the rule's row
```
