# Ohm on the wall's light-cone window, twins in one job, raw (Heron), 2026-11-23

Declared by home (2026-11-23), from the home VS's draft (`prereg/drafts-2026-11-23/ohm_window_night_DRAFT.md`, 89a5715a)
and the owner's choices of 2026-11-23:
- 13:4x CET: plan B, the twins, t = 1 and 3, three arms, 7 pairs; about 50 s (floor and mirror on a few items only,
  1000 shots); the window's M and W judged, W(t) / W(1) beside, no fractional gates;
- 14:5x CET: the first 7 pairs; the light-cone circuits pinned to the 40-qubit circuit's physical qubits (in the tool
  only, psf-os unchanged); no run if neither device builds; floor and mirror on A1 s00 only (4 items); one prediction
  (OW-1); run tonight.

The desk design is `notes/ohm_readable_2026-11-23`; the try-builds are `notes/ohm_window_try_2026-11-23`. This file is
declared when its commit is pushed, before the night's first fetch. Tools: `gpu/ohm_window_night.py` as of the declaring
commit, with psf-os 0.3.3 (a45c54a, tag v0.3.3; released 2026-11-24). A change after the push is a new declared file.

## Question

On the 11-12 Ohm circuits, at 1 and 3 cycles, does the device read the transfer across the wall when it is summed over
the wall's light-cone window instead of the whole right half? Does the order of the three arms show in it? And, at the
same layers, does a circuit made only of the window's backward light cone (fewer qubits, fewer CZ, the same physical
qubits) keep more of it than the 40-qubit circuit?

## Circuits (`gpu/ohm_window_night.py`, on `gpu/ohm_answers.py`)

- The 11-12 circuits (`prereg/ohm_2026-11-12.md`): 40-qubit chain, fSim(pi/4, phi) brickwork from a weakly polarised
  wall (m 0.5).
  - A0: phi 0.
  - A1: phi pi/2.
  - A2: phi pi/2 with RZ(H p_k) after each cycle, p = (1, -1, 0), H 1.
- Strings: the first 7 pairs of the 11-12 strings (seed 20261112, K 14): s00-s06 and their complements c00-c06.
- Cycles t = 1 and 3. The window is the 2t - 1 chain sites next to the wall (positions 20 .. 20 + 2t - 2): 1 site at
  t = 1, 5 at t = 3.
- Twins, every (arm, t, string) built twice in the same job:
  - **F**, the 40-qubit circuit. The chain is chosen as `gpu/ohm_build.py` chooses it (daily/du91 shapes, then psf-os
    rule C), and psf-os's user entrance places it.
  - **L**, the light-cone circuit: only the qubits and fSim gates of the window's backward light cone. That is 4 qubits
    (chain positions 18-21) at t = 1 and 16 (14-29) at t = 3. It sits on F's physical qubits at the same chain
    positions.
  - The light-cone items are offered only the copy that is F's qubits. psf-os's own qualification check of that copy
    runs, and the build refuses if it fails. This is an override for this job only, in the tool; psf-os is not
    changed. Without it, psf-os put the 4-qubit cone at another copy on the 11-22 fez record. The owner accepted this
    override (2026-11-23).

Compiled (try-build), with the CZ count checked against intended = 2 (A0) or 3 (A1, A2) x fSim:

| t | twin | qubits | CZ: A0 / A1, A2 | CZ layers: A0 / A1, A2 |
|---|---|---|---|---|
| 1 | L | 4 | 6 / 9 | 4 / 6 |
| 1 | F | 40 | 78 / 117 | 4 / 6 |
| 3 | L | 16 | 66 / 99 | 12 / 18 |
| 3 | F | 40 | 234 / 351 | 12 / 18 |

- A1 and A2 are equal in CZ and CZ depth (the build refuses otherwise).
- The twins have the same CZ layers; L has fewer qubits measured and fewer CZ.
- psf-os 0.3.3 with its park default unchanged. No sent circuit has a mid-circuit measurement or a delay, so nothing is
  parked; the build checks and records this.

## Job and seconds

