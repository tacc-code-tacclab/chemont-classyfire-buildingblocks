#!/usr/bin/env python
"""Phase 2a MANDATORY feasibility gate: genuine ClassyFire InChIKey hit-rate probe.

Draws a random, representative probe of unique standardised ZINC building blocks
(fixed seed) and looks each InChIKey up against the reachable authoritative
ClassyFire entities endpoints. Measures the genuine hit rate, which is the single
number that decides whether >= 200k genuine labels are reachable from this host.

Resumable + idempotent: every response (hit or miss) is cached in a SQLite cache
keyed by InChIKey; a structure is never queried twice. Conservative rate limiting
with exponential backoff. No throttling bypass. Kill and re-run to resume.

Usage:
  python scripts/v4/feasibility_probe.py --n 5000 --seed 20260722 --rps 4 --workers 4
"""
import argparse, sqlite3, json, time, threading, sys, os, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
import random, pathlib, datetime

ROOT = pathlib.Path("/data01/cris/projects/DAG")
ZINC_DB = ROOT / "database/chemical_taxonomy_zinc.db"
CACHE_DB = ROOT / "data/v4_classyfire_groundtruth/cache/classyfire_probe_cache.db"
AUDIT = ROOT / "logs/v4/agent_actions.log"
PROGRESS = ROOT / "logs/v4/feasibility_probe_progress.log"

ALL_SOURCES = {
    # name -> base_url. wishartlab: authoritative original ClassyFire, tolerant at
    # low rps, clean 404 on genuine miss. fiehnlab: secondary batch cache, throttles
    # hard (429) so it is unsuitable for a large probe; used only for cross-check.
    "wishartlab": "http://classyfire.wishartlab.com",
    "fiehnlab":   "https://cfb.fiehnlab.ucdavis.edu",
}
SOURCES = [("wishartlab", ALL_SOURCES["wishartlab"])]  # overridden in main() from --sources


def log_audit(msg):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(AUDIT, "a") as fh:
        fh.write(f"[{ts}] {msg}\n")


def init_cache():
    con = sqlite3.connect(CACHE_DB, timeout=120, check_same_thread=False)
    # WAL: durable, and lets the reporting job read while the daemon writes.
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute("PRAGMA busy_timeout=120000")
    con.execute("""CREATE TABLE IF NOT EXISTS classyfire_raw(
        inchikey TEXT PRIMARY KEY, source TEXT, http_status INTEGER,
        outcome TEXT, n_bytes INTEGER, raw_json TEXT, fetched_at TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS probe_sample(
        inchikey TEXT PRIMARY KEY, compound_id TEXT, catalog TEXT,
        molecular_weight REAL, seed INTEGER)""")
    con.commit()
    return con


class RateLimiter:
    def __init__(self, rps):
        self.min_interval = 1.0 / rps
        self.lock = threading.Lock()
        self.next_t = 0.0
    def wait(self):
        with self.lock:
            now = time.monotonic()
            t = max(now, self.next_t)
            self.next_t = t + self.min_interval
        sleep = t - time.monotonic()
        if sleep > 0:
            time.sleep(sleep)


def classify_body(body):
    if not body or not body.strip() or body.strip() in ("{}", "null", "[]"):
        return "EMPTY", None
    try:
        j = json.loads(body)
    except Exception:
        return "NONJSON", None
    if isinstance(j, dict) and (j.get("class") or j.get("superclass") or
                                j.get("kingdom") or j.get("direct_parent")):
        return "HIT", j
    return "NOLABEL", j


def _backoff(attempt, base=4.0, cap=180.0):
    """Exponential backoff with full jitter (seconds), capped."""
    return min(cap, base * (2 ** attempt)) * (0.5 + 0.5 * random.random())


