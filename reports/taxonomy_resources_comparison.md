# Taxonomy resource comparison

## Scope

This evidence-based comparison covers the exact public artifacts and live capabilities inspected on 2026-07-21. It is an input to, not a substitute for, the required 20–50-molecule pilot comparison and final strategy decision.

| Criterion | ChemOnt / ClassyFire | ChEBI | DrugTax |
|---|---|---|---|
| Primary purpose | Structural chemical taxonomy plus remote classifier | Curated chemical ontology/database | Coarse local SMILES-string labels |
| Captured version | ChemOnt 2.1 (2016); API client commit `b7a194f` | Release 253 (2026-07-07) | 1.0.14, commit `e47fe84` (2022) |
| Public hierarchy | 4,825 classes, 4,824 `is_a` edges | 218,542 terms, 307,965 asserted `is_a` edges | No formal graph |
| Hierarchy depth | Maximum 11 edges | Maximum asserted depth 23 | Two implicit ranks |
| Class multiple inheritance | No: every non-root term has one parent | Yes: 54,697 terms have multiple direct parents | Not represented |
| Compound multiple membership | Yes: direct class plus alternative categories | Yes for curated entities | Yes, broad heuristic labels |
| Stable class IDs | `CHEMONTID` | `CHEBI` IDs plus `alt_id` mappings | None |
| Local hierarchy | Yes, OBO | Yes, OBO/OWL | Hard-coded labels only |
| Local arbitrary-molecule classifier | No public classifier/rule implementation | No; exact existing-record matching and ontology lookup only | Yes, but chemically unreliable raw-string rules |
| API dependency | Required for new classifications | Not required for release import or exact matching | None for SMILES; PubChem only for optional name lookup |
| Bulk scalability | Unproven and risky: remote queue, observed timeout, no SLA | Strong for local exact-match enrichment and graph import | Computationally fast, scientifically unsuitable |
| Reproducibility | Hierarchy reproducible; new assignments depend on remote opaque service | Strong with pinned release/checksums | Deterministic only for identical raw string/version; representation-dependent |
| License | No affirmative repository/OBO license found; site requires permission for commercial use or redistribution | CC BY 4.0 | GPL-3.0 software |
| Maintenance evidence | Ontology 2016; client last commit 2019; service still responds | Active monthly EMBL-EBI releases | Last source commit 2022 |

## Experimental findings

ChemOnt 2.1 is internally complete and acyclic, with definitions for all 4,825 terms, but is a strict single-parent tree. A live ClassyFire submission of aspirin succeeded and returned a direct parent plus ten alternative categories. The classifier itself and its reported historical rule/toolkit stack are not present in the public repository. During the same investigation, a taxonomy-node request returned a 504/timed out, HTTPS reset while the hard-coded HTTP route worked, and no production throughput or rate guarantee was found. Returned assignments can be cached and traced, but arbitrary-molecule classification cannot be reproduced locally from the public artifacts.

ChEBI 253 is an acyclic multi-parent ontology with 54,697 terms having multiple direct asserted parents and 109,108 typed non-`is_a` relationships. Seven of nine illustrative building blocks matched local ChEBI records exactly by RDKit-derived InChIKey. This confirms useful identity validation and enrichment but is not a pilot coverage estimate. ChEBI does not classify absent arbitrary molecules; roles, conjugacy, tautomer, enantiomer, and part relationships must remain typed separately from the structural subclass DAG.

DrugTax is not a ChemOnt implementation and does not call ClassyFire. It uses literal substrings and character counts in unparsed SMILES. The probe ran at roughly 580 classifications/second, but common aromatic structures were labeled inorganic, sodium chloride was labeled organic, and malformed text was accepted. It has no stable class identifiers, definitions table, or parent-child graph. It is excluded from authoritative use.

## Provisional architectural implication

No inspected resource independently satisfies arbitrary-structure classification, local reproducibility, chemical correctness, stable identifiers, and multi-parent hierarchy requirements.

- ChemOnt supplies a relevant structural vocabulary and ClassyFire can supply remote rule-based memberships, but licensing, security, service stability, and scale require explicit controls.
- ChEBI supplies the strongest public, current, locally reproducible DAG and exact-identity enrichment, but cannot cover unseen structures by itself.
- DrugTax must not be used as the canonical classifier; retaining its test results documents why.

The 20–50-compound test must therefore measure ClassyFire completion/latency and ChEBI exact-match coverage on the actual ZINC pilot. A scalable fallback may require a transparent RDKit SMARTS classification layer whose outputs are explicitly labeled deterministic/rule-based rather than authoritative ontology assignments. The final architecture will be selected only after that test.

## Reproducibility and source artifacts

Detailed provenance, checksums, API evidence, code inspection, licenses, and limitations are recorded in `reports/chemont_classyfire_investigation.md`, `reports/chebi_investigation.md`, and `reports/drugtax_investigation.md`. Raw/test artifacts are under `data/external/` and `results/resource_tests/`. The preserved `data/external/chebi/chebi.owl.gz.old_20260721_181646` is an interrupted download retained under the project no-delete policy; it is not the validated release artifact.
