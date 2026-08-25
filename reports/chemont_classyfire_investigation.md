# ChemOnt / ClassyFire investigation

## Scope and conclusion

This report evaluates the ChemOnt 2.1 taxonomy and the ClassyFire service/API as candidates for classifying commercial synthetic building blocks. It does not select the project's final taxonomy strategy.

ChemOnt is a chemically meaningful, structure-oriented vocabulary with stable `CHEMONTID` identifiers, definitions, synonyms, cross-references, and a complete downloadable hierarchy. The downloaded release is strictly a **single-parent tree**, not a multiple-inheritance ontology. ClassyFire can assign arbitrary submitted structures to a primary path plus alternative structural categories, but the actual classifier and its structural rules are not available in the public API-client repository. Classification is therefore remote-service-dependent. A live one-structure submission succeeded, but an ontology-node request timed out, HTTPS failed in this environment, the published ontology snapshot is from 2016, and the public API client was last committed in 2019. These facts make unthrottled classification of hundreds of thousands of new molecules a reproducibility and scalability risk that must be measured before adoption.

## Resources acquired

| Resource | Local path | Version / revision | Source | SHA-256 |
|---|---|---|---|---|
| ChemOnt ontology ZIP | `data/external/chemont/ChemOnt_2_1.obo.zip` | data version 2.1; file date 2016-08-26 | `http://classyfire.wishartlab.com/system/downloads/1_0/chemont/ChemOnt_2_1.obo.zip` | `ddc3f66fe817271006a447848faf50cbe5e37da861fc8a7dde466d98d4477659` |
| ChemOnt ontology | `data/external/chemont/ChemOnt_2_1.obo` | 2.1; OBO header date `26:08:2016 16:28` | extracted from official ZIP | `8616a6ecb96c8aeb204739a4de045cd290eab9a0e164d0ceaa5d888d0751fe22` |
| WishartLab ClassyFire API client | `external_repositories/other_repositories/classyfire_api/` | commit `b7a194f694f8cef34b15bb8a1ef96583aed37d83`; last commit 2019-03-27; 53 commits; no tags | `https://bitbucket.org/wishartlab/classyfire_api.git` | repository pinned by commit |
| Homepage snapshot | `results/resource_tests/chemont/classyfire_home_http.html` | homepage advertises ClassyFire 1.0 and ChemOnt coverage of 4,825 classes | `http://classyfire.wishartlab.com/` | retained as raw evidence |

Acquisition date was 2026-07-21 UTC. The server responses unusually supplied 2023 `Date` headers; those headers are retained and must not be mistaken for the acquisition date.

## What the downloaded ontology actually contains

A standard-library parser checked every `[Term]` stanza and every `is_a` reference:

| Property | Observed value |
|---|---:|
| Terms | 4,825 |
| Text definitions | 4,825 |
| Synonyms | 9,025 |
| Cross-reference lines | 850 |
| `is_a` edges | 4,824 |
| Root nodes | 1 (`CHEMONTID:9999999`, Chemical entities) |
| Non-root terms with exactly one parent | 4,824 |
| Terms with multiple `is_a` parents | 0 |
| Other `relationship:` lines | 0 |
| Missing parent references | 0 |
| Obsolete terms | 0 |
| Cycles | 0 |
| Maximum root-to-node distance | 11 edges |

The OBO header identifies `format-version: 1.2`, `data-version: 2.1`, ontology `ChemOnt`, generation by OBO-Edit 2.3.1, and developers Yannick Djoumbou Feunang and David S. Wishart. Entries provide `CHEMONTID` IDs, names, English structural definitions, scoped synonyms, external cross-references, and one `is_a` parent. Synonym mappings include ChEBI, MeSH, IUPAC, LIPID MAPS, and ChemOnt terms.

This matches the ClassyFire paper's design: the hierarchy itself is a tree with named levels (kingdom, superclass, class, subclass, and deeper levels), while a molecule can match several categories. It is important not to conflate these two properties. ChemOnt 2.1 does **not** provide multiple-inheritance class edges. Multiple chemical meanings arise in ClassyFire output through a selected direct-parent path and additional category assignments.

## API and classifier behavior from actual code

The public WishartLab repository is a Ruby **HTTP client**, not the ClassyFire classification engine. `lib/classyfire_api.rb` implements:

- `POST /queries` for SMILES, InChI, IUPAC-name, or FASTA submissions;
- `GET /queries/{id}.{json,csv,sdf}` and `/queries/{id}/status.json`;
- `GET /entities/{inchikey}.{json,csv,sdf}` for already classified entities;
- `GET /tax_nodes/{C-prefixed-id}.json`;
- client-side file deduplication, chunk submission, polling, and result retrieval.

It contains no ChemOnt assignment rules, SMARTS library, feature-weight dictionary, ChemAxon-based preprocessing implementation, or local classification executable. The 2016 paper reports that the service used ChemAxon JChem 15.5.25.0 and more than 9,000 rules/patterns/criteria. Those components are not present in the cloned repository or OBO file. Consequently:

- the hierarchy can be parsed, queried, graphed, and redistributed locally subject to licensing;
- previously returned assignments can be cached locally;
- **new arbitrary structures cannot be classified locally and reproducibly from these public artifacts alone**.

The API client defaults to chunks of 10 structures in current source, initially submits two jobs, and sleeps 60 seconds between submission rounds; its generated documentation reflects an older 1,000/240-second variant. The live homepage advises fewer than 1,000 structures per input for quick results. No formal rate-limit, throughput guarantee, queue SLA, API versioning policy, or bulk license grant was found.

