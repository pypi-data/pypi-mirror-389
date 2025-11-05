# tests/test_recursive.py  
import unittest
import chemcalc_lib as cc

class TestRecursiveFunctionality(unittest.TestCase):
    """Test recursive mixture calculations based on example_recursive.py"""
    
    def setUp(self):
        """Set up test data from recursive example"""
        # Define basic components
        self.components = {
            "Water": {"name": "Water", "mw": 18.015, "vm": 18.0},
            "Ethanol": {"name": "Ethanol", "mw": 46.07, "vm": 58.0},
            "NaCl": {
                "name": "NaCl", "mw": 58.44, "vm": 27.0,
                "properties": {
                    "entities": [
                        {"name": "Na⁺", "stoichiometry": 1.0},
                        {"name": "Cl⁻", "stoichiometry": 1.0}
                    ]
                }
            }
        }
        
        # Define mixtures
        self.water_ethanol = {
            "name": "Water-Ethanol",
            "parents": [
                {"name": "Water", "amount": 70, "amount_type": "φ", "unit": "%"},
                {"name": "Ethanol", "amount": 30, "amount_type": "φ", "unit": "%"}
            ]
        }
        
        self.saline_solution = {
            "name": "Saline-Solution", 
            "parents": [
                {"name": "Water-Ethanol", "amount": 95, "amount_type": "V", "unit": "mL"},
                {"name": "NaCl", "amount": 0.9, "amount_type": "m", "unit": "g"}
            ]
        }
        
        # Create dictionary of all nodes
        self.all_nodes = {
            **self.components,
            "Water-Ethanol": self.water_ethanol,
            "Saline-Solution": self.saline_solution
        }
    
    def test_recursive_mole_fractions(self):
        """Test recursive mole fraction calculation"""
        results = cc.get_mole_fractions_recursive(self.all_nodes, include_entities=True)
        
        # Should return a list of terminal mixtures
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)  # One terminal mixture
        
        result = results[0]
        
        # Check expected keys
        self.assertIn('name', result)
        self.assertIn('mole_fractions', result)
        self.assertIn('entity_mole_fractions', result)
        self.assertIn('component list', result)
        
        self.assertEqual(result['name'], 'Saline-Solution')
        
        # Check that mole fractions sum to 1 (approximately)
        total_mole_fraction = sum(result['mole_fractions'].values())
        self.assertAlmostEqual(total_mole_fraction, 1.0, places=6)
        
        # Check that we have the expected entities
        self.assertIn('Na⁺', result['entity_mole_fractions'])
        self.assertIn('Cl⁻', result['entity_mole_fractions'])
    
    def test_node_classification(self):
        """Test that nodes are properly classified by level"""
        nodes_by_level, node_types = cc.classify_node_levels(self.all_nodes)
        
        # Check level classification
        self.assertEqual(len(nodes_by_level), 3)  # 3 levels: 0, 1, 2
        
        # Level 0 should have base components
        self.assertIn('Water', nodes_by_level[0])
        self.assertIn('Ethanol', nodes_by_level[0]) 
        self.assertIn('NaCl', nodes_by_level[0])
        
        # Level 1 should have Water-Ethanol
        self.assertIn('Water-Ethanol', nodes_by_level[1])
        
        # Level 2 should have Saline-Solution
        self.assertIn('Saline-Solution', nodes_by_level[2])
        
        # Check node types
        self.assertEqual(node_types['Water-Ethanol'], 'intermediate')
        self.assertEqual(node_types['Saline-Solution'], 'terminal')


if __name__ == '__main__':
    unittest.main()
