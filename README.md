# Chemical taxonomy DAG for commercial building blocks

This project builds a reproducible chemical-class DAG, compound-to-class mappings, graph exports, and SQLite databases for commercial synthetic building blocks. It covers a validated 1,000-compound ZINC pilot and the complete publicly accessible static ZINC building-block source exports acquired for this study. It does not implement sphere embeddings, SphereFlowNet, SynFlowNet training, or GFlowNet changes.

## Current deliverables

- Pilot database: `database/chemical_taxonomy_pilot.db`
- Full ZINC database: `database/chemical_taxonomy_zinc.db`
- Pilot exports: `taxonomy/pilot_*`
- Full exports: `taxonomy/taxonomy_nodes.tsv`, `taxonomy/taxonomy_edges.tsv`, `taxonomy/compound_membership.tsv`, `taxonomy/compound_primary_paths.tsv`, `taxonomy/taxonomy.{json,graphml}`
- Pilot gate: `results/pilot/pilot_validation.json`
- Full validation: `results/full/full_validation.json`
- Scientific and provenance reports: `reports/`
- Persistent execution audit: `logs/agent_actions.log`

The canonical classifier is the transparent local RDKit ruleset **`dag-rdkit-rules-1.1.1`**, defined in `src/pilot_taxonomy.py`. Its `DAGCHEM` assignments are deterministic project rules, not authoritative ChemOnt or ChEBI assertions. ChemOnt/ClassyFire, ChEBI, and DrugTax were experimentally evaluated; see `reports/resource_test_results.md` and `reports/taxonomy_strategy.md`.

## Environment

The completed run used Linux, Python 3.12.13, RDKit 2026.03.2, NetworkX 3.6.1, pandas 2.3.3, requests 2.33.1, NumPy 2.4.3, and SQLite 3.53.1. `environment.yml` records the direct project packages actually present; transitive packages are resolved by Conda/Pip and are not falsely pinned as direct dependencies.

Create or activate the environment:

```bash
conda env create -f environment.yml
conda activate ptrag_bcrabl
```

When the named environment already exists, do not recreate it. Confirm the project root before running anything:

```bash
cd /data01/cris/projects/DAG
pwd
python -c "from rdkit import rdBase; import networkx, pandas; print(rdBase.rdkitVersion, networkx.__version__, pandas.__version__)"
```

## Reproducing the pilot

These commands are intended for a clean reproduction workspace or after explicitly preserving every target. Existing project policy forbids deletion and requires an existing target to be renamed to `<name>.old_<YYYYMMDD_HHMMSS>` before replacement.

```bash
python scripts/standardize_pilot.py \
  --input data/pilot/zinc_commercial_building_blocks_1000_raw.tsv \
  --output data/processed/pilot_compounds_standardised.tsv \
  --failed data/processed/failed_compounds.tsv \
  --duplicates data/processed/pilot_duplicate_mapping.tsv \
  --metrics results/pilot/standardisation_metrics.json

python scripts/run_pilot_taxonomy.py
python scripts/build_tree_projection.py
python scripts/validate_pilot.py
```

`standardize_pilot.py` and the pilot builder preserve existing outputs using timestamped `.old_...` names. `validate_pilot.py` writes `results/pilot/pilot_validation.json`; use it only where replacing that validation result has already been safely handled. The validated canonical result is `PASS` under ruleset 1.1.1.

## Reproducing the full ZINC run

Source acquisition is reproducible from the captured official indexes, but ZINC redistribution restrictions apply. On a clean workspace with authorized access:

```bash
python results/resource_tests/zinc/acquire_full_zinc_bb_sources.py
python scripts/run_full_zinc_taxonomy.py --workers 64 --chunksize 64
```

The full builder reads `data/raw/zinc/full_bb_source_20260721/*.src.txt`, applies the same standardizer and **unchanged ruleset 1.1.1**, and writes the full processed TSVs, taxonomy exports, SQLite database, metrics, and validation. It refuses to overwrite its canonical targets. The measured run processed 4,572,128 supplier rows to 1,956,542 unique representatives in about 18 minutes with 64 workers. See `reports/zinc_full_dataset_provenance.md`, `reports/full_taxonomy_statistics.md`, and `reports/full_quality_control.md` for exact counts and limitations.

Do not rerun either canonical pipeline merely to inspect results. Read the existing JSON, TSV, GraphML, or SQLite artifacts instead.

## Input contracts

The pilot standardizer expects a headered TSV containing at least:

- `source_compound_id`: stable, nonempty source record ID;
- `original_smiles`: molecular structure to standardize.

Additional provenance columns are retained when present. The full ZINC reader uses the official source-export contract of whitespace-delimited `SMILES supplier_code` rows and constructs stable `ZINCSRC:<catalog>:<line>` record IDs.

Future datasets should provide one record per source offer with a stable source ID and SMILES. Supplier/catalog identifiers, original source ID, commercial status, source URL/version, and stereochemical representation should be retained rather than synthesized. Duplicate source records remain traceable even when standardized representatives are deduplicated.

The read-only future-input preflight is:

```bash
python scripts/run_taxonomy_pipeline.py \
  --input data/raw/enamine/enamine_building_blocks.tsv \
  --source enamine \
  --output-prefix enamine
```

This command validates schema, identifiers, and RDKit parseability and prints a machine-readable adapter plan. It intentionally does not classify or write outputs because the current production builders have dataset-specific source/output contracts. See `reports/future_enamine_integration.md` before implementing the Enamine adapter.

## Taxonomy and database semantics

- Taxonomy nodes are chemical classes; individual molecules are compound instances.
- `taxonomy_edges` contains typed class-to-class edges. The canonical representation is an acyclic DAG.
- `compound_membership` contains direct deterministic-rule assignments and separately marked inferred ancestor memberships.
- `taxonomy_paths` is a deterministic primary-path projection, not the complete chemical meaning of a multifunctional molecule.
- Reaction compatibility, if added later, must remain separate from `is_a` classification.
- Similarity-only output must never be labeled as authoritative ontology evidence.

The relational schema, keys, indexes, and provenance tables are documented in `reports/database_schema.md`. JSON exports have top-level `nodes` and `edges`; GraphML loads with NetworkX.

## Licensing and protected data

- `prompt.md` is protected and must never be modified, renamed, overwritten, or deleted.
- ZINC permits sharing search/screen results but restricts redistribution of major portions without written permission. Raw and full derived bulk data are retained locally for research.
- The ClassyFire homepage requires permission for commercial use or redistribution of its data; public accessibility is not an unrestricted license.
- ChEBI release 253 is distributed under CC BY 4.0 and requires attribution.
- DrugTax source is GPL-3.0. Its test outputs are non-authoritative and it is not part of the canonical classifier.
- The official Enamine/SynFlowNet catalog is not present. Do not fabricate it, substitute ZINC IDs, or upload proprietary structures to remote services without authorization and a secure mechanism.

All work products, downloads, temporary files, and logs must stay under `/data01/cris/projects/DAG`. Never delete files. Preserve prior versions and append every material action to `logs/agent_actions.log`.

## Key reports

- `reports/taxonomy_strategy.md`: evidence-based architecture decision
- `reports/pilot_quality_control.md`: pilot validation details
- `reports/dag_vs_tree.md`: information lost by the tree projection
- `reports/full_limitations.md`: full-run scientific and source limitations
- `reports/future_enamine_integration.md`: safe future input replacement workflow

