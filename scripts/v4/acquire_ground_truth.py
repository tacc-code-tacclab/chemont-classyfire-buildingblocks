#!/usr/bin/env python
"""Phase 2b: unattended, resumable, MULTI-HOST genuine-ClassyFire acquisition.

Designed to run for days under a cron watchdog with NO interactive session.

Parallelism model: ONE stream PER HOST (wishartlab, fiehnlab). The two hosts are
independent services, so one gentle stream each respects each host's own rate limit
while ~2x-ing aggregate throughput. The work queue is partitioned by `ord % n_hosts`
so a given InChIKey is only ever sent to one host -- no key is queried twice.

Guarantees:
  * Single process (exclusive lock file) -> the cron watchdog can never start a 2nd copy.
  * Never re-queries a cached InChIKey (answered keys are deleted from the queue).
  * Per-host rate limit: 1 request at a time per host, exponential backoff + jitter on 429,
    escalating cooldown when a host is sustained-throttled. 5xx = definitive non-hit (the
    server's new "not found"), never mistaken for throttling.
  * Checkpoints every 25 keys (WAL). Kill/reboot safe: relaunch resumes from the cache.
  * Stops at --target genuine HITs OR when the pool is exhausted; writes a completion
    sentinel; annotates nothing (production stays gated on human OK).

Usage (watchdog):
  python scripts/v4/acquire_ground_truth.py --target 200000 --rps 0.4 --sources wishartlab,fiehnlab
"""
import argparse, sqlite3, time, datetime, pathlib, random, sys, os, fcntl, json, threading
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import feasibility_probe as fp

ROOT = pathlib.Path("/data01/cris/projects/DAG")
ZINC = ROOT / "database/chemical_taxonomy_zinc.db"
LOCK = ROOT / "logs/v4/acquire.lock"
SENTINEL = ROOT / "reports/v4/ACQUISITION_COMPLETE"
PROG = ROOT / "logs/v4/acquire_progress.log"
STATS = ROOT / "logs/v4/acquire_stats.log"
DEFIN = {"HIT", "MISS", "EMPTY", "NOLABEL", "SERVER5XX"}


def log(path, msg):
    with open(path, "a") as fh:
        fh.write(f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}\n")


def build_queue_if_needed(con, seed):
    con.execute("CREATE TABLE IF NOT EXISTS acquire_queue(inchikey TEXT PRIMARY KEY, ord INTEGER)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_queue_ord ON acquire_queue(ord)")
    con.commit()
    if con.execute("SELECT COUNT(*) FROM acquire_queue").fetchone()[0] == 0 and \
       not con.execute("SELECT 1 FROM sqlite_master WHERE name='queue_built'").fetchone():
        fp.log_audit(f"Phase2b: building full-pool queue seed={seed}")
        zc = sqlite3.connect(f"file:{ZINC}?mode=ro", uri=True, timeout=180)
        iks = [r[0] for r in zc.execute(
            "SELECT DISTINCT inchikey FROM compounds WHERE inchikey IS NOT NULL AND inchikey!=''")]
        zc.close()
        random.Random(seed).shuffle(iks)
        con.executemany("INSERT OR IGNORE INTO acquire_queue VALUES (?,?)",
                        [(ik, i) for i, ik in enumerate(iks)])
        con.execute("CREATE TABLE queue_built(done INTEGER)")
        con.commit()
        fp.log_audit(f"Phase2b: queue built n={len(iks)}")
    con.execute("DELETE FROM acquire_queue WHERE inchikey IN (SELECT inchikey FROM classyfire_raw)")
    con.commit()


