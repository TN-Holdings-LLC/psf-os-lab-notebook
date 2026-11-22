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