## Live service probes

Raw requests, headers, and responses are under `results/resource_tests/chemont/`.

1. A known entity GET for `BDAGIHXWWSANSR-UHFFFAOYSA-N` returned HTTP 200. The response identifies formic acid and includes kingdom, superclass, class, subclass, direct parent, four alternative parents, ancestors, substituents, external descriptors, predicted ChEBI terms, and `classification_version: "2.1"`.
2. A harmless one-molecule POST submitted aspirin SMILES (`CC(=O)Oc1ccccc1C(=O)O`) and returned HTTP 201 with query ID `13084872`. Status became `Done`; retrieval returned HTTP 200 and one valid entity. Its direct parent was Acylsalicylic acids (`CHEMONTID:0004577`), with ten alternative parents and a full ancestor list. This demonstrates acceptance of an arbitrary structure and multiple structural memberships, not multiple parents in the ontology graph.
3. `GET /tax_nodes/C0000002.json` returned an nginx HTTP 504 on one attempt and timed out with no response on another. This demonstrates endpoint/service instability during the probe.
4. HTTPS requests reset the connection in this environment. HTTP requests succeeded. The official client itself hard-codes `http://classyfire.wishartlab.com`, so transmitted novel structures are not protected by TLS when using that code as written.

The single successful submission establishes functionality, not production throughput. It is insufficient evidence for 1,000- or 200,000-molecule scalability.

## Taxonomy suitability

### Strengths

- Purely structural categories are relevant to synthetic building blocks and avoid drug-role or biological-role bias.
- Stable, machine-readable `CHEMONTID` identifiers and a complete OBO hierarchy are available.
- Every term has a definition, and many have synonyms or mappings to external vocabularies.
- The hierarchy is internally complete and acyclic and is simple to reconstruct.
- ClassyFire returns traceable direct and alternative assignments, explicit IDs, ancestor names, molecular framework, substituents, and predicted ChEBI mappings.
- The live aspirin result shows that arbitrary user-submitted structures can be accepted, rather than only looking up pre-indexed database compounds.

### Limitations and implications

- **Hierarchy structure:** ChemOnt 2.1 is a tree. It cannot itself supply class-level multiple inheritance for the project's canonical DAG. A DAG can still represent its tree edges plus separate compound-to-many-class memberships, or carefully sourced enrichment edges from another ontology.
- **Local execution:** unavailable from the acquired public materials. The OBO definitions are prose and mappings, not executable classification rules.
- **Reproducibility:** results depend on a remote, unversioned operational service, although returned records state classification version 2.1. Cache raw responses and record timestamps, inputs, IDs, and checksums.
- **Scalability:** the homepage's `<1000` guidance, client-side sleeps, lack of documented bulk service guarantees, and observed 504 make direct processing of roughly 200,000 structures risky. A controlled 20–50 molecule benchmark should measure latency and failure/retry behavior before the pilot.
- **Maintenance:** downloadable ontology version 2.1 is dated 2016; the API-client head is from 2019; the live homepage still identifies ClassyFire 1.0. The service responded in the present probe, but no evidence of a recent ontology release or active client development was found.
- **Stereochemistry:** the paper recommends chiral/isomeric structure strings because stereochemistry can change the most specific category. Standardized isomeric SMILES should be retained in submissions.
- **Preprocessing opacity:** remote preprocessing uses a proprietary historical toolkit according to the paper; exact salt, charge, tautomer, and normalization behavior is not reproducible from the public client.
- **Security:** the functional route observed here was plain HTTP, and the client hard-codes HTTP. Do not submit confidential Enamine structures without an approved secure mechanism.

## Licensing and redistribution

No standalone license file was present in the cloned API-client repository, and the downloaded OBO does not declare a license in its header. The live homepage says the web server is freely accessible, asks users to cite the 2016 paper, and states that commercial use or redistribution of the data in whole or in part requires explicit author permission and acknowledgment.

Therefore the material must **not** be described as open-license data. Public accessibility is not equivalent to permission for unrestricted redistribution. Before distributing a database containing ChemOnt content or ClassyFire-derived annotations—especially commercially—obtain clarification or permission from the authors. The repository's absence of a license also means no affirmative software reuse grant was identified.

## Recommended next resource-test controls

For the later 20–50 molecule comparison stage:

1. Submit standardized isomeric SMILES in small, uniquely labeled batches and retain request/response bodies and query IDs.
2. Measure submit latency, queue latency, retrieval latency, invalid entities, HTTP failures, and retry counts.
3. Preserve the direct path and all alternative parents as separate membership evidence; never invent multi-parent ChemOnt edges.
4. Pin the local OBO checksum and reject returned `chemont_id` values absent from that snapshot, or explicitly version any extensions.
5. Cache all successful results so subsequent pipeline runs can be deterministic without re-querying.
6. Treat predicted ChEBI terms as ClassyFire predictions, not authoritative ChEBI assertions.
7. Evaluate licensing and a secure submission channel before any full dataset or proprietary Enamine use.

## Evidence sources

- Local ChemOnt OBO and API-client code listed above.
- ClassyFire homepage and live API responses retained under `results/resource_tests/chemont/`.
- Djoumbou Feunang et al., *ClassyFire: automated chemical classification with a comprehensive, computable taxonomy*, Journal of Cheminformatics 8, 61 (2016), DOI `10.1186/s13321-016-0174-y`.

