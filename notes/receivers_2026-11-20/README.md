# Receivers for tonight's results, and two small fixes (workplace Claude, 2026-11-20; psf-os after-2026-11-20; not declared)

Home's added instruction 3, items 5 and 6. The two receivers and the sentinel cover are behind an argument whose
default is the behaviour of psf-os 0.2.0 / night-2026-11-20 (61869bb), byte for byte; run_local's seeds are the one
changed default (small fix 1; `stride=1` gives the old seeds). None of it is used by tonight's tools (decoy, loopvar),
which stay at 61869bb. Tests in psf-os `tests/test_feedforward.py` and `tests/test_loop.py`.

## Receiver 1: decoy row 1 ("the loss sits on the register's first bits; a fixed first item shields")

`feedforward.build_bundle(..., behind_fixed_first=True)`: two or more conditional sub-items are allowed when the
sub-item whose bits come first in the register (`bit_order[0]`, or the first item) holds no conditional and at least
one bit (a fixed item, as tonight's Z: rd2's off arm). Otherwise refused as before. The manifest records
`conditional_neighbours.allowed_by = "behind_fixed_first"` and `shield`. With `allow_conditional_neighbours=True` the
option changes nothing (the same circuits and manifest). Test: `test_bundle_behind_fixed_first_receiver`.
To be used only if the declared decoy night reads row 1; rows 2-6 leave the rule as it is.

## Receiver 2: loopvar DRIFTS (between-job variance in the loop's threshold)

`loop.rejudge(round, sigma)` and `loop.next_stacks(..., between_job_sigma=sigma)` (and `between_job_sigma` in a
night's run.json, read by the runner and by verify): every verdict that holds g is judged again with
SE = sqrt(g_se^2 + sigma^2); OVERSHOOT kept as scored; None or 0 is the declared rule, byte for byte. sigma is the
excess between-job standard deviation of g (loopvar's s_b; a dict per L is accepted). Test:
`test_rule_between_job_term_receiver`.

The 2026-11-18 and 2026-11-19 records judged again (`rejudge_loop.py` -> `rejudge_loop.md`):

- 2026-11-19: r2's L1 HELPS (g 0.0182, shot SE 0.0080) holds only up to sigma* = 0.0045. Any sigma >= 0.005 turns it
  NOT SHOWN; RULE3 then stops L1 at P0 (stop-loss: NOT SHOWN twice) instead of adding +M, and +M was the night's
  largest gain (r3 L1 g 0.047, HELPS up to sigma 0.022). The term would have cost the night its best step.
- 2026-11-18: L2 HELPS holds up to sigma* = 0.0078, L1 to 0.0137, L3 to 0.0254; from sigma 0.010 the night does not
  stop after r1 (an L NOT SHOWN for the first time keeps its stack one more round).
- So the between-job term is not free: it trades false steps for missed ones. If loopvar reads DRIFTS with s_b near
  0.005-0.01, the threshold change would have changed both recorded nights. [OWNER: whether to adopt it, and from
  which s_b]

## Small fix 1: run_local's seeds

Aer seeds shot i of a run with seed + i, so v0.2.0's run_local (circuit k at seed + k, bundle part j at
seed + 1000 k + j) gave neighbouring circuits and parts the same shots shifted by one. New default
`feedforward.local_seeds`: slot k x 64 + j at seed + w x slot, w = max(10,000, shots + 1); `stride=1` keeps v0.2.0's
formula so recorded dry runs reproduce; the submission record says `seed_stride` when the new seeds are used. Circuit 0
keeps its seed. Test: `test_run_local_seed_slots`.

Past noiseless dry runs read the same words with the new seeds as with the old (`seed_stride_check.py` ->
`seed_stride_check.txt`; one build per tool on the 2026-11-19 marrakesh record, run_local with stride 1 and with the
default, the tool's own score): ff_night, rus_night, qpe_repro_night parts A and B: SAME WORDS. (The noisy dry runs of
the loop tools use the workplace VS's branch_noise with its own wide stride; unchanged.)

## Small fix 2: the sentinel over the test's qubits (home's candidate 4)

`build(..., sentinel_over_test=True)` / `build_bundle(..., sentinel_over_test=True)`: the ring rule
(`place.rule_choice(prefer=...)`, through `RuleCompiler(dev, prefer=...)`) puts, at the same ring length, an outline
holding every item's qubits first; the manifest and build report record `sentinel_cover` (asked, covered, all).
Nothing is refused on a partial cover. Default off: the same job byte for byte (the 11-16 .. 11-19 builds are
unchanged; the default path is not touched). Test: `test_sentinel_over_the_test_qubits`.

What it found on the 2026-11-19 marrakesh record: rule C places a 2-qubit item at qubits 0, 1 and a 5-qubit item at
0-4. Qubit 0 has one coupler and qubit 1 two, so no ring can pass there: the cover stays empty (recorded) and the
ring is the default one (a plain 40-cycle through 3, 4, 5, 6, 7, 17, ...). The other way round works:
`ring_chains(dev, n)` lists the chains of n consecutive sites of the default sentinel ring (40 chains for n = 2, 3, 5,
7 on that record); a test given one with `chains={tag: chain}` is watched on its own qubits (cover all). That moves
the test off 2026-11-19's qubits, so it is the owner's choice per draft.
