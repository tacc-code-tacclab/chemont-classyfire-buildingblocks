# Pilot database schema

The canonical pilot database is `database/chemical_taxonomy_pilot.db`, a SQLite database built exclusively by `scripts/run_pilot_taxonomy.py`. SQLite foreign keys are enabled during construction and validation. The database contains 1,000 compounds, 29 class nodes, 30 class edges, 8,309 memberships, 1,000 primary paths, and three provenance records.

## Tables

| Table | Key and purpose |
|---|---|
| `compounds` | `compound_id` primary key; source identity, original/canonical/isomeric structures, InChI/InChIKey, formula, mass, charge, commercial fields, and standardization status |
| `taxonomy_nodes` | `node_id` primary key; name, definition, source namespace/ID, node type, ruleset version, and deterministic priority |
| `taxonomy_edges` | composite key `(parent_id, child_id, relation_type)`; both endpoints reference `taxonomy_nodes`; canonical `is_a` DAG |
| `compound_membership` | composite key `(compound_id, class_id, membership_type)`; foreign keys to compounds/classes; evidence, method source, and Boolean primary marker |
| `taxonomy_paths` | one row per compound; primary leaf foreign key plus human-readable and node-ID paths |
| `provenance` | one row per resource; version, URL/local path, date, SHA-256 when applicable, and licence |

Indexes cover compound InChIKey, membership class, and edge child. `CHECK(is_primary IN (0,1))` constrains the membership flag. Validation uses `PRAGMA integrity_check` and `PRAGMA foreign_key_check`.

Compounds and chemical classes remain separate: no molecule is represented as a taxonomy node. Direct deterministic memberships use `membership_type=direct`, `source=rdkit_smarts_or_property`, and versioned rule evidence. Ancestors use `membership_type=inferred_assignment` and `source=dag_ancestor_propagation`.

The final edge schema contains only the two foreign-key endpoints, relation type, and evidence source; no compatibility or placeholder columns remain.
