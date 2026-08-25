#!/usr/bin/env python
"""Phase 5 + Phase 7 finalization, run once when acquisition COMPLETEs.

  * freeze the genuine ground-truth set (immutable timestamped copy);
  * Phase 5: Bemis-Murcko SCAFFOLD split into train/validation/test with NO scaffold leakage
    (final test = genuine labels only);
  * Phase 7: held-out target-domain benchmark on the test split, stratified by scaffold novelty
    (max ECFP Tanimoto to train);
  * write the final report and a FINALIZED sentinel;
  * PAUSE: do NOT annotate the 1.95M pool -- production stays gated on human confirmation.

--preview runs the whole pipeline into a preview area WITHOUT freezing or writing FINALIZED,
so it can be validated on partial data before real completion.
"""
import argparse, sys, types, pathlib, json, shutil, datetime, hashlib
import pandas as pd
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold
from rdkit.Chem import AllChem, DataStructs

ROOT = pathlib.Path("/data01/cris/projects/DAG")
PILOT = ROOT / "data/v4_classyfire_groundtruth/resources_extracted/pilot_v3/pilot"
OBO = ROOT / "data/external/chemont/ChemOnt_2_1.obo"
GT = ROOT / "data/v4_classyfire_groundtruth/classyfire_ground_truth.parquet"
DATADIR = ROOT / "data/v4_classyfire_groundtruth"
DBV4 = ROOT / "database/v4/dag_v4.db"


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
                if cur and cur["id"]: add(cur)
                cur = {"id": None, "name": None, "is_a": []}
            elif line.startswith("[") and line != "[Term]":
                if cur and cur["id"]: add(cur)
                cur = None
            elif cur is not None:
                if line.startswith("id:"): cur["id"] = line.split(":", 1)[1].strip()
                elif line.startswith("name:"): cur["name"] = line.split(":", 1)[1].strip()
                elif line.startswith("is_a:"):
                    cur["is_a"].append(line.split(":", 1)[1].strip().split("!")[0].strip())
        if cur and cur["id"]: add(cur)
        return g
    m = types.ModuleType("obonet"); m.read_obo = read_obo
    return m


def scaffold_of(smi):
    try:
        m = Chem.MolFromSmiles(smi)
        if m is None:
            return None
        s = MurckoScaffold.GetScaffoldForMol(m)
        sm = Chem.MolToSmiles(s)
        return sm if sm else "ACYCLIC"
    except Exception:
        return None


def scaffold_split(df, seed=20260722, test_frac=0.15, dev_frac=0.15):
    df = df.copy()
    df["scaffold"] = df["standardized_smiles"].map(scaffold_of)
    df["scaffold"] = df["scaffold"].fillna("UNPARSED")
    groups = {}
    for sc, sub in df.groupby("scaffold"):
        groups[sc] = list(sub.index)
    # deterministic order: larger scaffolds first, ties by stable hash
    order = sorted(groups, key=lambda s: (-len(groups[s]),
                   hashlib.md5((str(seed) + s).encode()).hexdigest()))
    n = len(df)
    quota = {"test": test_frac * n, "validation": dev_frac * n, "train": n}
    have = {"test": 0, "validation": 0, "train": 0}
    assign = {}
    for sc in order:
        # fill test then validation up to quota, remainder to train
        if have["test"] < quota["test"]:
            split = "test"
        elif have["validation"] < quota["validation"]:
            split = "validation"
        else:
            split = "train"
        assign[sc] = split
        have[split] += len(groups[sc])
    df["split"] = df["scaffold"].map(assign)
    return df


def load_mapper():
    sys.modules["obonet"] = obonet_shim()
    sys.path.insert(0, str(PILOT))
    from chemont_rules import classify_smiles
    from lineage import load_obo, build_name_index, expand
    G = load_obo(str(OBO)); idx = build_name_index(G)
    return classify_smiles, G, idx, expand


