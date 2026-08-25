# Independent pilot quality control — ruleset 1.1.1

## Gate decision

**PASS — Stage 2 is authorized by the pilot quality gate.**

This was a narrow confirmation of the last remediation and existing gate evidence. No new adversarial exploration was performed, and Stage 2 was not started by this QC agent. The machine-readable result is `results/pilot/independent_qc_v3.json`.

## Chemistry confirmation

- Acetamidine, `CC(=N)N`, has no Amine, Primary amine, Secondary amine, Tertiary amine, or Aromatic amine assignment.
- Guanidine, `NC(=N)N`, has no amine or amine-subtype assignment.
- Ethylamine, `CCN`, remains a positive control for Amine and Primary amine.
- All 15 fixed taxonomy regression functions pass, including the earlier nitro, amide, sulfonamide, phenol/alcohol, multifunctional, aromatic-amine, organic-compound, boron, aldehyde/ketone, amidine, and guanidine cases.

No critical or major chemical defect remains within this prescribed regression scope.

## Artifact and database confirmation

The current validator loads and cross-compares TSV, JSON, GraphML, SQLite, paths, memberships, counts, ruleset versions, graph cycles, and foreign keys. Its fresh result is PASS.

Independent checks confirm:

- SQLite integrity is `ok` with zero foreign-key violations;
- the taxonomy graph is acyclic;
- 1,000 compounds, 29 nodes, 30 edges, 8,309 memberships, and 1,000 paths agree across artifacts;
- memberships comprise 7,309 direct and 1,000 inferred assignments;
- ruleset `dag-rdkit-rules-1.1.1` is consistent across code and outputs.

## Reports, tree analysis, and reproducibility

The current pilot results, pilot quality-control report, DAG-versus-tree report, metrics JSON, and validation JSON agree on their shared values.

The corrected tree analysis reports 2,036 meaningful maximally specific direct memberships, 645 compounds with multiple meaningful memberships, and 1,110 memberships that a hypothetical one-primary-membership representation would omit. Class-tree edge loss remains separately reported.

The two ruleset-1.1.1 reproducibility hash manifests are identical and the retained diff is empty. Canonical metrics exclude runtime-dependent values.

## Warnings retained

- No empirical boron structure occurs in this pilot; boron rules are validated synthetically.
- Twenty-six compounds have only generic coverage and an explicit unresolved-organic assignment.

These limitations are quantified and understood and do not constitute critical gate failures.

## Conclusion

All critical pilot gate requirements checked here pass, with no remaining critical or major defect. The independent result therefore sets `stage2_authorized` to `true`. Any Stage 2 acquisition and processing remains a separate execution step.
