# Full ZINC taxonomy statistics

The full commercial building-block build completed under unchanged ruleset `dag-rdkit-rules-1.1.1` with RDKit 2026.03.2. It processed 4,572,128 supplier rows and retained 1,956,542 chemically standardized unique compound instances after 5,244 total failures (94 input-format and 5,150 chemistry/identifier failures) and 2,610,342 standardized duplicates.

## Compound metrics

| Metric | Value |
|---|---:|
| Raw supplier rows | 4,572,128 |
| Valid-format rows | 4,572,034 |
| Successfully standardized rows | 4,566,884 (99.8874% of valid-format) |
| Chemistry/identifier failures | 5,150 |
| Standardized duplicates removed | 2,610,342 |
| Final unique compounds | 1,956,542 |
| Compounds with a recognized specific class | 1,907,866 (97.5121%) |
| Partially classified as unresolved organic | 48,676 (2.4879%) |
| Compounds assigned only `Chemical entity` | 1,318 |
| Compounds with multiple direct memberships | 1,955,224 (99.9326%) |
| Direct memberships | 14,146,991 |
| Inferred ancestor memberships | 1,955,224 |
| Total membership rows | 16,102,215 |

“Classified” in the machine metrics means every retained compound has at least one deterministic direct assignment. The more informative specific-class coverage excludes the 48,676 organic structures matched only by generic rules and explicitly marked unresolved; it does not exclude the 1,318 non-carbon entities assigned to `Chemical entity`.

## DAG metrics

| Metric | Value |
|---|---:|
| Chemical-class nodes | 29 |
| `is_a` edges | 30 |
| Root nodes | 1 |
| Leaf nodes | 20 |
| Maximum depth | 4 |
| Median primary-path depth | 3.0 |
| Nodes with multiple parents | 2 |
| Weakly connected components | 1 |
| Directed cycles | 0 |

The most common direct classes were Organic compound (1,955,224), Oxygen-containing organic compound (1,674,150), Nitrogen-containing organic compound (1,663,511), Multifunctional compound (1,493,765), Heterocyclic compound (1,301,962), Heteroaromatic compound (887,543), Organohalogen compound (752,506), and Amine (750,217).

The complete machine-readable metrics are in `results/full/full_metrics.json`.
