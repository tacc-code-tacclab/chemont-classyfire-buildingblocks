# Phase 5 + Phase 7 finalization (preview)

_Generated 20260722_133815. PREVIEW on partial data — not a completion._

## Frozen ground truth
- genuine labels: **4372**, distinct Bemis-Murcko scaffolds: **2091**


## Phase 5 — scaffold split (no scaffold leakage)
- train / validation / test = 3051 / 663 / 658
- scaffolds spanning >1 split (leakage): **0** (must be 0)
- files: `/data01/cris/projects/DAG/results/v4_chemont_mapper/finalize_preview/train.parquet`, `validation.parquet`, `test.parquet`

## Phase 7 — held-out target-domain benchmark (TEST split, genuine labels only)
| metric | held-out test | validation | prod target |
|---|---:|---:|---:|
| n | 658 | 663 | — |
| superclass | 0.78419452887538 | 0.6530920060331825 | 0.90 |
| class | 0.6550151975683891 | 0.6060606060606061 | 0.75 |
| exact-leaf | 0.135258358662614 | 0.10558069381598793 | 0.60 |
| on_path | 0.506079027355623 | 0.42232277526395173 | — |
| any_match | 0.7811550151975684 | 0.5158371040723982 | — |

### Novelty stratification (max ECFP Tanimoto of test mol to train)
- **<0.3**: n=116 superclass=0.8879310344827587 class=0.7413793103448276 exact=0.16379310344827586
- **0.3-0.5**: n=499 superclass=0.7735470941883767 class=0.6412825651302605 exact=0.13827655310621242
- **0.5-0.7**: n=43 superclass=0.627906976744186 class=0.5813953488372093 exact=0.023255813953488372

## Verdict & PAUSE
The mapper is compared to the provisional targets (superclass ≥0.90, class ≥0.75, exact ≥0.60).
**Production annotation of the ~1.95M pool is NOT performed.** It remains gated on human
confirmation per the task. Do not scale until a maintainer reviews these held-out numbers.
