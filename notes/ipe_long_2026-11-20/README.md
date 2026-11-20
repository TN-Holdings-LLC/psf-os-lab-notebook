# Phase estimation at n = 5, 6: what it would show, and its size (workplace Claude, 2026-11-20; desk, not declared)

Home's improvement candidate 6 ("the IPE - textbook gap grew with n; n = 5, 6 would show where IPE meets its
ceiling"), taken up after the owner's "進めて" on the memory-hierarchy reading: iterative phase estimation keeps one
ancilla and moves each bit to the classical register at once; the textbook circuit holds n counting qubits to the end.
No tool is built for the device yet; the owner chooses the size first (below).

## Exact values (apps.ipe_ideal; branching, no sampling)

| n | IPE noiseless | off as read | ceiling C(n) | IPE conditionals | IPE CZ | textbook CZ (mean, routed on a line) | textbook depth |
|---|---|---|---|---|---|---|---|
| 2 | 1 | 0.750 | 0.7500 | 2 | 4 | 5-15 (12.5) | 26-53 |
| 3 | 1 | 0.500 | 0.5884 | 5 | 6 | 15-39 (34.6) | 57-98 |
| 4 | 1 | 0.324 | 0.4706 | 9 | 8 | 36-80 (73.8) | 102-164 |
| 5 | 1 | 0.209 | **0.3792** | 14 | 10 | 68-138 (129.7) | 162-250 |
| 6 | 1 | 0.134 | **0.3065** | 20 | 12 | 120-222 (211.1) | 260-395 |

IPE's CZ grow by 2 per bit (the controlled phase of each round); its conditionals grow by n - 1 + 1 per bit (the
feedback of every bit already read, and the reset): 2, 5, 9, 14, 20. The textbook circuit is exact noiselessly at
every n (worst phase 1.000000).

## Projection with illustrative noise (`project.py`, `project_n2-6.txt`; noises notes/qpe_repro_2026-11-19/noise, never fitted)

| noise | IPE n = 2 .. 6 | textbook n = 2 .. 6 | IPE margin over C(n) |
|---|---|---|---|
| a: CZ 1 %, damping 2 % per read | 0.98 0.97 0.95 0.93 0.91 | 0.92 0.78 0.59 0.40 0.23 | grows to +0.61 |
| b: CZ 0.3 %, damping 5 % per read | 0.99 0.98 0.96 0.95 0.93 | 0.97 0.93 0.85 0.75 0.63 | grows to +0.62 |
| c: + dephasing 12 % per conditional | 0.95 0.86 0.73 0.60 0.47 | 0.98 0.95 0.90 0.83 0.73 | +0.20 +0.27 +0.26 +0.22 +0.16: peaks, then falls |
| d: dephasing 60 % per conditional | 0.76 0.47 0.27 0.15 0.08 | as c | below C(n) from n = 3 |

## What n = 5, 6 would tell (the device of 2026-11-19 against these shapes)

- 2026-11-19 marrakesh: IPE 0.955, 0.915, 0.880 (drops 0.040, 0.036 per bit); textbook 0.926, 0.845, 0.711 (drops
  0.081, 0.135).
- If what IPE loses comes per round (a CZ pair and a read: noises a, b), its drop per bit stays about flat and it stays
  far beyond the ceiling at n = 5, 6 (a straight line through 11-19 gives about 0.84 and 0.81 against 0.38 and 0.31).
- If it comes per conditional (noise c), the drop per bit grows with n, because each new bit adds one more
  conditional than the one before (3, 4, 5, 6), and the margin over the ceiling peaks and falls.
- So n = 5, 6 read less "where IPE meets its ceiling" (on 11-19's slope that is far beyond n = 6) than **whether the
  classical side's cost grows with the number of feedbacks**: whether the memory-hierarchy split stays cheap as the
  classical record grows. 11-19's two drops (0.040, 0.036) are flat, but two points cannot tell a shape. [a form for
  the owner: e.g. "the drop from n = 5 to 6 is within 2 SE of the drop from 2 to 3" (per round) against "larger by
  more than 2 SE" (per conditional)]
- The textbook circuit at n = 6 (CZ about 210) is expected near or below IPE's ceiling; its share says how far the
  all-quantum memory reaches on the night's device, beside.

## Size (1950 shots as 2026-11-19; 0.036 s per circuit + 0.00027 s per shot per circuit + 3 s per job)

| option | jobs | circuits | seconds by the model |
|---|---|---|---|
| n = 5 IPE and textbook, every phase, phases split in two jobs (32 items each) | 2 | 2 x 100 | 118.4 |
| n = 6 IPE and textbook, every phase, four jobs | 4 | 4 x 100 | 236.8 |
| n = 6 IPE only, two jobs | 2 | 2 x 100 | 118.4 |
| n = 5 both + n = 6 IPE only (the leanest that reads the shape at 5 and 6) | 4 | 400 | 236.8 |

A part of 64 items (196 circuits, 113 s) would pass a 60 s job limit if one is set only by splitting; the 2026-11-19
tool scores every phase of an n inside one job, so the split needs a score that pools phases over jobs (the per-shot
IPE - textbook difference then also spans two jobs unless both halves hold both circuits, as in the options above).
Home's candidate 4 belongs here too: the ring sentinel did not cover the qubits that carried IPE (0-2) on 11-19.

## The next two steps of the plan (sketch only)

- Qubit reuse (2): measure and reset a qubit and use it again within one circuit, so a long 1D chain runs on a few
  qubits; the comparison is the same chain on as many qubits as sites, both against an exact value.
- Constant-depth long-range entanglement (3): already a desk prototype, `notes/ffapps_2026-11-17` part B
  (apps.longrange: Bell pairs at once, Bell measurements at once, the byproduct removed on the last qubit; depth
  20-32 against 31-103 sequential for distance 4-16, ceiling 3/4); built and dry-run on 2026-11-17, never run on a
  device.
