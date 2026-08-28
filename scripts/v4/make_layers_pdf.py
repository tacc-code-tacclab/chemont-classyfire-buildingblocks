#!/usr/bin/env python
"""One PDF page per taxonomy showing how many LEVELS (layers) it has and how many
classes live at each level, plus one real root-to-leaf example path."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import sqlite3, pathlib, textwrap

DB = "/data01/cris/projects/DAG/database/v4/dag_v4.db"
FIG = pathlib.Path("/data01/cris/projects/DAG/reports/v4/figures")
TEAL = "#2A9D8F"; TEAL_D = "#1F6F66"
AMBER = "#E08A2E"; AMBER_D = "#B26A1C"
DARK = "#222"; GREY = "#6C6C6C"; TRACK = "#EDEDED"
c = sqlite3.connect(DB, timeout=60)


def deepest_path(table, id_col, name_col, parent_col, level_col, start_name):
    rid, lv = c.execute(f"SELECT {id_col},{level_col} FROM {table} WHERE {name_col}=?",
                        (start_name,)).fetchone()
    frontier = [rid]; deep = (lv, rid)
    while frontier:
        nf = []
        for p in frontier:
            for cid, dd in c.execute(
                    f"SELECT {id_col},{level_col} FROM {table} WHERE {parent_col}=?", (p,)):
                nf.append(cid)
                if dd > deep[0]:
                    deep = (dd, cid)
        frontier = nf
    cur = deep[1]; path = []
    while cur is not None and cur != "":
        nm, par = c.execute(f"SELECT {name_col},{parent_col} FROM {table} WHERE {id_col}=?",
                            (cur,)).fetchone()
        path.append(nm); cur = par
    return list(reversed(path))


def render(out, title, subtitle, levels, accent, accent_dark, example):
    """levels: list of (level_label, meaning, count)"""
    n = len(levels)
    fig, ax = plt.subplots(figsize=(8.3, 6.2))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0.03, 0.965, title, ha="left", va="top", fontsize=16, fontweight="bold", color=accent_dark)
    ax.text(0.03, 0.918, subtitle, ha="left", va="top", fontsize=10.5, color=GREY)

    top, bot = 0.83, 0.30
    maxc = max(c_ for _, _, c_ in levels)
    x_bar0, x_bar1 = 0.52, 0.95
    for i, (lab, meaning, cnt) in enumerate(levels):
        y = top - (top - bot) * (i / (n - 1))
        ax.text(0.03, y, lab, ha="left", va="center", fontsize=11, fontweight="bold", color=accent_dark)
        ax.text(0.10, y, meaning, ha="left", va="center", fontsize=10.5, color=DARK)
        w = (x_bar1 - x_bar0) * (cnt / maxc) ** 0.5
        ax.add_patch(FancyBboxPatch((x_bar0, y - 0.017), max(w, 0.006), 0.034,
                     boxstyle="round,pad=0,rounding_size=0.012", fc=accent, ec="none"))
        ax.text(x_bar0 + max(w, 0.006) + 0.008, y, f"{cnt:,}", ha="left", va="center",
                fontsize=10.5, color=DARK)

    # example path box
    ax.text(0.03, 0.235, "Example of one full path (root → leaf):",
            ha="left", va="top", fontsize=10.5, fontweight="bold", color=DARK)
    wrapped = textwrap.fill("  →  ".join(example), width=88)
    ax.add_patch(FancyBboxPatch((0.03, 0.03), 0.94, 0.175,
                 boxstyle="round,pad=0.01,rounding_size=0.02", fc="#F5F7F7", ec=accent, lw=0.6))
    ax.text(0.055, 0.185, wrapped, ha="left", va="top", fontsize=9.3, color=DARK, family="monospace")
    fig.savefig(f"{out}.pdf", bbox_inches="tight", facecolor="white")
    fig.savefig(f"{out}.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", out + ".pdf")


# ChemOnt
chem_lv = []
names = {0: "root  (Chemical entities)", 1: "kingdom  (Organic / Inorganic)", 2: "superclass  (the 31 families)",
         3: "class", 4: "subclass"}
for d, cnt in c.execute("SELECT depth,COUNT(*) FROM chemont_nodes GROUP BY depth ORDER BY depth"):
    chem_lv.append((f"L{d}", names.get(d, "deeper sub-family"), cnt))
ex_chem = deepest_path("chemont_nodes", "chemont_id", "name", "parent_id", "depth", "Benzenoids")
render(str(FIG / "chemont_layers"), "Chemical-structure taxonomy (ChemOnt) — how many layers",
       "what each molecule IS  ·  4,825 classes across 12 levels (root = level 0)",
       chem_lv, TEAL, TEAL_D, ex_chem)

# ChEMBL
tgt_lv = []
names = {0: "root  (Protein class)", 1: "group  (the 15 top groups)", 2: "family  (protein families)"}
for d, cnt in c.execute("SELECT class_level,COUNT(*) FROM target_class_tree_nodes GROUP BY class_level ORDER BY class_level"):
    tgt_lv.append((f"L{d}", names.get(d, "deeper sub-family"), cnt))
ex_tgt = deepest_path("target_class_tree_nodes", "class_id", "pref_name", "parent_class_id", "class_level", "Enzyme")
render(str(FIG / "target_layers"), "Biological-target taxonomy (ChEMBL) — how many layers",
       "what each molecule ACTS ON  ·  905 classes across 7 levels (root = level 0)",
       tgt_lv, AMBER, AMBER_D, ex_tgt)
c.close()
