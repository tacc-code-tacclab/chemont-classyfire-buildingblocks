# Phase 4 — Target-domain coverage analysis (auto-regenerated)

_Auto-generated 2026-08-25 12:01:08 by `report_snapshot.py`. Rolling snapshot while Phase 2b acquisition runs._

## Snapshot
- Genuine ClassyFire building-block labels: **200001**
- Distinct ChemOnt superclasses / classes / terminals: **26 / 425 / 1977**
- Pool of unique building blocks: 1,955,032 distinct InChIKeys.

## Genuine superclass distribution

| ChemOnt superclass | n |
|---|---:|
| Organoheterocyclic compounds | 80681 |
| Benzenoids | 64653 |
| Organic acids and derivatives | 18672 |
| Organic oxygen compounds | 10339 |
| Organic nitrogen compounds | 8013 |
| Phenylpropanoids and polyketides | 5604 |
| Lipids and lipid-like molecules | 5048 |
| Organosulfur compounds | 2155 |
| Organohalogen compounds | 1946 |
| Organic 1,3-dipolar compounds | 717 |
| Alkaloids and derivatives | 659 |
| Organometallic compounds | 387 |
| Nucleosides, nucleotides, and analogues | 271 |
| Hydrocarbons | 193 |
| Mixed metal/non-metal compounds | 116 |
| Organic Polymers | 113 |
| Lignans, neolignans and related compounds | 93 |
| Organic salts | 76 |
| Organophosphorus compounds | 72 |
| Homogeneous non-metal compounds | 54 |
| Hydrocarbon derivatives | 39 |
| Acetylides | 37 |
| Homogeneous metal compounds | 35 |
| Carbides | 24 |
| Allenes | 3 |
| Inorganic salts | 1 |

## Representativeness (fixed finding from the Phase 2a probe, seed 20260722)

Genuine hit rate is **catalog-dependent**: enaminebb (~50% of pool) ~27%, vs 70–100% for
curated catalogs (ryan/combiblocks/princeton/achemblock). The genuine-labelled set is therefore
biased toward common, publicly-classified chemistry and under-represents Enamine's novel space.
The local mapper must be evaluated on scaffold-novel / low-similarity compounds (Phase 5 split +
Phase 7 novelty-stratified metrics), not only on the well-covered easy classes.

## Preliminary target-domain mapper metrics (n=200001)
- superclass agreement: 0.6137669311653442
- class agreement: 0.4589389152844462
- exact-leaf: 0.09578452107739462
- on_path: 0.36867315663421685 ; any_match: 0.5633121834390828

Full descriptor / ECFP / scaffold comparison of labelled vs unlabelled is produced at
finalization (Phase 5/7) once acquisition stops. See `ground_truth_acquisition_report.md`
for the gate decision and `mapper_benchmark_report.md` for the OOD comparison.
