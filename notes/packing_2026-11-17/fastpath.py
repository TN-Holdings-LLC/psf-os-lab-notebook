"""Which conditionals could take IBM's fast path (workplace VS Claude, 2026-11-18; home instruction, section 4; a
record only, no design change).

IBM's text (qiskit-ibm-runtime, transpiler passes scheduling): a block of gates on a single qubit, conditioned on an
immediately preceding measurement of that same qubit, can complete with lower latency; such fast-path blocks on
disjoint qubits run in parallel; nested control flow is not eligible, and a barrier between the measurement and the
branch disables it. Read here as three conditions on each conditional of a compiled circuit:
  (1) the block holds one-qubit gates only, all on the qubit whose measurement wrote the condition bit;
  (2) that measurement is the qubit's last operation before the conditional, with no barrier between them;
  (3) the block holds no control flow (nesting).

  python fastpath.py OUTDIR [OUTDIR ...]     every if_else of every ff / off / floor arm in each build's job
"""
import json
import os
import sys


def classify(qc):
    """[(index, dict(one_qubit_block, on_measured_qubit, measured_just_before, no_barrier_between, not_nested))]."""
    last_op = {}                         # qubit -> (instruction index, name)
    writer = {}                          # clbit -> (instruction index, qubit)
    out = []
    for i, ins in enumerate(qc.data):
        op = ins.operation
        qs = [qc.find_bit(q).index for q in ins.qubits]
        if op.name == "if_else":
            bit, _ = op.condition
            cb = qc.find_bit(bit).index
            mi, mq = writer.get(cb, (None, None))
            body = op.blocks[0]
            bq = set()
            one = nested = True
            for b in op.blocks:
                if b is None:
                    continue
                for x in b.data:
                    loc = [qs[b.find_bit(q).index] for q in x.qubits]
                    if x.operation.name in ("if_else", "for_loop", "while_loop", "switch_case"):
                        nested = False
                    if len([q for q in loc]) > 1 and x.operation.name != "barrier":
                        one = False
                    bq |= set(loc)
            on_m = bq <= {mq} if mq is not None else False
            prev = last_op.get(mq)
            just = prev is not None and prev[0] == mi
            # a barrier on the measured qubit after the measurement shows up as its last op
            nobar = prev is not None and prev[1] != "barrier"
            out.append((i, dict(one_qubit_block=one, on_measured_qubit=on_m, measured_just_before=just,
                                no_barrier_between=nobar if just or prev is None else prev[1] != "barrier",
                                not_nested=nested, block_qubits=sorted(bq), measured_qubit=mq,
                                body_ops=[x.operation.name for x in body.data])))
            for q in qs:
                last_op[q] = (i, "if_else")
            continue
        for q in qs:
            last_op[q] = (i, op.name)
        if op.name == "measure":
            writer[qc.find_bit(ins.clbits[0]).index] = (i, qs[0])
    return out


def fast(r):
    return all(r[k] for k in ("one_qubit_block", "on_measured_qubit", "measured_just_before", "no_barrier_between",
                              "not_nested"))


def job(out):
    from qiskit import qpy
    from psf_os import feedforward as FF
    m = json.load(open(os.path.join(out, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(out, "job", "circuits.qpy"), "rb"))
    res, i = {}, 0
    for cell in m["cells"]:
        for _ in range(cell["points"]):
            c = cs[i]
            i += 1
            if cell["role"] == "sentinel":
                continue
            rows = classify(FF.compact(c))
            res[cell["name"]] = dict(conditionals=len(rows), fast=sum(fast(r) for _, r in rows),
                                     failing={k: sum(not r[k] for _, r in rows) for k in
                                              ("one_qubit_block", "on_measured_qubit", "measured_just_before",
                                               "no_barrier_between", "not_nested")},
                                     example=rows[0][1] if rows else None)
    return res


def main():
    for o in sys.argv[1:]:
        print(f"== {o}")
        for name, r in job(o).items():
            if r["conditionals"]:
                ex = r["example"]
                print(f"  {name:16s} conditionals {r['conditionals']:2d}, fast path {r['fast']:2d}; failing "
                      f"{ {k: v for k, v in r['failing'].items() if v} }; e.g. block on q{ex['block_qubits']} "
                      f"(measured q{ex['measured_qubit']}): {ex['body_ops']}")
            else:
                print(f"  {name:16s} no conditionals")


if __name__ == "__main__":
    main()
