# Full-dataset quality control

Automated full validation status: **PASS**.

The build consumed exactly 4,572,128 source rows. The accounting identity passes:

`4,572,128 = 94 malformed + 5,150 chemistry failures + 2,610,342 duplicates + 1,956,542 unique compounds`.

Independent post-build checks established:

- SQLite `PRAGMA integrity_check` returned `ok`.
- SQLite `PRAGMA foreign_key_check` returned zero violations.
- `compounds` and `taxonomy_paths` each contain 1,956,542 rows.
- `source_records` contains all 4,572,128 raw input rows.
- `failed_compounds` contains 5,244 rows and `duplicate_mapping` contains 2,610,342 rows.
- SQLite and exported TSVs both contain 16,102,215 memberships.
- GraphML and JSON each load as 29 nodes and 30 edges.
- The GraphML graph is directed and acyclic.
- All class edges and compound memberships resolve to existing foreign keys.
- Ruleset `dag-rdkit-rules-1.1.1` and RDKit 2026.03.2 are recorded in database provenance and graph metadata.

The pipeline ran with 64 ordered workers and a single transactional writer. The full build, exact ZINC-ID join, graph serialization, and database validation completed in 1,081.159 seconds. Input order was retained, so the first successful standardized occurrence remains the deterministic duplicate representative.

One source-adapter defect was detected in the first attempt: `bidebb` prefixes each exported SMILES with literal `>>>`. That attempt was stopped and all partial artifacts were preserved. The adapter now strips only that transport marker for parsing while retaining the exact supplied string as `original_smiles`; a 100-record regression passed before restart. No taxonomy SMARTS or standardization rule changed.

The machine-readable validation is `results/full/full_validation.json`. Its warnings correctly distinguish unresolved organic assignments from authoritative ontology classification and state that missing ZINC IDs were not fabricated.
