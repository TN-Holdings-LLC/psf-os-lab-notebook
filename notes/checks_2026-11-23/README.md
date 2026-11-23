# psf-os 0.3.3rc1 (candidate): the circuit as sent, checked (home VS, 2026-11-23; desk, no device)

The psf-os branch is `checks-and-durations-2026-11-23` (from v0.3.2). It is not tagged and not released.

| file | what it holds |
|---|---|
| `recheck_nights.py`, `recheck_0.3.3rc1.json` | the six recorded nights of 2026-11-21 and 2026-11-22 rebuilt by their own tools with 0.3.3rc1: the compiled parking check, the gates and bytes against the records |
| `bytecmp.py`, `bytes_0.3.2_vs_0.3.3rc1.txt` | the same six nights rebuilt with psf-os 0.3.2 and with 0.3.3rc1, every file compared |
| `beside_fake_lengths.py`, `beside_fake_lengths.json` | the 2026-11-22 branch-cost circuits timed with **FakeFez's snapshot values, not the device's record** (beside) |
| `reproduce_0.3.3rc1.txt` | `reproduce.py --psf-os <0.3.3rc1>`: 93 of 93 SAME |
| `verify_loop_1119_0.3.3rc1.txt`, `verify_loop_1120_0.3.3rc1.txt` | the loops' `verify` with 0.3.3rc1: every step SAME (16 and 13), each rebuilt job with the summary line "the same for all N circuits" |
| `tests_0.3.3rc1.txt` | psf-os's tests with `TOQB_DIR` set: 414 passed, 1 skipped (the heavy tensor-network test) |

## The recorded nights rebuilt

`PYTHONPATH=<0.3.3rc1> python notes/checks_2026-11-23/recheck_nights.py OUT`. Each night's own tool builds again from
the night's device record. Only two things are set to the night: `psf_os.__version__` reads as the night's version,
so that the tools' version gates pass, and build()'s park defaults are the night's (as `loop.verify` does).

| night | built with | jobs | compiled parking check | parked waits checked | test circuits against the record |
|---|---|---|---|---|---|
| weekend-shared-night-2026-11-21 | a164fc5 (no parking) | A, BC0, BC1 | nothing parked by psf-os | 0 | gates and bytes the same |
| qpe-parked-night-2026-11-21 | 0.3.0 | job0, job1 | passed | 382 + 610 (112 records) | gates and bytes the same |
| rus-fence-night-2026-11-21 | 0.3.0 | job0 | passed | 24 (4 records) | gates and bytes the same |
| likely-park-night-2026-11-22 | 0.3.1 candidate | job0 | passed | 142 (32 records) | gates and bytes the same |
| qpe-n78-night-2026-11-22 | 0.3.1 | job0 | passed | 576 (48 records) | gates and bytes the same |
| ipe-branch-cost-night-2026-11-22 | 0.3.1 | job0 | passed | 480 (64 records) | gates and bytes the same |

No build was refused, and no wait was left uncounted. `verify`'s new summary line reads "the same for all N circuits"
for every job.

Beside, never judged: the weekend's test C was parked by its tool, not by psf-os, so nothing was checked there. Its
waits as sent, read from the new record, are what the test meant: the target's P(|1>) during every wait is 0 in pk,
1 in fe, and 0.5 in most of pl's waits (1 in a few).

## 0.3.2 and 0.3.3rc1 build the same files

The same six nights were rebuilt with psf-os 0.3.2 (v0.3.2, f5744af) and with 0.3.3rc1. Every file is byte for byte
the same: run records and their QPY, the jobs' `circuits.qpy`, `build.json`, `checks.json`. Each manifest is the same
too, once its time, build environment, `psf_os_build` and the new `compiled` key are left out.

## Heron's time grid

There is no record of the devices' timing constraints in this notebook: every device record so far was fetched by
a psf-os that did not read them. The values below come from qiskit-ibm-runtime 0.49.0's fake backends (`conf_*.json`
shipped with the package, `timing_constraints`). They are **snapshots of the backends' configuration, not this
notebook's device records**:

| fake backend | snapshot | granularity | min_length | pulse_alignment | acquire_alignment | dt |
|---|---|---|---|---|---|---|
| FakeFez | backend_version 1.2.8 | 1 | 2 | 1 | 1 | 4 ns |
| FakeMarrakesh | 1.0.7 | 1 | 2 | 1 | 1 | 4 ns |
| FakeKingston | 1.0.0 | 1 | 2 | 1 | 1 | 4 ns |
| FakeTorino | 1.0.54 | 1 | 2 | 1 | 1 | 4 ns |

On that grid, 2026-11-22's 4500 dt fits: it is a multiple of 1 and longer than 2 dt. IBM accepted the delays that night.
The next `daily_fetch` writes the device's own values (`timing.json`, and `device.json` with psf-os 0.3.3rc1).

## The branch-cost night's conditionals (beside; FakeFez's values, not the device's record)

`beside_fake_lengths.py` times the rebuilt circuits of 2026-11-22 with FakeFez's durations: x 6 dt, measure 390 dt,
cz 21 or 26 dt. The decision latency is not in any record and is not counted, so every conditional's wait is a lower
bound.

| form | n | conditionals per circuit | a conditional's wait, lower bound (median) | circuit length (median) |
|---|---|---|---|---|
| F | 6 | 20 | 390 dt = 1.56 µs | 11.1 µs |
| F | 8 | 35 | 390 dt = 1.56 µs | 14.9 µs |
| S | 6, 8 | 5, 7 (the resets) | 396 dt = 1.58 µs | 11.1, 14.9 µs |
| SD (L) | 6, 8 | 5, 7 | 396 dt | 281, 519 µs |
| SD (2L) | 6, 8 | 5, 7 | 396 dt | 551, 1023 µs |

L was 4500 dt = 18 µs per conditional. On these values a conditional's wait is at least 1.56 µs. Guess (not measured):
the device's own wait for a conditional, latency included, is shorter than L. The circuits' lengths add up with the
delays recorded on the night (270 and 504 µs at L).
