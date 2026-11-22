# Declared: what the branch costs in IPE, cut into the feedback and its wait (one night, off marrakesh)

Home Claude, 2026-11-22, on the owner's choices of 2026-11-22 (20:1x JST: prepare the test; 20:5x JST: plan d, L =
4500 dt with the device's dt recorded beside, no direction declared). Declared when the commit that adds this file is
pushed, before the night's first fetch. The tools are as of that commit; psf-os 0.3.1 as released (v0.3.1, 7caedaa),
park=True and park_likely=True stated by the tool. Tool `gpu/ipe_branch_cost_night.py` (home VS, 8faec3c5 here). The
home VS's draft at this commit (`prereg/drafts-2026-11-23/ipe_branch_cost_DRAFT.md`) gives the Why, the design, the
checks, the known limits and the dry runs, copied below; where this file and the draft differ, this file holds.

## The [OWNER] items

1. **Plan d**: one job at 2950 shots, 68 circuits, 59.6 s by the model: F, S, SD at L and SD at 2 L; n = 6 and 8 at
   the draft's 8 phases each (k · a_n mod 2^n, a_6 = 41, a_8 = 159); one sentinel. Home dry build on the 2026-11-22
   records of ibm_fez and ibm_kingston: 68 circuits, 59.6 s, check PASS on both.
2. **L = 4500 dt** (a placeholder, not a measurement). SD in the verdicts is SD at L; SD at 2 L is beside
   (SD(L) − SD(2 L), the wait's cost per further L).
3. **The device's dt is recorded beside** (`OUT/dt.txt`, read from the backend's configuration at run time: a timing
   constant, not a calibration error number) so that L and 2 L can be stated in microseconds beside. It is used in no
   verdict.
4. **Words and the reading table**: as in the draft (copied below).
5. **Predictions**: none (choice (i)). Both differences are read by the table. The anatomy behind the test was cut
   after the declarations from nights not designed for it.
6. **The device**: the rule of 2026-11-21 (not marrakesh; the shorter queue of fez and kingston; ties by queue.json's
   order).

## Why

The anatomy of the IPE nights (`notes/ipe_anatomy_2026-11-22`) is **beside, after the declarations: hypotheses only.**
It found:

- a first-error hazard that depends on the night and the device: a round 1 → 2 jump of +0.035 on one marrakesh night,
  about +0.01 on another, about +0.03 on fez;
- on two nights, a hazard that grows with the corrections fired;
- on fez, an extra loss at controlled phases near π.

The loss per round can come from two places:

1. **the branch itself:** a conditional costs something beyond the time it takes;
2. **the time waited:** the qubits idle while the classical decision is made.

What 0.4 should try depends on which of the two it is. This test cuts the loss into these two parts.

## Design (one device record; no mitigation; ff arms only; one sentinel)

Three forms of IPE are built on the same phases and the same qubits, side by side in one job:

| form | the phase feedback of round r (r − 1 corrections from earlier bits) |
|---|---|
| **F** | each correction inside a conditional on its bit (the form as it is; psf-os parks the target at each run) |
| **S** | the corrections the right bits call for, applied without a condition (j is known), between two full fences, with the target's parking pair where F's parking puts it |
| **SD** | S with a delay of L × (r − 1) on every qubit, inside the same fences |
| R (beside, plan b) | F with the ancilla's neighbour read at every read (clbits n … 2n − 1, not scored) |

- **The reset is the same in every form:** the ancilla's reset (a conditional X on the bit just read) is kept as in F.
  The forms differ in the phase feedback only.
- **Three qubits in every item:** spectator, ancilla and target on a line. The spectator idles in F, S and SD, so the
  R twin uses the same qubits.
- **Phases:** j_k = k · a_n mod 2^n, k = 1 … K, a_n odd and near 0.618 · 2^n (a_6 = 41, a_8 = 159). Half of them are odd,
  so the anatomy can be repeated per round.
  - n = 6: 41, 18, 59, 36, 13, 54, 31, 8 (K = 8)
  - n = 8: 159, 62, 221, 124, 27, 186, 89, 248 (K = 8)
