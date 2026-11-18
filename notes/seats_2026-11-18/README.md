# Seat ledger and the broadcast limit (workplace VS Claude, 2026-11-18 afternoon; home instruction 18h, items 2 and 3)

Desk only. No IBM, no GitHub. No calibration error number is read: the tools read `device.json`'s coupling graph and
failed marks, and `circuits.qpy`. psf-os is not imported.

Files:
- `seats.py`: the ledger tool.
- `test_seats.py`: hand cases, plus the integer programme against exhaustive search on 30 random small graphs.
- `seats.json`: every record, with the placements.
- `seats_no_failures.json`: the reference with no failed marks.
- `broadcasts.py`: the broadcast count.
- `broadcasts_packing_2026-11-17.txt`: its output on the packing night.

## Item 2. Repetition-code blocks side by side

**Block.** A distance-d block is a line of 2d - 1 qubits: d data and d - 1 ancillas alternating. It is a simple path
as rule C's chains are:
- every qubit is usable: not failed, and not an end of a failed coupler;
- every link is a working coupler of the record.

**Side by side.** No shared qubit, and no coupler of the record, working or failed, joins two blocks.

**Max** is the largest number of blocks, from an integer programme over every block (scipy milp). The status is
"optimal" (proven) for every record below. **Fixed order** is a greedy pass in one fixed order: a reproducible lower
bound with no solver.

The failed marks of each device are the same in every record from 11-13 to 11-17 (39 records):
- marrakesh: qubits 82, 94, 113, 119, 130; coupler 113-119;
- fez: qubits 72, 148, 149; coupler 32-33;
- kingston: qubits 112, 113, 121, 146; couplers 112-113, 130-131, 145-146, 146-147.

The three devices have the same coupling graph. So the counts are the same every night:

| device | nights with a record | usable qubits | d = 3: max (fixed order) | d = 5 | d = 7 |
|---|---|---|---|---|---|
| marrakesh | 11-13, 14, 15, 16, 17 | 151 | 22 (17) | 12 (11) | 9 (8) |
| fez | 11-13, 14, 17 | 151 | 23 (20) | 13 (11) | 9 (7) |
| kingston | 11-16, 17 | 148 | 22 (18) | 12 (10) | 9 (7) |
| (no failed mark, reference) | - | 156 | 23 (20) | 13 (12) | 10 (8) |

There are no records of 11-18 yet. A block of 2d - 1 qubits holds d - 1 ancillas. With the qubits that separate
the blocks counted, d = 3 uses at most 22 x 5 = 110 qubits in blocks on marrakesh.

**Heavy-hex distance-3 code patches: not counted.** The shape could not be fixed from the public text:
- The Error Correction Zoo (heavy-hex code, after Chamberland et al., PRX 10, 011022 (2020), arXiv:1907.09528)
  gives d^2 data, (d+1)(d-1)/2 syndrome and d(d-1) flag qubits: 19 at d = 3.
- Sundaresan et al., Nat. Commun. (2023), doi:10.1038/s41467-023-38247-5, used 23 qubits of a 27-qubit device for d = 3. Its text names
  the roles of Q1-Q23, but the couplings are only in its Figure 1.
- arXiv:2504.07258 places a d = 3 patch on marrakesh; again, the qubits are only in a figure.

Counting a guessed shape would give a number without a meaning. To count it, take the 23 qubits and their couplings
from Sundaresan et al.'s Figure 1, and count disjoint copies the way `seats.py` does.

Sources:
- https://errorcorrectionzoo.org/c/heavy_hex
- https://pmc.ncbi.nlm.nih.gov/articles/PMC10195837
- https://arxiv.org/html/2504.07258v1

## Item 3. The broadcast limit, read again (IBM's public documents)

**What IBM writes.** "Execute dynamic circuits", section "Quantum Compute limitations"
(https://quantum.cloud.ibm.com/docs/en/guides/execute-dynamic-circuits):

> Due to the limited physical memory on control electronics, there is also a limit on the number of `if` statements
> [...] This limit is a function of the number of broadcasts and the number of broadcasted bits in a job (not a
> circuit). A broadcast is a transfer of unique classical data, and broadcasted bits is the number of classical bits
> being transferred. [...] Currently, if you broadcast 60 bits each time, then the job can have approximately 300
> broadcasts. If you broadcast just one bit each time, however, then the job can have 2400 broadcasts.

So the per-job wording is IBM's own. The limit is about memory: a job above it fails, it is not made to wait.

**The two jobs of 11-17** (`broadcasts.py`, from circuits.qpy). An if_test is counted as a new broadcast when a bit it
reads was measured again after that bit's last broadcast. On IBM's own example, the counter gives 3 conditionals,
2 broadcasts and 4 bits, as the text says.

| job | circuits | conditionals | broadcasts | broadcasted bits | max conditionals per circuit |
|---|---|---|---|---|---|
| single1 (alone) | 34 | 80 | 80 | 80 | 9 |
| packed | 7 | 80 | 80 | 80 | 40 |

The conditionals agree with home's count. Broadcasts and broadcasted bits are also equal per job, and both jobs
are far below the 2400 one-bit broadcasts of the text. If the limit is per job, as written, it does not tell the two
jobs apart.

**Per circuit or at the same time: unknown.** I found no public IBM text that gives a limit, or a wait, per circuit,
per shot, or for conditionals at the same time. What was found:
- The fast path ("transpiler passes scheduling", qiskit-ibm-runtime,
  https://quantum.cloud.ibm.com/docs/en/api/qiskit-ibm-runtime/0.41/transpiler-passes-scheduling): with several
  fast-path blocks in parallel, "each block will be padded out to the duration of the longest block". The 0.26 text
  says instead that they are not padded. This is about fast-path blocks only, and the conditionals of the 11-17
  jobs do not take the fast path (`notes/packing_2026-11-17/FASTPATH.md`).
- IBM's blog of 2025-11-19 (https://www.ibm.com/quantum/blog/utility-scale-dynamic-circuits):
  - feedforward latency "around ~600ns";
  - the new infrastructure "can detect independent sets of conditional operations and execute those operations in
    parallel";
  - "Previously, dynamic circuits executed conditional operations one after the other".

  No number is given for conditionals that are not independent, or for how many run at once.
- The old page "dynamic circuits considerations" (https://quantum.cloud.ibm.com/docs/en/guides/dynamic-circuits-considerations)
  now holds only the job limits; nothing on broadcasts.

So whether conditionals packed into one circuit wait for each other is not in the public documents I could find.
