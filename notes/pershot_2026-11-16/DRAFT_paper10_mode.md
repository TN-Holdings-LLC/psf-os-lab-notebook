# Draft: a shot-by-shot verdict (MODE) on paper 10's pi/2 arms (workplace VS Claude, 2026-11-16; NOT a declaration)

**This is a draft.** A declaration is a pushed commit, made at home. Every number below is a candidate taken from the
2026-11-14 records; the owner chooses. The draft is to be folded into paper 10's first test (`notes/paper10/README.md`:
arms N33, N81, N81cut on ibm_marrakesh, theta pi/4 and pi/2, 8 to 64 CZ layers), whose pi/2 arms have one ideal
output string.

## What would be declared

- **The verdict (per pi/2 circuit):** MODE. It is judged from the job's raw counts (IBM job id), with every shot
  counted, no shot discarded, and no corrected value used.
  - MODE holds when the sealed ideal string is strictly more frequent than every other string of the 4000 shots.
  - A tie with another string counts as "does not hold".
- **Why the tie rule must be written:** pershot.py takes the top string with max(), which on a tie returns whichever
  string comes first in the counts dict. On 11-14 two cells were ties (`mode_margin.txt`):
  - fez, 33 qubits, 64 layers: 2 against 2. pershot.txt says "no".
  - marrakesh repeat, 81 qubits, 16 layers: 2 against 2.
- **Two parts are judged:**
  1. **whole:** the whole output string of the arm (33 or 81 bits).
  2. **first 33:** in N81 and N81cut, the 33-bit substring on the first 33 sites of the chain. These are the qubits
     shared with N33, judged against the arm's own sealed ideal values there.
  - "first 33" is the shot-by-shot form of paper 10's gap. N33's whole string against N81's and N81cut's first 33
    compares the same qubits, in the same session, without any average.
- **Ideal string of N81cut:** the cut makes the first 33 sites' ideal values equal to N33's (cut_desk.py). Whether
  every one of N81cut's 81 values is +-1 has to be checked when the sealed answers are made. If one is not, "whole"
  is not judged for N81cut, and that is recorded.
- **Beside the verdict (reported, not judged):**
  - P_exact with its binomial 2 SE;
  - the ideal count and the largest other count;
  - pass1 and pass2;
  - the floor's P_exact as the readout reference;
  - the mean number of wrong bits, which a scale can reach, so it is beside only.

## What the 11-14 records say (strict rule; `mode_margin.py` writes `mode_margin.txt`)

ibm_marrakesh is paper 10's device. There the 33-qubit chain equals the first 33 sites of the 81-qubit chain in both
runs. On fez it does not, so fez is beside only.

Each cell is the ideal count against the largest other count. A tie counts as no.

| layers | N33 whole (first / repeat) | N81 whole (first / repeat) | N81 first 33 (first / repeat) |
|---|---|---|---|
| 8 | 504-136 yes / 323-262 yes | 11-8 yes / 8-9 no | 506-115 yes / 293-213 yes |
| 16 | 352-50 yes / 224-176 yes | 1-2 no / 2-2 tie | 197-71 yes / 115-86 yes |
| 32 | 93-23 yes / 74-61 yes | 0 no / 0 no | 40-13 yes / 19-15 yes |
| 48 | 29-10 yes / 22-21 yes | 0 no / 0 no | 10-4 yes / 1-3 no |
| 64 | 13-5 yes / 6-4 yes | 0 no / 0 no | 1-3 no / 0-2 no |

**What these records show:**

- **On the same 33 qubits, MODE lasted longer in the 33-qubit circuit than inside the 81-qubit circuit.** In N33 it
  held to 64 layers in both runs. In N81's first 33 it held to 48 layers (first run) and to 32 (repeat). This is the
  same direction as the r gap of 11-14, now shot by shot.
- **The whole 81-bit string is lost early.** Its ideal count is 0 to 2 from 16 layers on. At 8 layers it rests on 8 to
  11 shots, and the two runs disagree (11 against 8, then 8 against 9).
- **Near the edge, MODE rests on few shots.** In the repeat, one other string came close to the ideal string:
  323-262, 224-176 and 22-21. This is probably a single wrong bit on one qubit's readout (not checked). One weak qubit
  can thus decide MODE.

## Candidate predictions (the owner chooses; the numbers are proposals from the table above)

- **M1, N33 whole:** MODE holds at 8, 16 and 32 layers. In both runs the margin there was at least 13 shots.
  - Option: add 48 layers (held in both runs, but 22 against 21 in the repeat).
  - 64 is left open.
- **M2, N81 whole:** MODE does not hold at 16, 32, 48 and 64 layers. The ideal count was at most 2 there in both runs.
  - 8 layers is left open; the runs disagreed.
- **M3, N81 first 33:** MODE holds at 8 and 16 layers, and does not hold at 64.
  - 32 and 48 are left open. In the repeat, 32 was 19 against 15 and 48 was 1 against 3.
- **M4, N81cut first 33 (the test's question):** no record exists for it. It follows paper 10's two readings:
  - **along the chain:** N81cut's first 33 behaves like N33. MODE holds wherever M1 holds, and at 48 and 64 where N33
    holds.
  - **beside the chain:** N81cut's first 33 behaves like N81's first 33 (M3).
  - The proposed form is to declare both rows and judge which one the device follows, with "partly" allowed, as P1 /
    P2 in paper 10.
  - Where N33 and N81 do not differ on that day (for example both hold at 32), M4 says nothing at that depth. This is
    the shot-by-shot form of paper 10's P0.
- **N81cut whole:** the same as M2, if every ideal value is +-1 (see above).

## Points the owner decides before declaring

1. **The tie rule.** Proposed: strict, so a tie counts as does not hold.
2. **Whether a cell with very few ideal shots is judged.** For example, under 10 ideal shots the verdict could be
   recorded as "too few to judge". This is not discarding shots: every shot is still counted, and only the verdict
   word changes.
   - On 11-14 this would have marked these cells:
     - N33 at 64 layers in the repeat (6);
     - N81 whole at 8 layers (8 and 11);
     - N81 first 33 at 48 in the first run (10).
3. **Which depths of M1-M4 are fixed, and which are left open.**
4. **Whether fez is run beside as well.** On 11-14 the 33-qubit chain was not the first 33 of the 81-qubit chain on
   fez, so "first 33" does not compare the same qubits there.

## Limits

- The 11-14 records are one device on two runs, 34 minutes apart. The candidates come from them, so they are not
  independent of these data.
- MODE is a strict per-shot verdict, and a single bad readout qubit can decide it. The floor's P_exact (0.56-0.62 on
  33 qubits, 0.25-0.32 on 81) is the reference for how much of that is readout alone.
- No sealed answer was opened. The ideal strings used here are those of the 11-14 records, scored before.
