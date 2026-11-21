# Declared: should psf-os fence the RUS chains, and park their likely-|1> waiting qubits? One night off marrakesh

Home Claude, 2026-11-21, on the owner's choices of 2026-11-21 (21:0x JST: three forms in one job, the controls, off
marrakesh; 22:2x JST: the fills below, each chosen as home Claude proposed). Declared when the commit that adds this
file is pushed, before the night's device record is fetched. The tools are as of that commit; psf-os 0.3.0 as
released (v0.3.0, 2b8e2c4; the code of cedd90d). Tool `gpu/rus_fence_night.py` (home VS, 722e5ef0).

The home VS's draft at this commit (`prereg/drafts-2026-11-21/rus_fence_DRAFT.md`) is declared as written, with its
[OWNER] items filled as below; its Why, Design, dry runs, words, reading table, known limits and the excited count are
copied here. Where this file and the draft differ, this file holds.

## The [OWNER] items

1. **Plan gamma** (`--plan gamma-one-job`): one job at 1950 shots, 84 circuits, 50.2 s by the model: NF m3 L3 x 3, P0
   L3 x 7, P2 m3 L3 x 7, P3 L3 x 3 copies, each copy in the three forms D, F, M; the IPE control (phases 2, 6, 10, 14,
   parked and unparked) and the repetition code's F10, F6P, F6 x four errors; one sentinel. Home dry build on the
   2026-11-21 records of ibm_fez and ibm_kingston: 84 circuits, 50.2 s, check PASS on both (every RUS item, both
   controls' declared checks); on the marrakesh record the tool refuses ("the rule runs this test off ibm_marrakesh").
2. **The device**: not ibm_marrakesh; of ibm_fez and ibm_kingston the one with fewer pending jobs in `queue.json`
   (`pick`).
3. **Words, thresholds, the reading table and its next-step column**: as in the draft (copied below), with the gate
   changed (item 5).
4. **Predictions**: **RF-1** the IPE control KEEPS MORE (parked - unparked >= 2 SE; on marrakesh +0.0387 and +0.0349
   at n = 4; this device has no record). RF-2 (NF's parking) and RF-3 (P0's fence): no direction declared. Parking the
   likely value and the RUS fence have never run on a device.
5. **The gate, changed by the owner**: when the IPE control does not read KEEPS MORE, every number and word is still
   reported and the reading row is still read and recorded, but **no next step for psf-os is taken from this night**
   (the next-step column is suspended): a control that does not repeat on a new device is itself a result (parking
   may not carry to this device).
6. **M's rule**: a waiting qubit is parked when its noiseless probability of |1> is above 0.5 (as built; the limit
   that a qubit near 0.5 may be flipped the wrong way on the device is kept in the known limits).

## Why

