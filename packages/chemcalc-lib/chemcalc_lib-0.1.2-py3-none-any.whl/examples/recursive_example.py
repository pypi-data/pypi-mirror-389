#!/usr/bin/env python3
"""
Example script demonstrating how to use the library
"""

''' Example 2: mole fractions, and conversion, of a complex solution prepared in multiple steps with three solvents and three different salts'''

# Import the library

import ChemCalc_lib as cc

# Define basic components (leaf nodes)
# Because of the recursive structure, the user needs to define the dictionaries directly.
components = {
    "Water": {
        "name": "Water",
        "mw": 18.015,  # g/mol
        "vm": 18.0,    # mL/mol
    },
    "Ethanol": {
        "name": "Ethanol",
        "mw": 46.07,   # g/mol
        "vm": 58.0,    # mL/mol
    },
    "Glycerol": {
        "name": "Glycerol",
        "mw": 92.09,   # g/mol
        "vm": 73.0,    # mL/mol
    },
    "NaCl": {
        "name": "NaCl",
        "mw": 58.44,   # g/mol
        "vm": 27.0,    # mL/mol
        "properties": {
            "entities": [
                {"name": "Na⁺", "stoichiometry": 1.0},
                {"name": "Cl⁻", "stoichiometry": 1.0}
            ]
        }
    },
    "KCl": {
        "name": "KCl",
        "mw": 74.55,   # g/mol
        "vm": 37.0,    # mL/mol
        "properties": {
            "entities": [
                {"name": "K⁺", "stoichiometry": 1.0},
                {"name": "Cl⁻", "stoichiometry": 1.0}
            ]
        }
    },
    "CaCl₂": {
        "name": "CaCl₂",
        "mw": 110.98,  # g/mol
        "vm": 51.0,    # mL/mol
        "properties": {
            "entities": [
                {"name": "Ca²⁺", "stoichiometry": 1.0},
                {"name": "Cl⁻", "stoichiometry": 2.0}
            ]
        }
    }
}

water_ethanol = {
    "name": "Water-Ethanol",
    "parents": [
        {"name": "Water", "amount": 70, "amount_type": "φ", "unit": "%"},
        {"name": "Ethanol", "amount": 30, "amount_type": "φ", "unit": "%"}
    ]
}

glycerol_solution = {
    "name": "Glycerol-Water",
    "parents": [
        {"name": "Water", "amount": 90, "amount_type": "w", "unit": "%"},
        {"name": "Glycerol", "amount": 10, "amount_type": "w", "unit": "%"}
    ]
}

salt_mixture = {
    "name": "Salt-Mix",
    "parents": [
        {"name": "NaCl", "amount": 60, "amount_type": "w", "unit": "%"},
        {"name": "KCl", "amount": 30, "amount_type": "w", "unit": "%"},
        {"name": "CaCl₂", "amount": 10, "amount_type": "w", "unit": "%"}
    ]
}

hydroalcoholic_base = {
    "name": "Hydroalcoholic-Base",
    "parents": [
        {"name": "Water-Ethanol", "amount": 80, "amount_type": "w", "unit": "%"},
        {"name": "Glycerol-Water", "amount": 20, "amount_type": "w", "unit": "%"}
    ]
}

saline_solution = {
    "name": "Saline-Solution",
    "parents": [
        {"name": "Water-Ethanol", "amount": 95, "amount_type": "V", "unit": "mL"},
        {"name": "NaCl", "amount": 0.9, "amount_type": "m", "unit": "g"}
    ]
}

complex_solution = {
    "name": "Complex-Solution",
    "parents": [
        {"name": "Hydroalcoholic-Base", "amount": 90, "amount_type": "V", "unit": "mL"},
        {"name": "Salt-Mix", "amount": 2, "amount_type": "m", "unit": "g"}
    ]
}

# Create dictionary of all nodes
all_nodes = {
    # Components
    "Water": components["Water"],
    "Ethanol": components["Ethanol"],
    "Glycerol": components["Glycerol"],
    "NaCl": components["NaCl"],
    "KCl": components["KCl"],
    "CaCl₂": components["CaCl₂"],
    
    # Mixtures
    "Water-Ethanol": water_ethanol,
    "Glycerol-Water": glycerol_solution,
    "Salt-Mix": salt_mixture,
    "Hydroalcoholic-Base": hydroalcoholic_base, 
    "Saline-Solution": saline_solution,
    "Complex-Solution": complex_solution
}

# Calculate properties of all terminal mixtures
results = cc.get_mole_fractions_recursive(all_nodes, include_entities=True)

# Print results for each terminal mixture
for mixture in results:
    #rounding to make it easier to read
    mf_rounded = {k: round(v, 4) for k, v in mixture["mole_fractions"].items()}
    emf_rounded = {k: round(v, 4) for k, v in mixture["entity_mole_fractions"].items()}
    
    #actual print
    print("Terminal mixture:"      , mixture["name"])
    print("Mole fractions       :", mf_rounded)
    print("Entity mole fractions:", emf_rounded)
    print("")

# Convert to target amounts for all terminal mixtures
# Define target types for components in each terminal mixture
target_types = {
    "Saline-Solution": ["V", "V", "m"],  # Volume for water-ethanol, mass for NaCl
    "Complex-Solution": ["V", "V", "V", "m", "m", "m"]  # Different types for each component
}

total_amounts = {
    "Saline-Solution" : 1,    # 1   L
    "Complex-Solution": 0.5   # 0.5 L
}

total_amount_types = {
    "Saline-Solution": "V",  # Volume
    "Complex-Solution": "V"  # Volume
}

# Process each terminal mixture for conversion
for mixture in results:
    # Convert to target amounts
    conversion = cc.convert(mixture["component list"], target_types[mixture["name"]], total_amounts[mixture["name"]], total_amount_types[mixture["name"]])
    
    # Print converted amounts
    print("Amounts to prepare a 1L solution for", mixture["name"], ":")
    for comp_name, data in conversion["converted_amounts"].items():
        if data["amount_type"] == "V":
            print(comp_name, round(data["amount"],2), "L")
        elif data["amount_type"] == "m":
            print(comp_name, round(data["amount"],2), "g")
    print("")