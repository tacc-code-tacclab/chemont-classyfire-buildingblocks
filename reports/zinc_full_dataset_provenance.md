# Full ZINC commercial building-block source acquisition

## Result

On 2026-07-21, 29 explicit building-block catalogs were acquired from ZINC's official static 2D source-export area. The files contain **4,572,128 supplier rows**, of which **4,572,034 have at least a SMILES and supplier code** and 94 are blank or malformed. There are **2,731,017 distinct verbatim SMILES strings** across the valid-format rows. This last number is a text-level inventory only: it is not a count of chemically unique standardized structures.

The downloaded payload is 201,521,260 bytes. Every file passed SHA-256 verification. The complete machine-readable inventory, URL, index metadata, per-file counts, and hashes are in [`manifest.json`](../data/raw/zinc/full_bb_source_20260721/manifest.json); independently checkable hashes are in [`SHA256SUMS.txt`](../data/raw/zinc/full_bb_source_20260721/SHA256SUMS.txt).

## Official source and selection

The authoritative discovery point was <https://files.docking.org/catalogs/>. Complete supplier 2D exports are exposed at <https://files.docking.org/catalogs/source/> as lines containing a supplied SMILES and supplier code. This establishes that the approximately 1,523 browsable reference-SDF URLs seen during pilot discovery are sparse 3D reference coverage, not the complete accessible 2D structure universe.

The acquisition selected a source catalog only when both conditions held:

1. Its official source-export filename explicitly ended in `bb` or contained `block`.
2. The same catalog appeared in an official commercial availability group index: 3, 10, 20, 30, 40, or 50.

Group 1 (not for sale) was excluded. Explicitly BB-like source files without a matching current commercial-group listing were also excluded because purchasability could not be established from the official grouping. Where a catalog appeared in more than one group, the strongest listed availability was recorded; `molportbb` occurred in groups 10 and 30 and was assigned 30.

ZINC describes groups 30/40/50 as in stock for immediate delivery, group 20 as make-on-demand, group 10 as boutique/possibly expensive but worth asking about, and group 3 as potentially plated in libraries. These are ZINC catalog annotations, not a guarantee of present supplier stock.

## Catalog inventory

| Catalog | Group | Supplier rows | Malformed | Distinct SMILES within catalog | Source snapshot |
|---|---:|---:|---:|---:|---|
| achemblock | 40 | 63,820 | 3 | 63,297 | 2020-05-08 |
| alindabb | 40 | 7,289 | 0 | 7,289 | 2023-07-19 |
| apollobb | 40 | 24,958 | 69 | 24,803 | 2018-09-21 |
| arkbb | 40 | 31,228 | 0 | 31,056 | 2018-08-02 |
| aronisbb | 50 | 1,853 | 0 | 1,853 | 2018-09-24 |
| bidebb | 40 | 56,712 | 0 | 56,571 | 2018-08-02 |
| chbrbb | 10 | 3,506 | 0 | 3,504 | 2025-10-30 |
| chemodexbb | 40 | 34 | 0 | 33 | 2020-06-11 |
| combiblocksbb | 50 | 309,768 | 15 | 309,068 | 2024-10-21 |
| enaminebb | 50 | 1,147,314 | 0 | 1,143,609 | 2022-04-13 |
| evoblocks | 40 | 7,558 | 0 | 7,556 | 2018-08-29 |
| ibsbb | 40 | 13,248 | 0 | 13,248 | 2021-11-01 |
| iflabbb | 40 | 593 | 0 | 593 | 2022-04-12 |
| innovabb | 40 | 34,891 | 0 | 34,880 | 2024-04-17 |
| keyobb | 50 | 221,022 | 0 | 220,717 | 2022-05-20 |
| labseekerbb | 40 | 51,703 | 1 | 50,952 | 2021-10-05 |
| maybbb | 50 | 3,265 | 0 | 3,265 | 2021-11-22 |
| molportbb | 30 | 107,026 | 0 | 106,410 | 2025-10-20 |
| pharmekbb | 40 | 12,307 | 0 | 12,307 | 2018-09-11 |
| princetonbb | 40 | 121,123 | 0 | 121,123 | 2020-05-04 |
| ryanbb | 50 | 1,990,962 | 0 | 869,345 | 2018-08-02 |
| sciexbb | 30 | 33,178 | 0 | 33,178 | 2018-09-11 |
| sialbb | 50 | 117,226 | 6 | 74,018 | 2022-08-31 |
| specsbb | 40 | 9,013 | 0 | 9,013 | 2021-05-13 |
| tetrahedronbb | 40 | 92,553 | 0 | 91,814 | 2018-08-02 |
| timtecbb | 40 | 55,702 | 0 | 55,642 | 2018-09-17 |
| vitasmbb | 50 | 24,266 | 0 | 24,266 | 2022-05-20 |
| wuxibb | 40 | 7,256 | 0 | 7,241 | 2018-08-02 |
| zelinskybb | 40 | 22,754 | 0 | 22,754 | 2020-05-20 |
| **Total** |  | **4,572,128** | **94** | — | — |

Per-catalog distinct values cannot be summed because catalogs overlap. The global text inventory was computed separately and recorded in [`text_inventory.json`](../data/raw/zinc/full_bb_source_20260721/text_inventory.json).

## Reproducibility and interpretation

Acquisition is implemented in [`acquire_full_zinc_bb_sources.py`](../results/resource_tests/zinc/acquire_full_zinc_bb_sources.py). It uses the locally captured official source and availability-group indexes, bounded-retry HTTPS downloads, refuses to overwrite an existing file, and records source URLs, local paths, bytes, counts, source-index entries, and SHA-256 hashes.

The source files expose supplier identifiers rather than a guaranteed one-to-one set of ZINC IDs. Consequently, supplier rows are not reported as unique molecules. Duplicate supplier offers, repeated structures, alternate SMILES, salts, mixtures, and stereochemical variants remain possible. Parsing, chemical standardization, canonical deduplication, and classification belong to Stage 18 and were not performed here.

The source snapshots span 2018–2025, so “all accessible” means the complete explicit building-block exports discoverable through the official static indexes on the acquisition date, not a claim that every supplier record is currently orderable. The interactive ZINC interface was CAPTCHA-gated; no CAPTCHA was bypassed. The static exports required no credentials, payment, or license acceptance.

## Terms and handling

The official catalog page states that results of a ZINC search or screen may be shared, but major portions of ZINC may not be redistributed without written permission. These downloads are retained locally for research and provenance. They must not be redistributed as a bulk dataset without permission from ZINC and any applicable suppliers.

This completes acquisition only. No full-dataset processing, classification, taxonomy construction, or database population was started in this stage.
