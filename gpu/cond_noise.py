"""Dry runs only: ILLUSTRATIVE dephasing at conditionals, written by hand and never fitted to a device.

Two forms (2026-11-19, after the workplace VS's item 4):
  dephase_cond   every if_else costs a dephasing on every qubit of the circuit, fired or not (the earlier model);
  dephase_fired  an if_else costs a dephasing on every qubit of the circuit only when its condition holds (inside the
                 true branch, the block widened to every qubit), so a test that never fires costs nothing. A cost on
                 the block's own qubits alone would miss lut5's added tests (a Z on an ancilla holding a classical
                 value): what a fired test costs is time, which every waiting qubit pays. lut5's added tests (s == 0) fire for e = none
                 only, so this form separates (b0) from (b1) in a dry run, which dephase_cond cannot.
"""


def _err(lam):
    from qiskit_aer.noise import phase_damping_error
    return phase_damping_error(lam).to_instruction()


def _fired(op, qubits, clbits, all_qubits, lam):
    """The same if_else on every qubit, a dephasing appended to its true branch on each of them.
    Returns (op, qubits) to append."""
    from qiskit import QuantumCircuit
    from qiskit.circuit import IfElseOp
    rest = [q for q in all_qubits if q not in qubits]
    order = list(qubits) + rest
    n, m = len(order), len(clbits)

    def widen(body, noisy):
        w = QuantumCircuit(n, m)
        w.compose(body, qubits=range(len(qubits)), clbits=range(m), inplace=True)
        if noisy:
            for k in range(n):
                w.append(_err(lam), [k])
        return w

    true_body = op.blocks[0]
    false_body = op.blocks[1] if len(op.blocks) > 1 and op.blocks[1] is not None else None
    new = IfElseOp(op.condition, widen(true_body, True), widen(false_body, False) if false_body is not None else None,
                   label=op.label)
    return new, order


def dephase_conditionals(cc, lam=0.0, fired=0.0):
    """cc with the two illustrative costs; both zero gives cc itself."""
    if not lam and not fired:
        return cc
    out = cc.copy_empty_like()
    for ins in cc.data:
        op, qubits = ins.operation, ins.qubits
        if op.name == "if_else" and fired:
            op, qubits = _fired(op, ins.qubits, ins.clbits, cc.qubits, fired)
        out.append(op, qubits, ins.clbits)
        if ins.operation.name == "if_else" and lam:
            for q in out.qubits:
                out.append(_err(lam), [q])
    return out
