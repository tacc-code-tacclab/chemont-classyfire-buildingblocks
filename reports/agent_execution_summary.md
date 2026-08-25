# Agent execution summary

## Outcome

The project completed both gated stages without modifying `prompt.md`, deleting files, or writing outside `/data01/cris/projects/DAG`. The pilot initially failed two independent scientific reviews, was corrected through rulesets 1.1.0 and 1.1.1, and passed the third independent gate before Stage 2 began. The full ZINC run and a separate full-output audit both pass.

## Data and taxonomy results

- Pilot: 1,000 official ZINC supplier-building-block structures; 1,000 standardized, zero failures/duplicates; 974 specifically classified and 26 generic-only unresolved under `dag-rdkit-rules-1.1.1`.
- Full accessible ZINC source exports: 4,572,128 supplier rows from 29 explicit building-block catalogs; 94 malformed rows, 5,150 chemistry/identifier failures, 2,610,342 standardized duplicates, and 1,956,542 final unique structures.
- Full specific-class coverage: 1,907,866 / 1,956,542 = 97.5121%; 48,676 are generic-only unresolved.
- Full taxonomy: 29 class nodes, 30 subclass edges, two multi-parent nodes, one connected component, zero cycles, and 16,102,215 compound-membership rows.
- Identifier provenance: 323,576 unique structures map to official ZINC IDs by exact catalog/supplier/InChIKey evidence; 1,632,966 retain stable `ZINCSRC` source IDs. No ZINC IDs were fabricated.
- Databases: pilot and full SQLite integrity checks pass with zero foreign-key violations.

## Major decisions

SynFlowNet is methodological context only because its Enamine building-block file and precomputed masks are absent. ChemOnt/ClassyFire is retained as a structural benchmark but not a production dependency because its classifier is remote/opaque, the 30-molecule test encountered HTTP 429 responses, and redistribution/commercial terms require caution. ChEBI 253 is used conceptually for exact-identity validation/enrichment but cannot classify arbitrary absent molecules. DrugTax is excluded from canonical use because direct tests demonstrated representation-dependent chemical errors.

The canonical production method is a transparent, graph-aware RDKit SMARTS/property ruleset with project-stable class IDs, non-exclusive direct memberships, separately labeled inferred ancestry, an acyclic class DAG, and a derivative primary-path/tree projection. The pilot's missing empirical boron chemistry remains a warning; boronic acid and boronate rules have synthetic positive/negative tests.

## Validation history

The first automated pilot PASS was rejected by independent QC for nitro-to-amine, phenol/alcohol, multifunctionality, tertiary aromatic amine, and unconditional-organic defects plus validator/tree-metric weaknesses. Ruleset 1.1.0 fixed those issues. Independent QC v2 then found amidine/guanidine nitrogens still misclassified as amines. Ruleset 1.1.1 fixed that defect and added regression controls. Independent QC v3 passed 15/15 regression functions, loaded TSV/JSON/GraphML/SQLite consistency, DAG/database checks, report consistency, and byte-reproducibility. Only then was Stage 2 authorized.

Full processing used 64 ordered workers. A source-specific `>>>` transport prefix in `bidebb` was detected during an early run; all partial artifacts were preserved, the adapter was corrected while retaining original text in provenance, and the full run restarted. The completed run took 1,081.159 seconds. Independent full QC verified the raw accounting identity, membership counts, SQLite integrity/FKs, graph-format equality, acyclicity, identifiers, reports, and required deliverables.

## Repositories, resources, software, and licensing

- SynFlowNet: official repository commit `574f1e148f42e0c79877318fa9d84d2552cf5025`.
- DrugTax: official repository commit `e47fe8420344658520880c0a0e49c995edc71caa`.
- ClassyFire API client: commit `b7a194f694f8cef34b15bb8a1ef96583aed37d83`.
- ChemOnt: 2.1; ChEBI: release 253; RDKit: 2026.03.2; NetworkX: 3.6.1; pandas: 2.3.3; DuckDB: 1.5.4.
- No packages were installed.
- ZINC static exports are retained locally; major portions must not be redistributed without written permission. ChemOnt/ClassyFire licensing and insecure HTTP/service constraints are documented. ChEBI is CC BY 4.0.

## Audit and preservation

The persistent chronological audit is `logs/agent_actions.log`. It records commands, URLs, downloads, checksums, clones, versions, decisions, errors, fixes, preserved paths, and stage checkpoints. Superseded or partial files were retained using `.old_<timestamp>` names. The protected `prompt.md` was read but never modified, renamed, or deleted.

## Key entry points

- Pilot standardization: `python scripts/standardize_pilot.py`
- Pilot build: `python scripts/run_pilot_taxonomy.py`
- Pilot gate: `python scripts/validate_pilot.py`
- Full build: `python scripts/run_full_zinc_taxonomy.py`
- Future input preflight: `python scripts/run_taxonomy_pipeline.py --input <tsv> --source enamine --output-prefix enamine`

The future-input CLI is intentionally a read-only schema/provenance preflight; production Enamine processing must use the documented adapter plan and must not fabricate or reuse ZINC identifiers.
