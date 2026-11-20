# Where should a qubit wait? Parking in |0> (workplace Claude, 2026-11-20; desk and dry runs, not declared)

From the workplace VS's check of 2026-11-20: as sent (compiled), IPE's target waits in a superposition. The compiler
merges its return to |1> with the next round's preparation across the wait. That gives one carrier per wait, where
the circuit as written has none (`notes/footprint_2026-11-20/sent.txt`). psf-os after-2026-11-20's `fence_waits`
(a barrier on every qubit around each wait) keeps it in |1>. `park.py` adds an X before and after the wait, so the
target waits in |0>. The action is the same (checked: the exact distribution of every phase at n = 2, 3, 4 is equal
to the plain circuit's).

## Desk (`park.py`, density matrix, 2000 shots per phase; noises notes/qpe_repro_2026-11-19/noise, never fitted)

| noise | n | plain | fence | park |
|---|---|---|---|---|
| a (CZ 1 %, damping 2 % per read) | 3 / 4 / 5 | 0.967 / 0.948 / 0.932 | 0.950 / 0.918 / 0.890 | **0.973 / 0.959 / 0.946** |
| c (CZ 0.2 %, damping 2 %, dephasing 12 % per conditional) | 3 / 4 / 5 | 0.856 / 0.731 / 0.601 | 0.872 / 0.754 / 0.625 | **0.892 / 0.785 / 0.662** |

As sent, the waits have:

- plain: carriers 1 at each wait, excited n/2 over the circuit;
- fence: carriers 0, excited n - 1;
- park: carriers 0, excited 0.

## The tool (`gpu/ipe_park_night.py`, draft `prereg/drafts-2026-11-21/ipe_park_DRAFT.md`): dry runs, n = 4, two jobs

| noise | pl | fe | pk | park (pk - pl) | fence (fe - pl) | row |
|---|---|---|---|---|---|---|
| qpe a | 0.9449 | 0.9179 | 0.9579 | +0.0130 KEEPS MORE | -0.0270 KEEPS LESS | decay |
| qpe c | 0.7378 | 0.7562 | 0.7854 | +0.0476 KEEPS MORE | +0.0183 KEEPS MORE | dephasing |
| wait only (damping 6 % per read) | 0.9672 | 0.8776 | 1.0000 | +0.0328 KEEPS MORE | -0.0897 KEEPS LESS | decay |
| cond only (dephasing 5 % per conditional) | 0.8839 | 0.9094 | 0.9076 | +0.0237 KEEPS MORE | +0.0255 KEEPS MORE | dephasing |

(2 SE 0.002-0.007; `dry/*.txt`.) Each noise lands on the row of its mechanism. The comparison pk - fe (beside) is
+0.12 under decay only, and the same within error under dephasing only.

## What it says for psf-os (a proposal, not a rule)

"Do not spread the state while a conditional waits" holds as sent only with a fence. With a fence, "no carrier" and
"nothing excited" ask for the same thing: waiting qubits in |0>. A psf-os pass could fence every wait and park every
waiting qubit known to be |1> (from the footprint's branches). Whether the device rewards it is candidate C's
question.

## Every wait, not only the reads (after the workplace VS's その6, 2026-11-20)

The VS found that fenced at the reads only, the target still waits in a superposition at IPE's phase-feedback
conditionals. These are decided on bits read rounds before, and the compiler puts them after the next round's CZ,
outside the fence: 6 of n = 4's 9 conditionals. So "pk waits in |0>" held at the reads and resets only.

`fence_waits(qc, conditionals=True)` (psf-os after-2026-11-20) also fences each such run, and
`park(qc, conditionals=True)` parks the target there too. Counted as the VS counts, at every read and every
conditional run (`wait_footprint(span=True, conditionals=True)`, compiled, n = 4, phase 5):

| form | waits: read r / conditional c, carriers | excited | depth |
|---|---|---|---|
| plain | r1 c1 r1 c1 r1 c1 r1 | 3.5 | 63 |
| fence (reads) | r0 c1 r0 c1 r0 c1 | 4.5 | 66 |
| fence (every wait) | r0 c0 r0 c0 r0 c0 | 6.0 | 72 |
| park (reads) | r0 c1 r0 c1 r0 c1 | 1.5 | 66 |
| park (every wait) | r0 c0 r0 c0 r0 c0 r0 | 0.0 | 72 |

Only the every-wait forms hold the target in one basis state at every wait. The same distributions as the plain
circuit at every phase, n = 3, 4 (exact). `gpu/ipe_park_night.py` now builds them by default (`--reads-only` gives the
forms the VS checked in その6). Desk: `park2_n4.txt`; dry runs of the tool: `dry_all_waits/`.

Desk (`park2_n4.txt`, n = 4): noise a plain 0.948, fence (every wait) 0.918, park (reads) 0.959, park (every wait)
0.959; noise c 0.731, 0.790, 0.785, **0.824**. Under damping at the reads only, the extra fences change nothing;
under dephasing per conditional, parking at every wait adds 0.04.
