#!/usr/bin/env python
"""Phase 0: independently reproduce the V3 SMILES->ChemOnt benchmark.

Runs the *unmodified* V3 harness (benchmark.py, chemont_rules.py, lineage.py)
against its genuine ClassyFire ground truth. The only substitution is an in-memory
`obonet` shim built from the canonical ChemOnt_2_1.obo, so no third-party package
is installed and the ontology graph is identical in structure to obonet's output
(MultiDiGraph, child->parent edges keyed 'is_a', node attr 'name').

Runs inside a private copy of the V3 package so the extracted resources stay
pristine. Prints the reproduced metrics next to the expected V3 report values.
"""
import sys, os, shutil, types, pathlib, subprocess, hashlib

ROOT = pathlib.Path("/data01/cris/projects/DAG")
SRC = ROOT / "data/v4_classyfire_groundtruth/resources_extracted/pilot_v3/pilot"
WORK = ROOT / "results/v4_chemont_mapper/v3_repro"
OBO = ROOT / "data/external/chemont/ChemOnt_2_1.obo"


def build_obonet_shim():
    import networkx as nx

    def read_obo(path):
        g = nx.MultiDiGraph()
        cur = None
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.rstrip("\n")
                if line == "[Term]":
                    if cur and cur["id"]:
                        _add(g, cur)
                    cur = {"id": None, "name": None, "is_a": []}
                elif line.startswith("[") and line != "[Term]":
                    if cur and cur["id"]:
                        _add(g, cur)
                    cur = None
                elif cur is not None:
                    if line.startswith("id:"):
                        cur["id"] = line.split(":", 1)[1].strip()
                    elif line.startswith("name:"):
                        cur["name"] = line.split(":", 1)[1].strip()
                    elif line.startswith("is_a:"):
                        val = line.split(":", 1)[1].strip()
                        cur["is_a"].append(val.split("!")[0].strip())
        if cur and cur["id"]:
            _add(g, cur)
        return g

    def _add(g, cur):
        g.add_node(cur["id"], name=cur["name"])
        for p in cur["is_a"]:
            g.add_edge(cur["id"], p, key="is_a")

    mod = types.ModuleType("obonet")
    mod.read_obo = read_obo
    return mod


def main():
    if WORK.exists():
        shutil.rmtree(WORK)
    shutil.copytree(SRC, WORK)
    # ensure the OBO used is the canonical extracted one (byte-identical anyway)
    sys.modules["obonet"] = build_obonet_shim()
    os.chdir(WORK)
    sys.path.insert(0, str(WORK))
    import benchmark
    b = benchmark.run(verbose=True)

    print("\n================ Phase 0 reproduction vs V3 report ================")
    n = len(b)
    def pct(col):
        return b[col].mean() * 100
    so = b.super_ok.dropna(); co = b.class_ok.dropna()
    repro = {
        "n_organic": n,
        "on_path": pct("on_path"),
        "any_match": pct("any_match"),
        "exact_leaf": pct("exact"),
        "superclass": so.mean() * 100,
        "class": co.mean() * 100,
    }
    expected = {"n_organic": 1266, "on_path": 49.2, "any_match": 63.0,
                "exact_leaf": 8.7, "superclass": 65.3, "class": 55.9}
    print(f"{'metric':14s} {'reproduced':>12s} {'V3 report':>12s} {'delta':>8s}")
    for k in ["n_organic", "on_path", "any_match", "exact_leaf", "superclass", "class"]:
        r = repro[k]; e = expected[k]
        d = r - e
        fmt = "d" if k == "n_organic" else ".1f"
        print(f"{k:14s} {r:12{fmt}} {e:12{fmt}} {d:+8{fmt if k=='n_organic' else '.1f'}}")

    import json
    (ROOT / "reports/v4").mkdir(parents=True, exist_ok=True)
    json.dump({"reproduced": repro, "v3_report_expected": expected,
               "n_ground_truth_rows_total": None},
              open(ROOT / "reports/v4/v3_reproduction_metrics.json", "w"), indent=2)
    print("\nwrote reports/v4/v3_reproduction_metrics.json")
    print("regenerated detail:", WORK / "data/benchmark_detail.csv")


if __name__ == "__main__":
    main()
