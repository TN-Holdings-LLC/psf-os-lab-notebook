"""Figures for paper 9 (desk, 2026-11-14). Every value is read from committed records; nothing is fitted.

fig_yardstick.pdf  MSE / mean square against r for the 179 results of notes/paper9_yardstick/line_all.json,
                   with the floor (1 - r)^2 (rest = 0) and the line MSE / mean square = 1/2.
fig_size.pdf       r against CZ layers, N = 33 and N = 81, theta = pi/4 and pi/2, both devices (XX size test).
fig_gap.pdf        gap r(N = 33) - r(N = 81) on the same 33 qubits of ibm_marrakesh, by block, both runs of 11-14
                   (block definition of notes/xxcone_2026-11-14/cone.py).
usage: python notes/paper9/figures.py   (from the repository root)"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = "notes/paper9"
BLUE, ORANGE, AQUA, GRAY = "#2a78d6", "#eb6834", "#1baf7a", "#8a8a85"
plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#555", "axes.linewidth": 0.6, "lines.linewidth": 1.4,
                     "legend.frameon": False, "pdf.fonttype": 42})
STEPS, LAYERS = (2, 4, 8, 12, 16), (8, 16, 32, 48, 64)
BLOCKS = {"far": range(0, 11), "mid": range(11, 22), "near": range(22, 33)}


def yardstick():
    rows = json.load(open("notes/paper9_yardstick/line_all.json"))
    fig, ax = plt.subplots(figsize=(3.4, 2.7))
    rr = np.linspace(0, 1.05, 200)
    ax.plot(rr, (1 - rr) ** 2, color=GRAY, lw=1, label="floor $(1-r)^2$ (rest = 0)")
    ax.axhline(0.5, color="#333", lw=0.8, ls="--")
    ax.axvline(1 - 2 ** -0.5, color="#333", lw=0.8, ls=":")
    ax.text(1.04, 0.52, "reads below", ha="right", va="bottom", fontsize=7)
    ax.text(0.30, 1.05, "$r = 0.293$", ha="left", fontsize=7)
    for ok, col, mk, lab in ((True, BLUE, "o", "reads"), (False, ORANGE, "s", "does not read")):
        s = [x for x in rows if bool(x["reads"]) == ok]
        ax.scatter([x["r"] for x in s], [x["ratio"] for x in s], s=12, c=col, marker=mk, lw=0.4,
                   edgecolors="white", label=f"{lab} ({len(s)})", zorder=3)
    ax.set_xlim(0, 1.05); ax.set_ylim(0, 1.15)
    ax.set_xlabel("kept share $r = \\sum ze / \\sum e^2$"); ax.set_ylabel("MSE / mean square")
    ax.legend(loc="upper right", fontsize=7)
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_yardstick.pdf"); plt.close(fig)


def size():
    fig, axs = plt.subplots(1, 2, figsize=(6.6, 2.5), sharey=True)
    for ax, dev in zip(axs, ("marrakesh", "fez")):
        base = f"results/xxsize-2026-11-14-{dev}/ibm_{dev}"
        for n, col, mk in ((33, BLUE, "o"), (81, ORANGE, "s")):
            c = json.load(open(f"{base}_n{n}/scores.json"))["circuits"]
            for th, ls, fill in (("0785", "-", True), ("1571", "--", False)):
                r = [c[f"N{n}_th{th}_s{s:02d}"]["amplitude_ratio"] for s in STEPS]
                ax.plot(LAYERS, r, ls=ls, color=col, marker=mk, ms=4,
                        mfc=col if fill else "white", label=f"N = {n}, $\\theta = \\pi/{4 if th == '0785' else 2}$")
        ax.axhline(1 - 2 ** -0.5, color="#333", lw=0.8, ls=":")
        ax.set_title(f"ibm_{dev}", fontsize=8); ax.set_xlabel("CZ layers"); ax.set_xticks(LAYERS)
    axs[0].set_ylabel("kept share $r$"); axs[0].set_ylim(0, 0.9)
    axs[0].text(9, 0.30, "0.293", fontsize=7, va="bottom")
    axs[1].legend(loc="upper right", fontsize=7)
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_size.pdf"); plt.close(fig)


def gaps(d33, d81):
    sc = {n: json.load(open(os.path.join(d, "scores.json")))["circuits"] for n, d in ((33, d33), (81, d81))}
    lab = {33: json.load(open(os.path.join(d33, "build.json")))["chains"]["33"]["labels"],
           81: json.load(open(os.path.join(d81, "build.json")))["chains"]["81"]["labels"]}
    assert lab[81][:33] == lab[33]
    out = {}
    for th in ("0785", "1571"):
        for b, idx in BLOCKS.items():
            g = []
            for s in STEPS:
                rr = []
                for n in (33, 81):
                    c = sc[n][f"N{n}_th{th}_s{s:02d}"]
                    z, e = np.array(c["z"])[list(idx)], np.array(c["exact"])[list(idx)]
                    rr.append(float(np.dot(z, e) / np.dot(e, e)))
                g.append(rr[0] - rr[1])
            out[(th, b)] = g
    return out


def gap():
    runs = {"first run (12:30 CET)": gaps("results/xxsize-2026-11-14-marrakesh/ibm_marrakesh_n33",
                                           "results/xxsize-2026-11-14-marrakesh/ibm_marrakesh_n81"),
            "repeat (13:04 CET)": gaps("results/xxcone-2026-11-14/ibm_marrakesh_n33",
                                       "results/xxcone-2026-11-14/ibm_marrakesh_n81")}
    fig, axs = plt.subplots(1, 2, figsize=(6.6, 3.0), sharey=True)
    for ax, th in zip(axs, ("0785", "1571")):
        for b, col, mk in (("near", ORANGE, "s"), ("mid", AQUA, "^"), ("far", BLUE, "o")):
            for (name, g), ls, fill in zip(runs.items(), ("-", "--"), (True, False)):
                ax.plot(LAYERS, g[(th, b)], ls=ls, color=col, marker=mk, ms=4, mfc=col if fill else "white",
                        label=f"{b}, {name.split(' (')[0]}")
        ax.axhline(0, color=GRAY, lw=0.6)
        ax.set_title(f"$\\theta = \\pi/{4 if th == '0785' else 2}$", fontsize=8)
        ax.set_xlabel("CZ layers"); ax.set_xticks(LAYERS)
    axs[0].set_ylabel("$r_{33} - r_{81}$ on the same qubits")
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, fontsize=7)
    fig.tight_layout(rect=(0, 0.17, 1, 1)); fig.savefig(f"{OUT}/fig_gap.pdf"); plt.close(fig)
    with open(f"{OUT}/fig_gap.txt", "w") as f:
        for name, g in runs.items():
            for th in ("0785", "1571"):
                f.write(f"{name} theta {th}: " + " | ".join(
                    f"{L}: far {g[(th, 'far')][i]:+.3f} mid {g[(th, 'mid')][i]:+.3f} near {g[(th, 'near')][i]:+.3f}"
                    for i, L in enumerate(LAYERS)) + "\n")


if __name__ == "__main__":
    yardstick(); size(); gap()
