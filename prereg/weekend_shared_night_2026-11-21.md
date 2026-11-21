# Declared: the weekend's three tests in one night, shared and cut (2026-11-21)

Home Claude, 2026-11-21, on the owner's choices of 2026-11-21 (0:3x JST: plan 10 of the home VS's table, A at 4000
shots with F16 kept, the ledger's path by replay only; 9:39 JST: start; 9:5x JST: the fills below confirmed, "この内容で宣言する"). Declared when the commit that adds this file
is pushed, before the night's device record is fetched. The tools are as of that commit; psf-os branch
loop-paired-2026-11-21 at a164fc5 (`build(ff_only=...)`; on top of after-2026-11-20). Tool
`gpu/weekend_shared_night.py` (home VS, bfae2760); the three candidates' tools are imported read only:

| | test | its draft at this commit (design, words, reading table, known limits) | tool |
|---|---|---|---|
| A | the repetition code's four forms: the CZ count or the footprint? | `prereg/drafts-2026-11-21/repcode4_DRAFT.md` | `gpu/repcode4_night.py` |
| B | phase estimation at n = 4, 5, 6: does the feedback's cost grow? | `prereg/drafts-2026-11-21/qpe_long_DRAFT.md` | `gpu/qpe_long_night.py` |
| C | where a qubit waits: IPE sent plain, fenced, parked | `prereg/drafts-2026-11-21/ipe_park_DRAFT.md` | `gpu/ipe_park_night.py` |

Each draft is declared as written, with its [OWNER] items filled as below. Where this file and a draft differ, this
file holds.

## The night (plan 10; `notes/weekend_shared_2026-11-21/`)

- Three jobs, 116.9 s by the model (the device's charges have been 0.935 of the model over 105 jobs):
  - job A: A's four forms (F16, F10, F6P, F6) x the four error items, 4000 shots, ff arm only; 20 circuits, 25.3 s;
  - jobs BC0, BC1: B's plan shape (IPE n = 4, 5, 6, every phase) and C's three forms (pl, fe, pk; n = 4, every phase),
    1950 shots, ff arm only; B's n = 4 items are C's pl items (the same circuits); 76 circuits and 45.8 s each.
- Every arm that a verdict reads is sent: every verdict pools ff successes and every ceiling is exact. The off and
  floor arms are not sent (they were beside in every draft and are not reported tonight).
- Layout `own`: every candidate on its own rule-C placement, as in its single job and on 2026-11-19 (A on [0-4]; B and
  C on the IPE pair [0, 1]). One sentinel per job (psf-os); no readout probe (none of A, B, C has one).
- Every check of each candidate passes on each job before anything is sent (`check`); the home dry build on the
  2026-11-20 marrakesh record: PASS, and the bytes are the same with layout `apart` and `own`.
- No mitigation; DD and twirling off; every shot counted. The device: as every night (`gpu/daily_fetch.py`, the shortest
  queue).

## The [OWNER] items

**A** (repcode4):
1. One job (ff only, 25.3 s).
2. The words and the reading table as written in the draft: ceiling per form BEYOND THE CEILING / NOT BEYOND (p >=
   0.875 + 2 SE); footprint F6P - F10 and CZ F6 - F6P with KEEPS MORE (d >= 2 SE) / SAME WITHIN ERROR / KEEPS LESS
   (d <= -2 SE); F10 - F16 beside; the five-row reading table.
3. The depth: accepted as a known limit (F6P 35 layers against F10's 43, F6 29 against F6P's 35). A loss in
   proportion to time adds to both comparisons and is not separated; the circuits are not padded.
4. Predictions: **RC4-1** F16 NOT BEYOND THE CEILING (2026-11-19: 0.812 against 0.875). RC4-2 and RC4-3: no direction
   declared (read by the table only).

**B** (qpe_long):
1. Plan shape.
2. The shape on the log of the share: D_n = ln p(n - 1) - ln p(n), a = D_6 - D_5, SE = sqrt(t4^2 + 4 t5^2 + t6^2),
   ACCELERATES (a >= 2 SE) / FLAT / SLOWS (a <= -2 SE); the share's acceleration beside. Ceiling per n as written.
3. The reading table as written (six outcomes, one row each).
4. Predictions: **QL-1** IPE BEYOND THE CEILING at n = 4 (2026-11-19: 0.880 against 0.471). At n = 5 and 6 no direction
   declared. QL-2: no direction declared. QL-3: not in plan shape.
5. Placement rule C, as 2026-11-19. 6. Plain, as 2026-11-19 (B's n = 4 is C's pl).

**C** (ipe_park):
1. Run. 2. n = 4. Fenced and parked at every wait (the tool's default since the workplace VS's その6).
3. The words and the reading table as written: park pk - pl and fence fe - pl with KEEPS MORE / SAME WITHIN ERROR /
   KEEPS LESS (2 SE); pk - fe beside; the reading table (3 + 1 + 5 rows).
4. Predictions PK-1 and PK-2: no direction declared (read by the table only).

Two predictions in all (RC4-1, QL-1), each from a device record; the other questions are read by their tables only.

## Known limits added by sharing

- B's shape reads three n from two jobs (job BC0: n = 5 and 40 phases of n = 6; job BC1: the other 24 phases of n = 6
  and n = 4). A drift between the two jobs enters the acceleration (loopvar 2026-11-20: excess SD up to 0.014 between
  jobs on one L). Fewer jobs than B alone (four).
- C's forms are all in job BC1, so C's comparisons are inside one job.
- With the off arm not sent, IPE's off-arm values of 2026-11-19 have no partner tonight.

## Device procedure (home)

GitHub first (VPN ON), then the device (VPN OFF), as every night. The device step:
```
python gpu/daily_fetch.py OUT/fetch_in ; DEV=<the chosen device's dev folder>
python gpu/weekend_shared_night.py build $DEV OUT/A  --cands A  --shots 4000 --ff-only --layout own
python gpu/weekend_shared_night.py build $DEV OUT/BC --cands BC --b-n4-from-c --ff-only --layout own
python gpu/weekend_shared_night.py check OUT/A ; python gpu/weekend_shared_night.py check OUT/BC     # PASS, or stop
python -m psf_os submit --job OUT/A/job0/job ; ... OUT/BC/job0/job ; OUT/BC/job1/job
python -m psf_os collect --job <each> --wait-min 20
python gpu/weekend_shared_night.py score OUT/A ; python gpu/weekend_shared_night.py score OUT/BC
```
