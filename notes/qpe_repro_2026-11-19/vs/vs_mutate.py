"""V4: does the tool's check stop a broken job? (workplace VS Claude, 2026-11-18). The tool is not changed: a built
OUT is copied, its job/circuits.qpy is rewritten with one kind of damage, and `qpe_repro_night.py check` is run on
the copy. Damage, one copy each:
  swap   : every textbook ff arm, the clbits of its reads of bits 0 and 1 exchanged (a j whose bits 0 and 1 agree is
           left unchanged by this, so only the j whose bits 0 and 1 differ are expected to fail);
  sign   : every IPE ff arm, the sign of every rz inside its conditional blocks reversed (the phase feedback; the
           conditional-X reset holds no rz);
  floor_x: one X left on a measured qubit just before its read, in one IPE floor arm and one textbook floor arm.

  python vs_mutate.py SRC_OUT WORKDIR TOOL.py
"""
import json
import os
import re
import shutil
import subprocess
import sys


def load(out):
    from qiskit import qpy
    m = json.load(open(os.path.join(out, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(out, "job", "circuits.qpy"), "rb"))
    names = [cell["name"] + (f"#{p}" if cell["points"] > 1 else "") for cell in m["cells"] for p in range(cell["points"])]
    return names, cs


def swap_reads(c):
    data = list(c.data)
    ms = {c.find_bit(ins.clbits[0]).index: k for k, ins in enumerate(data) if ins.operation.name == "measure"}
    a, b = ms[0], ms[1]
    ca, cb = data[a].clbits, data[b].clbits
    c.data[a] = data[a].replace(clbits=cb)
    c.data[b] = data[b].replace(clbits=ca)
    return c


def flip_feedback(c):
    n = 0
    for k, ins in enumerate(list(c.data)):
        op = ins.operation
        if op.name != "if_else":
            continue
        blocks = []
        for blk in op.blocks:
            if blk is None:
                blocks.append(None)
                continue
            nb = blk.copy_empty_like()
            for x in blk.data:
                if x.operation.name == "rz":
                    g = x.operation.copy()
                    g.params = [-float(g.params[0])]
                    nb.append(g, x.qubits, x.clbits)
                    n += 1
                else:
                    nb.append(x.operation, x.qubits, x.clbits)
            blocks.append(nb)
        c.data[k] = ins.replace(operation=op.replace_blocks(blocks))
    return c, n


def x_before_read(c):
    from qiskit.circuit.library import XGate
    from qiskit.circuit import CircuitInstruction
    data = list(c.data)
    k = next(i for i, ins in enumerate(data) if ins.operation.name == "measure")
    c.data.insert(k, CircuitInstruction(XGate(), data[k].qubits, ()))
    return c


def mutate(src, work, tool, kind):
    from qiskit import qpy
    dst = os.path.join(work, f"mut_{kind}_{os.path.basename(src.rstrip(chr(92) + '/'))}")
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    names, cs = load(dst)
    hit = []
    floors_done = set()
    for i, name in enumerate(names):
        mt = re.fullmatch(r"ff_(ipe|tqpe)(\d)_(\d+)(_off|_floor)?", name)
        if not mt:
            continue
        fam, arm = mt.group(1), (mt.group(4) or "_ff")[1:]
        if kind == "swap" and fam == "tqpe" and arm == "ff":
            cs[i] = swap_reads(cs[i])
            hit.append(name)
        elif kind == "sign" and fam == "ipe" and arm == "ff":
            cs[i], k = flip_feedback(cs[i])
            if k:
                hit.append(name)
        elif kind == "floor_x" and arm == "floor" and fam not in floors_done and int(mt.group(3)) == 3:
            cs[i] = x_before_read(cs[i])
            floors_done.add(fam)
            hit.append(name)
    with open(os.path.join(dst, "job", "circuits.qpy"), "wb") as f:
        qpy.dump(cs, f)
    r = subprocess.run([sys.executable, tool, "check", dst], capture_output=True, text=True)
    last = (r.stdout.strip().splitlines() or ["(no output)"])[-1]
    failed = re.findall(r"'([^']+)'", last)
    print(f"{kind:8s} {os.path.basename(dst)}: damaged {len(hit)} arm(s); check exit {r.returncode}; {last[:60]}"
          f"{'...' if len(last) > 60 else ''}")
    print(f"         damaged but not failed: {sorted(set(hit) - set(failed)) or '-'}")
    print(f"         failed but not damaged: {sorted(set(failed) - set(hit)) or '-'}")
    if r.returncode not in (0, 1):
        print(r.stderr[-800:])
    return dict(kind=kind, damaged=hit, failed=failed, exit=r.returncode)


if __name__ == "__main__":
    src, work, tool = sys.argv[1:4]
    res = [mutate(src, work, tool, k) for k in ("swap", "sign", "floor_x")]
    if len(sys.argv) > 4:
        json.dump(res, open(sys.argv[4], "w"), indent=1)
