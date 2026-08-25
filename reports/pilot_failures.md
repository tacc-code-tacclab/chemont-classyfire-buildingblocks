# Pilot failures and limitations

Molecular standardization reported zero failed compounds and the taxonomy pipeline completed all 1,000 rows. There were no database, graph-cycle, missing-reference, or foreign-key failures.

Twenty-six compounds matched only generic structural/elemental classes and were directly marked `DAGCHEM:0000800` (`Unresolved organic compound`). They are retained and traceable, not removed. The ruleset intentionally favors transparent recognized concepts over exhaustive or speculative classification.

The principal unresolved limitations are:

- no boron compound occurs in the acquired pilot, so boronic rules have synthetic rather than dataset validation;
- the project taxonomy is deliberately shallower than ChemOnt and does not claim ClassyFire equivalence;
- functional SMARTS can overlap by design, and edge chemotypes require continued expert review;
- ChEBI exact-identity enrichment was not included in this run;
- the source ZINC supplier snapshot is historical and current stock is unverified;

Independent QC initially failed ruleset 1.0.0 for nitro/amine confusion, contradictory phenol ancestry, inflated multifunctionality, missed tertiary aromatic amines, unconditional organic assignment, incomplete serialized-artifact validation, inflated tree metrics, and nondeterministic runtime metrics. Ruleset 1.1.0 fixes each defect and adds regressions. No critical pipeline error remains under the strengthened validation criteria. Stage 2 has not been started pending renewed independent review.
