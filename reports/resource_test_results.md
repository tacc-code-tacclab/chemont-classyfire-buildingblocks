# Taxonomy resource tests on 30 diverse pilot molecules

## Scope

Strict Step 7 tested three already-acquired resources on a reproducible subset of the standardized ZINC pilot:

- ClassyFire/ChemOnt 2.1 through the live remote service;
- ChEBI release 253 through local exact-identity matching and asserted ontology traversal;
- DrugTax 1.0.14 through its vendored local SMILES classifier.

This report compares observed behavior and evidence types. It deliberately does **not** select the canonical taxonomy strategy and does not classify the remaining 970 pilot molecules.

## Reproducible test panel

The input was `data/processed/pilot_compounds_standardised.tsv` (1,000 successfully standardized unique compounds). `results/resource_tests/run_pilot_panel_local.py` computed RDKit 2026.03.2 Morgan fingerprints (radius 2, 2,048 bits) and used `MaxMinPicker.LazyBitVectorPick` with seed `20260721` to choose 30 structures. This is a structure-diversity selection, not the first 30 records and not a hand-picked favorable set.

The panel spans 11 supplier catalogs and includes aromatic and aliphatic molecules, amines, carboxylic acids, heterocycles, halogens, sulfur, phosphorus, stereochemically specified structures, peptides/nucleotides, and multifunctional compounds. Nineteen have no potential stereochemistry, nine are fully specified, and two are partially specified. The exact panel and selection diagnostics are in `results/resource_tests/pilot_diverse_panel_30.tsv` (SHA-256 `b0172cb25598bb5041e22922050c931e872185d8c7ac752ccfda5aa0f69d7542`).

Selection completed in 0.127 seconds. Re-executing the same fingerprint/picker calculation reproduced the ordered identifiers; the script refuses to overwrite its existing evidence files.

## Results at a glance

| Criterion | ClassyFire / ChemOnt | ChEBI 253 local | DrugTax 1.0.14 local |
|---|---|---|---|
| Molecules returning a result | 30/30 | 9/30 exact identities | 30/30 accepted strings |
| Evidence meaning | Remote deterministic structure classification | Authoritative released identity and asserted ontology for exact matches only | Deterministic string heuristic; non-authoritative |
| Stable class identifiers | Yes, `CHEMONTID` | Yes, `CHEBI` | No |
| Hierarchy returned | Primary path depth 3–5 plus alternatives | Asserted multi-parent paths, depth varies | Kingdom plus broad label list only |
| Multiple memberships | 30/30 had 2–26 alternative parents | 6/9 exact matches had multiple direct `is_a` parents | 29/30 had multiple heuristic labels |
| Unresolved/failures | 0 molecular failures after rate-limited retry | 21 absent from exact identity index | 0 exceptions, but one clear kingdom error |
| Network dependency | Required | None | None for direct SMILES mode |
| Local panel time | Not local | 6.494 s OBO parse + 0.002 s lookup | 0.076 s |
| Reproducibility | Cached responses reproducible; future server rerun not guaranteed | Release- and checksum-pinned | Version/input deterministic but representation-sensitive |

These coverage numbers are descriptive for this deliberately diverse 30-molecule panel, not estimates for all 1,000 or for a future Enamine dataset.

## ClassyFire / ChemOnt live test

### Protocol and response behavior

Thirty isomeric standardized SMILES were submitted as six batches of five. The requests and responses were cached under `results/resource_tests/chemont/pilot_panel_30_20260721/`. All six submissions returned HTTP 201 and query IDs `13085163` through `13085168`. Total POST time was 15.095 seconds (median 2.567 seconds per batch; range 1.315–3.635 seconds).

The initial polling implementation had a 180-second global deadline, 10-second connection timeout, 45-second read timeout, and at most three transport attempts. The service completed the jobs, but the status/result sequence triggered 17 HTTP 429 “Limit exceeded” responses. The entire failed retrieval trace was retained rather than overwritten. There were no transport exceptions. This is direct evidence of an undocumented practical request limit.

