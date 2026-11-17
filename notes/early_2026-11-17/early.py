"""Early measurement: keep finished outputs in classical bits, where they do not decay (workplace prototype, 2026-11-17;
owner "早いほうが作って"; desk only, not declared, psf-os unchanged).

The 1950s lesson (owner): the fix for memories that lose their contents was a memory that keeps them. A device with
mid-circuit measurements already has one: the classical register. The principle of deferred measurement read the other
way: a qubit that from some point on is used only as a control (and never measured otherwise, or measured at the end)
can be measured at that point; every later controlled gate becomes a gate conditioned on the bit. The distribution of
every other measured bit is unchanged.

In the neuron chain (psf_os.feedforward.rus_chain; the third design gpu/rus3_night.chain) neuron j-1's output is, after
its neuron, only the control of neuron j's input rotations. So:

  early chain   neuron j-1's output is read (flipped, as the third design reads its outputs) in the same layer as its
                own last ancilla measurement, into an extra bit e_{j-1} (e = 1 - output). Neuron j's first try rotates
                its ancilla only if e_{j-1} = 0 (output 1): the whole first attempt in one single-bit conditional (CY
                and S^dag act trivially on the ancilla's |0> when the rotation is skipped). Neuron j's retries need no condition
                on e_{j-1}: a retry runs only after a failed try, and a try fails only if the rotation ran (with the
                rotation skipped the ancilla stays |0> and reads success). So no conditional is nested, and IBM's rules
                hold (checked by psf_os.feedforward.analyse). While neuron j waits, only its own output is held
                flipped; no earlier output waits at all.

Bits: c[0 .. L m - 1] the tries and c[L m] the last output (read flipped) as in the third design; c[L m + 1 + j] = e_j
for j = 0 .. L - 2. The off arm given to feedforward.build is the third design's off arm (no retries, input rotations
coherent, the same qubits), widened to the same bits (the earlier outputs read at the end into the extra bits, which
changes nothing measured before): the ceiling of the compound prototype applies unchanged.

  python early.py identity                 exact joint distribution of (tries, last output) against the third design
  python early.py build DEVDIR OUT [--dry-clifford-sentinel]
  python early.py ledger OUT RD_OUT        time-budget ledger (decision latency 0 and 1 us), early chain against the
                                           third design (RD_OUT: a gpu/compound_night.py build)
  python early.py score OUT                the compound prototype's margin g = c - e per L and its slope
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NB = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (os.path.join(NB, "gpu"), os.path.join(NB, "notes", "rus_coherent_2026-11-17"),
          os.path.join(NB, "notes", "compound_2026-11-17"), os.path.join(NB, "notes", "timebudget_2026-11-17")):
    sys.path.insert(0, p)

THETA, M = 1.1, 2
LS = (1, 2, 3, 4, 5)


def _first_try(qc, a, o, theta, e):
    """Neuron's first attempt; e is None (no input) or the bit e_{j-1}: the whole attempt in one conditional, run only
    when e = 0 (output 1); with the rotation skipped CY and S^dag would act trivially on the ancilla's |0> anyway."""
    if e is None:
        qc.ry(2 * theta, a)
        qc.cy(a, o)
        qc.sdg(a)
        qc.ry(-2 * theta, a)
        return
    with qc.if_test((e, 0)):
        qc.ry(2 * theta, a)
        qc.cy(a, o)
        qc.sdg(a)
        qc.ry(-2 * theta, a)


def _retry(qc, a, o, theta):
    qc.ry(math.pi / 2, o)
    qc.x(a)
    qc.ry(2 * theta, a)
    qc.cy(a, o)
    qc.sdg(a)
    qc.ry(-2 * theta, a)


def chain_early(L, theta=THETA, m=M):
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
    from psf_os import feedforward as FF
    nb = L * m + 1 + (L - 1)
    q, c = QuantumRegister(2 * L, "q"), ClassicalRegister(nb, "c")
    qc = QuantumCircuit(q, c)
    for j in range(L):
        a, o = 2 * j, 2 * j + 1
        e = None if j == 0 else c[L * m + j]                   # e_{j-1} sits in c[L m + 1 + (j - 1)]
        _first_try(qc, a, o, theta, e)
        for r in range(m):
            if r > 0:
                qc.barrier(a, o)
                with qc.if_test((c[j * m + r - 1], 1)):
                    _retry(qc, a, o, theta)
                qc.barrier(a, o)
            qc.x(o)                                            # the output held flipped while the ancilla is read
            qc.barrier(a, o)
            qc.measure(a, j * m + r)
            if r == m - 1 and j < L - 1:
                qc.measure(o, L * m + 1 + j)                   # finished: read flipped into e_j, same layer
            qc.barrier(a, o)
            if not (r == m - 1 and j < L - 1):
                qc.x(o)
    qc.x(2 * L - 1)                                            # the last output read flipped (third design)
    qc.measure(2 * L - 1, L * m)
    spec = dict(kind="rus", L=L, theta=theta, m=m, out_bit=L * m,
                tries=[list(range(j * m, j * m + m)) for j in range(L)], exact=math.sin(FF.rus_q(theta)) ** (2 * L),
                form="blocks")
    return qc, spec


