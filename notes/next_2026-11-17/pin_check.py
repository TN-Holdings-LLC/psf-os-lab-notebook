"""Part C check (home VS Claude, 2026-11-17 evening CET; desk only, not declared): do the delay-pinned circuits of
notes/next_2026-11-17/pin_delay.py pass psf-os's feed-forward entrance once it accepts top-level delays?
Tonight's T2 (rd1..rd5, third design) is try-built on the 2026-11-17 fez record; each item's compiled ff and off arms
are pinned (pin_delay.pin, latency 0), mapped back to the item's logical qubits (chain[k] -> k), and built again
through FF.build (the pinned off arm given as the explicit off arm). Checks per item:
  1. the entrance accepts the pinned ff / off circuits (FF.analyse, form 'blocks') and FF.build passes;
  2. the rebuilt ff / off arms keep every delay (count; the floor too) and, delays aside, the same instructions per
     qubit and clbit as the pinned circuit (pin_delay.same_structure); CZ count unchanged;
  3. exact noiseless distributions (branching statevector, coherent.branch_distribution) of the pinned logical ff
     circuit equal those of the unpinned compiled logical ff circuit (max |difference|);
  4. the ledger: the rebuilt ff arm's ASAP wait against the original's JIT wait.
usage: PYTHONPATH=~/psf-os-ff:NB:NB/gpu python pin_check.py NB OUTDIR"""
import json
import os
import sys

NB, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(NB, "notes", "next_2026-11-17"))
sys.path.insert(0, os.path.join(NB, "notes", "rus_coherent_2026-11-17"))
sys.path.insert(0, os.path.join(NB, "notes", "compound_2026-11-17"))
import pin_delay as PD  # noqa: E402
import coherent as CO  # noqa: E402
import compound as CP  # noqa: E402
from qiskit import qpy, QuantumCircuit, QuantumRegister  # noqa: E402
from psf_os import feedforward as FF  # noqa: E402
from psf_os.device import Device  # noqa: E402

LG = PD.LG


def by_name(o):
    man = json.load(open(os.path.join(o, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(o, "job", "circuits.qpy"), "rb"))
    out, i = {}, 0
    for cell in man["cells"]:
        for _ in range(cell["points"]):
            out[cell["name"]] = cs[i]
            i += 1
    return out


def logical(c, chain):
    """A device circuit on chain qubits -> the logical circuit (chain[k] -> k), classical register kept."""
    idx = {q: k for k, q in enumerate(chain)}
    out = QuantumCircuit(QuantumRegister(len(chain), "q"), *c.cregs)
    for ins in c.data:
        qs = [c.find_bit(x).index for x in ins.qubits]
        if any(q not in idx for q in qs):
            if ins.operation.name in ("barrier", "delay"):
                continue
            raise ValueError(f"{ins.operation.name} off the chain")
        out.append(ins.operation, [out.qubits[idx[q]] for q in qs], ins.clbits)
    return out


def ndelay(c):
    return sum(1 for n, _ in FF.walk(c) if n == "delay")


dev = Device.load(os.path.join(NB, "results/ff-night-2026-11-17/fetch_in/ibm_fez/dev"))
items = CP.items()
spec_of = {t: s for t, _, s in items}
o1 = os.path.join(OUT, "t2")
rep = FF.build(dev, items, o1, shots=4000, sentinel_spec=dict(kind="echo_clifford", D=24))
b1 = by_name(o1)
rows, new_items = {}, []
for tag, it in rep["items"].items():
    chain = it["chain"]
    ff, off = b1[f"ff_{tag}"], b1[f"ff_{tag}_off"]
    pf, nf = PD.pin(ff)
    po, no = PD.pin(off)
    lf, lo = logical(pf, chain), logical(po, chain)
    a = FF.analyse(lf, form="blocks")
    FF.analyse(lo, form="blocks")
    d0 = CO.branch_distribution(logical(ff, chain))
    d1 = CO.branch_distribution(lf)
    diff = max(abs(d0.get(k, 0) - d1.get(k, 0)) for k in set(d0) | set(d1))
    s = dict(spec_of[tag])
    s["off_circuit"] = lo
    new_items.append((tag, lf, s))
    rows[tag] = dict(chain=chain, delays_ff=nf, delays_off=no, analyse=a, exact_max_diff=diff,
                     wait_jit_original=LG.ledger(ff, 0.0, "jit")["wait_qus"],
                     wait_asap_original=LG.ledger(ff, 0.0, False)["wait_qus"], pinned_ff=pf, pinned_off=po)
o2 = os.path.join(OUT, "t2_pinned")
rep2 = FF.build(dev, new_items, o2, shots=4000, sentinel_spec=dict(kind="echo_clifford", D=24))
b2 = by_name(o2)
ok_all = True
for tag, r in rows.items():
    rf, ro, rfl = b2[f"ff_{tag}"], b2[f"ff_{tag}_off"], b2[f"ff_{tag}_floor"]
    pf, po = r.pop("pinned_ff"), r.pop("pinned_off")
    r.update(rebuilt_delays_ff=ndelay(rf), rebuilt_delays_off=ndelay(ro), rebuilt_delays_floor=ndelay(rfl),
             structure_ff=PD.same_structure(pf, rf), structure_off=PD.same_structure(po, ro),
             wait_asap_rebuilt=LG.ledger(rf, 0.0, False)["wait_qus"], cz=rep2["items"][tag]["cz"],
             cz_original=rep["items"][tag]["cz"])
    ok = (r["rebuilt_delays_ff"] == r["delays_ff"] and r["rebuilt_delays_off"] == r["delays_off"]
          and r["structure_ff"] and r["structure_off"] and r["exact_max_diff"] < 1e-12 and r["cz"] == r["cz_original"])
    ok_all &= ok
    print(f"{tag}: chain {chain}; delays ff {r['delays_ff']} -> rebuilt {r['rebuilt_delays_ff']} (floor "
          f"{r['rebuilt_delays_floor']}), off {r['delays_off']} -> {r['rebuilt_delays_off']}; structure ff "
          f"{r['structure_ff']} off {r['structure_off']}; CZ {r['cz_original']} -> {r['cz']}; exact max |diff| "
          f"{r['exact_max_diff']:.1e}; wait q.us: original ASAP {r['wait_asap_original']:.2f} JIT "
          f"{r['wait_jit_original']:.2f}, rebuilt (ASAP executor) {r['wait_asap_rebuilt']:.2f}  {'ok' if ok else 'FAIL'}",
          flush=True)
print(f"entrance build: {rep2['circuits']} circuits, {rep2['qpu_seconds_model']} s model (unpinned: {rep['circuits']}, "
      f"{rep['qpu_seconds_model']} s)")
print("PASS" if ok_all else "FAIL")
json.dump(rows, open(os.path.join(OUT, "pin_check.json"), "w"), indent=1, default=str)
