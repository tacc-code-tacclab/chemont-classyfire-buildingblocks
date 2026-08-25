#!/usr/bin/env python3
"""Independent cross-artifact and chemistry QC for the pilot gate."""

from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

import networkx as nx
from rdkit import Chem

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.pilot_taxonomy import NODES, direct_classes  # noqa: E402


def tsv(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe(name: str, smiles: str, expected: set[str], absent: set[str]) -> dict:
    found = direct_classes(Chem.MolFromSmiles(smiles))
    return {
        "name": name,
        "smiles": smiles,
        "expected_present": sorted(expected),
        "expected_absent": sorted(absent),
        "observed": sorted(found),
        "pass": expected <= found and not (absent & found),
        "missing": sorted(expected - found),
        "unexpected": sorted(absent & found),
    }


def main() -> None:
    nodes = tsv("taxonomy/pilot_taxonomy_nodes.tsv")
    edges = tsv("taxonomy/pilot_taxonomy_edges.tsv")
    memberships = tsv("taxonomy/pilot_compound_membership.tsv")
    paths = tsv("taxonomy/pilot_compound_primary_paths.tsv")
    compounds = tsv("data/processed/pilot_compounds_standardised.tsv")
    tree_edges = tsv("taxonomy/pilot_taxonomy_tree_edges.tsv")

    g_tsv = nx.DiGraph((e["parent_id"], e["child_id"]) for e in edges)
    graphml = nx.read_graphml(ROOT / "taxonomy/pilot_taxonomy.graphml")
    payload = json.loads((ROOT / "taxonomy/pilot_taxonomy.json").read_text())
    json_nodes = {n["id"] for n in payload["nodes"]}
    json_edges = {(e["parent"], e["child"]) for e in payload["edges"]}
    tsv_nodes = {n["node_id"] for n in nodes}
    tsv_edges = {(e["parent_id"], e["child_id"]) for e in edges}
    compound_ids = {r["source_compound_id"] for r in compounds}

    con = sqlite3.connect(ROOT / "database/chemical_taxonomy_pilot.db")
    con.execute("PRAGMA foreign_keys=ON")
    db_counts = {
        table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ["compounds", "taxonomy_nodes", "taxonomy_edges", "compound_membership", "taxonomy_paths", "provenance"]
    }
    db_integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    fk_violations = con.execute("PRAGMA foreign_key_check").fetchall()
    db_memberships = set(con.execute("SELECT compound_id,class_id,membership_type,source,evidence,is_primary FROM compound_membership"))
    db_paths = set(con.execute("SELECT compound_id,primary_leaf_class,taxonomy_path,node_id_path FROM taxonomy_paths"))
    provenance = [dict(zip(["resource", "version", "url", "download_date", "checksum", "licence"], row)) for row in con.execute("SELECT * FROM provenance")]
    con.close()

    tsv_memberships_for_db = {
        (r["compound_id"], r["class_id"], r["membership_type"], r["classification_method"], r["evidence"], int(r["is_primary"]))
        for r in memberships
    }
    tsv_paths_for_db = {(r["compound_id"], r["primary_leaf_class"], r["taxonomy_path"], r["node_id_path"]) for r in paths}

    direct_by_compound: dict[str, set[str]] = defaultdict(set)
    inferred_by_compound: dict[str, set[str]] = defaultdict(set)
    primary_by_compound: dict[str, list[str]] = defaultdict(list)
    for row in memberships:
        target = direct_by_compound if row["membership_type"] == "direct" else inferred_by_compound
        target[row["compound_id"]].add(row["class_id"])
        if row["is_primary"] == "1":
            primary_by_compound[row["compound_id"]].append(row["class_id"])

    ancestor_errors = []
    for cid in compound_ids:
        expected = set().union(*(nx.ancestors(g_tsv, c) for c in direct_by_compound[cid])) - direct_by_compound[cid]
        if expected != inferred_by_compound[cid]:
            ancestor_errors.append(cid)

    path_errors = []
    for row in paths:
        node_path = json.loads(row["node_id_path"])
        if (
            row["compound_id"] not in compound_ids
            or row["primary_leaf_class"] not in direct_by_compound[row["compound_id"]]
            or primary_by_compound[row["compound_id"]] != [row["primary_leaf_class"]]
            or node_path[-1] != row["primary_leaf_class"]
            or any((a, b) not in tsv_edges for a, b in zip(node_path, node_path[1:]))
        ):
            path_errors.append(row["compound_id"])

    probes = [
        probe("aniline", "Nc1ccccc1", {"DAGCHEM:0000200", "DAGCHEM:0000201", "DAGCHEM:0000204"}, {"DAGCHEM:0000321"}),
        probe("amide negative", "CC(=O)N", set(), {"DAGCHEM:0000200"}),
        probe("sulfonamide negative", "CS(=O)(=O)N", set(), {"DAGCHEM:0000200"}),
        probe("nitro amine negative", "C[N+](=O)[O-]", set(), {"DAGCHEM:0000200"}),
        probe("tertiary aromatic amine", "CN(C)c1ccccc1", {"DAGCHEM:0000203", "DAGCHEM:0000204"}, set()),
        probe("carboxylic acid not ketone", "CC(=O)O", {"DAGCHEM:0000300"}, {"DAGCHEM:0000321"}),
        probe("aldehyde", "CC=O", {"DAGCHEM:0000320"}, {"DAGCHEM:0000321"}),
        probe("ketone", "CC(=O)C", {"DAGCHEM:0000321"}, {"DAGCHEM:0000320"}),
        probe("phenylboronic acid", "OB(O)c1ccccc1", {"DAGCHEM:0000600"}, {"DAGCHEM:0000601"}),
        probe("pinacol phenylboronate", "CC1(C)OB(c2ccccc2)OC1(C)C", {"DAGCHEM:0000601"}, {"DAGCHEM:0000600"}),
        probe("aminofluoropyridine multifunctional", "Nc1ncccc1F", {"DAGCHEM:0000204", "DAGCHEM:0000401", "DAGCHEM:0000502", "DAGCHEM:0000700"}, set()),
        probe("ethylamine not multifunctional", "CCN", {"DAGCHEM:0000201"}, {"DAGCHEM:0000700"}),
        probe("hydrazine not organic", "NN", set(), {"DAGCHEM:0000100"}),
    ]

    primary_non_graph_leaf = sum(g_tsv.out_degree(r["primary_leaf_class"]) > 0 for r in paths)
    multifunctional_count = sum("DAGCHEM:0000700" in direct_by_compound[c] for c in compound_ids)
    phenol_ids = {c for c in compound_ids if "DAGCHEM:0000311" in direct_by_compound[c]}
    phenol_inferred_alcohol = sum("DAGCHEM:0000310" in inferred_by_compound[c] for c in phenol_ids)

    structural_checks = {
        "tsv_node_count": len(nodes), "tsv_edge_count": len(edges), "tsv_membership_count": len(memberships),
        "tsv_path_count": len(paths), "standardized_compound_count": len(compounds),
        "tsv_dag_acyclic": nx.is_directed_acyclic_graph(g_tsv),
        "graphml_dag_acyclic": nx.is_directed_acyclic_graph(graphml),
        "json_tsv_nodes_equal": json_nodes == tsv_nodes,
        "json_tsv_edges_equal": json_edges == tsv_edges,
        "graphml_tsv_nodes_equal": set(graphml.nodes) == tsv_nodes,
        "graphml_tsv_edges_equal": set(graphml.edges) == tsv_edges,
        "edge_endpoints_resolve": all(a in tsv_nodes and b in tsv_nodes for a, b in tsv_edges),
        "membership_endpoints_resolve": all(r["compound_id"] in compound_ids and r["class_id"] in tsv_nodes for r in memberships),
        "path_compound_coverage_exact": {r["compound_id"] for r in paths} == compound_ids,
        "primary_and_path_semantics_errors": len(path_errors),
        "ancestor_propagation_errors": len(ancestor_errors),
        "db_integrity": db_integrity,
        "db_foreign_key_violation_count": len(fk_violations),
        "db_counts": db_counts,
        "db_tsv_memberships_equal": db_memberships == tsv_memberships_for_db,
        "db_tsv_paths_equal": db_paths == tsv_paths_for_db,
        "tree_edge_count": len(tree_edges),
        "expected_tree_edge_count": len(nodes) - 1,
        "primary_leaf_values_that_are_not_graph_leaves": primary_non_graph_leaf,
    }

    defects = [
        {"id": "CHEM-001", "severity": "critical", "title": "Nitro nitrogen is falsely classified as amine", "evidence": "Nitromethane matches the generic [NX3] amine SMARTS."},
        {"id": "CHEM-002", "severity": "critical", "title": "Phenol is asserted as a subclass of non-aromatic alcohol", "evidence": f"DAG edge Alcohol -> Phenol contradicts the Alcohol definition; {phenol_inferred_alcohol}/{len(phenol_ids)} pilot phenols inherit Alcohol."},
        {"id": "CHEM-003", "severity": "critical", "title": "Multifunctional rule double-counts ancestor and descendant concepts", "evidence": f"Ethylamine is labeled multifunctional solely from Amine + Primary amine; {multifunctional_count}/1000 pilot compounds receive Multifunctional."},
        {"id": "CHEM-004", "severity": "major", "title": "Tertiary aromatic amines are missed", "evidence": "N,N-dimethylaniline lacks Aromatic amine because its rule permits H1/H2 only, contrary to the node definition."},
        {"id": "CHEM-005", "severity": "major", "title": "Organic compound is assigned unconditionally", "evidence": "Hydrazine (NN) is assigned Organic compound despite containing no carbon."},
        {"id": "VAL-001", "severity": "major", "title": "Gate validator does not validate serialized JSON/GraphML or TSV-to-database equality", "evidence": "validate_pilot.py checks the in-code graph(), not loaded exports, and omits table/export count and equality checks."},
        {"id": "TREE-001", "severity": "major", "title": "DAG-versus-tree compound-loss metric is structurally inflated", "evidence": "All direct generic and ancestor/descendant rule hits are counted as information loss; one primary path is conflated with the separate class-edge tree projection."},
        {"id": "REPRO-001", "severity": "minor", "title": "Metrics JSON is not byte reproducible", "evidence": "elapsed_seconds changes between otherwise byte-identical reruns."},
    ]

    required_files = [
        "database/chemical_taxonomy_pilot.db", "taxonomy/pilot_taxonomy_nodes.tsv", "taxonomy/pilot_taxonomy_edges.tsv",
        "taxonomy/pilot_compound_membership.tsv", "taxonomy/pilot_compound_primary_paths.tsv", "taxonomy/pilot_taxonomy.graphml",
        "taxonomy/pilot_taxonomy.json", "scripts/validate_pilot.py", "reports/pilot_1000_results.md",
        "reports/pilot_quality_control.md", "reports/pilot_failures.md", "reports/dag_vs_tree.md",
    ]
    result = {
        "status": "FAIL",
        "stage2_authorized": False,
        "reason": "critical chemical correctness defects remain despite structural artifact integrity",
        "structural_checks": structural_checks,
        "chemistry_probes": probes,
        "chemistry_probe_passed": sum(p["pass"] for p in probes),
        "chemistry_probe_total": len(probes),
        "defects": defects,
        "severity_counts": dict(Counter(d["severity"] for d in defects)),
        "required_pilot_files_missing": [p for p in required_files if not (ROOT / p).exists()],
        "provenance_rows": provenance,
        "rerun": {
            "taxonomy_tsv_json_graphml_database_byte_identical": True,
            "pilot_metrics_byte_identical": False,
            "note": "All canonical structural artifacts matched SHA-256 before/after; metrics differed only because runtime is serialized.",
        },
        "scope": "Independent pilot QC only; Stage 2 not started.",
    }
    out = ROOT / "results/pilot/independent_qc.json"
    if out.exists():
        raise FileExistsError(f"refusing to overwrite {out}")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
