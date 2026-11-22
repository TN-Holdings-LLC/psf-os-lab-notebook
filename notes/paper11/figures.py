"""Figures of paper 11 (TN Holdings), drawn from the committed score files only.

  python notes/paper11/figures.py   -> notes/paper11/fig_park.pdf, fig_rus.pdf, fig_wait.pdf, fig_ipe.pdf,
                                       fig_loopvar.pdf

Every value is read from a results/ folder named beside it; 2 SE of a share without a stored SE is the binomial
2 * sqrt(p (1 - p) / N) with N the shots pooled for that share, as the scorers compute it. Times are the
night's first fetch (CET), as in the paper's table.
"""
import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker

NB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.dirname(os.path.abspath(__file__))
INK, MUTED, GRID = "#1f2328", "#59636e", "#d0d7de"
C = ["#2a6fdb", "#d1495b", "#1b998b", "#edae49", "#7a5195"]


def R(p):
    return json.load(open(os.path.join(NB, "results", p)))


def two_se(p, n):
    return 2.0 * math.sqrt(p * (1.0 - p) / n)


def style(ax):
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(colors=INK, labelsize=8)


def fig_park():
    c = R("weekend-shared-night-2026-11-21/BC/scores/C/park_scores.json")["4"]["shares"]
    n_c = 31200
    q = R("qpe-parked-night-2026-11-21/qp/parked_scores.json")["per_n"]
    rf = R("rus-fence-night-2026-11-21/rf/rusfence_scores.json")["control_ipe"]
    lp = R("likely-park-night-2026-11-22/lp/likely_scores.json")["control"]
    q78 = R("qpe-n78-night-2026-11-22/qn/qpe78_scores.json")["per_n"]
    fig, (a, b) = plt.subplots(1, 2, figsize=(9.6, 3.4), gridspec_kw=dict(width_ratios=[1, 2.2]))
    forms = [("pl", "superposition\n(as sent)"), ("fe", "|1>\n(fenced)"), ("pk", "|0>\n(parked)")]
    for i, (k, lab) in enumerate(forms):
        a.bar(i, c[k], color=C[i], width=0.6)
        a.errorbar(i, c[k], yerr=two_se(c[k], n_c), color=INK, capsize=3, linewidth=1)
    a.set_xticks(range(3), [f[1] for f in forms])
    a.set_ylim(0.85, 0.95)
    a.set_ylabel("share of shots right (IPE n = 4)", fontsize=8)
    a.set_title("(a) where the target waits\nmarrakesh, 2026-11-21 01:52", fontsize=8, color=INK)
    style(a)
    pts = [("marrakesh\n11-21 10:59", n, q[str(n)]["d"], q[str(n)]["d_2se"]) for n in (4, 5, 6)]
    pts += [("fez\n11-21 14:29", 4, rf["d"], rf["two_se"]), ("kingston\n11-22 03:46", 4, lp["d"], lp["two_se"])]
    pts += [("fez\n11-22 11:56", n, q78[str(n)]["d"], q78[str(n)]["d_two_se"]) for n in (6, 7, 8)]
    xs, labels = [], []
    groups = []
    for night, n, d, s in pts:
        if not groups or groups[-1] != night:
            groups.append(night)
        x = len(xs) + 0.6 * (len(groups) - 1)
        xs.append(x)
        labels.append(f"n={n}")
        b.errorbar(x, d, yerr=s, fmt="o", color=C[(len(groups) - 1) % len(C)], capsize=3, markersize=4)
    b.axhline(0, color=MUTED, linewidth=0.8)
    b.set_xticks(xs, labels, fontsize=7)
    gx = {}
    for (night, *_), x in zip(pts, xs):
        gx.setdefault(night, []).append(x)
    for night, xx in gx.items():
        b.text(sum(xx) / len(xx), -0.045, night, ha="center", va="top", fontsize=7, color=MUTED)
    b.set_ylim(-0.06, 0.08)
    b.set_ylabel("parked - unparked, same job (2 SE)", fontsize=8)
    b.set_title("(b) parking the always-|1> target, by night and n (nothing compared across nights)",
                fontsize=8, color=INK)
    style(b)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_park.pdf"))
    plt.close(fig)


