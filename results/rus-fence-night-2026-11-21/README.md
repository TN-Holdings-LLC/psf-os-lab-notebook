# The RUS chains' fence and parking the likely value, 2026-11-21 on ibm_fez (`prereg/rus_fence_night_2026-11-21.md`)

- Declared in 3cf00493, pushed by the owner before the night's first fetch (14:29:46 CET). Run on the owner's machine
  (`versions.txt`: Python 3.12.13, qiskit 2.5.2, aer 0.17.2, runtime 0.49.0, numpy 2.5.3) from a fresh worktree at
  3cf00493 with psf-os 0.3.0 as released (v0.3.0, 2b8e2c4), both checked clean and the version checked (PRE_OK).
  The owner's `git worktree add ~/psfos_v030 v0.3.0` reported the folder already there; the preflight found it at
  2b8e2c4 and clean.
- **The first night off ibm_marrakesh.** `fetch_in/queue.json`: pending marrakesh 0, fez 0, kingston 0; the rule (not
  marrakesh; the shorter queue of fez and kingston, ties by queue.json's order) -> **ibm_fez**, calibration 2026-11-21
  14:12:00+01:00.
- Built as declared (`--plan gamma-one-job`); check PASS (`rf/check.txt`): per RUS item the three forms' compiled
  distributions equal, CZ equal (33 / 33 / 33; P3 22), the fences kept (F 8-15, M 10-22), M's X kept (6-30 more
  one-qubit gates); `psf_os_build` 0.3.0, park True, explicit; both controls' declared checks PASS.
- Scored by the declared tool on the owner's machine (`rf/score.txt`, `rf/rusfence_scores.json`); re-scored at home
  (aer 0.18.0): the same text.

| job | folder | id | circuits | shots | s model | s charged | RU | created - finished (CET) |
|---|---|---|---|---|---|---|---|---|
| job0 | `rf/job0/` | dc0pq2eq4uuc73a2vcl0 | 84 | 1950 | 50.2 | 48 | 0.784 | 14:30:50 - 14:32:31 |

## RUS items (P read as declared; nearer to exact is better; g of a difference as the loop reads it)

| item (copies) | D default | F fenced | M fenced + likely value parked | exact | fence F - D (2 SE) | park M - F (2 SE) |
|---|---|---|---|---|---|---|
| P0 L3 (7) | 0.6604 | 0.6151 | 0.6291 | 0.8230 | -0.0453 (0.0116) KEEPS LESS | +0.0140 (0.0117) KEEPS MORE |
| NF m3 L3 (3) | 0.6181 | 0.6097 | 0.6974 | 0.8230 | -0.0084 (0.0180) SAME | +0.0877 (0.0175) KEEPS MORE |
| P2 m3 L3 (7) | 0.7122 | 0.7042 | 0.7094 | 0.8230 | -0.0080 (0.0110) SAME | +0.0051 (0.0110) SAME |
| P3 L3 (3) | 0.6294 | 0.6051 | 0.6072 | 0.8230 | -0.0243 (0.0180) KEEPS LESS | +0.0021 (0.0181) SAME |

- **Reading (the declared table): P0's fence KEEPS LESS and NF's parking KEEPS MORE -> row 1, "damping dominates the
  waits"** (the desk's wait type: the fence costs on P0, parking gains).
- **Next step for psf-os (row 1; the gate open, the control KEEPS MORE):** 0.3.1: "park the likely value" a default
  candidate; do not fence RUS-like chains by default.
- Beside, never read for the row: P2's fence SAME (the desk expected + under damping and dephasing alike: not seen);
  P3's fence KEEPS LESS and its parking SAME; P0's parking KEEPS MORE too.
- Beside, from the table, never judged: M against D, the form a default would send today: NF +0.079, P0 -0.031, P3
  -0.022, P2 -0.003. Parking the likely value gains on top of the fence, but the full fence it is built on costs on
  P0 and P3; a default that parks without fencing every qubit is a desk question for 0.3.1, not answered tonight.
- The excited count while waiting (record only; the draft's table, the kingston record): NF 23.35 / 16.15 / 4.54, P0
  13.52 / 10.19 / 8.91. NF, whose count parking cuts most, gains most; whether the differences follow the counts is not
  judged.

## Controls (same job)

- **IPE n = 4 at phases 2, 6, 10, 14: parked 0.7172 - unparked 0.6881 = +0.0291 (2 SE 0.0146) KEEPS MORE.** Parking
  the always-|1> target keeps more on a second device too (marrakesh: +0.0387, +0.0349).
- **Repetition code**: footprint F6P - F10 +0.0283 (2 SE 0.0094) KEEPS MORE; CZ F6 - F6P +0.0108 (2 SE 0.0085) KEEPS
  MORE; **F6 0.9294 (2 SE 0.0058) BEYOND THE CEILING** (0.875). The first time a form of the repetition code passes
  its ceiling (marrakesh, 2026-11-21: F6 0.8741, NOT BEYOND). Beside, by the two differences: F6P 0.9186, F10 0.8903.
  Another device, another calibration; across devices nothing is compared.

## Against the declaration

| prediction | numbers | |
|---|---|---|
| RF-1 the IPE control KEEPS MORE | +0.0291 (2 SE 0.0146) | held |

RF-2 and RF-3: no direction declared; read by the table (NF's parking KEEPS MORE; P0's fence KEEPS LESS).
Predictions over the nights of 11-16 to 11-21: 65 declared; 45 held, 20 failed.

## Two numbers side by side

- Vanity: the repetition code's F6 beyond its ceiling (0.929 against 0.875); parking the likely value +0.088 on NF.
- Essence: on a second device, in one job of 48 s, two of paper 11's rules hold (parking the always-|1> target +0.029;
  fewer carriers +0.028 and fewer CZ +0.011), and the RUS chains' waits read as damping: parking the
  likely value gains, the full fence costs. What a default should send for RUS chains is not settled by this night.

## Reproduce

`python reproduce.py --psf-os <psf-os 0.3.0> rus-fence-night-2026-11-21` (1 of 1 SAME at home).
