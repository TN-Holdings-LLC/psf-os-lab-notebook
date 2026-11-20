# DRAFT (not declared): does the classical side's cost grow with the number of feedbacks? Phase estimation at n = 4, 5, 6 (weekend candidate B)

Workplace Claude, 2026-11-20 (home's added instruction 3, item 4; home's improvement candidate 6). The plan, words,
thresholds and predictions marked [OWNER] are the owner's; the workplace built the tool, sized it and dry-ran it.
Tool: `gpu/qpe_long_night.py` (reads the declared `gpu/qpe_repro_night.py` only). Notes: `notes/ipe_long_2026-11-20/`.

## Why

- 2026-11-19 (`results/qpe-repro-night-2026-11-19`, marrakesh): iterative phase estimation (IPE: one ancilla, each
  bit read at once and fed back as a phase to the next round) 0.955, 0.915, 0.880 at n = 2, 3, 4, far beyond its
  ceiling C(n) (0.75, 0.588, 0.471); the textbook circuit (n counting qubits held to the end) 0.926, 0.845, 0.711.
- Each added bit adds one round (a CZ pair and a read) and n conditionals (the phase feedback of every bit already
  read, and the reset): 2, 5, 9, 14, 20 conditionals at n = 2 .. 6.
- If the loss is per round, the share falls by a fixed factor per added bit. If it is per conditional, the factor
  grows with n (one more conditional per bit than the bit before). 2026-11-19's two drops (0.040, 0.036) cannot tell
  a shape. Three n on one night can.
- This is the memory-hierarchy question in one number: does keeping the record in classical memory stay cheap as the
  record grows?

## Design (one device record; rule C placement; no mitigation; DD and twirling off; every shot counted)