- **L, one conditional's wait, in the device's dt:**; 4500 dt is a placeholder, not a measurement.
  - **How the length is set:** the compiled F gives the number of waits at each place (`check` counts the round's
    conditionals in the compiled circuit), and L gives each wait's length.
  - **Why L cannot come from the records:** psf-os 0.3.1 has no time per operation, the device records hold no
    durations and no dt, and calibration numbers are not read.
  - **Why dt:** delays are written in dt because qiskit 2.5.2's qpy (the job's circuits.qpy) keeps only dt.

### Plans (the declared row: d)

Sizes use the 2026-11-22 fez record (P 0.5785 at n = 6 and 0.4236 at n = 8).

| plan | content | circuits | shots | s (model) | 2 SE of a difference, per n / mean of the two n |
|---|---|---|---|---|---|
| **a** | F, S, SD; n = 6, 8; 8 phases each | 52 | 3900 | **59.6** | 0.0079 / 0.0056 |
| b | a + R twins at 4 phases per n | 60 | 3350 | 59.4 | 0.0085 / 0.0060 (R: 0.0085) |
| c | F, S, SD; 16 phases per n | 100 | 1950 | 59.2 | 0.0079 / 0.0056 |
| d | F, S, SD at L and at 2 L; 8 phases per n | 68 | 2950 | 59.6 | 0.0091 / 0.0064 |

- Every plan is under 60 s.
- **Plan c** covers more phases at the same precision. Use it if the anatomy should be repeated on more angles.
- **Plan d** reads the wait's cost per further L. Use it if the choice of L is uncertain (see Known limits).

### check (PASS before anything is sent; PASS on ibm_fez and ibm_kingston, every plan)

1. **Noiseless:** every item has all n bits right with probability 1 (exact, psf-os footprint). F, S and SD therefore
   give the same distribution of the scored bits.
2. **Compiled gates:**
   - CZ equal in F, S and SD at every phase (fez and kingston: n = 6 mean 11.25, n = 8 mean 15.25);
   - the X and SX gates outside conditionals and the fences are the same in all three at every phase;
   - F's conditional blocks are counted and reported.
3. **Delays and conditionals:**
   - F's conditionals per run are as built;
   - SD's delays survive compiling and the job's qpy: L × (r − 1) per round, on all three qubits;
   - F and S have no delay.
4. **Build record:** `psf_os_build` reads version 0.3.1, park True (explicit), park_likely True, declared 0.3.1, and
   psf-os parked the target in every item.

### The device

The rule of 2026-11-21 applies: not ibm_marrakesh. Of ibm_fez and ibm_kingston, run on the one with fewer pending
jobs in queue.json; ties go by queue.json's order. Both records build and check.

## Verdicts

P is the share of shots with all n bits right, pooled over the phases of each n. Each difference is averaged over
the two n, with its SE from the per-n SEs.

| difference | what it reads | words (2 SE) |
|---|---|---|
| **SD − F** | the branch beyond its wait | FEEDBACK COSTS (≥ 2 SE, > 0), NO FEEDBACK COST SEEN, FEEDBACK GAINS (≤ −2 SE, < 0) |
| **S − SD** | the wait | WAIT COSTS, NO WAIT COST SEEN, WAIT GAINS |

**Beside, not judged:**

- the per-n values;
- plan d's SD(L) − SD(2 L);
- plan b's F − R (what reading the neighbour costs);
- the anatomy repeated on this night's F (hazard by round, by angle, by corrections fired).

## Reading (every pair on one row; what 0.4 would try)

