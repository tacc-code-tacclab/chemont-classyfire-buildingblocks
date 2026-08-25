# V4 final execution summary

_Authoritative prompt: `prompt_claude_chemont_v5_resources.md`. Env: `ptrag_bcrabl`,
Python 3.12.13, RDKit 2026.03.2. All work under `/data01/cris/projects/DAG`; no legacy files
deleted or overwritten; `prompt.md` untouched. Numbers marked "(live)" grow while the Phase 2b
acquisition daemon runs — regenerate with `build_ground_truth.py`._

## Status by phase

| phase | status |
|---|---|
| 0 — reproduce V3 | ✅ exact reproduction (all 6 metrics) |
| 0.5 — connectivity/access audit | ✅ done; wishartlab reachable + rate-limited |
| Layer A — ChemOnt 2.1 | ✅ parsed, validated, cross-checked (0 mismatches vs genuine ClassyFire) |
| 1 — ZINC population | ✅ canonical V4 input materialised |
| 2a — feasibility gate | ✅ **PASS on availability**; retrieval-rate is the constraint |
| 2b — scaled retrieval | 🟢 launched, resumable daemon running (multi-day) |
| 3 — ground-truth DB | ✅ schema + validated ingestion (rebuilds as labels grow) |
| 4 — coverage analysis | ✅ rolling; key finding = catalog-dependent coverage bias |
| 5 — structure-aware splits | ⏸ deferred until enough genuine labels (design specified) |
| 6 — mapper improvement | ⏸ deferred (avoid overfitting ~100 labels); plan specified |
| 7 — metrics | ✅ OOD (reproduced) + preliminary target-domain (n=111) |

## Answers to the required final questions

**1. Exact canonical ZINC building-block source in this project?**
`database/chemical_taxonomy_zinc.db` table `compounds`, built by the prior run from the static
official ZINC building-block source exports `data/raw/zinc/full_bb_source_20260721/*.src.txt`
(29 supplier catalogs), standardised with ruleset `dag-rdkit-rules-1.1.1`. Not re-downloaded.

**2. How many unique standardised commercial/purchasable ZINC structures?**
**1,956,542** unique standardised structures (from 4,572,128 supplier rows; 2,610,342 duplicates
collapsed; 5,244 failures). **1,955,032** distinct InChIKeys; **100%** have an InChIKey;
**323,576** carry an official ZINC ID (rest keep `ZINCSRC` provenance IDs).

**3. How many genuine ClassyFire classifications recovered?**
**≥131 and growing (live)** — genuine precomputed ClassyFire records recovered by exact
InChIKey lookup, each validated against ChemOnt 2.1. (Snapshot reports use n=111.) The Phase 2b
daemon continues to accumulate toward the ≥200,000 target.

**4. Was the ≥200,000 target reached?**
**Not yet.** It is **reachable** (see Q7/feasibility) but bounded by retrieval throughput
(~10–14 days of respectful single-stream querying), so it is not reached within one session.

**5. From which exact sources were genuine labels obtained?**
`http://classyfire.wishartlab.com/entities/{InChIKey}.json` — the authoritative original
ClassyFire, returning genuine precomputed kingdom→direct_parent records with real ChemOnt IDs
(evidence level 1). Fiehn Lab batch (`cfb.fiehnlab.ucdavis.edu`) verified as a valid cross-check
source but throttles too hard for bulk use here. **No** local rules, similarity, name-matching,
or LLM labels were used as ground truth.

**6. How many distinct ChemOnt superclass/class/subclass/terminal classes represented?**
Snapshot (n=111): **8 superclasses**, **87 distinct terminal ChemOnt classes** (Benzenoids and
Organoheterocyclic compounds dominate). Grows with N.

**7. How representative is the labelled subset of the full building-block space?**
Feasibility probe (n=149, seed 20260722): pool-weighted genuine hit rate **53.7% (95% CI
45.7–61.5%)** ⇒ **~1.05M genuine labels available (CI 0.89–1.20M)**, far above 200k. **But
coverage is strongly catalog-biased**: Enamine (~50% of pool) only ~27%, vs 70–100% for curated
catalogs. So a lookup-only labelled set is biased toward common, publicly-classified chemistry
and under-represents Enamine's novel space — the mapper must be evaluated on scaffold-novel /
low-similarity compounds, not just easy classes.

