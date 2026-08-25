# CRITICAL FILE-SYSTEM SAFETY RULES

These rules are mandatory and override all other project instructions.

1. NEVER delete files or directories.

2. NEVER use destructive commands, including but not limited to:
   - rm
   - rmdir
   - unlink
   - shred
   - find ... -delete
   - git clean
   - git reset --hard

3. NEVER overwrite an existing important file without first preserving the previous version.

4. If an existing file or directory must be replaced, rename the previous version using:

   <original_name>.old_<YYYYMMDD_HHMMSS>

   Example:

   taxonomy.db
   becomes
   taxonomy.db.old_20260721_183500

5. If a new attempt or alternative implementation is needed, create a new version rather than deleting the old one.

   Examples:

   taxonomy_v1/
   taxonomy_v2/

   or:

   pipeline_old_20260721_183500/

6. NEVER modify, rename, overwrite, or delete:

   /data01/cris/projects/DAG/prompt.md

7. NEVER modify or delete anything outside:

   /data01/cris/projects/DAG

8. Do not modify system files, user configuration files, other projects, or other directories under /data01/cris/projects/.

9. Before any potentially destructive or irreversible operation, choose a non-destructive alternative.

10. All downloaded files, cloned repositories, generated data, temporary files, and outputs must remain under:

    /data01/cris/projects/DAG

# MANDATORY AUDIT LOG

Maintain a persistent chronological log at:

/data01/cris/projects/DAG/logs/agent_actions.log

The log must record:

- timestamp;
- current task;
- commands executed;
- files created;
- files modified;
- files renamed;
- packages installed;
- repositories cloned;
- datasets downloaded;
- URLs used;
- errors encountered;
- fixes applied;
- major decisions and reasons.

Before modifying an existing file, log the intended modification.

Whenever an existing file is preserved by renaming it to `.old_<timestamp>`, record both the old and new paths.

At the end of every major project stage, write a checkpoint entry to the log.

Never delete or truncate the audit log.

Also create a concise final audit summary:

reports/agent_execution_summary.md


# Chemical Taxonomy DAG for Commercial Building Blocks

## PROJECT ROOT AND COMPUTING ENVIRONMENT

You are working on a Linux server.

The project root directory is:

/data01/cris/projects/DAG

The master prompt is:

/data01/cris/projects/DAG/prompt.md

The Conda environment is already activated:

conda activate ptrag_bcrabl

You MUST work directly inside:

/data01/cris/projects/DAG

Do NOT create another top-level project directory.

Before starting:

1. Run `pwd` and confirm that the working directory is:

   /data01/cris/projects/DAG

2. Confirm that the active Conda environment is:

   ptrag_bcrabl

3. Read this entire `prompt.md` before starting.

4. Inspect all files already present in the project directory.

5. Use the existing Conda environment whenever possible.

6. Install missing packages only when required and document all additions.

7. Keep ALL code, repositories, downloaded databases, intermediate files, logs, reports, and results inside:

   /data01/cris/projects/DAG

8. Use relative paths in scripts whenever possible.

9. Record software versions, repository commit hashes, ontology versions, database versions, download dates, source URLs, and checksums.

Proceed autonomously.

Do not pause to ask the user for approval for normal operations such as:

- creating directories;
- cloning public repositories;
- downloading public datasets;
- installing required open-source Python packages;
- running scripts;
- testing APIs;
- processing molecules;
- creating databases;
- writing reports.

Only stop if access requires credentials, payment, acceptance of a restrictive licence, or another action that cannot legally or technically be performed automatically.

---

# 1. SCIENTIFIC OBJECTIVE

The objective is to construct a professional, chemically meaningful, reproducible, and machine-readable taxonomy of COMMERCIAL SYNTHETIC BUILDING BLOCKS.

The final taxonomy will ultimately be used for the approximately 200,000 Enamine building blocks employed by SynFlowNet.

