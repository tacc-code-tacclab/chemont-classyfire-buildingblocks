# DrugTax investigation

## Executive finding

DrugTax 1.0.14 is a small, fully local Python heuristic classifier for one chemical kingdom and a non-exclusive set of 31 broad superclass labels. It is neither a downloadable taxonomy/ontology nor a local implementation of ClassyFire/ChemOnt. Its direct-SMILES path makes no API calls and does not use ClassyFire. The optional drug-name path uses `pubchempy` to query PubChem only to obtain an isomeric SMILES, after which the same local string rules run.

DrugTax is fast and can provide exploratory coarse features, but it is not suitable as the authoritative taxonomy backbone for commercial building blocks. It supplies no stable class identifiers, definitions table, parent-child graph, deeper hierarchy, provenance per assignment, or structural parsing. Direct tests found chemically serious representation-dependent errors and acceptance of malformed strings.

## Sources and captured version

| Item | Value |
|---|---|
| Authoritative repository | <https://github.com/MoreiraLAB/DrugTax> |
| Local clone | `external_repositories/drugtax/` |
| Commit | `e47fe8420344658520880c0a0e49c995edc71caa` |
| Commit date | 2022-10-27 16:52:26 +01:00 |
| Package version | 1.0.14 (`pyproject.toml`) |
| PyPI | <https://pypi.org/project/DrugTax/> |
| Paper | Preto, Correia & Moreira, *J Cheminform* 14, 73 (2022), <https://doi.org/10.1186/s13321-022-00649-w> |
| Licence | GNU GPL v3.0 (`LICENSE`; SPDX GPL-3.0 in GitHub metadata) |
| Repository maintenance | Not archived, but the last source push and commit were 2022-10-27; no tags exist in the remote as checked 2026-07-21. This is evidence of inactivity, not proof of abandonment. |
| Captured live metadata | `data/external/drugtax/github_repository_metadata_20260721.json` |

The repository includes its own 1.0.14 wheel and source archive. Checksums:

| Artifact | SHA-256 |
|---|---|
| `LICENSE` | `3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986` |
| `pyproject.toml` | `c331df4f36fb9bd648bc90a3fd10229c72aea958b8c1a802895203050862d628` |
| `dist/drugtax-1.0.14-py3-none-any.whl` | `16f524ba2252caeff4bb7c693843676c0a9dae72ac04b95c5a9da43f195f7758` |
| `dist/drugtax-1.0.14.tar.gz` | `77ca97726098c54dd291f90e5dc506d67e3d712720b616082343727abd1af786` |
| Captured GitHub metadata | `210a8513042a3fdcdc0d70ec65a2558d9b206818ad80a83ffe18254a3bac56c6` |

No separate associated classification database was required or found. The classification knowledge is embedded directly in `src/DrugTax/drugtax.py` and element lists in `variables.py`.

## Actual implementation

The public interface centers on `DrugTax(input_smile)`. Inspection of `src/DrugTax/drugtax.py` shows that it:

1. Counts literal characters and strips selected SMILES punctuation with regular expressions.
2. Decides organic versus inorganic by testing whether uppercase `"C"` occurs in the raw input, except for a short exact-string exclusion list.
3. Finds rings by splitting the raw string on sequential ring digits.
4. Applies literal substring and character-count rules for up to 26 organic or five inorganic superclass labels.
5. Returns all matched superclass names as an untyped Python list; `__repr__` renders their sorted names.

Examples of rules include literal `C(=O)O` for a carboxyl group, carbon/element adjacency strings for organohalogens and organometallics, and charge-symbol counts for cation/anion/zwitterion labels. It does not call RDKit or another chemistry toolkit, parse a molecular graph, sanitize a structure, canonicalize equivalent SMILES, or reject invalid SMILES.

`src/DrugTax/superclasses.py` provides sequential bulk wrappers:

- `smiles_list` and CSV-file modes are local and network-independent.
- `drugs_list` calls `pubchempy.get_compounds(name, 'name')`, requiring PubChem/network availability; a broad bare `except` silently omits failures.
- Bulk output stores a rendered multi-line taxonomy string and a frequency table, rather than stable normalized class records.

`plotting.py` provides optional UpSet plotting. It does not change classification.

## Relationship to ClassyFire and ChemOnt

The paper says DrugTax extends the classification concepts explored by ClassyFire, and several broad label names overlap with ChemOnt superclasses. Code inspection found no ClassyFire URL, client, API request, ChemOnt ontology file, ClassyFire class ID, or imported ClassyFire dependency. Therefore:

- **Dependency on ClassyFire at runtime:** none.
- **Reuse of the complete ClassyFire classifier/rules:** no.
- **ChemOnt hierarchy or stable identifiers returned:** no.
- **ClassyFire API limits:** not applicable to DrugTax's local SMILES mode.
- **External API dependency:** PubChem only in the optional name-to-SMILES convenience mode.

