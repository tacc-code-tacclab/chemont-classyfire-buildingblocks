"""Versioned, deterministic RDKit taxonomy for the commercial-BB pilot."""
from __future__ import annotations

import csv, hashlib, json, sqlite3, statistics
from datetime import datetime, timezone
from collections import defaultdict
from pathlib import Path
import networkx as nx
import pandas as pd
from rdkit import Chem, rdBase

RULESET_VERSION = "dag-rdkit-rules-1.1.1"

NODES = [
 ("DAGCHEM:0000001","Chemical entity","A molecular chemical entity",0),
 ("DAGCHEM:0000100","Organic compound","Compound containing carbon",10),
 ("DAGCHEM:0000110","Nitrogen-containing organic compound","Organic compound containing nitrogen",20),
 ("DAGCHEM:0000120","Oxygen-containing organic compound","Organic compound containing oxygen",20),
 ("DAGCHEM:0000130","Sulfur-containing organic compound","Organic compound containing sulfur",20),
 ("DAGCHEM:0000140","Phosphorus-containing organic compound","Organic compound containing phosphorus",20),
 ("DAGCHEM:0000150","Boron-containing organic compound","Organic compound containing boron",20),
 ("DAGCHEM:0000200","Amine","Organic nitrogen compound with an amine nitrogen",40),
 ("DAGCHEM:0000201","Primary amine","Amine nitrogen bearing two hydrogens",70),
 ("DAGCHEM:0000202","Secondary amine","Amine nitrogen bearing one hydrogen",70),
 ("DAGCHEM:0000203","Tertiary amine","Amine nitrogen bearing no hydrogens",65),
 ("DAGCHEM:0000204","Aromatic amine","Amine nitrogen directly bonded to an aromatic atom",90),
 ("DAGCHEM:0000300","Carboxylic acid","Compound containing a carboxylic acid group",80),
 ("DAGCHEM:0000310","Alcohol","Compound containing a non-aromatic hydroxyl group",55),
 ("DAGCHEM:0000311","Phenol","Compound containing an aromatic hydroxyl group",80),
 ("DAGCHEM:0000320","Aldehyde","Compound containing an aldehyde carbonyl",75),
 ("DAGCHEM:0000321","Ketone","Compound containing a ketone carbonyl",70),
 ("DAGCHEM:0000400","Organohalogen compound","Organic compound with a carbon-halogen bond",45),
 ("DAGCHEM:0000401","Organofluorine compound","Organic compound with a carbon-fluorine bond",65),
 ("DAGCHEM:0000402","Organochlorine compound","Organic compound with a carbon-chlorine bond",65),
 ("DAGCHEM:0000403","Organobromine compound","Organic compound with a carbon-bromine bond",65),
 ("DAGCHEM:0000404","Organoiodine compound","Organic compound with a carbon-iodine bond",65),
 ("DAGCHEM:0000500","Heterocyclic compound","Compound containing a ring heteroatom",55),
 ("DAGCHEM:0000501","Heteroaromatic compound","Aromatic compound containing an aromatic heteroatom",75),
 ("DAGCHEM:0000502","Pyridine","Compound containing a pyridine ring",100),
 ("DAGCHEM:0000600","Boronic acid","Compound containing a carbon-bound boronic acid group",100),
 ("DAGCHEM:0000601","Boronate ester","Compound containing a carbon-bound boronate ester group",100),
 ("DAGCHEM:0000700","Multifunctional compound","Compound assigned at least two specific direct structural classes",5),
 ("DAGCHEM:0000800","Unresolved organic compound","Organic compound with no specific direct rule assignment",-100),
]

