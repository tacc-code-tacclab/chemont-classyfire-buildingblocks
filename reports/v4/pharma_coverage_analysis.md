# Pharmacology-taxonomy feasibility: coverage of the building-block catalogue

**Question.** Besides the structural ChemOnt tree, could we attach a *pharmacological*
taxonomy to the ~1.95M commercial building blocks? Which reference is best?

**Method.** Representative random sample of unique building-block InChIKeys (seed 20260722)
looked up in **ChEMBL** (one polite stream, cached/resumable:
`scripts/v4/pharma_coverage_probe.py`). ChEMBL gives, in one place, ATC therapeutic class,
clinical/approval phase, and bioactivity (proxy for a target/mechanism annotation being
possible). ChEBI roles were also considered but the local `chebi.obo` has **0 `has_role`**
entries and no InChIKeys, so it is not usable without the heavier OWL.

## Coverage (sample n=300; probe continuing to 1200)

| candidate pharmacology axis | what it labels | coverage of catalogue |
|---|---|---|
| **ATC (WHO therapeutic class)** | what disease/therapy area | **~0%** (0/300; 95% upper bound ≲1.3% ⇒ <~25k of 1.95M) |
| approved drug (max phase 4) | is it a marketed drug | ~0% (0/300) |
| any clinical phase (≥1) | reached clinical testing | ~0.3% (1/300) |
| **ChEMBL target / bioactivity** | which protein target(s) it was tested on | **~7.3%** (22/300; ~143k of 1.95M) |
| ChEBI pharmacological role | curated role (drug, inhibitor…) | not usable from local file; expected low |

## Reading & recommendation

- **ATC / therapeutic taxonomies are not viable here.** Building blocks are reagents and
  fragments, not approved drugs, so essentially none carry an ATC code (and MeSH
  "pharmacological action" would be similarly ~0%). An ATC facet would be empty.
- **The only pharmacology axis with real coverage is ChEMBL target/bioactivity (~7%).** For
  the subset that has been assayed we can attach the **ChEMBL protein-target class hierarchy**
  (enzyme → kinase → …, GPCR, ion channel, transporter, …) — itself a clean tree, mechanistic
  rather than therapeutic. This is the **best choice** if a pharmacology facet is wanted.
- **But it is inherently sparse and biased.** ~7% ≈ ~143k molecules, skewed toward the more
  drug-like building blocks; the other ~93% simply have no measured pharmacology. So a
  pharmacology layer can only be an **optional enrichment on a subset**, not a
  catalogue-wide backbone like the structural ChemOnt tree (genuine ~54%, structural mapper
  ~100%).

**Bottom line.** Keep ChemOnt (structural) as the backbone. If a pharmacology facet is added,
use **ChEMBL target-class** on the ~7% assayed subset, as a separate optional layer; do **not**
build on ATC/therapeutic, which is ~empty for this catalogue.
