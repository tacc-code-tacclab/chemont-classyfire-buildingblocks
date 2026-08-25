# ZINC commercial building-block pilot provenance

## Outcome

The pilot contains exactly 1,000 unique, RDKit-readable ZINC structures drawn only from official ZINC supplier catalogs explicitly named as building-block catalogs (`*bb`, plus `evoblocks`). It is saved as:

`data/pilot/zinc_commercial_building_blocks_1000_raw.tsv`

SHA-256: `fe2a11171a4edfbd6c0d44f027ec5b8b4f5ac730001834ea72550360eb53bd58`

This is not the first 1,000 records. A capped, supplier- and physicochemical-tranche-stratified hash sample produced 1,041 unique candidates, followed by seeded Morgan-fingerprint MaxMin selection of 1,000 records.

## Current official access assessment (2026-07-21)

The interactive ZINC15 and ZINC20 sites redirected automated access to CAPTCHA verification during this work. No CAPTCHA was bypassed. The current publicly accessible official route found was the ZINC-hosted static catalog export at <https://files.docking.org/catalogs/>.

ZINC describes this endpoint as catalog-focused static exports, gives vendor-code/ZINC-ID/InChIKey mappings, and defines catalog availability groups as follows:

- groups `30`, `40`, and `50`: “in stock for immediate delivery”;
- group `20`: make-on-demand;
- group `10`: boutique compounds that may be expensive but are worth asking about;
- group `1`: not for sale.

Only explicit `*bb` catalogs and the explicitly named `evoblocks` catalog under groups 10, 40, and 50 were used. Group 1 and generic drug-like/screening subsets were not used. Most catalog files and structural exports used here carry February–March 2018 timestamps. Thus “commercial” means listed in a ZINC commercial supplier building-block catalog in that historical snapshot; it does **not** establish current stock in July 2026. Each output row states this limitation.

ZINC's static-export page also says that major portions may not be redistributed without express permission. This pilot is only 1,000 records, but downstream redistribution should still cite ZINC and review the current terms. The full-dataset stage must not assume that unrestricted redistribution is allowed.

## Official catalogs used

The final attempt inspected 17 explicit building-block catalogs:

| ZINC availability group | Catalog | Supplier label used |
|---:|---|---|
| 10 | `molportbb` | MolPort |
| 10 | `chbrbb` | ChemBridge |
| 40 | `evoblocks` | EvoBlocks |
| 40 | `arkbb` | Ark Pharm building blocks |
| 40 | `chemodexbb` | Chemodex building blocks |
| 40 | `iflabbb` | InterBioScreen building blocks |
| 40 | `innovabb` | Innovapharm building blocks |
| 40 | `labseekerbb` | LabSeeker building blocks |
| 40 | `ibsbb` | InterBioScreen building blocks |
| 40 | `apollobb` | Apollo Scientific building blocks |
| 50 | `combiblocksbb` | Combi-Blocks |
| 50 | `sialbb` | Sigma-Aldrich (SIAL) |
| 50 | `enaminebb` | Enamine building blocks, ZINC snapshot |
| 50 | `frontierbb` | Frontier Scientific building blocks |
| 50 | `keyobb` | Key Organics building blocks |
| 50 | `ryanbb` | Ryan Scientific building blocks |
| 50 | `vitasmbb` | Vitas-M building blocks |

Fifteen supplier labels are represented in the final pilot. Some attempted catalogs contributed no unique selected structure after availability, parsing, overlap, deduplication, and MaxMin selection.

URL pattern:

```text
https://files.docking.org/catalogs/<availability-group>/<catalog>/
https://files.docking.org/catalogs/<availability-group>/<catalog>/<catalog>.info.txt.gz
https://files.docking.org/catalogs/<availability-group>/<catalog>/tranches/<tranche>/<record>.ref.sdf.gz
```

The exact per-record SDF URL is retained in `source_url`. Raw catalog mappings, captured HTML indexes, checksums, and the candidate manifest are under `data/raw/zinc/`.

## Acquisition scope and Stage 2 gate

This was deliberately a pilot acquisition, not a complete-catalog download:

- at most 850 reference-SDF URLs could be selected per catalog;
- filenames within each physicochemical tranche were ordered by SHA-256 of a fixed seed plus catalog/tranche/filename, preventing “first record” sampling;
- catalogs without exposed reference-SDF tranches were skipped rather than replaced by generic ZINC compounds;
- the final capped enumeration contained only 1,523 SDF URLs across all usable catalogs;
- 1,514 SDF records parsed and nine failed;
- canonical isomeric-SMILES deduplication left 1,041 unique candidates;
- no complete supplier structure catalog and no complete ZINC building-block set was processed.

The compact `.info.txt.gz` mapping files were downloaded in full because they are needed to map a selected ZINC ID to its supplier code. Together they occupy 29,822,953 bytes compressed. They are metadata mappings rather than a processed full structure dataset. Individual structure payloads observed from the official server were generally a few kilobytes; 1,523 were requested, so the expected structural payload was on the order of a few megabytes plus HTTP overhead. The server sometimes labels plain-text SDF payloads with a `.gz` suffix; the acquisition code detects gzip magic rather than trusting the filename.

Stage 2 was not started.

## Candidate parsing and deduplication

Reference SDF records were read with RDKit 2026.03.2. For each successfully parsed structure:

- the SDF title supplied the ZINC ID;
- the official `.info.txt.gz` mapping supplied the supplier code;
- RDKit generated a non-canonical isomeric SMILES for `original_smiles`;
- RDKit generated a canonical isomeric SMILES solely as the pilot deduplication key.

