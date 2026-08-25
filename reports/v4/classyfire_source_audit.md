# Phase 0.5 — ClassyFire connectivity and access audit

_Empirical tests from this host (`/data01/cris/projects/DAG`) during the V4 run._

## Outbound network

Outbound network **is available** from this host (control test `https://www.google.com/`
→ HTTP 200; DNS resolves for the ClassyFire hosts). This is a change from prior-run
conditions where ClassyFire access was blocked/throttled.

## Candidate genuine-label sources tested

| source | URL pattern | reachable | returns genuine ClassyFire? | notes |
|---|---|---|---|---|
| **ClassyFire (wishartlab)** | `http://classyfire.wishartlab.com/entities/{InChIKey}.json` | **yes (HTTP 200)** | **yes** — precomputed entity: kingdom/superclass/class/subclass + `chemont_id`s | `https` fails (000, cert/redirect); use `http`. Strict rate limiting. Clean `404` on genuine cache miss. |
| **Fiehn Lab ClassyFire Batch** | `https://cfb.fiehnlab.ucdavis.edu/entities/{InChIKey}.json` | yes (HTTP 200) | yes — full record incl. `direct_parent` + `alternative_parents` | Throttles **very aggressively** (HTTP 429 after a few requests). Homepage: "Batch Compound Classification". Suitable for cross-check / batch submission, not for fast bulk pulls at our concurrency. |
| GNPS ClassyFire (`gnps-classyfire.ucsd.edu`) | — | no (000) | — | not reachable |

Both entity endpoints return `application/json` and **genuine precomputed ClassyFire
results with real ChemOnt IDs** (verified on aspirin `BSYNRYMUTXBXSQ-UHFFFAOYSA-N`:
Benzenoids → Benzene and substituted derivatives → Benzoic acids and derivatives,
`CHEMONTID:0002448/0002279/0000176`). These are **precomputed InChIKey lookups**, i.e.
tier-1/tier-2 genuine ground truth, not live on-the-fly submission.

## Observed rate-limiting behaviour (empirical, no documented SLA found)

- **wishartlab**: tolerates roughly ~1 request/second in short bursts, then returns
  `HTTP 429` and needs a cooldown of tens of seconds. Four concurrent workers at ~4 req/s
  triggered an IP-level 429 block within seconds. At a **single-worker ~0.35–0.6 req/s**
  pace with retry-on-429, throughput is sustainable with negligible deferrals.
  Effective sustainable answer rate observed: **~0.3–0.5 definitive answers/second**.
- **fiehnlab**: 429 after ~3 requests even at 0.3 s spacing; unusable for a large sweep
  from this host without an arrangement with the operators.

Implication for scale: at ~0.4 answers/s, a full 1.95 M sweep would take ~**56 days**;
reaching 200 k genuine labels at the measured hit rate needs ~330–450 k lookups ≈
**10–13 days** of continuous, respectful single-stream querying. This is the binding
operational constraint, independent of the hit rate.

## Licensing / redistribution

- ClassyFire homepage (`classyfire.wishartlab.com`, title "Run Classification - ClassyFire")
  states **commercial use and redistribution require permission**. Public reachability is
  **not** an unrestricted licence. Genuine labels retrieved here are stored locally with
  full provenance and raw responses; **redistribution of a major derived portion is gated
  on written permission** from the operators.
- Fiehn Lab batch service is an academic resource; bulk/programmatic use should be cleared
  with the operators and its throttling respected.

## Access actions that would materially help (for the user)

1. **An allowlist / higher rate-limit arrangement** (or a local ClassyFire DB dump) from
   the ClassyFire (Wishart Lab) operators — removes the ~10–13 day wall for 200 k.
2. **A Fiehn Lab batch run** on a supplied set of building-block InChIKeys, returned to us,
   is the other legitimate route mentioned in the V3 report.

Until such an arrangement exists, retrieval proceeds respectfully at the sustainable
single-stream pace, fully cached and resumable, and no throttling is bypassed.
