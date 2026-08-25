# Molecular standardisation

## Outcome

The RDKit pipeline processed all 1,000 records in `data/pilot/zinc_commercial_building_blocks_1000_raw.tsv`. No record was silently discarded. All source columns and identifiers are preserved in the successful output.

| Metric | Count |
|---|---:|
| Raw records | 1,000 |
| Successfully parsed and standardized | 1,000 |
| Failed | 0 |
| Standardized duplicates removed | 0 |
| Final unique compounds | 1,000 |

The accounting invariant `raw = failed + duplicates + final unique` passes. The canonical output has 1,000 unique source IDs and 1,000 unique deduplication keys. A second independent execution produced byte-identical standardized, failure, duplicate, and metrics files.

## Implementation and versions

- Python: 3.12 in the activated `ptrag_bcrabl` Conda environment.
- RDKit: 2026.03.2.
- Core implementation: `src/standardize.py`.
- Command-line workflow: `python scripts/standardize_pilot.py`.
- Tests: `python -m unittest -v tests.test_standardize`.

No packages were installed. The standard-library `unittest` runner is used because `pytest` is not installed.

## Standardisation sequence

Each record is processed independently:

1. Validate that SMILES is non-empty.
2. Parse with RDKit and full sanitisation enabled.
3. Split disconnected components and retain the largest organic fragment using RDKit `LargestFragmentChooser(preferOrganic=True)`.
4. Apply RDKit `Cleanup`, including normalization and reionization rules.
5. Apply RDKit `Uncharger`; neutralizable charges are removed while permanent charges remain.
6. Generate the RDKit canonical tautomer. The enumerator is explicitly configured to retain tetrahedral and bond stereochemistry and then reassign stereo.
7. Re-sanitize and generate canonical non-isomeric SMILES, canonical isomeric SMILES, InChI, InChIKey, formula, molecular weight, charge, and heavy-atom count.
8. Deduplicate by standardized canonical **isomeric** SMILES, retaining the earliest input record as representative and writing every later equivalent record to a duplicate mapping.

## Explicit chemistry decisions

### Salts, mixtures, and disconnected fragments

The pipeline retains one largest organic component. All discarded component SMILES, the original fragment count, and the policy are recorded per molecule. This treats conventional counterions as non-parent material while remaining auditable. It may not be suitable for true co-crystals, coordination complexes, or intentionally multicomponent reagents; such records can be identified from `fragment_count` and reviewed. The current pilot contains only single-component input SMILES, so no fragments were removed.

### Charge normalization

RDKit cleanup/normalization is followed by `Uncharger`. The charge before and after uncharging is stored in `charge_normalisation`. Of the pilot records, 772 remained `0 -> 0`, 209 changed `+1 -> 0`, four changed `+2 -> 0`, and 15 remained `+1 -> +1`. The final set therefore contains 985 neutral structures and 15 permanently charged structures. Charge changes are explicit and reversible through the preserved original SMILES.

### Tautomers

The RDKit canonical tautomer is used so alternative tautomer drawings converge for comparison and deduplication. This is a deterministic computational convention, not a claim about the dominant experimental tautomer. The original SMILES is retained. Stereo removal is disabled in the tautomer enumerator because the default behavior was found by testing to remove specified tetrahedral stereo in a non-tautomeric center.

### Stereochemistry

Canonical isomeric SMILES and InChI retain specified stereochemistry. Potential stereo elements are reported as `fully_specified`, `partially_specified`, `unspecified`, or `no_potential_stereochemistry`. The pilot contains 388 fully specified, 16 partially specified, 12 unspecified, and 584 without potential stereo elements. Undefined stereochemistry is not invented.

### Isotopes

Explicit isotope labels are preserved and counted. None of the 1,000 pilot records contains explicit isotope labels. Unit tests verify isotope retention.

### Duplicates

The deduplication key is standardized canonical isomeric SMILES. Thus alternative input ordering, neutralizable charge forms, and canonicalized tautomers can converge, while distinct specified stereoisomers remain distinct. Duplicate removal occurs only after successful standardization. No duplicates were found in this pilot. The header-only mapping file is retained to make that result explicit.

## Outputs and fields

`data/processed/pilot_compounds_standardised.tsv` contains one row per unique standardized compound. It includes all original provenance fields and the required fields:

- `source_compound_id`, `original_smiles`, `canonical_smiles`, `isomeric_smiles`;
- `inchi`, `inchikey`, `molecular_formula`, `molecular_weight`;
- `formal_charge`, `heavy_atom_count`, `stereochemistry_status`, `sanitisation_status`.

Additional audit fields are `fragment_count`, `fragment_policy`, `removed_fragments_smiles`, `charge_normalisation`, `tautomer_policy`, `isotope_status`, and `deduplication_key`.

`data/processed/failed_compounds.tsv` always contains the required header: `compound_id`, `original_smiles`, `failure_stage`, and `failure_reason`. It has zero data rows for this run.

`data/processed/pilot_duplicate_mapping.tsv` maps every removed duplicate to its retained source compound and records the exact standardized key and reason. It has zero data rows for this run.

Machine-readable counts are stored in `results/pilot/standardisation_metrics.json`. Independent second-run artifacts are retained under `results/pilot/reproducibility_run2/`.

## Quality checks

- Six unit tests pass: valid properties, salt handling, permanent charge retention, isotope preservation, explicit invalid-SMILES failure, and tautomer convergence.
- All 1,000 output isomeric SMILES parse successfully.
- All 1,000 regenerated InChIKeys equal the stored InChIKeys.
- The second complete run is byte-identical to the canonical run.
- `failed + duplicates + final unique` exactly equals the raw count.

RDKit emitted informational warnings for charge rearrangement, proton addition/removal, undefined stereo omission, and intermediate tautomer kekulization attempts. No final molecule failed sanitisation or identifier generation. These messages arise during normalization/tautomer enumeration; the finalized structures passed the explicit parse and InChIKey round-trip checks.

## Checksums

| File | SHA-256 |
|---|---|
| Raw pilot input | `fe2a11171a4edfbd6c0d44f027ec5b8b4f5ac730001834ea72550360eb53bd58` |
| Standardized output | `047419f36835ab77da3f8b2007267de63fdcef2536920dfe86d96afad3577f90` |
| Failure output | `fe182784be67b3fcc9e4ee1a085e1b836767f77d070fd43aa6e9660a4dc3d1a8` |
| Duplicate mapping | `cb5cb4335d0896426b91c570d9ffd6dc1fad3e4fb6e07665fd905be92bcf0d97` |
| Metrics JSON | `9c3454d7dfbd9ca913699c40deaf09094065ca5963383defeb5d6dab6195d285` |
