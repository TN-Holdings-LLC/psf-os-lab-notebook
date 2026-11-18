# Fast path of the conditionals

(workplace VS Claude, 2026-11-18; a record only, no design change)

**IBM's text:** in the qiskit-ibm-runtime "transpiler passes scheduling" page, a single-qubit block conditioned on an
immediately preceding measurement of the same qubit can take a lower-latency fast path. Such blocks on disjoint qubits
run in parallel. Nesting is not eligible, and a barrier between the measurement and the branch disables the fast path.

**Method:** `fastpath.py` checks every if_else of the compiled arms against these three conditions. The arms come from
dry builds of `gpu/os2_night.py` on the 11-17 marrakesh record.

| item | conditionals | fast path | why not |
|---|---|---|---|
| P0 (rus_chain m = 3) | 2 per neuron | 0 | the block holds a CZ (the retry acts on ancilla and output) |
| P1 (flip_chain) | 1 per neuron | 0 | CZ in the block, and a barrier and the output X stand between the ancilla read and the branch |
| P2 (rd, rus3 chain) | 1 per neuron | 0 | as P1 |
| nf (flip_chain, flip = False) | 1 per neuron | 0 | as P1 |
| dr (readout probe) | none | - | - |

**Reading:**
- No conditional of the night is fast-path eligible.
- Each one ends a quantum block and waits for the full decision latency.
- When items are packed, one item's conditional may end the block for the others too (the page: control flow ends a
  "quantum block", and the next starts after a nondeterministic period). This is a candidate mechanism for the packing
  loss, not a measured one.
