# IBM 2023 utility, Fig. 3: how accurate, and what the correction did (exploratory, 2026-11-16)

Owner 2026-11-16 (JST morning): can the gap between IBM's corrected numbers and ours give evidence of the correction?
Not declared: the 11-10 / 11-11 declarations say IBM's mitigated values are not compared numerically; this note is
beside the records and changes no verdict. `extract.py` reads Fig. 3 from the vector drawing of the published PDF;
`compare.py` (output `compare.txt`) splits each set with the identity MSE / mean square = (1 - r)^2 + rest.

The figure's grey exact curve agrees with our own exact values at our 17 angles to 1e-4 (weight-10) and 2e-4
(weight-17), so the read coordinates are reliable to about that. IBM's angles are 0.1 rad steps (13-14 points), ours
k pi / 32 (17 points); each set is measured against the exact values at its own angles.

| 5 steps, MSE / mean square (r) | Mz | weight-10 | weight-17 |
|---|---|---|---|
| IBM unmitigated (Pauli-twirled, gain 1), ibm_kyiv 2023 | 0.042 (0.80) | 0.236 (0.52) | 0.637 (0.20) |
| IBM ZNE-mitigated | 0.000 (1.01) | 0.003 (0.98) | 0.010 (1.04) |
| ours raw (no twirling, no mitigation), ibm_fez 2026-11-10 | not run | 0.135 (0.63) | 0.809 (0.10) |

What it shows about the correction:

- IBM's unmitigated values were almost a pure shrink (rest 0.000-0.002): on weight-10 and weight-17 every point kept
  the same share (0.50-0.52 and 0.20-0.22 across the angles); on Mz the share fell with the angle (0.83 to 0.66).
- ZNE multiplied each point by about the inverse of the share that point kept (gain x kept 0.95-1.07 on Mz and
  weight-10). So the correction acted as a per-point division; on Mz it followed the angle-dependent share, which a
  single division would not (a single division would leave 0.003 there, still reading).
- On weight-10 and weight-17, where the share was the same everywhere, one division by IBM's own r would have left
  0.000 and 0.001, against ZNE's 0.003 and 0.010: ZNE added point-to-point scatter (gain x kept 0.65-1.36 on
  weight-17) while removing the shrink.
- Ours against IBM's unmitigated: Heron kept more of weight-10 (0.63 against 0.52) and less of weight-17 (0.10
  against 0.20). Not a device comparison: different devices and years, IBM's values were twirled (which turns
  coherent error into a shrink), ours were not, and weight-17 sits on a 68-qubit cone embedded in fez.

Limits: values read from a figure, not from IBM's data files (figshare 10.6084/m9.figshare.22500355, not reachable
from here); one figure, one depth; no claim on how ZNE works inside, only on what its output did to each point.
