#!/usr/bin/env python
"""Multi-page PDF per taxonomy: ONE top-family per page, showing its sub-families.
Each page auto-caps its depth so the whole sub-tree fits on a single page; branches
that go deeper are marked '(+N deeper)'.

  chemont_subfamilies.pdf : one page per ChemOnt superclass (31 pages)
  target_subfamilies.pdf  : one page per ChEMBL group (15 pages)
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import sqlite3, pathlib

DB = "/data01/cris/projects/DAG/database/v4/dag_v4.db"
FIG = pathlib.Path("/data01/cris/projects/DAG/reports/v4/figures")
TEAL = "#2A9D8F"; TEAL_D = "#1F6F66"
AMBER = "#E08A2E"; AMBER_D = "#B26A1C"
DARK = "#222"; GREY = "#6C6C6C"; LINE = "#CFCFCF"
BUDGET = 50
c = sqlite3.connect(DB, timeout=60)


def subtree_size(node_id, children):
    tot = 0
    for cid, _ in children(node_id):
        tot += 1 + subtree_size(cid, children)
    return tot


def build_rows(root_id, root_label, children):
    """Pick the deepest cap that fits BUDGET, then DFS to that cap."""
    # count nodes per relative depth
    per = {0: 1}; frontier = [root_id]; d = 0
    while frontier:
        d += 1; nxt = []
        for p in frontier:
            for cid, _ in children(p):
                nxt.append(cid)
        if nxt:
            per[d] = len(nxt)
        frontier = nxt
    cap = 1
    while cap + 1 in per and sum(per[k] for k in range(cap + 2)) <= BUDGET:
        cap += 1
    rows = []

    def walk(nid, label, depth, parent_row):
        idx = len(rows)
        row = {"depth": depth, "label": label, "parent": parent_row,
               "kind": "root" if depth == 0 else "node", "extra": None}
        rows.append(row)
        kids = children(nid)
        if depth >= cap:
            if kids:
                hidden = sum(1 + subtree_size(k, children) for k, _ in kids)
                row["extra"] = f"(+{hidden} deeper)"
            return
        for cid, nm in kids:
            walk(cid, nm, depth + 1, idx)

    walk(root_id, root_label, 0, None)
    return rows, cap


def draw_page(pdf, rows, title, breadcrumb, accent, accent_dark, subtitle):
    n = len(rows)
    HEAD, ROW, BOTM = 1.15, 0.26, 0.2          # inches
    page_h = HEAD + ROW * n + BOTM
    fig, ax = plt.subplots(figsize=(8.3, page_h))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    def yf(inch_from_top):
        return 1 - inch_from_top / page_h
    ax.text(0.03, yf(0.30), title, ha="left", va="top", fontsize=15, fontweight="bold", color=accent_dark)
    ax.text(0.03, yf(0.62), breadcrumb, ha="left", va="top", fontsize=8.5, color=GREY)
    ax.text(0.03, yf(0.82), subtitle, ha="left", va="top", fontsize=9, color=GREY, style="italic")

    top, bot = yf(HEAD), yf(page_h - BOTM)
    ys = [top - (top - bot) * (i / max(1, n - 1)) for i in range(n)]
    indent = 0.05
    xs = [0.03 + r["depth"] * indent for r in rows]
    fs = 11 if n < 26 else (9.5 if n < 40 else 8.2)
    for i, r in enumerate(rows):
        p = r["parent"]
        if p is None:
            continue
        gx = xs[p] + 0.017
        ax.plot([gx, gx], [ys[p] - 0.006, ys[i]], color=LINE, lw=1.0, zorder=1)
        ax.plot([gx, xs[i] - 0.006], [ys[i], ys[i]], color=LINE, lw=1.0, zorder=1)
    for i, r in enumerate(rows):
        x, y = xs[i], ys[i]
        if r["kind"] == "root":
            ax.scatter([x], [y], s=90, color=accent_dark, edgecolors="white", lw=1, zorder=3)
            ax.text(x + 0.02, y, r["label"], ha="left", va="center", fontsize=fs + 2,
                    fontweight="bold", color=DARK)
        else:
            bold = r["depth"] == 1
            ax.scatter([x], [y], s=(54 if bold else 26), color=accent,
                       edgecolors="white" if bold else "none", lw=1, zorder=3)
            txt = r["label"] + (f"   {r['extra']}" if r["extra"] else "")
            ax.text(x + 0.016, y, txt, ha="left", va="center", fontsize=fs,
                    fontweight=("bold" if bold else "normal"),
                    color=(accent_dark if bold else DARK))
    pdf.savefig(fig, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def chem_children(nid):
    return c.execute("SELECT chemont_id,name FROM chemont_nodes WHERE parent_id=? ORDER BY name", (nid,)).fetchall()


def tgt_children(nid):
    return c.execute("SELECT class_id,pref_name FROM target_class_tree_nodes WHERE parent_class_id=? ORDER BY pref_name", (nid,)).fetchall()


# ---- ChemOnt: one page per superclass
supers = c.execute("SELECT chemont_id,name FROM chemont_nodes WHERE depth=2 ORDER BY name").fetchall()
with PdfPages(FIG / "chemont_subfamilies.pdf") as pdf:
    for sid, sname in supers:
        rows, cap = build_rows(sid, sname, chem_children)
        total = subtree_size(sid, chem_children)
        draw_page(pdf, rows,
                  f"ChemOnt superclass:  {sname}",
                  "Chemical entities  →  Organic/Inorganic compounds  →  this superclass",
                  TEAL, TEAL_D,
                  f"{total} sub-classes below in total  ·  shown to depth {cap} (branches marked '(+N deeper)' continue further)")
print("wrote chemont_subfamilies.pdf", len(supers), "pages")

# ---- ChEMBL: one page per group
groups = c.execute("SELECT class_id,pref_name FROM target_class_tree_nodes WHERE class_level=1 ORDER BY pref_name").fetchall()
with PdfPages(FIG / "target_subfamilies.pdf") as pdf:
    for gid, gname in groups:
        rows, cap = build_rows(gid, gname, tgt_children)
        total = subtree_size(gid, tgt_children)
        sub = (f"{total} sub-families below in total  ·  shown to depth {cap}"
               if total else "single leaf category (no sub-families)")
        draw_page(pdf, rows, f"ChEMBL target group:  {gname}",
                  "Protein class  →  this group  →  protein families …",
                  AMBER, AMBER_D, sub)
print("wrote target_subfamilies.pdf", len(groups), "pages")
c.close()