- Items: 3 arms x 2 t x 14 strings x 2 twins = 168 user circuits.
- Floor and mirror (psf-os's user entrance; the mirror from the compiled circuit, as `gpu/ohm_build.py`) only for A1,
  string s00, at each t and twin: 4 items, 8 circuits. The other items are built and accepted by psf-os as usual, and
  their floor and mirror records are not sent (`OUT/unsent_runs`).
- One ring sentinel (4 circuits).
- **180 circuits, 1000 shots: 2.6 + 0.000269 x 180 x 1000 = 51.0 s** (the usual formula). psf-os's own model gives 58.1 s
  (limit 60 in the tool).
- No placeholder carries a physical unit and no circuit holds a delay, so rules 1 and 2 of `prereg/README.md` do not
  apply.

## Device and placement (no quality number)

- Right before the fetch, read the pending jobs. Not ibm_marrakesh.
- Of ibm_fez and ibm_kingston, the one with fewer pending; a tie goes to the queue file's order (`gpu/ohm_window_night.py
  pick QUEUE.json`).
- If the chosen device does not build, the other. If neither builds, no run.
- Try-builds on the newest records in this notebook (`results/ipe-branch-cost-night-2026-11-22/fetch_in/`, 11-22 12:56
  CET):
  - ibm_fez: chain shape S1, F at copy drow 4;
  - ibm_kingston: chain shape S1, F at copy drow 0;
  - both: 180 circuits, 51.0 s, every L item on F's physical qubits.

## Answers (sealed)

- `gpu/ohm_window_night.py answers`: per-qubit <Z> of every item, by chain position.
  - A0's 40-qubit circuits by free fermions.
  - The rest by quimb CircuitMPS (chi 2048, cutoff 1e-10).
- `ohm_window_answers.json` sha256 **216d6b960c927df4ab9c41ab87180a7f55a7005f04448217a1efece4f6787a11** (home VS, 36 s
  on the CPU). The build writes them by tag and label.
- Checks printed (no values):
  - L's window against F's: 7.3e-15;
  - A0 quimb against free fermions: 3.4e-15;
  - |total Z - initial| on F: 5.3e-15.
- The 40-qubit t = 3 answers of these strings were released with the 11-12 results, so they are public. L's window at
  t = 3 equals F's. The new answers are t = 1 and L's other qubits.

## Pre-run check (before submission): `gpu/ohm_window_night.py check OUT ANS`

- Runs on the job's own compiled circuits, noise-free (Aer: statevector up to 12 qubits, MPS above).
- Every circuit's per-qubit <Z> is within 1e-6 of the answers.
- The 4 mirrors read all zeros (1e-6).
- The twins' windows are equal within 1e-6.
- FAIL anywhere: not run.
- Try-builds: ibm_fez ALL PASS and ibm_kingston ALL PASS (worst 1.6e-10; mirrors 2.6e-14; twins' windows 5.7e-11;
  6 s each).
- If the job built from the fresh record has the try-build's circuits_sha256, the PASS carries over. Otherwise the check
  is run on the new build before submission.

## Verdicts (`gpu/ohm_window_night.py score OUT ANS`)

M_w, the window's transfer of one circuit, is the sum over the window of (1 - z) / 2, minus the string's own count of 1
there, in quanta. For L and F alike it is compared with the exact value of the same circuit.

1. **Window M**, per arm, t and twin (12 cells), over the cell's 14 circuits: READS if the mean squared difference of
   M_w is at most half the mean square of the exact M_w (the 11-12 rule); otherwise DOES NOT READ.
2. **Window W**, per arm, t and twin (12 cells). W_k = (M_w(s_k) - M_w(c_k)) / 2 per pair, over the 7 pairs: READS if
   the mean squared difference of W_k is at most half the mean square of the exact W_k; otherwise DOES NOT READ.
3. **Twins**, per arm and t (6 cells). Per string, take the squared M_w error of F minus that of L; the mean over the
   14 strings with its standard error (their spread / sqrt 14):
   - the light-cone circuit **KEEPS MORE** if the mean exceeds +2 SE;
   - **KEEPS LESS** if it is below -2 SE;
   - **SAME** otherwise.
4. **Order at t = 3**, per twin: the device's mean W at t = 3 is A0 > A1 > A2, yes or no.

Beside, never judged, never used to correct:
- W(3) / W(1) per arm and twin, device and exact;
- S = mean of M_w(s) + M_w(c);
- floor and mirror means of the 4 items;
- the sentinel;
- CZ.

## Reading table

Per cell (verdicts 1 and 2):

| window M | window W | reading |
|---|---|---|
| READS | READS | each circuit's transfer and the wall's transfer both read in this cell |
| READS | DOES NOT READ | the circuits read but the string-minus-complement difference does not |
| DOES NOT READ | READS | the difference reads (the bias common to s and c cancels) while single circuits do not |
| DOES NOT READ | DOES NOT READ | neither reads in this cell |

Twins (verdict 3), per arm and t:

| twins | reading |
|---|---|
| KEEPS MORE | at equal layers, the circuit of the window's light cone alone keeps more of the window's transfer |
| SAME | at equal layers, cutting the qubits and CZ outside the light cone makes no difference beyond 2 SE |
| KEEPS LESS | the 40-qubit circuit keeps more; cutting the outside does not help here |

Order at t = 3 (verdict 4):

| L | F | reading |
|---|---|---|
| yes | yes | the arms' order shows in both twins |
| yes | no | the order shows only in the light-cone circuit |
| no | yes | the order shows only in the 40-qubit circuit |
| no | no | the order does not show at t = 3 |

Together, at t = 3: verdict 1 on F in how many arms, against verdict 3 (the twins). This is read per arm too.

| window M on F at t = 3 | twins at t = 3 | reading |
|---|---|---|
| READS in all three arms | KEEPS MORE (any arm) | the window reads on the 40-qubit circuit, and the light cone alone keeps more |
| READS in all three arms | SAME in all | the window reads; cutting the outside adds nothing at this size |
| READS in all three arms | KEEPS LESS (any arm) | the window reads; the 40-qubit circuit keeps more where it says so |
| READS in one or two arms | KEEPS MORE (any arm) | the window reads in part; the light cone helps |
| READS in one or two arms | SAME in all | the window reads in part; cutting adds nothing |
| READS in one or two arms | KEEPS LESS (any arm) | the window reads in part; cutting costs |
| READS in no arm | KEEPS MORE (any arm) | the 40-qubit window does not read; the light cone keeps more (see L's verdict 1) |
| READS in no arm | SAME in all | the window does not read at t = 3, with or without the outside |
| READS in no arm | KEEPS LESS (any arm) | the window does not read, and cutting costs |

## Prediction (before any data; not rewritten if wrong)

- **OW-1: at t = 3, the window's M READS on F (the 40-qubit circuit) in all three arms.** Held if verdict 1 is READS for
  F at t = 3 in A0, A1 and A2; failed otherwise (including no run).
  - Basis: the 11-12 F circuits are these same circuits. On the first 7 pairs, the window M ratios were 0.010 / 0.024 /
    0.063 (fez) and 0.013 / 0.035 / 0.047 (kingston), A0 / A1 / A2.
  - The window measure was thought of **after those records were seen** (`notes/ohm_idle_2026-11-23`, section 4); this
    prediction asks whether it repeats on a new day.
- Not declared (owner, 2026-11-23): the window's W reading on F, and the order at t = 3. No prediction for t = 1, for L
  or for the twins (no record of a light-cone circuit exists).

## Device procedure (home)

GitHub first (VPN ON): push this declaration. Then the device (VPN OFF), from a fresh worktree of the notebook at the
declaring commit, with psf-os 0.3.3 (a45c54a) on PYTHONPATH and the sealed answers file outside the repository:
```
python gpu/daily_fetch.py OUT/fetch_in
DEV=$(python gpu/ohm_window_night.py pick OUT/fetch_in/queue.json | cut -d' ' -f1)
python gpu/ohm_window_night.py build OUT/fetch_in/$DEV/dev OUT/ow ANSWERS_SEALED OUT/ow_answers
python gpu/ohm_window_night.py check OUT/ow OUT/ow_answers                 # ALL PASS, or stop
python -m psf_os submit --job OUT/ow/job ; python -m psf_os collect --job OUT/ow/job --wait-min 20
python gpu/ohm_window_night.py score OUT/ow OUT/ow_answers
```
If the chosen device does not build, the build is run on the other device's record; if neither builds, no run.

## Limits

- One device-day. Raw values only.
- 7 pairs, so W is that of these strings.
- At t = 1 the three arms are equal by construction (the field acts after the cycle), so t = 1 tells nothing about
  the arms. It is the common reference beside (W(3) / W(1)).
- The window M is a different quantity from the 11-12 declared M. The window also exchanges 1s through its far edge,
  and its exact value is computed per circuit.
- The window idea and the candidates come after the 11-12 records were seen. F at t = 3 repeats those circuits (on a
  new day, with 7 of the 14 pairs).
- The twins share their physical qubits and their layers. They differ in qubits measured, CZ, and spectator qubits.
  A difference between them does not say which of these makes it.
- Floor and mirror on 4 items only. Per-circuit readout and return are not measured on the others.