| SD − F | S − SD | reading | 0.4 tries |
|---|---|---|---|
| FEEDBACK COSTS | WAIT COSTS | both the branch and its wait cost | fewer conditionals: a round's corrections merged into one conditional on the earlier bits (a look-up); the parked wait kept |
| FEEDBACK COSTS | NO WAIT COST SEEN | the branch costs beyond its time | deferring the corrections: applied once, late, from the bits together, or a classical post-correction where the algorithm allows it |
| FEEDBACK COSTS | WAIT GAINS | the branch costs; the idle alone helps (a dynamical effect, not a cost of time) | deferred corrections with a fixed idle, read beside first |
| NO FEEDBACK COST SEEN | WAIT COSTS | the loss is the time waited, not the branch | shorter waits (fewer conditionals), every waiting qubit parked, placement away from slow times |
| NO FEEDBACK COST SEEN | NO WAIT COST SEEN | neither part costs at this n and L | the loss lies elsewhere: the angle-dependent loss seen beside (controlled phases near π) before any control rule |
| NO FEEDBACK COST SEEN | WAIT GAINS | the delay helps, the branch is neutral | not a control rule; the idle as a dynamical decoupling question, beside |
| FEEDBACK GAINS | WAIT COSTS | F keeps more than S + delay although the wait costs: the delay overstates F's wait (L too long) | none before reading plan d's two lengths |
| FEEDBACK GAINS | NO WAIT COST SEEN | not expected noiselessly | check the build; none |
| FEEDBACK GAINS | WAIT GAINS | both reversed | check the build; none |

## Known limits

- **S is not an estimator.** The fixed corrections need j, so S is a probe, not a way to estimate phases.
  - On shots where an earlier bit is wrong, S's corrections are right and F's are wrong.
  - This does not change P (such shots fail either way), but it changes the later rounds' hazards in those shots.
- **L is set by a model, not measured.** SD − F reads the branch only when L equals F's real wait.
  - If L is too short, SD − F holds part of the wait as well; if too long, SD − F can read FEEDBACK GAINS (the
    reading table's row).
  - Plan d's second length gives the wait's slope per L, which shows how much a wrong L moves SD − F.
- **The delay is the same at every place:** L × (number of conditionals), whether they fire or not. A wait that depends
  on firing (section 4 of the anatomy) would show in SD − F.
- **The delay unit:** dt, the device's clock step. The device records do not hold dt, and psf-os does not convert
  units. Whether IBM accepts delays inside these dynamic circuits as written has not been tried.
- **Dry runs cannot test the device's behaviour.** They show the tool separates the two parts when the noise does
  (below), not what the device will do.
- One night, one device, n = 6 and 8, one family of circuits.

## Dry runs (ILLUSTRATIVE noise, written by hand, never fitted; `notes/ipe_branch_cost_2026-11-22/`)

Plan a was built on the ibm_fez record of 2026-11-22 (likely-park fetch_in). Every noise type also has p2 = 0.01
depolarizing on every CZ.

| noise | SD − F (2 SE) | S − SD (2 SE) | words | row |
|---|---|---|---|---|
| per conditional: dephasing 0.02 on every qubit (the branch) | +0.0915 (0.0038) | −0.0014 (0.0031) | FEEDBACK COSTS / NO WAIT COST SEEN | branch beyond its time |
| per wait unit: damping 0.01 and dephasing 0.02 (a conditional, or a delay of L) | +0.0002 (0.0046) | +0.1297 (0.0040) | NO FEEDBACK COST SEEN / WAIT COSTS | time waited |
| both | +0.0749 (0.0049) | +0.1297 (0.0040) | FEEDBACK COSTS / WAIT COSTS | both |

- Each type falls on its own row.
- **Plan d (both noises):** SD(L) − SD(2 L) = +0.1097 (2 SE 0.0057).
- **Plan b (both noises):** F − R = +0.0087 (2 SE 0.0078). No readout crosstalk is modelled here, so this is a chance
  excursion at the edge. It is a warning that the R twin at 4 phases is weak.

## Device procedure (home)

GitHub first (VPN ON), then the device (VPN OFF), as every night. The device step:
```
python gpu/daily_fetch.py OUT/fetch_in
DEV=$(python gpu/ipe_branch_cost_night.py pick OUT/fetch_in)
python -c "from qiskit_ibm_runtime import QiskitRuntimeService as Q; print(Q().backend('$DEV').dt)" > OUT/dt.txt
python gpu/ipe_branch_cost_night.py build OUT/fetch_in/$DEV/dev OUT/bc --plan d --L-dt 4500
python gpu/ipe_branch_cost_night.py check OUT/bc                     # PASS, or stop
python -m psf_os submit --job OUT/bc/job0/job ; python -m psf_os collect --job OUT/bc/job0/job --wait-min 20
python gpu/ipe_branch_cost_night.py score OUT/bc
```
