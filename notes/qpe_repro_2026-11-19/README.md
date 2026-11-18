# Phase estimation reproduced and compared with the textbook circuit (workplace Claude, 2026-11-18; desk only, not declared)

Owner: "1" (of the reproduction candidates: the iterative phase estimation of Corcoles et al. with dynamic circuits,
with the textbook phase estimation beside). Home's supplement (職場クロードへの補足_位相推定の比較_2026-11-18):
two yardsticks with separate words; to run on the night of 2026-11-19; draft in `prereg/drafts-2026-11-19/`.
Tool: `gpu/qpe_repro_night.py`. Branch from 16d14fc8 (tonight's declarations unchanged; new files only). psf-os
unchanged (0f57c76).

## What the paper did and what is reproduced

Corcoles et al., "Exploiting dynamic quantum circuits in a quantum algorithm with superconducting qubits", PRL 127,
100501 (2021), arXiv:2102.01682 (read from the arXiv text; the supplement was not read): two transmons, the phase of
an eigenstate read one bit per sub-circuit with feed-forward of the earlier bits, up to 10 bits, random phases; the
baseline was **Kitaev's non-adaptive phase estimation** (separate circuit families per bit, classical
post-processing), compared at equal numbers of measurements; IPE was ahead below about 100 measurements per estimate.

Here: the same algorithm in the form of notes/ffapps_2026-11-17 (ancilla + target |1>, U = P(2 pi phi), phi = j / 2^n
for every j, so every phase is exact and the answer is known), n = 2, 3, 4 on one device in one night, and beside
each n the **textbook** circuit (n counting qubits, coherent inverse QFT; not the paper's baseline). Already on the
device: T3-A (fez, n = 2: 0.861, n = 3: 0.772) and N3 (marrakesh, n = 4: 0.903), each beyond its ceiling. New: the
three n side by side on one device, and the textbook circuit beside each.

## Two yardsticks (home's supplement 1)

| yardstick | compares | words |
|---|---|---|
| ceiling | IPE ff (all phases pooled, every shot) against C(n), the best fixed decoder of the off arm's bits | BEYOND THE CEILING / NOT BEYOND (as T3-A, N3) |
| per shot | IPE ff against the textbook circuit's share of shots with all n bits right, no correction | draft [OWNER]: IPE RIGHT MORE OFTEN / TEXTBOOK RIGHT MORE OFTEN / NOT SEPARATED |

The textbook circuit reads every phi exactly without noise, so it has no ceiling; the per-shot yardstick is the
essence number (what one shot gives on this device tonight), not a stronger ceiling claim.

## Size (records of 2026-11-17 night 2: marrakesh, fez, kingston, all the same)

| part | items | circuits | s (model) at 2000 shots | at 4000 shots |
|---|---|---|---|---|
| A: n = 2, 3 | IPE 12 + textbook 12 | 76 | 46.8 | 87.8 |
| B: n = 4 | IPE 16 + textbook 16 | 100 | 60.6 | 114.6 |

Per circuit (marrakesh): IPE n 2/3/4 CZ 0-4 / 0-6 / 0-8, depth 10-28 / 20-45 / 31-63, mid-circuit reads 1/2/3,
conditionals 2/5/9, 2 qubits; textbook n 2/3/4 CZ 5-15 / 15-39 / 36-80, depth 26-53 / 57-98 / 102-164, 3/4/5 qubits
(the same CZ as `notes/ffapps_2026-11-17/textbook_qpe.json`). Each item has ff, off and floor arms; the textbook's off
arm is the same circuit (no conditionals): a same-job replicate, beside. One ring sentinel per job.

## Checks

- `ideal`: IPE noiseless 1 for every phase; C(2) 0.7500, C(3) 0.5884, C(4) 0.4706; the textbook circuits as built
  (routed, CZ basis) read every phase with probability 1.000000.
- `check` (noiseless Aer of every compiled arm): PASS for A and B on all three records.
- Dry runs (marrakesh record, Clifford sentinel, `dry/`), illustrative noises written by hand (`noise/`), never fitted:

| noise | n 2: IPE / textbook | n 3 | n 4 | ceiling | per shot |
|---|---|---|---|---|---|
| none (made with `psf_os.feedforward.run_local(OUT, seed=20261119)`, not `dry`) | 1 / 1 | 1 / 1 | 1 / 1 | BEYOND x3 | NOT SEPARATED x3 |
| a: CZ 1 %, damping 2 % per read | 0.982 / 0.918 | 0.964 / 0.781 | 0.947 / 0.591 | BEYOND x3 | IPE x3 |
| b: CZ 0.3 %, damping 5 % | 0.990 / 0.976 | 0.976 / 0.926 | 0.960 / 0.851 | BEYOND x3 | IPE x3 |
| c: CZ 0.2 %, dephasing 12 % per conditional | 0.950 / 0.984 | 0.858 / 0.950 | 0.731 / 0.897 | BEYOND x3 | TEXTBOOK x3 |
| d: as c with 60 % | 0.754 / - | 0.473 / - | 0.268 / - | NOT BEYOND x3 | - |

Rows a to d: `qpe_repro_night.py dry OUT noise/illus_X.json` (seed 20261119, circuit i at seed + 10000 i). Every
verdict word is reached. Which way the per-shot comparison goes on the device depends on what a conditional
costs against what a CZ costs: that is what the test measures, and tonight's timing test reads the first half.

## What it cannot say

- The paper's baseline (Kitaev) is not run; the textbook circuit is another baseline. A Kitaev arm (2 circuits per bit,
  no feed-forward) would be the paper's comparison and is a candidate for later.
- Exact phases j / 2^n only (the paper drew random phases); success = all n bits right, not a phase error.
- The textbook circuit is routed on a line by a fixed rule (no search); a better routing would lower its CZ count.

## Independent check by the workplace VS (2026-11-18, `vs_check.md`, `vs/`, `vs_out/`)

V1 the builds (circuits, seconds, check) agree on all three records; V2 C(n) by two other methods and the bit order on
every built circuit agree; V3 an independent scorer reads the dry runs a to d as the workplace did (the noiseless row
via run_local); V4 every mutation that changes a noiseless output (a textbook read swapped, the feedback's sign, an X
left in a floor) makes check FAIL. `circuits_sha256` differed (QPY bytes: VS qiskit 2.5.2, workplace 2.6.1), and so
did psf-os's gate hash, which writes a conditional block as a text drawing. Since then `build` writes into part.json
`circuits_digest` (every gate, conditional blocks opened; `digest OUT` prints it) and the versions, so two machines
compare the digest.