The exact Enamine dataset is currently unavailable and has been requested from Enamine.

While waiting for it, we will construct and validate the complete taxonomy pipeline using publicly accessible COMMERCIAL/PURCHASABLE BUILDING BLOCKS FROM ZINC.

The project must therefore proceed in two stages:

## STAGE 1 — PILOT

Download approximately 1,000 diverse commercial/purchasable ZINC building blocks.

Use them to:

- design the database;
- implement molecular standardisation;
- evaluate existing taxonomy resources;
- classify the compounds;
- construct the chemical taxonomy;
- build the DAG;
- validate the complete pipeline;
- identify errors and limitations.

## STAGE 2 — FULL ZINC DATASET

ONLY if Stage 1 passes validation:

- download the complete publicly accessible ZINC commercial/purchasable building-block dataset;
- run exactly the same validated pipeline;
- classify all available building blocks;
- construct the complete taxonomy DAG;
- produce the final database and graph representations.

The pipeline must later accept the Enamine/SynFlowNet dataset by replacing only the input molecular dataset.

---

# 2. STRICT PROJECT SCOPE

This project concerns ONLY CHEMICAL TAXONOMY.

Cristian's responsibility is to build the chemical taxonomy and deliver it as a clean machine-readable structure.

Do NOT:

- implement Sphere Neural Networks;
- implement sphere embeddings;
- implement sphere losses;
- modify SynFlowNet;
- modify GFlowNet;
- develop mathematical sphere representations;
- train SphereFlowNet.

The taxonomy will later be given to Tiansi Dong, who will decide how to mathematically represent and use it.

The current task is therefore:

COMMERCIAL BUILDING BLOCKS
        ↓
CHEMICAL CLASSIFICATION
        ↓
HIERARCHICAL CHEMICAL TAXONOMY
        ↓
DAG
        ↓
MACHINE-READABLE DATABASE

---

# 3. INSPECT SYNFLOWNET

Clone the official SynFlowNet repository into:

external_repositories/synflownet/

Inspect the repository carefully.

Determine:

- how building blocks are represented;
- expected input format;
- how they are standardised;
- how salts are handled;
- how stereochemistry is handled;
- how duplicates are removed;
- what preprocessing scripts exist;
- what reaction templates exist;
- what SMARTS reaction rules exist;
- how building-block/reaction compatibility is calculated;
- whether precomputed masks exist;
- what information is available about the original Enamine dataset.

Do NOT assume that the approximately 200,000 Enamine building blocks are included.

Create:

reports/synflownet_data_inspection.md

Document the exact files and scripts found.

The SynFlowNet repository is being inspected for methodological context only.

The current taxonomy dataset must come from ZINC.

---

# 4. CREATE THE PROJECT STRUCTURE

Create the following structure directly under:

/data01/cris/projects/DAG

Expected structure:

DAG/
│
├── prompt.md
├── README.md
│
├── data/
│   ├── raw/
│   │   └── zinc/
│   ├── pilot/
│   ├── external/
│   │   ├── chemont/
│   │   ├── chebi/
│   │   └── drugtax/
│   └── processed/
│
├── external_repositories/
│   ├── synflownet/
│   ├── drugtax/
│   └── other_repositories/
│
├── database/
│
├── taxonomy/
│
├── results/
│   ├── resource_tests/
│   ├── pilot/
│   └── full/
│
├── reports/
│
├── src/
│
├── scripts/
│
├── tests/
│
└── logs/

Do not create another project root.

---

# 5. TAXONOMY RESOURCES TO INVESTIGATE

The primary existing taxonomy resources to evaluate are:

1. ChemOnt / ClassyFire
2. ChEBI
3. DrugTax

These resources have different potential roles.

Our CURRENT HYPOTHESIS is:

ChemOnt / ClassyFire
    → primary structural chemical taxonomy backbone

ChEBI
    → ontology validation and possible enrichment

