"""
make_figures.py

Draws the report figures that can be rebuilt from the shipped result files
alone. It reads only results/verified/ and writes PNGs (200 dpi) to figures/,
so it runs without any licensed data.

Run: python make_figures.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results" / "verified"
FIGURES = ROOT / "figures"

BLUE = "#2166ac"
GREY = "#8c8c8c"
INK = "#333333"

plt.rcParams.update({
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": "#e6e6e6",
    "grid.linewidth": 0.8,
    "axes.axisbelow": True,
})


def save(fig, name):
    path = FIGURES / name
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  wrote figures/{name}")


def cost_waterfall():
    """Ledger D1: gross alpha to fully costed alpha on the broad composite."""
    w = pd.read_csv(RESULTS / "waterfall_definitive.csv")
    labels = ["Gross signal", "+ bid-ask\nspreads", "+ borrow\navailability", "+ borrow\nfees"]
    alpha = w["Alpha%mo"].to_numpy()
    tstat = w["t"].to_numpy()

    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    x = range(len(alpha))
    ax.bar(x, alpha, width=0.6, color=BLUE)
    ax.grid(axis="x", visible=False)
    for i, (a, t) in enumerate(zip(alpha, tstat)):
        ax.text(i, a + 0.04, f"{a:.3f}%\n(t = {t:.2f})", ha="center", va="bottom",
                fontsize=9, color=INK)
    for i in range(1, len(alpha)):
        drop = alpha[i - 1] - alpha[i]
        ax.text(i - 0.5, alpha[i - 1] * 0.55, f"-{drop:.3f}", ha="center",
                fontsize=8.5, color=GREY)
    ax.set_xticks(list(x), labels)
    ax.set_ylabel("Alpha (%/month)")
    ax.set_ylim(0, alpha.max() * 1.3)
    ax.set_title("Cost waterfall on the broad composite, 2003 to 2026")
    save(fig, "cost_waterfall_definitive.png")


def specification_grid():
    """Ledger G1: the 65-test grid on the 1995-2019 development window."""
    g = pd.read_csv(RESULTS / "spec_results_N65.csv")
    t = g["nw_t"].sort_values(ascending=False).reset_index(drop=True)
    n_196 = int((g["nw_t"].abs() > 1.96).sum())
    n_300 = int((g["nw_t"].abs() > 3.0).sum())
    min_bhy = g["p_BHY"].min()

    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.scatter(range(1, len(t) + 1), t, s=22, color=BLUE, zorder=3)
    ax.grid(axis="x", visible=False)
    for level, style in [(3.0, "-"), (1.96, "--"), (-1.96, "--")]:
        ax.axhline(level, color=GREY, linestyle=style, linewidth=1)
    ax.text(len(t) + 0.5, 3.0, "|t| = 3.0", va="bottom", ha="right", fontsize=8.5, color=GREY)
    ax.text(len(t) + 0.5, 1.96, "|t| = 1.96", va="bottom", ha="right", fontsize=8.5, color=GREY)
    ax.text(0.03, 0.36,
            f"{len(g)} tests: {n_196} clear |t| = 1.96, {n_300} clears 3.0\n"
            f"none survive BHY (lowest adjusted p = {min_bhy:.3f})",
            transform=ax.transAxes, ha="left", va="top", fontsize=9, color=INK)
    ax.set_xlabel("Test, ranked by t-statistic")
    ax.set_ylabel("Newey-West t-statistic")
    ax.set_xlim(0, len(t) + 1)
    ax.set_title("65-test specification grid, 1995 to 2019")
    save(fig, "spec_grid_65_tests.png")


def table1_fama_macbeth():
    """Ledger E2: the reference Table I re-derived; nothing clears Bonferroni."""
    fm = pd.read_csv(RESULTS / "rederived_table1_fm.csv").sort_values("NW_t")
    bonferroni = 2.77

    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.barh(fm["Factor"], fm["NW_t"], height=0.6, color=BLUE)
    ax.grid(axis="y", visible=False)
    ax.axvline(1.96, color=GREY, linestyle="--", linewidth=1)
    ax.axvline(bonferroni, color=INK, linestyle="-", linewidth=1)
    ax.axvline(0, color=INK, linewidth=0.8)
    ax.text(1.96, -0.85, "t = 1.96 ", ha="right", fontsize=8.5, color=GREY)
    ax.text(bonferroni, -0.85, " Bonferroni t = 2.77", ha="left", fontsize=8.5, color=INK)
    for y, t in enumerate(fm["NW_t"]):
        label = f"{t:.3f}" if abs(t - bonferroni) < 0.05 else f"{t:.2f}"
        ax.text(t + (0.05 if t >= 0 else -0.05), y, label, va="center",
                ha="left" if t >= 0 else "right", fontsize=8.5, color=INK)
    ax.set_xlabel("Fama-MacBeth premium, Newey-West t-statistic")
    ax.set_xlim(-1.5, 3.8)
    ax.set_ylim(-1.1, len(fm) - 0.4)
    ax.set_title("Reference Table I re-derived: no factor clears Bonferroni")
    save(fig, "table1_fama_macbeth.png")


if __name__ == "__main__":
    print("Drawing figures from results/verified/")
    cost_waterfall()
    specification_grid()
    table1_fama_macbeth()
