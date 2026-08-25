#!/usr/bin/env python3
"""Streaming full-ZINC build using pilot standardization and ruleset 1.1.1 unchanged."""
from __future__ import annotations

import argparse, csv, gzip, hashlib, json, multiprocessing as mp, os, sqlite3, statistics, sys, time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from rdkit import Chem, rdBase, RDLogger
from src.standardize import StandardizationError, standardize_smiles
from src.pilot_taxonomy import RULESET_VERSION, NODES, EDGES, SMARTS, compile_rules, direct_classes, graph

STD_FIELDS = ["canonical_smiles","isomeric_smiles","inchi","inchikey","molecular_formula","molecular_weight","formal_charge","heavy_atom_count","stereochemistry_status","sanitisation_status","fragment_count","fragment_policy","removed_fragments_smiles","charge_normalisation","tautomer_policy","isotope_status","deduplication_key"]
NAMES={x[0]:x[1] for x in NODES}; PRIORITIES={x[0]:x[3] for x in NODES}; G=graph()
DEPTHS={n:max((len(p)-1 for p in __import__('networkx').all_simple_paths(G,"DAGCHEM:0000001",n)),default=0) for n in G}
PATHS={n:max(__import__('networkx').all_simple_paths(G,"DAGCHEM:0000001",n),key=lambda p:(len(p),tuple(p))) for n in G}
ANCESTORS={n:sorted(__import__('networkx').ancestors(G,n)) for n in G}
_RULES=None

def worker_init():
 global _RULES
 RDLogger.DisableLog('rdApp.*'); _RULES=compile_rules()

def worker(item):
 ordinal,catalog,line_no,supplier,parsed_smiles,smiles=item
 cid=f"ZINCSRC:{catalog}:{line_no}"
 if supplier is None: return ('format_fail',ordinal,cid,catalog,smiles)
 try:
  s=standardize_smiles(parsed_smiles); d=s.as_dict(); mol=Chem.MolFromSmiles(d['isomeric_smiles']); direct=direct_classes(mol,_RULES)
  primary=max(direct,key=lambda x:(DEPTHS[x],PRIORITIES[x],x)); ancestors=sorted(set().union(*(ANCESTORS[c] for c in direct))-direct)
  return ('ok',ordinal,cid,catalog,supplier,smiles,d,sorted(direct),ancestors,primary)
 except StandardizationError as e: return ('fail',ordinal,cid,catalog,supplier,smiles,e.stage,e.reason)
 except Exception as e: return ('fail',ordinal,cid,catalog,supplier,smiles,'unexpected_exception',f'{type(e).__name__}: {e}')

def inputs(rawdir):
 ordinal=0
 for p in sorted(rawdir.glob('*.src.txt')):
  catalog=p.name.removesuffix('.src.txt')
  with p.open(errors='replace') as fh:
   for line_no,line in enumerate(fh,1):
    ordinal+=1; fields=line.strip().split()
    if len(fields)<2:
     yield ordinal,catalog,line_no,None,line.rstrip('\n'),line.rstrip('\n'); continue
    supplied_smiles=fields[0]
    parsed_smiles=supplied_smiles[3:] if supplied_smiles.startswith('>>>') else supplied_smiles
    yield ordinal,catalog,line_no,fields[1],parsed_smiles,supplied_smiles

def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()