def chain_reuse(L, theta=THETA, m=M):
    """The early chain on two qubits for every L: after neuron j has been read (ancilla bit, output bit e_j), each
    read qubit is set back to |0> by an X conditioned on its own bit (two single-bit conditionals, gates only), and
    neuron j + 1 runs on the same two qubits. Bits as in chain_early."""
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
    from psf_os import feedforward as FF
    nb = L * m + 1 + (L - 1)
    q, c = QuantumRegister(2, "q"), ClassicalRegister(nb, "c")
    qc = QuantumCircuit(q, c)
    a, o = 0, 1
    for j in range(L):
        e = None if j == 0 else c[L * m + j]
        if e is not None:
            with qc.if_test((e, 1)):                           # the output qubit reads |e>: back to |0>
                qc.x(o)
            with qc.if_test((c[(j - 1) * m + m - 1], 1)):      # the ancilla reads its last try's bit: back to |0>
                qc.x(a)
        _first_try(qc, a, o, theta, e)
        for r in range(m):
            if r > 0:
                qc.barrier(a, o)
                with qc.if_test((c[j * m + r - 1], 1)):
                    _retry(qc, a, o, theta)
                qc.barrier(a, o)
            qc.x(o)
            qc.barrier(a, o)
            qc.measure(a, j * m + r)
            if r == m - 1 and j < L - 1:
                qc.measure(o, L * m + 1 + j)
            qc.barrier(a, o)
            if not (r == m - 1 and j < L - 1):
                qc.x(o)
    qc.x(o)
    qc.measure(o, L * m)
    spec = dict(kind="rus", L=L, theta=theta, m=m, out_bit=L * m,
                tries=[list(range(j * m, j * m + m)) for j in range(L)], exact=math.sin(FF.rus_q(theta)) ** (2 * L),
                form="blocks")
    return qc, spec


def rd_chain(L, theta=THETA, m=M):
    import rus3_night as R3
    return R3.chain(L, theta, m=m)


def off_arm(L, theta=THETA, m=M):
    """The third design's off arm (no retries, coherent input rotations), widened to the early chain's bits."""
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
    from psf_os import feedforward as FF
    rd, _ = rd_chain(L, theta, m)
    off = FF.strip_conditionals(FF.lower(rd))
    nb = L * m + 1 + (L - 1)
    w = QuantumCircuit(QuantumRegister(off.num_qubits, "q"), ClassicalRegister(nb, "c"))
    w.compose(off, qubits=list(range(off.num_qubits)), clbits=list(range(off.num_clbits)), inplace=True)
    for j in range(L - 1):                                     # the extra bits: earlier outputs read at the end
        w.measure(2 * j + 1, L * m + 1 + j)                    # (beside only; they change nothing measured before)
    return w


def marginal(dist, nbits_keep, nbits_total):
    out = {}
    for k, p in dist.items():
        kk = k[nbits_total - nbits_keep:]                      # keep c[nbits_keep - 1] .. c[0]
        out[kk] = out.get(kk, 0.0) + p
    return out


def identity(Ls=(1, 2, 3)):
    import coherent as CO
    from psf_os import feedforward as FF
    rows = []
    for L in Ls:
        r, _ = rd_chain(L)
        dr = CO.branch_distribution(FF.lower(r))
        for form, fn in (("early", chain_early), ("reuse", chain_reuse)):
            e, _ = fn(L)
            de = CO.branch_distribution(FF.lower(e))
            keep = L * M + 1
            me = marginal(de, keep, e.num_clbits)
            tv = CO.tvd(me, dr)
            an = FF.analyse(e, "blocks")
            rows.append(dict(L=L, form=form, qubits=e.num_qubits, tvd=float(tv), conditionals=an.get("conditionals"),
                             ok=bool(tv < 1e-12)))
            print(f"L {L} {form} ({e.num_qubits} qubits): joint distribution of (tries, last output) against the third "
                  f"design: total variation {tv:.2e}; IBM rules (analyse, form blocks): passed; conditionals "
                  f"{an.get('conditionals')}")
    return rows


