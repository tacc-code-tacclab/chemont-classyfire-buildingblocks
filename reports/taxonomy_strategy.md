# Canonical taxonomy strategy

## Decision

The pilot and future full-scale pipeline will use a **locally executable, versioned RDKit SMARTS structural taxonomy** as the canonical arbitrary-molecule classifier. It will assign non-exclusive chemically defined classes with project-stable identifiers and explicit `deterministic_structure_rule` evidence. The class hierarchy will be a directed acyclic graph and compounds will remain separate instances linked through membership records.

ChEBI release 253 will provide exact-InChIKey identity validation and ontology enrichment. Its asserted structural `is_a` ancestry may be retained as authoritative ChEBI evidence for exact-matched compounds, while role, conjugacy, tautomer, enantiomer, part, and other non-subclass relations remain typed and separate. ChemOnt 2.1 and cached ClassyFire results will be retained as an external structural benchmark for the 30-compound panel, not as the production classifier. DrugTax is excluded from canonical membership generation.

This changes the initial hypothesis because experimental evidence shows that no inspected external resource is both scientifically adequate and operationally scalable for arbitrary commercial building blocks.

## Evidence behind the selection

| Criterion | Local RDKit rules + ChEBI enrichment | ClassyFire production dependency | ChEBI alone | DrugTax |
|---|---|---|---|---|
| Chemical meaning | Explicit named SMARTS classes; reviewable | Strong structural vocabulary; opaque classifier | Strong curated ontology for represented entities | Coarse and error-prone |
| Arbitrary structures | Yes, deterministic local rules | Yes, remote service | No | Accepts strings, but without chemical parsing |
| Reproducibility | Pinned rules, RDKit, inputs, and checksums | Remote implementation unavailable | Strong for pinned releases | Input-spelling dependent |
| 200k scalability | Local and parallelizable | Unsupported; 17 HTTP 429 responses in the 30-molecule bounded trace | Local exact lookup scales, but partial coverage | Fast but scientifically invalid |
| Stable identifiers | Versioned project IDs plus mapped external IDs | `CHEMONTID`, but assignment service-dependent | Stable `CHEBI` IDs | None |
| Multiple membership | Native non-exclusive assignments | Direct plus alternative categories | Native asserted multiple inheritance | Broad labels only |
| DAG support | Explicit rule-class DAG plus ChEBI structural enrichment | ChemOnt itself is a tree | Extensive multi-parent `is_a` graph | No graph |
| Licensing/security | Project code/data; source ontologies separately attributed | Site requires permission for commercial use/redistribution; working route was HTTP | CC BY 4.0 | GPL-3.0 software |

The required 30-compound experiment produced 30/30 eventual ClassyFire results, but the initial bounded trace encountered 17 HTTP 429 responses. ChEBI exact identity coverage was 9/30, of which six had multiple direct asserted parents. DrugTax accepted all strings but made a clear organic/inorganic error and other suspicious assignments. These results are detailed in `reports/resource_test_results.md`.

## Canonical evidence model

Every membership must state one of the following evidence levels; they are not interchangeable:

1. `authoritative_ontology_assignment`: an asserted ChEBI relationship associated with an exact standardized identity match.
2. `deterministic_structure_rule`: direct RDKit substructure/property evaluation against a versioned rule.
3. `external_rule_based_assignment`: cached ClassyFire result, including query ID, retrieval date, classification version, and raw-response checksum.
4. `inferred_assignment`: ancestor propagation from an explicitly recorded direct membership; the source edge path must be reconstructible.
5. `unresolved`: no sufficiently specific rule or authoritative identity assignment.

Similarity-only prediction is not part of the canonical strategy and must never be labeled authoritative.

## Rule taxonomy design controls

- Classes must describe recognized structural concepts such as amines, carboxylic acids, alcohols, phenols, aldehydes, ketones, organohalogens, boronic acids/esters, heterocycles, sulfur compounds, phosphorus compounds, and multifunctional compounds.
- Rules operate on standardized RDKit molecular graphs, never raw SMILES substrings.
- Rules are non-exclusive. A fluorinated aminopyridine can simultaneously receive pyridine/heteroaromatic, aromatic amine, and organofluorine memberships.
- Each rule records an immutable ID, name, definition, SMARTS or property predicate, parent IDs, version, and tests with positive and negative controls.
- Generic ancestors are inferred only through stored DAG edges. Direct and inferred evidence are distinct.
- The rule DAG must pass cycle detection, missing-reference checks, and deterministic export checks.
- ChEBI nodes retain their own namespace and provenance. Cross-ontology equivalence or mapping edges are added only with explicit evidence; names alone are insufficient.

## Primary paths and tree projection

The DAG is canonical. A deterministic primary-leaf selection policy will produce one convenience path per compound using specificity/depth, rule priority, and stable-ID tie-breaking. The resulting tree projection is derivative and must quantify discarded class edges and compound memberships.

## Scalability and maintenance

The local classifier requires one RDKit parse plus a bounded set of compiled SMARTS/property checks per molecule. Rules and ontology imports are versioned independently of input adapters, so changing ZINC input to Enamine does not change the taxonomy architecture. Performance will be measured on the 1,000-compound pilot and extrapolated conservatively; the future Enamine run will retain source IDs and regenerate all memberships rather than reuse ZINC identifiers.

## Limitations accepted at this gate

The project rule taxonomy will be shallower than the full ChemOnt vocabulary and cannot claim ClassyFire equivalence. Its advantage is transparent evidence, reproducibility, chemical reviewability, and scale. ChEBI enrichment will remain incomplete for unseen catalog structures. The ZINC pilot also lacks boron chemistry because none was exposed in the bounded reference-SDF candidate pool; boronic-class rules must still be implemented and unit-tested synthetically, and this source-domain gap must remain a pilot warning.
