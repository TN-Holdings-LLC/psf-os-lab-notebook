# The packing test made runnable (home VS Claude, 2026-11-17 evening; desk only, not declared, no device)

Home Claude's instruction "相乗りの準備" (2026-11-17 evening), on the notebook at 9a55f4fa and psf-os
feedforward-2026-11-16 at 871d9e6. Draft: `prereg/drafts-2026-11-17/packing_DRAFT.md` (updated for the owner's change:
the single job puts every item on the same physical qubits as the packed job). Tool: `gpu/packing_night.py`.

## psf-os (feedforward-2026-11-16, on 871d9e6)

- `build(..., chains={tag: [qubits]})`: an item placed on a given chain, accepted only as rule C's chains are (n
  distinct usable qubits, each consecutive pair a working coupler; `given_chain`); recorded as chain_rule "given".
  Without `chains` nothing changes (the single build's records are byte for byte as before).
- `build_bundle(dev, items, out, tag)`: the bundled items of `notes/next_2026-11-17/README.md`. `bundle_place` (one
  rule-C chain, one site skipped after an item and more while a coupler would join two), one ff, one off and one floor
  circuit for all sub-items, one classical register (a bit offset per sub-item), one sentinel. Acceptance: `checks()`
  of each arm, the conditionals kept, `bundle_acceptance` (no instruction or barrier, blocks included, on the qubits
  or bits of two sub-items), and per sub-item and arm the same `wire_signature` as the sub-item compiled alone on the
  same qubits. Records: one per arm, with the table {sub-item: segment, qubits, bit offset, bit count, its spec}.
- `cards(out)`: one card per sub-item, from the marginal counts of its bits, by the same code as a single item (ff,
  off, post, the floor's all-zero share over its own bits, the job's sentinel). `gpu/compound_night.py` and
  `gpu/early_night.py` read them unchanged (their tags rd{L} / ea{L}).
- `run_local`: a circuit too large for one statevector is simulated as its independent parts (`components`), joined
  shot by shot (exact: no shared qubit or bit). Other circuits as before.
- Tests added (5): a given chain accepted / refused; a bundle of two copies of two items gives four cards, the
  teleport copies exactly as alone and the neuron copies within 4 SE of the item alone on the same qubits; an
  instruction, a conditional or a barrier across two sub-items is refused; the time model counts 3 arms + the sentinel
  for 2 or 5 sub-items; a 9-item bundle above the statevector limit runs locally by parts.

## Desk results (`fez/`, `marrakesh/`: plan.json, check.txt / .json, score.txt, packing_scores.json)

| record | packed | single | total by the model | check |
|---|---|---|---|---|
| 2026-11-17 fez (`results/ff-night-2026-11-17/fetch_in/ibm_fez/dev`) | 7 circuits, 10.8 s, chain of 69 (qubits 0-124) | 1 job, 34 circuits, 40.9 s | 51.7 s | PASS |
| 2026-11-17 marrakesh (`results/balanced-night-2026-11-17/fetch_in/ibm_marrakesh/dev`) | 7 circuits, 10.8 s, chain of 69 (qubits 0-92) | 1 job, 34 circuits, 40.9 s | 51.7 s | PASS |

(Built with the Clifford echo sentinel for the dry run; a device build uses the ring sentinel: the same circuit
counts.)

- Check on both records: independence ok; per item ff and off the same instructions per wire as the single job's
  circuit and exact distributions identical (total variation 0.0, now that both sit on the same qubits); ledger: the
  last measurement and the wait of every item the same packed as single (ASAP and JIT, latency 0 and 1 us); the
  feed-forward checks ok; the same physical qubits single and packed.
- Noiseless end to end (`feedforward.run_local` on both jobs, then `score`): d_i = +0.0003, -0.0002, -0.0002,
  +0.0008, +0.0017 (rd1..rd5), -0.0003, +0.0000, +0.0002, +0.0000, -0.0003 (ea1..ea5), each 2 SE 0.014-0.022; mean
  +0.0002 (2 SE 0.0062). The difference is the shot noise of two noiseless samplings; the exact distributions are
  equal (check 2), so the exact d_i are 0. The two records give the same numbers (the same circuits per item and the
  same seeds).
- `score` prints numbers only; the verdict words and thresholds stay [OWNER].
