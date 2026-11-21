# Paper 11: outline (home, 2026-11-21; an outline, not a draft text)

Working title: "Where a Qubit Waits: Rules for Real-Time Control from Declared Nights on IBM Heron". Author TN Holdings
(only). It follows paper 10 (doi 10.5281/zenodo.24367001, which counts the first 57 declared predictions) and covers
the three device runs after it: 2026-11-20 (decoy, loopvar), 2026-11-20 evening (the paired loop), 2026-11-21 (the
weekend's three tests in one night). Every result was declared before its device record was fetched; every shot
counted; no mitigation.

## The claim, and its scope

- A program that measures in the middle and acts on the result at once spends most of its loss while it waits.
  Tonight's question was not whether real-time control works (paper 10) but what an operating layer should do with
  the waits. The device answered in four rules, each from a declared comparison inside one job:
  1. **Park**: a qubit that waits in |1> keeps more if it is turned to |0> for the wait and back after (IPE n = 4:
     +0.039, 2 SE 0.0045; on another calibration with psf-os 0.3.0's default, +0.035, +0.031, +0.039 at n = 4, 5, 6). Fencing it so that it waits in |1> instead of a superposition gains nothing (-0.004, SAME).
  2. **Few carriers and few CZ**: both count (repetition code: one carrier instead of three at equal CZ +0.015; 6 CZ
     instead of 10 at one carrier +0.022).
  3. **Do not seat a conditional item next to another**: the first conditional item of a packed circuit loses about
     0.057 whatever stands before it (decoy: a fixed item first does not shield it).
  4. **Decide inside one job**: copies inside a job agree, jobs minutes apart drift beyond shot noise (one L of three,
     p 0.006); a loop that compares across jobs reads the drift as an effect. The paired loop compares the incumbent
     and the candidate in the same job.
- Beside the rules: the classical record of iterative phase estimation stays cheap to n = 6 (beyond the ceiling at
  n = 4, 5, 6 by +0.43, +0.49, +0.54; the loss per added bit FLAT on the log, i.e. per round, not per conditional).
- Not claimed: that parking helps every circuit (one circuit family, one n, one device, one night); that the
  repetition code passes its ceiling (its best form F6 0.8741 against 0.875, NOT BEYOND); any error correction (F6
  decodes during the wait and cannot protect a memory).

## Evidence (all declared; job ids, calibration times and charges in each results folder)

| run / device | test (folder) | result | declared predictions |
|---|---|---|---|
| 11-20 marrakesh (cal. 11-19 23:09) | decoy (`results/decoy-night-2026-11-20`) | A loses -0.0565 / -0.0567 / -0.085 at D0 / D1 / D2 (2 SE about 0.020), B SAME everywhere: row 2, the first conditional item loses | DC-1 held |
| 11-20 marrakesh | loopvar (`results/loopvar-night-2026-11-20`) | copies agree inside a job (9 pairs pooled, chi2 9 df, p 0.625); between jobs L2 DRIFTS (p 0.006, excess SD 0.014), L1 p 0.080, L3 p 0.623 | LV-1 held |
| 11-20 evening marrakesh (cal. 11-19 23:09) | the paired loop (`results/loop-paired-night-2026-11-20`) | two rounds, 110 s: L1 P2+M (+0.046 in-job), L2 P0 (P1 not adopted, -0.023), L3 P2+M (+0.039 then +0.033); no overshoot | LP-2 held (one row) |
| 11-21 marrakesh (cal. 11-21 01:34) | A: repetition code, four forms (`results/weekend-shared-night-2026-11-21/A`) | F16 0.7511, F10 0.8364, F6P 0.8518, F6 0.8741 (all NOT BEYOND 0.875); footprint +0.0153 and CZ +0.0224 KEEPS MORE: "both" | RC4-1 held |
| 11-21 marrakesh | B: IPE n = 4, 5, 6 (`…/BC`) | 0.8957, 0.8715, 0.8451, all BEYOND; log drops 0.0274, 0.0308, acceleration +0.0034 (2 SE 0.0077) FLAT | QL-1 held |
| 11-21 marrakesh | C: plain / fence / park (`…/BC`, job BC1) | 0.8957 / 0.8914 / 0.9344; park KEEPS MORE, fence SAME | none declared (table only) |
| 11-21 marrakesh (cal. 11-21 10:39) | IPE parked by psf-os 0.3.0's default (`results/qpe-parked-night-2026-11-21`) | parked - unparked in one job: +0.0349, +0.0312, +0.0386 at n = 4, 5, 6 (2 SE about 0.0075), KEEPS MORE at every n; parked beyond at every n; parked shape FLAT | QP-1 held, QP-3 held |

Predictions since paper 10: 7 declared, 7 held. Over the nights of 11-16 to 11-21: 64 declared; 44 held, 20 failed
(each failure stays in paper 10 and its folder). Device time for this paper: 165 + 110 + 111 + 83 = 469 s charged.

Independent checks (home VS, qiskit, aer and numpy only, no project scorer): decoy and loopvar (a2c6eb56), the
paired loop (bfae2760, seven of seven items agree); the weekend night (1a87c959: every number, word and row agrees).

## Sections (planned)

1. **Introduction**: paper 10's result in one paragraph; the question of this paper: what to do with the waits.
   The 11-16 neuron finding (holding the likely 1 as |0> while waiting, +0.11 to +0.18) as the first hint, which
   changed the encoding; C isolates the wait itself (same action, same CZ, three ways to wait).
2. **Method**: declaration on push; one job per comparison; the 2 SE words; the reading tables fixed before the
   data and counted to have no gaps; tools as of the declaring commit; the shared night (three tests, three jobs,
   off and floor arms not sent because no verdict reads them).
3. **Where a qubit waits (C)**: the forms, the footprint as sent (the compiler merged the target's rotations across
   the wait: what is written is not what waits), the result, the reading row. Why decay, not dephasing, is the
   reading: |0> keeps, |1> is no better than the superposition.
4. **What a wait costs (A)**: the four forms; carriers and CZ separated by F6P; both keep more; the depth as a known
   limit; F6 at the ceiling, not beyond; the 11-19 F16 (0.812) against tonight's (0.751): another calibration.
5. **Packing (decoy)**: the earlier finding (11-18: one conditional neighbour costs 0.06); the decoy design (Z first,
   Z last, no Z); row 2; the rule kept in psf-os.
6. **Deciding inside one job (loopvar, the paired loop)**: 11-19's same stack read +0.006 then +0.018 across jobs;
   loopvar's drift; the paired rule and its desk comparison (wrong steps 2.2-3.1 per night down to 0.06-0.56 under a
   drift type); the evening run; LP-2 on one row (thin).
7. **The classical record (B)**: IPE to n = 6; the log measure and why (a fixed loss per conditional shows on the log,
   not on the share); FLAT.
8. **The operating layer after these nights (psf-os)**: park by default (only qubits in |1> on every branch; the
   noiseless output and the CZ count checked equal at every build; old records rebuilt without parking)
   (psf-os park-default-2026-11-21, 21ca4c2: only IPE changes among the tools so far; 1032 of 1032 waits parked; reproduce 88 of 88 SAME; the owner's rules: park=False written in any test that compares with the unparked form, the bundle paths parked too, the off arm parked as the ff arm); the packing rule unchanged; the paired loop (opt-in);
   the footprint recorded at every build; the ledger's path checked by replay of the device records, not on the device
   (psf-os ledger-replay-2026-11-21, b736028: the 11-20 night replayed with a same-calibration ledger line starts from the ledger's stacks and stops where a circuit is not in the record; a broken ledger is not used, with its reason).
9. **Limits**: one device (marrakesh), one night per test; park on IPE n = 4 only; A's depth differences; B's shape
   from two jobs; the off arms not sent on 11-21; LP-2 one row; drift measured on one night.
10. **Reproduction**: `reproduce.py` entries (decoy, loopvar, paired dw/dc and `verify`, weekend A/B/C), all SAME.
11. **Conclusion**.

## Figures (planned)

- Fig. 1: C, the three forms per phase (pl, fe, pk), with the footprint as sent under each.
- Fig. 2: A, the four forms against the ceiling, with carriers and CZ on the axis labels.
- Fig. 3: loopvar, g per L and job with 2 SE; the paired loop's decisions beside.
- Fig. 4: B, log share against n with the ceiling's log.

## Two numbers side by side (to carry into the text)

- Vanity: IPE beyond its ceiling at n = 6 by +0.54; the parked IPE 0.934 at n = 4.
- Essence: four rules for the operating layer, each from one declared comparison inside one job, at 386 s of device
  time in all; the repetition code's best form still does not pass its ceiling.

## Before the text

- [PENDING] psf-os park-default (tests, the effect table on every earlier tool, reproduce all SAME); then a release
  (0.3.0) for the paper to cite.
- [OWNER] The title; whether the ledger replay is in the paper or only in the release notes; whether F6/F6P count as
  one test with the others (repcode4 draft, item 4).
