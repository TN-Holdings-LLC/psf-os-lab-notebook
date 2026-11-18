"""2. The two packing tests (results/parallel-night-2026-11-18), re-scored from raw_counts.json alone (home VS Claude,
2026-11-18; qiskit and numpy only).

Packed circuits are cut into items by their instructions alone (vlib.parts: qubits and bits joined by any instruction);
each part is matched to the single item whose circuit touches the same physical qubits; the output bit of every
circuit or part is read from the circuit (vlib.out_bit_general) and compared with the record's table afterwards.
Every read is 1 - bit (all items here hold logical 1 as |0>: rd and ea). Noiseless values: exact branching of the
single circuits. d = |s - v| - |p - v|, SE from the two binomial errors, a mean's 2 SE = 2 sqrt(sum SE^2) / k.
usage: python notes/verify_2026-11-18/v2_parallel.py   (from the notebook root)"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = "results/parallel-night-2026-11-18"
LINES = []


def say(s):
    print(s, flush=True)
    LINES.append(s)


def read_single(cell):
    c, phys = V.compact(cell["circuit"])
    ob, oq = V.out_bit_general(c)
    p, n = V.p_bit(cell["counts"], ob)
    return dict(P=1 - p, n=n, out_bit=ob, out_qubit=phys[oq], qubits=phys, circ=c,
                tries=V.tries_bits(c), counts=cell["counts"])


def read_packed(cell, singles):
    """{item: dict(P, n, qubits, bits, out_bit (global), still_failed)} for a packed circuit; items matched by qubits."""
    qc = cell["circuit"]
    ps, spanning = V.parts(qc)
    out = {}
    for qs, cs in ps:
        if not cs:
            continue
        match = [t for t, s in singles.items() if s["qubits"] == qs]
        sub = V.restrict(qc, qs, cs)
        ob, oq = V.out_bit_general(sub)
        m = V.marginal(cell["counts"], cs)
        p, n = V.p_bit(m, ob)
        tr = V.tries_bits(sub)
        still = sum(v for k, v in m.items() if any(all(k[len(k) - 1 - b] == "1" for b in t) for t in tr)) / n
        out[match[0] if len(match) == 1 else f"unmatched {qs}"] = dict(P=1 - p, n=n, qubits=qs, bits=cs,
                                                                       out_bit_global=cs[ob], out_bit_local=ob,
                                                                       out_qubit=qs[oq], still_failed=still,
                                                                       circ=sub)
    return out, spanning


def dse(s, ns, p, npk):
    return math.sqrt(s * (1 - s) / ns + p * (1 - p) / npk)


def still_failed(single):
    c = single["counts"]
    tot = sum(c.values())
    return sum(v for k, v in c.items() if any(all(k[len(k) - 1 - b] == "1" for b in t) for t in single["tries"])) / tot


def pa(home):
    job, man = V.load_job(os.path.join(ROOT, "pa"))
    tags = [f"rd{L}" for L in range(1, 6)] + [f"ea{L}" for L in range(1, 6)]
    singles_off = {t: read_single(job[f"ff_{t}_off"]) for t in tags}
    others = sorted(n for n in job if not any(n.startswith(f"ff_{t}") for t in tags) and not n.startswith("ksent"))
    say(f"P-A: single items {tags}; other cells (the bundle) {others}")
    bname = [n for n in others if n.endswith("_off")][0]
    rname = bname[:-4]
    packed, span = read_packed(job[bname], singles_off)
    repeat, _ = read_packed(job[rname], singles_off)
    say(f"  bundle off arm = {bname}, repeat (its ff arm) = {rname}; parts found {len(packed)}; barriers spanning two "
        f"parts {len(span)}")
    rec = job[bname]["record"]["bundle"]
    rows, ds, ses = {}, [], []
    for t in tags:
        s, p = singles_off[t], packed[t]
        v = 1 - V.p_bit_dist(V.branch_dist(s["circ"]), s["out_bit"])
        d = abs(s["P"] - v) - abs(p["P"] - v)
        se = dse(s["P"], s["n"], p["P"], p["n"])
        rt = [k for k, x in rec.items() if sorted(x["qubits"]) == p["qubits"]]
        rr = rec[rt[0]] if len(rt) == 1 else None
        r_ok = (rr is not None and len(rt) == 1,
                rr is not None and "rus" in rr and rr["bit_offset"] + rr["rus"]["out_bit"] == p["out_bit_global"])
        h = home["pa"]["rows"][t]
        rows[t] = dict(single=s["P"], packed=p["P"], repeat=repeat[t]["P"], v=v, d=d, two_se=2 * se,
                       record_qubits_match=r_ok[0], record_out_bit_match=r_ok[1])
        ds.append(d)
        ses.append(se)
        say(f"  {t}: single off {s['P']:.4f} [{h['single_off']:.4f}]  packed {p['P']:.4f} [{h['packed_off']:.4f}]  repeat "
            f"{repeat[t]['P']:.4f} [{h['packed_repeat']:.4f}]  v {v:.4f} [{h['noiseless_off']:.4f}]  d {d:+.4f} "
            f"[{h['d']:+.4f}] (2 SE {2 * se:.4f} [{h['two_se']:.4f}]); qubits {p['qubits']}, out bit {p['out_bit_global']}"
            f" (record {rt}: qubits {r_ok[0]}, bit {r_ok[1]})")
    m, mse = sum(ds) / len(ds), 2 * math.sqrt(sum(x * x for x in ses)) / len(ses)
    say(f"  P-A mean d_off {m:+.4f} (2 SE {mse:.4f}) -> "
        f"{'PACKING KEEPS LESS' if m <= -mse else 'PACKING KEEPS MORE' if m >= mse else 'SAME WITHIN ERROR'}")
    return dict(rows=rows, mean=m, two_se=mse)


def pb(home):
    job, man = V.load_job(os.path.join(ROOT, "pb"))
    sa, sb = read_single(job["ff_sa"]), read_single(job["ff_sb"])
    sb_off = read_single(job["ff_sb_off"])
    v = 1 - V.p_bit_dist(V.branch_dist(sa["circ"]), sa["out_bit"])
    v_b = 1 - V.p_bit_dist(V.branch_dist(sb["circ"]), sb["out_bit"])
    v_off = 1 - V.p_bit_dist(V.branch_dist(sb_off["circ"]), sb_off["out_bit"])
    say(f"P-B: sa on qubits {sa['qubits']} (out bit {sa['out_bit']}, qubit {sa['out_qubit']}) P {sa['P']:.4f}; sb on "
        f"{sb['qubits']} (out bit {sb['out_bit']}, qubit {sb['out_qubit']}) P {sb['P']:.4f}; noiseless rd2 {v:.4f} (on B "
        f"{v_b:.4f})")
    singles = {"A": sa, "B": sb}
    res = {}
    hp = home["pb"]
    for bn in ("B1", "B2", "B3"):
        cell = job[f"ff_{bn}"]
        packed, span = read_packed(cell, singles if bn != "B1" else {"A": sa, "B": sb_off})
        rec = cell["record"]["bundle"]
        say(f"  {bn}: parts {[(k, x['qubits'], x['bits']) for k, x in packed.items()]}; spanning barriers {len(span)}")
        for sub, info in rec.items():
            key = "A" if sorted(info["qubits"]) == sa["qubits"] else "B"
            x = packed[key]
            ok_q = sorted(info["qubits"]) == x["qubits"]
            ok_b = info["bit_offset"] + info["rus"]["out_bit"] == x["out_bit_global"] if "rus" in info else None
            say(f"     record {sub}: qubits {info['qubits']} bits {info['bit_offset']}..{info['bit_offset'] + info['clbits'] - 1}"
                f" -> read from the circuit: part {key} qubits {x['qubits']} bits {x['bits'][0]}..{x['bits'][-1]}, output "
                f"bit {x['out_bit_global']} on qubit {x['out_qubit']} (agree: qubits {ok_q}, output bit {ok_b})")
        items = ["A"] if bn == "B1" else ["A", "B"]
        ds, ses = [], []
        for k in items:
            ref = sa if k == "A" else sb
            x = packed[k]
            d = abs(ref["P"] - v) - abs(x["P"] - v)
            se = dse(ref["P"], ref["n"], x["P"], x["n"])
            ds.append(d)
            ses.append(se)
            tagname = f"{bn.lower()}{k.lower()}"
            say(f"     {tagname}: alone {ref['P']:.4f}  packed {x['P']:.4f}  d {d:+.4f} (2 SE {2 * se:.4f}); still failing "
                f"after 2 tries: alone {still_failed(ref):.3f}, packed {x['still_failed']:.3f}")
            res[tagname] = dict(alone=ref["P"], packed=x["P"], d=d, two_se=2 * se, still_alone=still_failed(ref),
                                still_packed=x["still_failed"], qubits=x["qubits"], out_bit=x["out_bit_global"])
        m, mse = sum(ds) / len(ds), 2 * math.sqrt(sum(s * s for s in ses)) / len(ses)
        verdict = 'PACKED KEEPS LESS' if m <= -mse else 'PACKED KEEPS MORE' if m >= mse else 'SAME WITHIN ERROR'
        say(f"     {bn} mean d {m:+.4f} (2 SE {mse:.4f}) -> {verdict}")
        res[bn] = dict(mean=m, two_se=mse, verdict=verdict)
        if bn == "B1":
            xb = packed["B"]
            d = abs(sb_off["P"] - v_off) - abs(xb["P"] - v_off)
            say(f"     B1's B (rd2 off packed) {xb['P']:.4f} against sb off {sb_off['P']:.4f} (noiseless {v_off:.4f}): d "
                f"{d:+.4f} (2 SE {2 * dse(sb_off['P'], sb_off['n'], xb['P'], xb['n']):.4f})")
    # the swap test: what if the output bits of A and B were exchanged?
    for bn in ("B2", "B3"):
        cell = job[f"ff_{bn}"]
        packed, _ = read_packed(cell, singles)
        a, b = packed["A"], packed["B"]
        say(f"  {bn} cross-read check: A's part read with B's bit layout would give P(A) from bit {b['out_bit_global']} = "
            f"{1 - V.p_bit(cell['counts'], b['out_bit_global'])[0]:.4f}, B from bit {a['out_bit_global']} = "
            f"{1 - V.p_bit(cell['counts'], a['out_bit_global'])[0]:.4f} (as read: A {a['P']:.4f}, B {b['P']:.4f})")
    # per bit: where does A lose? (ff and off arms, alone against packed)
    say("  per bit P(1), alone -> packed (2 SE of the difference); bits of rd2: tries of neuron 0, tries of neuron 1, output")
    for arm in ("", "_off"):
        refs = {"A": read_single(job[f"ff_sa{arm}"]), "B": read_single(job[f"ff_sb{arm}"])}
        for bn in ("B2", "B3"):
            packed, _ = read_packed(job[f"ff_{bn}{arm}"], refs)
            for k in ("A", "B"):
                ref, x = refs[k], packed[k]
                mx = V.marginal(job[f"ff_{bn}{arm}"]["counts"], x["bits"])
                cells = []
                for b in range(len(x["bits"])):
                    p0, n0 = V.p_bit(ref["counts"], b)
                    p1, n1 = V.p_bit(mx, b)
                    cells.append(f"{p0:.3f}->{p1:.3f} ({p1 - p0:+.3f}, {2 * dse(p0, n0, p1, n1):.3f})")
                say(f"     {bn}{arm or ' ff'} {k}: " + "; ".join(cells))
    return res


def main():
    home = json.load(open(os.path.join(ROOT, "parallel_scores.json")))
    r = dict(pa=pa(home), pb=pb(home))
    hb = home["pb"]
    say("home P-B numbers (from parallel_scores.json): " + json.dumps(
        {k: (round(v["d"], 4) if isinstance(v, dict) and "d" in v else v) for k, v in hb.get("rows", hb).items()}
        if isinstance(hb, dict) else hb)[:600])
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    json.dump(r, open(os.path.join(HERE, "out", "v2_parallel.json"), "w"), indent=1, default=str)
    open(os.path.join(HERE, "out", "v2_parallel.txt"), "w").write("\n".join(LINES) + "\n")


if __name__ == "__main__":
    main()
