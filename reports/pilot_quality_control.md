# Pilot quality control

Automated validation status for ruleset `dag-rdkit-rules-1.1.1`: **PASS with two documented warnings**.

| Check | Result |
|---|---:|
| Standardized input compounds | 1,000 |
| Database compounds | 1,000 |
| Taxonomy nodes / edges | 29 / 30 |
| Root / leaf nodes | 1 / 20 |
| Maximum / median primary depth | 4 / 3 |
| Nodes with multiple parents | 2 |
| Weakly connected components | 1 |
| Directed cycles | 0 |
| Database integrity | `ok` |
| Foreign-key violations | 0 |
| Primary-path coverage | 1,000 / 1,000 |
| Direct / inferred memberships | 7,309 / 1,000 |
| Specifically classified compounds | 974 |
| Partially classified / unresolved organic | 26 |

All 13 independent chemistry probes and 15 regression test functions passed by direct Python execution. In addition to DAG, boron, multifunctional, and carbonyl controls, regressions cover nitro nitrogen exclusion, tertiary aromatic amines, amide/sulfonamide negatives, ancestor/descendant-safe multifunctionality, carbon-gated organic assignment, corrected phenol parentage, and exclusion of amidine/guanidine-like nitrogens from amine subtypes. Acetamidine and guanidine negative controls and an ethylamine positive control pass in `results/pilot/amidine_guanidine_regression.json`. `pytest` itself was unavailable, so no package was installed; the assertion functions were invoked directly.

The two validation warnings are: the pilot contains no empirical boron structure, and 26 compounds retain only generic coverage with an explicit unresolved-organic membership. Both boronic classes are implemented and synthetically tested, but empirical boron-domain validation cannot be claimed.

Reproducibility controls include stable IDs, pinned ruleset version, fixed sort order, fixed primary-path tie-breaking, input/rule checksums, and deterministic serialization. Runtime was removed from canonical metrics. A second complete 1.1.1 build produced identical SHA-256 hashes for TSV, JSON, GraphML, SQLite, and metrics; evidence is under `results/pilot/reproducibility_ruleset_1_1_1/`. The validator loads and cross-compares TSV, JSON, GraphML, SQLite, paths, memberships, counts, ruleset versions, graph cycles, and foreign keys.
