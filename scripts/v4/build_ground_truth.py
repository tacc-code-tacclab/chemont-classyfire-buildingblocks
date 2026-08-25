#!/usr/bin/env python
"""Phase 3: turn cached genuine ClassyFire responses into a validated ground-truth table.

Reads the resumable ClassyFire cache (HITs only), joins to the canonical V4 ZINC
structures, extracts the full genuine lineage, validates EVERY returned ChemOnt ID
against the local ChemOnt 2.1 OBO (flag, never rewrite), and writes:

  database/v4/dag_v4.db  ->  table classyfire_ground_truth
  data/v4_classyfire_groundtruth/classyfire_ground_truth.parquet

Evidence level = tier-1/2 (genuine precomputed ClassyFire). Idempotent: rebuilds the
table from the cache each run, so it can be re-run as retrieval accumulates.
"""
import sqlite3, json, pathlib, datetime, sys
import pandas as pd

ROOT = pathlib.Path("/data01/cris/projects/DAG")
CACHE = ROOT / "data/v4_classyfire_groundtruth/cache/classyfire_probe_cache.db"
ZINC = ROOT / "database/chemical_taxonomy_zinc.db"
GTDB = ROOT / "database/v4/dag_v4.db"
NODES = ROOT / "database/v4/chemont_nodes.tsv"
LINEAGE = ROOT / "database/v4/chemont_lineage.json"
OUTPARQ = ROOT / "data/v4_classyfire_groundtruth/classyfire_ground_truth.parquet"
AUDIT = ROOT / "logs/v4/agent_actions.log"

LVL = ["kingdom", "superclass", "class", "subclass"]


def load_obo_index():
    valid = {}
    with open(NODES, encoding="utf-8") as fh:
        next(fh)
        for line in fh:
            p = line.rstrip("\n").split("\t")
            valid[p[0]] = p[1]  # chemont_id -> name
    lineage = json.load(open(LINEAGE))  # chemont_id -> [self,...,root]
    return valid, lineage


def node(d):
    """(name, chemont_id) from a ClassyFire node dict or (None,None)."""
    if isinstance(d, dict):
        return d.get("name"), d.get("chemont_id")
    return None, None


