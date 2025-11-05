# tests/test_basic.py
import unittest
import numpy as np
import chemcalc_lib as cc

class TestBasicFunctionality(unittest.TestCase):
    """Test basic mixture calculations based on examples.py"""
    
    def setUp(self):
        """Set up test data from Example 1"""
        self.names = ["Water", "Ethanol", "NaCl"]
        self.amounts = [70.0, 30.0, 1.0]
        self.amount_types = ["φ", "φ", "c"]
        self.units = ["%", "%", "mol/L"]
        self.molar_weights = [18.02, 46.07, 58.44]
        self.molar_volumes = [18.0, 58.5, 27.0]
        self.entities = [[], [], ["Na+", "Cl-"]]
        self.stoichiometries = [[], [], [1.0, 1.0]]
        
        self.component_data = cc.create_mixture(
            self.names, self.amounts, self.amount_types, self.units,
            Mw=self.molar_weights, Vm=self.molar_volumes,
            entities=self.entities, stoichiometries=self.stoichiometries
        )
    
    def test_create_mixture(self):
        """Test that mixture creation works correctly"""
        self.assertEqual(len(self.component_data), 3)
        self.assertEqual(self.component_data[0]['name'], 'Water')
        self.assertEqual(self.component_data[2]['name'], 'NaCl')
        
    def test_get_mole_fractions(self):
        """Test mole fraction calculation"""
        result = cc.get_mole_fractions(self.component_data, include_entities=True)
        
        # Check that we get the expected keys
        self.assertIn('mole_fractions', result)
        self.assertIn('entity_mole_fractions', result)
        self.assertIn('average_molar_weight', result)
        
        # Check that mole fractions sum to 1 (approximately)
        total_mole_fraction = sum(result['mole_fractions'].values())
        self.assertAlmostEqual(total_mole_fraction, 1.0, places=6)
        
        # Check that entity mole fractions sum to 1 (approximately) 
        total_entity_fraction = sum(result['entity_mole_fractions'].values())
        self.assertAlmostEqual(total_entity_fraction, 1.0, places=6)
        
        # Check that we have the expected entities
        self.assertIn('Na+', result['entity_mole_fractions'])
        self.assertIn('Cl-', result['entity_mole_fractions'])
    
    def test_convert_to_target_amounts(self):
        """Test conversion to target amount types"""
        target_types = ["V", "V", "m"]
        total_amount = 1.0
        total_amount_type = "V"
        
        conversion = cc.convert(
            self.component_data, target_types, total_amount, total_amount_type
        )
        
        # Check that we get converted amounts
        self.assertIn('converted_amounts', conversion)
        self.assertIn('mole_fractions', conversion)
        
        # Check that all components have converted amounts
        for name in self.names:
            self.assertIn(name, conversion['converted_amounts'])
            
        # Check that target types are respected
        self.assertEqual(conversion['converted_amounts']['Water']['amount_type'], 'V')
        self.assertEqual(conversion['converted_amounts']['NaCl']['amount_type'], 'm')
    
    def test_populate_unit_cell(self):
        """Test unit cell population calculation"""
        result = cc.get_mole_fractions(self.component_data)
        
        mole_fractions = result['mole_fractions']
        molar_volumes = {"Water": 18.0, "Ethanol": 58.5, "NaCl": 27.0}
        entities = {
            "Water": [("Water", 1)],
            "Ethanol": [("Ethanol", 1)], 
            "NaCl": [("Na+", 1), ("Cl-", 1)]
        }
        cell = {'a': 15, 'b': 15, 'c': 15, 'alpha': 90, 'beta': 90, 'gamma': 90}
        
        unit_cell_result = cc.populate_unit_cell(
            mole_fractions, molar_volumes, entities, cell
        )
        
        # Check that we get expected keys
        self.assertIn('cell_volume_L', unit_cell_result)
        self.assertIn('total_moles', unit_cell_result)
        self.assertIn('component_counts', unit_cell_result)
        self.assertIn('entity_counts', unit_cell_result)
        
        # Check that entity counts include ions
        self.assertIn('Na+', unit_cell_result['entity_counts'])
        self.assertIn('Cl-', unit_cell_result['entity_counts'])


class TestMolalityFunctionality(unittest.TestCase):
    """Test molality calculations based on Example 2"""
    
    def test_molality_calculation(self):
        """Test molality handling from Example 2"""
        names = ["Water", "Ethanol", "NaCl", "Urea", "Hydroxybenzoic acid"]
        amounts = [70.0, 30.0, 1.0, 0.5, 0.8]
        amount_types = ["φ", "φ", "c", "b", "b"]
        units = ["%", "%", "mol/L", "mol/kg", "mol/kg"]
        molar_weights = [18.02, 46.07, 58.44, 60.06, 138.12]
        molar_volumes = [18.0, 58.5, 27.0, 45.5, 94.60]
        entities = [[], [], ["Na+", "Cl-"], [], []]
        stoichiometries = [[], [], [1.0, 1.0], [], []]
        
        component_data = cc.create_mixture(
            names, amounts, amount_types, units, Mw=molar_weights,
            Vm=molar_volumes, entities=entities, stoichiometries=stoichiometries
        )
        
        result = cc.get_mole_fractions(component_data, include_entities=True)
        
        # Should return a list for multiple molal solutes
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)  # Two molal solutes
        
        # Each result should have the expected keys
        for res in result:
            self.assertIn('mole_fractions', res)
            self.assertIn('entity_mole_fractions', res)


if __name__ == '__main__':
    unittest.main()
