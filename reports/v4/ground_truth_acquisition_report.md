# Phase 2a — Feasibility probe & gate decision; Phase 2b acquisition status

## Probe design

- Random, representative sample of unique standardised building blocks drawn from the
  full pool of **1,955,032 distinct InChIKeys**, **seed = 20260722** (recorded), shuffled
  across all 28 catalogs. Target sample 5,000; gate decided on the answers accumulated so far.
- Genuine **InChIKey entity lookups** against `http://classyfire.wishartlab.com/entities/{ik}.json`
  (the authoritative original ClassyFire), single respectful stream ~0.2–0.6 req/s,
  retry-on-429, **every response cached** (`data/v4_classyfire_groundtruth/cache/classyfire_probe_cache.db`),
  fully resumable/idempotent. Throttled/errored keys are left uncached and retried in a
  later pass (never counted as misses). Script: `scripts/v4/feasibility_probe.py`.

## Result (feasibility measurement)

| quantity | value |
|---|---|
| definitive answers (HIT/MISS/EMPTY) | 149 (accumulating) |
| genuine HITs | 80 |
| **genuine hit rate** | **53.7%** |
| 95% Wilson CI | **[45.7%, 61.5%]** |
| pool (distinct InChIKeys) | 1,955,032 |
| **expected available genuine labels** | **~1,049,681** (CI 893,305 – 1,202,429) |
| lookups to reach 200k (at point rate) | ~372,500 |
| hit-rate threshold to reach 200k | 10.23% |

Every genuine HIT is the **complete** ClassyFire record (kingdom/superclass/class/subclass,
intermediate_nodes, direct_parent, alternative_parents, molecular_framework,
`classification_version`) with real ChemOnt IDs. On the 58 built so far, **100% of returned
ChemOnt IDs validate against the local ChemOnt 2.1 OBO** (0 unknown/obsolete).

### Hit rate is strongly catalog-dependent (representativeness caveat)

| catalog | share of pool | probe n | hit rate |
|---|---|---:|---:|
| enaminebb | ~50.3% | 73 | **27.4%** |
| combiblocksbb | ~9.2% | 23 | 69.6% |
| ryanbb | ~21.2% | 20 | 75.0% |
| achemblock | ~3.1% | 10 | 100% |
| princetonbb | ~4.5% | 6 | 83.3% |
| sciexbb | ~1.1% | 4 | 100% |
| bidebb | ~1.7% | 4 | 75.0% |

Enamine — the largest catalog, and the most novel/proprietary chemistry — has by far the
**lowest** precomputed coverage (~27%), while curated/common commercial catalogs are
70–100%. The genuine-labelled subset will therefore be **biased toward common, publicly
classified compounds and away from Enamine's novel space**. Even so, Enamine alone
(~27% × 983k ≈ 265k) and the pool overall (~1.05M) both clear 200k. This bias is quantified
further in `ground_truth_coverage_analysis.md`.

## GATE DECISION

**Availability gate: PASS.** The extrapolated genuine yield (~1.05M, CI lower bound ~893k)
is far above the 200,000 target; the required hit-rate threshold (10.23%) is exceeded with
large margin, including within the dominant Enamine catalog.

**Binding constraint: retrieval throughput, not availability.** wishartlab enforces a strict
IP-level rate limit (~1 req/s bursts then HTTP 429; four workers @4 req/s triggered a block).
A respectful single stream sustains only ~0.2–0.6 definitive answers/second, so:

- collecting **200,000** genuine labels needs ~372,500 lookups ≈ **10–14 days** of continuous,
  respectful single-stream retrieval;
- a full ~1.95M sweep ≈ **~8 weeks**.

**Action taken:** because 2a is favourable, Phase 2b scaled retrieval is **authorised and
launched** as a long-running, resumable, checkpointed background daemon
(`scripts/v4/acquire_ground_truth.py`, single stream, shared cache, `--target 450000`).
It accumulates genuine labels over days; `scripts/v4/build_ground_truth.py` materialises the
validated ground-truth table at any checkpoint. **No fabrication or local-prediction
backfill is used** to reach the target.

**User actions that would remove the time wall (either suffices):**
1. An **allowlist / raised rate limit**, or a **local ClassyFire database dump**, from the
   ClassyFire (Wishart Lab) operators.
2. A **Fiehn Lab ClassyFire Batch** run on a supplied set of building-block InChIKeys,
   returned to the project (the route the V3 report also recommended).

Until then, retrieval continues at the sustainable pace; the ≥200k target is **reachable but
not yet reached** within a single session.
