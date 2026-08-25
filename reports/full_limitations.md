# Full taxonomy limitations

The full pipeline is reproducible, local, fast enough for multi-million-row use, and preserves complete source/duplicate/failure provenance. Its limitations are primarily taxonomy breadth and source metadata coverage, not graph or database integrity.

1. The canonical classifier is a transparent project-local RDKit SMARTS taxonomy with 29 nodes, not the complete ChemOnt or ChEBI vocabulary. Its assignments are deterministic structural rules, not authoritative ontology assertions.
2. 48,676 retained organic compounds (2.4879%) lack a recognized specific class in ruleset 1.1.1. Expanding rules could improve coverage, but doing so requires a new reviewed ruleset rather than changing this validated full run retrospectively.
3. Generic elemental and structural classes cause most compounds to have several direct memberships. This is chemically traceable, but users should distinguish broad memberships from the most specific primary class.
4. Only 323,576 of 1,956,542 unique representatives (16.5382%) could be assigned an official ZINC ID by an exact, unambiguous match on catalog, supplier code, and standardized InChIKey using the locally available official `.info` mappings. The remaining 1,632,966 retain stable `ZINCSRC:<catalog>:<line>` IDs. No ZINC ID was inferred or fabricated.
5. Official `.info` mappings were locally available for only 17 catalogs, and standardized parent/tautomer decisions can legitimately prevent equality with an original-catalog InChIKey. Thus missing ZINC-ID coverage is a metadata-join limitation, not molecule loss.
6. Source snapshots span 2018–2025. Commercial-group membership reflects the official static ZINC snapshot, not guaranteed present-day supplier inventory.
7. Standardization retains the largest organic fragment, normalizes charges, canonicalizes tautomers, and preserves specified stereo according to the documented pilot semantics. Alternative domain policies would produce different identities and duplicate counts.
8. The local taxonomy recognizes a bounded set of building-block motifs. Similarity-only predictions were not used to fill gaps, and ChEBI exact-identity enrichment was not treated as an arbitrary-molecule classifier.
9. The full raw export is subject to ZINC's restriction against redistribution of major portions without written permission; these artifacts are for local research.

The measured end-to-end runtime was **1,081.159 seconds (about 18.0 minutes)** with 64 workers. This demonstrates ample computational scalability for a future approximately 200,000-record Enamine input, provided the same input adapter supplies stable identifiers and SMILES. The taxonomy architecture does not require redesign for that replacement.
