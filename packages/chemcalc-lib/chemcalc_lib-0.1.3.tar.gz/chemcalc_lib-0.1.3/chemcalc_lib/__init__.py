"""
ChemCalc: A library for chemical mixture calculations and composition conversions.

This library provides functions for:
- Converting between different amount types (mass, volume, moles, concentrations, etc.)
- Calculating mole fractions from various mixture specifications
- Handling complex mixture compositions including entities and stoichiometry
- Supporting recursive mixture calculations
- Unit cell population calculations

Example usage:
    import chemcalc_lib as cc
    
    # Create mixture components
    components = cc.create_mixture(
        names=['Water', 'Ethanol'],
        amounts=[70, 30],
        amount_types=['φ', 'φ'],
        units=['%', '%'],
        Mw=[18.015, 46.068],
        Vm=[18.0, 58.4]
    )
    
    # Get mole fractions
    results = cc.get_mole_fractions(components)
    print(results['mole_fractions'])
"""

from .core import *

__version__ = "0.1.3"
__author__ = "Theophile Gaudin"
__email__ = "gaudin.theophile@gmail.com"
__description__ = "A library for chemical mixture calculations and composition conversions"

# Expose main functions at package level
__all__ = [
    # Basic utilities
    'create_mixture',
    'create_amount_matrix',
    'convert_to_standard_unit',
    'get_column_index',
    'get_mole_fractions',
    'convert',
    'extract_entities_information',
    
    # Recursive utilities  
    'distribute_mixture_component',
    'get_mole_fractions_recursive',
    'classify_node_levels',
    'collect_entities_information',
    
    # Calculation functions
    'mole_fraction_algebra',
    'entities_mole_fraction_algebra', 
    'amount_conversion_algebra',
    'populate_unit_cell',
    'solve_partitioned_system',
    'check_physically_valid',
    'calculate_mole_fractions_with_molality',
    'convert_molar_volume',
    
    # Constants
    'amount_type_to_std_unit'
]
