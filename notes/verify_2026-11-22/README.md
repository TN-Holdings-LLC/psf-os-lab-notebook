# The night of 2026-11-22 (psf-os 0.3.1's candidate on ibm_kingston): the home VS's independent recount

From the home instruction `VSクロードへの指示_0.3.1候補の結果の独立検証とリリースの準備_2026-11-22.md`. The report is
`VSから家へ_0.3.1候補の結果の独立検証_2026-11-22.md`.

`lp_indep.py RECORD OUT.json` writes `lp_indep.txt` and `.json`. It uses qiskit, aer and numpy only, and recounts:

- D's and L's P per item, read as declared, with exact derived here;
- the noiseless value of each compiled form, by noiseless Aer sampling at 400000 shots. It agrees with the record's
  exact values within 0.0015;
- L − D with its 2 SE and word, and OVERSHOOT (none);
- the rule's row: park_likely the default;
- the IPE control: +0.0523, KEEPS MORE;
- what was sent: 68 circuits, 1950 shots, copies 4 / 14 / 10, psf_os_build 0.3.1 naming the 28 L items, every parked
  wait fenced with a measured qubit;
- the device rule (kingston 2 < fez 3, marrakesh excluded) and the charge (40 s, 0.6518 RU, 41.2 s).

Every number and word equals the record. reproduce.py with psf-os a6170e5 gives 1 of 1 SAME.

## The night of 2026-11-22 evening (IPE parked at n = 6, 7, 8 on ibm_fez): the home VS's independent recount

From the home instruction `VSクロードへの指示_位相推定n78の結果の独立検証_2026-11-22.md`. The report is
`VSから家へ_位相推定n78の結果の独立検証_2026-11-22.md`.

`qn_indep.py RECORD NOTEBOOK OUT.json` uses qiskit, aer and numpy only, with the notebook's apps.ipe for the circuit
definition. It recounts:

- the parked shares and 2 SE per n, against the declared ceilings;
- the twins' differences;
- the log drops and the acceleration with the declared SE: ACCELERATES, beside;
- the declared table's row: the range reaches n = 8, parking not seen there;
- the phases against k · a mod 2^n (a = 41, 79, 159) and the twins at k = 1 … 4;
- the compiled CZ: by qiskit's own level-1 transpile on a 2-qubit line, every phase gives 11.00 / 13.00 / 15.00 and
  the 16 phases 11.12 / 13.12 / 15.12, as sent in the job;
- the parked items fenced with target and ancilla, and the twins unparked;
- psf_os_build;
- the device rule (a tie at 0 -> ibm_fez by order) and the charge (37 s, 0.6043 RU, 39.0 s).

Every number and word equals the record. reproduce.py with psf-os 0.3.1 gives 1 of 1 SAME.
