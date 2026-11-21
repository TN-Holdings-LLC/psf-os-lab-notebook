# Parking a waiting qubit in |0> by default: what it does to the tools (desk, 2026-11-21)

Home VS Claude, on the home instruction `VSクロードへの指示_待つ量子ビットを0に置く既定_2026-11-21.md` (the owner's
decision of 2026-11-21 9:59 JST, after the weekend's test C). The report is `VSから家へ_0に置く既定_2026-11-21.md`.

- psf-os: branch `park-default-2026-11-21` (from a164fc5). See its CHANGELOG.
- No device. **The rule rests on the device's test C only** (IPE n = 4, one night, one device). The dry runs here are
  expectations under hand-written noise.

## The rule as built

`psf_os.footprint.park_waits`, used by `feedforward.build(park=True)`, the new default:

- **Where:** at every wait. A wait is a mid-circuit measurement group, or a run of conditionals, fenced as
  `fence_waits(conditionals=True)`. The qubits looked at are those neither measured there nor inside its conditionals.
- **What is parked:** a qubit in |1> in every branch, put in |0> for the wait. There is an X before the wait's fence
  and an X after its closing fence. The fences keep the pair from cancelling and keep gates out of the wait, as in C's
  pk.
- **What is left alone:**
  - |0> qubits;
  - carriers (superposition or entangled), recorded as the footprint as before;
  - qubits that are |0> in some branches and |1> in others.
- **Checks at each build:**
  - the exact noiseless distribution of the classical bits is unchanged;
  - the compiled CZ count of each arm is the same as without parking.
  Otherwise the build is refused.
- **Record:** where and which qubits (logical and physical), and excited before and after. It goes in every record,
  in `checks.json` and in the build report.
- **Default and switch:**
  - `park=False` gives the old form, byte for byte.
  - A recorded build is remade with its record's "park", False when absent.
  - The loop's `verify` and `Night.go` read run.json's "park", False when absent.

On IPE n = 4, `park_waits` gives exactly C's pk circuit (the same instructions; checked on phase 5).

## Impact on the tools (`impact.py`, `impact.txt`, `impact.json`)

The ff arm as psf-os builds it, compiled by rule C on the 2026-11-19 marrakesh record.

| tool | items | items parked | waits / parked waits | parked qubit | excited (sum over waits) before → after | compiled depth added | CZ | noiseless distribution |
|---|---|---|---|---|---|---|---|---|
| neuron / RUS loop P0 (os3, paired, loopvar) | 3 | 0 | 15 / 0 | nothing to park | 20.7 → 20.7 | 0 | same | same |
| RUS P3 | 3 | 0 | 9 / 0 | nothing to park | 11.9 → 11.9 | 0 | same | same |
| RUS P1 (loopvar's x) | 6 | 0 | 33 / 0 | nothing to park | 16.8 → 16.8 | 0 | same | same |
| RUS NF (B's other frame) | 6 | 0 | 27 / 0 | nothing to park | 36.0 → 36.0 | 0 | same | same |
| RUS P2 | 6 | 0 | 33 / 0 | nothing to park | 16.8 → 16.8 | 0 | same | same |
| **IPE n = 2-6, every phase** | 124 | **124** | 1032 / **1032** | **the target (logical 1)** | **1032 → 0** | 0 to +3 (n 2) … +16 (n 6) | same | same |
| textbook phase estimation n = 2-5 | 60 | 0 | 0 / 0 | nothing to park (no mid-circuit read) | 0 | 0 | same | same |
| repetition code F16, F10, F6P, F6 | 4 each | 0 | 4 / 0 each | nothing to park | 6.0 → 6.0 each | 0 | same | same |
| decoy sub-item rd2 and its Z | 2 | 0 | 8 / 0 | nothing to park | 3.6 → 3.6 | 0 | same | same |

- **IPE:** the target waits in |1> at every read and at every run of phase feedback: 2 waits per item at n = 2, up to
  10 at n = 6. Every one is parked.
- **The RUS chains:** they have excited qubits at their waits, but every one is |1> in some branches and |0> in others
  (a neuron's output after its tries). By the rule these are not parked. (P1 holds the likely value as |0> by design
  instead.)
- **Repetition code:** the syndrome bits that wait in |1> are inside the look-up's conditionals, so they take part in
  the wait.
- **Unchanged builders:** decoy's bundles are built by `build_bundle`, which does not park; neither does
  `build_pack_fixed`. Its sub-item has nothing to park anyway.

## Dry runs (`dry.py`, `dry.txt`; ILLUSTRATIVE noise, never fitted)

IPE only, since every other tool's parked circuit is the circuit itself. d = parked − as before (plain), every phase
pooled, 2000 shots per phase.

| n | damping 6 % per read: d (2 SE) | dephasing 5 % per conditional: d | one-qubit gates 0.5 %: d (the price of the X pairs) |
|---|---|---|---|
| 2 | +0.0081 (0.0020) | +0.0065 (0.0039) | −0.0006 (0.0042) |
| 3 | +0.0204 (0.0022) | +0.0214 (0.0048) | −0.0009 (0.0041) |
| 4 | +0.0323 (0.0020) | +0.0434 (0.0046) | −0.0009 (0.0034) |
| 5 | +0.0454 (0.0016) | +0.0710 (0.0040) | −0.0011 (0.0027) |
| 6 | +0.0594 (0.0013) | +0.1007 (0.0033) | −0.0011 (0.0022) |

- **Gain:** under either type of the weekend's C noise, parking gains, and the gain grows with n (more waits).
- **Loss:** under gate errors alone it loses about 0.001 (two X per parked wait), within 2 SE at 2000 shots.
- These are expectations only. The rule rests on the device's C.

## Rebuilding the earlier nights

- **Records:** every recorded build lacks the "park" key, so it is remade unparked.
- **reproduce.py:** it re-scores from raw counts and does not rebuild. With the new branch every entry is SAME
  (`repro.txt`).
- **The paired loop of 2026-11-20:** `gpu/os_loop_paired.py verify` with the new branch gives every step SAME.
- **Declared tools that build IPE items** (`gpu/qpe_long_night.py`, `gpu/ipe_park_night.py`, `gpu/qpe_repro_night.py`,
  the weekend's shared tool):
  - Built afresh with the new psf-os and no `park=False`, their plain and fenced IPE would be parked: C's pl and fe
    would become pk.
  - Their declarations pin psf-os a164fc5, which does not park. A new test that wants the plain form must pass
    `park=False` [OWNER].
