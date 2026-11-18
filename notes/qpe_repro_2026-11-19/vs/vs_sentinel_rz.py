"""The RZ angles of one sentinel point, in circuit order, for a line-by-line comparison between machines (workplace VS
Claude, 2026-11-18; the workplace's request after a555554e). Written exactly: every angle as float.hex(), raw (as
loaded from circuits.qpy) and after the tool's _wrap; with its physical qubit. Also the sentinel points' digests by
the tool's _gates, one per point, and the numpy / qiskit versions.

  python vs_sentinel_rz.py OUT CELL_NAME#POINT OUT.json
"""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "gpu"))
import qpe_repro_night as Q  # noqa: E402


def main():
    import numpy
    import qiskit
    from qiskit import qpy
    out, which, js = sys.argv[1:4]
    m = json.load(open(os.path.join(out, "job", "manifest.json")))
    names = [c["name"] + (f"#{p}" if c["points"] > 1 else "") for c in m["cells"] for p in range(c["points"])]
    roles = [c["role"] for c in m["cells"] for _ in range(c["points"])]
    cs = qpy.load(open(os.path.join(out, "job", "circuits.qpy"), "rb"))
    c = cs[names.index(which)]
    rz = [[c.find_bit(i.qubits[0]).index, float(i.operation.params[0]).hex(), Q._wrap(float(i.operation.params[0])).hex()]
          for i in c.data if i.operation.name == "rz"]
    pts = {}
    for name, role, cc in zip(names, roles, cs):
        if role == "sentinel":
            doc = dict(num_qubits=cc.num_qubits, num_clbits=cc.num_clbits, gates=Q._gates(cc))
            pts[name] = hashlib.sha256(json.dumps(doc, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    json.dump(dict(circuit=which, versions=dict(Q._versions(), numpy=numpy.__version__, qiskit_full=qiskit.__version__),
                   rz_count=len(rz), columns=["physical qubit", "raw angle (float.hex)", "after _wrap (float.hex)"],
                   rz=rz, sentinel_point_digests=pts), open(js, "w"), indent=0)
    print(f"{which}: {len(rz)} rz -> {os.path.basename(js)}")


if __name__ == "__main__":
    main()
