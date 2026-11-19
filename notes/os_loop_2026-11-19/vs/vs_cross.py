"""Two records of the same loop night built on two machines, compared job by job (workplace VS Claude, 2026-11-19;
instruction "その3"). Independent of psf-os: qiskit only. For every job folder present in both:
  - circuits.qpy bytes equal or not;
  - the gates of the test circuits and of the ring sentinel apart (a digest written here: conditional blocks opened,
    every angle wrapped into (-pi, pi] for rz / p / u-type phases, parameters rounded to 1e-9, the global phase left out);
  - every path in manifest.json that differs (with the values' kinds), and every key that differs in the run records
    (runs/*.json): what a cross-machine verify must leave out, and what it must keep.

  python vs_cross.py NIGHT_A NIGHT_B [OUT.json]
"""
import hashlib
import json
import math
import os
import sys

from qiskit import qpy


def wrap(t):
    t = math.remainder(t, 2 * math.pi)
    return math.pi if abs(t + math.pi) < 1e-9 else t


def gates(c, qmap=None, cmap=None):
    qmap = qmap or {q: c.find_bit(q).index for q in c.qubits}
    cmap = cmap or {b: c.find_bit(b).index for b in c.clbits}
    out = []
    for ins in c.data:
        op = ins.operation
        qs = [qmap[q] for q in ins.qubits]
        cs = [cmap[b] for b in ins.clbits]
        if op.name == "if_else":
            tgt, val = op.condition
            bits = [cmap[b] for b in tgt] if hasattr(tgt, "size") and not hasattr(tgt, "_index") else [cmap[tgt]]
            try:
                bits = [cmap[b] for b in tgt]
            except TypeError:
                bits = [cmap[tgt]]
            blocks = [None if b is None else gates(b, {bq: qs[i] for i, bq in enumerate(b.qubits)},
                                                   {bc: cs[i] for i, bc in enumerate(b.clbits)}) for b in op.blocks]
            out.append(["if_else", qs, cs, bits, int(val), blocks])
        else:
            ps = []
            for p in op.params:
                try:
                    v = float(p)
                    v = wrap(v) if op.name in ("rz", "p", "u1", "rx", "ry") else v
                    ps.append(0.0 if abs(v) < 1e-12 else round(v, 9))
                except (TypeError, ValueError):
                    ps.append(str(p))
            out.append([op.name, qs, cs, ps])
    return out


def digest(cs):
    return hashlib.sha256(json.dumps([dict(n=c.num_qubits, m=c.num_clbits, g=gates(c)) for c in cs],
                                     sort_keys=True).encode()).hexdigest()[:16]


def diffs(a, b, path=""):
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            out += diffs(a.get(k), b.get(k), f"{path}/{k}")
        return out
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        out = []
        for i, (x, y) in enumerate(zip(a, b)):
            out += diffs(x, y, f"{path}[{i}]")
        return out
    return [] if a == b else [path]


def generic(paths):
    """'/cells[3]/run_sha256' -> '/cells[*]/run_sha256' (the kinds of path, not every index)."""
    import re
    return sorted({re.sub(r"\[\d+\]", "[*]", p) for p in paths})


def job_compare(ja, jb):
    ma, mb = (json.load(open(os.path.join(j, "manifest.json"))) for j in (ja, jb))
    roles = [c["role"] for c in ma["cells"] for _ in range(c["points"])]
    ca, cb = (qpy.load(open(os.path.join(j, "circuits.qpy"), "rb")) for j in (ja, jb))
    t = lambda cs: [c for c, r in zip(cs, roles) if r != "sentinel"]
    s = lambda cs: [c for c, r in zip(cs, roles) if r == "sentinel"]
    return dict(bytes_same=open(os.path.join(ja, "circuits.qpy"), "rb").read() == open(os.path.join(jb, "circuits.qpy"), "rb").read(),
                tests_same=digest(t(ca)) == digest(t(cb)), sentinel_same=digest(s(ca)) == digest(s(cb)),
                manifest_paths=generic(diffs(ma, mb)))


def main():
    a, b = sys.argv[1:3]
    rows = {}
    for d in sorted(os.listdir(a)):
        ja, jb = os.path.join(a, d, "job"), os.path.join(b, d, "job")
        if not (os.path.isdir(ja) and os.path.isdir(jb)):
            continue
        r = job_compare(ja, jb)
        rk = set()
        ra, rb = os.path.join(a, d, "runs"), os.path.join(b, d, "runs")
        if os.path.isdir(ra):
            for f in sorted(os.listdir(ra)):
                if f.endswith(".json") and os.path.exists(os.path.join(rb, f)):
                    rk |= set(generic(diffs(json.load(open(os.path.join(ra, f))), json.load(open(os.path.join(rb, f))))))
        r["run_record_paths"] = sorted(rk)
        rows[d] = r
        print(f"{d}: bytes {'same' if r['bytes_same'] else 'differ'}; test gates {'SAME' if r['tests_same'] else 'DIFFERENT'}; "
              f"sentinel gates {'same' if r['sentinel_same'] else 'differ (beside)'}")
        print(f"    manifest paths that differ: {r['manifest_paths']}")
        print(f"    run-record paths that differ: {r['run_record_paths']}")
    if len(sys.argv) > 3:
        json.dump(rows, open(sys.argv[3], "w"), indent=1)


if __name__ == "__main__":
    main()