def fetch_one(ik, limiter, max_tries=6, sources=None):
    """Try each source until a definitive answer. Returns dict for cache row.

    429 and 5xx are transient -> exponential backoff with jitter, then retry.
    404 is a genuine MISS. Anything still unresolved after retries is returned as a
    non-definitive outcome (THROTTLED/ERR) so the caller can DEFER (leave uncached)
    and try again later -- never counted as a miss, so we are never throttled or banned.

    `sources` (list of (name, base_url)) overrides the global SOURCES -- used to bind a
    worker to a single host for parallel multi-host acquisition.
    """
    last = None
    for src_name, base in (sources if sources is not None else SOURCES):
        url = f"{base}/entities/{ik}.json"
        throttled = False
        for attempt in range(max_tries):
            limiter.wait()
            req = urllib.request.Request(url, headers={
                "Accept": "application/json",
                "User-Agent": "DAG-chemont-research/1.0 (academic; respects rate limits)"})
            try:
                with urllib.request.urlopen(req, timeout=45) as r:
                    body = r.read().decode("utf-8", "replace")
                outcome, j = classify_body(body)
                if outcome == "HIT":
                    return dict(source=src_name, http_status=200, outcome="HIT",
                               n_bytes=len(body), raw_json=body)
                last = dict(source=src_name, http_status=200, outcome=outcome,
                            n_bytes=len(body), raw_json=body if outcome != "HIT" else None)
                break
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    last = dict(source=src_name, http_status=404, outcome="MISS",
                                n_bytes=0, raw_json=None)
                    break
                if e.code == 429:
                    # genuine rate-limit -> back off and retry; this is the ONLY throttle signal
                    throttled = True
                    time.sleep(_backoff(attempt))
                    continue
                if 500 <= e.code < 600:
                    # wishartlab returns 5xx for InChIKeys it cannot classify / has no entity
                    # for (it replaced the old 404, ~45% of the pool). This is a stable, definitive
                    # non-hit -- NOT a throttle (else the daemon stalls). No retry: keeps throughput
                    # high. (If the server's not-found behaviour ever reverts, SERVER5XX rows can be
                    # re-probed by clearing them from the cache.)
                    last = dict(source=src_name, http_status=e.code, outcome="SERVER5XX",
                                n_bytes=0, raw_json=None)
                    break
                last = dict(source=src_name, http_status=e.code, outcome=f"HTTP{e.code}",
                            n_bytes=0, raw_json=None)
                break
            except Exception:
                time.sleep(_backoff(attempt, base=2.0, cap=60.0))
                continue
        else:
            # exhausted retries without a definitive answer on this source
            if throttled:
                last = dict(source=src_name, http_status=429, outcome="THROTTLED",
                            n_bytes=0, raw_json=None)
            else:
                last = last or dict(source=src_name, http_status=0, outcome="ERR",
                                    n_bytes=0, raw_json=None)
        if last and last["outcome"] == "HIT":
            return last
    return last or dict(source="none", http_status=0, outcome="NO_ANSWER", n_bytes=0, raw_json=None)


