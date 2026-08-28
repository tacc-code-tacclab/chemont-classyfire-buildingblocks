#!/usr/bin/env python
"""Grant-panel schematic: the two taxonomies at a glance. Deliberately label-light."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import pathlib

OUT = pathlib.Path("/data01/cris/projects/DAG/reports/v4/figures/taxonomy_schematic")

TEAL = "#2A9D8F"
AMBER = "#E08A2E"
EDGE = "#C7C7C7"
DARK = "#222222"
GREY = "#6C6C6C"
TRACK = "#E7E7E7"


def positions(counts, x0, x1, ys, pad=0.05):
    lv = []
    for c, y in zip(counts, ys):
        if c == 1:
            xs = [(x0 + x1) / 2]
        else:
            xs = [x0 + pad + (x1 - x0 - 2 * pad) * (i / (c - 1)) for i in range(c)]
        lv.append([(x, y) for x in xs])
    return lv


def draw_tree(ax, levels, color, node_s):
    for li in range(1, len(levels)):
        prev, cur = levels[li - 1], levels[li]
        for i, (x, y) in enumerate(cur):
            pi = int(round(i * (len(prev) - 1) / max(1, len(cur) - 1))) if len(cur) > 1 else 0
            px, py = prev[pi]
            ax.plot([px, x], [py, y], color=EDGE, lw=1.1, zorder=1)
    for li, lv in enumerate(levels):
        s = node_s if li else node_s * 1.8  # root a touch bigger
        ax.scatter([p[0] for p in lv], [p[1] for p in lv], s=s,
                   color=color, edgecolors="white", linewidths=1.1, zorder=3)


def coverage(ax, x0, x1, y, frac, color, label):
    h = 0.035
    ax.add_patch(FancyBboxPatch((x0, y), x1 - x0, h, boxstyle="round,pad=0,rounding_size=0.02",
                                fc=TRACK, ec="none", zorder=2))
    ax.add_patch(FancyBboxPatch((x0, y), (x1 - x0) * frac, h,
                                boxstyle="round,pad=0,rounding_size=0.02",
                                fc=color, ec="none", zorder=3))
    ax.text((x0 + x1) / 2, y - 0.055, label, ha="center", va="top", fontsize=8.5, color=GREY)


fig, ax = plt.subplots(figsize=(7.6, 3.5))
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

# supertitle
ax.text(0.5, 0.975, "Two complementary molecule taxonomies",
        ha="center", va="top", fontsize=11, color=DARK, fontweight="bold")

# thin divider
ax.plot([0.5, 0.5], [0.08, 0.80], color="#E2E2E2", lw=1.0, zorder=0)

# ---------------- LEFT: structural taxonomy (deep & broad, covers all)
lx0, lx1 = 0.04, 0.46
ax.text((lx0 + lx1) / 2, 0.85, "STRUCTURE", ha="center", va="center",
        fontsize=11.5, color=TEAL, fontweight="bold")
ax.text((lx0 + lx1) / 2, 0.805, "what each molecule IS", ha="center", va="center",
        fontsize=9, color=GREY)
Ltree = positions([1, 2, 4, 7], lx0, lx1, [0.75, 0.62, 0.49, 0.36])
draw_tree(ax, Ltree, TEAL, node_s=70)
ax.text((lx0 + lx1) / 2, 0.285, "deep & broad  ·  every molecule fits",
        ha="center", va="center", fontsize=8.5, color=DARK)
coverage(ax, lx0, lx1, 0.16, 1.0, TEAL, "covers the WHOLE library")

# ---------------- RIGHT: target taxonomy (shallow, few families, subset)
rx0, rx1 = 0.54, 0.96
ax.text((rx0 + rx1) / 2, 0.85, "TARGET", ha="center", va="center",
        fontsize=11.5, color=AMBER, fontweight="bold")
ax.text((rx0 + rx1) / 2, 0.805, "what each molecule ACTS ON", ha="center", va="center",
        fontsize=9, color=GREY)
Rtree = positions([1, 4, 9], rx0, rx1, [0.75, 0.55, 0.40])
draw_tree(ax, Rtree, AMBER, node_s=90)
# four short anchor words on the L1 row
for (x, y), lab in zip(Rtree[1], ["Enzyme", "Receptor", "Channel", "Transporter"]):
    ax.text(x, y + 0.075, lab, ha="center", va="bottom", fontsize=8.2, color=DARK,
            bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none"))
ax.text((rx0 + rx1) / 2, 0.285, "a few protein families  ·  only assayed molecules",
        ha="center", va="center", fontsize=8.5, color=DARK)
coverage(ax, rx0, rx1, 0.16, 0.07, AMBER, "covers a SUBSET (~7%)")

fig.savefig(f"{OUT}.png", dpi=300, bbox_inches="tight", facecolor="white")
fig.savefig(f"{OUT}.pdf", bbox_inches="tight", facecolor="white")
print("wrote", f"{OUT}.png", "and", f"{OUT}.pdf")
