"""The excited count at the waits (the footprint's, as the parking impact table counted it) split into the waiting
qubits by kind and the qubits that take part in the wait (measured there or inside its conditionals: not waiting)."""
import json
import os
import sys

nb = sys.argv[1]
im = json.load(open(os.path.join(nb, "notes/park_default_2026-11-21/impact.json")))
ev = json.load(open(os.path.join(nb, "notes/evacuate_2026-11-21/table.json")))
lines = []
for k in ev:
    tot = im[k]["summary"]["excited_before"]
    e = ev[k]["summary"]["excited"]
    s = sum(e.values())
    n = ev[k]["summary"]["items"]
    lines.append(f"{k}: {n} items; excited at the waits {tot:.2f} ({tot / n:.2f} per item) = waiting qubits {s:.2f} "
                 f"(K {e['K']:.2f}, B {e['B']:.2f}, E {e['E']:.2f}, L {e['L']:.2f}) + taking part in the wait "
                 f"{tot - s:.2f}")
print("\n".join(lines))
open(sys.argv[2], "w").write("\n".join(lines) + "\n")