def items(Ls=LS, reuse=False):
    """ea{L}: the early chain, off arm = the third design's (so the device's off arm is the ceiling's circuit). eb{L}:
    the two-qubit chain; its off arm is the default (conditionals removed, beside only): the third design's off arm
    needs 2L qubits, and the ceiling c(L) is a noiseless number of that circuit, so the margin g is read the same way."""
    out = []
    for L in Ls:
        if reuse:
            qc, spec = chain_reuse(L)
            out.append((f"eb{L}", qc, spec))
        else:
            qc, spec = chain_early(L)
            spec["off_circuit"] = off_arm(L)
            out.append((f"ea{L}", qc, spec))
    return out


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("identity")
    b = sub.add_parser("build")
    b.add_argument("devdir")
    b.add_argument("out")
    b.add_argument("--dry-clifford-sentinel", action="store_true")
    b.add_argument("--reuse", action="store_true", help="the two-qubit chain (eb) instead of the early chain (ea)")
    lg = sub.add_parser("ledger")
    lg.add_argument("out")
    lg.add_argument("rd_out")
    sub.add_parser("score").add_argument("out")
    a = ap.parse_args()
    if a.cmd == "identity":
        rows = identity()
        json.dump(rows, open(os.path.join(HERE, "identity.json"), "w"), indent=1)
    elif a.cmd == "build":
        from psf_os import feedforward as FF
        from psf_os.device import Device
        spec = dict(kind="echo_clifford", D=24) if a.dry_clifford_sentinel else None
        rep = FF.build(Device.load(a.devdir), items(reuse=a.reuse), a.out, shots=4000, max_seconds=60, sentinel_spec=spec)
        print(json.dumps({k: rep[k] for k in ("device", "circuits", "qpu_seconds_model")}))
        for t, v in rep["items"].items():
            print(t, "chain", v["chain"], "CZ", v["cz"], "off CZ", v["off_cz"], "depth", v["depth"], "mid", v["mid"],
                  "conditionals", v["conditionals"])
    elif a.cmd == "ledger":
        import ledger as LG
        res = {}
        for lat in (0.0, 1.0):
            E = LG.job_ledgers(a.out, lat, roles=("user",))
            R = LG.job_ledgers(a.rd_out, lat, roles=("user",))
            pre = "ff_eb" if any(k.startswith("ff_eb") for k in E) else "ff_ea"
            print(f"decision latency {lat} us (1 us hypothetical). wait in qubit-us; T in us (JIT)")
            print("L | rd: conditionals in a row / T / wait ASAP / wait JIT | early: the same")
            for L in LS:
                r, e = R[f"ff_rd{L}"], E[f"{pre}{L}"]
                res.setdefault(str(lat), {})[L] = dict(rd=r, early=e)
                print(f"{L} | {r['jit']['dec_depth']} / {r['jit']['T_us']:.1f} / {r['asap']['wait_qus']:.1f} / "
                      f"{r['jit']['wait_qus']:.1f} | {e['jit']['dec_depth']} / {e['jit']['T_us']:.1f} / "
                      f"{e['asap']['wait_qus']:.1f} / {e['jit']['wait_qus']:.1f}")
        name = "ledger_reuse_vs_rd.json" if pre == "ff_eb" else "ledger_early_vs_rd.json"
        json.dump(res, open(os.path.join(HERE, name), "w"), indent=1)
    elif a.cmd == "score":
        import compound as CP
        import rus3_night as R3
        from psf_os import feedforward as FF
        ref = {int(k): v for k, v in json.load(open(os.path.join(NB, "notes", "compound_2026-11-17",
                                                                    "ideal.json"))).items()}
        cards = FF.cards(a.out)
        rows = {}
        pre = "eb" if any(k.startswith("eb") for k in cards) else "ea"
        for L in LS:
            c = R3.relabel(cards[f"{pre}{L}"])
            rows[L] = dict(CP.margin(c, ref[L]), off=c["off"]["p1"], sentinel=c["sentinel"])
            r = rows[L]
            print(f"L {L}: ff {r['p_ff']:.3f} (noiseless rd {ref[L]['ff']:.3f})  g {r['g']:+.3f} (2 SE {2 * r['se']:.3f}) "
                  f"-> {r['ceiling_verdict']}; off {r['off']:.3f} (noiseless {ref[L]['off']:.3f}); sentinel {r['sentinel']}")
        b_, sb = CP.slope(list(LS), [rows[L]["g"] for L in LS], [rows[L]["se"] for L in LS])
        print(f"slope of g {b_:+.4f} per step (2 SE {2 * sb:.4f})")
        json.dump(dict(rows=rows, slope=b_, se=sb), open(os.path.join(a.out, "early_scores.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