EDGES = [
 ("DAGCHEM:0000001","DAGCHEM:0000100"),
 *[("DAGCHEM:0000100",x) for x in ["DAGCHEM:0000110","DAGCHEM:0000120","DAGCHEM:0000130","DAGCHEM:0000140","DAGCHEM:0000150","DAGCHEM:0000400","DAGCHEM:0000500","DAGCHEM:0000700","DAGCHEM:0000800"]],
 ("DAGCHEM:0000110","DAGCHEM:0000200"),
 *[("DAGCHEM:0000200",x) for x in ["DAGCHEM:0000201","DAGCHEM:0000202","DAGCHEM:0000203","DAGCHEM:0000204"]],
 ("DAGCHEM:0000120","DAGCHEM:0000300"),("DAGCHEM:0000120","DAGCHEM:0000310"),("DAGCHEM:0000120","DAGCHEM:0000311"),("DAGCHEM:0000120","DAGCHEM:0000320"),("DAGCHEM:0000120","DAGCHEM:0000321"),
 *[("DAGCHEM:0000400",x) for x in ["DAGCHEM:0000401","DAGCHEM:0000402","DAGCHEM:0000403","DAGCHEM:0000404"]],
 ("DAGCHEM:0000500","DAGCHEM:0000501"),("DAGCHEM:0000501","DAGCHEM:0000502"),
 ("DAGCHEM:0000150","DAGCHEM:0000600"),("DAGCHEM:0000150","DAGCHEM:0000601"),
 ("DAGCHEM:0000120","DAGCHEM:0000600"),("DAGCHEM:0000120","DAGCHEM:0000601"),
]

SMARTS = {
 "DAGCHEM:0000110":"[#6].[#7]", "DAGCHEM:0000120":"[#6].[#8]", "DAGCHEM:0000130":"[#6].[#16]", "DAGCHEM:0000140":"[#6].[#15]", "DAGCHEM:0000150":"[#6].[#5]",
 "DAGCHEM:0000200":"[NX3;!$([N+](=O)[O-]);!$(N-C=O);!$(N-S(=O)=O);!$([N]-C=[N])]", "DAGCHEM:0000201":"[NX3;H2;!$([N+](=O)[O-]);!$(N-C=O);!$(N-S(=O)=O);!$([N]-C=[N])]", "DAGCHEM:0000202":"[NX3;H1;!$([N+](=O)[O-]);!$(N-C=O);!$(N-S(=O)=O);!$([N]-C=[N])]", "DAGCHEM:0000203":"[NX3;H0;!$([N+]);!$(N-C=O);!$(N-S(=O)=O);!$([N]-C=[N])]", "DAGCHEM:0000204":"[NX3;H0,H1,H2;!$([N+]);!$(N-C=O);!$(N-S(=O)=O);!$([N]-C=[N])]-[a]",
 "DAGCHEM:0000300":"[CX3](=O)[OX2H1]", "DAGCHEM:0000310":"[CX4][OX2H1]", "DAGCHEM:0000311":"[c][OX2H1]", "DAGCHEM:0000320":"[CX3H1](=O)[#6]", "DAGCHEM:0000321":"[#6][CX3](=O)[#6]",
 "DAGCHEM:0000400":"[#6][F,Cl,Br,I]", "DAGCHEM:0000401":"[#6]F", "DAGCHEM:0000402":"[#6]Cl", "DAGCHEM:0000403":"[#6]Br", "DAGCHEM:0000404":"[#6]I",
 "DAGCHEM:0000501":"[a;!#6]", "DAGCHEM:0000502":"n1ccccc1", "DAGCHEM:0000600":"[#6]-[BX3]([OX2H1])[OX2H1]", "DAGCHEM:0000601":"[#6]-[BX3]([OX2;H0])([OX2;H0])",
}

def graph():
 g=nx.DiGraph(); g.add_nodes_from(x[0] for x in NODES); g.add_edges_from(EDGES); return g

def compile_rules(): return {k:Chem.MolFromSmarts(v) for k,v in SMARTS.items()}

