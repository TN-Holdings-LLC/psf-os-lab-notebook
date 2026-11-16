# Declared: does real-time control bring a chain of repeat-until-success neurons on Heron closer to its exact value than the same circuit without control?

Home Claude, 2026-11-16 (owner 19:32 JST "やる", on the proposal: judge ff against the off arm of the same job,
theta 1.1, L = 1-3, m = 3). Declared with this commit, pushed before the device records of the run are fetched; a
change after the push is a new declared file. Desk work: `notes/feedforward_2026-11-16/` (`rus_neuron_desk.py`,
`psfos_rus.md`, `RUS_NOISE_DESK.md`).

## Why the verdict compares two arms of one job

The teleport test of the same day (`results/feedforward-2026-11-16`) judged the ff arm against a bound taken from the
noiseless circuit. On the device the arm without control also came out above that line at k = 1 (0.7935 against
0.7637), consistent with decay toward |0>, which there pointed at the success outcome. Here the verdict is ff against
off of the same job, the same layout and the same night, so a bias that moves both arms moves both. The target value
of this test is P(last output 1), high at theta 1.1; decay toward |0> lowers both arms, and the ff arm, with more
gates and mid-circuit waits, at least as much.

## Circuits and job

psf-os branch `feedforward-2026-11-16` (commit 32dc3e5; `psf_os/feedforward.py`): `rus_chain(L, 1.1, m=3)` for
L = 1, 2, 3, written for IBM's dynamic circuits (conditional blocks of gates only; each try's measurement after its
block; no nesting). Built by `python gpu/rus_night.py build DEVDIR OUT` (without the flag `--dry-clifford-sentinel`,
which is for dry runs only). One job: per L the arms ff (the circuit), off (the conditional blocks removed, the try
measurements kept) and floor (the compiled ff circuit without sx and x, also inside blocks; ideal every bit 0); one
ring sentinel. Placement by rule C (coupling graph and failed marks only). 4000 shots, no mitigation, dynamical
decoupling and twirling off. 13 circuits, 17.5 s by the model (which leaves out mid-circuit measurement and
feed-forward time).

## Device

The night's device by the standing rule (`gpu/daily_fetch.py`: every device of ibm_marrakesh, ibm_fez, ibm_kingston
with at most 10 pending jobs, else the fewest); when several qualify, the first in that order. One device only. The
records are fetched after this file is pushed.

## Pre-run check (before submission)

`python gpu/rus_night.py check OUT`: noiseless Aer of every arm but the sentinel. ff and off within 0.03 of the desk's
noiseless P(last output 1) (ff 0.919 / 0.849 / 0.781, off 0.793 / 0.634 / 0.502 for L = 1 / 2 / 3); floor all zeros
in every shot. FAIL: the job is not run. On the 2026-11-16 marrakesh record (try-build, before this commit): PASS
(ff 0.918 / 0.850 / 0.790; off 0.792 / 0.628 / 0.512; floor 1.000). The whole chain build, check, noiseless run,
score with the dry-run sentinel on the same record: CLOSER WITH CONTROL at L = 1, 2, 3 (d 0.117 / 0.225 / 0.290).

## Answers

The exact value comes from the circuit, not from data: P(last output 1) = (sin^2 q)^L with tan q = tan^2 theta:
0.9371 (L = 1), 0.8782 (L = 2), 0.8230 (L = 3). Even noiselessly the ff arm with 3 tries sits below it by the share
still failing after 3 tries (-0.02 to -0.03).

## Verdict (`python gpu/rus_night.py score OUT` as of the commit that carries this sentence; unchanged after it)

Per L in {1, 2, 3}, from the job's raw counts, every shot of the ff and off arms counted, none discarded, no corrected
value used: P = share of shots with the last output bit 1;
d = |P_off - exact| - |P_ff - exact|; SE_d = sqrt(P_ff (1 - P_ff) / N + P_off (1 - P_off) / N);
**CLOSER WITH CONTROL** when d >= 2 SE_d; otherwise **NOT CLOSER**.

## Predictions (written before the data)

1. L = 1: CLOSER WITH CONTROL.
2. L = 2: CLOSER WITH CONTROL.
3. L = 3: CLOSER WITH CONTROL.

Basis: the circuit (off's error at L = 1 is the failed share times (0.5 - exact), and grows with L) and the
workplace's illustrative noise model (`RUS_NOISE_DESK.md`, not fitted to any device: d / 2 SE_d at m = 3 about 7, 9,
11). Each prediction holds or fails as a whole; a failed one is reported as failed.

## Reported beside (never judged, never used to correct)

P_ff - exact and P_off - exact in SE; ff's share still failing after 3 tries; the post view (the off arm's shots whose
every first try succeeded: kept share, discarded shots, P; biased by construction for L >= 2); the floor's all-zero
share and per-bit share of 1; the sentinel; the success split by the try bits.
