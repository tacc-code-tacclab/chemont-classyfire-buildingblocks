# Phase 0 — Independent reproduction of the V3 SMILES → ChemOnt benchmark

## What V3 is

The canonical V3 package (`resources/pilot_chemont_v3.zip`, sha256 `ae89521e…`) is a
local, offline SMILES → ChemOnt mapper on the **complete ChemOnt 2.1 backbone**:

- `chemont_rules.py` — **61** deterministic RDKit SMARTS/descriptor rules mapping to
  ChemOnt class *names*, with a **skeleton-first** primary-class selection (ring/skeleton
  classes primary; peripheral functional groups as alternative parents, mirroring ClassyFire).
- `lineage.py` — loads the canonical `ChemOnt_2_1.obo` and expands each assigned class to
  its full canonical `CHEMONTID` lineage from root `CHEMONTID:9999999` to leaf.
- `benchmark.py` — scores the mapper against **genuine** ClassyFire labels.

## Ground truth used by the benchmark

`data/ground_truth.csv`: **1,307 rows** of real molecules with **genuine ClassyFire**
classifications (kingdom→terminal) + SMILES, sourced from the EPA `treecompareR` package
lists **BIOSOLIDS2021** and **USGSWATER** (classified by CompTox with ClassyFire).
The benchmark filters to organic → **1,266 molecules**.

**Domain caveat (from the V3 authors, confirmed):** these are *environmental* chemicals
(pollutants, pesticides, PCBs) — a valid **out-of-domain (OOD)** correctness check, **not**
the building-block target domain, and never a basis for production readiness.

## Reproduction method

Ran the **unmodified** V3 harness (`benchmark.py`, `chemont_rules.py`, `lineage.py`) inside
a private copy (`results/v4_chemont_mapper/v3_repro/`), substituting only an in-memory
`obonet` shim built from the canonical OBO (structurally identical MultiDiGraph:
child→parent `is_a` edges, node `name`), so **no third-party package was installed** and the
extracted resources stayed pristine. Script: `scripts/v4/reproduce_v3_benchmark.py`.

## Result — exact reproduction

| metric | reproduced | V3 report | delta |
|---|---:|---:|---:|
| organic molecules | 1,266 | 1,266 | 0 |
| `on_path` (primary is correct ancestor-or-exact) | 49.2% | 49.2% | 0.0 |
| `any_match` (right class in candidate set) | 63.0% | 63.0% | 0.0 |
| exact leaf (primary == ClassyFire terminal) | 8.7% | 8.7% | 0.0 |
| superclass agreement | 65.3% | 65.3% | 0.0 |
| class-level agreement | 55.9% | 55.9% | 0.0 |
| coverage (got a primary class) | 93.9% | — | — |
| mean primary depth | 4.40 | ~4.4 | — |

All six reported metrics reproduce **exactly**. Output:
`reports/v4/v3_reproduction_metrics.json`, regenerated per-molecule detail at
`results/v4_chemont_mapper/v3_repro/data/benchmark_detail.csv` (byte-checked against the
shipped `benchmark_detail.csv`: identical `super_ok`/`class_ok` distributions —
827 True / 439 False on superclass).

## Confirmations required by Phase 0

- **Real ChemOnt 2.1 IDs & ancestor lineages**: yes — superclass/class agreement is only
  computable because `lineage.expand` walks the canonical OBO; lineages terminate at the
  single real root `CHEMONTID:9999999`.
- Genuine ground-truth molecules: **1,307** (1,266 organic scored).
- Local rules: **61**.
- Metrics verified, not trusted: see table.

## Documented discrepancies (flagged, not silently fixed)

1. Ground-truth file has **1,307** rows; the report prose says "1.305 molecole". The
   benchmark's organic-filtered N (1,266) reproduces exactly, so the headline is a minor
   prose rounding, not a data defect. Recorded, not altered.
2. Early in reproduction, an `obonet` shim bug (missing term-flush) yielded 0% superclass
   agreement while `on_path`/`any_match` still matched (those metrics don't touch the OBO
   graph). Fixed the shim; all metrics then matched. This is a reproduction-harness note,
   not a V3 defect.

## Baseline for V4

The V3 report's own verdict stands and is confirmed: the mapper is **not ready** to
annotate 1.95 M. `any_match 63%` ≫ `exact 8.7%` shows the right class is usually among the
candidates but leaf-level selection/coverage is weak — and, critically, the only genuine
labels available in V3 are **environmental/OOD**. Closing the loop requires genuine
ClassyFire labels **on building blocks** (Phase 2), which is exactly what the V4 feasibility
probe measures.
