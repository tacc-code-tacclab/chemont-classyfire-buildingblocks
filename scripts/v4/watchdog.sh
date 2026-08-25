#!/usr/bin/env bash
# Cron watchdog (every 15 min): keep the single-stream ClassyFire acquisition alive across
# crashes/reboots, independent of any interactive session or tmux. Relaunches from checkpoint.
# The daemon itself holds an exclusive lock, so even if this races it can never start a 2nd stream.
set -u
ROOT=/data01/cris/projects/DAG
PY=/data01/cris/miniforge3/envs/ptrag_bcrabl/bin/python
LOG="$ROOT/logs/v4/watchdog.log"
SENT="$ROOT/reports/v4/ACQUISITION_COMPLETE"
cd "$ROOT" || exit 1
ts() { date '+%Y-%m-%d %H:%M:%S'; }

# acquisition finished -> nothing to keep alive (report_job handles finalization)
[ -f "$SENT" ] && exit 0

# already running -> ok
if pgrep -f "scripts/v4/acquire_ground_truth.py" >/dev/null 2>&1; then
    exit 0
fi

echo "[$(ts)] acquire not running -> relaunching from checkpoint" >> "$LOG"
setsid nohup "$PY" "$ROOT/scripts/v4/acquire_ground_truth.py" \
    --target 200000 --rps wishartlab=0.4,fiehnlab=0.45 --seed 20260722 --sources wishartlab,fiehnlab \
    >> "$ROOT/logs/v4/acquire.out" 2>&1 < /dev/null &
echo "[$(ts)] relaunched pid $!" >> "$LOG"
