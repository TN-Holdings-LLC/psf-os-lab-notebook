"""The next step after T1 (draft for a declaration; workplace Claude, 2026-11-17, home instruction 17f 1a): the
repeat-until-success neuron without mid-circuit measurements at L = 2 and 3, beside the third design. To be used if T1's
coh1 is CLOSER WITH CONTROL. Not declared; the numbers and verdict words are the owner's.

  python gpu/coh2_night.py ideal                   exact identities and the noiseless table (no sampling)
  python gpu/coh2_night.py build DEVDIR OUT [--dry-clifford-sentinel]
  python gpu/coh2_night.py check OUT
  python gpu/coh2_night.py score OUT

Items (theta 1.1, m = 2, 4000 shots):
  coh{L}  the workplace's zipper+ line (notes/rus_coherent_2026-11-17/coherent.zipper(L, 1.1, 2, plus=True)), no
          mid-circuit measurement; output read flipped (X before its measurement) and relabelled 1 - bit, as in T1.
          Its off arm (given explicitly): every neuron runs try 0 only, and its output is then moved onto the line
          position the ff arm's output reaches (2 CX per step onto the untouched |0>s), so that the next neuron's
          control stands next to its block and the last output is read on the same physical qubit as in the ff arm
          (checked by `check`). This extends T1's off arm (coherent.zipper(tries=1) is L = 1 only).
  rd{L}   the third design of 2026-11-16 (gpu/rus3_night.chain(L, 1.1, 2)), read with its declared relabelling.
Verdict per item (as T1): gpu/rus_night.verdict on the relabelled cards (CLOSER WITH CONTROL / NOT CLOSER).
Beside (never judged): |P_ff - noiseless| of each item, rd minus coh, with its two SE.
Reference values: notes/compound_2026-11-17/ideal.json (the third design's exact noiseless ff and off, read as
declared), which `ideal` shows to be also coh{L}'s (exact identities)."""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(NB, "notes", "rus_coherent_2026-11-17"))
sys.path.insert(0, HERE)

THETA, M = 1.1, 2
LS = (2, 3)
SHOTS = 4000
TOL = 0.03


def ref():
    return {int(k): v for k, v in json.load(open(os.path.join(NB, "notes", "compound_2026-11-17",
                                                              "ideal.json"))).items()}


def off_line(L, theta=THETA, m=M):
    """Each neuron: try 0 only (zipper+ gates), then its output moved from base + 1 to base + m, where the ff arm's
    output stands after its m tries. Same line length as coherent.zipper(L, theta, m)."""
    from qiskit import QuantumCircuit
    import coherent as CO
    qc = QuantumCircuit(L * (m + 1))
    for j in range(L):
        base = j * (m + 1)
        ctrl = base - 1 if j > 0 else None
        a, o = base, base + 1
        if ctrl is None:
            qc.ry(2 * theta, a)
        else:
            CO._prep_from_zero(qc, 2 * theta, ctrl, a)
        qc.cy(a, o)
        qc.sdg(a)
        if ctrl is None:
            qc.ry(-2 * theta, a)
        else:
            CO._cry_up_to_phase(qc, -2 * theta, ctrl, a)
        for p in range(o, base + m):
            CO._move(qc, p, p + 1)
    return qc


def _finish(line, meas, out_pos, m, L):
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
    import coherent as CO
    b = CO.to_basis(line)
    qc = QuantumCircuit(QuantumRegister(b.num_qubits, "q"), ClassicalRegister(L * m + 1, "c"))
    qc.compose(b, inplace=True)
    qc.x(out_pos)                                       # read the output flipped (relabelled 1 - bit in the score)
    for p, bit in meas:
        qc.measure(p, bit)
    return qc


def coherent_item(L, theta=THETA, m=M):
    import coherent as CO
    from psf_os import feedforward as FF
    ff_line, ff_meas = CO.zipper(L, theta, m, plus=True)
    out_pos = dict((bit, p) for p, bit in ff_meas)[L * m]
    ff = _finish(ff_line, ff_meas, out_pos, m, L)
    off = _finish(off_line(L, theta, m), ff_meas, out_pos, m, L)     # the same measured positions as the ff arm
    spec = dict(kind="rus", L=L, theta=theta, m=m, out_bit=L * m, tries=[list(range(j * m, j * m + m)) for j in range(L)],
                exact=math.sin(FF.rus_q(theta)) ** (2 * L), off_circuit=off)
    return ff, spec


