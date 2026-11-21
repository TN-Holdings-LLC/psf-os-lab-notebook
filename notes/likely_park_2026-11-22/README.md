# Keeping the likely-value X pairs without the full fence's cost: the 0.3.1 desk design (2026-11-22)

Home VS Claude, on the home instruction `VSクロードへの指示_RUSの柵の結果の独立検証と0.3.1の机上設計_2026-11-21.md`,
part 2. The report is `VSから家へ_0.3.1の机上設計_2026-11-22.md`.

- psf-os branch `likely-park-2026-11-22` (from v0.3.0): `footprint.park_likely`, `build(park_likely=...)`, off by
  default.
- No device. The only device record for parking the likely value is the night of 2026-11-21 on ibm_fez
  (`results/rus-fence-night-2026-11-21`).

## What the night said

- Parking the likely value gained on top of the full fence: NF +0.0877, P0 +0.0140.
- The full fence cost: P0 −0.0453, P3 −0.0243.
- So the form sendable today, M, read against D: NF +0.079, P0 −0.031, P3 −0.022.

## The forms (`forms.py`, `forms.txt`, `forms.json`; compiled by psf-os 0.3.0 on the ibm_fez record of 2026-11-21)

| form | what keeps the X pair | the pair after compiling |
|---|---|---|
| D | — (no pair) | — |
| F | the full fence at every wait (no pair) | — |
| M | the full fence at every wait (the night's M) | kept |
| MW | the full fence only at the waits with a parked qubit | kept (the same results as M) |
| **MP** | **a partial fence at those waits only: the parked qubits and the wait's own qubits** | **kept, tied to the wait** |
| MQ | a barrier on the parked qubits alone | kept, but free of the wait: the compiler moves it outside (the same results as D) |
| X0 | nothing (X pair; folding into the neighbouring gates) | cancelled: the compiled circuit is D's |
| Y0 | nothing (Y pair) | cancelled: the compiled circuit is D's |

In every form and item the compiled CZ and the compiled noiseless distribution equal D's.

Compiled depth (D → F, M, MP, MQ):

- P0: 68 → 74, 78, 74, 72.
- NF: 71 → 75, 91, 87, 79.
- P3: 62 → 68, 72, 68, 66.

## Dry runs: g against D (ILLUSTRATIVE noise; wait = damping per read, the type the night read; cond = dephasing per conditional; phase = a coherent phase while reading)

| item | F | M (= MW) | **MP** |
|---|---|---|---|
| P0 L3 | −0.056 / +0.044 / +0.005 | +0.042 / +0.044 / +0.014 | **+0.009 / 0.000 / +0.029** |
| NF m3 L3 | +0.009 / +0.044 / +0.011 | +0.324 / +0.044 / −0.016 | **+0.268 / 0.000 / +0.020** |
| P3 L3 | −0.070 / +0.017 / −0.056 | +0.029 / +0.017 / −0.050 | **+0.011 / 0.000 / +0.016** |
| P2 m3 L3 | +0.044 / +0.044 / +0.007 | the same as F | 0 (its pairs cancel once the other fences are gone) |

(2 SE about 0.006 per difference at 40000 shots.)

- **MP is the form closest to "D plus the pair".**
  - Under damping it keeps most of the parking on NF (+0.268 of M's +0.324).
  - It is above D on every item, with no part of the full fence's effect: neither the fence's cost on P0 and P3 under
    damping, nor its gain under dephasing.
- **The illustrative damping overstates the parking on P0.** M − F is +0.098 at the desk against +0.014 on the device.
  So MP's small positives on P0 and P3 are uncertain in size on a device. NF's is the one the device's night supports.
- **MW is the night's M** on these items: the fence at the parked waits is where its cost lies.
- **X0 and Y0** confirm that a pair with nothing in between is folded away by the compiler. Every pair needs a barrier
  on its qubit, and to stay in the wait that barrier must hold the wait's own qubits too.

## The 0.3.1 candidate (psf-os `likely-park-2026-11-22`)

`build(park_likely=False | True | [tags])` applies `footprint.park_likely`, the MP form, after `park`.

- It is checked as `park` is: the noiseless distribution, and the compiled CZ against the unparked arms.
- A pair that the compiler cancels unfenced, such as CX…CX across the waits, refuses the build. A test shows this.
- The records carry `park_likely`.
- Without the argument everything is 0.3.0's, byte for byte.
- For every RUS item, the circuit it compiles is the desk's MP form exactly (`plan.txt`: L = MP).

## Device plans (`plan.py`, `plan.txt`, `plan_<device>.json`; built and checked on the ibm_fez and ibm_kingston records, never run)

Per item, D and L (the candidate) side by side in one job, plus the IPE control (n = 4 at phases 2, 6, 10, 14, parked
and unparked). 1950 shots, ff arms only, one sentinel.

| plan | NF m3 L3 / P0 L3 / P3 L3 copies | circuits | s (model) | 2 SE of L − D: NF / P0 / P3 |
|---|---|---|---|---|
| A | 3 / 8 / 5 | 44 | 27.8 | 0.017 / 0.010 / 0.013 |
| B | 4 / 14 / 10 | 68 | 41.2 | 0.015 / 0.008 / 0.009 |

In every item L's compiled circuit is MP's, the compiled distributions of D and L are equal, and their CZ is equal (33
/ 33; P3 22 / 22).

## Limits

- The footprint's excited count in program order is not a faithful measure under a partial fence: gates of other qubits
  may stand between the pair in program order but not in time. It rose for MP while the dry runs gained. Only g is read
  here.
- The rule uses noiseless probabilities. A qubit near 0.5 may be parked the wrong way more often than not.
- One device night behind it; illustrative noise only.
