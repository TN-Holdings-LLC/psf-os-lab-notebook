# Shot by shot: verdicts that no correction can reach (desk, exploratory, 2026-11-16)

Owner 2026-11-16 ("事後処理が絶対できないテストないの？", then "進めて"). Any expectation value, a success probability
included, can be extrapolated (ZNE, PEC); what no processing can do is turn a wrong shot into the right one when the
right one is sealed. So the verdict counts the device's own shots, from the job's raw counts (IBM job id), and a
corrected number is not eligible by declaration.

`pershot.py` (output `pershot.txt`, `pershot.json`): the records of 2026-11-14 whose ideal output is one bitstring:
the XX chain at theta = pi/2 (every <Z> is +-1) and every mirror and floor (ideal all zeros). Per circuit: P_exact (share
of shots equal to the ideal string), MODE (is the ideal string the most frequent one), pass1 / pass2 (at most 1 / 2
wrong bits), and beside it the mean number of wrong bits (linear in <Z>, so a scale reaches it).

| pi/2 chain, deepest CZ layers where | MODE holds | r >= 0.293 |
|---|---|---|
| fez, 33 qubits | 48 | 48 |
| fez, 81 qubits | 8 | 32 |
| marrakesh, 33 qubits (first / repeat) | 64 / 64 | 64 / 64 |
| marrakesh, 81 qubits (first / repeat) | 8 / none | 64 / 64 |

P_exact at 8 layers: 0.08-0.13 for 33 qubits, 0.002-0.003 for 81. On 33 qubits the shot-by-shot verdict and the r line
end at the same depth; on 81 qubits the whole string is lost long before the per-qubit pattern (r 0.80-0.83 at 8 layers
with P_exact 0.002-0.003): MODE asks for the whole 81-bit answer in one shot, r for each bit on average. The floor
(no dynamics) gives P_exact 0.56-0.60 on 33 qubits and 0.28-0.31 on 81: readout alone already costs about half the
33-bit strings and two thirds of the 81-bit ones.

## Draft for a declaration (not declared; to be folded into paper 10's first test, whose pi/2 arms are deterministic)

- Judged, per pi/2 circuit, from the job's raw counts, every shot counted, no shot discarded, no corrected value used:
  MODE (the sealed ideal string is the most frequent string of the 4000 shots).
- Beside: P_exact with its binomial 2 SE, pass1, pass2; the floor's P_exact as the readout reference.
- Predictions to choose from these records (the owner's call): e.g. MODE holds at 33 qubits to 48 layers on fez and 64
  on marrakesh, and at 81 qubits only at 8 layers.

## Declaration draft (workplace VS Claude, 2026-11-16; not declared)

`DRAFT_paper10_mode.md`: MODE on paper 10's pi/2 arms (strict tie rule, whole string and first 33 sites), with
candidate predictions from the 11-14 records; `mode_margin.py` / `mode_margin.txt`: ideal count against the largest
other count per circuit.
