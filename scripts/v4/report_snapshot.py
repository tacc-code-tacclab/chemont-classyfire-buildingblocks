#!/usr/bin/env python
"""Scheduled reporting snapshot (cron, every 6h). Session-independent.

Steps:
  1. append a timestamped line to logs/v4/progress.log so the numbers can be watched grow
     (label count, distinct superclass/class/terminal, target-domain superclass/class/exact-leaf);
  2. regenerate reports/v4/ground_truth_coverage_analysis.md from live data;
  3. if acquisition is COMPLETE and not yet FINALIZED, run finalize_on_complete.py.

Assumes build_ground_truth.py and target_domain_benchmark.py were just run (report_job.sh
does that first), so classyfire_ground_truth.parquet and target_domain_benchmark.json are fresh.
"""
import json, pathlib, datetime, subprocess, sys
import pandas as pd

ROOT = pathlib.Path("/data01/cris/projects/DAG")
GT = ROOT / "data/v4_classyfire_groundtruth/classyfire_ground_truth.parquet"
BENCH = ROOT / "reports/v4/target_domain_benchmark.json"
PROGRESS = ROOT / "logs/v4/progress.log"
COVER = ROOT / "reports/v4/ground_truth_coverage_analysis.md"
SENTINEL = ROOT / "reports/v4/ACQUISITION_COMPLETE"
FINALIZED = ROOT / "reports/v4/FINALIZED"
CACHE = ROOT / "data/v4_classyfire_groundtruth/cache/classyfire_probe_cache.db"
PY = "/data01/cris/miniforge3/envs/ptrag_bcrabl/bin/python"


def main():
    df = pd.read_parquet(GT) if GT.exists() else pd.DataFrame()
    n = len(df)
    bench = json.load(open(BENCH)) if BENCH.exists() else {}
    n_super = df.classyfire_superclass.nunique() if n else 0
    n_class = df.classyfire_class.nunique() if n else 0
    n_term = df.classyfire_terminal_chemont_id.nunique() if n else 0

    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = (f"[{ts}] labels={n} superclasses={n_super} classes={n_class} terminals={n_term} "
            f"td_superclass={bench.get('superclass')} td_class={bench.get('class')} "
            f"td_exact_leaf={bench.get('exact_leaf')} td_n={bench.get('n_target_domain')}")
    with open(PROGRESS, "a") as fh:
        fh.write(line + "\n")
    print(line)

    # regenerate coverage report from live data
    superdist = df.classyfire_superclass.value_counts().to_dict() if n else {}
    dist_rows = "\n".join(f"| {k} | {v} |" for k, v in superdist.items())
    cov = f"""# Phase 4 — Target-domain coverage analysis (auto-regenerated)

_Auto-generated {ts} by `report_snapshot.py`. Rolling snapshot while Phase 2b acquisition runs._

## Snapshot
- Genuine ClassyFire building-block labels: **{n}**
- Distinct ChemOnt superclasses / classes / terminals: **{n_super} / {n_class} / {n_term}**
- Pool of unique building blocks: 1,955,032 distinct InChIKeys.

## Genuine superclass distribution

| ChemOnt superclass | n |
|---|---:|
{dist_rows}

## Representativeness (fixed finding from the Phase 2a probe, seed 20260722)

Genuine hit rate is **catalog-dependent**: enaminebb (~50% of pool) ~27%, vs 70–100% for
curated catalogs (ryan/combiblocks/princeton/achemblock). The genuine-labelled set is therefore
biased toward common, publicly-classified chemistry and under-represents Enamine's novel space.
The local mapper must be evaluated on scaffold-novel / low-similarity compounds (Phase 5 split +
Phase 7 novelty-stratified metrics), not only on the well-covered easy classes.

## Preliminary target-domain mapper metrics (n={bench.get('n_target_domain')})
- superclass agreement: {bench.get('superclass')}
- class agreement: {bench.get('class')}
- exact-leaf: {bench.get('exact_leaf')}
- on_path: {bench.get('on_path')} ; any_match: {bench.get('any_match')}

Full descriptor / ECFP / scaffold comparison of labelled vs unlabelled is produced at
finalization (Phase 5/7) once acquisition stops. See `ground_truth_acquisition_report.md`
for the gate decision and `mapper_benchmark_report.md` for the OOD comparison.
"""
    COVER.write_text(cov)

    # trigger finalization exactly once when acquisition is complete
    if SENTINEL.exists() and not FINALIZED.exists():
        print("acquisition COMPLETE -> running finalize_on_complete.py")
        subprocess.run([PY, str(ROOT / "scripts/v4/finalize_on_complete.py")], check=False)


if __name__ == "__main__":
    main()
