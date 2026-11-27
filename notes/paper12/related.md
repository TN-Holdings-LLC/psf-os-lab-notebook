# Paper 12: related work, candidates (workplace, 2026-11-27)

New entries were checked on 2026-11-27 by a web search (title, first author, year, arXiv number seen on arxiv.org or
the journal's page). Nothing here is cited for a claim yet; home picks.

## Carried over from papers 8, 9 and 11 (already in the series' references)

- TN Holdings, papers 7 to 11 (doi:10.5281/zenodo.24046673, 24136512, 24278888, 24367001, 24496368) and psf-os 0.3.3
  (doi:10.5281/zenodo.24496267).
- The utility experiment and its tensor-network re-simulation, as cited in paper 9 (`notes/paper9/paper9.tex`
  references, e.g. arXiv:2306.14887).
- Mid-circuit measurement errors and idling, as cited in paper 11: Hothem et al., arXiv:2410.16706 (2024); Smith et al.,
  TimeStitch, arXiv:2105.01760 (2021); Liu et al., arXiv:2607.02031 (2026).

## New candidates (checked)

- Mirror circuits as a benchmark: Proctor, T. et al. "Scalable randomized benchmarking of quantum computers using
  mirror circuits." Phys. Rev. Lett. 129, 150502 (2022); arXiv:2112.09853. Why: our (b), (c), (d) are mirrors of the
  compiled circuit; their benchmark uses mirror circuits to estimate error rates, not a job's own window.
- Capability measured by circuits of the user's shape: Proctor, T. et al. "Measuring the capabilities of quantum
  computers." Nature Physics 18, 75 (2022); arXiv:2008.11294. Why: volumetric benchmarks with mirror circuits; the
  closest frame for "a ruler made of the job's own circuits".
- Twirling turns a coherent error into a stochastic one: Wallman, J. J. and Emerson, J. "Noise tailoring for scalable
  quantum computation via randomized compiling." Phys. Rev. A 94, 052325 (2016); arXiv:1512.01098. Hashim, A. et al.
  "Randomized compiling for scalable quantum computing on a noisy superconducting quantum processor." Phys. Rev. X 11,
  041039 (2021); arXiv:2010.00215. Why: the twirl dry runs (3.4); a coherent error cancels in U U^dagger.
- Readout error, measured and mitigated: Bravyi, S. et al. "Mitigating measurement errors in multiqubit experiments."
  Phys. Rev. A 103, 042605 (2021); arXiv:2006.14044. van den Berg, E., Minev, Z. K. and Temme, K. "Model-free
  readout-error mitigation for quantum expectation values." arXiv:2012.09738 (2020; Phys. Rev. A 105, 032620, 2022 -
  journal reference 要確認). Why: our (e) is a readout pair in the job, read, not used to correct; TREX twirls the
  readout, which bears on a full twirl with a twirled readout (the later candidate).
- Drift between calibrations: Proctor, T. et al. "Detecting and tracking drift in quantum information processors."
  Nature Communications 11, 5396 (2020); arXiv:1907.13608. Why: the calibration comparison's day-to-day ratios and
  the map's age (3.7); our per-qubit record across nights.

## To be checked (要確認; not verified today)

- IBM's documentation of the backend properties' `last_update_date` and how often calibration runs (for the map's age
  in 3.7): 要確認 (a vendor page, not a paper; cite only as accessed on a date).
- A reference for "a mirror's square root takes out half of a readout error" being known in the benchmarking
  literature: 要確認 (none found today; it may be ours to state with its one-line derivation).
