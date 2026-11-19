"""Figures of paper 10 (TN Holdings), drawn from the committed score files only.

  python notes/paper10_ff/figures.py      -> notes/paper10_ff/fig_ceiling.pdf, fig_packing.pdf
  python notes/paper10_ff/figures.py night19 [--loop D] [--interfere D] [--repcode D] [--qpe DA DB]
                                          -> fig_loop19.pdf, fig_night19.pdf (11-19; the folders hold the score files)

The 11-19 folders are not committed yet; NIGHT19 holds the names expected under results/ and can be overridden.
"""
import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

NB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.dirname(os.path.abspath(__file__))
R = lambda p: json.load(open(os.path.join(NB, "results", p)))

INK, MUTED, GRID = "#1f2328", "#59636e", "#d0d7de"
C = ["#2a6fdb", "#d1495b", "#1b998b", "#edae49"]


def series(path, pkey):
    d = R(path)
    rows = d["rows"]
    Ls = sorted(int(k) for k in rows)
    g = [rows[str(L)]["g"] for L in Ls]
    se = [rows[str(L)]["se"] for L in Ls]
    over = [bool(rows[str(L)].get("overshoot")) or rows[str(L)].get("verdict") == "OVERSHOOT" for L in Ls]
    return Ls, g, se, over


def fig_ceiling():
    runs = [("third design, fez, 11-17 (T2)", "ff-night-2026-11-17/compound/compound_scores.json", "p_ff"),
            ("early chain, marrakesh, 11-17 (N2)", "ff-night2-2026-11-17/early2/early2_scores.json", "p_ff"),
            ("balanced pair, marrakesh, 11-17", "balanced-night-2026-11-17/balanced_scores.json", "p_pooled"),
            ("balanced pair, marrakesh, 11-18 (recalibrated)", "balanced-repeat-2026-11-18/balanced_scores.json",
             "p_pooled")]
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.axhline(0, color=MUTED, lw=1)
    for k, (lab, p, key) in enumerate(runs):
        Ls, g, se, over = series(p, key)
        off = (k - 1.5) * 0.07
        x = [L + off for L in Ls]
        ax.plot(x, g, color=C[k], lw=2, label=lab, zorder=2)
        for xi, gi, si, oi in zip(x, g, se, over):
            ax.errorbar(xi, gi, yerr=2 * si, color=C[k], lw=1.2, capsize=0, zorder=3)
            ax.plot(xi, gi, "o", ms=8, mfc="white" if oi else C[k], mec=C[k], mew=2, zorder=4)
    ax.set_xlabel("chain length L (neurons)", color=INK)
    ax.set_ylabel("g = c(L) - |P - exact|", color=INK)
    ax.grid(axis="y", color=GRID, lw=0.8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.set_title("Margin over the correction ceiling (2 SE bars; open: overshoot, not credited)", fontsize=9,
                 color=INK)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_ceiling.pdf"))


def fig_packing():
    a = R("packing-night-2026-11-17/packing_scores.json")
    b = R("parallel-night-2026-11-18/parallel_scores.json")
    tags = list(a["rows"])
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.2), gridspec_kw=dict(width_ratios=[2.2, 1]))
    ax = axs[0]
    d = [a["rows"][t]["d"] for t in tags]
    e = [a["rows"][t].get("two_se", 2 * a["rows"][t].get("se", 0)) for t in tags]
    ax.bar(range(len(tags)), d, yerr=e, color=C[1], width=0.6, error_kw=dict(lw=1, ecolor=INK))
    da = [b["pa"]["rows"][t]["d"] for t in tags]
    ax.plot(range(len(tags)), da, "o", ms=7, color=C[2], label="11-18: off arms packed (P-A)")
    ax.axhline(0, color=MUTED, lw=1)
    ax.set_xticks(range(len(tags)))
    ax.set_xticklabels(tags, fontsize=7)
    ax.set_ylabel("d = |s - v| - |p - v|", color=INK)
    ax.set_title("11-17: ten control arms packed (bars); 11-18: off arms (dots)", fontsize=8, color=INK)
    ax.legend(frameon=False, fontsize=7, loc="lower right")
    ax = axs[1]
    names = ["b1a", "b2a", "b2b", "b3a", "b3b"]
    vals = [b["pb"]["sub"][n]["d"] for n in names]
    errs = [2 * b["pb"]["sub"][n]["se"] for n in names]
    ax.bar(range(5), vals, yerr=errs, color=[C[0], C[1], C[3], C[1], C[3]], width=0.6,
           error_kw=dict(lw=1, ecolor=INK))
    ax.axhline(0, color=MUTED, lw=1)
    ax.set_xticks(range(5))
    ax.set_xticklabels(["B1 A", "B2 A", "B2 B", "B3 A", "B3 B"], fontsize=7)
    ax.set_title("11-18: rd2 with one neighbour (P-B)", fontsize=8, color=INK)
    for x in axs:
        x.grid(axis="y", color=GRID, lw=0.8)
        for s in ("top", "right"):
            x.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_packing.pdf"))


