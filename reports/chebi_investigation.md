# ChEBI investigation

## Scope and acquisition

This investigation evaluates ChEBI as an ontology-validation and enrichment resource for a taxonomy of commercial synthetic building blocks. It does not evaluate ZINC, classify the pilot set, or select the final integrated strategy.

The official monthly EMBL-EBI ontology release was downloaded on 2026-07-21 from the [ChEBI ontology directory](https://ftp.ebi.ac.uk/pub/databases/chebi/ontology/). The official [downloads page](https://www.ebi.ac.uk/chebi/downloads/) states that a monthly release and nightly builds are available and describes FULL, CORE, and LITE variants in OWL, OBO, and OBO Graph JSON. Release files were chosen instead of `nightly/` to make the analysis reproducible.

| Local file | Upstream URL | Bytes | SHA-256 |
|---|---|---:|---|
| `data/external/chebi/README` | `https://ftp.ebi.ac.uk/pub/databases/chebi/ontology/README` | 4,329 | `89476a8f4df0ef17730710e2ca7715421e0e18258c94adb8546561008f72a1a7` |
| `data/external/chebi/LICENSE` | `https://ftp.ebi.ac.uk/pub/databases/chebi/ontology/LICENSE` | 18,655 | `fe7b4ce83b8381cc5b216bbb4af73c570688d1b819c73bbaed8ca401f4677cd6` |
| `data/external/chebi/chebi.obo.gz` | `https://ftp.ebi.ac.uk/pub/databases/chebi/ontology/chebi.obo.gz` | 47,168,991 | `f2c6fb770bb195780440167e8f01c583313d9cac54bdc8b5e3ba88a3fc45cf29` |
| `data/external/chebi/chebi.owl.gz` | `https://ftp.ebi.ac.uk/pub/databases/chebi/ontology/chebi.owl.gz` | 66,401,672 | `6bd83eab561f2cd2b1dd0f60deecc5baa4a9b057984162084123330c1fa95830` |

Both archives pass `gzip -t`; the OWL file also passes a complete streaming XML parse. The OBO and OWL headers independently identify ChEBI release **253**, dated **2026-07-07**, with version IRI `http://purl.obolibrary.org/obo/chebi/253/chebi.owl`. This is newer than the version 252 OLS page observed during the investigation, demonstrating why the upstream release archive should be the provenance authority.

## Purpose and data model

ChEBI is both a curated chemical database and an ontology of chemical entities, not a general-purpose structure classifier. It includes individual molecular entities, groups, substances, and chemical classes, along with non-structural role concepts. ChEBI training material describes three broad sub-ontologies: molecular structure, role, and subatomic particle. Consequently, downstream use must distinguish structural `is_a` classification from `has role` and chemistry-specific relationships.

The FULL release includes identifiers, labels, definitions, subsets/star ratings, synonyms, curated cross-references, formula/mass/charge, SMILES/InChI/InChIKey, secondary identifiers, and relationships. CORE omits synonyms and curated cross-references; LITE retains IDs, labels, subsets, and relationships. FULL is appropriate for local identity mapping and enrichment; LITE is sufficient for a hierarchy-only deployment.

## Observed OBO/OWL structure

The OBO file uses OBO format 1.2. The OWL file is RDF/XML and expresses terms as OWL classes. IDs such as `CHEBI:17296` map to persistent OBO-style IRIs such as `http://purl.obolibrary.org/obo/CHEBI_17296`. The release contains 19,418 `alt_id` assertions for secondary/merged identifiers; consumers should retain these mappings rather than treating old identifiers as new nodes.

Streaming analysis of the complete OBO release produced:

| Metric | Count |
|---|---:|
| ChEBI terms | 218,542 |
| Explicit `is_a` edges | 307,965 |
| Terms with at least one `is_a` parent | 218,249 |
| Terms with more than one direct `is_a` parent | 54,697 (25.0%) |
| Maximum direct `is_a` parent count | 14 |
| Non-`is_a` relationship assertions | 109,108 |
| Relationship types other than `is_a` | 9 |
| Terms with definitions | 55,402 |
| Terms with SMILES | 201,171 |
| Terms with InChI/InChIKey | 189,632 |
| Terms with formula | 202,337 |
| Obsolete terms explicitly present | 1 |

The explicit `is_a` graph passed topological cycle detection across all 218,542 nodes. There are 293 terms with no asserted `is_a` parent, and the maximum asserted path depth is 23. The apparently large root count reflects leaf/entity records lacking an asserted parent as well as conceptual roots; it should not be interpreted as 293 designed top-level taxonomy branches. ChEBI has no fixed number of hierarchy levels, and a term can occur at different depths through different parent paths.

Multiple inheritance is extensive and chemically useful. For example, `CHEBI:100000` has direct parents corresponding to benzenes, ring assemblies, and azetidines. Converting this ontology to a single-parent tree would discard asserted structural information.

The nine observed non-`is_a` relations are `has role` (59,087), `has functional parent` (20,512), `is conjugate base of` (8,757), `is conjugate acid of` (8,707), `has part` (4,120), `is enantiomer of` (2,800), `has parent hydride` (1,872), `is tautomer of` (1,951), and `is substituent group from` (1,302). Several are explicitly cyclic/symmetric in the OBO typedefs. They must not be merged blindly into the canonical subclass DAG. In particular, `has role` is annotation/enrichment rather than structural subsumption.

## Stable identifiers and traceability

Primary ChEBI IDs are stable accession-style identifiers. Merged or replaced accessions can be represented as `alt_id`, and the release contains definitions, subset/star status, xrefs, and source annotations where available. A robust database import should therefore store the release number, primary ID, alternative IDs, and provenance separately. It should not assume that the human-readable name is stable or unique.

## Local identity lookup experiment

RDKit 2026.03.2 was used to generate InChIKeys from nine representative building-block SMILES and match them against the FULL release. Seven had exact ChEBI records: aniline, benzylamine, benzoic acid, phenylboronic acid, 4-bromopyridine, ethanolamine, and cyclopropylamine. Pinacol phenylboronate and a synthetic heterocycle test did not match. Full results are in `results/resource_tests/chebi/exact_structure_lookup.tsv`.

This 7/9 result is an illustrative capability test, **not a coverage estimate** for the ZINC pilot. It shows the central limitation: a local ChEBI release supports efficient identity lookup and retrieval of existing asserted parents, roles, and chemistry relations, but does not provide a deterministic algorithm that assigns an arbitrary previously unseen molecule to ChEBI structural classes. OLS and ChEBI web services can search existing records; they do not turn ChEBI itself into a ClassyFire-like arbitrary-structure classifier. New authoritative entries require ChEBI submission/curation.

Exact identity matching should use standardized structures and consider protonation, salt/fragment handling, tautomerism, stereochemistry, and InChI layers. A failed exact InChIKey match is not evidence that no relevant chemical class exists; it only means the supplied representation did not match a released entry.

## Bulk and local scalability

The compressed ontology can be streamed locally with modest memory, and the complete asserted graph can be extracted in seconds to minutes on this server. This is technically suitable for bulk enrichment of hundreds of thousands of compounds **when exact IDs or structure matches exist**. A local index over InChIKey/SMILES and adjacency tables avoids API rate limits and provides reproducible release-pinned results. FULL OWL is much larger uncompressed (the server listing reports approximately 826 MB), while OBO is simpler for bulk extraction. LITE is preferable when only hierarchy edges are required.

API calls are unnecessary for bulk hierarchy import and would add latency and changing external-state dependence. APIs remain useful for interactive inspection, but release files should underpin production provenance.

## Licence, redistribution, and maintenance

The ontology metadata, downloaded `LICENSE`, and official [about page](https://www.ebi.ac.uk/chebi/about/) specify **Creative Commons Attribution 4.0 International (CC BY 4.0)**. Attribution should name ChEBI, its URL, and release version. The README contains one contradictory sentence saying “Attribution-ShareAlike 4.0,” but its own file manifest says CC BY 4.0 and the bundled legal text is CC BY 4.0; this appears to be a README wording error. Any redistribution should follow the bundled LICENSE and cite release 253.

ChEBI is actively maintained by EMBL-EBI, publishes monthly releases plus nightly builds, exposes public downloads and services, and provides issue tracking. Release pinning and checksums make local reuse reproducible.

## Recommended role in this project

ChEBI is strong for:

- stable chemical identifiers and exact-structure enrichment;
- authoritative asserted class/role relations for molecules already present;
- cross-checking structural assignments from an arbitrary-molecule classifier;
- supplying definitions, synonyms, and ontology paths;
- validating multiple inheritance and enriching the canonical DAG with carefully filtered `is_a` edges.

ChEBI should **not be the sole primary classifier** for the commercial-building-block dataset because it cannot authoritatively classify arbitrary absent structures and its scope emphasizes biologically relevant chemical entities rather than purchasable synthetic building blocks. The most defensible role is validation and enrichment after standardized exact matching, with explicit evidence labels. Only structural `is_a` edges should enter the subclass DAG by default; roles and chemistry-specific relations should remain typed, separate edges or annotations.

## Reproducible artifacts

- `results/resource_tests/chebi/analyze_chebi.py`: streaming release analysis.
- `results/resource_tests/chebi/ontology_metrics.json`: release and content counts.
- `results/resource_tests/chebi/relationship_counts.tsv`: typed relation counts.
- `results/resource_tests/chebi/multiple_parent_examples.tsv`: examples of asserted multiple inheritance.
- `results/resource_tests/chebi/test_local_capabilities.py`: exact-match and graph tests.
- `results/resource_tests/chebi/exact_structure_lookup.tsv`: identity lookup outcomes.
- `results/resource_tests/chebi/asserted_is_a_graph_check.json`: asserted subclass DAG cycle result.

All quantitative counts refer to the downloaded full release 253 and explicit OBO assertions; no OWL reasoner was run, so inferred axioms are not included.