def benchmark(df, classify_smiles, G, idx, expand):
    LVLCOLS = ["classyfire_kingdom", "classyfire_superclass", "classyfire_class",
               "classyfire_subclass", "classyfire_terminal_name"]
    rows = []
    for _, r in df.iterrows():
        smi = r["standardized_smiles"]
        if not isinstance(smi, str) or not smi:
            continue
        res = classify_smiles(smi); prim = res["primary"]
        lin = expand(G, idx, prim) if prim else None
        names = [n for _, n in lin] if lin else []
        gt_terminal = r["classyfire_terminal_name"]
        gt_set = {r[c] for c in LVLCOLS if isinstance(r[c], str) and r[c]}
        alln = {h["chemont_name"] for h in res["all"]}
        my_super = names[2] if len(names) > 2 else ""
        my_class = names[3] if len(names) > 3 else ""
        rows.append(dict(
            on_path=bool(prim) and prim in gt_set,
            exact=bool(prim) and prim == gt_terminal,
            any_match=bool(alln & gt_set),
            super_ok=(my_super == r["classyfire_superclass"]) if isinstance(r["classyfire_superclass"], str) and r["classyfire_superclass"] else None,
            class_ok=(my_class == r["classyfire_class"]) if isinstance(r["classyfire_class"], str) and r["classyfire_class"] else None,
        ))
    b = pd.DataFrame(rows); so = b.super_ok.dropna(); co = b.class_ok.dropna()
    return dict(n=int(len(b)), on_path=float(b.on_path.mean()), any_match=float(b.any_match.mean()),
                exact_leaf=float(b.exact.mean()),
                superclass=float(so.mean()) if len(so) else None,
                class_=float(co.mean()) if len(co) else None)