DrugTax
    → potential software/helper layer for automated classification

However, this is only a hypothesis.

The agents MUST test these resources before committing to the final architecture.

Additional authoritative chemical classification resources may be evaluated if clearly relevant, but do not unnecessarily expand the scope.

---

# 6. DOWNLOAD AND INSPECT TAXONOMY RESOURCES

Automatically obtain all publicly available resources needed to evaluate:

- ChemOnt;
- ClassyFire;
- ChEBI;
- DrugTax.

Clone public repositories where available.

Download public ontology files and database releases where available.

Store:

repositories
    → external_repositories/

ontology/database files
    → data/external/

For each resource determine:

- exact purpose;
- taxonomy versus ontology;
- hierarchy structure;
- number of hierarchy levels;
- support for multiple inheritance;
- availability of parent-child relationships;
- availability of stable class identifiers;
- downloadable full taxonomy;
- local classification capability;
- API requirement;
- API limits;
- bulk processing capability;
- ability to classify arbitrary molecules not already present in the database;
- scalability to hundreds of thousands of molecules;
- licence;
- redistribution restrictions;
- reproducibility;
- current maintenance status.

Inspect actual code and data.

Do not rely only on README descriptions.

Create:

reports/taxonomy_resources_comparison.md

---

# 7. STAGE 1 — DOWNLOAD 1,000 ZINC COMMERCIAL BUILDING BLOCKS

The first molecular dataset MUST come from ZINC.

The compounds must represent:

COMMERCIAL / PURCHASABLE SYNTHETIC BUILDING BLOCKS

Do NOT use:

- random ZINC drug-like compounds;
- ChEMBL compounds;
- PubChem compounds;
- ChEBI compounds;
- approved drugs;
- generic screening molecules.

The goal is specifically to approximate the chemical domain of the Enamine building blocks used by SynFlowNet.

Determine the CURRENT official method for obtaining publicly accessible ZINC building blocks.

Use official ZINC resources where technically possible.

Select approximately 1,000 UNIQUE COMMERCIAL/PURCHASABLE BUILDING BLOCKS.

Do NOT simply select the first 1,000 records.

Construct a chemically diverse subset.

Where possible include:

- primary amines;
- secondary amines;
- aromatic amines;
- aliphatic amines;
- carboxylic acids;
- alcohols;
- phenols;
- aldehydes;
- ketones;
- aryl halides;
- alkyl halides;
- boronic acids;
- boronate esters;
- heterocycles;
- heteroaromatic compounds;
- sulfur-containing building blocks;
- phosphorus-containing building blocks;
- multifunctional compounds.

Use a reproducible diversity-selection strategy.

Possible approaches include molecular fingerprints and MaxMin diversity selection.

Record:

- ZINC ID;
- original SMILES;
- source;
- commercial/purchasable status;
- building-block annotation where available;
- supplier information where available;
- source URL;
- query or download method;
- download date.

Save the raw pilot dataset as:

data/pilot/zinc_commercial_building_blocks_1000_raw.tsv

Create:

reports/zinc_pilot_provenance.md

---

# 8. MOLECULAR STANDARDISATION

Implement a professional RDKit-based standardisation pipeline.

For each molecule record:

- source_compound_id;
- original_smiles;
- canonical_smiles;
- isomeric_smiles;
- InChI;
- InChIKey;
- molecular_formula;
- molecular_weight;
- formal_charge;
- heavy_atom_count;
- stereochemistry_status;
- sanitisation_status.

Investigate and explicitly document decisions regarding:

- salts;
- mixtures;
- disconnected fragments;
- charge normalisation;
- tautomers;
- stereochemistry;
- isotopes;
- duplicate structures.

Do NOT silently remove molecules.

Any failed molecule must be written to:

data/processed/failed_compounds.tsv

with:

compound_id
original_smiles
failure_stage
failure_reason

Successfully processed molecules:

data/processed/pilot_compounds_standardised.tsv

Deduplicate using a chemically justified canonical representation.

Report:

- raw count;
- successfully parsed count;
- failed count;
- duplicates removed;
- final unique count.

---

# 9. TEST TAXONOMY CLASSIFICATION ON 20–50 MOLECULES FIRST

Before classifying all 1,000 pilot molecules, select approximately 20–50 chemically diverse molecules from the pilot.

Test each available classification approach.

Where technically possible test:

- ClassyFire / ChemOnt;
- ChEBI;
- DrugTax.

For every method determine:

- whether the molecule can be classified;
- hierarchy returned;
- class identifiers returned;
- depth of classification;
- multiple class memberships;
- classification failures;
- API response time;
- local execution time;
- reproducibility;
- dependence on external APIs.

Compare classifications across resources.

Store outputs under:

results/resource_tests/

Create:

reports/resource_test_results.md

This stage must identify the practical classification strategy before processing the 1,000-compound dataset.

---

# 10. SELECT THE FINAL TAXONOMY STRATEGY

Based on the previous tests, select the best taxonomy architecture.

The selection criteria are:

1. chemical correctness;
2. explicit structural meaning;
3. hierarchical organisation;
4. ability to classify arbitrary commercial building blocks;
5. reproducibility;
6. scalability;
7. support for multiple inheritance;
8. stable identifiers;
9. local execution where possible;
10. long-term maintainability.

The preferred current architecture is:

ChemOnt/ClassyFire
        ↓
primary structural taxonomy

ChEBI
        ↓
validation / enrichment

DrugTax
        ↓
classification helper if useful

But change this strategy if the experimental evidence clearly indicates a better solution.

Document the final decision in:

reports/taxonomy_strategy.md

Do NOT continue to full 1,000-compound classification until the strategy has been selected.

---

# 11. CHEMICAL TAXONOMY PRINCIPLE

The taxonomy must represent CHEMICALLY MEANINGFUL CLASSES.

Do NOT create arbitrary unsupervised clusters and label them as chemical taxonomy classes.

Machine-learning clustering may be used for exploratory analysis or diversity sampling, but not as a substitute for chemically defined taxonomy.

Examples of valid taxonomy concepts include:

Organic compounds

    ├── Organoheterocyclic compounds
    │       └── Pyridines
    │
    ├── Amines
    │       ├── Aliphatic amines
    │       └── Aromatic amines
    │
    └── Organohalogen compounds
            └── Organofluorine compounds

A compound may legitimately belong to several classes.

For example, one building block may simultaneously be:

- a pyridine;
- an aromatic amine;
- an organofluorine compound.

Therefore, DO NOT force the master representation into a strict single-parent tree.

---

# 12. MASTER REPRESENTATION: DAG

The primary taxonomy representation should be a:

DIRECTED ACYCLIC GRAPH (DAG)

The DAG represents relationships between CHEMICAL CLASSES.

A class may have multiple parent classes if supported by the ontology.

The graph MUST remain acyclic.

Automatically test the graph for cycles.

Also create a simplified TREE PROJECTION for comparison and for users who require a single primary hierarchy.

The DAG is the canonical master representation.

---

# 13. IMPORTANT: TAXONOMY CLASSES ARE NOT INDIVIDUAL MOLECULES

Keep two concepts strictly separate.

## A. TAXONOMY

Contains chemical classes.

Examples:

Amine
Aromatic amine
Pyridine
Organofluorine compound

## B. COMPOUND INSTANCES

Contains individual ZINC building blocks.

Example:

ZINC12345678

may be linked to:

Aromatic amine
Pyridine
Organofluorine compound

Do NOT automatically create one taxonomy node for every molecule.

Individual compounds are INSTANCES linked to taxonomy classes.

---

# 14. DESIGN THE DATABASE

Using the 1,000-compound pilot, create a professional database structure that can later scale to the complete ZINC dataset and subsequently to the Enamine dataset.