After the initial bounded attempt stopped, the same completed query IDs—not resubmitted molecules—were retrieved sequentially with at least three seconds between requests. All six returned HTTP 200. Individual retrievals took 1.102–2.243 seconds (approximately 10.75 seconds total). Successful raw results, headers, normalized records, and the retry summary are under `results/resource_tests/chemont/pilot_panel_30_20260721_retrieval_retry/`.

### Classification content

All 30 entities were classified with `classification_version: 2.1`; no entities were invalid. Every returned InChIKey matched its standardized input InChIKey, an important check against unintended remote structure changes.

- Primary hierarchy depth was 3–5 named levels (median 4).
- Every molecule had alternative category assignments.
- Alternative-parent counts ranged from 2 to 26 (median 8.5).
- Direct-parent-plus-alternative memberships totaled 305 across 30 molecules.
- Superclasses were Organoheterocyclic compounds (16), Benzenoids (5), Organic nitrogen compounds (3), Organic acids and derivatives (3), Organosulfur compounds (1), Nucleosides/nucleotides/analogues (1), and Alkaloids and derivatives (1).
- All 30 direct-parent labels were distinct, illustrating the specificity returned for a diversity-focused panel.

Representative chemically plausible assignments include pivalic acid as Carboxylic acids, a halogen-rich aromatic as Iodobenzenes, an adenosine phosphate as Purine ribonucleoside monophosphates, a peptide as Peptides, and a quinolone building block as Quinoline carboxylic acids.

ClassyFire also returned `predicted_chebi_terms`. They are preserved in a column explicitly named `predicted_chebi_terms_non_authoritative`. They are ClassyFire predictions and **must not** be represented as authoritative ChEBI assertions.

### Practical assessment from this test

Arbitrary standardized building blocks were classified deeply and with stable class IDs, including multifunctional memberships. However, classification depends on the remote proprietary/unavailable-local engine and plain-HTTP endpoint. The observed 429 responses show that submission/poll/retrieval must be throttled, cached, restartable, and resumable. Six small batches succeeded after low-frequency retrieval; this does not establish throughput for 1,000 or approximately 200,000 molecules.

## ChEBI local exact-identity and ontology test

### Protocol

The full compressed release-253 OBO was streamed locally. Standardized InChIKeys were matched exactly to released entries. For each match, the test retained the ChEBI ID and name, direct asserted `is_a` parents, all asserted ancestors, minimum/maximum asserted path depth, and typed non-`is_a` relationships. No API or similarity matching was used.

Parsing the complete OBO took 6.494 seconds; all 30 indexed lookups together took 0.002 seconds. Results are in `results/resource_tests/chebi/pilot_panel_30_exact_ontology.tsv` (SHA-256 `7d00ea48864fedad5b17f1fc07473b3e2753ac6198aac646b5d5a09dc805a72c`).

### Observed coverage and hierarchy

Nine of 30 standardized structures (30%) had exact ChEBI identities. Six of those nine had more than one direct asserted `is_a` parent. Maximum asserted depths for matched records ranged from 11 to 15; because ChEBI is a DAG, minimum and maximum path depths can differ.

Matches included rolziracetam, pivalic acid, isaxonine, a tranylcypromine stereoisomer, glutathione/phytochelatin records, tempol, dichloroxylenol, famotidine, and rufloxacin. The glutathione InChIKey mapped to three released IDs, demonstrating that exact structure alone can correspond to multiple ChEBI records or abstraction contexts and must not be forced to one identifier without additional policy.

The 21 unmatched structures are recorded as `unresolved_exact_identity`, not “unclassifiable.” ChEBI contains relevant class concepts for many of them, but the release does not provide a local arbitrary-structure assignment algorithm. Inferring a class by similarity or by ClassyFire-predicted ChEBI terms would change the evidence type and was not done.

## DrugTax local probe

The vendored source at commit `e47fe842...` classified the same standardized isomeric SMILES without network calls. Thirty calls completed in 0.076 seconds. All input strings were accepted, 29 received multiple superclass labels, and membership counts ranged from one to eight.

