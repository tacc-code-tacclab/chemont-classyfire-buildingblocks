#!/usr/bin/env python
"""Phase 7 (preliminary): benchmark the V3 61-rule mapper on the GENUINE building-block
ground truth accumulated so far, mirroring the V3 harness metrics.

This closes the loop on the *target* domain (commercial building blocks) rather than the
environmental OOD set. It is preliminary while genuine labels keep accumulating; N grows as
`acquire_ground_truth.py` runs. Compares directly to the reproduced OOD numbers.
"""
import sys, types, pathlib, json
import pandas as pd

ROOT = pathlib.Path("/data01/cris/projects/DAG")
PILOT = ROOT / "data/v4_classyfire_groundtruth/resources_extracted/pilot_v3/pilot"
OBO = ROOT / "data/external/chemont/ChemOnt_2_1.obo"
GT = ROOT / "data/v4_classyfire_groundtruth/classyfire_ground_truth.parquet"


def obonet_shim():
    import networkx as nx
    def read_obo(path):
        g = nx.MultiDiGraph(); cur = None
        def add(c):
            g.add_node(c["id"], name=c["name"])
            for p in c["is_a"]:
                g.add_edge(c["id"], p, key="is_a")
        for line in open(path, encoding="utf-8"):
            line = line.rstrip("\n")
            if line == "[Term]":
                if cur and cur["id"]:
                    add(cur)
                cur = {"id": None, "name": None, "is_a": []}
            elif line.startswith("[") and line != "[Term]":
                if cur and cur["id"]:
                    add(cur)
                cur = None
            elif cur is not None:
                if line.startswith("id:"):
                    cur["id"] = line.split(":", 1)[1].strip()
                elif line.startswith("name:"):
                    cur["name"] = line.split(":", 1)[1].strip()
                elif line.startswith("is_a:"):
                    cur["is_a"].append(line.split(":", 1)[1].strip().split("!")[0].strip())
        if cur and cur["id"]:
            add(cur)
        return g
    m = types.ModuleType("obonet"); m.read_obo = read_obo
    return m


def main():
    sys.modules["obonet"] = obonet_shim()
    sys.path.insert(0, str(PILOT))
    from chemont_rules import classify_smiles
    from lineage import load_obo, build_name_index, expand
    G = load_obo(str(OBO)); idx = build_name_index(G)

    df = pd.read_parquet(GT)
    LVLCOLS = ["classyfire_kingdom", "classyfire_superclass", "classyfire_class",
               "classyfire_subclass", "classyfire_terminal_name"]
    rows = []
    for _, r in df.iterrows():
        smi = r["standardized_smiles"]
        if not isinstance(smi, str) or not smi:
            continue
        res = classify_smiles(smi)
        prim = res["primary"]
        lin = expand(G, idx, prim) if prim else None
        names = [n for _, n in lin] if lin else []
        gt_terminal = r["classyfire_terminal_name"]
        gt_set = {r[c] for c in LVLCOLS if isinstance(r[c], str) and r[c]}
        alln = {h["chemont_name"] for h in res["all"]}
        my_super = names[2] if len(names) > 2 else ""
        my_class = names[3] if len(names) > 3 else ""
        rows.append({
            "inchikey": r["inchikey"], "gt_terminal": gt_terminal,
            "gt_super": r["classyfire_superclass"], "gt_class": r["classyfire_class"],
            "my_primary": prim or "",
            "on_path": bool(prim) and prim in gt_set,
            "exact": bool(prim) and prim == gt_terminal,
            "any_match": bool(alln & gt_set),
            "super_ok": (my_super == r["classyfire_superclass"]) if isinstance(r["classyfire_superclass"], str) and r["classyfire_superclass"] else None,
            "class_ok": (my_class == r["classyfire_class"]) if isinstance(r["classyfire_class"], str) and r["classyfire_class"] else None,
        })
    b = pd.DataFrame(rows)
    n = len(b)
    so = b.super_ok.dropna(); co = b.class_ok.dropna()
    out = {
        "n_target_domain": int(n),
        "coverage_primary": float((b.my_primary != "").mean()),
        "on_path": float(b.on_path.mean()),
        "any_match": float(b.any_match.mean()),
        "exact_leaf": float(b.exact.mean()),
        "superclass": float(so.mean()) if len(so) else None,
        "class": float(co.mean()) if len(co) else None,
        "n_super": int(len(so)), "n_class": int(len(co)),
    }
    b.to_csv(ROOT / "results/v4_chemont_mapper/target_domain_detail.csv", index=False)
    json.dump(out, open(ROOT / "reports/v4/target_domain_benchmark.json", "w"), indent=2)
    print(json.dumps(out, indent=2))
    print("\nper genuine superclass (target domain):")
    g = b.copy()
    g["super_ok_b"] = g.super_ok.fillna(False)
    for sc, sub in g.groupby("gt_super"):
        print(f"  {sc:36s} n={len(sub):3d}  super_ok={sub.super_ok.dropna().mean()*100 if len(sub.super_ok.dropna()) else 0:5.1f}%"
              f"  on_path={sub.on_path.mean()*100:5.1f}%  exact={sub.exact.mean()*100:5.1f}%")


if __name__ == "__main__":
    main()
