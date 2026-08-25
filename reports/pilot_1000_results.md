# Pilot 1,000 classification results

All 1,000 standardized ZINC records were processed with corrected local ruleset `dag-rdkit-rules-1.1.1` using RDKit 2026.03.2. Runtime is deliberately excluded from canonical metrics so reruns remain byte reproducible.

The classifier created 7,309 direct deterministic memberships and 1,000 inferred ancestor memberships. Of the 1,000 organic pilot molecules, 974 received at least one recognized specific structural class, while 26 were explicitly marked `Unresolved organic compound` in addition to generic elemental/structural classes. These 26 are partially rather than falsely specifically classified.

Frequent direct classes were oxygen-containing organic compounds (879), nitrogen-containing organic compounds (847), heterocycles (665), heteroaromatics (458), amines (436), carboxylic acids (276), sulfur-containing compounds (258), and organohalogens (252). Specific amine memberships included 210 primary, 129 secondary, 137 tertiary, and 216 aromatic assignments. Pyridine matched 106 compounds. Amidine- and guanidine-like nitrogens are excluded from amine/subtype rules.

All assignments are nonexclusive. The database distinguishes direct `deterministic_structure_rule` evidence from `inferred_assignment` ancestry. No similarity predictions and no authoritative external ontology claims were generated. Exact ChEBI enrichment was omitted from this integrated run because it was optional and would not improve arbitrary-molecule rule coverage.

The canonical outputs are the four pilot TSVs, GraphML, JSON, and SQLite database under `taxonomy/` and `database/`. The primary-path file is a deterministic convenience projection; it is not the canonical membership representation.
