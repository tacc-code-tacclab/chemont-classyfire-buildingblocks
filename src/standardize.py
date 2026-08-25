"""Transparent RDKit molecular standardisation for building blocks."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from rdkit.Chem.MolStandardize import rdMolStandardize


@dataclass(frozen=True)
class StandardizationResult:
    canonical_smiles: str
    isomeric_smiles: str
    inchi: str
    inchikey: str
    molecular_formula: str
    molecular_weight: float
    formal_charge: int
    heavy_atom_count: int
    stereochemistry_status: str
    sanitisation_status: str
    fragment_count: int
    fragment_policy: str
    removed_fragments_smiles: str
    charge_normalisation: str
    tautomer_policy: str
    isotope_status: str
    deduplication_key: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


class StandardizationError(ValueError):
    """A molecule could not be standardized."""

    def __init__(self, stage: str, reason: str):
        super().__init__(reason)
        self.stage = stage
        self.reason = reason


def _smiles(mol: Chem.Mol, isomeric: bool = True) -> str:
    return Chem.MolToSmiles(mol, canonical=True, isomericSmiles=isomeric)


def _choose_fragment(mol: Chem.Mol) -> tuple[Chem.Mol, int, str]:
    fragments = list(Chem.GetMolFrags(mol, asMols=True, sanitizeFrags=True))
    if not fragments:
        raise StandardizationError("fragment_selection", "no molecular fragments found")
    chooser = rdMolStandardize.LargestFragmentChooser(preferOrganic=True)
    selected = chooser.choose(mol)
    selected_key = _smiles(selected)
    removed: list[str] = []
    skipped_selected = False
    for fragment in fragments:
        value = _smiles(fragment)
        if not skipped_selected and value == selected_key:
            skipped_selected = True
        else:
            removed.append(value)
    return selected, len(fragments), ".".join(sorted(removed))


def _stereo_status(mol: Chem.Mol) -> str:
    elements = list(Chem.FindPotentialStereo(mol))
    if not elements:
        return "no_potential_stereochemistry"
    specified = sum(item.specified == Chem.StereoSpecified.Specified for item in elements)
    if specified == len(elements):
        return "fully_specified"
    if specified == 0:
        return "unspecified"
    return "partially_specified"


def standardize_smiles(smiles: str) -> StandardizationResult:
    if not smiles or not smiles.strip():
        raise StandardizationError("input_validation", "empty SMILES")
    try:
        mol = Chem.MolFromSmiles(smiles, sanitize=True)
    except Exception as exc:
        raise StandardizationError("smiles_parse", f"RDKit exception: {exc}") from exc
    if mol is None:
        raise StandardizationError("smiles_parse", "RDKit returned no molecule")

    try:
        selected, fragment_count, removed = _choose_fragment(mol)
        cleaned = rdMolStandardize.Cleanup(selected)
        charge_before = Chem.GetFormalCharge(cleaned)
        uncharged = rdMolStandardize.Uncharger().uncharge(cleaned)
        charge_after = Chem.GetFormalCharge(uncharged)
        enumerator = rdMolStandardize.TautomerEnumerator()
        enumerator.SetRemoveSp3Stereo(False)
        enumerator.SetRemoveBondStereo(False)
        enumerator.SetReassignStereo(True)
        canonical = enumerator.Canonicalize(uncharged)
        Chem.SanitizeMol(canonical)
        Chem.AssignStereochemistry(canonical, cleanIt=True, force=True)
    except StandardizationError:
        raise
    except Exception as exc:
        raise StandardizationError("rdkit_standardisation", f"RDKit exception: {exc}") from exc

    try:
        isomeric_smiles = _smiles(canonical, isomeric=True)
        canonical_smiles = _smiles(canonical, isomeric=False)
        inchi = Chem.MolToInchi(canonical)
        inchikey = Chem.InchiToInchiKey(inchi)
    except Exception as exc:
        raise StandardizationError("identifier_generation", f"RDKit exception: {exc}") from exc
    if not inchi or not inchikey:
        raise StandardizationError("identifier_generation", "empty InChI or InChIKey")

    isotope_count = sum(1 for atom in canonical.GetAtoms() if atom.GetIsotope())
    return StandardizationResult(
        canonical_smiles=canonical_smiles,
        isomeric_smiles=isomeric_smiles,
        inchi=inchi,
        inchikey=inchikey,
        molecular_formula=rdMolDescriptors.CalcMolFormula(canonical),
        molecular_weight=round(Descriptors.MolWt(canonical), 6),
        formal_charge=Chem.GetFormalCharge(canonical),
        heavy_atom_count=canonical.GetNumHeavyAtoms(),
        stereochemistry_status=_stereo_status(canonical),
        sanitisation_status="success",
        fragment_count=fragment_count,
        fragment_policy="largest_organic_fragment_retained; removed fragments recorded",
        removed_fragments_smiles=removed,
        charge_normalisation=(
            f"rdkit_cleanup_then_uncharger:{charge_before}->{charge_after}"
        ),
        tautomer_policy="RDKit TautomerEnumerator canonical tautomer",
        isotope_status=(f"preserved:{isotope_count}" if isotope_count else "none"),
        deduplication_key=isomeric_smiles,
    )