def items(Ls=LS):
    import rus3_night as R3
    out = []
    for L in Ls:
        out.append((f"coh{L}", *coherent_item(L)))
        out.append((f"rd{L}", *R3.chain(L, THETA, m=M)))
    return out


def _p_out_dist(dist, n, bit):
    """P(output 1, read as declared) = 1 - P(bit = 1) from an exact {bitstring: p}."""
    return 1 - sum(p for k, p in dist.items() if k[n - 1 - bit] == "1")


def _marg(dist, n, bits):
    out = {}
    for k, p in dist.items():
        kk = "".join(k[n - 1 - b] for b in bits)
        out[kk] = out.get(kk, 0.0) + p
    return out


def ideal():
    """Exact: coh{L}'s joint distribution of (ancilla bits, output bit) against the third design's (ff arms; off arms:
    the try-0 bits and the output); and the noiseless values read as declared."""
    import coherent as CO
    import rus3_night as R3
    from psf_os import feedforward as FF
    R = ref()
    rows = {}
    for L in LS:
        ff, spec = coherent_item(L)
        rd, _ = R3.chain(L, THETA, m=M)
        n = L * M + 1
        d_coh = {"ff": CO.branch_distribution(ff), "off": CO.branch_distribution(spec["off_circuit"])}
        d_rd = {"ff": CO.branch_distribution(FF.lower(rd)),
                "off": CO.branch_distribution(FF.strip_conditionals(FF.lower(rd)))}
        row = dict(exact=spec["exact"])
        keep_off = [j * M for j in range(L)] + [L * M]  # off arms: try-0 bits and the output (the retry bits differ
                                                         # by construction: rd re-reads its ancilla, coh's stay |0>)
        for arm in ("ff", "off"):
            if arm == "ff":
                row[f"tvd_{arm}"] = float(CO.tvd(d_coh[arm], d_rd[arm]))
            else:
                row[f"tvd_{arm}"] = float(CO.tvd(_marg(d_coh[arm], n, keep_off), _marg(d_rd[arm], n, keep_off)))
            row[f"coh_{arm}"] = _p_out_dist(d_coh[arm], n, L * M)
            row[f"rd_{arm}"] = _p_out_dist(d_rd[arm], n, L * M)
            row[f"ref_{arm}"] = R[L][arm]
        rows[L] = row
        print(f"L {L}: exact {row['exact']:.4f}; ff coh {row['coh_ff']:.4f} rd {row['rd_ff']:.4f} (ideal.json "
              f"{R[L]['ff']:.4f}), joint TVD {row['tvd_ff']:.1e}; off coh {row['coh_off']:.4f} rd {row['rd_off']:.4f} "
              f"(ideal.json {R[L]['off']:.4f}), joint TVD (try-0 bits, output) {row['tvd_off']:.1e}")
    return rows


def build(a):
    from psf_os import feedforward as FF
    from psf_os.device import Device
    spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None   # dry runs only, never a device
    rep = FF.build(Device.load(a.devdir), items(), a.out, shots=SHOTS, max_seconds=60, sentinel_spec=spec)
    print(json.dumps({k: rep[k] for k in ("device", "circuits", "qpu_seconds_model", "shots") if k in rep}))
    for t, v in rep["items"].items():
        print(t, "chain", v["chain"], "CZ", v["cz"], "off CZ", v["off_cz"], "depth", v["depth"], "mid", v["mid"],
              "conditionals", v["conditionals"])


