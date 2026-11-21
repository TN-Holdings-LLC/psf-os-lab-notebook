# Where should a qubit wait: the home VS's independent check of the all-waits forms (2026-11-21)

Home VS Claude, from the home instruction `VSクロードへの指示_待つ場所の点検_2026-11-21.md`. Desk only, no device. The
report to home: `VSから家へ_待つ場所の点検_2026-11-21.md` (psf_zero_project).

## Setup

- Notebook b9c7f01a; psf-os after-2026-11-20 = d4fb614. The night version 61869bb is used for item 5 only.
- Builds on the 2026-11-19 marrakesh record (`results/loop-night-2026-11-19/fetch_in/ibm_marrakesh/dev`), into a
  work folder WORK outside the notebook:
  - `gpu/ipe_park_night.py build DEV WORK/aw_n{3,4}_j{0,1} --job J --n N`: every wait (the default);
  - the same with `--reads-only`, into `WORK/ro_n{3,4}_j{0,1}`.
- The scripts here use qiskit, aer and numpy only. They do not use psf-os's footprint or the notebook's dry and
  scorers. psf-os and the tool are used only to build the circuits and for the tool's own `check`.

## Files

| file | what | output |
|---|---|---|
| `waits.py` | For every wait (a measure or an if_else at the top level) and every waiting qubit: the ops that may run during it (neither ancestors nor descendants in the dependency graph of the sent circuit), and the qubit's state there, exactly, per classical branch (carrier = not a basis state; excited = P(1)). Also the exact distribution of the register. | `waits_summary.txt` |
| `build_fence.py` | Builds the plain IPE items through `feedforward.build(fence=True)` and compares every sent ff circuit, instruction by instruction, with the tool's fe form. Refuses if `WORK/bf_*` exists (psf-os does not overwrite). | `build_fence.txt` |
| `discrim.py` | Inserts ILLUSTRATIVE noise (never fitted) into the sent circuits: CZ depolarizing, amplitude damping on the waiting qubit at every read, phase damping on it at every conditional. Exact distributions by a branching density matrix, 1950 shots per phase, 20 seeds, words and rows as the draft. | `discrim_n4.json`, `discrim_n3.json` |
| `compare_default.py` | Default (no fence) builds of repcode_night, rus_night and qpe_repro_night part A, 61869bb against d4fb614, byte for byte. | `default_build_compare.txt` |
| `look.py` | Lists the instructions of sent circuits (reading aid). | |

## Results

1. **Every wait is fenced.** fe and pk (every wait, n = 3 and 4) have no op that may run during a wait. The one
   exception is pk's last read; see 2. `build(fence=True)` gives the tool's fe in all 24 ff circuits. With
   `--reads-only`, ops still float at 42-47 of the 104 waits of n = 4's fe.
2. **No carrier in fe or pk.** No waiting qubit is in a superposition at any point. pk is never excited at the cut
   before a wait.
   - pk's last instruction is the target's X (back to |1>). It is outside the last fence, so it may run during the
     ancilla's last read: the target may be in |1> during that read and after it, once per item. The target is never
     read, so the result is unchanged. The draft's Known limits say so (owner's wording, 2026-11-21).
3. **Same distribution, noiseless.** pl, fe and pk have the same exact distribution at every phase of n = 3 and 4
   (total variation 0). The single outcome in each of the 72 circuits matches its run card's success bits. The tool's
   `check` is PASS on all four jobs.
4. **One-to-one at n = 4** (20 seeds each):

   | noise | n = 4 | n = 3 |
   |---|---|---|
   | gates only | not seen 20 | not seen 19, against 1 |
   | damping per read | decay 20 | decay 20 |
   | dephasing per conditional | dephasing 20 | dephasing 20 |
   | mixed noises | as their mechanism, 20 each | weak damping: decay 18, against 2 |

   The night runs n = 4 only (owner, 2026-11-21).
5. **Defaults unchanged.** job/circuits.qpy, runs/ and build.json are byte-identical between 61869bb and d4fb614.
   job/manifest.json differs in `written` (the build time) only. d4fb614 adds checks.json beside the job.

## The weekend night's record (results/weekend-shared-night-2026-11-21): the home VS's independent recount

From the home instruction `VSクロードへの指示_週末の結果の独立検証_2026-11-21.md`. The report is
`VSから家へ_週末の結果の独立検証_2026-11-21.md`.

`weekend_indep.py RECORD OUT.json` writes `weekend_indep.txt` and `.json`. It uses qiskit, aer and numpy only. It
reads:

- the success bits named in each record;
- their right values from noiseless Aer of the recorded circuit (every one deterministic and equal to the record);
- the pooled shares and 2 SE;
- the declared comparisons;
- B's log shape, with SE = sqrt(t4^2 + 4 t5^2 + t6^2);
- the words and the rows of the reading tables.

The ceilings are the declared exact values; they are not recomputed.

Results:

- Every number and word equals the record.
- B's n = 4 is the 16 pl4 items; no job holds an ipe4 item.
- The compiled CZ of pl, fe and pk is the same at every phase.
- reproduce.py with psf-os a164fc5 gives 3 of 3 SAME.

## The parked phase estimation (results/qpe-parked-night-2026-11-21): the home VS's independent recount

From the home instruction `VSクロードへの指示_置いたIPEの結果の独立検証_2026-11-21.md`. The report is
`VSから家へ_置いたIPEの結果の独立検証_2026-11-21.md`.

`parked_indep.py RECORD WEEKEND_RECORD OUT.json` writes `parked_indep.txt` and `.json`. It uses qiskit, aer and numpy
only, and recounts:

- the parked shares and 2 SE per n;
- the paired differences on the phases that hold both forms, checking that each pair is in one job and that the
  phases are 0, step, 2 step, ...;
- the parked log shape with the declared SE;
- the words and the reading table's row (row 1).

Every number and word equals the record. Beside:

- **What was sent:** the jobs hold ff arms only and record `psf_os_build` 0.3.0 / park True / explicit; 83 s,
  1.3656 RU, 87.0 s.
- **The target at the waits:** in every branch at every wait of the parked n = 4 circuits, it is in |0>
  (P(|1>) <= 2.5e-31).
- **Against the weekend:** the parked n = 4 circuits equal the weekend's C pk circuits (16 of 16).
- **Compiled CZ per phase:** paired phases average 6.0, against 8.0 / 10.0 / 11.7 on the other phases. At n = 4, four
  of the eight paired phases (2, 6, 10, 14) keep the full 8 CZ.
- reproduce.py with psf-os 0.3.0 gives 1 of 1 SAME.
