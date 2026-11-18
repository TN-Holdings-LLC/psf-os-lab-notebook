# psf-os v0.2 prototype: three build rules (home VS Claude, 2026-11-18 evening; desk only)

Home Claude's instruction "OS 更新の試作、組み立ての決まり3つ" (owner's decision 20:18 JST). psf-os branch
`v0.2-proto-2026-11-18` from `register-cond-2026-11-18` cd3bba9; notebook from 2afc11c2. Nothing here is declared or
run on a device.

## The three rules (psf-os `psf_os/feedforward.py`, `psf_os/job.py`)

1. **Fixed arms packed automatically**: `build(..., pack_fixed=True)` (default False: the build as before) calls
   `build_pack_fixed`. Every item's ff arm stays its own circuit, on the segment `bundle_place` gives it (one site
   between items, no coupler joining two); the off arms of all items become one circuit and their floors one circuit
   (one register, a bit offset per item). Acceptance: `checks()` of every circuit, the conditionals kept in each ff,
   `bundle_acceptance` on the packed off and floor, and per item the packed off and floor restricted to the item equal
   to the item's own compiled alone on the same qubits (`wire_signature`), the off arm also by its exact distribution
   (`exact_distribution`, branching state vector). `cards()` gives each item the card a single build gives, its off and
   floor read from its own bits of the packed circuits. Ten items: 16 circuits (10 ff + off + floor + 4 sentinel),
   20.9 s by the model, against 34 circuits / 40.9 s.
2. **Conditional items are not packed side by side**: `build_bundle` refuses a bundle with two or more sub-items that
   hold conditional operations, the reason citing 2026-11-17 (`results/packing-night-2026-11-17`) and 2026-11-18
   (`results/parallel-night-2026-11-18`, P-B); `allow_conditional_neighbours=True` lifts it for a test of the loss
   itself, and the manifest records `conditional_neighbours` (items, allowed, used). Several conditionals inside one
   item (a table-lookup decoder, a neuron chain) are not neighbours; every bundle's manifest records
   `conditionals_per_item`.
3. **Build environment recorded and compared**: every job's manifest gets `env` (python, qiskit, qiskit-aer,
   qiskit-ibm-runtime, numpy; `job.build_env`); `job.verify_env(manifest or job folder)` compares it with the running
   environment and, when they differ, says that the ring sentinel's circuit bytes may not match on a rebuild (the
   sentinel is never judged). It never stops anything; a job without the record gives same = None.

`assemble` gained `extra=` (fields a builder adds to the manifest; refused if one would overwrite the manifest's own).
circuits.qpy is never changed by any of this.

## Checks

- Tests: 5 new in `tests/test_feedforward.py` (pack_fixed against the single build on the same qubits: 16 circuits for
  the ten items of tonight, ff bytes identical, the packed off's exact distribution per item equal, noiseless cards
  equal within 4 SE and floors 1; the neighbour rule: refused, allowed and recorded, one conditional beside a fixed
  item (tonight's B1) built without the flag; several conditionals in one item counted, not refused; the environment
  record and verify_env; pack_fixed on tonight's P-A record gives the ff circuits byte for byte as tonight's single
  ff). Four existing bundle tests (three in test_feedforward.py, one in test_register_cond.py) bundle conditional
  sub-items to test the bundle's mechanics; they now pass the flag explicitly. Whole suite with TOQB_DIR: 321 passed,
  1 skipped (psf-os 95e6cc9).
- `reproduce.py --psf-os <branch>` on every result of 2026-11-16 to 2026-11-18: 28 of 28 SAME.
- `rebuild_check.py` (`rebuild_check.txt / .json`): tonight's jobs rebuilt from their device records with the declared
  tools and the branch at its defaults: balanced repeat 32, timing A 41, timing B 35, OS2 Dw 20, Dc 20, round 1 23 qpy
  files, every one byte-identical (sentinels included, in this environment). The parallel test's build is now refused
  at P-B by rule 2, as intended; rebuilt with the flag passed by a wrapper (`rebuild_parallel_with_flag.py`, the tool
  unchanged): 52 qpy files, every one byte-identical.
- Note for rebuilding older records: the declared `gpu/parallel_night.py` (P-B) and the 2026-11-17 packing test
  (`packing-night-2026-11-17`, ten conditional items packed) bundle conditional items; with this branch their build
  needs `allow_conditional_neighbours=True`. Re-scoring them (reproduce) is not affected.
