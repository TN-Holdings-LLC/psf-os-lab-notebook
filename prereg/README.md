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
3. **Rulers inside the circuit.** A quantity that a circuit or a job carries in itself, such as a ratio taken inside
   one circuit (a window's odd part over the circuit's own total odd part) or against a mirror of the same layers in
   the same job, may be declared like a fence or a parking: as part of how the test is built and read, written before
   the data. It is not a correction: it is declared with its own words and reading table, the raw quantities are
   still reported, and nothing is fitted to a device or chosen after the data.
   - The owner's choice, 2026-11-24 (10:30 JST): "補正と見なさないで、フェンスを入れたり休ませたりと同様に、量を追加する
     工夫で良い。意図的に数字だけを掘り出す作業とは違う". After `notes/ohm_window_beside_2026-11-24`.
4. **Few units, the t quantile.** From the declarations after 2026-11-24, a word whose SE comes from the scatter of
   fewer than 10 units (pairs, strings, phases) uses the two-sided 95 % t quantile with n - 1 degrees of freedom in
   place of 2 (for 7 pairs, 2.447). With 10 or more, or with an SE from shot noise, 2 SE as before. Declarations
   before this rule keep their widths.
   - Why: on the Ohm ruler dry runs, 2 SE from 7 pairs gave false DIFFERS in 11 to 12 % of noise-free cells; the t
     quantile gave 5 to 6 % and kept every real departure (`notes/ohm_ruler_next_2026-11-24`).
5. **No scatter, no word.** From the same date, a word whose SE is exactly 0 (data with no scatter) reads NOT READ,
   not a difference.
   - The owner's choices, 2026-11-24 (15:44 JST), on the workplace's points 1 and 4.

The owner's choices for psf-os 0.3.2 (2026-11-22 22:0x JST): a circuit's delays capped at 100 µs (allow_long_delay=True
passes); the charge estimate is the 0.3.1 model plus the delays' term (the records' estimates unchanged; 2-7 % above
the charge, on the safe side for budgets); `gpu/daily_fetch.py` also writes `dt.txt` (its earlier outputs unchanged).
