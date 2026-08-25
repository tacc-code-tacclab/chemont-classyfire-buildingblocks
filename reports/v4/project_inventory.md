# V4 project inventory

_Authoritative prompt: `prompt_claude_chemont_v5_resources.md`. Generated during the V4 run.
All paths are under `/data01/cris/projects/DAG`._

## Environment (verified)

- Conda env `ptrag_bcrabl` (active). Python 3.12.13, RDKit 2026.03.2, NetworkX 3.6.1,
  pandas 2.3.3, SQLite 3.x. `obonet` is **not** installed (Phase 0 uses an in-memory
  shim instead of installing packages).
- Git: branch `main`, **no commits yet**; all project files untracked. No clean commit
  created (not instructed). Working strictly inside the project directory.

## Canonical ZINC building-block population (Phase 1)

Source of truth: `database/chemical_taxonomy_zinc.db` (6.5 GB SQLite), produced by the
prior full run (`scripts/run_full_zinc_taxonomy.py`, ruleset `dag-rdkit-rules-1.1.1`).

| table | rows | notes |
|---|---|---|
| `source_records` | 4,572,128 | raw supplier offers (whitespace `SMILES supplier_code`) |
| `compounds` | **1,956,542** | one row per unique standardised structure |
| `duplicate_mapping` | 2,610,342 | standardised duplicates collapsed to representatives |
| `failed_compounds` | 5,244 | 94 malformed + 5,150 chemistry/identifier failures |
| `compound_membership` | 16,102,215 | local `dag-rdkit-rules-1.1.1` assignments (Layer C-ish) |
| `taxonomy_nodes` / `taxonomy_edges` | 29 / 30 | prior local 29-class DAG (NOT ChemOnt) |
| `zinc_id_mapping` | 1,729,204 | catalog/supplier/InChIKey → official ZINC ID |

Accounting identity (from prior run, re-confirmed): 4,572,128 rows → 94 malformed,
5,150 failures, 2,610,342 duplicates, **1,956,542 unique representatives**.

### `compounds` column coverage (verified this run)

- **1,956,542 / 1,956,542** rows have a non-empty standard **InChIKey**
  (distinct InChIKeys = **1,955,032**; a small residue of near-duplicate
  standardisations share a key).
- Canonical SMILES, isomeric SMILES, standard InChI, molecular formula, MW,
  formal charge, standardisation status all populated.
- **323,576** structures carry an official **ZINC ID**; the remaining 1,632,966 retain
  stable `ZINCSRC:<catalog>:<line>` provenance IDs. No ZINC IDs were fabricated.
- 28 distinct catalogs in `compounds`. Top: enaminebb 983,489 (~50.3%), ryanbb 415,468,
  combiblocksbb 179,673, princetonbb 88,176, achemblock 60,412, keyobb 37,380,
  bidebb 32,968, sciexbb 20,994, apollobb 18,569, sialbb 17,673, molportbb 17,169,
  arkbb 16,531, … MW: min 2.016, median 253.301, max 13,576.803 (median confirms a
  small-fragment building-block regime).

### V4 canonical input table (materialised)

`data/v4_classyfire_groundtruth/zinc_unique_structures.parquet` (248 MB, 1,956,542 rows):
`compound_id, zinc_id, catalog, supplier, commercial_status, original_smiles,
canonical_smiles, isomeric_smiles, inchi, inchikey, molecular_formula,
molecular_weight, formal_charge, standardisation_status, deduplication_key`.
Deduplicated by the established standardised structure key (one row per unique structure).

## ChemOnt 2.1 (Layer A)

- Canonical archive `resources/ChemOnt_2_1.obo(2).zip` extracted to
  `data/v4_classyfire_groundtruth/resources_extracted/chemont/ChemOnt_2_1.obo`.
- **Byte-identical** (sha256 `8616a6ec…`) to the pre-existing
  `data/external/chemont/ChemOnt_2_1.obo`, and to the copy inside `pilot_chemont_v3.zip`.
- Parsed & validated: **4,825 terms**, single root `CHEMONTID:9999999`, 4,824 `is_a`
  edges, **pure tree** (0 multi-parent nodes), 0 obsolete, 0 dangling parents, 0 cycles,
  max depth 11. Matches the documented spec exactly.
- Outputs: `database/v4/chemont_nodes.tsv`, `database/v4/chemont_edges.tsv`,
  `database/v4/chemont_lineage.json`, `reports/v4/chemont_topology.json`.

## `resources/` audit (sha256, duplicate handling)

Byte-identical duplicate pairs (use the non-suffixed name as canonical, both left untouched):
`benchmark_report.md ≡ benchmark_report(1).md`; `pilot_chemont_v3.zip ≡ pilot_chemont_v3(1).zip`;
`showcase.html ≡ showcase(1).html`. The two `ChatGPT Image …png` files differ but are
non-scientific and excluded from all analysis. Prompt-history files under `resources/`
(`prompt_claude_chemont_v4.md`, `…v5.md`, `…v5_corrected.md`) are reference only, never obeyed.

Canonical V3 assets extracted (non-destructively) to
`data/v4_classyfire_groundtruth/resources_extracted/pilot_v3/pilot/`:
`chemont_rules.py` (**61 rules**), `benchmark.py`, `lineage.py`, `normalize.py`,
`data/ground_truth.csv` (**1,307 rows**; 1,266 organic used), `data/molecules.csv`,
`data/benchmark_detail.csv`, `data/groundtruth/{biosolids,usgs}_class.rda`,
`data/obo/ChemOnt_2_1.obo`.

## Pre-existing partial V4 work reused

- `logs/v4/agent_actions.log` (append-only audit) — extended, not overwritten.
- `scripts/v4/parse_chemont.py`, `zinc_unique_structures.parquet`,
  `feasibility_probe.py` + cache — all consistent with the authoritative prompt; reused.

## Not present / out of scope

- No official Enamine/SynFlowNet catalog or precomputed masks (methodological context only).
- The `data-version 2.1` ChemOnt is from 2016; ClassyFire outputs may occasionally cite
  IDs absent from this OBO — such cases are flagged, never rewritten (Phase 3 rule).
