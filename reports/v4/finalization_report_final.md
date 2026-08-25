# Phase 5 + Phase 7 finalization (final)

_Generated 20260810_120104. FINAL: acquisition complete._

## Frozen ground truth
- genuine labels: **200001**, distinct Bemis-Murcko scaffolds: **41368**
- frozen copy: `classyfire_ground_truth_frozen_20260810_120104.parquet`

## Phase 5 — scaffold split (no scaffold leakage)
- train / validation / test = 130930 / 30050 / 39021
- scaffolds spanning >1 split (leakage): **0** (must be 0)
- files: `/data01/cris/projects/DAG/data/v4_classyfire_groundtruth/train.parquet`, `validation.parquet`, `test.parquet`

## Phase 7 — held-out target-domain benchmark (TEST split, genuine labels only)
| metric | held-out test | validation | prod target |
|---|---:|---:|---:|
| n | 39021 | 30050 | — |
| superclass | 0.723943517593091 | 0.7004658901830283 | 0.90 |
| class | 0.5953994660094475 | 0.6586852271213534 | 0.75 |
| exact-leaf | 0.13021193716204096 | 0.16845257903494176 | 0.60 |
| on_path | 0.4236949334973476 | 0.5535440931780367 | — |
| any_match | 0.6295584428897261 | 0.6651247920133111 | — |

### Novelty stratification (max ECFP Tanimoto of test mol to train)
- **<0.3**: n=2914 superclass=0.4759780370624571 class=0.3787931635856296 exact=0.05765271105010295
- **0.3-0.5**: n=22933 superclass=0.7657088039070336 class=0.6321578212290503 exact=0.12763266907949244
- **0.5-0.7**: n=12610 superclass=0.711340206185567 class=0.5810928701720993 exact=0.1494052339413164
- **>=0.7**: n=564 superclass=0.5886524822695035 class=0.5230496453900709 exact=0.18085106382978725

## Verdict & PAUSE
The mapper is compared to the provisional targets (superclass ≥0.90, class ≥0.75, exact ≥0.60).
**Production annotation of the ~1.95M pool is NOT performed.** It remains gated on human
confirmation per the task. Do not scale until a maintainer reviews these held-out numbers.
