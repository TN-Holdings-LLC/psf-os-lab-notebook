"""The wait footprint as SENT (compiled by psf-os's Compiler on the 2026-11-19 marrakesh record, rule C placement),
counted over the whole wait (span=True), plain and with psf-os after-2026-11-20's fence (a barrier on every qubit
before each mid-circuit read and after each run of conditionals). Workplace Claude, 2026-11-20, after the workplace
VS's finding (the written count is smaller than the sent one: the compiler merges gates across a wait). Circuits
only: no noise model, no calibration number.

  python notes/footprint_2026-11-20/sent.py > notes/footprint_2026-11-20/sent.txt
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, "..", ".."))
for d in ("gpu", "notes/ffapps_2026-11-17", "notes/rus_coherent_2026-11-17", "notes/os2_2026-11-18"):
    sys.path.insert(0, os.path.join(NB, d))

from psf_os import feedforward as FF  # noqa: E402
from psf_os.device import Device  # noqa: E402
from psf_os.footprint import fence_waits, wait_footprint  # noqa: E402

DEV = os.path.join(NB, "results", "loop-night-2026-11-19", "fetch_in", "ibm_marrakesh", "dev")


def _c(x):
    return x if hasattr(x, "data") else x[0]


def main():
    import apps as AP
    import repcode4_night as RC4
    import rus2_night as R2
    import rus3_night as R3
    dev = Device.load(DEV)
    comp = FF.Compiler(dev)

    def row(name, qc):
        qc = FF.lower(qc)
        ch = FF.place(dev, qc.num_qubits)["chain"]
        w = wait_footprint(qc, span=True)
        out = [name, f"{w['max']} / {w['total']}"]
        for c in (qc, fence_waits(qc)):
            cc = comp.run(FF.on_device(c, ch, dev.num_qubits))
            f = wait_footprint(cc, span=True)
            out += [f"{f['max']} / {f['total']}", str(FF.cz_count(cc)), str(cc.depth())]
        print("| " + " | ".join(out) + " |", flush=True)

    print("| circuit | written: max / total (span) | sent: max / total | CZ | depth | sent with fence: max / total | "
          "CZ | depth |")
    print("|---|---|---|---|---|---|---|---|")
    for k in (1, 2):
        row(f"teleport k = {k}", _c(FF.teleport_test(k)))
    for L in (1, 2, 3):
        row(f"neuron P0 m 3 L {L}", _c(FF.rus_chain(L, 1.1, m=3)))
        row(f"neuron P1 m 2 L {L}", _c(R2.flip_chain(L, 1.1, m=2)))
        row(f"neuron P2 m 2 L {L}", _c(R3.chain(L, 1.1, m=2)))
    for n in (2, 3, 4, 5, 6):
        row(f"IPE n {n} phase 1", AP.ipe(n, 1, True)[0])
    for f in RC4.FORMS:
        for e in RC4.ERRORS:
            row(f"repcode4 {f} error {e}", _c(RC4.circuit(f, e)))


if __name__ == "__main__":
    main()
