#!/usr/bin/env python3
import csv, json, sqlite3, sys
from pathlib import Path
import networkx as nx
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from src.pilot_taxonomy import graph, RULESET_VERSION

def rows(path):
 with open(path) as f:return list(csv.DictReader(f,delimiter="\t"))
errors=[]; warnings=[]
nodes=rows(ROOT/"taxonomy/pilot_taxonomy_nodes.tsv"); edges=rows(ROOT/"taxonomy/pilot_taxonomy_edges.tsv"); mem=rows(ROOT/"taxonomy/pilot_compound_membership.tsv"); paths=rows(ROOT/"taxonomy/pilot_compound_primary_paths.tsv"); compounds=rows(ROOT/"data/processed/pilot_compounds_standardised.tsv")
nids={x['node_id'] for x in nodes}; cids={x['source_compound_id'] for x in compounds}
tsv_g=nx.DiGraph((e['parent_id'],e['child_id']) for e in edges); tsv_g.add_nodes_from(nids)
if not nx.is_directed_acyclic_graph(tsv_g):errors.append("serialized TSV taxonomy graph contains cycle")
if any(e['parent_id'] not in nids or e['child_id'] not in nids for e in edges):errors.append("edge references missing node")
if any(m['compound_id'] not in cids or m['class_id'] not in nids for m in mem):errors.append("membership foreign key unresolved")
if {x['compound_id'] for x in paths} != cids:errors.append("primary paths do not cover all compounds")
code_g=graph(); code_edges=set(code_g.edges); tsv_edges={(e['parent_id'],e['child_id']) for e in edges}
if set(code_g)!=nids or code_edges!=tsv_edges:errors.append("in-code graph differs from serialized TSV")
payload=json.load(open(ROOT/"taxonomy/pilot_taxonomy.json")); json_nodes={x['id'] for x in payload['nodes']}; json_edges={(x['parent'],x['child']) for x in payload['edges']}
if json_nodes!=nids or json_edges!=tsv_edges:errors.append("JSON nodes/edges differ from TSV")
graphml=nx.read_graphml(ROOT/"taxonomy/pilot_taxonomy.graphml"); graphml_edges=set(graphml.edges)
if set(graphml)!=nids or graphml_edges!=tsv_edges:errors.append("GraphML nodes/edges differ from TSV")
if not nx.is_directed_acyclic_graph(graphml):errors.append("serialized GraphML contains cycle")
for p in paths:
 ids=json.loads(p['node_id_path'])
 if not ids or ids[-1]!=p['primary_leaf_class'] or any((a,b) not in tsv_edges for a,b in zip(ids,ids[1:])):errors.append(f"invalid primary path: {p['compound_id']}");break
con=sqlite3.connect(ROOT/"database/chemical_taxonomy_pilot.db"); con.execute("PRAGMA foreign_keys=ON"); fk=con.execute("PRAGMA foreign_key_check").fetchall(); integrity=con.execute("PRAGMA integrity_check").fetchone()[0]
db_counts={t:con.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in ['compounds','taxonomy_nodes','taxonomy_edges','compound_membership','taxonomy_paths','provenance']}
if db_counts['compounds']!=len(compounds) or db_counts['taxonomy_nodes']!=len(nodes) or db_counts['taxonomy_edges']!=len(edges) or db_counts['compound_membership']!=len(mem) or db_counts['taxonomy_paths']!=len(paths):errors.append("SQLite table counts differ from serialized TSV/input counts")
db_nodes={r[0] for r in con.execute('SELECT node_id FROM taxonomy_nodes')};db_edges={(r[0],r[1]) for r in con.execute('SELECT parent_id,child_id FROM taxonomy_edges')}
db_mem={(r[0],r[1],r[2],r[3],r[4],str(r[5])) for r in con.execute('SELECT compound_id,class_id,membership_type,source,evidence,is_primary FROM compound_membership')}
tsv_mem={(m['compound_id'],m['class_id'],m['membership_type'],m['classification_method'],m['evidence'],m['is_primary']) for m in mem}
db_paths={(r[0],r[1],r[2],r[3]) for r in con.execute('SELECT compound_id,primary_leaf_class,taxonomy_path,node_id_path FROM taxonomy_paths')};tsv_paths={(p['compound_id'],p['primary_leaf_class'],p['taxonomy_path'],p['node_id_path']) for p in paths}
if db_nodes!=nids or db_edges!=tsv_edges:errors.append("SQLite taxonomy differs from TSV")
if db_mem!=tsv_mem:errors.append("SQLite memberships differ from TSV")
if db_paths!=tsv_paths:errors.append("SQLite paths differ from TSV")
prov=dict(con.execute('SELECT resource,version FROM provenance'));con.close()
if payload.get('metadata',{}).get('ruleset_version')!=RULESET_VERSION or {n['version'] for n in nodes}!={RULESET_VERSION} or prov.get('taxonomy_rules')!=RULESET_VERSION:errors.append("ruleset version differs across code/TSV/JSON/database")
if fk:errors.append(f"database foreign key failures: {fk[:3]}")
if integrity!="ok":errors.append("database integrity check failed")
boron=sum(1 for m in mem if m['class_id'] in {'DAGCHEM:0000600','DAGCHEM:0000601'} and m['membership_type']=='direct')
if boron==0:warnings.append("pilot has no boron compounds; synthetic boron rule tests are required and pass separately")
unresolved={m['compound_id'] for m in mem if m['class_id']=='DAGCHEM:0000800' and m['membership_type']=='direct'}
if unresolved:warnings.append(f"{len(unresolved)} compounds have only generic coverage and are marked unresolved organic")
metrics=json.load(open(ROOT/"results/pilot/pilot_metrics.json"))
if any(k in metrics for k in ['elapsed_seconds','timestamp','run_time']):errors.append("nondeterministic runtime metadata present in canonical metrics")
metrics.update({"database_integrity":integrity,"foreign_key_violations":len(fk),"dag_acyclic":nx.is_directed_acyclic_graph(tsv_g),"boron_direct_memberships":boron,"specifically_classified_compounds":len(cids)-len(unresolved),"partially_classified_unresolved_compounds":len(unresolved),"serialized_counts_crosschecked":True,"database_counts":db_counts})
result={"status":"PASS" if not errors else "FAIL","critical_errors":errors,"warnings":warnings,"metrics":metrics,"ruleset_version":RULESET_VERSION}
(ROOT/"results/pilot/pilot_validation.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); print(json.dumps(result,indent=2,sort_keys=True)); raise SystemExit(bool(errors))
