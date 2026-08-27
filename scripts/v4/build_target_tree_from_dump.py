#!/usr/bin/env python
"""Build the clean ChEMBL protein-target-class TREE from the offline ChEMBL SQLite dump
and join it onto Layer D (our building-block -> assayed-target table).

The protein-family hierarchy (enzyme -> kinase -> ...; membrane receptor -> GPCR -> ...)
is NOT available over the ChEMBL REST API, so we use the local dump:
  target_dictionary (chembl_id, tid, target_type, organism)
    -> target_components (tid -> component_id)
    -> component_class  (component_id -> protein_class_id)
    -> protein_classification (protein_class_id, parent_id, pref_name, class_level,
                               protein_class_desc = full L1..Ln path)

Outputs (kept SEPARATE from the ChemOnt structural tree):
  database/v4/dag_v4.db : target_class_tree_nodes, target_class_tree_edges  (the taxonomy)
  database/v4/dag_v4.db : target_class_layer_enriched                       (molecule->target->class)
  data/v4_classyfire_groundtruth/target_class_layer_enriched.parquet
  reports/v4/target_class_tree.json
"""
import sqlite3, json, glob, pathlib, sys
import pandas as pd

ROOT = pathlib.Path("/data01/cris/projects/DAG")
TARGET_LAYER = ROOT / "data/v4_classyfire_groundtruth/cache/target_layer.db"
DBV4 = ROOT / "database/v4/dag_v4.db"
OUTPARQ = ROOT / "data/v4_classyfire_groundtruth/target_class_layer_enriched.parquet"


def find_db():
    cands = glob.glob(str(ROOT / "data/external/chembl/**/chembl_*.db"), recursive=True)
    if not cands:
        sys.exit("ChEMBL .db not found yet under data/external/chembl/ (extract first)")
    return max(cands, key=lambda p: pathlib.Path(p).stat().st_size)


def main():
    dbp = find_db()
    print("ChEMBL dump:", dbp)
    ch = sqlite3.connect(f"file:{dbp}?mode=ro", uri=True, timeout=120)

    # our distinct assayed targets
    tl = sqlite3.connect(f"file:{TARGET_LAYER}?mode=ro", uri=True, timeout=60)
    tids = [r[0] for r in tl.execute("SELECT DISTINCT target_chembl_id FROM mol_targets")]
    tl.close()
    print("distinct targets to classify:", len(tids))

    # ---- 1) export the full protein-classification tree (small, ~1k rows)
    pc = pd.read_sql_query(
        "SELECT protein_class_id, parent_id, pref_name, class_level, protein_class_desc "
        "FROM protein_classification", ch)
    print("protein_classification rows:", len(pc))

    # ---- 2) map each target -> its protein class rows
    ch.execute("CREATE TEMP TABLE want(cid TEXT PRIMARY KEY)")
    ch.executemany("INSERT OR IGNORE INTO want VALUES (?)", [(t,) for t in tids])
    q = """
      SELECT td.chembl_id AS target_chembl_id, td.pref_name AS target_pref_name,
             td.target_type, td.organism,
             pc.protein_class_id, pc.class_level, pc.pref_name AS class_name,
             pc.protein_class_desc
      FROM target_dictionary td
      JOIN want w ON td.chembl_id = w.cid
      LEFT JOIN target_components tc ON td.tid = tc.tid
      LEFT JOIN component_class cc ON tc.component_id = cc.component_id
      LEFT JOIN protein_classification pc ON cc.protein_class_id = pc.protein_class_id
    """
    tmap = pd.read_sql_query(q, ch)
    ch.close()

    # split the full path "enzyme  kinase  ..." into levels
    def levels(desc):
        if not isinstance(desc, str) or not desc:
            return []
        parts = [p for p in desc.replace("\t", "  ").split("  ") if p.strip()]
        return [p.strip() for p in parts]
    tmap["path"] = tmap["protein_class_desc"].map(levels)
    for i in range(1, 4):
        tmap[f"class_l{i}"] = tmap["path"].map(lambda p: p[i-1] if len(p) >= i else None)
    tmap["class_leaf"] = tmap["class_name"]
    tmap["protein_class_path"] = tmap["path"].map(lambda p: " > ".join(p) if p else None)

    # one representative class row per target (deepest class)
    tmap["depth"] = tmap["class_level"].fillna(0)
    tgt_class = (tmap.sort_values("depth", ascending=False)
                 .drop_duplicates("target_chembl_id")
                 [["target_chembl_id", "target_pref_name", "target_type", "organism",
                   "class_l1", "class_l2", "class_l3", "class_leaf", "protein_class_path"]])

    # ---- 3) join onto the molecule->target layer
    layer = pd.read_parquet(ROOT / "data/v4_classyfire_groundtruth/target_class_layer.parquet")
    enr = layer.merge(tgt_class.drop(columns=["target_pref_name", "target_type", "organism"]),
                      on="target_chembl_id", how="left")
    enr.to_parquet(OUTPARQ, index=False)

    dbc = sqlite3.connect(DBV4, timeout=120)
    # the taxonomy tree itself
    pc.rename(columns={"protein_class_id": "class_id", "parent_id": "parent_class_id"}).to_sql(
        "target_class_tree_nodes", dbc, if_exists="replace", index=False)
    edges = pc[pc["parent_id"].notna()][["parent_id", "protein_class_id"]].rename(
        columns={"parent_id": "parent_class_id", "protein_class_id": "child_class_id"})
    edges.to_sql("target_class_tree_edges", dbc, if_exists="replace", index=False)
    enr.to_sql("target_class_layer_enriched", dbc, if_exists="replace", index=False)
    dbc.commit(); dbc.close()

    # ---- 4) summary
    classified_targets = tgt_class[tgt_class["class_l1"].notna()]
    mol_with_class = enr[enr["class_l1"].notna()]["inchikey"].nunique()
    summary = {
        "chembl_dump": pathlib.Path(dbp).name,
        "protein_classification_tree_size": int(len(pc)),
        "tree_depth_levels": int(pc["class_level"].max()) if len(pc) else None,
        "distinct_targets": int(len(tids)),
        "targets_with_protein_class": int(len(classified_targets)),
        "targets_with_protein_class_pct": f"{len(classified_targets)/max(1,len(tids))*100:.1f}%",
        "molecules_total_in_layer": int(enr["inchikey"].nunique()),
        "molecules_with_a_protein_class": int(mol_with_class),
        "by_class_l1": classified_targets["class_l1"].value_counts().to_dict(),
        "by_class_l2_top": classified_targets["class_l2"].value_counts().head(15).to_dict(),
    }
    json.dump(summary, open(ROOT / "reports/v4/target_class_tree.json", "w"), indent=2, default=str)
    print(json.dumps(summary, indent=2, default=str))
    print("\nwrote:", OUTPARQ, "and dag_v4.db tables target_class_tree_{nodes,edges}, "
          "target_class_layer_enriched")


if __name__ == "__main__":
    main()