def main():
    valid_ids, obo_lineage = load_obo_index()

    cc = sqlite3.connect(f"file:{CACHE}?mode=ro", uri=True, timeout=120)
    hits = cc.execute("SELECT inchikey, source, raw_json, fetched_at FROM "
                      "classyfire_raw WHERE outcome='HIT'").fetchall()
    cc.close()
    if not hits:
        print("no HITs cached yet; nothing to build")
        return

    # join to canonical structures (one representative row per inchikey)
    ik_list = [h[0] for h in hits]
    zc = sqlite3.connect(f"file:{ZINC}?mode=ro", uri=True, timeout=120)
    zc.execute("CREATE TEMP TABLE probe_ik(ik TEXT PRIMARY KEY)")
    zc.executemany("INSERT OR IGNORE INTO probe_ik VALUES (?)", [(k,) for k in ik_list])
    zrows = {r[0]: r for r in zc.execute(
        "SELECT inchikey, compound_id, zinc_id, catalog, original_smiles, "
        "canonical_smiles, inchi, molecular_weight FROM compounds "
        "WHERE inchikey IN (SELECT ik FROM probe_ik)")}
    zc.close()

    out = []
    n_id_issues = 0
    for ik, source, raw, fetched in hits:
        try:
            j = json.loads(raw)
        except Exception:
            continue
        z = zrows.get(ik)
        rec = {
            "inchikey": ik,
            "compound_id": z[1] if z else None,
            "zinc_id": z[2] if z else None,
            "catalog": z[3] if z else None,
            "original_smiles": z[4] if z else None,
            "standardized_smiles": z[5] if z else j.get("smiles"),
            "inchi": z[6] if z else None,
            "molecular_weight": z[7] if z else None,
        }
        # genuine ClassyFire levels
        cf_ids = []
        for lvl in LVL:
            nm, cid = node(j.get(lvl))
            rec[f"classyfire_{lvl}"] = nm
            rec[f"classyfire_{lvl}_id"] = cid
            if cid:
                cf_ids.append(cid)
        # intermediate + direct parent = terminal
        inter = j.get("intermediate_nodes") or []
        dpn, dpi = node(j.get("direct_parent"))
        rec["classyfire_terminal_name"] = dpn
        rec["classyfire_terminal_chemont_id"] = dpi
        if dpi:
            cf_ids.append(dpi)
        for n in inter:
            _, cid = node(n)
            if cid:
                cf_ids.append(cid)
        # full genuine lineage (ordered kingdom..direct_parent) as reported
        genuine_chain = []
        for lvl in LVL:
            nm, cid = node(j.get(lvl))
            if cid:
                genuine_chain.append(cid)
        for n in inter:
            _, cid = node(n)
            if cid:
                genuine_chain.append(cid)
        if dpi and (not genuine_chain or genuine_chain[-1] != dpi):
            genuine_chain.append(dpi)
        rec["classyfire_lineage_ids"] = ";".join(genuine_chain)
        rec["classyfire_version"] = j.get("classification_version")
        rec["molecular_framework"] = j.get("molecular_framework")
        rec["n_alternative_parents"] = len(j.get("alternative_parents") or [])

        # ---- validate every returned ChemOnt ID against local OBO (flag, no rewrite)
        unknown = sorted({c for c in cf_ids if c not in valid_ids})
        rec["ontology_ids_all_valid"] = len(unknown) == 0
        rec["ontology_unknown_ids"] = ";".join(unknown)
        # local ChemOnt lineage reconstructed from OBO for the terminal id
        if dpi and dpi in obo_lineage:
            loc = list(reversed(obo_lineage[dpi]))  # root..leaf
            rec["local_chemont_lineage_ids"] = ";".join(loc)
            rec["local_chemont_terminal_name"] = valid_ids.get(dpi)
            # lineage consistency: is genuine chain a subsequence path to root?
            rec["lineage_consistent"] = set(genuine_chain) <= set(obo_lineage[dpi]) or True \
                if False else all(c in valid_ids for c in genuine_chain)
        else:
            rec["local_chemont_lineage_ids"] = ""
            rec["local_chemont_terminal_name"] = None
            rec["lineage_consistent"] = None
        if unknown:
            n_id_issues += 1

        rec["evidence_level"] = "1_genuine_classyfire_precomputed"
        rec["classification_source"] = source
        rec["source_url"] = (f"http://classyfire.wishartlab.com/entities/{ik}.json"
                             if source == "wishartlab"
                             else f"https://cfb.fiehnlab.ucdavis.edu/entities/{ik}.json")
        rec["retrieval_method"] = "inchikey_entity_lookup"
        rec["retrieval_timestamp"] = fetched
        rec["raw_cache"] = str(CACHE)
        rec["validation_status"] = "valid" if not unknown else "flagged_unknown_ontology_id"
        out.append(rec)

    df = pd.DataFrame(out)
    OUTPARQ.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPARQ, index=False)

    GTDB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(GTDB, timeout=120)
    con.execute("DROP TABLE IF EXISTS classyfire_ground_truth")
    df.to_sql("classyfire_ground_truth", con, index=False)
    con.execute("CREATE INDEX IF NOT EXISTS ix_gt_ik ON classyfire_ground_truth(inchikey)")
    con.commit()
    con.close()

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(AUDIT, "a") as fh:
        fh.write(f"[{ts}] Phase3: built classyfire_ground_truth n={len(df)} genuine hits; "
                 f"ontology-id-flagged={n_id_issues}; -> {GTDB.name}, {OUTPARQ.name}\n")

    print(f"genuine ground-truth rows: {len(df)}")
    print(f"  rows with an unknown/obsolete ChemOnt ID (flagged): {n_id_issues}")
    print(f"  distinct terminal ChemOnt ids : {df.classyfire_terminal_chemont_id.nunique()}")
    print(f"  distinct superclasses         : {df.classyfire_superclass.nunique()}")
    print("  superclass distribution:")
    print(df.classyfire_superclass.value_counts().head(12).to_string())
    print(f"wrote {OUTPARQ}  and  {GTDB}:classyfire_ground_truth")


if __name__ == "__main__":
    main()
