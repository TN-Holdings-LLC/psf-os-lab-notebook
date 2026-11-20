"""The wait footprint (psf_os.footprint, psf-os after-2026-11-20) of the circuits the declared tests of 2026-11-16 to
2026-11-19 used, as written (logical qubits, noiseless, every branch). Workplace Claude, 2026-11-20. It reads the
circuits only: no record, no noise model, no calibration number.

  python notes/footprint_2026-11-20/table.py > notes/footprint_2026-11-20/table.txt
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, "..", ".."))
for d in ("gpu", "notes/ffapps_2026-11-17", "notes/rus_coherent_2026-11-17", "notes/os2_2026-11-18"):
    sys.path.insert(0, os.path.join(NB, d))

from psf_os import feedforward as FF  # noqa: E402
from psf_os.footprint import wait_footprint  # noqa: E402


def _c(x):
    return x if hasattr(x, "data") else x[0]


def row(name, qc):
    qc = FF.lower(qc)
    r = wait_footprint(qc)
    cz = sum(1 for n, _ in FF.walk(qc) if n == "cz")
    cond = sum(1 for n, _ in FF.walk(qc) if n == "if_else")
    per = [len(w["carriers"]) for w in r["waits"]]
    print(f"| {name} | {len(r['qubits'])} | {cz} | {cond} | {len(per)} | {r['max']} | {r['total']} | "
          f"{r['excited_waits']:.2f} | {per if len(per) <= 12 else str(per[:12])[:-1] + ', ...]'} |")


def main():
    import rus2_night as R2
    import rus3_night as R3
    import apps as AP
    import repcode_night as RC
    import repcode2_night as RC2
    import repcode4_night as RC4
    print("| circuit (night of first use) | qubits | CZ written | conditionals | waits | max carriers | carrier-waits | "
          "excited-waits | carriers per wait |")
    print("|---|---|---|---|---|---|---|---|---|")
    for k in (1, 2):
        t = FF.teleport_test(k)
        row(f"teleport k = {k} (11-16)", t if hasattr(t, "data") else t[0])
    for L in (1, 2, 3):
        row(f"neuron P0, m = 3, L = {L} (11-16, rus_chain)", _c(FF.rus_chain(L, 1.1, m=3)))
        row(f"neuron P1 (hold flipped), m = 2, L = {L} (11-17, flip_chain)", _c(R2.flip_chain(L, 1.1, m=2)))
        row(f"neuron P2 / rd (read flipped), m = 2, L = {L} (11-17, rus3 chain)", _c(R3.chain(L, 1.1, m=2)))
        row(f"neuron NF (no flip), m = 2, L = {L} (11-17)", _c(R2.flip_chain(L, 1.1, m=2, flip=False)))
    for n in (2, 3, 4, 5, 6):
        row(f"IPE n = {n}, phase 1 / 2^n (11-17 / 11-19)", AP.ipe(n, 1, True)[0])
    import qpe_repro_night as Q
    for n in (2, 4):
        row(f"textbook QPE n = {n}, phase 1 / 2^n (11-19; final measurements only)", Q.textbook_logical(n, 1)[0])
    for e in ("n", "0"):
        row(f"repetition code lut3, error {e}, 16 CZ (11-19)", RC.circuit(e, RC.TABLE3)[0])
        row(f"repetition code lut3, error {e}, 10 CZ (repcode2)", RC2.circuit(e, RC2.TABLE3)[0])
        for f in ("F6P", "F6"):
            row(f"repetition code lut3, error {e}, {f} (repcode4)", RC4.circuit(f, e)[0])


if __name__ == "__main__":
    main()
