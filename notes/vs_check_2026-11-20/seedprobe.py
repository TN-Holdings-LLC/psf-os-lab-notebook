"""How Aer seeds the shots of a circuit with a mid-circuit measurement (workplace VS, 2026-11-20). No device."""
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


def circ(control_flow):
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.measure(0, 0)
    if control_flow:
        with qc.if_test((qc.clbits[0], 1)):
            qc.x(1)
    else:
        qc.h(1)
    qc.h(0)
    qc.measure([0, 1], [0, 1]) if not control_flow else qc.measure(1, 1)
    return qc


for method in ("density_matrix", "statevector"):
    for cf in (True, False):
        sim = AerSimulator(method=method)
        mem = {s: sim.run(circ(cf), shots=200, memory=True, seed_simulator=s).result().get_memory(0)
               for s in (7, 8, 1007, 10 ** 6 + 7)}
        a = mem[7]
        shift = max(range(0, 5), key=lambda d: sum(x == y for x, y in zip(a[d:], mem[8])))
        same1 = sum(x == y for x, y in zip(a[1:], mem[8])) / 199
        same0 = sum(x == y for x, y in zip(a, mem[8])) / 200
        far = sum(x == y for x, y in zip(a, mem[10 ** 6 + 7])) / 200
        print(f"{method:15s} if_else {cf!s:5s}: seed 7 vs 8 same-position {same0:.2f}, shifted by one {same1:.2f}; "
              f"7 vs 10^6+7 {far:.2f}")
