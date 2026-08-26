#!/usr/bin/env python
"""PROTOTYPE — Layer D (pharmacology facet): ChEMBL target-class annotation for the
subset of building blocks that are in ChEMBL (from the pharma coverage probe).

Kept SEPARATE from the structural ChemOnt tree. For each in-ChEMBL building block we
record the distinct protein targets it has been assayed against (name, organism,
target type), plus a best-effort protein-family class (ChEMBL protein classification).

Robust to a slow/flaky ChEMBL API: long timeouts, exponential backoff, gentle single
stream, cached + resumable. Re-run to continue.

Outputs:
  database/v4/dag_v4.db  table  target_class_layer   (one row per molecule-target pair)
  data/v4_classyfire_groundtruth/target_class_layer.parquet
  reports/v4/target_class_layer.json  (summary)
"""
import sqlite3, json, time, urllib.request, urllib.error, pathlib, datetime
import pandas as pd

ROOT = pathlib.Path("/data01/cris/projects/DAG")
PHARMA = ROOT / "data/v4_classyfire_groundtruth/cache/pharma_probe.db"
CACHE = ROOT / "data/v4_classyfire_groundtruth/cache/target_layer.db"
DBV4 = ROOT / "database/v4/dag_v4.db"
OUTPARQ = ROOT / "data/v4_classyfire_groundtruth/target_class_layer.parquet"
B = "https://www.ebi.ac.uk/chembl/api/data"
LOG = ROOT / "logs/v4/target_layer.log"


def log(m):
    with open(LOG, "a") as fh:
        fh.write(f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {m}\n")


def get(url, tries=6):
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json",
                                                       "User-Agent": "curl/8"})
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(min(60, 3 * (a + 1)))
        except Exception:
            time.sleep(min(60, 3 * (a + 1)))
    return None


def main():
    con = sqlite3.connect(CACHE, timeout=60)
    con.execute("""CREATE TABLE IF NOT EXISTS mol_targets(
        inchikey TEXT, chembl_id TEXT, target_chembl_id TEXT, target_pref_name TEXT,
        target_organism TEXT, target_type TEXT)""")
    con.execute("CREATE TABLE IF NOT EXISTS mol_done(inchikey TEXT PRIMARY KEY)")
    con.execute("""CREATE TABLE IF NOT EXISTS target_class(
        target_chembl_id TEXT PRIMARY KEY, target_type TEXT, pref_name TEXT,
        organism TEXT, class_l1 TEXT, class_l2 TEXT)""")
    con.commit()

    pc = sqlite3.connect(f"file:{PHARMA}?mode=ro", uri=True, timeout=60)
    mols = pc.execute("SELECT inchikey, chembl_id FROM pharma WHERE in_chembl=1").fetchall()
    pc.close()
    done = {r[0] for r in con.execute("SELECT inchikey FROM mol_done")}
    todo = [(ik, cid) for ik, cid in mols if ik not in done]
    log(f"start: molecules in ChEMBL={len(mols)} todo={len(todo)}")
    print(f"molecules in ChEMBL={len(mols)}  todo={len(todo)}", flush=True)

    # ---- stage 1: molecule -> distinct targets (from activities)
    for i, (ik, cid) in enumerate(todo, 1):
        j = get(f"{B}/activity.json?molecule_chembl_id={cid}"
                f"&only=target_chembl_id,target_pref_name,target_organism&limit=1000")
        seen = {}
        if j and j.get("activities"):
            for a in j["activities"]:
                t = a.get("target_chembl_id")
                if t and t not in seen:
                    seen[t] = (a.get("target_pref_name"), a.get("target_organism"))
        for t, (nm, org) in seen.items():
            con.execute("INSERT INTO mol_targets VALUES (?,?,?,?,?,?)",
                        (ik, cid, t, nm, org, None))
        con.execute("INSERT OR IGNORE INTO mol_done VALUES (?)", (ik,))
        con.commit()
        if i % 10 == 0:
            print(f"  stage1 {i}/{len(todo)}", flush=True)
        time.sleep(0.7)

    # ---- stage 2: enrich each distinct target with type + protein-family class
    tids = [r[0] for r in con.execute(
        "SELECT DISTINCT target_chembl_id FROM mol_targets WHERE target_chembl_id NOT IN "
        "(SELECT target_chembl_id FROM target_class)")]
    log(f"stage2: distinct targets to classify={len(tids)}")
    print(f"stage2: targets to classify={len(tids)}", flush=True)
    for i, t in enumerate(tids, 1):
        j = get(f"{B}/target/{t}.json")
        l1 = l2 = ttype = pref = org = None
        if j:
            ttype = j.get("target_type"); pref = j.get("pref_name"); org = j.get("organism")
            comp = j.get("target_components") or []
            if comp:
                cls = comp[0].get("target_component_classifications") or []
                # best-effort readable levels if present
                if cls:
                    c0 = cls[0]
                    l1 = c0.get("l1") or c0.get("protein_class_l1")
                    l2 = c0.get("l2") or c0.get("protein_class_l2")
        con.execute("INSERT OR REPLACE INTO target_class VALUES (?,?,?,?,?,?)",
                    (t, ttype, pref, org, l1, l2))
        con.commit()
        if i % 20 == 0:
            print(f"  stage2 {i}/{len(tids)}", flush=True)
        time.sleep(0.7)

    # ---- assemble the layer
    df = pd.read_sql_query("""
        SELECT m.inchikey, m.chembl_id, m.target_chembl_id,
               COALESCE(tc.pref_name, m.target_pref_name) AS target_pref_name,
               COALESCE(tc.organism, m.target_organism)   AS target_organism,
               tc.target_type, tc.class_l1 AS protein_class_l1, tc.class_l2 AS protein_class_l2
        FROM mol_targets m LEFT JOIN target_class tc
          ON m.target_chembl_id = tc.target_chembl_id""", con)
    df.to_parquet(OUTPARQ, index=False)
    dbc = sqlite3.connect(DBV4, timeout=60)
    df.to_sql("target_class_layer", dbc, if_exists="replace", index=False)
    dbc.commit(); dbc.close()

    n_mol = df.inchikey.nunique()
    summary = {
        "molecules_in_chembl": len(mols),
        "molecules_with_at_least_one_target": int(n_mol),
        "molecule_target_pairs": int(len(df)),
        "distinct_targets": int(df.target_chembl_id.nunique()),
        "by_target_type": df.drop_duplicates("target_chembl_id").target_type.value_counts(dropna=False).to_dict(),
        "by_protein_class_l1": df.drop_duplicates("target_chembl_id").protein_class_l1.value_counts(dropna=False).head(15).to_dict(),
        "top_targets": df.target_pref_name.value_counts().head(15).to_dict(),
        "top_organisms": df.drop_duplicates(["inchikey","target_organism"]).target_organism.value_counts().head(8).to_dict(),
    }
    json.dump(summary, open(ROOT / "reports/v4/target_class_layer.json", "w"), indent=2, default=str)
    log(f"done: {n_mol} molecules, {len(df)} pairs, {df.target_chembl_id.nunique()} targets")
    print(json.dumps(summary, indent=2, default=str))
    con.close()


if __name__ == "__main__":
    main()
