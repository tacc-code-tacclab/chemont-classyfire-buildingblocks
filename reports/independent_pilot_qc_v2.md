# Independent pilot quality control — ruleset 1.1.0

## Gate decision

**FAIL — Stage 2 is not authorized.**

Ruleset `dag-rdkit-rules-1.1.0` successfully fixes all five chemical defects identified in the first independent review, and the structural pipeline now passes the expanded artifact and reproducibility checks. However, one bounded adversarial test found a remaining major amine false-positive. Under the stated gate rule—PASS only if no critical or major defect remains—the pilot cannot yet pass.

The machine-readable decision is `results/pilot/independent_qc_v2.json`.

## Verified remediation

All thirteen original chemistry probes pass. Specifically:

- nitromethane is no longer classified as an amine;
- Phenol is no longer a subclass of the explicitly non-aromatic Alcohol class;
- ethylamine is no longer labeled multifunctional merely from Amine and Primary amine ancestry;
- N,N-dimethylaniline receives both Tertiary amine and Aromatic amine;
- hydrazine is not assigned Organic compound;
- amide and sulfonamide negatives, aniline, aldehyde/ketone separation, acid/ketone separation, boronic acid, boronate ester, and multifunctional aminofluoropyridine probes pass.

The revised multifunctional logic uses structural families rather than raw ancestor/descendant membership count. The pilot unresolved count drops from 65 to 25.

## Remaining major defect

### CHEM-V2-001 — Amidine nitrogen is classified as primary amine

The bounded adversarial molecule acetamidine, `CC(=N)N`, receives both `DAGCHEM:0000200` (Amine) and `DAGCHEM:0000201` (Primary amine). Amidines are a distinct resonance-stabilized functional class, not primary amines. The SMARTS now excludes nitro, amide, and sulfonamide nitrogens but still lacks amidine/guanidine exclusions.

This is directly relevant to the pilot: guanidine/amidine-like commercial building blocks were already observed during representative review. The defect is therefore major rather than a purely hypothetical scope extension.

No additional probe expansion was performed after this bounded finding.

## Structural, database, and reproducibility checks

The remediated structural pipeline passes:

- 1,000 compounds, 29 nodes, 30 edges, 8,347 memberships, and 1,000 paths;
- SQLite integrity `ok` and zero foreign-key violations;
- database table counts equal the input/TSV counts;
- SQLite nodes, edges, memberships, and paths agree with serialized outputs;
- TSV, JSON, and GraphML node/edge sets agree;
- loaded TSV and GraphML graphs are acyclic;
- ruleset version 1.1.0 agrees across code, TSV, JSON, and database provenance;
- the validator now loads serialized artifacts instead of checking only the in-code graph;
- thirteen taxonomy tests and six standardization tests pass;
- a full taxonomy rebuild is byte-identical across TSV, JSON, GraphML, SQLite, and metrics artifacts.

The previous nondeterministic `elapsed_seconds` field has been removed from canonical metrics.

## Corrected DAG-versus-tree semantics

The revised analysis separates two different losses:

- class-DAG projection: 30 DAG edges become 28 tree edges, so two multi-parent class edges are lost;
- hypothetical one-primary-membership projection: among 2,059 maximally specific meaningful direct memberships, 653 compounds have multiple meaningful memberships and 1,128 memberships would be omitted.

Generic memberships and ancestor/descendant duplicates are no longer counted as independent meaningful losses, and the report explicitly states that the canonical DAG retains all memberships. This resolves the earlier tree-metric defect.

## Required action

Refine the amine SMARTS to exclude amidine and guanidine nitrogens, add positive amine controls and explicit amidine/guanidine negatives, rebuild all dependent artifacts, and rerun the gate. Until a fresh independent result has no critical or major defects, the complete ZINC dataset must not be downloaded or processed.

Stage 2 was not started during this review.