**8. Held-out benchmark results (target-domain and OOD)?**
- **OOD (reproduced V3, n=1,266):** on_path 49.2%, any_match 63.0%, exact-leaf 8.7%,
  superclass 65.3%, class 55.9% — exact match to the V3 report.
- **Target-domain (preliminary, genuine BB labels, n=111):** superclass 68.5%, class 49.5%,
  exact-leaf 13.5%, on_path 44.1%, any_match 63.1%, coverage 100%. (Wide CIs; grows with N.)
  A true held-out **Phase 5** split awaits sufficient labels.

**9. Does the mapper meet production-readiness targets?**
**No.** Targets: superclass ≥90%, class ≥75%, exact-leaf ≥60%. Target-domain gaps: −21.5pp,
−25.5pp, −46.5pp. Targets not lowered.

**10. Is it scientifically justified to annotate the remaining ~1.95M now?**
**No.** The production-scaling gate is not met: genuine target-domain ground truth is not yet
assembled at scale, no held-out structure-aware evaluation exists yet, and the mapper is below
targets. Annotating 1.95M now would propagate mapper errors into the SphereFlowNet taxonomy mask.

**11. If not, what exact bottleneck remains and what user action is required?**
Bottleneck: **ClassyFire retrieval throughput** (strict IP rate limit ⇒ ~372k lookups / ~10–14
days for 200k). Either user action removes it: (a) an **allowlist / raised rate limit or a local
ClassyFire DB dump** from the ClassyFire (Wishart Lab) operators; or (b) a **Fiehn Lab ClassyFire
Batch** run on supplied building-block InChIKeys, returned to the project. Redistribution of a
major derived portion of ClassyFire also needs the operators' permission.

**12. Which files contain the final ground truth, splits, database, code, reports?**
- Ground truth: `data/v4_classyfire_groundtruth/classyfire_ground_truth.parquet`;
  DB table `database/v4/dag_v4.db:classyfire_ground_truth`; raw cache
  `data/v4_classyfire_groundtruth/cache/classyfire_probe_cache.db`.
- Canonical input: `data/v4_classyfire_groundtruth/zinc_unique_structures.parquet`.
- ChemOnt: `database/v4/{chemont_nodes.tsv,chemont_edges.tsv,chemont_lineage.json}` and
  `dag_v4.db:{chemont_nodes,chemont_edges,provenance}`.
- Splits: not yet created (Phase 5 deferred).
- Code: `scripts/v4/{parse_chemont.py, reproduce_v3_benchmark.py, feasibility_probe.py,
  acquire_ground_truth.py, build_ground_truth.py, target_domain_benchmark.py}`.
- Reports: `reports/v4/{project_inventory, v3_reproduction_report, classyfire_source_audit,
  ground_truth_acquisition_report, ground_truth_coverage_analysis, mapper_benchmark_report,
  error_analysis, final_execution_summary}.md` (+ JSON: `chemont_topology`, `gate_stats`,
  `v3_reproduction_metrics`, `target_domain_benchmark`, `layerA_crosscheck`).
- Logs: `logs/v4/agent_actions.log`, `logs/v4/{feasibility_probe,acquire}*.{out,log}`.

## How to continue (operator)

1. The acquisition daemon runs in tmux session **`dag_acquire`** (`tmux attach -t dag_acquire`).
   It is resumable/idempotent — kill and relaunch `scripts/v4/acquire_ground_truth.py` any time.
2. Periodically run `python scripts/v4/build_ground_truth.py` to re-materialise the validated
   ground-truth table, then `python scripts/v4/target_domain_benchmark.py` for updated metrics.
3. When genuine labels reach the thousands, execute Phase 5 (scaffold split) and Phase 6
   (OBO-derived facet priority + building-block-focused rule/ML expansion).
4. Pursue an allowlist / batch arrangement (Q11) to reach 200k in days instead of weeks.