def direct_classes(mol, rules=None):
 rules=rules or compile_rules()
 if not any(a.GetAtomicNum()==6 for a in mol.GetAtoms()): return {"DAGCHEM:0000001"}
 out={"DAGCHEM:0000100"}
 for node,q in rules.items():
  if q and mol.HasSubstructMatch(q): out.add(node)
 ring=mol.GetRingInfo().AtomRings()
 if any(any(mol.GetAtomWithIdx(i).GetAtomicNum()!=6 for i in r) for r in ring): out.add("DAGCHEM:0000500")
 families=set()
 if out & {"DAGCHEM:0000200","DAGCHEM:0000201","DAGCHEM:0000202","DAGCHEM:0000203","DAGCHEM:0000204"}: families.add("amine")
 for node,family in [("DAGCHEM:0000300","acid"),("DAGCHEM:0000310","hydroxyl"),("DAGCHEM:0000311","hydroxyl"),("DAGCHEM:0000320","aldehyde"),("DAGCHEM:0000321","ketone"),("DAGCHEM:0000130","sulfur"),("DAGCHEM:0000140","phosphorus")]:
  if node in out: families.add(family)
 if out & {"DAGCHEM:0000401","DAGCHEM:0000402","DAGCHEM:0000403","DAGCHEM:0000404"}: families.add("halogen")
 if out & {"DAGCHEM:0000500","DAGCHEM:0000501","DAGCHEM:0000502"}: families.add("heterocycle")
 if out & {"DAGCHEM:0000600","DAGCHEM:0000601"}: families.add("boron")
 specific=set().union(out & {"DAGCHEM:0000130","DAGCHEM:0000140","DAGCHEM:0000200","DAGCHEM:0000201","DAGCHEM:0000202","DAGCHEM:0000203","DAGCHEM:0000204","DAGCHEM:0000300","DAGCHEM:0000310","DAGCHEM:0000311","DAGCHEM:0000320","DAGCHEM:0000321","DAGCHEM:0000401","DAGCHEM:0000402","DAGCHEM:0000403","DAGCHEM:0000404","DAGCHEM:0000500","DAGCHEM:0000501","DAGCHEM:0000502","DAGCHEM:0000600","DAGCHEM:0000601"})
 if len(families)>=2: out.add("DAGCHEM:0000700")
 if not specific: out.add("DAGCHEM:0000800")
 return out

def classify(df):
 g=graph(); rules=compile_rules(); memberships=[]; paths=[]; priorities={x[0]:x[3] for x in NODES}; names={x[0]:x[1] for x in NODES}
 depths={n:max((len(p)-1 for p in nx.all_simple_paths(g,"DAGCHEM:0000001",n)),default=0) for n in g}
 for row in df.itertuples(index=False):
  mol=Chem.MolFromSmiles(row.isomeric_smiles); direct=direct_classes(mol,rules)
  for c in sorted(direct): memberships.append((row.source_compound_id,c,"direct","rdkit_smarts_or_property",f"{RULESET_VERSION}:{SMARTS.get(c,'property_predicate')}",1 if c==max(direct,key=lambda x:(depths[x],priorities[x],x)) else 0))
  ancestors=set().union(*(nx.ancestors(g,c) for c in direct))-direct
  for c in sorted(ancestors): memberships.append((row.source_compound_id,c,"inferred_assignment","dag_ancestor_propagation",f"ancestor of direct membership under {RULESET_VERSION}",0))
  primary=max(direct,key=lambda x:(depths[x],priorities[x],x)); candidates=list(nx.all_simple_paths(g,"DAGCHEM:0000001",primary)); path=max(candidates,key=lambda p:(len(p),tuple(p)))
  paths.append((row.source_compound_id,primary," > ".join(names[x] for x in path),json.dumps(path)))
 return memberships,paths

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write_tsv(path, header, rows):
 with open(path,"w",newline="") as f:
  w=csv.writer(f,delimiter="\t",lineterminator="\n"); w.writerow(header); w.writerows(rows)

def preserve(path):
 path=Path(path)
 if path.exists():
  stamp=datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
  path.rename(path.with_name(path.name+f".old_{stamp}"))

