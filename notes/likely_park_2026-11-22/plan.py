"""Device plans for the 0.3.1 candidate (psf-os likely-park-2026-11-22, build(park_likely=...)), built and checked,
never run (home VS, 2026-11-22; desk). Per RUS item the default D and the candidate L (the likely value parked behind a
partial fence) side by side in one job, copies a, b, ...; the IPE control (n = 4 at phases 2, 6, 10, 14, parked and
unparked); ff arms only; 1950 shots; one job within 60 s. Checked: per item L's compiled circuit is the desk's MP form
(forms.py), the compiled noiseless distributions of D and L are equal, their compiled CZ equal; psf_os_build records
park_likely.

  python notes/likely_park_2026-11-22/plan.py DEVDIR WORK OUT.json
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(NB, "gpu"))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(NB, "notes", "ffapps_2026-11-17"))
import rus_fence_night as RF  # noqa: E402
import forms as FM  # noqa: E402

SHOTS = 1950
IPE_PHASES = (2, 6, 10, 14)
PLANS = {"A": {"nfl3m3": 3, "p0l3": 8, "p3l3": 5}, "B": {"nfl3m3": 4, "p0l3": 14, "p3l3": 10}}


def main():
    import apps as AP
    from psf_os import feedforward as FF
    from psf_os.device import Device
    from psf_os.footprint import exact_distribution
    dev = Device.load(sys.argv[1])
    work = sys.argv[2]
    os.makedirs(work, exist_ok=True)
    comp = FF.Compiler(dev)
    res = {}
    for name, copies in PLANS.items():
        items, likely, skip = [], [], []
        lows = {}
        for key, c in copies.items():
            presc, m, L = RF.RUS[key]
            qc, spec = RF.rus_circuit(presc, m, L)
            lows[key] = (FF.lower(qc), spec)
            for cp in "abcdefghijklmnop"[:c]:
                items.append((f"{key}D{cp}", qc, spec))
                items.append((f"{key}L{cp}", qc, spec))
                likely.append(f"{key}L{cp}")
        for j in IPE_PHASES:
            qc, succ = AP.ipe(4, j, True)
            off, _ = AP.ipe(4, j, False)
            sp = dict(success=succ, off_circuit=off, form="blocks")
            items += [(f"ipk4_{j}", qc, sp), (f"ipu4_{j}", qc, sp)]
            skip.append(f"ipu4_{j}")
        out = os.path.join(work, name)
        rep = FF.build(dev, items, out, shots=SHOTS, max_seconds=60, ff_only=[t for t, _, _ in items], park=True,
                       park_skip=skip, park_likely=likely, sentinel_spec=dict(kind="echo_clifford", D=24))
        from qiskit import qpy
        man = json.load(open(os.path.join(out, "job", "manifest.json")))
        cs = qpy.load(open(os.path.join(out, "job", "circuits.qpy"), "rb"))
        cells = {c["cell"]: c for c in man["cells"]}
        by = {cells[p["cell"]]["name"][3:]: cs[i] for i, p in enumerate(man["pubs"])}
        checks = []
        for key in copies:
            low, spec = lows[key]
            chain = FF.place(dev, low.num_qubits)["chain"]
            mp = FF.compact(comp.run(FF.on_device(FM.build_form(low, "MP"), chain, dev.num_qubits)))
            cd, cl = FF.compact(by[f"{key}Da"]), FF.compact(by[f"{key}La"])
            dd, dl = exact_distribution(cd), exact_distribution(cl)
            checks.append(dict(item=key, L_is_MP=(cl == mp),
                               distribution_same=all(abs(dd.get(x, 0) - dl.get(x, 0)) < 1e-9 for x in set(dd) | set(dl)),
                               cz=(FF.cz_count(cd), FF.cz_count(cl))))
        p = 0.7
        res[name] = dict(copies=copies, circuits=rep["circuits"], seconds=rep["qpu_seconds_model"],
                         two_se={k: round(2 * math.sqrt(2 * p * (1 - p) / (SHOTS * c)), 4) for k, c in copies.items()},
                         psf_os_build=man.get("psf_os_build"), checks=checks)
        print(f"plan {name}: {rep['circuits']} circuits, {rep['qpu_seconds_model']:.1f} s; 2 SE {res[name]['two_se']}; "
              f"psf_os_build {man.get('psf_os_build')}; " + "; ".join(
                  f"{c['item']} L = MP {c['L_is_MP']}, distribution same {c['distribution_same']}, CZ {c['cz']}"
                  for c in checks), flush=True)
    json.dump(res, open(sys.argv[3], "w"), indent=1)


if __name__ == "__main__":
    main()