- **The desk study** (`notes/evacuate_2026-11-21`). The RUS chains' excited count at their waits cannot be evacuated
  qubit by qubit: it is entangled, or on qubits that take part in the wait. But two things move them a lot under
  illustrative noise:
  - the fence alone, with a sign that depends on the form and the noise;
  - an X pair around each wait on every waiting qubit whose probability of |1> is above 0.5 ("park the likely
    value"). This removes 76-85 % of the waiting qubits' excited count in P0, P3 and NF.
- **The device records** behind any expectation:
  - The weekend's C (`results/weekend-shared-night-2026-11-21`): the fence alone on IPE, fe − pl −0.0042, SAME; parking
    the always-|1> target, pk − pl +0.0387.
  - The parked phase estimation (`results/qpe-parked-night-2026-11-21`): +0.031 to +0.039.
  - **Both are the always-|1> case on IPE, on ibm_marrakesh.** The fence on the RUS chains, and parking the likely
    value, have never run on a device.
- **The device:** off marrakesh, to fill paper 11's limit of one device.

## Design (one device record; rule C placement; no mitigation; ff arms only)

**RUS items:** three forms of one circuit, side by side in one job, with copies a, b, …

| form | content |
|---|---|
| D default | psf-os 0.3.0 as built: the chains have nothing to park, so no fence and no X |
| F fenced | `fence_waits(conditionals=True)` |
| M fenced + the likely value parked | F, and at every wait an X before the fence and after the closing fence on each waiting qubit (neither measured there nor inside its conditionals) whose noiseless probability of \|1>, over the branches with their weights, is above 0.5 |

- M's qubits and their probabilities are in `part.json` (`majority`) per job: NF m3 L3 15 qubit-waits, P0 L3 5,
  P2 m3 L3 3, P3 L3 4.
- `check` holds that, per item:
  - the three forms' noiseless distributions are equal (as compiled);
  - their compiled CZ counts are equal (33, 33, 33; P3 22);
  - the fences survive compiling (F 14-15 full fences, M 16-22);
  - M's X are kept: one-qubit gates exceed F's by the added X.
- **Differences**, read as the loop reads g (|P − exact|, nearer is better; P read as declared, P2 flipped):
  - the fence F − D;
  - parking M − F (against F, so that the fence does not enter).

**Controls in the same night** (addition 2, A):

- IPE n = 4 at phases 2, 6, 10, 14, parked (0.3.0's default) and unparked (`park_skip`). Those are the paired phases
  of 2026-11-21 that keep all 8 CZ when compiled. Read as C's park: parked − unparked.
- The repetition code: F10, F6P, F6 × the four errors, read as the weekend's A. Footprint F6P − F10, CZ F6 − F6P, and
  F6 against the ceiling 0.875.

**The device (the rule):** not ibm_marrakesh. Of ibm_fez and ibm_kingston, the one with fewer pending jobs in
daily_fetch's `queue.json` (ties: queue.json's order) whose record `fetch_in/<device>/dev` exists (`pick`). Every plan
builds and checks on both records.

## Plan (the declared row of the draft's table)

| plan | jobs (shots) | RUS items x copies | controls | circuits | s | 2 SE of a difference (P ~ 0.7): NF / P0, P2 / P3 |
|---|---|---|---|---|---|---|
| gamma | 1 (1950) | NF x 3, P0 x 7, P2 x 7, P3 x 3 | in the job | 84 | **50.2** | 0.017 / 0.011 / 0.017 |

Controls at 1950 shots: IPE 2 SE about 0.010; the repetition code's comparisons about 0.011.

## Dry runs (ILLUSTRATIVE noise, never fitted; `expect.txt`; `dry/`)

Three noise types:

- wait: damping 6 % per read.
- cond: dephasing 5 % per conditional.
- phase: a coherent RZ(0.15) on the other qubits while a neighbour is read (the third type, addition 2, C3).

| item | wait: fence / park | cond: fence / park | phase: fence / park |
|---|---|---|---|
| NF m3 L3 | +0.009 / **+0.316** | +0.044 / 0.000 | +0.011 / **−0.027** |
| P0 L3 | **−0.056** / +0.098 | **+0.044** / 0.000 | +0.005 / +0.008 |
| P2 m3 L3 | +0.044 / 0.000 | +0.044 / 0.000 | +0.007 / 0.000 |
| P3 L3 | −0.070 / +0.099 | +0.017 / 0.000 | −0.056 / +0.006 |

- **Parking works only against damping, as the desk reasoning says.**
  - Under dephasing a superposition stays one after an X, so parking does nothing (0.000).
  - Under a coherent phase, the X only reverses the phase picked up during the wait and does not cancel it, so parking
    can cost (NF −0.027).
- **The fence's sign on P0 tells damping (−) from dephasing per conditional (+).**

## Verdicts

- Per item and difference: KEEPS MORE (g ≥ 2 SE), SAME WITHIN ERROR, KEEPS LESS (g ≤ −2 SE). These are C's words.
- The controls: as on their own nights (C's park words; the weekend A's words and ceiling words).
- **Gate (as changed, item 5):** when the IPE control does not read KEEPS MORE, the rows are still read and recorded,
  and no next step for psf-os is taken from this night.

## Reading table (the fence read on P0, parking read on NF; P2's fence and P3 beside)

| P0 fence (F − D) | NF parking (M − F) | reading (desk reason) | next step for psf-os |
|---|---|---|---|
| KEEPS LESS | KEEPS MORE | damping dominates the waits (the desk's wait type: fence − on P0, park +) | 0.3.1: "park the likely value" a default candidate; do not fence RUS-like chains by default |
| KEEPS MORE | SAME WITHIN ERROR | dephasing per conditional dominates (the cond type: fence +, park 0) | 0.3.1: fencing the waits a default candidate; no likely-value parking |
| SAME WITHIN ERROR | KEEPS LESS | a coherent phase while reading dominates (the phase type: park −) | neither; the echo across waits (idea 2) studied at the desk |
| KEEPS MORE | KEEPS MORE | damping and dephasing both act | both candidates for 0.3.1 (fence, then park on it) |
| KEEPS MORE | KEEPS LESS | dephasing and a coherent phase | fencing a candidate; parking not added, the reason recorded |
| SAME WITHIN ERROR | KEEPS MORE | damping, with the fence neutral on P0 | parking a candidate; the fence not changed |
| KEEPS LESS | SAME WITHIN ERROR | the fence costs on P0; parking not seen | neither added; the fence's cost recorded |
| KEEPS LESS | KEEPS LESS | not read for a mechanism (no single desk type gives it) | neither; recorded |
| SAME WITHIN ERROR | SAME WITHIN ERROR | not seen at this night's shot noise | neither; recorded |

- Every one of the 9 outcomes falls on one row.
- **Beside, never read for a row:**
  - P2's fence: + under damping and dephasing in the desk, so a KEEPS LESS there would be against the desk;
  - P3's two differences;
  - the repetition code's words;
  - the excited count (below).

## Predictions

- **RF-1** the IPE control KEEPS MORE.
- RF-2 (NF's parking) and RF-3 (P0's fence): no direction declared.
- The only device records behind RF-1 are the always-|1> park on IPE (two nights, marrakesh).

## Beside: the excited count while waiting, as compiled (record only; `expect.txt`, the kingston record)

| item | D | F | M |
|---|---|---|---|
| NF m3 L3 | 23.35 | 16.15 | 4.54 |
| P0 L3 | 13.52 | 10.19 | 8.91 |
| P2 m3 L3 | 15.90 | 8.69 | 6.16 |
| P3 L3 | 6.48 | 4.81 | 4.77 |
| P0 L2 | 6.23 | 5.12 | 5.23 |

This is the expected waiting qubits in |1>, summed over the waits (footprint, span, conditionals). Whether the device's
differences follow these is looked at after the night, never as a verdict.

## Known limits

- **The fence does two things:** it stops the compiler from merging gates across a wait, and it changes when gates sit
  against the reads. "Noise during the wait" and "a different compiled schedule" are mixed in F − D. M − F holds the
  schedule fixed (the same fences), adding only X pairs.
- **M's rule uses noiseless probabilities.** On the device, a qubit near 0.5 may be flipped the wrong way more often
  than not.
- **M adds one-qubit gates:** 4-30 X per item, 2 per parked qubit-wait. Their error is in M − F.
- **The control on a new device:** its +0.035 is marrakesh's; on fez or kingston it has no record. The gate suspends
  only the next step (item 5).
- One night, one device; copies in one job; noise is illustrative only.

## Device procedure (home)

GitHub first (VPN ON), then the device (VPN OFF), as every night. The device step:
```
python gpu/daily_fetch.py OUT/fetch_in
DEV=$(python gpu/rus_fence_night.py pick OUT/fetch_in)        # not marrakesh; the shorter queue of fez, kingston
python gpu/rus_fence_night.py build OUT/fetch_in/$DEV/dev OUT/rf --plan gamma-one-job
python gpu/rus_fence_night.py check OUT/rf                     # PASS, or stop
python -m psf_os submit --job OUT/rf/job0/job ; python -m psf_os collect --job OUT/rf/job0/job --wait-min 20
python gpu/rus_fence_night.py score OUT/rf
```
