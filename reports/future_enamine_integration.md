# Future Enamine / SynFlowNet input integration

## Status and invariant architecture

The official approximately 200,000-record Enamine/SynFlowNet building-block file is not available in this project. No Enamine structures or identifiers were fabricated, inferred from ZINC, or substituted with ZINC identifiers.

The validated architecture does not require a taxonomy redesign when the file becomes available:

```text
source adapter
  -> RDKit standardization and explicit failures
  -> stereochemistry-aware canonical deduplication
  -> deterministic dag-rdkit-rules-1.1.1 classification
  -> direct and inferred compound memberships
  -> class DAG plus primary tree projection
  -> relational database and graph exports
  -> integrity, cycle, provenance, and coverage validation
```

Only the source adapter and output namespace should change. Ruleset `dag-rdkit-rules-1.1.1`, class IDs, class edges, evidence types, standardization semantics, and validation requirements should remain pinned unless a separately reviewed new version is justified.

## Required input schema

The preferred headered TSV schema is:

| Column | Required | Meaning |
|---|---|---|
| `source_compound_id` | yes | Stable unique Enamine record or catalog identifier; never substitute a ZINC ID |
| `original_smiles` | yes | Original supplied SMILES, preferably isomeric where stereo is known |
| `supplier_code` | recommended | Enamine catalog/order code if distinct from the stable ID |
| `commercial_status` | recommended | Status exactly as supplied, with snapshot date |
| `supplier` | recommended | `Enamine` or source-provided supplier label |
| `source_url` | recommended | Authorized file/catalog provenance, not a fabricated molecule URL |
| `source_version` | recommended | Release/catalog date or file version |

Accepted aliases for preflight include `compound_id`, `source_id`, `id`, or `ID` for the identifier and `isomeric_smiles`, `smiles`, or `SMILES` for structure. Production ingestion should map aliases explicitly to the preferred names and retain the original columns.

Requirements:

1. IDs must be nonempty and unique at the source-record level.
2. A repeated chemical structure may have multiple valid source offers; do not remove those records before provenance capture.
3. Salts, mixtures, invalid structures, and duplicates must flow through the validated standardizer and explicit failure/duplicate tables; never silently discard them.
4. Preserve source stereochemistry. Do not manufacture unspecified stereocenters.
5. Record file checksum, acquisition date, version, license/contract terms, and authorized storage location.

## Safe preflight command

Place the authorized file inside the project, for example:

```text
data/raw/enamine/enamine_building_blocks.tsv
```

Then run the read-only adapter preflight:

```bash
python scripts/run_taxonomy_pipeline.py \
  --input data/raw/enamine/enamine_building_blocks.tsv \
  --source enamine \
  --output-prefix enamine \
  --id-column source_compound_id \
  --smiles-column original_smiles
```

For a fast schema probe without scanning the whole authorized file:

```bash
python scripts/run_taxonomy_pipeline.py \
  --input data/raw/enamine/enamine_building_blocks.tsv \
  --source enamine \
  --output-prefix enamine \
  --max-rows 1000
```

The command prints JSON and performs no writes. `READY_FOR_ADAPTER_IMPLEMENTATION` means the scanned records have usable IDs/SMILES and no missing or duplicate IDs; it is not a classification PASS. RDKit parse failures are reported as records for the later failed-compound table rather than silently rejected.

The lightweight CLI is deliberately non-destructive. The existing pilot builder reads fixed pilot paths and the full-ZINC builder reads the official ZINC source-export layout; neither should be pointed at proprietary Enamine data. Before production execution, implement and review a dataset adapter that parameterizes the input and all output namespaces.

## Planned Enamine output namespace

The adapter should produce new paths without replacing ZINC artifacts:

