# Phases 6–7 — Mapper benchmark report

## Scope and honesty note

The V4 mission gates production-scale mapper work on having a **genuine target-domain
ground-truth set**. That set is being acquired now (Phase 2b daemon) and is small at this
snapshot. Accordingly:

- **Phase 6 (mapper improvement)** — the V3 61-rule mapper is preserved and reproduced as the
  baseline; substantive rule/ML expansion is **deferred** until enough genuine building-block
  labels exist to drive and validate it without overfitting a tiny set. Doing otherwise would
  tune on ~100 points and report inflated numbers — explicitly disallowed by the prompt.
- **Phase 7 (metrics)** — reported below on (a) the reproduced environmental **OOD** set and
  (b) a **preliminary target-domain** set (genuine building-block labels so far).

## Benchmark A — Environmental OOD (reproduced V3, n=1,266 organic)

Independent reproduction (`scripts/v4/reproduce_v3_benchmark.py`) — exact match to the V3
report on all metrics:

| metric | value |
|---|---:|
| on_path | 49.2% |
| any_match | 63.0% |
| exact leaf | 8.7% |
| superclass agreement | 65.3% |
| class agreement | 55.9% |
| coverage (primary) | 93.9% |

This validates the mapper's correctness and the harness, but the domain is environmental
pollutants — **not** a production-readiness basis.

## Benchmark B — Target domain (genuine building-block labels, PRELIMINARY, n=111)

`scripts/v4/target_domain_benchmark.py` runs the identical V3 mapper + canonical OBO lineage
against the genuine ClassyFire labels retrieved for **commercial building blocks**:

| metric | target domain (n=111) | OOD (n=1,266) | prod target |
|---|---:|---:|---:|
| coverage (primary) | 100% | 93.9% | — |
| on_path | 44.1% | 49.2% | — |
| any_match | 63.1% | 63.0% | — |
| exact leaf | **13.5%** | 8.7% | ≥60% |
| superclass agreement | **68.5%** | 65.3% | ≥90% |
| class agreement | 49.5% | 55.9% | ≥75% |

Per genuine superclass (target domain):

| superclass | n | super_ok | on_path | exact |
|---|---:|---:|---:|---:|
| Benzenoids | 48 | 79.2% | 50.0% | 18.8% |
| Organoheterocyclic compounds | 38 | 81.6% | 57.9% | 13.2% |
| Organic acids and derivatives | 8 | 12.5% | 0.0% | 0.0% |
| Organic nitrogen compounds | 5 | 60.0% | 20.0% | 20.0% |
| Organic oxygen compounds | 5 | 60.0% | 40.0% | 0.0% |
| Phenylpropanoids and polyketides | 4 | 0.0% | 0.0% | 0.0% |
| Lipids and lipid-like molecules | 2 | 0.0% | — | 0.0% |
| Organosulfur compounds | 1 | 0.0% | — | 0.0% |

### Reading of Benchmark B

- On the **building-block** domain the mapper is **stronger where it was designed to be**
  (Benzenoids 79% super_ok, Organoheterocyclic 82%; exact-leaf 13.5% > OOD 8.7%), because the
  61 rules were curated for building-block-relevant skeletons.
- It is **weak** exactly where the V3 report predicted: Organic acids & derivatives, oxygen,
  nitrogen, phenylpropanoids — these are the priority targets for Phase 6 rule expansion.
- **N=111 is small**: 95% CIs are wide (superclass 68.5% ≈ ±9pp). These numbers will firm up
  and shift as the daemon accumulates thousands of labels. They are reported as a preliminary,
  honest signal, **not** a production verdict.

## Verdict vs production-readiness targets

Neither benchmark meets the provisional targets (superclass ≥90%, class ≥75%, exact-leaf ≥60%).
On the target domain the gaps are: superclass 68.5% vs 90% (−21.5pp), class 49.5% vs 75%
(−25.5pp), exact-leaf 13.5% vs 60% (−46.5pp). The mapper is **not** production-ready, and the
prompt's targets are **not** lowered. Path to close the gap: accumulate genuine building-block
labels (Phase 2b), then execute Phase 6 (OBO-derived facet priority, building-block-focused
rule/ML expansion) under Phase 5 structure-aware splits and Phase 7 novelty-stratified metrics.
