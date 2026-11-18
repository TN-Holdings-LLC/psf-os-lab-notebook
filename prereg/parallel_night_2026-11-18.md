# Declared: two packing tests, night of 2026-11-18 (P-A pack the fixed circuits only; P-B what makes the loss)

Home Claude, 2026-11-18 (owner about 10:50 JST: "できれば並列もやる", and the choice of the two forms below). Declared
with the commit that carries this file, pushed before the device record of the run is fetched. Tool as of this commit:
`gpu/parallel_night.py` (build, check, score), psf-os feedforward-2026-11-16 at 0f57c76 (unchanged). Common rules as in
`prereg/packing_night_2026-11-17.md` (device by the standing rule, the first qualifying in the order ibm_marrakesh,
ibm_fez, ibm_kingston; placement by the coupling map and failed marks only; no mitigation, DD and twirling off; 4000
shots; every shot counted).

## Background

The fifth round of 2026-11-17 (`results/packing-night-2026-11-17`): ten feed-forward items in one circuit per arm kept
0.20 less in the control arm than the same items alone on the same qubits (mean d -0.197, 2 SE 0.007), while their off
arms (no conditionals) agreed within 0.03. The cost goes with conditionals running side by side; the mechanism is not
known. None of the items' conditional blocks qualifies for the controller's low-latency path (each block holds a CZ;
`notes/packing_2026-11-17/FASTPATH.md`).

## P-A: pack the fixed circuits only (one job, `OUT/pa`, 37 circuits, 44.3 s by the model)

The ten items of 2026-11-17 (rd1..5, ea1..5), each with its ff, off and floor arms alone, on the qubits the bundle gives
it; plus one bundle of the ten off arms (no conditional) in one circuit (the bundle's "off" arm: the reading; its "ff"
arm: the same circuit, a repeat, beside), and their floor; one ring sentinel. The production form this stands for: the
ten ff arms alone, one packed off, one packed floor and the sentinel, 16 circuits, 20.9 s by the model, against 34
circuits, 40.9 s all alone.

**Verdict.** Per item d_off = |s - v| - |p - v| (s the off arm alone, p packed, v its noiseless value), the mean over
ten items with its 2 SE: PACKING KEEPS LESS (mean <= -2 SE) / PACKING KEEPS MORE (mean >= 2 SE) / SAME WITHIN ERROR.
Beside: the words per item, the repeat, CLOSER WITH CONTROL per item with the off arm alone and packed, the floors.

## P-B: what makes the loss (one job, `OUT/pb`, 19 circuits, 24.2 s by the model)

rd2 (`gpu/rus3_night.chain(2, 1.1, 2)`) on two segments A and B of one rule-C chain, the same in every bundle; three
bundles and rd2 alone on A (sa) and on B (sb):
- B1: A rd2 (conditionals), B rd2's off arm (mid-circuit measurements, no conditional);
- B2: A rd2, B rd2;
- B3: A rd2, B rd2 preceded by a delay on all its qubits longer than A's whole duration (ledger, ASAP, decision
  latency 1 us, times 1.25, rounded up to 16 dt; 21.1 us against 16.9 us on the 2026-11-17 marrakesh record), so that no
  decision of B falls inside A on the schedule as written.

**Verdict.** Per sub-item with conditionals d = |s - v| - |p - v| (s its reference alone, p packed, v rd2's noiseless
value); per bundle the mean over its sub-items with conditionals (B1: A; B2 and B3: A and B) with its 2 SE: PACKED KEEPS
LESS / PACKED KEEPS MORE / SAME WITHIN ERROR. Beside: B1's B (a fixed circuit packed) against sb's off arm; the share
still failing after the second try; the floors.

**Reading (fixed before the data; beside, not a verdict).**
- B1 same, B2 less, B3 same: the loss needs two conditional items whose decisions overlap.
- B1 same, B2 less, B3 less: the loss needs two conditional items in one circuit, whatever their timing (or the delay is
  not kept by the device as written).
- B1 less: a neighbour with mid-circuit measurements is enough; not specific to conditionals.
- B2 same: two items do not show the loss; it needs more items (ten on 2026-11-17).

## Checks before submission (`check OUT`; a FAIL means neither job is submitted)

Independence of every bundle arm; per packed sub-item the same instructions per wire and the same exact distribution
as its reference alone (B3's B with its delay removed); the same physical qubits; the recorded acceptance of every arm,
no sx / x in a floor, no conditional in an off arm or in P-A's bundle, conditionals kept where they belong; in B3, B's
first operation after its delay starts after A's last operation ends (latency 0 and 1 us). Try-build on the 2026-11-17
marrakesh record: PASS; noiseless end to end: P-A mean d -0.0011 (2 SE 0.0066); P-B B1 / B2 / B3 SAME WITHIN ERROR.

## Predictions (written before the data)

1. PA-1 P-A's verdict is not PACKING KEEPS LESS.
2. PB-1 B2 is PACKED KEEPS LESS.
3. PB-2 B1 is SAME WITHIN ERROR.
4. PB-3 B3 is SAME WITHIN ERROR.

Basis: 2026-11-17 (the off arms agreed packed and alone within 0.03; the control arm lost with ten items); PB-1 to PB-3
are the hypothesis that the loss comes from conditional items whose decisions overlap. Each prediction holds or fails as
a whole; a failed one is reported as failed.

## Known limits (stated before the data)

- Whether the device keeps a top-level delay as written around other items' mid-circuit measurements and conditionals
  is not stated in IBM's public documents (home VS, 2026-11-17); B3 is read with that limit.
- Two items one site apart: crosstalk through the lattice or readout lines is part of d.