Speed and apparent coverage overstate scientific performance. The aromatic organohalogen `Fc1cc(F)c(I)c(Br)c1` was labeled `inorganic / homogenous_non_metal` because DrugTax tests for uppercase `C` in raw SMILES while aromatic carbon is lowercase. It also produced suspiciously broad systematic labels: `hydrocarbon_derivatives` for 29/30, `organoheterocyclic` for 26/30, and `organopnictogens` for 22/30. For example, several ordinary nitrogen heterocycles were labeled organometallic or organopnictogen by literal-string rules.

DrugTax outputs have no stable class IDs or formal parent-child graph. The normalized file therefore marks every successful assignment as `deterministic_string_heuristic` and explicitly states that it is not authoritative ontology evidence. Output is at `results/resource_tests/drugtax/pilot_panel_30.tsv` (SHA-256 `c047491c5bbabff827dcca13b5b4441b22a929f346ccb65e86b494a3cff25b6d`).

## Cross-resource interpretation

The combined table `results/resource_tests/pilot_panel_30_resource_comparison.tsv` keeps the evidence boundary visible on every row:

- ClassyFire columns are remote structure-based assignments to ChemOnt IDs;
- ChEBI columns appear only for exact released identities and asserted ontology relationships;
- DrugTax columns are local heuristic labels without ontology authority.

The resources therefore do not have directly comparable “coverage.” ClassyFire attempts assignment for arbitrary input, ChEBI exact lookup asks whether a released entity exists, and DrugTax accepts raw strings regardless of chemical validity. A 30/30 return rate has a different scientific meaning for each method.

For the nine ChEBI-matched structures, ClassyFire supplied specific primary categories that were broadly chemically consistent with the released ChEBI names and parents. ChEBI frequently retained several asserted parents, while ChemOnt supplied one primary path plus a richer list of alternative category memberships. This difference is material to DAG design but is not, by itself, a final architecture decision.

## Failures, limitations, and reproducibility

1. **ClassyFire rate limiting:** HTTP 429 occurred during status/result retrieval. Low-frequency retry worked without resubmission. Future tests must use adaptive backoff, persistent query IDs, and response caching.
2. **Remote dependency:** cached raw ClassyFire outputs can be reproduced locally, but regenerating them depends on future service state and an unavailable-local classifier.
3. **ChEBI absence:** 21 exact-identity misses quantify release coverage only. They are not classification failures and cannot be filled authoritatively by similarity.
4. **DrugTax correctness:** zero exceptions is not zero scientific failures. One kingdom error was directly observed, alongside implausibly frequent broad labels.
5. **Panel size:** 30 molecules is appropriate for a resource gate, not for estimating final dataset coverage.
6. **Selection domain:** the panel is maximally diverse within this specific standardized ZINC pilot and inherits its acquisition limitations, including the absence of boron compounds in the available candidate pool.
7. **Timing:** wall times are host- and service-state-dependent. Local release pinning supports repeatability; network timings are observational.

No package was installed. The scripts refuse to overwrite their canonical outputs, prior ChemOnt evidence was preserved, and both the failed ClassyFire trace and successful low-frequency retry remain available for audit.

## Reproducible artifacts

- `results/resource_tests/run_pilot_panel_local.py`: deterministic panel selection, local ChEBI lookup, and local DrugTax probe.
- `results/resource_tests/run_classyfire_panel.py`: bounded small-batch submission/polling and initial failure trace.
- `results/resource_tests/normalize_classyfire_retry.py`: normalization of successful cached-query retrieval.
- `results/resource_tests/compile_resource_test_comparison.py`: evidence-aware cross-resource join.
- `results/resource_tests/pilot_panel_local_timings.json`: local timing and count metrics.
- `results/resource_tests/pilot_panel_30_resource_comparison.json`: concise comparison counts.

The normalized ClassyFire file has SHA-256 `1a4aacfc3296e4246934cfdb69aa6f0a81b388287a70df3895237da343451be5`; the combined table has SHA-256 `d75632f055153487b09fa0930ce1e97fdee7753c7780e19352d64f4aad44de80`.

