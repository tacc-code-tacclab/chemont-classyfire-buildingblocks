# Error analysis — mapper failure modes

Sources: reproduced OOD detail (`results/v4_chemont_mapper/v3_repro/data/benchmark_detail.csv`)
and preliminary target-domain detail (`results/v4_chemont_mapper/target_domain_detail.csv`,
n=111 genuine building-block labels).

## Dominant failure mode: facet **selection**, not coverage

On the target domain, 62/111 are off-path, but **21 of those are "rescued" by `any_match`** —
i.e. the correct class was among the mapper's candidate set, it just wasn't chosen as the
*primary*. `any_match` (63.1%) ≫ `on_path` (44.1%) ≫ `exact` (13.5%) is the signature of a
**selection/priority** problem layered on a **leaf-coverage** problem:

1. **Primary-facet selection errors** (fixable without new rules). Top target-domain confusions:
   - said *Benzene and substituted derivatives* when the true benzenoid **class** is more
     specific (Anilines, Anisoles, etc.) → the skeleton-first heuristic stops at the generic
     benzene class instead of the specific substituted-benzene subclass.
   - said *Anisoles* / *Aniline and substituted anilines* / *Piperazines* as primary when the
     genuine terminal sits on a different branch → a peripheral facet outranked the true
     skeleton for that molecule.
   - This is precisely what **Phase 6 step 1** targets: derive each rule class's priority from
     its real ChemOnt superclass (Benzenoids/Organoheterocyclic = skeleton, primary) instead of
     hand-tuned tiers, so specific ring subclasses win over generic ancestors and over
     peripheral groups.

2. **Leaf-coverage gaps** (need new rules). Whole superclasses are near-0%:
   *Organic acids and derivatives* (12.5% super_ok), *Phenylpropanoids and polyketides*,
   *Lipids*, *Organosulfur*. The 61 rules simply don't encode these classes' specific leaves.
   These are the **priority classes for Phase 6 rule expansion**, chosen because they actually
   occur in the genuine building-block ground truth (not the environmental set).

## OOD vs target-domain consistency

The OOD reproduction shows the same structure (`any_match 63.0%` ≫ `exact 8.7%`) and the same
weak superclasses (Organic acids, Lipids, Organosulfur), so the failure modes are **domain-
stable** — the fixes identified will help both domains, with priority weighting toward the
building-block class frequencies.

## Caveats

Target-domain N=111 → per-superclass counts are tiny (Lipids n=2, Organosulfur n=1); those rows
are illustrative only. The analysis will be re-run at larger N as Phase 2b accumulates labels,
and extended with confusion matrices, calibration, and novelty-stratified breakdowns (Phase 7)
once the genuine set supports them.