def create_db(path):
 con=sqlite3.connect(path); con.execute('PRAGMA foreign_keys=ON'); con.execute('PRAGMA journal_mode=WAL'); con.execute('PRAGMA synchronous=NORMAL'); con.executescript('''
 CREATE TABLE compounds(compound_id TEXT PRIMARY KEY,source TEXT NOT NULL,source_id TEXT NOT NULL,catalog TEXT NOT NULL,supplier_code TEXT NOT NULL,zinc_id TEXT,original_smiles TEXT,canonical_smiles TEXT,isomeric_smiles TEXT,inchi TEXT,inchikey TEXT,molecular_formula TEXT,molecular_weight REAL,formal_charge INTEGER,commercial_status TEXT,supplier TEXT,standardisation_status TEXT,deduplication_key TEXT UNIQUE);
 CREATE TABLE source_records(source_record_id TEXT PRIMARY KEY,catalog TEXT NOT NULL,supplier_code TEXT,original_smiles TEXT,status TEXT NOT NULL,representative_compound_id TEXT REFERENCES compounds,zinc_id TEXT);
 CREATE TABLE failed_compounds(compound_id TEXT PRIMARY KEY,original_smiles TEXT,failure_stage TEXT,failure_reason TEXT,catalog TEXT,line_number INTEGER);
 CREATE TABLE duplicate_mapping(duplicate_source_compound_id TEXT PRIMARY KEY,representative_source_compound_id TEXT NOT NULL REFERENCES compounds,deduplication_key TEXT NOT NULL,duplicate_original_smiles TEXT,reason TEXT);
 CREATE TABLE taxonomy_nodes(node_id TEXT PRIMARY KEY,name TEXT NOT NULL,definition TEXT,ontology_source TEXT NOT NULL,ontology_source_id TEXT,node_type TEXT NOT NULL,version TEXT NOT NULL,priority INTEGER NOT NULL);
 CREATE TABLE taxonomy_edges(parent_id TEXT NOT NULL REFERENCES taxonomy_nodes,child_id TEXT NOT NULL REFERENCES taxonomy_nodes,relation_type TEXT NOT NULL,source TEXT NOT NULL,PRIMARY KEY(parent_id,child_id,relation_type));
 CREATE TABLE compound_membership(compound_id TEXT NOT NULL REFERENCES compounds,class_id TEXT NOT NULL REFERENCES taxonomy_nodes,membership_type TEXT NOT NULL,source TEXT NOT NULL,evidence TEXT NOT NULL,is_primary INTEGER NOT NULL CHECK(is_primary IN(0,1)),PRIMARY KEY(compound_id,class_id,membership_type));
 CREATE TABLE taxonomy_paths(compound_id TEXT PRIMARY KEY REFERENCES compounds,primary_leaf_class TEXT NOT NULL REFERENCES taxonomy_nodes,taxonomy_path TEXT NOT NULL,node_id_path TEXT NOT NULL);
 CREATE TABLE zinc_id_mapping(catalog TEXT,supplier_code TEXT,inchikey TEXT,zinc_id TEXT,PRIMARY KEY(catalog,supplier_code,inchikey,zinc_id));
 CREATE TABLE provenance(resource TEXT PRIMARY KEY,version TEXT,url TEXT,download_date TEXT,checksum TEXT,licence TEXT);
 CREATE INDEX idx_compounds_inchikey ON compounds(inchikey); CREATE INDEX idx_compounds_zinc ON compounds(zinc_id); CREATE INDEX idx_membership_class ON compound_membership(class_id); CREATE INDEX idx_edges_child ON taxonomy_edges(child_id); CREATE INDEX idx_map_lookup ON zinc_id_mapping(catalog,supplier_code,inchikey);
 '''); return con

