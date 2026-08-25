#!/usr/bin/env python3
import csv,json,sys
from pathlib import Path
import networkx as nx
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from src.pilot_taxonomy import graph
g=graph(); root="DAGCHEM:0000001"
depth={n:max((len(p)-1 for p in nx.all_simple_paths(g,root,n)),default=0) for n in g}
tree=[]
for child in sorted(set(g)-{root}):
 parents=sorted(g.predecessors(child)); parent=max(parents,key=lambda p:(depth[p],p)); tree.append((parent,child,"primary_is_a","deterministic_parent_projection"))
out=ROOT/"taxonomy/pilot_taxonomy_tree_edges.tsv"
with open(out,"w",newline="") as f:
 w=csv.writer(f,delimiter="\t",lineterminator="\n");w.writerow(["parent_id","child_id","relation_type","source"]);w.writerows(tree)
with open(ROOT/"taxonomy/pilot_compound_membership.tsv") as f: mem=list(csv.DictReader(f,delimiter="\t"))
generic={"DAGCHEM:0000001","DAGCHEM:0000100","DAGCHEM:0000110","DAGCHEM:0000120","DAGCHEM:0000130","DAGCHEM:0000140","DAGCHEM:0000150","DAGCHEM:0000400","DAGCHEM:0000500","DAGCHEM:0000700","DAGCHEM:0000800"}
direct={}
for m in mem:
 if m['membership_type']=='direct' and m['class_id'] not in generic: direct.setdefault(m['compound_id'],set()).add(m['class_id'])
meaningful={cid:{x for x in classes if not any(x!=y and nx.has_path(g,x,y) for y in classes)} for cid,classes in direct.items()}
stats={"dag_edges":g.number_of_edges(),"tree_edges":len(tree),"class_edges_lost_by_primary_parent_tree":g.number_of_edges()-len(tree),"classes_with_multiple_parents":sum(g.in_degree(n)>1 for n in g),"meaningful_maximally_specific_direct_memberships":sum(map(len,meaningful.values())),"compounds_with_multiple_meaningful_direct_memberships":sum(len(v)>1 for v in meaningful.values()),"hypothetical_meaningful_memberships_lost_by_one_primary_membership_only":sum(max(0,len(v)-1) for v in meaningful.values()),"note":"Tree edge loss and hypothetical compound primary-only loss are separate; the canonical DAG retains every membership."}
(ROOT/"results/pilot/dag_vs_tree_metrics.json").write_text(json.dumps(stats,indent=2,sort_keys=True)+"\n");print(json.dumps(stats,indent=2))
