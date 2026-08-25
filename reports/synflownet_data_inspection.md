# SynFlowNet data and preprocessing inspection

## Scope and reproducibility

This report covers methodological context from the official SynFlowNet implementation only. It does not treat SynFlowNet as the molecular-data source for this project and does not imply that its Enamine catalog is publicly distributed.

- Repository: `https://github.com/mirunacrt/synflownet.git`
- Local path: `external_repositories/synflownet/`
- Inspected branch: `main`
- Commit: `574f1e148f42e0c79877318fa9d84d2552cf5025`
- Commit date: 2025-01-31T09:22:36+00:00
- Commit subject: `Merge pull request #5 from carlosinator/refactor/enamine-process`
- Inspection/download date: 2026-07-21 (UTC)
- Declared package version: `0.1` (`VERSION` contains `MAJOR="0"`, `MINOR="1"`)
- License: MIT (`LICENSE`)
- Template-file SHA-256: `5ddf9be764dbec581d257f045aa53215d54f709f01647a155e454f216ec9a72c`
- License-file SHA-256: `05e12d8c01f1ce6417745036c0a987b22fd3ecae8f1cf5a6b4fd124fc7e063ea`

No package was installed and no code in the cloned repository was modified.

## Executive findings

SynFlowNet expects building blocks as a plain text file containing one SMILES string per line. The configured default is `enamine_bbs.txt`. It expects a separately pickled NumPy compatibility tensor named `precomputed_bb_masks_enamine_bbs.pkl`. Neither artifact is present in the repository at the inspected commit. The repository includes only instructions and scripts for turning a separately obtained Enamine “Global stock” SMILES list into the input and mask.

The documented preprocessing is: retain molecules with fewer than 20 RDKit atoms, optionally randomly subsample (example: 5,000), strip salts, remove stereochemistry, round-trip through the model's graph representation and back to canonical SMILES, remove empty strings, then remove exact duplicate strings. The model therefore intentionally operates on achiral, salt-stripped representations in the documented prepared dataset. It does not retain identifiers, supplier metadata, prices, original SMILES, failure records, or mappings from original to processed records.

Compatibility is structural SMARTS matching, not an ontology. For every bimolecular reaction and both reactant positions, the precomputation checks each building block with `HasSubstructMatch` against the corresponding RDKit reactant template. The resulting tensor shape is `(2, number_of_bimolecular_reactions, number_of_building_blocks)`. The bundled `hb.txt` contains 105 SMIRKS/SMARTS reaction rules: 13 unimolecular and 92 bimolecular by reactant-template count.

## Exact files relevant to building blocks and reactions

| File | Function |
|---|---|
| `README.md` | High-level data requirements and pointer to preprocessing instructions. |
| `src/synflownet/data/building_blocks/README.md` | States that building blocks are available on request from Enamine Global stock and gives the preprocessing command order. |
| `src/synflownet/data/building_blocks/select_short_building_blocks.py` | Filters parsed molecules to `mol.GetNumAtoms() < num_atoms`; default threshold is 20 atoms. |
| `src/synflownet/data/building_blocks/subsample_building_blocks.py` | Selects either the first `n` strings or an unseeded `random.sample`; default `n=5000`, default is first records. |
| `src/synflownet/data/building_blocks/sanitize_building_blocks.py` | RDKit salt stripping, stereochemistry removal, graph round-trip, SMILES emission, and empty-string filtering. |
| `src/synflownet/data/building_blocks/remove_duplicates.py` | Exact string deduplication via `list(set(building_blocks))`. |
| `src/synflownet/data/building_blocks/precompute_bb_masks.py` | Builds and pickles the building-block/reaction-position compatibility tensor. |
| `src/synflownet/data/templates/hb.txt` | 105 reaction SMIRKS/SMARTS templates used by default. |
| `src/synflownet/tasks/config.py` | Default filenames and `sanitize_building_blocks=False` runtime default. |
| `src/synflownet/tasks/reactions_task.py` | Loads the building-block strings, templates, and pickle, then constructs the environment/context. |
| `src/synflownet/envs/synthesis_building_env.py` | Parses molecules and reactions, constructs action masks, selects compatible second building blocks, and implements forward/backward reaction actions. |
| `src/synflownet/utils/synthesis_utils.py` | Reaction wrapper, reaction application/reversal, optional runtime building-block sanitization, and fingerprints. |

No tests directory is present despite test configuration in `pyproject.toml`.

## Building-block representation and expected input