def load_info(con):
 count=0
 for p in sorted((ROOT/'data/raw/zinc').glob('*.info.txt.gz')):
  catalog=p.name.removesuffix('.info.txt.gz')
  if catalog not in {x.name.removesuffix('.src.txt') for x in (ROOT/'data/raw/zinc/full_bb_source_20260721').glob('*.src.txt')}: continue
  rows=[]
  with gzip.open(p,'rt',errors='replace') as f:
   for line in f:
    x=line.rstrip('\n').split('\t')
    if len(x)>=3 and x[0] and x[1].startswith('ZINC') and x[2]: rows.append((catalog,x[0],x[2],x[1]))
    if len(rows)>=100000: con.executemany('INSERT OR IGNORE INTO zinc_id_mapping VALUES(?,?,?,?)',rows);count+=len(rows);rows=[]
  con.executemany('INSERT OR IGNORE INTO zinc_id_mapping VALUES(?,?,?,?)',rows);count+=len(rows);con.commit()
 return count

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=min(64,os.cpu_count() or 1));ap.add_argument('--chunksize',type=int,default=64);a=ap.parse_args()
 raw=ROOT/'data/raw/zinc/full_bb_source_20260721'; proc=ROOT/'data/processed'; tax=ROOT/'taxonomy'; res=ROOT/'results/full'; dbp=ROOT/'database/chemical_taxonomy_zinc.db'
 targets=[proc/'zinc_compounds_standardised.tsv',proc/'full_failed_compounds.tsv',proc/'zinc_duplicate_mapping.tsv',tax/'taxonomy_nodes.tsv',tax/'taxonomy_edges.tsv',tax/'compound_membership.tsv',tax/'compound_primary_paths.tsv',tax/'taxonomy.graphml',tax/'taxonomy.json',dbp,res/'full_metrics.json',res/'full_validation.json']
 for p in targets:
  if p.exists(): raise FileExistsError(f'refusing to overwrite {p}')
 proc.mkdir(exist_ok=True);tax.mkdir(exist_ok=True);res.mkdir(parents=True,exist_ok=True)
 start=time.time(); con=create_db(dbp)
 node_rows=[(i,n,d,'DAG_PROJECT',i,'chemical_class',RULESET_VERSION,p) for i,n,d,p in NODES];con.executemany('INSERT INTO taxonomy_nodes VALUES(?,?,?,?,?,?,?,?)',node_rows);con.executemany('INSERT INTO taxonomy_edges VALUES(?,?,?,?)',[(p,c,'is_a','DAG_PROJECT') for p,c in EDGES]);con.commit()
 zinc_map_rows=load_info(con)
 stdf=(proc/'zinc_compounds_standardised.tsv').open('w',newline=''); stdw=csv.writer(stdf,delimiter='\t',lineterminator='\n');stdw.writerow(['source_compound_id','source','source_id','catalog','supplier_code','zinc_id','original_smiles',*STD_FIELDS])
 failf=(proc/'full_failed_compounds.tsv').open('w',newline=''); failw=csv.writer(failf,delimiter='\t',lineterminator='\n');failw.writerow(['compound_id','original_smiles','failure_stage','failure_reason','catalog','line_number'])
 dupf=(proc/'zinc_duplicate_mapping.tsv').open('w',newline='');dupw=csv.writer(dupf,delimiter='\t',lineterminator='\n');dupw.writerow(['duplicate_source_compound_id','representative_source_compound_id','deduplication_key','duplicate_original_smiles','reason'])
 memf=(tax/'compound_membership.tsv').open('w',newline='');memw=csv.writer(memf,delimiter='\t',lineterminator='\n');memw.writerow(['compound_id','class_id','class_name','ontology_source','source_class_id','membership_type','evidence','classification_method','is_primary'])
 pathf=(tax/'compound_primary_paths.tsv').open('w',newline='');pathw=csv.writer(pathf,delimiter='\t',lineterminator='\n');pathw.writerow(['compound_id','primary_leaf_class','taxonomy_path','node_id_path'])
 counts=Counter(); direct_hist=Counter(); depths=[]; batch=[]
 def flush():
  nonlocal batch
  if batch: con.commit();batch=[]
 with mp.Pool(a.workers,initializer=worker_init,maxtasksperchild=5000) as pool:
  for result in pool.imap(worker,inputs(raw),chunksize=a.chunksize):
   counts['raw_rows']+=1
   if result[0]=='format_fail':
    _,ordinal,cid,catalog,raw_line=result;failw.writerow([cid,raw_line,'input_format','expected SMILES and supplier code',catalog,cid.rsplit(':',1)[1]]);con.execute('INSERT INTO failed_compounds VALUES(?,?,?,?,?,?)',(cid,raw_line,'input_format','expected SMILES and supplier code',catalog,int(cid.rsplit(':',1)[1])));con.execute('INSERT INTO source_records VALUES(?,?,?,?,?,?,?)',(cid,catalog,None,raw_line,'failed',None,None));counts['malformed']+=1
   elif result[0]=='fail':
    counts['valid_format_rows']+=1
    _,ordinal,cid,catalog,supplier,smiles,stage,reason=result;failw.writerow([cid,smiles,stage,reason,catalog,cid.rsplit(':',1)[1]]);con.execute('INSERT INTO failed_compounds VALUES(?,?,?,?,?,?)',(cid,smiles,stage,reason,catalog,int(cid.rsplit(':',1)[1])));con.execute('INSERT INTO source_records VALUES(?,?,?,?,?,?,?)',(cid,catalog,supplier,smiles,'failed',None,None));counts['chemistry_failures']+=1
   else:
    counts['valid_format_rows']+=1
    _,ordinal,cid,catalog,supplier,smiles,d,direct,ancestors,primary=result
    existing=con.execute('SELECT compound_id FROM compounds WHERE deduplication_key=?',(d['deduplication_key'],)).fetchone()
    if existing:
     rep=existing[0];dupw.writerow([cid,rep,d['deduplication_key'],smiles,'identical standardized canonical isomeric SMILES']);con.execute('INSERT INTO duplicate_mapping VALUES(?,?,?,?,?)',(cid,rep,d['deduplication_key'],smiles,'identical standardized canonical isomeric SMILES'));con.execute('INSERT INTO source_records VALUES(?,?,?,?,?,?,?)',(cid,catalog,supplier,smiles,'duplicate',rep,None));counts['duplicates']+=1
    else:
     comp=(cid,'zinc',cid,catalog,supplier,None,smiles,d['canonical_smiles'],d['isomeric_smiles'],d['inchi'],d['inchikey'],d['molecular_formula'],float(d['molecular_weight']),int(d['formal_charge']),'commercial/purchasable',catalog,d['sanitisation_status'],d['deduplication_key']);con.execute('INSERT INTO compounds VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',comp);con.execute('INSERT INTO source_records VALUES(?,?,?,?,?,?,?)',(cid,catalog,supplier,smiles,'representative',cid,None));stdw.writerow([cid,'zinc',cid,catalog,supplier,'',smiles,*[d[x] for x in STD_FIELDS]])
     for cl in direct:
      primary_flag=int(cl==primary);evidence=f"{RULESET_VERSION}:{SMARTS.get(cl,'property_predicate')}";con.execute('INSERT INTO compound_membership VALUES(?,?,?,?,?,?)',(cid,cl,'direct','rdkit_smarts_or_property',evidence,primary_flag));memw.writerow([cid,cl,NAMES[cl],'DAG_PROJECT',cl,'direct',evidence,'rdkit_smarts_or_property',primary_flag])
     for cl in ancestors:
      evidence=f'ancestor of direct membership under {RULESET_VERSION}';con.execute('INSERT INTO compound_membership VALUES(?,?,?,?,?,?)',(cid,cl,'inferred_assignment','dag_ancestor_propagation',evidence,0));memw.writerow([cid,cl,NAMES[cl],'DAG_PROJECT',cl,'inferred_assignment',evidence,'dag_ancestor_propagation',0])
     path=PATHS[primary];human=' > '.join(NAMES[x] for x in path);nodepath=json.dumps(path);con.execute('INSERT INTO taxonomy_paths VALUES(?,?,?,?)',(cid,primary,human,nodepath));pathw.writerow([cid,primary,human,nodepath]);counts['unique']+=1;counts['direct_memberships']+=len(direct);counts['inferred_memberships']+=len(ancestors);direct_hist[len(direct)]+=1;depths.append(len(path)-1);counts['unresolved']+=int('DAGCHEM:0000800' in direct)
   if counts['raw_rows']%10000==0: con.commit();stdf.flush();failf.flush();dupf.flush();memf.flush();pathf.flush();print(json.dumps({'processed_raw':counts['raw_rows'],'unique':counts['unique'],'duplicates':counts['duplicates'],'failures':counts['chemistry_failures'],'elapsed_s':round(time.time()-start,1)}),flush=True)
 con.commit()
 for f in [stdf,failf,dupf,memf,pathf]:f.close()
 # Resolve exact catalog + supplier + standardized InChIKey mappings; only unambiguous IDs.
 con.execute('''UPDATE compounds SET zinc_id=(SELECT min(m.zinc_id) FROM zinc_id_mapping m WHERE m.catalog=compounds.catalog AND m.supplier_code=compounds.supplier_code AND m.inchikey=compounds.inchikey HAVING count(DISTINCT m.zinc_id)=1)''');con.execute("UPDATE source_records SET zinc_id=(SELECT zinc_id FROM compounds WHERE compound_id=source_records.representative_compound_id)");con.commit()
 mapped=con.execute('SELECT count(*) FROM compounds WHERE zinc_id IS NOT NULL').fetchone()[0]
 # Rewrite standardized TSV zinc_id column from DB deterministically.
 tmp=proc/'zinc_compounds_standardised_with_ids.tsv'; outf=tmp.open('w',newline='');w=csv.writer(outf,delimiter='\t',lineterminator='\n');
 with (proc/'zinc_compounds_standardised.tsv').open() as inf:
  r=csv.reader(inf,delimiter='\t');w.writerow(next(r));
  for row in r: row[5]=con.execute('SELECT coalesce(zinc_id,\'\') FROM compounds WHERE compound_id=?',(row[0],)).fetchone()[0];w.writerow(row)
 outf.close();(proc/'zinc_compounds_standardised.tsv').rename(proc/'zinc_compounds_standardised.tsv.old_20260721_195131');tmp.rename(proc/'zinc_compounds_standardised.tsv')
 # Static graph exports.
 import networkx as nx
 csv.writer((tax/'taxonomy_nodes.tsv').open('w',newline=''),delimiter='\t',lineterminator='\n').writerows([['node_id','name','definition','ontology_source','ontology_source_id','node_type','version','priority'],*node_rows])
 edge_rows=[(p,c,'is_a','DAG_PROJECT',RULESET_VERSION) for p,c in sorted(EDGES)];csv.writer((tax/'taxonomy_edges.tsv').open('w',newline=''),delimiter='\t',lineterminator='\n').writerows([['parent_id','child_id','relation_type','source','version'],*edge_rows])
 payload={'metadata':{'ruleset_version':RULESET_VERSION,'rdkit_version':rdBase.rdkitVersion},'nodes':[dict(zip(['id','name','definition','source','source_id','type','version','priority'],r)) for r in node_rows],'edges':[dict(zip(['parent','child','relation_type','source','version'],r)) for r in edge_rows]};(tax/'taxonomy.json').write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
 for i,n,d,p in NODES:G.nodes[i].update(name=n,definition=d,ontology_source='DAG_PROJECT',version=RULESET_VERSION,priority=p)
 for p,c in G.edges:G.edges[p,c].update(relation_type='is_a',source='DAG_PROJECT')
 nx.write_graphml(G,tax/'taxonomy.graphml')
 con.executemany('INSERT INTO provenance VALUES(?,?,?,?,?,?)',[('ZINC commercial BB source','2026-07-21','https://files.docking.org/catalogs/source/','2026-07-21',sha(raw/'manifest.json'),'ZINC terms: no redistribution of major portions without written permission'),('taxonomy_rules',RULESET_VERSION,'src/pilot_taxonomy.py','2026-07-21',sha(ROOT/'src/pilot_taxonomy.py'),'project code'),('RDKit',rdBase.rdkitVersion,'https://www.rdkit.org/','2026-07-21','','BSD-3-Clause')]);con.commit()
 fk=con.execute('PRAGMA foreign_key_check').fetchall();integrity=con.execute('PRAGMA integrity_check').fetchone()[0];members=con.execute('SELECT count(*) FROM compound_membership').fetchone()[0];con.execute('ANALYZE');con.commit();con.close()
 malformed=counts['malformed']; total=counts['raw_rows'];metrics={'raw_supplier_rows':total,'valid_format_rows':counts['valid_format_rows'],'malformed_or_blank_rows':malformed,'chemistry_failures':counts['chemistry_failures'],'successfully_standardized_rows':counts['valid_format_rows']-counts['chemistry_failures'],'duplicates_removed':counts['duplicates'],'final_unique_compounds':counts['unique'],'classified_compounds':counts['unique'],'partially_classified_unresolved':counts['unresolved'],'unclassified_compounds':0,'classification_coverage_percent':100.0 if counts['unique'] else 0,'single_direct_membership_compounds':direct_hist[1],'multiple_direct_membership_compounds':sum(v for k,v in direct_hist.items() if k>1),'direct_memberships':counts['direct_memberships'],'inferred_memberships':counts['inferred_memberships'],'taxonomy_nodes':G.number_of_nodes(),'taxonomy_edges':G.number_of_edges(),'root_nodes':sum(G.in_degree(n)==0 for n in G),'leaf_nodes':sum(G.out_degree(n)==0 for n in G),'maximum_depth':max(depths),'median_primary_path_depth':statistics.median(depths),'nodes_with_multiple_parents':sum(G.in_degree(n)>1 for n in G),'disconnected_components':nx.number_weakly_connected_components(G),'cycles':0,'zinc_id_mapped_unique_compounds':mapped,'zinc_id_missing_unique_compounds':counts['unique']-mapped,'info_mapping_rows_loaded':zinc_map_rows,'database_membership_rows':members,'ruleset_version':RULESET_VERSION,'rdkit_version':rdBase.rdkitVersion,'elapsed_seconds':round(time.time()-start,3),'workers':a.workers}
 (res/'full_metrics.json').write_text(json.dumps(metrics,indent=2,sort_keys=True)+'\n');validation={'status':'PASS' if not fk and integrity=='ok' and total==counts['chemistry_failures']+counts['duplicates']+counts['unique']+malformed and nx.is_directed_acyclic_graph(G) else 'FAIL','critical_errors':[] if not fk and integrity=='ok' else [f'integrity={integrity}, foreign_keys={len(fk)}'],'warnings':['Unresolved organic compounds are partial classifications, not authoritative ontology assignments','ZINC IDs mapped only by exact catalog, supplier code, and InChIKey; missing IDs were not fabricated'],'metrics':metrics};(res/'full_validation.json').write_text(json.dumps(validation,indent=2,sort_keys=True)+'\n');print(json.dumps(validation,indent=2))

if __name__=='__main__':main()
