# DRAFT (not declared): iterative phase estimation reproduced at n = 2, 3, 4, with the textbook circuit beside, night of 2026-11-19 (workplace Claude, 2026-11-18)

Owner's "1" and home's supplement of 2026-11-18. A draft: every verdict word, threshold, shot count and prediction
marked [OWNER] is the owner's; the declaration is written and pushed at home. Tool: `gpu/qpe_repro_night.py` (ideal /
build / check / dry / score). Design, size and dry runs: `notes/qpe_repro_2026-11-19/README.md`.

## Common

- psf-os [OWNER: feedforward-2026-11-16 at 0f57c76, or the v0.2 branch of tonight; the tool's circuits are byte for
  byte the same with both (the workplace's rebuild of 2026-11-18 / 19)]. Device by the standing rule [OWNER: order, e.g. ibm_marrakesh,
  ibm_fez, ibm_kingston, the first qualifying]; one device record for both jobs.
- Rule C placement (coupling graph and failed marks only); no mitigation; dynamical decoupling and twirling off;
  [OWNER: 2000] shots per circuit; every shot counted. No device error number is read. Conditional items are not
  packed. Each job's `check` before submission; a FAIL means that job is not run.

## What is run (two jobs)

- Job A (`--part A`): n = 2, 3. Job B (`--part B`): n = 4. Every phase phi = j / 2^n, j = 0 .. 2^n - 1.
- IPE item `ipe{n}_{j}` (notes/ffapps_2026-11-17 `apps.ipe`): ancilla and target |1>, U = P(2 pi phi); bits read least
  significant first, the phase feedback of every bit already read, a conditional-X reset; ff, off (feedback removed,
  reset kept) and floor arms.
- Textbook item `tqpe{n}_{j}`: n counting qubits and the target, controlled phases and the coherent inverse QFT, routed
  on a line by the fixed rule of notes/rus_coherent_2026-11-17, final measurements only; ff, off (the same circuit: a
  replicate, beside) and floor arms.
- One ring sentinel per job. Size at 2000 shots: A 76 circuits 46.8 s, B 100 circuits 60.6 s by the model (B is
  0.6 s over a 60 s job limit if one is set; 1950 shots give B 59.3 s and A 45.6 s) [OWNER: shots].

## What is read (`score OUT_A OUT_B`), per n, within one job

- IPE: p = share of shots with all n bits right, every phase pooled; 2 SE from the pooled shots.
- Textbook: q, the same share for the textbook ff arm.
- C(n), the ceiling: the best fixed decoder of the off arm's bits, noiseless and exact: C(2) 0.7500, C(3) 0.5884,
  C(4) 0.4706.

## Verdicts (two yardsticks, separate words)

1. Ceiling, per n: **BEYOND THE CEILING** when p >= C(n) + 2 SE, otherwise **NOT BEYOND** (the words of T3-A and N3).
2. Per shot, per n, d = p - q with SE_d = sqrt(SE_p^2 + SE_q^2): [OWNER words] **IPE RIGHT MORE OFTEN** when d >= 2
   SE_d (d > 0), **TEXTBOOK RIGHT MORE OFTEN** when d <= -2 SE_d (d < 0), otherwise **NOT SEPARATED**. The textbook
   circuit has no ceiling (it reads every phase exactly without noise); this yardstick is the share of right answers
   per shot without correction, not a ceiling claim.

Beside, never judged: the margins p - C(n) across n (two jobs), d across n, the IPE off arm as read, the textbook
replicate arm, per-phase shares, floors, CZ and depth per item, the sentinel, the jobs' execution times.

## Predictions [OWNER] (written before the data)

- Q-1 [OWNER] At each n = 2, 3, 4, IPE is BEYOND THE CEILING. (Basis: T3-A fez n = 2 0.861 and n = 3 0.772, N3
  marrakesh n = 4 0.903, against 0.750 / 0.588 / 0.471.)
- Q-2 [OWNER] The per-shot yardstick: a direction, or none declared. The workplace has no basis for a direction: the
  dry runs read either way depending on what a conditional costs against a CZ (`notes/qpe_repro_2026-11-19/dry/`),
  and that is what tonight's timing test begins to measure. If tonight's timing gives a decision latency, the owner
  may set Q-2 from it before this is declared.

Each prediction holds or fails as a whole; a failed one is reported as failed.

## Reproduce

`python gpu/qpe_repro_night.py score OUT_A OUT_B` from the recorded jobs gives the same `qpe_scores.json`; `build`
with the recorded device record, part and shots gives the same circuits.
