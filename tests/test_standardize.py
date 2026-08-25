import unittest

from src.standardize import StandardizationError, standardize_smiles


class StandardizationTests(unittest.TestCase):
    def test_valid_molecule_fields(self):
        result = standardize_smiles("N[C@@H](C)C(=O)O")
        self.assertEqual(result.sanitisation_status, "success")
        self.assertTrue(result.inchikey)
        self.assertEqual(result.molecular_formula, "C3H7NO2")
        self.assertEqual(result.stereochemistry_status, "fully_specified")

    def test_salt_fragment_is_recorded_and_parent_retained(self):
        result = standardize_smiles("CC[NH3+].[Cl-]")
        self.assertEqual(result.fragment_count, 2)
        self.assertIn("[Cl-]", result.removed_fragments_smiles)
        self.assertEqual(result.formal_charge, 0)
        self.assertEqual(result.canonical_smiles, "CCN")

    def test_permanent_charge_is_retained(self):
        result = standardize_smiles("C[N+](C)(C)C")
        self.assertEqual(result.formal_charge, 1)

    def test_isotopes_are_preserved(self):
        result = standardize_smiles("[13CH3]CO")
        self.assertEqual(result.isotope_status, "preserved:1")
        self.assertIn("13", result.isomeric_smiles)

    def test_invalid_smiles_has_explicit_stage(self):
        with self.assertRaises(StandardizationError) as caught:
            standardize_smiles("not_a_smiles")
        self.assertEqual(caught.exception.stage, "smiles_parse")

    def test_tautomer_canonicalization_is_reproducible(self):
        first = standardize_smiles("O=c1cccc[nH]1")
        second = standardize_smiles("Oc1ccccn1")
        self.assertEqual(first.deduplication_key, second.deduplication_key)


if __name__ == "__main__":
    unittest.main()
