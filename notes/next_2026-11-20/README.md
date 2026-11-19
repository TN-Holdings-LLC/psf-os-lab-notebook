# What the night of 2026-11-19 suggests changing (home Claude and the home VS, 2026-11-19 evening)

Proposals only; nothing below is built or declared. The owner chose 1 and 2 for the night of 2026-11-20
(drafts in `prereg/drafts-2026-11-20/`).

1. Packing order (`decoy_DRAFT.md`): the conditional item whose register bits come first lost on 11-18 and 11-19. Test
   whether a fixed item in the first bits shields the conditional items behind it; if so, psf-os's "no conditional
   neighbours" rule could become "conditional items behind a fixed first item".
2. The loop's round-to-round variation (`loopvar_DRAFT.md`): rounds 1 and 2 at the same stack read +0.006 and +0.018 on
   L = 1. Measure within-job and between-job variation before changing the rule (home VS: LOOP-1 failed two nights
   running because a first NOT SHOWN keeps the stack; acting on it would need the variation known first).
3. +M beyond L = 1 (home VS): +M lifted L = 1 from +0.018 to +0.047; L = 2, 3 went to P0 by R3 first. Their g with P1
   was negative (-0.018 to -0.028), not like L = 1.
4. The ring sentinel did not cover the qubits that carried the phase estimation (0-2) in either job; place it over the
   test's qubits.
5. Repetition code: 0.063 under its ceiling; fewer CZ / conditionals per item (lut3 - lut1 = -0.010 beside).
6. Phase estimation: the IPE-textbook gap grew with n (+0.03, +0.07, +0.17); n = 5, 6 would show where IPE meets its
   ceiling.
7. Records: the loop's ledger line of the night stays outside the record (the owner's ~/n1119/os-ledger.json); copy it
   into the record (asked of the owner 2026-11-19). Done: the loop table's SE of g (db30739b).