Create a local relational database.

A lightweight database such as SQLite or DuckDB is acceptable for the pilot and full ZINC dataset if performance is sufficient.

The database must contain logically separate tables for:

## compounds

At minimum:

compound_id
source
source_id
original_smiles
canonical_smiles
isomeric_smiles
inchi
inchikey
molecular_formula
molecular_weight
formal_charge
commercial_status
supplier
standardisation_status

## taxonomy_nodes

At minimum:

node_id
name
definition
ontology_source
ontology_source_id
node_type

## taxonomy_edges

At minimum:

parent_id
child_id
relation_type
source

## compound_membership

At minimum:

compound_id
class_id
membership_type
source
evidence
is_primary

## taxonomy_paths

At minimum:

compound_id
primary_leaf_class
taxonomy_path

## provenance

At minimum:

resource
version
url
download_date
checksum
licence

Use primary keys and indexes where appropriate.

Enforce referential integrity.

Create database construction scripts.

Do NOT manually create or modify final database records.

Save the pilot database under:

database/chemical_taxonomy_pilot.db

Document the complete schema in:

reports/database_schema.md

---

# 15. CLASSIFY THE 1,000-COMPOUND PILOT

Using the selected taxonomy strategy, classify all successfully standardised compounds in the approximately 1,000-molecule ZINC pilot.

For every classification record:

- compound ID;
- taxonomy class ID;
- class name;
- ontology source;
- source class ID;
- membership type;
- evidence;
- classification method;
- primary versus secondary membership.

Explicitly distinguish:

- authoritative ontology assignment;
- deterministic structure-based classification;
- rule-based assignment;
- inferred assignment;
- unresolved/unclassified.

Never present a similarity-only prediction as an authoritative ontology assignment.

---

# 16. BUILD THE PILOT DAG

Create the taxonomy DAG from the chemical classes assigned to the pilot building blocks.

The DAG should contain:

NODES
    = chemical classes

EDGES
    = parent-child / subclass relationships

COMPOUND MEMBERSHIP
    = separate links between molecules and class nodes

Create:

taxonomy/pilot_taxonomy_nodes.tsv

taxonomy/pilot_taxonomy_edges.tsv

taxonomy/pilot_compound_membership.tsv

taxonomy/pilot_compound_primary_paths.tsv

Export the graph as:

taxonomy/pilot_taxonomy.graphml

taxonomy/pilot_taxonomy.json

The JSON format must explicitly contain:

nodes
edges

and must be simple to load in Python.

Create a Python loader and validator.

---

# 17. OPTIONAL SYNFLOWNET REACTION ANNOTATION

If technically straightforward, apply SynFlowNet reaction compatibility rules to the ZINC pilot building blocks.

This information must remain SEPARATE from the core taxonomy.

For example:

Compound X
    is_a → Aromatic amine

Compound X
    compatible_with_reaction_slot → amide_coupling_amine

These are different relationships.

Store reaction compatibility separately:

taxonomy/pilot_compound_reaction_compatibility.tsv

Do not modify the core chemical taxonomy to force reaction compatibility into `is_a` relationships.

---

# 18. PILOT QUALITY CONTROL

The 1,000-compound pilot is a mandatory validation gate.

Calculate:

- number of downloaded compounds;
- number successfully parsed;
- standardisation failures;
- duplicate molecules;
- final unique compounds;
- classified compounds;
- partially classified compounds;
- unclassified compounds;
- compounds with one class membership;
- compounds with multiple memberships;
- total taxonomy nodes;
- total taxonomy edges;
- root nodes;
- leaf nodes;
- maximum hierarchy depth;
- median hierarchy depth;
- nodes with multiple parents;
- disconnected components;
- cycles.

The DAG MUST pass the cycle check.

The database MUST pass referential-integrity checks.

All compound foreign keys must resolve.

All taxonomy edges must reference valid nodes.

