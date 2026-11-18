"""Per-circuit digests, to find which circuits make two machines' `digest OUT` differ (workplace VS Claude,
2026-11-18). For each circuit of a job: the SHA-256 (first 16 hex) of its gate list as `qpe_repro_night.digest`
writes it (conditional blocks opened), its CZ count, and the same digest with every rz angle dropped (gate names and
qubits only). Run it on both machines and compare the JSON files line by line: a circuit whose `no_angles` agrees but
whose `digest` differs differs only in rz angles. One whose CZ count agrees but whose `no_angles` differs has the
same two-qubit gates in another arrangement.

  python vs_digest_cells.py OUT OUT.json
"""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "gpu"))
import qpe_repro_night as Q  # noqa: E402  (the tool's own gate list, so that the digests are the tool's)


def strip(g):
    out = []
    for x in g:
        if x[0] == "if_else":
            out.append(x[:4] + [[strip(b) if b is not None else None for b in x[4]]])
        else:
            out.append([x[0], x[1], x[2], [] if x[0] == "rz" else x[3]])
    return out


def h(doc):
    return hashlib.sha256(json.dumps(doc, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]


def main():
    from qiskit import qpy
    out, js = sys.argv[1:3]
    m = json.load(open(os.path.join(out, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(out, "job", "circuits.qpy"), "rb"))
    names = [cell["name"] + (f"#{p}" if cell["points"] > 1 else "") for cell in m["cells"] for p in range(cell["points"])]
    rows = {}
    for name, c in zip(names, cs):
        g = Q._gates(c)
        rows[name] = dict(digest=h(dict(num_qubits=c.num_qubits, num_clbits=c.num_clbits, gates=g)),
                          no_angles=h(strip(g)), cz=c.count_ops().get("cz", 0))
    json.dump(dict(digest=Q.circuits_digest(os.path.join(out, "job", "circuits.qpy")), versions=Q._versions(),
                   circuits=rows), open(js, "w"), indent=1)
    print(f"{len(rows)} circuits -> {os.path.basename(js)}")


if __name__ == "__main__":
    main()
