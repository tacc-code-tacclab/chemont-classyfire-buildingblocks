# Independent pilot quality control

## Gate decision

**FAIL — Stage 2 is prohibited.**

The pilot artifacts are structurally consistent and reproducible, but critical chemical-correctness defects remain in the taxonomy rules and hierarchy. The existing automated `pilot_validation.json` PASS is therefore not sufficient to satisfy the scientific validation gate.

The authoritative machine-readable independent result is `results/pilot/independent_qc.json`.

## Structural and database checks

The following checks passed independently:

- 1,000 standardized compounds are represented by 1,000 database compound rows and 1,000 primary paths.
- TSV and database counts agree: 29 taxonomy nodes, 31 taxonomy edges, and 8,392 compound memberships.
- SQLite `PRAGMA integrity_check` returns `ok` and `PRAGMA foreign_key_check` returns zero violations.
- Database memberships and paths exactly equal their TSV representations.
- TSV, JSON, and GraphML node and edge sets agree exactly.
- Both TSV- and GraphML-loaded graphs are acyclic.
- All edge and membership endpoints resolve.
- Direct-to-inferred ancestor propagation has zero discrepancies.
- Each compound has exactly one consistent primary assignment and a valid stored edge path.
- The 28-edge tree projection has the expected `nodes - 1` edge count.
- All required pilot files checked by the independent script are present.
- A taxonomy-pipeline rerun reproduced the taxonomy TSVs, JSON, GraphML, and SQLite database byte-for-byte.
- A standardization rerun reproduced all processed outputs byte-for-byte; its six unit tests passed.

The metrics JSON is not byte-identical across taxonomy reruns because it serializes nondeterministic wall-clock runtime. This is minor and is not the reason for the FAIL.

## Critical defects

### CHEM-001 — Nitro nitrogen is falsely classified as amine

The generic amine SMARTS matches nitro nitrogen. Nitromethane, `C[N+](=O)[O-]`, receives direct `Amine` membership. This is a chemically incorrect positive and shows that the current rule is insufficiently constrained.

### CHEM-002 — Phenol is a child of “non-aromatic alcohol”

The DAG asserts `Alcohol -> Phenol`, while the Alcohol node is explicitly defined as containing a **non-aromatic** hydroxyl group. All 113 directly assigned pilot phenols consequently inherit the contradictory Alcohol membership. This is an ontology-level error, not merely an edge-case SMARTS issue.

### CHEM-003 — Multifunctional classification double-counts hierarchy-related concepts

The multifunctional rule counts simultaneous ancestor/descendant direct matches as distinct functions. Ethylamine is labeled multifunctional solely because it matches both `Amine` and `Primary amine`. The pilot assigns `Multifunctional compound` to 729 of 1,000 structures, so this error materially affects reported membership and DAG-versus-tree conclusions.

## Major defects

### CHEM-004 — Tertiary aromatic amines are missed

The Aromatic amine rule permits only nitrogens with one or two hydrogens. N,N-dimethylaniline therefore lacks Aromatic amine membership even though its amine nitrogen is directly bonded to an aromatic atom and satisfies the project node definition.

### CHEM-005 — Organic compound is unconditional

Every parsed molecule starts with direct Organic compound membership. Hydrazine, `NN`, is therefore classified as organic despite containing no carbon. The root assignment needs an explicit chemical predicate or an input-domain invariant enforced by validation.

### VAL-001 — The gate validator does not validate serialized artifacts

`scripts/validate_pilot.py` checks the graph reconstructed from Python constants rather than loading the exported TSV, JSON, and GraphML graphs. It also omits complete TSV-to-database equality checks. Corruption or divergence in a serialized deliverable can therefore escape the official gate even though the independent checks currently show that the artifacts agree.

### TREE-001 — Tree-loss metrics are inflated and conflate projections

The reported 100% compound-loss statistic counts generic memberships and ancestor/descendant direct rule hits as separate meaningful information losses. It also conflates loss from selecting one primary compound path with loss from projecting the class DAG to a single-parent class tree. The current number does not isolate chemically independent memberships lost by the class-tree projection.

## Additional semantic observation

The field named `primary_leaf_class` contains a graph node with children for 195 compounds. Stored paths and primary flags are internally consistent, but the field does not always identify a taxonomy leaf in the exported DAG. The intended meaning should be clarified or selection restricted to leaves.

## Chemistry challenge set

Nine of thirteen independent positive/negative probes passed. The failures were the nitro false-positive, tertiary aromatic-amine false-negative, ethylamine multifunctional false-positive, and unconditional organic assignment to hydrazine. Existing tests for boronic acid, boronate ester, aminofluoropyridine multiple membership, and acid-versus-ketone discrimination passed, but they did not cover the defects above.

Representative pilot records from primary amines, carboxylic acids, phenols, pyridines, organofluorine, sulfur, phosphorus, multifunctional, and unresolved classes were inspected. The structural outputs are traceable, but examples involving guanidine/amidine-like nitrogens further demonstrate that broad amine matching requires more chemical review.

## Required remediation before a new gate run

1. Correct and expand the amine rules with explicit positive and negative chemistry tests.
2. Resolve the Phenol/Alcohol ontology contradiction.
3. Define multifunctionality using chemically independent class dimensions rather than raw direct-membership count.
4. Make Organic compound conditional or enforce and test a carbon-containing input invariant.
5. Extend `validate_pilot.py` to load and compare every serialized graph/table/database artifact.
6. Separate class-tree edge loss from one-primary-path compound-membership loss and recompute meaningful-information statistics.
7. Rebuild all dependent TSV, graph, database, metric, and report outputs; rerun both automated and independent validation.

Until those corrections are implemented and a fresh independent QC returns PASS, the strict Stage 1 validation requirements are not met and the complete ZINC building-block dataset must not be downloaded or processed.