The input is a newline-delimited text file, not a TSV/SDF or a record table. Each complete line is passed to `Chem.MolFromSmiles`. The default configuration in `src/synflownet/tasks/config.py` is:

```text
building_blocks_filename = enamine_bbs.txt
precomputed_bb_masks_filename = precomputed_bb_masks_enamine_bbs.pkl
sanitize_building_blocks = False
templates_filename = hb.txt
```

`src/synflownet/tasks/reactions_task.py` resolves these under the installed source tree's `data/building_blocks/` and `data/templates/`, reads SMILES with `read().splitlines()`, and unpickles the masks. Thus ordering is semantically important: mask column `j` corresponds to building-block line/index `j`. The code does not validate IDs or a schema because there are no IDs or columns.

At runtime, the context stores the strings as a list and set, creates RDKit molecules with `Chem.MolFromSmiles`, and may compute either Morgan fingerprints or load MolGPS embeddings. The initial action (`AddFirstReactant`) can select any building block. A second reactant is limited by the compatibility mask for the selected bimolecular reaction.

The graph model supports an explicit atom vocabulary and chirality attributes, but that capability should not be confused with preservation of catalog stereochemistry: the documented building-block sanitization explicitly removes stereochemistry before training input is produced.

## Preprocessing details

### Size selection

`select_short_building_blocks.py` parses every input SMILES and retains it only when `GetNumAtoms() < 20`. This is a strict threshold, so a 20-atom molecule is excluded. `GetNumAtoms()` is the RDKit atom count of the parsed molecule (normally explicit atoms/heavy atoms in ordinary SMILES, including disconnected salt components). The script does not catch a failed parse before calling `GetNumAtoms`, so malformed SMILES can stop execution.

### Subsampling

`subsample_building_blocks.py` defaults to the first 5,000 lines. With `--random True`, it calls Python `random.sample` without setting or accepting a seed. Consequently, the random route is not reproducible unless the caller controls Python's RNG externally or modifies the script. No fingerprint-based diversity selection is provided.

### Salts and disconnected fragments

`sanitize_building_blocks.py` uses RDKit's default `SaltRemover.SaltRemover().StripMol(bb)`. This removes fragments matching RDKit's default salt definitions. It is not a general largest-organic-fragment chooser, and the code neither records which fragments were removed nor defines behavior through a project-specific salt list. Remaining disconnected fragments are not otherwise explicitly resolved. Exceptions are warned about and the affected structure is omitted from the returned list.

The optional runtime sanitization paths in `synthesis_building_env.py` and `synthesis_utils.py` apply essentially the same default salt remover. The configured default is `False`, consistent with using a pre-sanitized file produced by the standalone pipeline.

### Stereochemistry

The sanitizer calls `Chem.RemoveStereochemistry(bb)`, then converts molecule → NetworkX-like graph → molecule with `ctx.obj_to_graph` / `ctx.graph_to_obj`; the comment explicitly notes that `graph_to_obj` removes stereochemistry. Output is then generated with `Chem.MolToSmiles`. Therefore tetrahedral and bond stereo are intentionally collapsed in the documented prepared building blocks. This can merge distinct stereoisomers at the later deduplication step.

### Canonicalization and chemical normalization

The graph round-trip followed by `Chem.MolToSmiles` provides an RDKit-normalized/canonical string under the installed RDKit behavior. There is no explicit tautomer canonicalization, isotope policy, metal-disconnection policy, charge neutralization, pH model, InChI generation, or provenance mapping. RDKit parsing/sanitization occurs implicitly in `MolFromSmiles`; the pipeline does not emit a structured failure table.

### Duplicate removal

`remove_duplicates.py` uses `list(set(building_blocks))`. This removes exact duplicate processed strings and loses stable input order. Since it follows stereo removal and SMILES normalization in the documented command sequence, stereoisomers that collapse to the same processed string are duplicates. No InChIKey or tautomer-insensitive identity criterion is used, and duplicate-to-source mappings/counts are not preserved.

## Reaction templates and SMARTS rules

The only bundled template collection is `src/synflownet/data/templates/hb.txt`. It has one reaction SMARTS/SMIRKS string per line. At this commit it contains:

- 105 total templates;
- 13 one-reactant (unimolecular) templates;
- 92 two-reactant (bimolecular) templates.

The templates encode mapped reactant patterns, optional agent sections, and mapped products. They cover a broad set of transformations, including heterocycle-forming reactions, amide/ester formation, sulfonamide formation, substitutions, halogen transformations, and carbon–carbon couplings. The report deliberately does not assign reaction names not supplied by upstream; `hb.txt` contains rules but no stable template IDs, names, citations, yields, conditions, confidence, or per-rule provenance.

