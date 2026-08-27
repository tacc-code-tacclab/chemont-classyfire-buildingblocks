# Layer D — ChEMBL protein target-class TREE (built from the offline dump)

The clean protein-family hierarchy that the ChEMBL REST API does **not** expose was built
from the offline **ChEMBL 37 SQLite dump** (5.76 GB download → 30 GB db;
`scripts/v4/parallel_dl_chembl.sh` for the fast segmented download,
`scripts/v4/build_target_tree_from_dump.py` for the build).

## The taxonomy (kept separate from the ChemOnt structural tree)
- Source join: `target_dictionary → target_components → component_class → protein_classification`.
- **905 nodes, 6 levels**, single root "Protein class". It is a **tree** (each class one parent),
  exactly like ChemOnt but for *what a molecule acts on* instead of *what it is*.
- Exported for the repo as `database/v4/target_class_tree_nodes.tsv` /
  `target_class_tree_edges.tsv`; also `dag_v4.db : target_class_tree_{nodes,edges}`.

Top of the tree (L1 → L2 examples):
```
Protein class
├─ Enzyme            → Kinase, Protease, Cytochrome P450, Phosphodiesterase, Transferase, …
├─ Membrane receptor → Family A/B/C GPCR, Frizzled, Toll-like/IL-1, …
├─ Ion channel       → Ligand-gated, Voltage-gated, Other
├─ Transporter       → Electrochemical, Primary active, …
├─ Transcription factor → Nuclear receptor
├─ Epigenetic regulator → Reader, Writer, Eraser
├─ Transporter / Adhesion / Secreted / Structural / Surface antigen / Unclassified …
```

## Join onto our building blocks
- Of the **1,081** distinct targets our building blocks were assayed against, **593 (54.9%)**
  map to a protein-family class (the rest are cell-lines, whole organisms, "unchecked" or
  non-protein screening targets — no protein class, correctly left null).
- **55 of 78** molecules in the layer get ≥1 protein-family class.
- Distribution of the classified targets — **L1:** enzyme 468, membrane receptor 43,
  transporter 19, ion channel 15, transcription factor 13, epigenetic regulator 11, …
  **L2:** kinase 370, GPCR-7tm1 40, transferase 22, reductase 16, hydrolase 14, protease 8, …
  (kinase-heavy, reflecting the screening libraries these fragments came from).

Enriched layer: `data/v4_classyfire_groundtruth/target_class_layer_enriched.parquet` and
`dag_v4.db : target_class_layer_enriched` — one row per molecule–target pair with
`class_l1, class_l2, class_l3, class_leaf, protein_class_path`.

## Status
The pharmacology facet now has a **real, clean target-class taxonomy**, separate from ChemOnt.
Coverage remains the earlier finding: only ~7% of the catalogue has any ChEMBL bioactivity, and
of those targets ~55% carry a protein-family class — so this is an **optional enrichment layer on
a small, drug-like subset**, not a catalogue-wide backbone. ChemOnt (structural) stays the
backbone; this ChEMBL target-class tree is Layer D on top of it.
