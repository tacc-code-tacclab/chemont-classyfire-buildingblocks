#!/usr/bin/env python
"""One PDF page per taxonomy: a real indented family-tree of the actual class names,
read straight from database/v4/dag_v4.db.

  chemont_family_tree.pdf : root -> 2 kingdoms -> 31 superclasses (the ChemOnt families)
  target_family_tree.pdf  : root -> 15 groups  -> their protein families (ChEMBL, level 2)
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sqlite3, pathlib

DB = "/data01/cris/projects/DAG/database/v4/dag_v4.db"
FIG = pathlib.Path("/data01/cris/projects/DAG/reports/v4/figures")
TEAL = "#2A9D8F"; TEAL_D = "#1F6F66"
AMBER = "#E08A2E"; AMBER_D = "#B26A1C"
DARK = "#222222"; GREY = "#6C6C6C"; LINE = "#CFCFCF"


def render(rows, out, title, subtitle, accent, accent_dark, note=None):
    """rows: list of dicts {depth, label, kind in {root,group,leaf}, parent_row}"""
    n = len(rows)
    page_w = 8.3
    page_h = min(11.6, 1.5 + 0.26 * n)
    fig, ax = plt.subplots(figsize=(page_w, page_h))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    ax.text(0.02, 0.985, title, ha="left", va="top", fontsize=15, fontweight="bold", color=accent_dark)
    ax.text(0.02, 0.957, subtitle, ha="left", va="top", fontsize=9.5, color=GREY)
    if note:
        ax.text(0.02, 0.935, note, ha="left", va="top", fontsize=8, color=GREY, style="italic")

    top, bot = 0.905, 0.018
    ys = [top - (top - bot) * (i / max(1, n - 1)) for i in range(n)]
    indent = 0.052
    xs = [0.03 + r["depth"] * indent for r in rows]
    fs = 11 if n < 36 else (9.5 if n < 46 else 8.3)

    # connector lines (elbow from each node to its parent)
    for i, r in enumerate(rows):
        p = r["parent_row"]
        if p is None:
            continue
        gx = xs[p] + 0.018
        ax.plot([gx, gx], [ys[p] - 0.008, ys[i]], color=LINE, lw=1.0, zorder=1)
        ax.plot([gx, xs[i] - 0.006], [ys[i], ys[i]], color=LINE, lw=1.0, zorder=1)

    # nodes
    for i, r in enumerate(rows):
        x, y = xs[i], ys[i]
        if r["kind"] == "root":
            ax.scatter([x], [y], s=90, color=accent_dark, edgecolors="white", lw=1, zorder=3)
            ax.text(x + 0.02, y, r["label"], ha="left", va="center", fontsize=fs + 2,
                    fontweight="bold", color=DARK)
        elif r["kind"] == "group":
            ax.scatter([x], [y], s=64, color=accent, edgecolors="white", lw=1, zorder=3)
            ax.text(x + 0.018, y, r["label"], ha="left", va="center", fontsize=fs + 0.5,
                    fontweight="bold", color=accent_dark)
        else:
            ax.scatter([x], [y], s=26, color=accent, edgecolors="none", zorder=3)
            ax.text(x + 0.016, y, r["label"], ha="left", va="center", fontsize=fs,
                    color=(GREY if r.get("dim") else DARK),
                    style=("italic" if r.get("dim") else "normal"))

    fig.savefig(f"{out}.pdf", bbox_inches="tight", facecolor="white")
    fig.savefig(f"{out}.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", out + ".pdf/.png", f"({n} rows)")


c = sqlite3.connect(DB, timeout=60)

# ---------------- ChemOnt : root -> kingdoms -> superclasses
rows = []
rows.append({"depth": 0, "label": "Chemical entities  (root)", "kind": "root", "parent_row": None})
root_i = 0
for king_id, king in c.execute("SELECT chemont_id,name FROM chemont_nodes WHERE depth=1 ORDER BY name DESC"):
    ki = len(rows)
    rows.append({"depth": 1, "label": king, "kind": "group", "parent_row": root_i})
    for (nm,) in c.execute("SELECT name FROM chemont_nodes WHERE parent_id=? ORDER BY name", (king_id,)):
        rows.append({"depth": 2, "label": nm, "kind": "leaf", "parent_row": ki})
render(rows, str(FIG / "chemont_family_tree"),
       "Chemical-structure taxonomy (ChemOnt)",
       "what each molecule IS  ·  root → 2 kingdoms → 31 superclasses  ·  4,825 classes, up to 11 levels",
       TEAL, TEAL_D,
       note="Showing the top families (superclasses); each splits further into finer classes down to level 11.")

# ---------------- ChEMBL : root -> L1 groups -> L2 families
rows = []
rows.append({"depth": 0, "label": "Protein class  (root)", "kind": "root", "parent_row": None})
root_i = 0
for cid, l1 in c.execute("SELECT class_id,pref_name FROM target_class_tree_nodes WHERE class_level=1 ORDER BY pref_name"):
    gi = len(rows)
    rows.append({"depth": 1, "label": l1, "kind": "group", "parent_row": root_i})
    l2 = [r[0] for r in c.execute(
        "SELECT pref_name FROM target_class_tree_nodes WHERE parent_class_id=? ORDER BY pref_name", (cid,))]
    if l1 == "Auxiliary transport protein":  # 11 long, obscure names -> collapse
        rows.append({"depth": 2, "label": f"({len(l2)} auxiliary-subunit families)",
                     "kind": "leaf", "parent_row": gi, "dim": True})
    else:
        for nm in l2:
            rows.append({"depth": 2, "label": nm, "kind": "leaf", "parent_row": gi})
render(rows, str(FIG / "target_family_tree"),
       "Biological-target taxonomy (ChEMBL)",
       "what each molecule ACTS ON  ·  root → 15 groups → protein families  ·  905 classes, up to 6 levels",
       AMBER, AMBER_D,
       note="Showing groups and their protein families (level 2); several families split further into specific "
            "sub-families down to level 6.  Groups with no bullet list are single leaf categories.")

c.close()
