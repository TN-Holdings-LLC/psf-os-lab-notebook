# The weekend's three candidates shared in one night, and the seconds saved (desk, 2026-11-21)

Home VS Claude, on the home instruction `VSクロードへの指示_週末の相乗りと節約の案_2026-11-21.md` (the IBM time left is
about 60 min; the owner: "できるだけ相乗り"). The report to home is `VSから家へ_週末の相乗り_2026-11-21.md`
(psf_zero_project). Nothing here changes a test: no circuit, ceiling, word or threshold of a candidate. The tool lists
cuts and their seconds; the owner chooses [OWNER].

Tool: `gpu/weekend_shared_night.py` (new). It imports the candidates' tools read only:
- A: `gpu/repcode4_night.py`;
- B: `gpu/qpe_long_night.py`;
- C: `gpu/ipe_park_night.py`.

Device record for every build: `results/loop-night-2026-11-19/fetch_in/ibm_marrakesh/dev`, as the drafts used.

## The time model, and what the device charged

- The model (`psf_os.job.qpu_seconds`) is 0.036 s per circuit, plus 0.00027 s per circuit-shot, plus 3 s per job.
- Home's reading is right. Joining jobs saves 3 s per job removed and nothing else. The seconds come from circuits ×
  shots.
- The device's own charges agree (`charges.py`, `charges.txt`):
  - Over 105 recorded jobs, the charge is 2.6 s + 0.000269 s per circuit-shot. The largest residual is 9.9 s.
  - A per-circuit term does not show (fit −0.0009 s).
  - Charged / model is 0.935 over 101 jobs.
- psf-os refuses a job whose records hold different shot counts. A runs at 4000 shots, B and C at 1950, so A shares a
  job with B or C only at one shot count for all.

## The cuts (`table.txt`, `table.json`; model seconds, 60 s per job at most)

