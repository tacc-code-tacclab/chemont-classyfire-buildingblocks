from rdkit import Chem
from src.pilot_taxonomy import direct_classes, graph, RULESET_VERSION
import networkx as nx

def classes(smiles): return direct_classes(Chem.MolFromSmiles(smiles))
def test_dag_and_version(): assert nx.is_directed_acyclic_graph(graph()) and RULESET_VERSION=="dag-rdkit-rules-1.1.1"
def test_boronic_acid_positive_negative():
 assert "DAGCHEM:0000600" in classes("OB(O)c1ccccc1")
 assert "DAGCHEM:0000600" not in classes("c1ccccc1")
def test_boronate_positive_negative():
 assert "DAGCHEM:0000601" in classes("CC1(C)OB(c2ccccc2)OC1(C)C")
 assert "DAGCHEM:0000601" not in classes("CCO")
def test_multifunctional_nonexclusive():
 c=classes("Nc1ncccc1F"); assert {"DAGCHEM:0000204","DAGCHEM:0000401","DAGCHEM:0000501","DAGCHEM:0000502"} <= c
def test_acid_not_ketone():
 c=classes("CC(=O)O"); assert "DAGCHEM:0000300" in c and "DAGCHEM:0000321" not in c
def test_nitro_is_not_amine(): assert "DAGCHEM:0000200" not in classes("C[N+](=O)[O-]")
def test_tertiary_aromatic_amine(): assert {"DAGCHEM:0000203","DAGCHEM:0000204"} <= classes("CN(C)c1ccccc1")
def test_primary_amine_not_multifunctional_from_ancestry(): assert "DAGCHEM:0000700" not in classes("CCN")
def test_hydrazine_not_organic(): assert "DAGCHEM:0000100" not in classes("NN")
def test_phenol_not_subclass_of_nonaromatic_alcohol(): assert ("DAGCHEM:0000310","DAGCHEM:0000311") not in graph().edges
def test_aniline_probe(): assert {"DAGCHEM:0000200","DAGCHEM:0000201","DAGCHEM:0000204"} <= classes("Nc1ccccc1")
def test_amide_and_sulfonamide_not_amines():
 assert "DAGCHEM:0000200" not in classes("CC(=O)N")
 assert "DAGCHEM:0000200" not in classes("CS(=O)(=O)N")
def test_aldehyde_and_ketone_discrimination():
 assert "DAGCHEM:0000320" in classes("CC=O") and "DAGCHEM:0000321" not in classes("CC=O")
 assert "DAGCHEM:0000321" in classes("CC(=O)C") and "DAGCHEM:0000320" not in classes("CC(=O)C")
def test_amidine_and_guanidine_are_not_amines():
 for smiles in ("CC(=N)N", "NC(=N)N"):
  c=classes(smiles)
  assert not ({"DAGCHEM:0000200","DAGCHEM:0000201","DAGCHEM:0000202","DAGCHEM:0000203","DAGCHEM:0000204"} & c)
def test_true_primary_amine_control_for_amidine_exclusion():
 assert {"DAGCHEM:0000200","DAGCHEM:0000201"} <= classes("CCN")