def build(root: Path):
 inp=root/"data/processed/pilot_compounds_standardised.tsv"; df=pd.read_csv(inp,sep="\t",dtype=str); g=graph()
 if not nx.is_directed_acyclic_graph(g): raise ValueError("taxonomy graph has cycle")
 memberships,paths=classify(df); node_rows=[(i,n,d,"DAG_PROJECT",i,"chemical_class",RULESET_VERSION,p) for i,n,d,p in NODES]
 edge_rows=[(p,c,"is_a","DAG_PROJECT",RULESET_VERSION) for p,c in sorted(EDGES)]
 tax=root/"taxonomy"; dbp=root/"database/chemical_taxonomy_pilot.db"
 for target in [tax/"pilot_taxonomy_nodes.tsv",tax/"pilot_taxonomy_edges.tsv",tax/"pilot_compound_membership.tsv",tax/"pilot_compound_primary_paths.tsv",tax/"pilot_taxonomy.json",tax/"pilot_taxonomy.graphml",dbp,root/"results/pilot/pilot_metrics.json"]: preserve(target)
 write_tsv(tax/"pilot_taxonomy_nodes.tsv",["node_id","name","definition","ontology_source","ontology_source_id","node_type","version","priority"],node_rows)
 write_tsv(tax/"pilot_taxonomy_edges.tsv",["parent_id","child_id","relation_type","source","version"],edge_rows)
 names={x[0]:x[1] for x in NODES}
 membership_export=[(cid,cl,names[cl],"DAG_PROJECT",cl,typ,evidence,method,primary) for cid,cl,typ,method,evidence,primary in memberships]
 write_tsv(tax/"pilot_compound_membership.tsv",["compound_id","class_id","class_name","ontology_source","source_class_id","membership_type","evidence","classification_method","is_primary"],membership_export)
 write_tsv(tax/"pilot_compound_primary_paths.tsv",["compound_id","primary_leaf_class","taxonomy_path","node_id_path"],paths)
 data={"metadata":{"ruleset_version":RULESET_VERSION,"rdkit_version":rdBase.rdkitVersion},"nodes":[dict(zip(["id","name","definition","source","source_id","type","version","priority"],r)) for r in node_rows],"edges":[dict(zip(["parent","child","relation_type","source","version"],r)) for r in edge_rows]}
 (tax/"pilot_taxonomy.json").write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")
 for i,n,d,p in NODES: g.nodes[i].update(name=n,definition=d,ontology_source="DAG_PROJECT",version=RULESET_VERSION,priority=p)
 for p,c in g.edges: g.edges[p,c].update(relation_type="is_a",source="DAG_PROJECT")
 nx.write_graphml(g,tax/"pilot_taxonomy.graphml")
 con=sqlite3.connect(dbp); con.execute("PRAGMA foreign_keys=ON")
 con.executescript("""
 CREATE TABLE compounds(compound_id TEXT PRIMARY KEY,source TEXT NOT NULL,source_id TEXT NOT NULL,original_smiles TEXT,canonical_smiles TEXT,isomeric_smiles TEXT,inchi TEXT,inchikey TEXT,molecular_formula TEXT,molecular_weight REAL,formal_charge INTEGER,commercial_status TEXT,supplier TEXT,standardisation_status TEXT);
 CREATE TABLE taxonomy_nodes(node_id TEXT PRIMARY KEY,name TEXT NOT NULL,definition TEXT,ontology_source TEXT NOT NULL,ontology_source_id TEXT,node_type TEXT NOT NULL,version TEXT NOT NULL,priority INTEGER NOT NULL);
 CREATE TABLE taxonomy_edges(parent_id TEXT NOT NULL REFERENCES taxonomy_nodes,child_id TEXT NOT NULL REFERENCES taxonomy_nodes,relation_type TEXT NOT NULL,source TEXT NOT NULL,PRIMARY KEY(parent_id,child_id,relation_type));
 CREATE TABLE compound_membership(compound_id TEXT NOT NULL REFERENCES compounds,class_id TEXT NOT NULL REFERENCES taxonomy_nodes,membership_type TEXT NOT NULL,source TEXT NOT NULL,evidence TEXT NOT NULL,is_primary INTEGER NOT NULL CHECK(is_primary IN(0,1)),PRIMARY KEY(compound_id,class_id,membership_type));
 CREATE TABLE taxonomy_paths(compound_id TEXT PRIMARY KEY REFERENCES compounds,primary_leaf_class TEXT NOT NULL REFERENCES taxonomy_nodes,taxonomy_path TEXT NOT NULL,node_id_path TEXT NOT NULL);
 CREATE TABLE provenance(resource TEXT PRIMARY KEY,version TEXT,url TEXT,download_date TEXT,checksum TEXT,licence TEXT);
 CREATE INDEX idx_compounds_inchikey ON compounds(inchikey); CREATE INDEX idx_membership_class ON compound_membership(class_id); CREATE INDEX idx_edges_child ON taxonomy_edges(child_id);
 """)
 comp=[(r.source_compound_id,r.source,r.zinc_id,r.original_smiles,r.canonical_smiles,r.isomeric_smiles,r.inchi,r.inchikey,r.molecular_formula,float(r.molecular_weight),int(r.formal_charge),r.commercial_status,r.supplier,r.sanitisation_status) for r in df.itertuples(index=False)]
 con.executemany("INSERT INTO compounds VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",comp); con.executemany("INSERT INTO taxonomy_nodes VALUES(?,?,?,?,?,?,?,?)",node_rows); con.executemany("INSERT INTO taxonomy_edges(parent_id,child_id,relation_type,source) VALUES(?,?,?,?)",[(a,b,c,d) for a,b,c,d,_ in edge_rows]); con.executemany("INSERT INTO compound_membership VALUES(?,?,?,?,?,?)",memberships); con.executemany("INSERT INTO taxonomy_paths VALUES(?,?,?,?)",paths)
 con.executemany("INSERT INTO provenance VALUES(?,?,?,?,?,?)",[("standardized_pilot","local",str(inp.relative_to(root)),"2026-07-21",sha(inp),"project data"),("taxonomy_rules",RULESET_VERSION,"src/pilot_taxonomy.py","2026-07-21",sha(__file__),"project code"),("RDKit",rdBase.rdkitVersion,"https://www.rdkit.org/","2026-07-21","","BSD-3-Clause")]); con.commit(); con.close()
 depths=[len(json.loads(x[3]))-1 for x in paths]; direct_counts=defaultdict(int)
 for cid,cl,typ,*_ in memberships:
  if typ=="direct": direct_counts[cid]+=1
 metrics={"raw_standardized_compounds":len(df),"classified_compounds":sum(v>0 for v in direct_counts.values()),"unclassified_compounds":0,"direct_memberships":sum(direct_counts.values()),"inferred_memberships":sum(1 for x in memberships if x[2]=="inferred_assignment"),"compounds_with_multiple_direct_memberships":sum(v>1 for v in direct_counts.values()),"multiple_membership_percent":100*sum(v>1 for v in direct_counts.values())/len(df),"taxonomy_nodes":g.number_of_nodes(),"taxonomy_edges":g.number_of_edges(),"root_nodes":sum(g.in_degree(n)==0 for n in g),"leaf_nodes":sum(g.out_degree(n)==0 for n in g),"maximum_hierarchy_depth":max(depths),"median_primary_path_depth":statistics.median(depths),"nodes_with_multiple_parents":sum(g.in_degree(n)>1 for n in g),"disconnected_components":nx.number_weakly_connected_components(g),"cycles":0,"ruleset_version":RULESET_VERSION}
 (root/"results/pilot/pilot_metrics.json").write_text(json.dumps(metrics,indent=2,sort_keys=True)+"\n")
 return metrics
