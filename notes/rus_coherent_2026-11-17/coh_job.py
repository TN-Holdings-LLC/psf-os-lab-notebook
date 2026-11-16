"""Draft tool (not declared) for the first coherent test: one job with the coherent repeat-until-success neuron
(zipper+, no mid-circuit measurement) and the third design of 2026-11-16 (rd, mid-circuit measurements), L = 1, m = 2,
theta 1.1, both through psf_os.feedforward.build (ff, off, floor arms, one ring sentinel; for the coherent item the
off arm is the same line with try 0 only, given explicitly; for rd the off arm is its circuit without conditionals).
  python coh_job.py build DEVDIR OUT [--dry-clifford-sentinel]
  python coh_job.py score OUT            (cards; rd read with its declared relabelling; no verdict here)
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "gpu"))
import coherent as CO  # noqa: E402

THETA, L, M = 1.1, 1, 2


def coherent_item(L=L, m=M, theta=THETA):
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
    from psf_os import feedforward as FF

    def with_meas(line, meas):
        b = CO.to_basis(line)
        qc = QuantumCircuit(QuantumRegister(b.num_qubits, "q"), ClassicalRegister(L * m + 1, "c"))
        qc.compose(b, inplace=True)
        for p, bit in meas:
            qc.measure(p, bit)
        return qc
    ff = with_meas(*CO.zipper(L, theta, m, plus=True))
    off_line, off_meas = CO.zipper(L, theta, m, plus=True, tries=1)
    off = with_meas(off_line, off_meas)
    spec = dict(kind="rus", L=L, theta=theta, m=m, out_bit=L * m,
                tries=[list(range(j * m, j * m + m)) for j in range(L)], exact=math.sin(FF.rus_q(theta)) ** (2 * L),
                off_circuit=off)
    return ff, spec


def items():
    import rus3_night as R3
    return [("coh1", *coherent_item()), ("rd1", *R3.chain(L, THETA, m=M))]


def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None
    rep = FF.build(Device.load(a.devdir), items(), a.out, shots=4000, sentinel_spec=spec)
    print(json.dumps({k: rep[k] for k in ("device", "circuits", "qpu_seconds_model") if k in rep}))
    print(json.dumps({t: (v["chain"], v["cz"], v["off_cz"], v["depth"], v["mid"]) for t, v in rep["items"].items()}))


def score(a):
    from psf_os import feedforward as FF
    import rus3_night as R3
    cards = FF.cards(a.out)
    out = {}
    for tag in ("coh1", "rd1"):
        c = R3.relabel(cards[tag]) if tag == "rd1" else cards[tag]
        out[tag] = c
        print(f"{tag}: exact {c['exact']:.4f}; ff {c['ff']['p1']:.4f} (2 SE {c['ff']['two_se']:.4f}, still failed "
              f"{c['ff']['still_failed_after_m']:.4f}); off {c['off']['p1']:.4f}; post {c['post']['p1']:.4f} (kept "
              f"{c['post']['kept_share']:.4f}); floor {c['floor']['all_zero']:.4f}; sentinel {c['sentinel']}")
    json.dump(out, open(os.path.join(a.out, "coh_scores.json"), "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    b.add_argument("--dry-clifford-sentinel", action="store_true")
    sub.add_parser("score").add_argument("out")
    a = ap.parse_args()
    {"build": build, "score": score}[a.cmd](a)
