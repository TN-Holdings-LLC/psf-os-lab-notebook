# Declared: the neuron chain's third design on another device (ibm_kingston)

Home Claude, 2026-11-16 (owner 21:20 JST "別装置", choosing to run the third design on another device). Declared with
this commit, pushed before the device record of the run is fetched; a change after the push is a new declared file.

## What is run

Exactly the job of `prereg/rus_neuron3_2026-11-16.md`: `python gpu/rus3_night.py build DEVDIR OUT` (the tool as of
1c9ada0f, unchanged; without `--dry-clifford-sentinel`): rd{L} (m = 2, outputs held flipped around every ancilla
measurement, the last output read flipped and relabelled 1 - bit) and flip{L} (the second design, beside), L = 1, 2, 3,
theta 1.1; ff, off and floor arms; one ring sentinel; 22 circuits, 4000 shots, 27.6 s by the model; no mitigation,
dynamical decoupling and twirling off; placement by rule C (coupling graph and failed marks only). psf-os branch
feedforward-2026-11-16, commit 32dc3e5.

## Device

**ibm_kingston**, named here (the standing rule's first qualifying device was ibm_marrakesh for the night's runs so
far; this test asks whether the result carries to another device). It is run if kingston has at most 10 pending jobs
when the queue is read (`gpu/daily_fetch.py`, which fetches the record); otherwise it is not run tonight. Its own
record is used; nothing from the marrakesh runs is used for placement or reading.

## Pre-run check (before submission)

`python gpu/rus3_night.py check OUT` as declared there. On the 13:11 CET kingston record (try-build, before this
commit): PASS; the chains are on physical qubits 0-1, 0-3, 0-5, as on marrakesh.

## Verdict

As declared in `prereg/rus_neuron3_2026-11-16.md` (`python gpu/rus3_night.py score OUT`, unchanged): per L for the rd
items, CLOSER WITH CONTROL when d >= 2 SE_d, otherwise NOT CLOSER.

## Prediction (written before the data)

1. L = 1, 2, 3 (rd): CLOSER WITH CONTROL.

No prediction for the read gain (the tool prints its two-part check, which counts here only as beside): nothing is
known about kingston's qubits 0-5 that would give one; the scorer's line "predictions" belongs to the marrakesh
declaration and is reported, not judged, for this run.

It holds or fails as a whole; if it fails it is reported as failed.

## Reported beside (never judged)

The read gain at each L; the flip items; post; ff's share still failing after 2 tries; ff against the noiseless value
(0.892 / 0.792 / 0.708); the floor; the sentinel; the marrakesh numbers of the same design (13:15 CET).
