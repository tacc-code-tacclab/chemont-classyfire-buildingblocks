# Independent full-output quality control

## Decision

**PASS.**

The completed full ZINC commercial-building-block outputs pass bounded independent structural, accounting, database, graph, identifier, and report-consistency checks under ruleset `dag-rdkit-rules-1.1.1`. No canonical output was modified and the 4.57-million-row chemistry pipeline was not rerun.

The machine-readable result is `results/full/independent_full_qc.json`.

## Raw and standardization accounting

The full accounting invariant closes exactly:

`4,572,128 raw = 94 malformed/blank + 5,150 chemistry failures + 2,610,342 duplicates + 1,956,542 final unique compounds`.

Equivalently, 4,566,884 successfully standardized rows equal 2,610,342 duplicates plus 1,956,542 retained unique structures. The failure TSV contains 5,244 data rows and the duplicate mapping contains 2,610,342 data rows, matching SQLite.

## Classification arithmetic

All 1,956,542 retained compounds have at least one direct deterministic assignment, so the recorded coverage is 100.0% and the unclassified count is zero. This broad coverage must be interpreted with the documented limitation that 48,676 organic compounds have only generic unresolved-organic coverage and 1,318 non-carbon records have root-only coverage.

Membership arithmetic passes: 14,146,991 direct plus 1,955,224 inferred memberships equals 16,102,215 total membership rows in both TSV and SQLite.

## Database and endpoint checks

SQLite reports `quick_check = ok`; a complete `PRAGMA foreign_key_check` returns zero violations. Independently observed table counts are:

- 4,572,128 source records;
- 5,244 failed records;
- 2,610,342 duplicate mappings;
- 1,956,542 compounds and paths;
- 29 taxonomy nodes and 30 edges;
- 16,102,215 memberships;
- 1,729,204 catalog/supplier/InChIKey-to-ZINC mapping rows;
- three provenance rows.

Membership and path export line counts match these database counts. Samples from both the beginning and end of the exports use existing `ZINCSRC` compound IDs, valid `DAGCHEM` class IDs, valid membership types, and valid primary paths. Full database foreign-key enforcement covers all endpoints rather than only the samples.

## Graph exports

The taxonomy TSV, JSON, and GraphML exports contain identical sets of 29 nodes and 30 edges. The loaded GraphML graph is acyclic and the validation records one weakly connected component. JSON metadata records RDKit 2026.03.2 and ruleset `dag-rdkit-rules-1.1.1`, consistent with the membership evidence, database provenance, validation, and reports.

## Identifier namespaces

All 1,956,542 representative primary keys use the stable source namespace `ZINCSRC:<catalog>:<line>`. Separately, 323,576 representatives have an exact official ZINC ID in the nullable `zinc_id` field, while 1,632,966 remain explicitly unmapped. These counts sum to the retained compound count and agree with the validation and limitation reports. No missing ZINC ID was fabricated.

## Required deliverables and reports

The full SQLite database, four taxonomy TSV exports, JSON, GraphML, full validation/metrics JSON, provenance report, taxonomy statistics, quality-control report, unclassified-compounds report, and limitations report are present and non-empty. Their shared counts and ruleset version agree.

## Reproducibility evidence

The implementation is local, version-pinned, order-deterministic, and records source manifests/checksums plus software and ruleset provenance. Internal database/export agreement provides strong evidence that this completed run is coherent. A second full chemistry execution was explicitly prohibited for this bounded QC, so byte-for-byte reproduction of the 4.57-million-row run was not independently regenerated here.

## Retained warnings

- Generic unresolved-organic assignments are partial deterministic coverage, not authoritative ontology classifications.
- Official ZINC-ID mapping covers 323,576 representatives; the remaining identifiers are traceable source IDs.
- Source catalogs are historical static snapshots and do not guarantee current supplier stock.

These are documented limitations rather than critical integrity failures. The independent full-output verdict is therefore PASS.