- `data/processed/enamine_compounds_standardised.tsv`
- `data/processed/enamine_failed_compounds.tsv`
- `data/processed/enamine_duplicate_mapping.tsv`
- `taxonomy/enamine_taxonomy_nodes.tsv`
- `taxonomy/enamine_taxonomy_edges.tsv`
- `taxonomy/enamine_compound_membership.tsv`
- `taxonomy/enamine_compound_primary_paths.tsv`
- `taxonomy/enamine_taxonomy.json`
- `taxonomy/enamine_taxonomy.graphml`
- `database/chemical_taxonomy_enamine.db`
- `results/enamine/enamine_metrics.json`
- `results/enamine/enamine_validation.json`

Taxonomy node/edge content should be byte-equivalent to the reviewed ruleset 1.1.1 graph. Dataset-specific files differ only in compound instances, memberships, primary paths, provenance, failures, duplicates, and metrics.

## Production execution gate

Do not execute the Enamine production run until all of the following are true:

1. The file was received through an authorized channel and its license/contract permits local processing.
2. Storage, backups, logs, and derived-output redistribution rules are documented.
3. Input checksum and record count are recorded before transformation.
4. The adapter has tests for column mapping, duplicate source IDs, missing SMILES, malformed rows, salts, stereo, and identifier retention.
5. Every planned target is absent or its previous version is preserved as `.old_<YYYYMMDD_HHMMSS>`.
6. A 30–50 molecule Enamine smoke test passes standardization, classification, DAG, and database integrity checks.
7. No proprietary structure is sent to ClassyFire, PubChem, or another remote API without explicit authorization and a secure transport/data-processing agreement.
8. Ruleset version remains exactly `dag-rdkit-rules-1.1.1`, or a new version has its own reviewed regression and reproducibility gate.

After adapter implementation, the intended production interface remains:

```bash
python scripts/run_taxonomy_pipeline.py \
  --input data/raw/enamine/enamine_building_blocks.tsv \
  --source enamine \
  --output-prefix enamine
```

At that point the CLI must be extended behind an explicit execution flag or subcommand, retain read-only preflight as the default, refuse overwrites, and write all outputs atomically into the Enamine namespace. Until that reviewed extension exists, the command is preflight-only.

## Validation parity with the ZINC pipeline

The Enamine run must report:

- raw source records, format failures, chemistry failures, standardized records, duplicates, and unique representatives;
- classified, partially classified/unresolved, and unclassified counts;
- direct and inferred memberships and single/multiple-membership counts;
- taxonomy node/edge/root/leaf counts, depths, multi-parent nodes, components, and cycles;
- SQLite integrity and foreign-key checks;
- exact correspondence among TSV, JSON, GraphML, and database nodes/edges/memberships/paths;
- ruleset and RDKit versions plus code/input/output checksums;
- deterministic rerun hashes on an isolated copy.

The classification evidence remains `rdkit_smarts_or_property` for direct assignments and `dag_ancestor_propagation` for inferred ancestors. ChEBI exact matches may be added as separately typed enrichment. ClassyFire-predicted ChEBI terms and similarity-only predictions must never be presented as authoritative ontology assignments.

## Scalability expectation

The full ZINC run processed 4.57 million supplier rows and 1.96 million unique representatives in approximately 18 minutes with 64 workers on this server. An approximately 200,000-record Enamine input is therefore computationally well within the demonstrated scale. The principal risks are input licensing, provenance, identifier/schema mapping, and taxonomy coverage—not CPU throughput or DAG/database size.

## Protected-data and licensing cautions

- Keep the Enamine file and all derived artifacts inside `/data01/cris/projects/DAG` unless its agreement specifies a different authorized system.
- Do not commit, publish, or redistribute proprietary structures, supplier mappings, or substantial derived catalogs without permission.
- Do not confuse historical ZINC supplier listings with the official Enamine/SynFlowNet dataset.
- Do not reuse ZINC IDs for Enamine records.
- `prompt.md` remains protected and must never be modified, renamed, overwritten, or deleted.
- Continue appending commands, files, errors, decisions, checksums, and checkpoints to `logs/agent_actions.log`.

