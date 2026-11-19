# The night of 2026-11-19: four tests, their jobs and their time (workplace Claude, 2026-11-19; a plan, not declared)

Home handover 2026-11-19, section 4.3. Model seconds by psf-os's time model (0.036 s per circuit + 0.00027 s per shot
+ 3 s per job), on the 2026-11-18 marrakesh record (the 2026-11-17 records of marrakesh, fez and kingston give the
same sizes for every job below).

| test | draft | jobs | circuits | model seconds |
|---|---|---|---|---|
| the compounding loop (v0.2, ledger) | `os_loop_DRAFT.md` | Dw, Dc, rounds (until a stop) | 22 + 22, then 16 to 31 per round | at most 240 (its own budget, diagnostics included); 55.2 for Dw + Dc, then 20.9 to 37.6 per round |
| interference E1-E3 | `interfere_DRAFT.md` (home VS) | 1 | 22 | 27.6 |
| repetition code | `repcode_DRAFT.md` | 1 | 40 | 47.6 |
| phase estimation reproduced | `qpe_repro_DRAFT.md` | 2 (A: n = 2, 3; B: n = 4) | 76 + 100 | 46.8 + 60.6 = 107.4 at 2000 shots [OWNER] (202.4 at 4000; 104.9 at 1950) |

**Total by the model: at most 422.6 s** (the loop at its full budget; 182.6 s without the loop). A loop that stops at
a fixed point after round 1, as on 2026-11-18, takes 76 to 86 s, the night then 259 to 269 s. For scale: the night of
2026-11-18 was charged 288 s on ibm_marrakesh.

## Order [OWNER]

The loop first (it reads the device record and runs unattended until it stops), then the three single jobs; or the three
single jobs first if the queue is long. Each job's `check` before its submission; a FAIL means that job is not run and
the others go on.

## Commands (home, VPN OFF, after the declaration is pushed)

```bash
# the loop (device; resumable; zip at the end)
python gpu/os_loop.py preflight --out ~/n1119/loop --zip <psf_zero_project>/res_loop1119.zip
python gpu/os_loop.py go ~/n1119/loop --zip <psf_zero_project>/res_loop1119.zip --ledger <ledger file> [OWNER]
# the single jobs (the device record the loop fetched)
DEV=~/n1119/loop/fetch_in/$(python -c "import json;print(json.load(open('$HOME/n1119/loop/fetch_in/queue.json'))['chosen'][0])")/dev
python gpu/interfere_night.py build $DEV ~/n1119/if && python gpu/interfere_night.py check ~/n1119/if
python gpu/repcode_night.py build $DEV ~/n1119/rc && python gpu/repcode_night.py check ~/n1119/rc
python gpu/qpe_repro_night.py build $DEV ~/n1119/qA --part A --shots 2000 && python gpu/qpe_repro_night.py check ~/n1119/qA
python gpu/qpe_repro_night.py build $DEV ~/n1119/qB --part B --shots 2000 && python gpu/qpe_repro_night.py check ~/n1119/qB
for J in if rc qA qB; do python -m psf_os submit --job ~/n1119/$J/job; done
for J in if rc qA qB; do python -m psf_os collect --job ~/n1119/$J/job --wait-min 20; done
python gpu/interfere_night.py score ~/n1119/if; python gpu/repcode_night.py score ~/n1119/rc
python gpu/qpe_repro_night.py score ~/n1119/qA ~/n1119/qB
```

The single jobs use psf-os v0.2 (register conditions for the repetition code; `allow_conditional_neighbours`, `gap`,
`bit_order` for the interference tests). `<psf_zero_project>` is the folder the zips go to, as on 2026-11-18.