def worker(widx, nsrc, source, rps, con, wlock, st, target):
    limiter = fp.RateLimiter(rps)
    name = source[0]
    while not st["stop"]:
        with wlock:
            if target and st["hits"] >= target:
                st["stop"] = True
                break
            batch = [r[0] for r in con.execute(
                "SELECT inchikey FROM acquire_queue WHERE ord % ? = ? ORDER BY ord LIMIT 300",
                (nsrc, widx)).fetchall()]
        if not batch:
            st["exhausted"][widx] = True
            break
        progress = 0
        consec = 0
        for ik in batch:
            if st["stop"]:
                break
            res = fp.fetch_one(ik, limiter, max_tries=2, sources=[source])
            oc = res["outcome"]
            if oc == "THROTTLED":
                consec += 1
                with wlock:
                    st["throttle"] += 1
                if consec >= 10:
                    log(STATS, f"[{name}] sustained throttle; backing off")
                    break
                continue
            consec = 0
            with wlock:
                if oc in DEFIN:
                    con.execute("INSERT OR REPLACE INTO classyfire_raw VALUES (?,?,?,?,?,?,?)",
                        (ik, res["source"], res["http_status"], oc, res["n_bytes"],
                         res["raw_json"], datetime.datetime.now().isoformat(timespec="seconds")))
                    con.execute("DELETE FROM acquire_queue WHERE inchikey=?", (ik,))
                    progress += 1
                    if oc == "HIT":
                        st["hits"] += 1
                else:
                    st["errors"] += 1
                st["done"] += 1
                if st["done"] % 25 == 0:
                    con.commit()
                    rate = st["done"] / max(1e-6, time.time() - st["t0"])
                    log(PROG, f"hits={st['hits']} done={st['done']} throttled={st['throttle']} "
                              f"errors={st['errors']} {rate:.2f}req/s")
                if target and st["hits"] >= target:
                    st["stop"] = True
        with wlock:
            con.commit()
        if progress == 0 or consec >= 10:
            st["stall"][widx] += 1
            cd = min(1800, 120 * st["stall"][widx])
            log(STATS, f"[{name}] no-progress; cooldown {cd}s (stall#{st['stall'][widx]})")
            slept = 0
            while slept < cd and not st["stop"]:
                time.sleep(5); slept += 5
        else:
            st["stall"][widx] = 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=200000)
    ap.add_argument("--rps", default="0.4",
                    help="per-host rate: a single float for all, or 'host=rate,host=rate'")
    ap.add_argument("--seed", type=int, default=20260722)
    ap.add_argument("--sources", default="wishartlab,fiehnlab")
    args = ap.parse_args()

    if SENTINEL.exists():
        print("acquisition already COMPLETE (sentinel present); nothing to do."); return

    LOCK.parent.mkdir(parents=True, exist_ok=True)
    lock_fh = open(LOCK, "w")
    try:
        fcntl.flock(lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("another acquisition instance is already running; exiting."); return
    lock_fh.write(f"pid={os.getpid()} started={datetime.datetime.now().isoformat()}\n"); lock_fh.flush()

    srcs = [(s, fp.ALL_SOURCES[s]) for s in args.sources.split(",") if s in fp.ALL_SOURCES]
    nsrc = len(srcs)
    # per-host rate: single float, or "host=rate,host=rate"
    if "=" in str(args.rps):
        rmap = {p.split("=")[0].strip(): float(p.split("=")[1]) for p in str(args.rps).split(",")}
        rps_list = [rmap.get(n, 0.4) for n, _ in srcs]
    else:
        rps_list = [float(args.rps)] * nsrc
    con = fp.init_cache()
    build_queue_if_needed(con, args.seed)

    hits = con.execute("SELECT COUNT(*) FROM classyfire_raw WHERE outcome='HIT'").fetchone()[0]
    remaining = con.execute("SELECT COUNT(*) FROM acquire_queue").fetchone()[0]
    st = {"hits": hits, "done": 0, "throttle": 0, "errors": 0, "stop": False,
          "t0": time.time(), "stall": [0] * nsrc, "exhausted": [False] * nsrc}
    wlock = threading.Lock()
    log(PROG, f"START hits={hits} queue_remaining={remaining} target={args.target} "
              f"sources={args.sources} rps_per_host={args.rps}")
    print(f"start: hits={hits} queue_remaining={remaining} sources={args.sources}", flush=True)

    threads = [threading.Thread(target=worker,
                                args=(i, nsrc, srcs[i], rps_list[i], con, wlock, st, args.target),
                                daemon=True) for i in range(nsrc)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    with wlock:
        con.commit()
    reason = "target_reached" if (args.target and st["hits"] >= args.target) else \
             ("pool_exhausted" if all(st["exhausted"]) else "stopped")
    summary = {"reason": reason, "genuine_hits": st["hits"],
               "definitive_answers": con.execute(
                   "SELECT COUNT(*) FROM classyfire_raw WHERE outcome IN "
                   "('HIT','MISS','EMPTY','NOLABEL','SERVER5XX')").fetchone()[0],
               "queue_remaining": con.execute("SELECT COUNT(*) FROM acquire_queue").fetchone()[0],
               "target": args.target, "finished_at": datetime.datetime.now().isoformat()}
    if reason in ("target_reached", "pool_exhausted"):
        SENTINEL.write_text(json.dumps(summary, indent=2))
        fp.log_audit(f"Phase2b: COMPLETE reason={reason} hits={st['hits']}")
        log(PROG, f"COMPLETE reason={reason} hits={st['hits']}")
        log(STATS, f"COMPLETE reason={reason} hits={st['hits']}")
    con.commit(); con.close()
    try:
        fcntl.flock(lock_fh, fcntl.LOCK_UN); lock_fh.close()
    except Exception:
        pass


if __name__ == "__main__":
    main()
