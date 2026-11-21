"""What parking (psf-os park-default-2026-11-21, psf_os.footprint.park_waits) does to the project's tools (home VS,
2026-11-21; desk, no device). Per tool and item, the ff arm as psf-os builds it (FF._prepare, then park_waits): the
waits, the waits with a parked qubit, the parked qubits, the excited count (expected waiting qubits in |1>, summed over
the waits) before and after, the compiled depth and CZ before and after (rule C on the 2026-11-19 marrakesh record),
and the exact noiseless distribution (park_waits refuses any change).

  python notes/park_default_2026-11-21/impact.py DEVDIR OUT.json
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, "..", ".."))
for d in ("gpu", "notes/ffapps_2026-11-17", "notes/rus_coherent_2026-11-17", "notes/os2_2026-11-18",
          "notes/early_2026-11-17", "notes/compound_2026-11-17", "notes/timebudget_2026-11-17"):
    sys.path.insert(0, os.path.join(NB, d))

from psf_os import feedforward as FF  # noqa: E402
from psf_os.device import Device  # noqa: E402
from psf_os.footprint import exact_distribution, fence_waits, park_waits, wait_footprint  # noqa: E402

THETA = 1.1


def tools():
    import apps as AP
    import qpe_repro_night as Q
    import repcode4_night as RC
    import rus2_night as R2
    import rus3_night as R3
    import parallel_night as PN
    out = {}
    out["neuron / RUS loop P0 (rus_chain m 3; os3, paired, loopvar)"] = [
        (f"P0 L{L}", *FF.rus_chain(L, THETA, m=3)) for L in (1, 2, 3)]
    out["RUS P3 (rus_chain m 2)"] = [(f"P3 L{L}", *FF.rus_chain(L, THETA, m=2)) for L in (1, 2, 3)]
    out["RUS P1 (flip_chain; loopvar's x)"] = [(f"P1 L{L} m{m}", *R2.flip_chain(L, THETA, m=m))
                                                for L in (1, 2, 3) for m in (2, 3)]
    out["RUS NF (flip_chain, no flip; B's other frame)"] = [(f"NF L{L} m{m}", *R2.flip_chain(L, THETA, m=m, flip=False))
                                                             for L in (1, 2, 3) for m in (2, 3)]
    out["RUS P2 (rus3 chain)"] = [(f"P2 L{L} m{m}", *R3.chain(L, THETA, m=m)) for L in (1, 2, 3) for m in (2, 3)]
    ipe = []
    for n in (2, 3, 4, 5, 6):
        for j in range(2 ** n):
            qc, succ = AP.ipe(n, j, True)
            off, _ = AP.ipe(n, j, False)
            ipe.append((f"IPE n{n} j{j}", qc, dict(success=succ, off_circuit=off, form="blocks")))
    out["IPE n 2-6 (every phase)"] = ipe
    tb = []
    for n in (2, 3, 4, 5):
        for j in range(2 ** n):
            qc, succ, _ = Q.textbook_logical(n, j)
            tb.append((f"textbook n{n} j{j}", qc, dict(success=succ, form="pauli")))
    out["textbook phase estimation n 2-5"] = tb
    for f in RC.FORMS:
        rows = []
        for e in RC.ERRORS:
            qc, succ = RC.circuit(f, e)
            off, _ = RC.circuit(f, e, lookup=False)
            rows.append((f"{f} {e}", qc, dict(success=succ, off_circuit=off)))
        out[f"repetition code {f}"] = rows
    qc, sp = PN.rd2()
    out["decoy sub-item rd2 (and its off variant Z)"] = [("rd2", qc, sp), ("rd2 Z", PN.offvariant(qc, sp), sp)]
    return out


def main():
    dev = Device.load(sys.argv[1])
    comp = FF.Compiler(dev)
    res = {}
    for name, items in tools().items():
        rows = []
        for tag, qc, spec in items:
            a, low, off, succ, spec2 = FF._prepare(tag.replace(" ", "_"), qc, spec)
            p, info = park_waits(low)
            chain = FF.place(dev, a["n"])["chain"]
            c0 = comp.run(FF.on_device(low, chain, dev.num_qubits))
            c1 = comp.run(FF.on_device(p, chain, dev.num_qubits)) if p is not low else c0
            d0, d1 = exact_distribution(low), exact_distribution(p)
            same = all(abs(d0.get(k, 0) - d1.get(k, 0)) < 1e-9 for k in set(d0) | set(d1))
            f0 = wait_footprint(fence_waits(low, conditionals=True), conditionals=True)
            rows.append(dict(tag=tag, waits=info["waits"], parked_waits=info.get("parked_waits", 0),
                             parked=info["parked"], excited_before=round(float(f0["excited_waits"]), 4),
                             excited_after=info.get("excited_after", round(float(f0["excited_waits"]), 4)),
                             depth_before=c0.depth(), depth_after=c1.depth(), cz_before=FF.cz_count(c0),
                             cz_after=FF.cz_count(c1), distribution_same=same))
        n_p = sum(1 for r in rows if r["parked_waits"])
        q = sorted({q for r in rows for w in r["parked"] for q in w["qubits"]})
        s = dict(items=len(rows), items_parked=n_p, waits=sum(r["waits"] for r in rows),
                 parked_waits=sum(r["parked_waits"] for r in rows), parked_logical_qubits=q,
                 excited_before=round(sum(r["excited_before"] for r in rows), 3),
                 excited_after=round(sum(r["excited_after"] for r in rows), 3),
                 depth_before=[min(r["depth_before"] for r in rows), max(r["depth_before"] for r in rows)],
                 depth_after=[min(r["depth_after"] for r in rows), max(r["depth_after"] for r in rows)],
                 depth_added=[min(r["depth_after"] - r["depth_before"] for r in rows),
                              max(r["depth_after"] - r["depth_before"] for r in rows)],
                 cz_same=all(r["cz_before"] == r["cz_after"] for r in rows),
                 distribution_same=all(r["distribution_same"] for r in rows))
        res[name] = dict(summary=s, rows=rows)
        print(f"{name}: {s['items']} items, {s['items_parked']} with a parked qubit; waits {s['waits']}, parked "
              f"{s['parked_waits']}; qubits {q}; excited {s['excited_before']} -> {s['excited_after']}; depth "
              f"{s['depth_before']} -> {s['depth_after']} (added {s['depth_added']}); CZ same {s['cz_same']}; "
              f"distribution same {s['distribution_same']}", flush=True)
    json.dump(res, open(sys.argv[2], "w"), indent=1)


if __name__ == "__main__":
    main()
