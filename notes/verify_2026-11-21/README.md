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
