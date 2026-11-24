import json, os, time
from qiskit import qpy
from qiskit.transpiler.passes import RemoveBarriers
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, amplitude_damping_error
from psf_os import feedforward as FF
b = "/root/w/B"
man = json.load(open(os.path.join(b, "job", "manifest.json")))
circs = qpy.load(open(os.path.join(b, "job", "circuits.qpy"), "rb"))
cname = {c["cell"]: c["name"] for c in man["cells"]}
k = next(i for i, p in enumerate(man["pubs"]) if "_t3_" in cname[p["cell"]] and "A2" in cname[p["cell"]] and "mirror" in cname[p["cell"]])
cc = FF.compact(RemoveBarriers()(circs[k]))
m = NoiseModel()
m.add_all_qubit_quantum_error(amplitude_damping_error(0.01).tensor(amplitude_damping_error(0.01)), ["cz"])
for kw in (dict(device="GPU"), dict(device="GPU", batched_shots_gpu=True)):
    t = time.time()
    r = AerSimulator(method="statevector", noise_model=m, **kw).run(cc, shots=1000, memory=True, seed_simulator=1).result()
    print(kw, cc.num_qubits, f"{time.time() - t:.1f} s per 1000 shots", len(r.get_memory(0)))