`Reaction` in `synthesis_utils.py` constructs RDKit reactions with `AllChem.ReactionFromSmarts`, initializes them, splits reactant templates at `.`, and supports one or two reactants. It uses template matching to test reactants and applies `RunReactants`. Product candidates are canonicalized through a SMILES round-trip and sanitized where possible. Reverse reactions are generated programmatically by swapping reactant and product templates when no separate reverse file is configured.

## Building-block/reaction compatibility

`precompute_bb_masks.py` hard-codes input `enamine_bbs.txt`, constructs `ReactionTemplateEnvContext`, and initializes:

```text
masks.shape = (2, num_bimolecular_rxns, num_building_blocks)
```

For reaction `i`, position `0` or `1`, and building block `j`, compatibility is 1 exactly when the RDKit molecule has a substructure match to that reactant SMARTS. With the current 92 bimolecular templates, an expected mask for `N` building blocks has shape `(2, 92, N)`.

During generation:

1. `ReactBi` is enabled only if the current molecule matches a reactant side and at least one catalog building block matches the complementary side.
2. `create_masks_for_bb_from_precomputed` selects the appropriate mask row depending on which side the current molecule matches and returns eligible second-building-block indices.
3. A slower `create_masks_for_bb` can compute the same logic directly by matching every building block.
4. Backward masking can require a reversed bimolecular transformation to yield at least one molecule whose canonical SMILES is exactly in the building-block set (`strict_bck_masking`).

This is deterministic rule/substructure compatibility, subject to RDKit/template/version behavior. It is not evidence that a supplier performs the reaction, nor a chemical taxonomy assignment.

## Precomputed masks: expected but not distributed

The configuration and training setup expect `precomputed_bb_masks_enamine_bbs.pkl`, but the cloned repository contains no such file. No other building-block compatibility pickle is present. `synthesis_building_env.py` tolerates absence at module import by setting the global value to `None`, but `ReactionTrainer.setup_env_context` directly opens the configured pickle; ordinary training with defaults therefore requires the user to generate/provide it.

The pickle contains only a dense compatibility array. The precompute script does not bundle a manifest, source checksum, RDKit version, template checksum, or building-block checksum. Reproducible reuse consequently requires recording those externally and ensuring exact building-block ordering.

## What is known about the Enamine dataset

The building-block README states that the source is Enamine's building-block catalog, “Global stock,” and that it is available upon request at `https://enamine.net/building-blocks/building-blocks-catalog`. The example workflow ultimately names the processed output `enamine_bbs.txt`; the example optionally downsamples to 5,000 before sanitization.

What is **not** included or established by this repository:

- no `building_blocks.txt` raw catalog;
- no `enamine_bbs.txt` processed catalog;
- no Enamine IDs, supplier rows, prices, stock flags, or catalog metadata;
- no count of the exact raw or final Enamine set in code/data;
- no precomputed Enamine mask pickle;
- no checksum or release/version of the source catalog;
- no license/redistribution statement for the absent Enamine data.

Accordingly, the repository does not supply the approximately 200,000 Enamine/SynFlowNet building blocks and cannot be used to reconstruct their exact identity. Any stated approximate count must come from the paper or external communication, not from bundled repository data.

## Implications for this taxonomy project

1. Use SynFlowNet only as methodological context. The current pilot must use the required ZINC commercial/purchasable data source.
2. Preserve both original and standardized structures and identifiers. SynFlowNet's one-string-per-line format is insufficient as the project's provenance format.
3. A future Enamine adapter can export the final standardized SMILES column as an ordered one-SMILES-per-line file and regenerate masks from that exact order.
4. Keep reaction compatibility separate from chemical-class membership. The mask describes eligibility for a reactant position, not an `is_a` relation.
5. The project standardizer should improve traceability over upstream: explicit failures, salt/fragment decisions, stereochemistry status, deterministic ordering, canonical identity, and duplicate provenance.
6. If exact behavioral compatibility with SynFlowNet is required later, pin the RDKit version and reproduce salt stripping, stereo removal, graph round-trip, template checksum, and list ordering before mask generation.

## Inspection limitations

This was a static inspection of the cloned source and bundled files at the pinned commit. No absent proprietary/request-only Enamine artifact was fabricated, no training was run, and no mask was generated because the required building-block input is absent. The reaction-rule count is based on the actual bundled template file; reaction-name interpretation is intentionally limited because upstream provides no rule labels or per-template documentation.