| row | night | circuits | jobs | s | 2 SE (against the draft) | not read any more |
|---|---|---|---|---|---|---|
| 0 | each alone, as the drafts (A 4000 shots; A needs 2 jobs under 60 s) | 560 | 8 | 370.0 | - | - |
| 1 | all three in shared jobs, nothing cut, all at 1950 | 552 | 6 | 328.6 | A ×1.43 | - |
| 2 | A at 2000 instead of 4000 (alone, one job) | 52 | 1 | 33.0 (from 68.4) | A ×1.41 | - |
| 3 | A without F16 (4000, one job) | 40 | 1 | 47.6 (from 68.4) | - | A's beside F10 − F16; the link to 2026-11-19's circuit |
| 4 | B's IPE n = 4 read from C's pl, + C | 452 | 5 | 269.4 (from 301.6) | - | nothing |
| 5 | C with fe and pk ff only (their off arm is pl's) | 84 | 1 | 50.2 (from 91.6) | - | fe's and pk's floors (beside) |
| 6a/6b/6c | A / B shape / C, each ff only | 20 / 120 / 52 | 1 / 2 / 1 | 25.3 / 73.6 / 32.2 | - | off and floor (beside) |
| 7 / 7b | B n = 5 (IPE + textbook) / n = 5 IPE only | 200 / 100 | 2 / 1 | 118.4 / 59.2 | - | B's shape (needs n = 4, 5, 6 on one night); 7b also IPE − textbook |
| 8 / 8b / 8c | A + B / A + C / B + C (A 4000 in its own jobs; n4 shared in 8c) | 408 / 208 / 452 | 6 / 4 / 5 | 278.4 / 160.0 / 269.4 | - | C / B / A |
| 9 | all three, only n4 shared (A 4000 in its own jobs) | 508 | 7 | 337.8 | - | nothing |
| **10** | **all three, ff only, n4 shared (A 4000 in its own job)** | **172** | **3** | **116.9** | **-** | **off and floor (beside)** |
| 10b | as 10, A at 1950 inside the shared jobs | 168 | 2 | 100.4 | A ×1.43 | off, floor |
| 10c | as 10, A without F16 | 168 | 3 | 112.5 | - | off, floor; F10 − F16 |
| 11 / 11b / 11c | A + C / A + B / B + C, ff only | 72 / 140 / 152 | 2 / 3 / 2 | 57.5 / 98.9 / 91.6 | - | B / C / A; off, floor |
| 12 | all three, ff only, B n = 5 IPE only | 104 | 2 | 75.5 | - | B's shape and textbook; off, floor |

Notes on the cuts:

- **B's IPE n = 4 = C's pl.** Same circuit and same off arm, as `AP.ipe(4, j)`. Compiled on the same qubits, all 48 arms
  of the two single builds are equal circuits. With B fenced, C's fe is B's fence (the same `fence_waits`).
- **Off and floor.** No candidate's verdict reads them:
  - every verdict pools ff success;
  - every ceiling is exact (A 0.875 per form; B and C C(n)).
  They are beside (the off arm's share, the floor's all-zero share, A's best fixed rule after the fact). `--ff-only`
  needs psf-os `build(ff_only=...)`: loop-paired-2026-11-21 (a164fc5), the commit the paired loop ran on.
- **C's fe and pk.** Their off arm is the same circuit as pl's (32 of 32 equal, `p1_all`). Their floors are not (0 of
  32): the floor follows the ff circuit's barriers and X.
- **Removing what was measured breaks comparisons:**
  - B without n = 4: the shape needs n = 4, 5, 6 on one night. Row 4 removes B's own n = 4 and reads C's.
  - A without F16: only the beside comparison goes. The declared pair (footprint F6P − F10, CZ F6 − F6P) stays.

## Layout

- `--layout apart` (as the instruction):
  - each group of candidates on its own qubits, at coupler distance ≥ 3 from the others;
  - the first group keeps rule C;
  - B and C form one group when B's n = 4 is C's pl.
  In `p1_all`: A [0-4], B [7, 8], C [11, 12].
- `--layout own`: every candidate on its rule-C qubits, as alone.
- In a psf-os job every arm is its own circuit, and the circuits run one after another. Two candidates never run at the
  same time, so distance between them guards against nothing inside one job. Moving B and C off [0, 1] does change
  their qubits from 2026-11-19's [OWNER].
- In row 10 the question does not arise: A has its own job, B and C share rule C [0, 1], and everyone keeps
  2026-11-19's qubits.

## Dry builds (`dry/`; the dry Clifford sentinel; noiseless)

| night | jobs (model s) | each candidate's own check | against the single builds | noiseless scores, shared against single |
|---|---|---|---|---|
| p10_A: A ff only, 4000 | 1 (25.3) | PASS | 16 ff arms: the same compiled circuit; CZ, depth the same | SAME |
| p10_BC: B shape + C, ff only, n4 from C | 2 (45.8, 45.8) | PASS (B job0, B job1, C job1) | 160 ff arms: the same compiled circuit; CZ, depth, footprint as sent the same | B SAME, C SAME |
| p1_all: all three, nothing cut, 1950, apart | 6 (328.6) | PASS (every candidate in every job) | 528 arms: CZ, depth, footprint as sent the same; 48 the same circuit (A, on its qubits); B and C moved | A, B, C SAME |

- "Own check" means each candidate's check function, run on a view of each job that holds only that candidate's
  cells and the sentinel:
  - A: `repcode4_night.check`. It covers c = 000, CZ 16/10/10/6 per arm with nothing cancelled, ceiling 0.875,
    carriers 3/3/1/1.
  - B and C: `qpe_repro_night.check` with the night's items, as `qpe_long_night.check` and `ipe_park_night.check`
    call it.
- `score` gives each candidate's own score function the cards read from every job. `psf_os.feedforward.cards` is
  swapped for the call only, because an ff-only item has no off arm for FF.cards. The candidates' code is unchanged.
- The psf-os notes "compiled CZ differ from the circuit as written" for IPE phases 8 and 12 (8 → 4, 6) appear in the
  single builds too. They are as on 2026-11-19 (C's draft: CZ 0-8).