The 2026-11-19 circuits unchanged (IPE from `notes/ffapps_2026-11-17` apps.ipe with its off arm; textbook =
qpe_repro_night.textbook_logical), every phase j = 0 .. 2^n - 1, 1950 shots per circuit, every job 100 circuits
(32 items x 3 arms + the sentinel's 4), 59.2 s by the model.

| plan (`--plan`) [OWNER] | jobs | contents per job | model seconds | what it reads |
|---|---|---|---|---|
| shape | 4 | IPE n = 4 (16 phases) + n = 5 phases 0-15; n = 5 16-31; n = 6 0-31; n = 6 32-63 | 4 x 59.2 = 236.8 | the shape (IPE at n = 4, 5, 6 on one night) |
| n5 | 2 | IPE and textbook n = 5, phases 0-15; the same 16-31 | 2 x 59.2 = 118.4 | n = 5 against its ceiling, IPE against textbook |
| n5n6 | 4 | n5's two jobs; IPE n = 6 0-31; 32-63 | 236.8 | n = 5 both, n = 6 IPE; no n = 4 on the same night |

The workplace proposes `shape`: it is the only plan that holds three n on one night, which the measure below needs.
n5 is the smaller choice if the night is short; it reads the ceiling and the textbook gap at n = 5, not the shape.

Exact values (`python gpu/qpe_long_night.py ideal`, apps.ipe_ideal): IPE noiseless 1 at every n; ceiling C(n) =
0.4706, 0.3792, 0.3065 at n = 4, 5, 6. IPE CZ 8, 10, 12; conditionals 9, 14, 20.

## Verdicts [OWNER]

- Ceiling, per n (the 2026-11-19 words, T3-A / N3): BEYOND THE CEILING (p >= C(n) + 2 SE) / NOT BEYOND; p is the
  share of shots with all n bits right, every phase of that n pooled (over the jobs that hold them).
- Shape (proposed, plan shape): on the log of the share, D_n = ln p(n - 1) - ln p(n) and the acceleration
  a = D_6 - D_5, SE = sqrt(t4^2 + 4 t5^2 + t6^2) with t_n = SE(p_n) / p_n. Words: ACCELERATES (a >= 2 SE), FLAT
  (|a| < 2 SE), SLOWS (a <= -2 SE).
- Beside, not read: the same acceleration on the share itself (p4 - p5 against p5 - p6).
- Plans n5 and n5n6, beside: IPE against textbook at n = 5 (the 2026-11-19 per-shot words, IPE RIGHT MORE OFTEN /
  TEXTBOOK RIGHT MORE OFTEN / NOT SEPARATED).

Why the log (changed after the dry runs, below): under a fixed loss per conditional the share falls faster with n,
but the share itself shrinks, so its absolute drop barely grows (noise c: drops 0.127, 0.136, FLAT on the share).
On the log, a fixed loss per round gives a constant D_n and a fixed loss per conditional adds that loss to D_n per bit
(noise c: 0.190, 0.254, ACCELERATES). The threshold is the usual 2 SE.

Sensitivity (plan shape, if the device repeats 2026-11-19's slope: p about 0.88, 0.84, 0.80 at n = 4, 5, 6):
2 SE of a is about 0.009, so the test can see a per-conditional loss of about 1 % of the log share per conditional.

## Reading table (fixed before the data) [OWNER]

| shape word | ceiling at n = 6 | reading |
|---|---|---|
| FLAT | BEYOND | the classical record stays cheap to n = 6: the loss per added bit is per round |
| ACCELERATES | BEYOND | each feedback costs: the loss per added bit grows with the conditionals, still beyond the ceiling at n = 6 |
| ACCELERATES | NOT BEYOND | each feedback costs, enough to lose the ceiling by n = 6 |
| FLAT | NOT BEYOND | the loss is per round but large: not read for the feedback cost |
| SLOWS | (either) | the loss per added bit shrinks: not read for the mechanism (e.g. a decoder-like saturation) |

All 6 outcomes of the two words (3 x 2) fall on exactly one row.

## Predictions [OWNER] (written before the data)

- QL-1 [OWNER: e.g. IPE BEYOND THE CEILING at n = 4, 5, 6]
- QL-2 [OWNER: e.g. FLAT, or ACCELERATES, or no direction]
- QL-3 (plans n5, n5n6) [OWNER: e.g. IPE RIGHT MORE OFTEN at n = 5]

## Dry runs (illustrative noise, never fitted; `notes/qpe_repro_2026-11-19/noise/illus_*.json`)

Built on the 2026-11-19 marrakesh record with the dry Clifford sentinel; each job dry-run with its own seed
(20261121 + 5,000,000 x job; seeds closer than the shots give the same shots shifted); scored over every job.
Noise a = CZ 1 % and damping 2 % per read (a loss per round); c = a with CZ 0.2 % and dephasing 12 % per
conditional (a loss per conditional).

| plan, noise | n = 4 | n = 5 | n = 6 | log drops | acceleration (2 SE) | word | on the share (beside) |
|---|---|---|---|---|---|---|---|
| shape, a | 0.9465 | 0.9303 | 0.9127 | 0.0173, 0.0191 | +0.0018 (0.0054) | FLAT | +0.0013 (0.0051) FLAT |
| shape, c | 0.7313 | 0.6047 | 0.4689 | 0.1901, 0.2544 | +0.0642 (0.0158) | ACCELERATES | +0.0092 (0.0097) FLAT |
| n5, a | | IPE 0.9292, textbook 0.4012 | | | | | IPE - textbook +0.528, IPE RIGHT MORE OFTEN |

Every n BEYOND THE CEILING in both noises (margins at n = 6: +0.61 in a, +0.16 in c). The measure tells the two
shapes apart in these noises; on the share alone it would not. `check` (noiseless Aer of every arm: ff success 1,
IPE off within 0.03 of exact, floors zero) PASS on every job of every plan.

## Known limits

- The sentinel does not watch the qubits that carry IPE: rule C puts the 2-qubit IPE at the device's corner (qubits
  0, 1 on a Heron), where no ring can pass (qubit 0 has one coupler, qubit 1 two). psf-os after-2026-11-20 offers
  `ring_chains(dev, 2)` (chains on the sentinel's own ring, passed as build's `chains`) and records the cover with
  `sentinel_over_test`; using either changes the test's qubits from 2026-11-19's [OWNER].
- The plan's jobs run at different times of the night; the shape reads three n from four jobs (n = 4 and half of
  n = 5 in job 0). A drift between jobs enters the acceleration (the loopvar test of 2026-11-20 measures that size).
- The textbook circuit is not in plan shape (the night's budget); its gap at n = 5 is in plans n5 and n5n6.
- Illustrative noises only; no device number is fitted or read.

## Decisions at home before declaring ([OWNER] list)

1. The plan: shape (proposed), n5 or n5n6.
2. The shape measure: on the log of the share (proposed) or on the share; the threshold 2 SE.
3. The reading table above, as proposed or changed.
4. Predictions QL-1 .. QL-3, each a direction or "none".
5. Placement: rule C as 2026-11-19 (proposed), or on the sentinel's ring (`ring_chains`).

## Device procedure (home)

```
# psf-os at the declared commit (branch after-2026-11-20 or later); notebook at the declaring commit
python gpu/qpe_long_night.py ideal                                     # ceilings 0.4706 0.3792 0.3065; the plans
for k in 0 1 2 3; do
  python gpu/qpe_long_night.py build DEV OUT$k --plan shape --job $k   # 100 circuits, 59.2 s each
  python gpu/qpe_long_night.py check OUT$k                             # PASS
done
python -m psf_os submit OUT0 ; python -m psf_os collect OUT0           # then OUT1, OUT2, OUT3, as every night
python gpu/qpe_long_night.py score OUT0 OUT1 OUT2 OUT3                 # per n, and the shape word
```