# --- 11-19 (the score files written by the declared tools; nothing is re-scored here) ---

NIGHT19 = dict(loop="os-loop-night-2026-11-19", interfere="interfere-night-2026-11-19",
               repcode="repcode-night-2026-11-19", qpe=("qpe-repro-night-2026-11-19/A", "qpe-repro-night-2026-11-19/B"))


def _res(d):
    return d if os.path.isabs(d) else os.path.join(NB, "results", d)


def _style(ax):
    ax.grid(axis="y", color=GRID, lw=0.8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def fig_loop19(folder):
    """g per round and L from rK/round_scores.json (2 SE = 2 g_se; open: overshoot, not credited)."""
    folder = _res(folder)
    ks = sorted(int(d[1:]) for d in os.listdir(folder)
                if d[:1] == "r" and d[1:].isdigit() and os.path.exists(os.path.join(folder, d, "round_scores.json")))
    rounds = [json.load(open(os.path.join(folder, f"r{k}", "round_scores.json"))) for k in ks]
    Ls = sorted({L for r in rounds for L in r["rows"]}, key=int)
    fig, ax = plt.subplots(figsize=(6.0, 3.4))
    ax.axhline(0, color=MUTED, lw=1)
    for i, L in enumerate(Ls):
        off = (i - (len(Ls) - 1) / 2) * 0.08
        pts = [(k, r["rows"][L]) for k, r in zip(ks, rounds) if L in r["rows"]]
        x = [k + off for k, _ in pts]
        g = [row["g"] for _, row in pts]
        ax.plot(x, g, color=C[i % 4], lw=2, label=f"L = {L}", zorder=2)
        for xi, (k, row) in zip(x, pts):
            over = bool(row.get("overshoot")) or row.get("verdict") == "OVERSHOOT"
            ax.errorbar(xi, row["g"], yerr=2 * row["g_se"], color=C[i % 4], lw=1.2, capsize=0, zorder=3)
            ax.plot(xi, row["g"], "o", ms=8, mfc="white" if over else C[i % 4], mec=C[i % 4], mew=2, zorder=4)
            ax.annotate("+".join(row["stack"]), (xi, row["g"]), textcoords="offset points", xytext=(0, -16),
                        ha="center", fontsize=6, color=MUTED)
    ax.set_xticks(ks)
    ax.set_xlabel("round", color=INK)
    ax.set_ylabel("g = |P0 - exact| - |P - exact|", color=INK)
    _style(ax)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.set_title("The loop on 11-19 (2 SE bars; open: overshoot, not credited)", fontsize=9, color=INK)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_loop19.pdf"))


def fig_night19(interfere, repcode, qpe):
    """(a) E1-E3 d per conditional sub-item; (b) repetition code; (c) IPE against C(n), the textbook q beside."""
    fi = json.load(open(os.path.join(_res(interfere), "interfere_scores.json")))["rows"]
    fr = json.load(open(os.path.join(_res(repcode), "repcode_scores.json")))
    fq = {}
    for d in qpe:
        fq.update(json.load(open(os.path.join(_res(d), "qpe_scores.json")))["results"])
    fig, axs = plt.subplots(1, 3, figsize=(9.6, 3.2), gridspec_kw=dict(width_ratios=[1.4, 1, 1.1]))

    ax = axs[0]
    subs = [("e1b", "E1 B"), ("e2a", "E2 A"), ("e2b", "E2 B"), ("e3a", "E3 A"), ("e3b", "E3 B")]
    subs = [(k, lab) for k, lab in subs if k in fi]
    ax.bar(range(len(subs)), [fi[k]["d"] for k, _ in subs], yerr=[fi[k]["two_se"] for k, _ in subs],
           color=[C[0] if k.endswith("a") else C[3] for k, _ in subs], width=0.6, error_kw=dict(lw=1, ecolor=INK))
    ax.axhline(0, color=MUTED, lw=1)
    ax.set_xticks(range(len(subs)))
    ax.set_xticklabels([lab for _, lab in subs], fontsize=7)
    ax.set_ylabel("d = |s - v| - |p - v|", color=INK)
    ax.set_title("(a) what the packing loss follows", fontsize=8, color=INK)

    ax = axs[1]
    c, g = fr["ceiling"], fr["padded"]["groups"]
    ax.bar([0], [c["margin"]], yerr=[c["two_se"]], color=C[2], width=0.6, error_kw=dict(lw=1, ecolor=INK))
    ax.bar([1, 2], [g["added_tests_never_fire"]["d"], g["added_tests_fire"]["d"]],
           yerr=[g["added_tests_never_fire"]["two_se"], g["added_tests_fire"]["two_se"]],
           color=[C[0], C[1]], width=0.6, error_kw=dict(lw=1, ecolor=INK))
    ax.axhline(0, color=MUTED, lw=1)
    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels([f"lut3 - C\n(C {c['C']:.3f})", "(b0)\nnever fire", "(b1)\nfire"], fontsize=7)
    ax.set_title("(b) repetition code: margin; lut5 - lut3", fontsize=8, color=INK)

    ax = axs[2]
    ns = sorted(fq, key=int)
    x = range(len(ns))
    ax.plot(x, [fq[n]["ipe"]["ceiling"] for n in ns], "_", ms=22, mew=2, color=INK, label="ceiling C(n)")
    ax.errorbar([i - 0.12 for i in x], [fq[n]["ipe"]["ff"] for n in ns], yerr=[fq[n]["ipe"]["two_se"] for n in ns],
                fmt="o", ms=7, color=C[0], label="IPE p", lw=1.2)
    ax.errorbar([i + 0.12 for i in x], [fq[n]["textbook"]["ff"] for n in ns],
                yerr=[fq[n]["textbook"]["two_se"] for n in ns], fmt="s", ms=6, mfc="white", mec=C[1], color=C[1],
                label="textbook q (no ceiling)", lw=1.2)
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"n = {n}" for n in ns], fontsize=7)
    ax.set_ylabel("share of shots right", color=INK)
    ax.set_ylim(0, 1)
    ax.legend(frameon=False, fontsize=6, loc="lower right", markerscale=0.7)
    ax.set_title("(c) phase estimation: two yardsticks", fontsize=8, color=INK)
    for a_ in axs:
        _style(a_)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_night19.pdf"))


def night19(argv=None):
    ap = argparse.ArgumentParser(prog="figures.py night19")
    ap.add_argument("--loop", default=NIGHT19["loop"])
    ap.add_argument("--interfere", default=NIGHT19["interfere"])
    ap.add_argument("--repcode", default=NIGHT19["repcode"])
    ap.add_argument("--qpe", nargs="+", default=list(NIGHT19["qpe"]))
    a = ap.parse_args(argv)
    fig_loop19(a.loop)
    fig_night19(a.interfere, a.repcode, a.qpe)


if __name__ == "__main__":
    import sys
    if sys.argv[1:2] == ["night19"]:
        night19(sys.argv[2:])
    else:
        fig_ceiling()
        fig_packing()