def novelty_strata(train_df, test_df, classify_smiles, G, idx, expand):
    def fps(df):
        out = []
        for _, r in df.iterrows():
            m = Chem.MolFromSmiles(r["standardized_smiles"]) if isinstance(r["standardized_smiles"], str) else None
            out.append(AllChem.GetMorganFingerprintAsBitVect(m, 2, 2048) if m else None)
        return out
    trfps = [f for f in fps(train_df) if f is not None]
    strata = {"<0.3": [], "0.3-0.5": [], "0.5-0.7": [], ">=0.7": []}
    for idx_, r in test_df.iterrows():
        m = Chem.MolFromSmiles(r["standardized_smiles"]) if isinstance(r["standardized_smiles"], str) else None
        if m is None or not trfps:
            continue
        fp = AllChem.GetMorganFingerprintAsBitVect(m, 2, 2048)
        sim = max(DataStructs.BulkTanimotoSimilarity(fp, trfps))
        b = "<0.3" if sim < 0.3 else "0.3-0.5" if sim < 0.5 else "0.5-0.7" if sim < 0.7 else ">=0.7"
        strata[b].append(idx_)
    res = {}
    for b, idxs in strata.items():
        if idxs:
            res[b] = benchmark(test_df.loc[idxs], classify_smiles, G, idx, expand)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()
    preview = args.preview
    tag = "preview" if preview else "final"
    outdir = ROOT / ("results/v4_chemont_mapper/finalize_preview" if preview else "data/v4_classyfire_groundtruth")
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(GT)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    if not preview:
        frozen = DATADIR / f"classyfire_ground_truth_frozen_{ts}.parquet"
        shutil.copy2(GT, frozen)

    split_df = scaffold_split(df)
    counts = split_df.split.value_counts().to_dict()
    n_scaf = split_df.scaffold.nunique()
    # leakage check
    leak = 0
    for sc, sub in split_df.groupby("scaffold"):
        if sub.split.nunique() > 1:
            leak += 1

    for sp in ["train", "validation", "test"]:
        sub = split_df[split_df.split == sp].drop(columns=["scaffold", "split"])
        sub.to_parquet(outdir / f"{sp}.parquet", index=False)

    classify_smiles, G, idx, expand = load_mapper()
    test_df = split_df[split_df.split == "test"]
    train_df = split_df[split_df.split == "train"]
    held_out = benchmark(test_df, classify_smiles, G, idx, expand)
    dev = benchmark(split_df[split_df.split == "validation"], classify_smiles, G, idx, expand)
    strata = novelty_strata(train_df, test_df, classify_smiles, G, idx, expand)

    report = {
        "tag": tag, "generated": ts, "n_ground_truth": int(len(df)),
        "n_scaffolds": int(n_scaf), "split_counts": counts, "scaffold_leakage": int(leak),
        "held_out_test": held_out, "validation": dev, "novelty_strata": strata,
        "targets": {"superclass": 0.90, "class": 0.75, "exact_leaf": 0.60},
    }
    outjson = ROOT / f"reports/v4/finalization_{tag}.json"
    json.dump(report, open(outjson, "w"), indent=2)

    md = f"""# Phase 5 + Phase 7 finalization ({tag})

_Generated {ts}. {'PREVIEW on partial data — not a completion.' if preview else 'FINAL: acquisition complete.'}_

## Frozen ground truth
- genuine labels: **{len(df)}**, distinct Bemis-Murcko scaffolds: **{n_scaf}**
{'' if preview else '- frozen copy: `classyfire_ground_truth_frozen_'+ts+'.parquet`'}

## Phase 5 — scaffold split (no scaffold leakage)
- train / validation / test = {counts.get('train',0)} / {counts.get('validation',0)} / {counts.get('test',0)}
- scaffolds spanning >1 split (leakage): **{leak}** (must be 0)
- files: `{outdir}/train.parquet`, `validation.parquet`, `test.parquet`

## Phase 7 — held-out target-domain benchmark (TEST split, genuine labels only)
| metric | held-out test | validation | prod target |
|---|---:|---:|---:|
| n | {held_out['n']} | {dev['n']} | — |
| superclass | {held_out['superclass']} | {dev['superclass']} | 0.90 |
| class | {held_out['class_']} | {dev['class_']} | 0.75 |
| exact-leaf | {held_out['exact_leaf']} | {dev['exact_leaf']} | 0.60 |
| on_path | {held_out['on_path']} | {dev['on_path']} | — |
| any_match | {held_out['any_match']} | {dev['any_match']} | — |

### Novelty stratification (max ECFP Tanimoto of test mol to train)
{chr(10).join(f"- **{k}**: n={v['n']} superclass={v['superclass']} class={v['class_']} exact={v['exact_leaf']}" for k,v in strata.items())}

## Verdict & PAUSE
The mapper is compared to the provisional targets (superclass ≥0.90, class ≥0.75, exact ≥0.60).
**Production annotation of the ~1.95M pool is NOT performed.** It remains gated on human
confirmation per the task. Do not scale until a maintainer reviews these held-out numbers.
"""
    (ROOT / f"reports/v4/finalization_report_{tag}.md").write_text(md)

    if not preview:
        # persist splits into dag_v4.db and write FINALIZED + audit
        import sqlite3
        con = sqlite3.connect(DBV4, timeout=120)
        split_df[["inchikey", "scaffold", "split"]].to_sql(
            "benchmark_splits", con, if_exists="replace", index=False)
        con.commit(); con.close()
        (ROOT / "reports/v4/FINALIZED").write_text(json.dumps(report, indent=2))
        with open(ROOT / "logs/v4/agent_actions.log", "a") as fh:
            fh.write(f"[{ts}] FINALIZED: frozen GT n={len(df)}, scaffold split "
                     f"{counts}, held-out test superclass={held_out['superclass']} "
                     f"class={held_out['class_']} exact={held_out['exact_leaf']}. "
                     f"Production annotation PAUSED pending human confirmation.\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
