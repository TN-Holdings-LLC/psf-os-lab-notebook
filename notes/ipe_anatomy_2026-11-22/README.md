# The anatomy of IPE on the device (home VS, 2026-11-22 night; home instruction "IPE の解剖", part A)

**Beside, after the declarations.** Every number here was cut from records after their nights were declared and
scored. None of it is a verdict. The patterns are hypotheses, and only a declared test (part B,
`prereg/drafts-2026-11-23/ipe_branch_cost_DRAFT.md`) can settle them. No declared tool and no file under `results/`
was changed.

## Tools (read only on `results/`)

| file | what it gives |
|---|---|
| `anatomy.py NOTEBOOK OUT.json` | per night, form and n: the first-error hazard h_r with 2 SE; the layer of each round's read; the reads and conditionals before it; beside, the within-n slope of log P on the compiled CZ |
| `angle.py RESULTS JOB...` | per (phase, round): the round's controlled-phase angle as a fraction of a turn, f = (j 2^m mod 2^n) / 2^n, and that round's hazard; the highest hazards; the hazard binned by \|f − 1/2\| |
| `fired.py RESULTS JOB...` | the hazard by the number of corrections that fire when the earlier bits are right, also at a fixed number of conditionals present |

- **Hazard:** h_r = P(round r wrong | every earlier round right). Round 1 reads clbit n − 1; round r holds r − 1
  feedback conditionals.
- **Odd phases:** pooled over odd phases, where every round is non-trivial.
- **Control nights:** the two controls ran phases 2, 6, 10, 14 only. For them the tool falls back to the phases with
  one trailing zero, where round 1 is trivial (its hazard is the read alone), and gives the 2 → 3 step in place of
  the 1 → 2 jump.
- **The unparked twins of 2026-11-21:** they ran four phases per n, none odd, so their rows use the fewest trailing
  zeros present (tz = 1, 2, 3). Their early rounds are trivial and the row says so.

`anatomy.txt` and `anatomy.json` hold every row.

## What the table shows (hypotheses)

### 1. The round 1 → 2 jump is not the same across devices and nights

| night | form | n | jump h2 − h1 |
|---|---|---|---|
| 11-19 marrakesh | unparked | 2, 3, 4 | +0.007, +0.016, +0.020 |
| 11-21 weekend marrakesh | unparked | 5, 6 | +0.010, +0.011 (C pl n = 4 +0.011) |
| 11-21 weekend marrakesh | fenced \|1> | 4 | +0.003 |
| 11-21 weekend marrakesh | parked | 4 | −0.005 |
| 11-21 parked night, marrakesh | parked | 4, 5, 6 | +0.037, +0.035, +0.036 (h2 = 0.061 at every n) |
| 11-22 fez | parked | 6, 7, 8 | +0.029, +0.033, +0.034 |
| 11-22 fez | unparked | 6, 7, 8 | +0.037, +0.031, +0.042 |

- The weekend's parked n = 4 and the 11-21 parked night's n = 4 are the same circuits on the same device:
  - weekend: h = 0.026, 0.022, 0.016, 0.016;
  - parked night: h = 0.024, 0.061, 0.041, 0.039.
  So the jump depends on the night.
- **Controls** (round 1 trivial, so the 2 → 3 step is given instead):
  - fez, RUS-fence night: rounds 2–4 at 0.09–0.11 in both forms;
  - kingston: rounds 2–4 at 0.02 parked, 0.03–0.05 unparked.

### 2. Within a night, the same round has the same hazard at every n

- 11-21 parked night: round 2 is 0.061 at n = 4, 5, 6.
- 11-22 fez, parked: rounds 1–5 are within about 2 SE of each other across n = 6, 7, 8.
- The loss sits with the round, not with the length of the circuit after it.

### 3. The fez peak is not tied to a round number or a layer

- **Round 6 on fez, parked:**

  | n | h6 | layer of the read | conditionals before |
  |---|---|---|---|
  | 6 | 0.123 | 116 | 20 |
  | 7 | 0.110 | 116 | 20 |
  | 8 | **0.149** (unparked 0.203) | 116 | 20 |

  The read sits at the same place at every n, yet the peak appears at n = 8 only.
- **Read layers:**
  - parked: 11, 30, 50, 71, 93, 116, 140, 165;
  - unparked: 11, 27, 44, 62, 81, 101, 122, 144.
- **What it does follow is the phase.** Round 6 at n = 8 reads clbit 2, and the highest per-round hazards on fez all
  have f = 0.4844, a controlled phase just short of π:
  - j 62 round 7, j 159 round 6, j 31 round 6, j 124 round 8: hazards 0.30–0.32, in both forms.
  - Binned over every non-trivial round after the first:

    | \|f − 1/2\| | hazard |
    |---|---|
    | [0, 0.02) | 0.123 |
    | [0.02, 0.05) | 0.200 |
    | [0.05, 0.15) | 0.109 |
    | ≥ 0.15 | about 0.10 |
- Marrakesh 11-21 shows no such pattern (0.037–0.057).

### 4. On two nights the hazard grows with the corrections that fire

The count is of corrections that fire (earlier bits that are 1) when the earlier bits are right.

| record | hazard by corrections fired |
|---|---|
| fez 11-22, parked | 0.091 (0), 0.094, 0.105, 0.116, 0.134, 0.231 (5) |
| marrakesh 11-21, parked night | 0.027 (0), 0.042, 0.050, 0.054, 0.068 (4) |
| marrakesh 11-21, weekend | 0.049 at 0, then about 0.03 |

- At a fixed number of conditionals present, the growth remains:
  - marrakesh 11-21: steady (e.g. 5 present: 0.035 → 0.073);
  - fez: mostly at the highest counts (5 present: about 0.11–0.13, then 0.307 with all 5 fired).
- The weekend record does not show it.
- **The firing count and the angle are not independent:** both follow the bits of j. This table cannot separate them.

### 5. The cost of a CZ within one n is larger on fez

- fez 11-22, parked: −0.035 to −0.053 in log P per compiled CZ.
- marrakesh: −0.008 to −0.024.
- The unparked fez rows have 4 phases each; their slope (+0.011 at n = 8) is not read.

## Time

The instruction asks for each wait's position in microseconds. That cannot come from the records:

- psf-os 0.3.1 has no time per operation (its model is per job, circuit and shot);
- the device records hold no durations;
- calibration numbers are not used.

So the position is given as the layer and as the reads and conditionals before each read. Those two counts are
enough to separate "tied to the round" from "tied to the place in the circuit" (section 3).

## What part B can and cannot settle

- **Can:** the declared test cuts the loss into the branch (F against S plus a delay) and the wait (S plus a delay
  against S), on phases that include odd ones, so this anatomy can be repeated on declared data.
- **Cannot:** the angle pattern (section 3) and the firing pattern (section 4) are not what B tests. B's phases keep
  both (k · a mod 2^n) but do not separate them.