def fig_rus():
    rf = R("rus-fence-night-2026-11-21/rf/rusfence_scores.json")
    lp = R("likely-park-night-2026-11-22/lp/likely_scores.json")
    items = [("p0l3", "P0"), ("nfl3m3", "NF"), ("p3l3", "P3"), ("p2l3m3", "P2")]
    fig, ax = plt.subplots(figsize=(8.4, 3.2))
    w = 0.25
    for i, (k, lab) in enumerate(items):
        f = rf[k]["fence F - D"]
        m = rf[k]["park M - F"]
        ax.errorbar(i - w, f["g"], yerr=f["two_se"], fmt="s", color=C[1], capsize=3, markersize=4,
                    label="fez 11-21: full fence F - D" if i == 0 else None)
        ax.errorbar(i, m["g"], yerr=m["two_se"], fmt="o", color=C[0], capsize=3, markersize=4,
                    label="fez 11-21: likely value parked on the fence M - F" if i == 0 else None)
        if k in lp:
            ax.errorbar(i + w, lp[k]["g"], yerr=lp[k]["two_se"], fmt="D", color=C[2], capsize=3, markersize=4,
                        label="kingston 11-22: 0.3.1's MP against 0.3.0, L - D" if i == 0 else None)
    ax.axhline(0, color=MUTED, linewidth=0.8)
    ax.set_xticks(range(len(items)), [i[1] + " L3" for i in items])
    ax.set_ylabel("g of the difference (2 SE)", fontsize=8)
    ax.set_title("RUS chains: the fence and parking the likely value, each difference inside one job",
                 fontsize=8, color=INK)
    ax.legend(fontsize=7, frameon=False, loc="upper right")
    style(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_rus.pdf"))
    plt.close(fig)


def fig_wait():
    a = R("weekend-shared-night-2026-11-21/A/scores/A/repcode4_scores.json")["forms"]
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    order = [("F16", "16 CZ, 3 carriers"), ("F10", "10 CZ, 3 carriers"), ("F6P", "10 CZ, 1 carrier"),
             ("F6", "6 CZ, 1 carrier")]
    for i, (k, lab) in enumerate(order):
        p, se = a[k]["p"], a[k]["se"]
        ax.bar(i, p, color=C[0], width=0.6)
        ax.errorbar(i, p, yerr=2 * se, color=INK, capsize=3, linewidth=1)
    ax.axhline(0.875, color=C[1], linewidth=1, linestyle="--")
    ax.text(3.45, 0.876, "ceiling 0.875", color=C[1], fontsize=7, ha="right", va="bottom")
    ax.set_xticks(range(4), [f"{k}\n{lab}" for k, lab in order], fontsize=7)
    ax.set_ylim(0.70, 0.90)
    ax.set_ylabel("lut3 c[0] right, four errors pooled", fontsize=8)
    ax.set_title("The repetition code's four forms (marrakesh, 2026-11-21 01:52; 4000 shots)", fontsize=8, color=INK)
    style(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_wait.pdf"))
    plt.close(fig)


def fig_ipe():
    wk = R("weekend-shared-night-2026-11-21/BC/scores/B/qpe_long_scores.json")["rows"]
    pk = R("qpe-parked-night-2026-11-21/qp/parked_scores.json")["per_n"]
    q78 = R("qpe-n78-night-2026-11-22/qn/qpe78_scores.json")["per_n"]
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    s1 = [(n, wk[str(n)]["ipe"], wk[str(n)]["ipe_2se"], wk[str(n)]["ceiling"]) for n in (4, 5, 6)]
    s2 = [(n, pk[str(n)]["parked"], pk[str(n)]["parked_2se"], None) for n in (4, 5, 6)]
    s3 = [(n, q78[str(n)]["p"], q78[str(n)]["two_se"], q78[str(n)]["ceiling"]) for n in (6, 7, 8)]
    for s, lab, col, mk in [(s1, "unparked, marrakesh 11-21 01:52 (every phase)", C[3], "s"),
                            (s2, "parked, marrakesh 11-21 10:59 (every phase)", C[0], "o"),
                            (s3, "parked by 0.3.1, fez 11-22 11:56 (16 phases)", C[2], "D")]:
        ax.errorbar([x[0] for x in s], [x[1] for x in s], yerr=[x[2] for x in s], fmt=mk + "-", color=col,
                    capsize=3, markersize=4, linewidth=1, label=lab)
    ceil = {x[0]: x[3] for x in s1 + s3 if x[3] is not None}
    ns = sorted(ceil)
    ax.plot(ns, [ceil[n] for n in ns], color=C[1], linestyle="--", linewidth=1, label="ceiling C(n)")
    ax.set_yscale("log")
    ax.set_yticks([0.2, 0.3, 0.5, 0.7, 0.9], ["0.2", "0.3", "0.5", "0.7", "0.9"])
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xticks(range(4, 9))
    ax.set_xlabel("n (bits read)", fontsize=8)
    ax.set_ylabel("share of shots with all n bits right", fontsize=8)
    ax.set_title("Iterative phase estimation against its ceiling (each night its own series)", fontsize=8,
                 color=INK)
    ax.legend(fontsize=7, frameon=False, loc="lower left")
    style(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_ipe.pdf"))
    plt.close(fig)


def fig_loopvar():
    v = R("loopvar-night-2026-11-20/loopvar_scores.json")["rows"]
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    for i, L in enumerate(("1", "2", "3")):
        pj = v[L]["per_job_copy"]
        for j, job in enumerate(("V1", "V2", "V3")):
            for c, cp in enumerate(("a", "b")):
                x = i * 4 + j + (c - 0.5) * 0.25
                ax.errorbar(x, pj[job][cp]["g"], yerr=2 * pj[job][cp]["se"], fmt="o", color=C[j], capsize=2,
                            markersize=3, label=(f"job {job}" if (i == 0 and c == 0) else None))
    ax.axhline(0, color=MUTED, linewidth=0.8)
    ax.set_xticks([1, 5, 9], ["L = 1", "L = 2", "L = 3"])
    ax.set_ylabel("g, two copies per job (2 SE)", fontsize=8)
    ax.set_title("The same circuits in three jobs seconds apart (marrakesh, 2026-11-20)", fontsize=8, color=INK)
    ax.legend(fontsize=7, frameon=False, loc="upper left")
    style(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_loopvar.pdf"))
    plt.close(fig)


if __name__ == "__main__":
    fig_park()
    fig_rus()
    fig_wait()
    fig_ipe()
    fig_loopvar()
    print("figures written to", OUT)