def check(a):
    """Noiseless Aer of every arm but the sentinel, read as declared, against ideal.json; floor arms all zero; the coh
    items' ff and off arms read the output on the same physical qubit."""
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    from psf_os import feedforward as FF
    R = ref()
    m = json.load(open(os.path.join(a.out, "job", "manifest.json")))
    cs = qpy.load(open(os.path.join(a.out, "job", "circuits.qpy"), "rb"))
    i, bad, lines, readq = 0, [], [], {}
    for cell in m["cells"]:
        for _ in range(cell["points"]):
            c = cs[i]
            i += 1
            if cell["role"] == "sentinel":
                continue
            tag = cell["name"][3:].replace("_floor", "").replace("_off", "")
            L = int(tag[-1])
            cc = FF.compact(c)
            n = cc.num_clbits
            cnt = AerSimulator().run(cc, shots=SHOTS, seed_simulator=20261117).result().get_counts()
            tot = sum(cnt.values())
            p1 = 1 - sum(v for k, v in cnt.items() if FF._bits(k, n)[L * M] == 1) / tot
            allz = sum(v for k, v in cnt.items() if set(FF._bits(k, n)) == {0}) / tot
            if cell["role"] == "floor":
                ok, r = allz == 1.0, "all zero 1"
            else:
                arm = "ff" if cell["role"] == "user" else "off"
                ok, r = abs(p1 - R[L][arm]) <= TOL, f"ref {R[L][arm]:.3f}"
            if tag.startswith("coh") and cell["role"] in ("user", "off"):
                readq[cell["name"]] = [c.find_bit(x.qubits[0]).index for x in c.data
                                       if x.operation.name == "measure" and c.find_bit(x.clbits[0]).index == L * M]
            lines.append(f"{cell['name']:16s} {cell['role']:6s} P(out 1, read as declared) {p1:.3f}  all zero "
                         f"{allz:.3f}  ({r}) {'ok' if ok else 'FAIL'}")
            bad += [] if ok else [cell["name"]]
    for L in LS:
        f, o = readq.get(f"ff_coh{L}"), readq.get(f"ff_coh{L}_off")
        same = bool(f) and f == o
        lines.append(f"coh{L} output read on physical qubit: ff {f}, off {o} {'ok' if same else 'FAIL'}")
        bad += [] if same else [f"coh{L} readout qubit"]
    print("\n".join(lines))
    print("PASS" if not bad else f"FAIL {bad}")
    return not bad


def score(a):
    from psf_os import feedforward as FF
    import rus3_night as R3
    from rus_night import verdict
    R = ref()
    cards = FF.cards(a.out)
    out = dict(cards={}, beside={})
    for L in LS:
        for tag in (f"coh{L}", f"rd{L}"):
            c = R3.relabel(cards[tag])
            d, se, v = verdict(c)
            c.update(d=d, se_d=se, d_in_se=d / se if se > 0 else None, verdict=v,
                     loss_vs_noiseless=c["ff"]["p1"] - R[L]["ff"])
            out["cards"][tag] = c
            print(f"{tag}: exact {c['exact']:.4f}; ff {c['ff']['p1']:.4f} (noiseless {R[L]['ff']:.4f}, loss "
                  f"{c['ff']['p1'] - R[L]['ff']:+.4f}); off {c['off']['p1']:.4f} (noiseless {R[L]['off']:.4f}); "
                  f"d {d:.4f} (2 SE_d {2 * se:.4f}) -> {v}; floor all zero {c['floor']['all_zero']:.4f}; "
                  f"sentinel {c['sentinel']}")
        f, r = out["cards"][f"coh{L}"]["ff"], out["cards"][f"rd{L}"]["ff"]
        gap = abs(r["p1"] - R[L]["ff"]) - abs(f["p1"] - R[L]["ff"])
        se = math.sqrt(f["p1"] * (1 - f["p1"]) / f["counted"] + r["p1"] * (1 - r["p1"]) / r["counted"])
        out["beside"][L] = dict(coh_closer_to_noiseless_by=gap, two_se=2 * se)
        print(f"beside L {L}: |rd - noiseless| - |coh - noiseless| = {gap:+.4f} (2 SE {2 * se:.4f})")
    V = {t: out["cards"][t]["verdict"] for t in out["cards"]}
    out["verdicts"] = V
    print("verdicts:", V)
    json.dump(out, open(os.path.join(a.out, "coh2_scores.json"), "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ideal")
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    b.add_argument("--dry-clifford-sentinel", action="store_true",
                   help="dry runs only: the ring sentinel at its Clifford point; never for the device job")
    for nm in ("check", "score"):
        sub.add_parser(nm).add_argument("out")
    a = ap.parse_args()
    if a.cmd == "ideal":
        rows = ideal()
        json.dump({str(k): v for k, v in rows.items()}, open(os.path.join(NB, "notes", "rus_coherent_2026-11-17",
                                                                          "coh2_ideal.json"), "w"), indent=1)
        sys.exit(0)
    r = {"build": build, "check": check, "score": score}[a.cmd](a)
    sys.exit(0 if r is not False else 1)
