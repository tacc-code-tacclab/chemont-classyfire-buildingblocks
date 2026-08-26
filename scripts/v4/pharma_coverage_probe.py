#!/usr/bin/env python
"""Feasibility probe: how much of the ZINC building-block catalogue can carry a
PHARMACOLOGICAL annotation (as opposed to the structural ChemOnt tree)?

Representative random sample of unique building-block InChIKeys -> ChEMBL lookups.
For each key we record whether it is in ChEMBL at all, its ATC codes (therapeutic
class), its max clinical phase (0..4; 4 = approved drug), and whether it has any
measured bioactivity (proxy for target/mechanism annotation being possible).

Single polite stream, cached + resumable. No bulk hammering.

  python scripts/v4/pharma_coverage_probe.py --n 1200 --seed 20260722 --rps 2
"""
import argparse, sqlite3, json, time, urllib.request, urllib.error, random, pathlib, datetime, sys

ROOT = pathlib.Path("/data01/cris/projects/DAG")
ZINC = ROOT / "database/chemical_taxonomy_zinc.db"
CACHE = ROOT / "data/v4_classyfire_groundtruth/cache/pharma_probe.db"
BASE = "https://www.ebi.ac.uk/chembl/api/data"


def get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "curl/8"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def lookup(ik):
    """Return dict of pharmacology coverage flags for one InChIKey."""
    rec = {"in_chembl": 0, "chembl_id": None, "atc": "", "max_phase": None, "n_act": 0}
    try:
        j = get(f"{BASE}/molecule/{ik}.json")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return rec, "absent"
        return rec, f"HTTP{e.code}"
    except Exception as e:
        return rec, f"ERR:{type(e).__name__}"
    rec["in_chembl"] = 1
    rec["chembl_id"] = j.get("molecule_chembl_id")
    rec["atc"] = ";".join(j.get("atc_classifications") or [])
    rec["max_phase"] = j.get("max_phase")
    # bioactivity presence (proxy for a target/mechanism annotation being possible)
    try:
        a = get(f"{BASE}/activity.json?molecule_chembl_id={rec['chembl_id']}&limit=1")
        rec["n_act"] = a.get("page_meta", {}).get("total_count", 0)
    except Exception:
        pass
    return rec, "present"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1200)
    ap.add_argument("--seed", type=int, default=20260722)
    ap.add_argument("--rps", type=float, default=2.0)
    args = ap.parse_args()

    con = sqlite3.connect(CACHE, timeout=60)
    con.execute("""CREATE TABLE IF NOT EXISTS pharma(
        inchikey TEXT PRIMARY KEY, in_chembl INT, chembl_id TEXT, atc TEXT,
        max_phase REAL, n_act INT, status TEXT)""")
    con.execute("CREATE TABLE IF NOT EXISTS samp(inchikey TEXT PRIMARY KEY, seed INT)")
    con.commit()

    have = con.execute("SELECT COUNT(*) FROM samp WHERE seed=?", (args.seed,)).fetchone()[0]
    if have < args.n:
        zc = sqlite3.connect(f"file:{ZINC}?mode=ro", uri=True, timeout=120)
        iks = list({r[0] for r in zc.execute(
            "SELECT inchikey FROM compounds WHERE inchikey IS NOT NULL AND inchikey!=''")})
        zc.close()
        random.Random(args.seed).shuffle(iks)
        con.executemany("INSERT OR IGNORE INTO samp VALUES (?,?)",
                        [(ik, args.seed) for ik in iks[:args.n]])
        con.commit()
    sample = [r[0] for r in con.execute("SELECT inchikey FROM samp WHERE seed=? LIMIT ?",
                                        (args.seed, args.n))]
    done = {r[0] for r in con.execute("SELECT inchikey FROM pharma")}
    todo = [k for k in sample if k not in done]
    print(f"pharma probe: sample={len(sample)} cached={len(done)} todo={len(todo)}", flush=True)

    interval = 1.0 / args.rps
    nxt = 0.0
    for i, ik in enumerate(todo, 1):
        w = nxt - time.monotonic()
        if w > 0:
            time.sleep(w)
        nxt = time.monotonic() + interval
        for attempt in range(4):
            rec, status = lookup(ik)
            if status.startswith("HTTP4") or status in ("absent", "present"):
                break
            time.sleep(2 * (attempt + 1))  # backoff on transient/429
        con.execute("INSERT OR REPLACE INTO pharma VALUES (?,?,?,?,?,?,?)",
                    (ik, rec["in_chembl"], rec["chembl_id"], rec["atc"],
                     rec["max_phase"], rec["n_act"], status))
        if i % 50 == 0:
            con.commit()
            print(f"  {i}/{len(todo)}", flush=True)
    con.commit()

    # ---- summary over the whole sample
    rows = list(con.execute(
        "SELECT in_chembl, atc, max_phase, n_act FROM pharma WHERE inchikey IN "
        "(SELECT inchikey FROM samp WHERE seed=?)", (args.seed,)))
    n = len(rows)
    in_chembl = sum(r[0] for r in rows)
    with_atc = sum(1 for r in rows if r[1])
    approved = sum(1 for r in rows if (r[2] or 0) >= 4)
    clinical = sum(1 for r in rows if (r[2] or 0) >= 1)
    with_act = sum(1 for r in rows if (r[3] or 0) > 0)
    POOL = 1955032

    def pct(k):
        return f"{k}/{n} = {k/n*100:.2f}%  (~{int(k/n*POOL):,} of {POOL:,})"

    out = {
        "n_sample": n, "pool": POOL,
        "in_chembl": pct(in_chembl),
        "with_bioactivity_target": pct(with_act),
        "with_ATC": pct(with_atc),
        "clinical_phase>=1": pct(clinical),
        "approved_drug_phase4": pct(approved),
    }
    print("\n=== PHARMACOLOGY COVERAGE (ChEMBL) ===")
    print(json.dumps(out, indent=2))
    json.dump(out, open(ROOT / "reports/v4/pharma_coverage.json", "w"), indent=2)
    con.close()


if __name__ == "__main__":
    main()