The name `original_smiles` in the required output schema therefore means an isomeric SMILES generated without canonical ordering from the official ZINC SDF graph. It is not a verbatim vendor-supplied SMILES field. Stage 6 molecular standardization remains responsible for formal standardization decisions.

Nine structures failed RDKit SDF parsing/sanitization. Their exact catalogs, tranches, and URLs are recorded in `data/raw/zinc/zinc_bb_candidate_download_manifest.json`; none was silently substituted.

## Diversity selection

Reproducible implementation:

`results/resource_tests/zinc/acquire_and_select_pilot.py`

Parameters:

- fingerprint: RDKit Morgan, radius 2, 2,048 bits;
- selection: `MaxMinPicker.LazyBitVectorPick`;
- seed: `20260721`;
- input: 1,041 unique canonical-isomeric structures;
- output: 1,000 structures.

Because only 41 valid unique candidates were excluded, MaxMin improves ordering and removes the least diversity-contributing candidates but cannot create the strong downselection that a much larger pool would provide. Supplier/tranche hash stratification is therefore an important complementary diversity safeguard.

## Output columns

| Column | Meaning |
|---|---|
| `zinc_id` | ZINC identifier from the official reference SDF title |
| `original_smiles` | Non-canonical isomeric SMILES generated from the official SDF graph |
| `source` | Official ZINC static catalog export |
| `commercial_status` | Historical ZINC supplier-BB listing; current stock explicitly unverified |
| `building_block_annotation` | Exact ZINC building-block catalog short name (`*bb`, or `evoblocks`) |
| `supplier` | Human-readable supplier/catalog label |
| `supplier_code` | Vendor code from the official ZINC info mapping |
| `zinc_tranche` | ZINC two-letter physicochemical tranche directory |
| `source_url` | Exact official reference-SDF URL |
| `query_or_download_method` | Hash-stratified catalog sampling plus Morgan MaxMin |
| `download_date` | UTC acquisition date |
| `diversity_rank` | MaxMin selection order, 1–1,000 |

All required provenance fields are populated in all 1,000 rows. ZINC does not provide price, lead time, supplier stock date, or a live stock assertion in these files.

## Pilot composition and structural coverage check

The output has 1,000 unique ZINC IDs and 1,000 unique SMILES, with no missing fields. Supplier representation is:

| Supplier label | Count |
|---|---:|
| Enamine building blocks (ZINC snapshot) | 314 |
| MolPort | 119 |
| InterBioScreen building blocks | 98 |
| Combi-Blocks | 75 |
| Apollo Scientific building blocks | 57 |
| Ark Pharm building blocks | 53 |
| Key Organics building blocks | 45 |
| EvoBlocks | 41 |
| Innovapharm building blocks | 39 |
| Frontier Scientific building blocks | 38 |
| LabSeeker building blocks | 34 |
| Sigma-Aldrich (SIAL) | 24 |
| Ryan Scientific building blocks | 22 |
| Chemodex building blocks | 21 |
| Vitas-M building blocks | 20 |

A non-authoritative SMARTS coverage audit found primary amines (170), secondary amines (113), aromatic amines (232), carboxylic acids (276), alcohols (154), phenols (100), aldehydes (20), ketones (61), aryl halides (219), alkyl halides (38), heterocycles (665), heteroaromatics (448), sulfur-containing structures (258), and phosphorus-containing structures (7). These counts overlap and are only coverage diagnostics.

No boron-containing structure occurred in the 1,041 unique reference-SDF candidates, so this pilot lacks boronic acids and boronate esters. This is a documented source-exposure limitation, not evidence that ZINC supplier building-block catalogs lack them. A future acquisition route with broader 2D source-SMILES access should explicitly stratify boron chemistry before pilot validation is considered scientifically complete.

## Reproduction and artifacts

Run from the project root in the `ptrag_bcrabl` environment:

```bash
python results/resource_tests/zinc/acquire_and_select_pilot.py
```

Primary artifacts:

- `data/raw/zinc/zinc_bb_candidate_pool.tsv.gz` — 1,041 deduplicated candidates;
- `data/raw/zinc/zinc_bb_candidate_download_manifest.json` — parameters, counts, checksums, and nine failures;
- `data/raw/zinc/zinc_pilot_raw_sha256_20260721.txt` — raw and output checksum inventory;
- `data/pilot/zinc_commercial_building_blocks_1000_raw.tsv` — selected pilot.

The acquisition script must not be rerun over these paths without first preserving the current versions according to the project safety policy.

## Limitations and interpretation

1. The publicly reachable catalog snapshot is stale. Supplier listing is evidence of historical purchasability, not current inventory.
2. The browsable reference-SDF coverage is much smaller than the mapping tables and varies by catalog. This biases the accessible pool.
3. The pilot includes a ZINC-hosted Enamine building-block catalog snapshot but is not the requested SynFlowNet Enamine dataset and must not be represented as such.
4. Supplier codes are identifiers, not proof of availability, price, or delivery time.
5. The pilot has no boron chemistry and only seven phosphorus-containing structures.
6. The final 1,000 are selected from only 1,041 unique candidates, limiting MaxMin's leverage.
7. ZINC's redistribution restriction must be considered before sharing major portions or proceeding to a full download.

Despite these limitations, the file is a defensible ZINC-only, supplier-building-block pilot for pipeline engineering. Chemical-domain validation should explicitly account for the missing boron class before the Stage 1 pass gate.