All compound memberships must reference valid compounds and classes.

Manually inspect representative examples from major chemical classes.

Pay particular attention to multifunctional building blocks.

Create:

reports/pilot_1000_results.md

reports/pilot_quality_control.md

reports/pilot_failures.md

---

# 19. DAG VERSUS TREE ANALYSIS

Generate a simplified primary-parent tree projection.

Compare it with the complete DAG.

Calculate:

- percentage of compounds with multiple class memberships;
- number of classes with multiple parents;
- relationships lost when converting the DAG to a tree;
- compounds losing meaningful classification information.

Create:

reports/dag_vs_tree.md

The purpose is to provide Tiansi Dong with objective information about whether the full DAG or a simplified tree is preferable for downstream mathematical representation.

Do not make decisions about sphere mathematics.

---

# 20. STAGE 1 PASS/FAIL GATE

DO NOT DOWNLOAD OR PROCESS THE COMPLETE ZINC BUILDING-BLOCK DATASET UNTIL THE PILOT HAS PASSED VALIDATION.

The pilot may proceed to Stage 2 only if all CRITICAL checks pass.

Critical requirements:

1. Molecular standardisation pipeline runs reproducibly.

2. No unexplained systematic molecule loss.

3. Database schema is valid.

4. Referential integrity passes.

5. Taxonomy graph is acyclic.

6. Taxonomy nodes and edges can be reconstructed reproducibly.

7. Compound-to-class mappings are traceable to their sources.

8. The selected classification method produces chemically meaningful classifications.

9. Classification failures are quantified and understood.

10. No critical pipeline errors remain.

11. The system can be executed end-to-end from scripts.

12. The classification strategy appears technically scalable to the full ZINC commercial building-block dataset.

Create an automated validation script:

scripts/validate_pilot.py

It should produce a machine-readable result such as:

results/pilot/pilot_validation.json

with:

{
  "status": "PASS" or "FAIL",
  "critical_errors": [...],
  "warnings": [...],
  "metrics": {...}
}

If status == FAIL:

DO NOT start Stage 2.

Investigate and fix the problems.

Repeat the pilot until it passes or until a fundamental limitation is identified.

Document unresolved limitations clearly.

If status == PASS:

Proceed automatically to Stage 2.

---

# 21. STAGE 2 — DOWNLOAD ALL AVAILABLE ZINC COMMERCIAL BUILDING BLOCKS

After the pilot passes validation, determine the current official ZINC mechanism for accessing the COMPLETE publicly available set of:

COMMERCIAL / PURCHASABLE BUILDING BLOCKS

Download all accessible compounds belonging to this category.

Do NOT download the entire generic ZINC database unless this is technically required to extract the building-block subset.

Do NOT replace the target dataset with generic drug-like or screening compounds.

The objective is specifically:

ALL PUBLICLY ACCESSIBLE ZINC COMMERCIAL/PURCHASABLE BUILDING BLOCKS

Store raw data under:

data/raw/zinc/

Record:

- exact query/filter used;
- source URLs;
- database version;
- download date;
- total records downloaded;
- checksums.

Create:

reports/zinc_full_dataset_provenance.md

Report the exact number of building blocks obtained.

Do NOT assume that this number will be approximately 200,000.

---

# 22. PROCESS THE COMPLETE ZINC BUILDING-BLOCK DATASET

Apply EXACTLY the validated Stage 1 pipeline:

Raw ZINC commercial building blocks
        ↓
standardisation
        ↓
deduplication
        ↓
chemical classification
        ↓
taxonomy membership
        ↓
DAG construction
        ↓
database
        ↓
quality control

Do NOT redesign the taxonomy specifically for the larger dataset unless a genuine scalability issue requires modification.

Any modification made after pilot validation must be documented.

---

# 23. FULL TAXONOMY OUTPUTS

Create:

taxonomy/taxonomy_nodes.tsv