def build_sample(con, n, seed):
    existing = con.execute("SELECT COUNT(*) FROM probe_sample WHERE seed=?", (seed,)).fetchone()[0]
    if existing >= n:
        rows = con.execute("SELECT inchikey, compound_id, catalog FROM probe_sample WHERE seed=?",
                           (seed,)).fetchall()
        return rows
    log_audit(f"Phase2a: building sample n={n} seed={seed} from {ZINC_DB.name}")
    zc = sqlite3.connect(f"file:{ZINC_DB}?mode=ro", uri=True, timeout=120)
    allrows = zc.execute(
        "SELECT compound_id, inchikey, catalog, molecular_weight FROM compounds "
        "WHERE inchikey IS NOT NULL AND inchikey!=''").fetchall()
    zc.close()
    # dedup by inchikey (keep first), then deterministic random sample
    seen = {}
    for cid, ik, cat, mw in allrows:
        if ik not in seen:
            seen[ik] = (cid, cat, mw)
    keys = list(seen.keys())
    rng = random.Random(seed)
    rng.shuffle(keys)
    chosen = keys[:n]
    con.executemany("INSERT OR IGNORE INTO probe_sample VALUES (?,?,?,?,?)",
                    [(ik, seen[ik][0], seen[ik][1], seen[ik][2], seed) for ik in chosen])
    con.commit()
    log_audit(f"Phase2a: sample built, {len(chosen)} unique inchikeys "
              f"(pool of {len(keys)} distinct inchikeys)")
    return [(ik, seen[ik][0], seen[ik][1]) for ik in chosen]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=20260722)
    ap.add_argument("--rps", type=float, default=4.0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--sources", default="wishartlab",
                    help="comma list from: wishartlab,fiehnlab")
    args = ap.parse_args()

    global SOURCES
    SOURCES = [(s, ALL_SOURCES[s]) for s in args.sources.split(",") if s in ALL_SOURCES]

    con = init_cache()
    sample = build_sample(con, args.n, args.seed)
    sample_iks = [r[0] for r in sample]

    done = set(r[0] for r in con.execute("SELECT inchikey FROM classyfire_raw").fetchall())
    todo = [ik for ik in sample_iks if ik not in done]
    log_audit(f"Phase2a: probe start n={len(sample_iks)} already_cached={len(done)} "
              f"todo={len(todo)} rps={args.rps} workers={args.workers}")
    print(f"probe: sample={len(sample_iks)} cached={len(done)} todo={len(todo)}", flush=True)

    limiter = RateLimiter(args.rps)
    wlock = threading.Lock()
    DEFINITIVE = {"HIT", "MISS", "EMPTY", "NOLABEL"}
    counters = {"HIT": 0, "MISS": 0, "deferred": 0, "done": 0}
    t0 = time.time()

    def work(ik):
        res = fetch_one(ik, limiter)
        with wlock:
            counters["done"] += 1
            if res["outcome"] in DEFINITIVE:
                # only cache definitive answers; throttled/errored keys are left
                # uncached so a later pass retries them (self-healing, idempotent).
                con.execute(
                    "INSERT OR REPLACE INTO classyfire_raw VALUES (?,?,?,?,?,?,?)",
                    (ik, res["source"], res["http_status"], res["outcome"],
                     res["n_bytes"], res["raw_json"],
                     datetime.datetime.now().isoformat(timespec="seconds")))
                if res["outcome"] == "HIT":
                    counters["HIT"] += 1
                elif res["outcome"] == "MISS":
                    counters["MISS"] += 1
            else:
                counters["deferred"] += 1
            if counters["done"] % 20 == 0:
                con.commit()
                rate = counters["done"] / max(1e-6, time.time() - t0)
                msg = (f"progress {counters['done']} HIT={counters['HIT']} "
                       f"MISS={counters['MISS']} deferred={counters['deferred']} "
                       f"{rate:.2f}req/s")
                with open(PROGRESS, "a") as fh:
                    fh.write(msg + "\n")
                print(msg, flush=True)
        return res["outcome"]

    max_passes = 8
    for p in range(max_passes):
        done_iks = set(r[0] for r in con.execute("SELECT inchikey FROM classyfire_raw").fetchall())
        todo = [ik for ik in sample_iks if ik not in done_iks]
        if not todo:
            break
        print(f"pass {p+1}: {len(todo)} keys remaining", flush=True)
        log_audit(f"Phase2a pass {p+1}: {len(todo)} keys remaining")
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            list(ex.map(work, todo))
        con.commit()
        if counters["deferred"] and p < max_passes - 1:
            time.sleep(15)  # let the server throttle window reset before retrying

    # final tally over the whole sample
    q = con.execute(
        "SELECT outcome, COUNT(*) FROM classyfire_raw WHERE inchikey IN "
        "(SELECT inchikey FROM probe_sample WHERE seed=?) GROUP BY outcome", (args.seed,))
    tally = dict(q.fetchall())
    total = sum(tally.values())
    hits = tally.get("HIT", 0)
    log_audit(f"Phase2a: probe COMPLETE total={total} tally={tally} hit_rate={hits/max(1,total):.4%}")
    print("FINAL TALLY:", json.dumps(tally, indent=2))
    print(f"hit_rate = {hits}/{total} = {hits/max(1,total):.4%}")
    con.close()


if __name__ == "__main__":
    main()
