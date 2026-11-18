"""Figures of paper 10 (TN Holdings), drawn from the committed score files only.

  python notes/paper10_ff/figures.py      -> notes/paper10_ff/fig_ceiling.pdf, fig_packing.pdf
"""
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


if __name__ == "__main__":
    fig_ceiling()
    fig_packing()
