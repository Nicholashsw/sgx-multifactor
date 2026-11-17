"""Hero chart: decile returns (gross) and the long-short book before and after costs."""
from pathlib import Path
import pandas as pd
# --- shared chart style (identical in every repo's figures.py) ---------------------------
# Palette: first three categorical slots of the validated reference palette (pass all-pairs
# CVD checks in light mode). Ink and grid are text tokens, never series colours.
import matplotlib as mpl
import matplotlib.pyplot as plt

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"

mpl.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10,
    "axes.titlesize": 11, "axes.titleweight": "regular", "axes.titlelocation": "left",
    "axes.labelsize": 9.5, "axes.labelcolor": INK2, "axes.edgecolor": INK2, "axes.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.facecolor": SURFACE, "figure.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "xtick.color": INK2, "ytick.color": INK2, "xtick.labelsize": 9, "ytick.labelsize": 9,
    "xtick.major.size": 0, "ytick.major.size": 0, "lines.linewidth": 2,
    "legend.frameon": False, "figure.dpi": 100, "savefig.dpi": 200,
})
FIGSIZE = (7.2, 4.0)   # one hero size for all six projects


def finish(fig, ax, title, subtitle, path):
    """Title (what the chart says) and subtitle (what is plotted, from which file), then save."""
    ax.set_title(title, color=INK, pad=22)
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, color=INK2, fontsize=8.5, va="bottom")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
# -------------------------------------------------------------------------------------------

ROOT = Path(__file__).parent
V = ROOT / "results" / "verified"
SHORT = ["Gross", "+\nspreads", "+\nscreen", "+\nfee"]


def hero():
    dec = pd.read_csv(V / "sgx3_deciles_corrected.csv").groupby("dec").act.mean() * 100
    wf = pd.read_csv(V / "waterfall_schemes_traded_days.csv").query("Score == 'Composite' and Book == 'Long-short'")
    # Traded scheme has no stage 1: gross bar is the "Every month" stage 1 (same gross signal)
    wf = pd.concat([wf.query("Costing == 'Every month' and Stage.str.startswith('1.')"),
                    wf.query("Costing == 'Traded'")])
    fig, host = plt.subplots(figsize=FIGSIZE)
    host.set_axis_off()
    a0 = host.inset_axes([0.08, 0.0, 0.40, 0.78])
    a1 = host.inset_axes([0.58, 0.0, 0.40, 0.78], sharey=a0)
    a1.tick_params(labelleft=False)
    a0.set_ylim(-0.8, 1.9)
    for a in (a0, a1):
        a.set_axisbelow(True)

    a0.bar(dec.index, dec.values, width=0.8, color=BLUE, edgecolor=SURFACE, linewidth=1)
    for k in (0, 9):
        a0.text(k, dec[k] + (0.04 if dec[k] > 0 else -0.12), f"{dec[k]:+.2f}", ha="center",
                va="bottom" if dec[k] > 0 else "top", color=INK, fontsize=8.5)
    a0.set_xticks(range(10), [str(k + 1) for k in range(10)])
    a0.set_xlabel("Decile (1 = lowest score), gross")
    a0.set_title("Deciles, 2008 to 2026", color=INK, fontsize=9, loc="left", pad=6)
    a0.set_ylabel("Mean monthly return (%)")

    x = range(len(wf))
    a1.bar(x, wf["Alpha%mo"], width=0.8, color=[BLUE] + [ORANGE] * (len(wf) - 1),
           edgecolor=SURFACE, linewidth=1)
    for i, v in zip(x, wf["Alpha%mo"]):
        a1.text(i, v + 0.04, f"{v:.2f}", ha="center", va="bottom", color=INK, fontsize=8.5)
    a1.set_xticks(list(x), SHORT, fontsize=7.5)
    a1.set_xlabel("Alpha %/mo, costs added left to right")
    a1.set_title("Composite long-short, 2003 to 2026,\ncosts on traded names", color=INK, fontsize=9, loc="left", pad=6)
    for a in (a0, a1):
        a.axhline(0, color=INK2, lw=0.6)
    finish(fig, host, "Returns rise with the score, but costs take most of the long-short alpha",
           "Files: sgx3_deciles_corrected.csv; waterfall_schemes_traded_days.csv (gross bar: Every month stage 1)",
           ROOT / "figures" / "hero.png")


if __name__ == "__main__":
    hero()
