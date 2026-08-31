"""Figures for the deck, in the deck palette so slides and charts match."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "web" / "data.json").read_text())

INK, INSTRUMENT, BOUND, MOSS, MUTED, GROUND = "#16202B", "#2E7BA6", "#D14A38", "#5A9970", "#8C9AA6", "#FFFFFF"
plt.rcParams.update({
    "font.size": 13, "font.family": "DejaVu Sans",
    "axes.edgecolor": MUTED, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": "#DCE2E8", "grid.linewidth": .8,
    "figure.facecolor": GROUND, "axes.facecolor": GROUND, "savefig.facecolor": GROUND,
})


def dial():
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    xs, ys = [], []
    for c, r in zip(D["base"]["coverage"], D["base"]["risk"], strict=True):
        if r is None or c < 0.3:
            continue
        xs.append(c * 100)
        ys.append((1 - r) * 100)
    ax.plot(xs, ys, lw=3, color=INSTRUMENT, zorder=2)

    cert = D["certified"]["0.05"]
    ax.scatter([cert["coverage"] * 100], [(1 - cert["risk"]) * 100], s=190, color=INSTRUMENT, zorder=5)
    ax.annotate("certified\n87.2% routed", (cert["coverage"] * 100, (1 - cert["risk"]) * 100),
                textcoords="offset points", xytext=(-104, 44), ha="center", color=INSTRUMENT, weight="bold")

    naive = D["naive"]["0.05"]
    ax.scatter([naive["coverage"] * 100], [(1 - naive["risk"]) * 100], s=230, marker="X", color=BOUND, zorder=5)
    ax.annotate("tuned\nlooks fine here", (naive["coverage"] * 100, (1 - naive["risk"]) * 100),
                textcoords="offset points", xytext=(10, -62), ha="center", color=BOUND, weight="bold")

    ax.axhline(95, ls="--", lw=1.6, color=MUTED)
    ax.text(48.5, 95.35, "95% target", color=MUTED, fontsize=11, ha="left")
    ax.set_xlabel("coverage: tickets routed without a human (%)")
    ax.set_ylabel("precision on routed tickets (%)")
    ax.set_ylim(89, 100.5)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.tight_layout()
    fig.savefig(ROOT / "deck" / "fig_dial.png", dpi=200)
    plt.close(fig)


def drift():
    fig, (a, b) = plt.subplots(1, 2, figsize=(11.6, 4.3))
    gi = min(range(len(D["grid"])), key=lambda i: abs(D["grid"][i] - D["certified"]["0.05"]["theta"]))

    tv = [c["tv"] for c in D["mix"]]
    a.plot(tv, [c["coverage"][gi] * 100 for c in D["mix"]], "o-", lw=3, ms=9, color=INSTRUMENT, label="coverage")
    a.plot(tv, [c["risk"][gi] * 100 for c in D["mix"]], "s-", lw=3, ms=9, color=MOSS, label="error")
    a.axhline(5, ls="--", lw=2, color=BOUND)
    a.set_title("The mix moves\ncoverage pays, guarantee holds", color=MOSS, weight="bold", fontsize=14)
    a.set_xlabel("shift in the category mix")

    fr = [c["fraction"] * 100 for c in D["taxonomy"]]
    b.plot(fr, [c["coverage"][gi] * 100 for c in D["taxonomy"]], "o-", lw=3, ms=9, color=INSTRUMENT, label="coverage")
    b.plot(fr, [c["risk"][gi] * 100 for c in D["taxonomy"]], "s-", lw=3, ms=9, color=BOUND, label="error")
    b.axhline(5, ls="--", lw=2, color=BOUND)
    b.set_title("The taxonomy changes\ncoverage flat, guarantee breaks", color=BOUND, weight="bold", fontsize=14)
    b.set_xlabel("% of the largest category redefined")

    for ax in (a, b):
        ax.set_ylim(0, 100)
        ax.legend(frameon=False, fontsize=11, loc="center left")
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    a.set_ylabel("percent")
    fig.tight_layout()
    fig.savefig(ROOT / "deck" / "fig_drift.png", dpi=200)
    plt.close(fig)


dial()
drift()
print("deck figures written")
