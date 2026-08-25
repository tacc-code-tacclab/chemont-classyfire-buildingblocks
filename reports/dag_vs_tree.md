# DAG versus tree projection

The corrected canonical class DAG has 29 nodes and 30 edges. Two nodes have multiple parents: boronic acid and boronate ester are children of both boron- and oxygen-containing organic compounds. Phenol is no longer asserted under the explicitly non-aromatic alcohol class.

The deterministic primary-parent projection contains 28 edges and discards two class relationships. This class-edge loss is distinct from compound membership projection. After excluding generic/bookkeeping classes and removing direct ancestors when a more specific descendant is also direct, the pilot has 2,036 meaningful maximally specific memberships; 645 compounds have multiple such memberships. A hypothetical one-membership-only representation would discard 1,110 meaningful memberships. The canonical DAG discards none.

The information loss is chemically material. For example, a fluorinated aminopyridine may retain pyridine as its primary path while losing explicit aromatic-amine and organofluorine memberships. The tree is useful for visualization and algorithms requiring one path, but it must not replace `pilot_compound_membership.tsv`.

Primary parents and primary leaves are selected deterministically by hierarchy depth, explicit rule priority, and stable ID. The projection is exported as `taxonomy/pilot_taxonomy_tree_edges.tsv`; quantitative results are in `results/pilot/dag_vs_tree_metrics.json`.
