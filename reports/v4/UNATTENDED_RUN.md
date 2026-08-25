# Unattended multi-day ClassyFire acquisition — operations guide

This runs with **no interactive session**, survives crashes/reboots, keeps a **single**
respectful request stream to `classyfire.wishartlab.com`, and stops itself at the goal.

## What is installed

**crontab** (`crontab -l`):
```
*/15 * * * *  scripts/v4/watchdog.sh     # relaunch acquisition from checkpoint if not alive
0 */6  * * *  scripts/v4/report_job.sh    # rebuild GT, benchmark, regenerate coverage, log progress
```

**Daemon** `scripts/v4/acquire_ground_truth.py` (target **200,000** genuine HITs, `--rps 0.3`):
- Single stream, enforced by an exclusive **lock file** (`logs/v4/acquire.lock`) — a 2nd copy
  exits instantly, so the 15-min watchdog can never create a second stream.
- **Never re-queries** a cached InChIKey: answered keys are deleted from `acquire_queue`;
  only throttled/errored keys are retried.
- Respects the rate limit: 1 request at a time, exponential backoff + jitter on 429/5xx, and an
  **escalating global cooldown** (up to 30 min) when a batch is sustained-throttled — so we are
  never banned. Commits every 50 keys (SQLite **WAL**); kill/reboot safe.
- Stops at 200k HITs **or** pool exhaustion, writes `reports/v4/ACQUISITION_COMPLETE`, and does
  **not** annotate anything.

**Finalization** `scripts/v4/finalize_on_complete.py` (auto-triggered by the report job once the
sentinel appears): freezes the ground truth, builds a **scaffold split** (train/val/test, 0
scaffold leakage), runs the **held-out Phase 7 benchmark** (with ECFP novelty stratification),
writes `reports/v4/finalization_report_final.md` + `FINALIZED`, and **PAUSES** — no production
annotation of the 1.95M pool until a human confirms.

## How to watch it grow

```
tail -f logs/v4/progress.log          # every 6h: labels, superclasses/classes/terminals, td metrics
tail -f logs/v4/acquire_progress.log  # live: hits, done, throttled, req/s
tail -f logs/v4/acquire_stats.log     # throttle/cooldown events, daily throughput, completion
cat  reports/v4/ground_truth_coverage_analysis.md   # regenerated each report cycle
```

## Incident 2026-07-29 (found & fixed): server changed 404 → 500

For ~7 days the daemon was alive but **collected nothing** (HITs frozen at 4,372). Cause:
`classyfire.wishartlab.com` now returns **HTTP 500** for InChIKeys it cannot classify
(~45% of the pool; it used to return 404). The old code mistook 5xx for rate-limiting and
went into permanent 30-min cooldowns before ever reaching HIT keys — it was **not** a ban
(aspirin and known-HIT keys still return 200). Fixed: persistent 5xx is now a definitive
non-hit outcome `SERVER5XX` (only HTTP 429 triggers a cooldown). Acquisition resumed
immediately. If wishartlab ever restores 404/entity behaviour, `SERVER5XX` rows in the cache
can be re-probed by deleting them.

## Current state at handoff

- Genuine HITs cached so far: **4,372** (never re-queried). Queue remaining: ~1.95M.
- wishartlab is **temporarily throttling** this IP after today's setup/testing (~8k requests),
  so live throughput is briefly near zero while the daemon respects the cooldown. It resumes
  automatically as the server's rate window resets; no action needed.
- At the sustainable pace, expect the run to take up to ~2 weeks to reach 200k. An **allowlist /
  raised limit / local ClassyFire dump** from the Wishart Lab, or a **Fiehn Lab batch** run,
  would collapse this to days (see `classyfire_source_audit.md`).

## Controls

- Stop everything: `crontab -e` (remove the two lines) and `kill <pid>` of the acquire process.
- Change the goal: edit `--target` in `scripts/v4/watchdog.sh` (and kill the daemon so the
  watchdog relaunches with the new value within 15 min).
- Force a report now: `bash scripts/v4/report_job.sh`.
- The run touches **only** `data/v4_*`, `database/v4/`, `logs/v4/`, `reports/v4/`,
  `results/v4_chemont_mapper/`. V1–V3 artefacts and `prompt.md` are never modified.
