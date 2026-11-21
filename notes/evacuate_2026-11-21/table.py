"""Which waiting qubits could be taken out of the waits, tool by tool (home VS, 2026-11-21 night; desk, no device).
psf-os evacuate-study-2026-11-21 (`psf_os.evacuate`: classify, evacuate). Per item, the ff arm as psf-os builds it
(FF._prepare): every waiting qubit of every wait sorted into 0 / L / K / B / E with its excited count; then each
evacuated form (L, K, B, and all three) against psf-os 0.3.0's default (the item parked as build parks it): compiled
CZ (rule C on the 2026-11-19 marrakesh record), compiled depth, the number of waits; the noiseless distribution is
checked by evacuate (refused if it changes).

  python notes/evacuate_2026-11-21/table.py DEVDIR OUT.json
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(NB, "notes", "park_default_2026-11-21"))
import impact as IM  # noqa: E402  (the same tools and items as the parking impact table)

from psf_os import feedforward as FF  # noqa: E402
from psf_os.device import Device  # noqa: E402
from psf_os.evacuate import KINDS, classify, evacuate  # noqa: E402
from psf_os.footprint import _windows, fence_waits, park_waits  # noqa: E402

FORMS = {"L": ("L",), "K": ("K",), "B": ("B",), "LKB": ("L", "K", "B")}


def n_waits(qc):
    return len(_windows(fence_waits(qc, conditionals=True)))


def main():
    dev = Device.load(sys.argv[1])
    comp = FF.Compiler(dev)
    res = {}
    for name, items in IM.tools().items():
        rows = []
        for tag, qc, spec in items:
            a, low, off, succ, spec2 = FF._prepare(tag.replace(" ", "_"), qc, spec)
            chain = FF.place(dev, a["n"])["chain"]
            base = park_waits(low)[0]                                   # psf-os 0.3.0's default
            cb = comp.run(FF.on_device(base, chain, dev.num_qubits))
            c = classify(low)
            subs = {}
            for w in c["waits"]:
                for r in w["qubits"].values():
                    if "sub" in r:
                        subs[r["sub"]] = subs.get(r["sub"], 0) + 1
            row = dict(tag=tag, totals=c["totals"], excited=c["excited_by_kind"], subs=subs, waits=n_waits(base),
                       depth=cb.depth(), cz=FF.cz_count(cb), forms={})
            for fn, kinds in FORMS.items():
                try:
                    e, info = evacuate(low, kinds)
                except ValueError as exc:
                    row["forms"][fn] = dict(error=str(exc))
                    continue
                if not info["changed"]:
                    row["forms"][fn] = dict(changed=False)
                    continue
                ce = comp.run(FF.on_device(e, chain, dev.num_qubits))
                row["forms"][fn] = dict(changed=True, cz=FF.cz_count(ce), cz_same=FF.cz_count(ce) == FF.cz_count(cb),
                                        depth=ce.depth(), waits=n_waits(e), same_as_park=(e == base),
                                        K=info.get("K"), B1=info.get("B1"), L=len(info.get("moved_L", [])))
            rows.append(row)
        tot = {k: sum(r["totals"][k] for r in rows) for k in KINDS}
        exc = {k: round(sum(r["excited"][k] for r in rows), 3) for k in KINDS}
        subs = {}
        for r in rows:
            for k, v in r["subs"].items():
                subs[k] = subs.get(k, 0) + v
        forms = {}
        for fn in FORMS:
            ch = [r["forms"][fn] for r in rows if r["forms"][fn].get("changed")]
            forms[fn] = dict(items_changed=len(ch), cz_same=all(x["cz_same"] for x in ch),
                             same_as_park=all(x["same_as_park"] for x in ch) if ch else None,
                             depth_added=[min(x["depth"] - r["depth"] for r, x in zip(
                                 [r for r in rows if r["forms"][fn].get("changed")], ch)),
                                 max(x["depth"] - r["depth"] for r, x in zip(
                                     [r for r in rows if r["forms"][fn].get("changed")], ch))] if ch else None,
                             waits_added=[min(x["waits"] - r["waits"] for r, x in zip(
                                 [r for r in rows if r["forms"][fn].get("changed")], ch)),
                                 max(x["waits"] - r["waits"] for r, x in zip(
                                     [r for r in rows if r["forms"][fn].get("changed")], ch))] if ch else None,
                             errors=sum(1 for r in rows if "error" in r["forms"][fn]))
        res[name] = dict(summary=dict(items=len(rows), qubit_waits=tot, excited=exc, subs=subs, forms=forms), rows=rows)
        print(f"{name}: {len(rows)} items; qubit-waits {tot}; excited {exc}; subs {subs}", flush=True)
        for fn, s in forms.items():
            if s["items_changed"]:
                print(f"   {fn}: {s['items_changed']} items changed; CZ same {s['cz_same']}; the same as park "
                      f"{s['same_as_park']}; depth added {s['depth_added']}; waits added {s['waits_added']}; "
                      f"errors {s['errors']}", flush=True)
    json.dump(res, open(sys.argv[2], "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
