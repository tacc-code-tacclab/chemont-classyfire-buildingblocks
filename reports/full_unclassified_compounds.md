# Full unresolved and failed compounds

No retained standardized compound lacks a direct taxonomy membership. However, “membership exists” must not be confused with specific chemical resolution.

## Partially classified retained compounds

48,676 of 1,956,542 retained compounds (2.4879%) matched generic organic/elemental rules but no recognized specific structural rule. They are explicitly assigned `DAGCHEM:0000800` (`Unresolved organic compound`). They remain in the database and membership export with traceable deterministic evidence. They are not presented as authoritative ontology assignments.

An additional 1,318 retained records contain no carbon after the validated standardization semantics and are assigned only the root `Chemical entity`. They are retained rather than silently discarded because source catalogs labeled them as building-block records.

## Failed source records

The failure table contains 5,244 source rows:

| Failure stage | Rows |
|---|---:|
| SMILES parsing | 3,801 |
| RDKit standardization | 1,015 |
| InChI/InChIKey generation | 334 |
| Malformed or blank source row | 94 |

The largest catalog contributions were `ryanbb` (1,886), `combiblocksbb` (1,653), `sialbb` (645), `keyobb` (270), `molportbb` (179), `arkbb` (170), and `tetrahedronbb` (145). Every failure retains the stable line-based source ID, original supplied SMILES/text, catalog, line number, failure stage, and RDKit reason in `data/processed/full_failed_compounds.tsv` and the database `failed_compounds` table.

These failures represent 0.1147% of raw supplier rows. No failed record was silently removed or substituted.
