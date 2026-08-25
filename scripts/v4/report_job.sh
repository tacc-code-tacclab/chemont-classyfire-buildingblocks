#!/usr/bin/env bash
# Scheduled reporting (cron, every 6h): rebuild the genuine ground-truth table from the cache,
# re-run the target-domain benchmark, regenerate the coverage report, and append a timestamped
# line to logs/v4/progress.log. Triggers finalization once acquisition is COMPLETE.
# Session-independent; safe to overlap with the running acquisition (WAL, read-only where possible).
set -u
ROOT=/data01/cris/projects/DAG
PY=/data01/cris/miniforge3/envs/ptrag_bcrabl/bin/python
LOG="$ROOT/logs/v4/report_job.log"
cd "$ROOT" || exit 1
ts() { date '+%Y-%m-%d %H:%M:%S'; }

# serialize report jobs with a lock so two never overlap
exec 9>"$ROOT/logs/v4/report_job.lock"
flock -n 9 || { echo "[$(ts)] previous report job still running; skip" >> "$LOG"; exit 0; }

echo "[$(ts)] report job start" >> "$LOG"
"$PY" "$ROOT/scripts/v4/build_ground_truth.py"      >> "$LOG" 2>&1
"$PY" "$ROOT/scripts/v4/target_domain_benchmark.py" >> "$LOG" 2>&1
"$PY" "$ROOT/scripts/v4/report_snapshot.py"         >> "$LOG" 2>&1
echo "[$(ts)] report job done" >> "$LOG"
