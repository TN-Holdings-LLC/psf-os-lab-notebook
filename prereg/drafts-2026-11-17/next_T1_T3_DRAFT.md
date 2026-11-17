# DRAFT (not declared): the next steps after T1 and T3-A, to run the same night (workplace Claude, 2026-11-17)

Home instruction 17f (owner 15:37 JST: "テスト1が成功したらテスト2に進む感じ？それならその準備もしておいて"). This is a
draft; the numbers, the verdict words and whether to run are the owner's; the declaration is written and pushed at
home. Common rules as in `prereg/ff_night_2026-11-17.md` (device, rule C placement, no mitigation, DD and twirling
off, every shot counted, each tool's `check` before submission, `score` as the verdict tool).

## N1 (after T1): the neuron without mid-circuit measurements at L = 2, 3 (`gpu/coh2_night.py`)

Condition to run: T1-1 held (coh1 CLOSER WITH CONTROL).

Items: coh2, coh3 (zipper+, no mid-circuit measurement; CZ 18 / 28; off arm = try 0 per neuron, the output moved to the
ff arm's read position, CZ 8 / 13) and rd2, rd3 (the third design; CZ 12 / 22) beside. Theta 1.1, m = 2, 4000 shots,
**16 circuits, 20.9 s by the model** (11-16 13:11 CET marrakesh record).

Exact identities (`coh2_night.py ideal`, branching simulation): coh{L}'s ff equals rd{L}'s ff in the joint
distribution of all tries and the output (TVD 1.9e-15, 3.1e-15); the off arms agree on (try-0 bits, output) (TVD
1.0e-15, 2.0e-15; the retry bits differ by construction); noiseless P(output 1): ff 0.7929 / 0.7060, off 0.6308 /
0.5010 (exact 0.8782 / 0.8230). Check PASS; both coh arms read the output on one physical qubit (5 and 8).

Verdict per item as T1 (d = |P_off - exact| - |P_ff - exact| >= 2 SE_d: CLOSER WITH CONTROL). Beside: |rd - noiseless|
- |coh - noiseless| per L with its two SE (never judged). Dry run (noiseless, Clifford sentinel): all four CLOSER WITH
CONTROL (d 0.155 / 0.180 / 0.201 / 0.207), beside +0.006 / +0.009 within 2 SE.

Draft predictions: N1-1 coh2 and coh3 CLOSER WITH CONTROL. N1-2 rd2 and rd3 CLOSER WITH CONTROL (as on 11-16).
Caution to keep: coh{L} is a fixed circuit, open to after-the-fact correction; N1 asks whether removing the waits beats
the added CZ (coh3 28 CZ against rd3's 22 and 6 mid-circuit measurements), not the ceiling question.

## N3 (after T3-A): iterative phase estimation at n = 4 (`gpu/apps2_night.py`)

Condition to run: T3-1 held (A BEYOND THE CEILING at n = 2 and 3).

Items: ipe4_j for all 16 phases (no selection: the ceiling is an average over all phases, and 16 fit one job). Two
qubits, CZ 0-8, depth 31-63, 3 mid-circuit measurements, 9 conditionals per circuit; **52 circuits, 61.0 s by the
model**. Ceiling C(4) = 0.4706 (exact, recomputed); off as read 0.3245; ff noiseless 1 for every phase. Check PASS.

Verdict as T3-A: the 16 circuits pooled, ff >= C(4) + 2 SE: BEYOND THE CEILING. Beside: the margin at n = 4 next to
tonight's n = 2, 3 (another job), per-phase ff, the off arm as read. Dry run: BEYOND, margin +0.529.

Draft prediction: N3-1 BEYOND THE CEILING at n = 4.

Beside (numbers only; whether to run it is the owner's): textbook phase estimation (n counting qubits, coherent
inverse QFT, target |1>) on the same record, rule C line with the fixed line routing, all phases checked noiselessly:

| n | iterative: qubits / CZ / conditionals | textbook: qubits / CZ / depth |
|---|---|---|
| 2 | 2 / 0-4 / 2 | 3 / 5-15 / 26-53 |
| 3 | 2 / 0-6 / 5 | 4 / 15-39 / 57-98 |
| 4 | 2 / 0-8 / 9 | 5 / 36-80 / 102-164 |

The textbook circuit is fixed (open to after-the-fact correction); the ceiling does not cover it.

## Both next steps together

N1 + N3: 68 circuits, about 82 s by the model, on top of tonight's 92.7 s.
