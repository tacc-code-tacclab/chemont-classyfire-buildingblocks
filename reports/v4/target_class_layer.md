# Layer D (prototype) — ChEMBL target-class pharmacology facet

**Scope.** A prototype pharmacological facet for the subset of building blocks that carry
measured bioactivity in ChEMBL (~7% of the catalogue, from `pharma_coverage_analysis.md`).
Kept **separate** from the structural ChemOnt tree (Layer A). Built by:
`scripts/v4/build_target_class_layer.py` (molecule → distinct assayed targets, then target
enrichment). A background enrichment pass finalises `target_type` for all targets.

## What the layer contains
One row per **molecule–target** pair: `inchikey, chembl_id, target_chembl_id,
target_pref_name, target_organism, target_type`. Stored at
`data/v4_classyfire_groundtruth/target_class_layer.parquet` and
`database/v4/dag_v4.db : target_class_layer`; summary in `reports/v4/target_class_layer.json`.

## Prototype numbers (sample of 1,200 catalogue molecules)
- In ChEMBL: **81 / 1,200 ≈ 6.8%**; of those, **78** had ≥1 assayed target.
- **1,466** molecule–target pairs; **1,081** distinct targets (~13–19 targets per molecule).
- Estimated catalogue coverage: **~6.5% (~127,000 of 1.95M)**.
- Distinct-target composition: **~85% `SINGLE PROTEIN`** (clean molecular targets); the rest is
  `CELL-LINE`, `ORGANISM`, `PROTEIN COMPLEX/FAMILY`, `UNCHECKED`, `NON-MOLECULAR`.
- Target organisms: mostly *Homo sapiens* (59), then *Plasmodium falciparum* (21), rodent
  (24), *E. coli*, firefly luciferase — i.e. a lot of **phenotypic / screening** assays.

## Two honest limitations found
1. **No protein-family tree via the REST API.** ChEMBL's web service does **not** expose the
   `enzyme → kinase → …` / GPCR / ion-channel hierarchy (the `target_component_classifications`
   field is empty over REST). A clean **target-class *taxonomy*** therefore needs the **offline
   ChEMBL SQL dump** (`PROTEIN_CLASSIFICATION` + `COMPONENT_CLASS` tables). Via REST the usable
   class axis is `target_type` + target name + organism.
2. **The signal is noisy for building blocks.** The most frequent "targets" are screening
   artefacts — `Unchecked` (38), whole-organism *P. falciparum* (20), `ADMET` (8) — because
   reagent-like fragments are mostly tested in phenotypic screens, not clean target panels.

## Recommendation
A pharmacology facet is **buildable but partial**: it can annotate only ~7% of the catalogue,
it is biased toward drug-like building blocks, and a proper protein-family taxonomy requires
the offline ChEMBL database rather than the REST API. Keep it as an **optional Layer D** on the
assayed subset — useful for enrichment/lookups — while **ChemOnt (structural) remains the
catalogue-wide backbone**. If a clean target-class tree is wanted, the next step is to load the
ChEMBL SQLite dump locally and join the `PROTEIN_CLASSIFICATION` hierarchy onto these targets.