DrugTax labels should consequently be recorded as deterministic heuristic assignments from DrugTax, not authoritative ChemOnt/ClassyFire assignments.

## Taxonomy-resource criteria

| Criterion | Finding |
|---|---|
| Purpose | Coarse taxonomic labels plus simple explainable string features and overlap plots |
| Taxonomy vs ontology | A fixed label set/rule classifier; not a formal downloadable ontology |
| Hierarchy | Two explicit ranks in practice: kingdom and broad superclass |
| Number of levels | 2 |
| Multiple class membership | Yes, multiple superclasses may be appended |
| Multiple inheritance | Not represented; there is no class graph |
| Parent-child relationships | Only implicit kingdom-to-superclass grouping in code/docstrings; no edge export |
| Stable class identifiers | None; lowercase label strings only |
| Definitions | Informal docstrings, not a structured class dictionary |
| Full taxonomy download | No separate taxonomy artifact |
| Arbitrary novel molecules | Accepts any input string, but does not validate it; correctness depends on exact SMILES spelling |
| Local classification | Yes for direct SMILES/file modes |
| Bulk processing | Yes, sequential Python loop; no multiprocessing or vectorization |
| API requirement | None for SMILES; PubChem required for drug-name resolution |
| Reproducibility | Deterministic for identical input/version; weak across alternative valid SMILES representations |
| Scalability | Computationally fast, but scientific error is the limiting factor |
| Licence/redistribution | GPL-3.0; redistribution/modification must comply with GPL obligations |

## Direct resource test

The reproducible probe is `results/resource_tests/drugtax/run_drugtax_probe.py`. It imports the cloned source without installing or modifying the environment. Outputs are:

- `results/resource_tests/drugtax/representative_smiles_results.tsv`
- `results/resource_tests/drugtax/benchmark.json`

On Python 3.12.13, 1,900 local classifications completed in 3.27 seconds (about 580 classifications/second on this host). This synthetic short run suggests CPU throughput alone would be adequate for approximately 200,000 records (rough extrapolation: minutes), although a realistic standardized dataset and end-to-end I/O benchmark are still required. The implementation is single-process and emits progress every 100 records.

Important observed failures include:

- aromatic aniline `Nc1ccccc1`, phenol `Oc1ccccc1`, pyridine `n1ccccc1`, thiophene `c1ccsc1`, and phenylboronic acid `OB(O)c1ccccc1` were labeled inorganic because aromatic carbon is lowercase and the kingdom test searches uppercase `C`;
- Kekulé aniline `NC1=CC=CC=C1` was instead labeled organic and even `organoheterocyclic`, demonstrating representation-dependent output;
- `[Na+].[Cl-]` was labeled organic because the `C` in `Cl` satisfies the raw uppercase-carbon test;
- carbon dioxide written `O=C=O` was labeled organic although the exact exclusion list only includes `C(=O)=O`;
- the malformed text `not_a_smiles` was accepted and labeled inorganic/homogeneous non-metal;
- Python 3.12 emitted invalid-escape `SyntaxWarning`s, although execution completed.

These are not edge cases for a building-block corpus: aromatic and halogenated compounds are expected to be common. Canonicalization alone cannot guarantee correctness because common canonical aromatic SMILES use lowercase atoms, and DrugTax does not consume a parsed graph.

## Dependency and packaging assessment

The code imports pandas for bulk tables, matplotlib and UpSetPlot inside plotting functions, and PubChemPy only inside name lookup. Core classification itself uses the Python standard library. The README recommends pinned historical versions (`upsetplot==0.6.0`, `pandas==1.1.5`, `matplotlib==3.3.4`, `pubchempy==1.0.4`). However, `pyproject.toml` declares no standard runtime `dependencies`; its `[tool.poetry] packages` list incorrectly names third-party packages and duplicates pandas. A plain package install may therefore omit required optional dependencies. No test suite or continuous-integration configuration is present.

No packages were installed for this investigation. Existing pandas was sufficient; optional UpSetPlot and PubChemPy were absent and were not needed for the local classifier probe.

## Suitability decision

DrugTax should **not** be used as the canonical taxonomy or authoritative classifier for this project. It cannot provide the required stable class nodes, hierarchy edges, definitions, deep paths, or traceable ontology assignments, and direct testing revealed systematic failures in core target chemistry.

At most, retain it as an explicitly non-authoritative exploratory/helper feature generator after professional RDKit standardization, and only if its outputs are independently validated. Even in that role, a graph-aware SMARTS/RDKit rule layer would be scientifically preferable. ChemOnt/ClassyFire and ChEBI must be evaluated independently for the canonical taxonomy architecture; DrugTax does not make either resource locally executable.

## Reproduction

From the project root and active `ptrag_bcrabl` environment:

```bash
python results/resource_tests/drugtax/run_drugtax_probe.py
```

The probe deliberately performs no network calls. The GitHub metadata capture date is 2026-07-21; repository and package source artifacts are pinned by commit and checksums above.