taxonomy/taxonomy_edges.tsv

taxonomy/compound_membership.tsv

taxonomy/compound_primary_paths.tsv

taxonomy/taxonomy.graphml

taxonomy/taxonomy.json

If reaction compatibility was generated:

taxonomy/compound_reaction_compatibility.tsv

Create the full database:

database/chemical_taxonomy_zinc.db

The database and exported files must represent ALL successfully processed ZINC commercial building blocks.

---

# 24. FULL-DATASET QUALITY CONTROL

Calculate:

- total raw ZINC building blocks;
- valid structures;
- invalid structures;
- duplicates;
- final unique structures;
- classified compounds;
- partially classified compounds;
- unclassified compounds;
- classification coverage percentage;
- single-membership compounds;
- multiple-membership compounds;
- taxonomy node count;
- taxonomy edge count;
- root count;
- leaf count;
- maximum depth;
- median depth;
- nodes with multiple parents;
- disconnected components;
- DAG cycle status.

Produce:

reports/full_taxonomy_statistics.md

reports/full_quality_control.md

reports/full_unclassified_compounds.md

reports/full_limitations.md

---

# 25. SCALABILITY AND FUTURE ENAMINE INPUT

The final pipeline must be designed so that when the official Enamine/SynFlowNet dataset becomes available, the input can be changed from:

ZINC commercial building blocks

to:

Enamine SynFlowNet building blocks

without changing the fundamental taxonomy architecture.

Prepare a documented command or workflow such as:

python scripts/run_taxonomy_pipeline.py \
    --input data/raw/enamine/enamine_building_blocks.tsv \
    --source enamine \
    --output-prefix enamine

Do NOT execute this phase now.

Do NOT fabricate Enamine data.

Do NOT substitute the ZINC identifiers for Enamine identifiers.

Document future Enamine integration in:

reports/future_enamine_integration.md

---

# 26. MULTI-AGENT WORK STRATEGY

Use specialised agents where useful.

Recommended roles:

## Agent A — SynFlowNet

Clone and inspect SynFlowNet.

Document building-block preprocessing and reaction rules.

## Agent B — ZINC

Determine the current official method to obtain ZINC commercial/purchasable building blocks.

Download the 1,000-compound pilot.

Later, only after PASS, obtain the complete dataset.

## Agent C — ChemOnt / ClassyFire

Investigate taxonomy data, classifier implementation, API, local execution, and scalability.

## Agent D — ChEBI

Download and analyse the ChEBI ontology.

Evaluate its role in taxonomy validation and enrichment.

## Agent E — DrugTax

Clone and inspect DrugTax.

Determine exactly how it classifies molecules and whether it depends on ClassyFire or other external resources.

## Agent F — Cheminformatics

Implement molecule standardisation, deduplication, validation, and diversity selection.

## Agent G — Database and DAG

Design the database schema, construct the DAG, implement cycle checks, graph exports, and database integrity checks.

## Agent H — Quality Control

Independently validate the pilot results before Stage 2.

Agents may work in parallel on independent investigations.

However:

DO NOT create multiple incompatible taxonomy architectures.

One integration step must select a single canonical taxonomy strategy before the 1,000-compound pilot is fully classified.

---

# 27. EXECUTION ORDER — STRICT

Follow this order.

## STEP 1

Confirm working directory and Conda environment.

## STEP 2

Create project directories.

## STEP 3

Clone and inspect SynFlowNet.

## STEP 4

Download and inspect ChemOnt/ClassyFire, ChEBI, and DrugTax resources.

## STEP 5

Download approximately 1,000 diverse ZINC commercial/purchasable building blocks.

## STEP 6

Standardise and deduplicate the 1,000 compounds.

## STEP 7

Test taxonomy resources on 20–50 representative compounds.

## STEP 8

Select and document the canonical taxonomy strategy.

## STEP 9

Design and implement the database schema.

## STEP 10

