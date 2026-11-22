# prereg/: how a declaration is written

The declarations are the dated files in this folder. A file is declared when home Claude moves it here and the
owner's push carries it, before the night's first fetch. A declaration is never edited after that. Drafts live in
`drafts-YYYY-MM-DD/` until they are declared.

These rules are for writing a declaration, not for any one test.

## Rules

1. **Placeholders with physical units.** Before declaring, convert every placeholder that carries a physical unit
   (dt, µs, ns, …) with the device's value, and write the converted value next to it. Example: "L = 4500 dt = 18 µs
   at dt 4 ns".
   - Added 2026-11-23, after `results/ipe-branch-cost-night-2026-11-22`: L was declared as 4500 dt while dt was
     unknown, and turned out to be 18 µs per conditional.
2. **Tests with delays.** Write the seconds of a test that holds delays from an estimate that includes the delay
   term: shots × the sum of the circuits' delays, as psf-os 0.3.2's time model adds it.
   - Added 2026-11-23, after the same night: 112 s were charged against a model of 59.6 s that left the delays out.

The owner's choices for psf-os 0.3.2 (2026-11-22 22:0x JST): a circuit's delays capped at 100 µs (allow_long_delay=True
passes); the charge estimate is the 0.3.1 model plus the delays' term (the records' estimates unchanged; 2-7 % above
the charge, on the safe side for budgets); `gpu/daily_fetch.py` also writes `dt.txt` (its earlier outputs unchanged).
