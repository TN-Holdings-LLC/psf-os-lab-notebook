"""Build the teleport comparison the ledger reads (desk only): the 2026-11-16 sequential teleport test
(psf_os.feedforward.teleport_test(D)) at distance D = 4, 8, 12, 16 beside the constant-depth form
(notes/ffapps_2026-11-17/apps.longrange(D / 2)) on one device record. The sentinel is at its Clifford point (never a
device job; the ledger skips it).

  python seqcmp.py DEVDIR OUT
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "ffapps_2026-11-17"))
sys.path.insert(0, os.path.join(HERE, "..", "rus_coherent_2026-11-17"))


def main(devdir, out):
    import apps
    from psf_os import feedforward as FF
    from psf_os.device import Device
    its = []
    for D in (4, 8, 12, 16):
        its.append((f"seq{D}", FF.teleport_test(D), dict(success={D: 0}, bound=0.75)))
        qc, s = apps.longrange(D // 2)
        its.append((f"lr{D // 2}", qc, dict(success=s, bound=0.75)))
    rep = FF.build(Device.load(devdir), its, out, shots=4000, max_seconds=400,
                   sentinel_spec=dict(kind="echo_clifford", D=24))
    for t, v in rep["items"].items():
        print(t, "CZ", v["cz"], "depth", v["depth"], "mid", v["mid"], "conditionals", v["conditionals"])


if __name__ == "__main__":
    main(*sys.argv[1:3])
