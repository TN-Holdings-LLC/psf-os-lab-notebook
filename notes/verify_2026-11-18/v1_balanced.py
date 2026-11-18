"""1. The balanced repeat (results/balanced-repeat-2026-11-18), re-scored from raw_counts.json alone, with the noiseless
values computed here from the recorded circuits (home VS Claude, 2026-11-18; qiskit and numpy only).

Per L: rd{L} (read 1 - bit) and nf{L} (read the bit); the output bit is read from the circuit (vlib.out_bit) and
compared with the record. Noiseless values: the exact branching distribution of the recorded compiled ff and off
circuits (compacted). exact = the ideal chain (statevector and closed form). c(L) = |off noiseless - exact| (the
declared ceiling: the circuit without control), for rd and for nf. P = (P_rd + P_nf) / 2, SE = sqrt(var_rd / n_rd +
var_nf / n_nf) / 2, g = c(L) - |P - exact|, slope of g over L by weighted least squares (weights 1 / SE^2).
Also the difference to 2026-11-17's same test (results/balanced-night-2026-11-17), pooled, rd and nf.
usage: python notes/verify_2026-11-18/v1_balanced.py   (from the notebook root)"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402

THETA, LS = 1.1, (1, 2, 3, 4, 5)
HERE = os.path.dirname(os.path.abspath(__file__))


def score(folder, noiseless=None):
    job, _ = V.load_job(folder)
    rows, nl = {}, noiseless or {}
    for L in LS:
        r = {}
        for fr in ("rd", "nf"):
            ff, off = job[f"ff_{fr}{L}"], job[f"ff_{fr}{L}_off"]
            cff, phys = V.compact(ff["circuit"])
            ob, oq = V.out_bit(cff)
            rec_ob = ff["record"]["rus"]["out_bit"] if ff["record"] else None
            p, n = V.p_bit(ff["counts"], ob)
            flip = fr == "rd"
            P = 1 - p if flip else p
            if (fr, L) not in nl:
                coff, _ = V.compact(off["circuit"])
                ob_off, _ = V.out_bit(coff)
                d_ff = V.branch_dist(cff)
                d_off = V.branch_dist(coff)
                pf, po = V.p_bit_dist(d_ff, ob), V.p_bit_dist(d_off, ob_off)
                nl[(fr, L)] = dict(ff=1 - pf if flip else pf, off=1 - po if flip else po)
            r[fr] = dict(P=P, n=n, out_bit=ob, out_bit_record=rec_ob, out_qubit_physical=phys[oq],
                         chain=phys, chain_record=ff["record"]["chain"] if ff["record"] else None,
                         noiseless_ff=nl[(fr, L)]["ff"], noiseless_off=nl[(fr, L)]["off"])
        ex_sv, ex_cf = V.ideal_chain(L, THETA)
        c_rd = abs(r["rd"]["noiseless_off"] - ex_sv)
        c_nf = abs(r["nf"]["noiseless_off"] - ex_sv)
        P = (r["rd"]["P"] + r["nf"]["P"]) / 2
        se = math.sqrt(r["rd"]["P"] * (1 - r["rd"]["P"]) / r["rd"]["n"] + r["nf"]["P"] * (1 - r["nf"]["P"]) / r["nf"]["n"]) / 2
        g = c_rd - abs(P - ex_sv)
        noiseless_pool = (r["rd"]["noiseless_ff"] + r["nf"]["noiseless_ff"]) / 2
        rows[L] = dict(rd=r["rd"], nf=r["nf"], exact=ex_sv, exact_closed=ex_cf, c_rd=c_rd, c_nf=c_nf, P=P, se=se,
                       g=g, noiseless_pool=noiseless_pool, overshoot=P > noiseless_pool + 2 * se)
    b, sb = V.wls_slope(list(LS), [rows[L]["g"] for L in LS], [rows[L]["se"] for L in LS])
    return rows, (b, sb), nl


def main():
    lines = []
    say = lambda s: (print(s, flush=True), lines.append(s))
    rows, (b, sb), nl = score("results/balanced-repeat-2026-11-18")
    home = json.load(open("results/balanced-repeat-2026-11-18/balanced_scores.json"))
    say("== 2026-11-18 balanced repeat, re-scored (own reading); home's numbers in brackets")
    for L in LS:
        r, h = rows[L], home["rows"][str(L)]
        say(f"L {L}: out bit rd {r['rd']['out_bit']} (record {r['rd']['out_bit_record']}), nf {r['nf']['out_bit']} "
            f"(record {r['nf']['out_bit_record']}); output qubit {r['rd']['out_qubit_physical']}; chain {r['rd']['chain']} "
            f"(record {r['rd']['chain_record']})")
        say(f"     rd {r['rd']['P']:.4f} [{h['rd']:.4f}]  nf {r['nf']['P']:.4f} [{h['nf']:.4f}]  pooled {r['P']:.4f} "
            f"[{h['p_pooled']:.4f}]  exact {r['exact']:.6f} (closed form {r['exact_closed']:.6f})  noiseless pool "
            f"{r['noiseless_pool']:.4f} [{h['noiseless']:.4f}] (rd {r['rd']['noiseless_ff']:.4f}, nf "
            f"{r['nf']['noiseless_ff']:.4f})")
        say(f"     off noiseless rd {r['rd']['noiseless_off']:.4f}, nf {r['nf']['noiseless_off']:.4f}; c(L) rd "
            f"{r['c_rd']:.4f} [{h['c']:.4f}] (nf {r['c_nf']:.4f})  g {r['g']:+.4f} [{h['g']:+.4f}]  2 SE "
            f"{2 * r['se']:.4f} [{2 * h['se']:.4f}]  overshoot {r['overshoot']}  -> "
            f"{'OVERSHOOT' if r['overshoot'] else ('BEYOND' if r['g'] >= 2 * r['se'] else 'NOT BEYOND')} [{h['verdict']}]")
    hs = home["slope"]
    say(f"slope {b:+.4f} (2 SE {2 * sb:.4f}) [{hs['slope']:+.4f} (2 SE {2 * hs['se']:.4f})] -> "
        f"{'COMPOUNDS' if b >= 2 * sb and not any(rows[L]['overshoot'] for L in LS) else 'NOT SHOWN'} [{hs['verdict']}]")
    worst = max(max(abs(rows[L]["P"] - home["rows"][str(L)]["p_pooled"]), abs(rows[L]["g"] - home["rows"][str(L)]["g"]),
                    abs(rows[L]["c_rd"] - home["rows"][str(L)]["c"]),
                    abs(rows[L]["noiseless_pool"] - home["rows"][str(L)]["noiseless"])) for L in LS)
    say(f"largest difference to home (P, g, c, noiseless): {worst:.1e}")
    # 2026-11-17
    rows17, (b17, sb17), _ = score("results/balanced-night-2026-11-17", noiseless=None)
    say("== against 2026-11-17 (same test), differences 11-18 minus 11-17 (2 SE)")
    diffs = {}
    for L in LS:
        a, z = rows[L], rows17[L]
        d = {}
        for k in ("rd", "nf"):
            pa, pz = a[k]["P"], z[k]["P"]
            d[k] = (pa - pz, 2 * math.sqrt(pa * (1 - pa) / a[k]["n"] + pz * (1 - pz) / z[k]["n"]))
        d["pooled"] = (a["P"] - z["P"], 2 * math.sqrt(a["se"] ** 2 + z["se"] ** 2))
        diffs[L] = d
        say(f"L {L}: pooled {d['pooled'][0]:+.4f} ({d['pooled'][1]:.4f})  rd {d['rd'][0]:+.4f} ({d['rd'][1]:.4f})  nf "
            f"{d['nf'][0]:+.4f} ({d['nf'][1]:.4f});  same chain {rows[L]['rd']['chain'] == rows17[L]['rd']['chain']}")
    say(f"2026-11-17 slope (own reading) {b17:+.4f} (2 SE {2 * sb17:.4f})")
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    json.dump(dict(rows={L: rows[L] for L in LS}, slope=[b, sb], rows_1117={L: rows17[L] for L in LS},
                   slope_1117=[b17, sb17], diffs=diffs), open(os.path.join(HERE, "out", "v1_balanced.json"), "w"),
              indent=1, default=str)
    open(os.path.join(HERE, "out", "v1_balanced.txt"), "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