Classify all approximately 1,000 pilot compounds.

## STEP 11

Construct the pilot DAG and tree projection.

## STEP 12

Populate the pilot database.

## STEP 13

Run complete pilot quality control.

## STEP 14

Run:

scripts/validate_pilot.py

## STEP 15

If:

pilot_validation.status == FAIL

fix the pipeline and repeat validation.

DO NOT download the full ZINC dataset.

## STEP 16

If:

pilot_validation.status == PASS

automatically proceed to Stage 2.

## STEP 17

Download ALL publicly accessible ZINC commercial/purchasable building blocks.

## STEP 18

Apply the validated taxonomy pipeline to ALL building blocks.

## STEP 19

Construct the complete DAG.

## STEP 20

Build the full chemical taxonomy database.

## STEP 21

Perform final quality control.

## STEP 22

Generate final documentation and prepare the pipeline for future Enamine input.

---

# 28. FINAL DELIVERABLES

The final project must contain:

## Database

database/chemical_taxonomy_pilot.db

database/chemical_taxonomy_zinc.db

## Full taxonomy

taxonomy/taxonomy_nodes.tsv

taxonomy/taxonomy_edges.tsv

taxonomy/compound_membership.tsv

taxonomy/compound_primary_paths.tsv

taxonomy/taxonomy.graphml

taxonomy/taxonomy.json

## Pilot taxonomy

taxonomy/pilot_taxonomy_nodes.tsv

taxonomy/pilot_taxonomy_edges.tsv

taxonomy/pilot_compound_membership.tsv

taxonomy/pilot_compound_primary_paths.tsv

taxonomy/pilot_taxonomy.graphml

taxonomy/pilot_taxonomy.json

## Reports

reports/synflownet_data_inspection.md

reports/zinc_pilot_provenance.md

reports/zinc_full_dataset_provenance.md

reports/taxonomy_resources_comparison.md

reports/resource_test_results.md

reports/taxonomy_strategy.md

reports/database_schema.md

reports/pilot_1000_results.md

reports/pilot_quality_control.md

reports/pilot_failures.md

reports/dag_vs_tree.md

reports/full_taxonomy_statistics.md

reports/full_quality_control.md

reports/full_unclassified_compounds.md

reports/full_limitations.md

reports/future_enamine_integration.md

## Reproducible code

src/

scripts/

tests/

README.md

environment.yml

---

# 29. FINAL SCIENTIFIC QUESTIONS

At the end of the project, answer clearly:

1. Can existing chemical taxonomy resources classify commercial synthetic building blocks effectively?

2. Which combination of ChemOnt/ClassyFire, ChEBI, and DrugTax is most appropriate?

3. What proportion of ZINC commercial building blocks can be classified?

4. How many compounds belong to multiple chemical classes?

5. Is a DAG materially more informative than a strict tree?

6. What information is lost in the tree projection?

7. How many building blocks remain unclassified and why?

8. Is the classification pipeline reproducible?

9. Is the pipeline scalable to approximately 200,000 Enamine building blocks?

10. Can the Enamine dataset later replace the ZINC input without redesigning the taxonomy?

---

# FINAL GOAL

The final output of this project must be a standalone:

CHEMICAL TAXONOMY OF COMMERCIAL SYNTHETIC BUILDING BLOCKS

represented as:

CHEMICAL TAXONOMY DAG
+
COMPOUND-TO-CLASS MAPPINGS
+
RELATIONAL DATABASE
+
GRAPH EXPORTS
+
FULL PROVENANCE
+
QUALITY CONTROL

The project must first prove that the approach works correctly on approximately 1,000 ZINC commercial building blocks.

Only after successful validation should the system automatically scale to ALL publicly accessible ZINC commercial/purchasable building blocks.

The resulting pipeline must then be ready to process the official approximately 200,000 Enamine/SynFlowNet building blocks as soon as that dataset becomes available.

