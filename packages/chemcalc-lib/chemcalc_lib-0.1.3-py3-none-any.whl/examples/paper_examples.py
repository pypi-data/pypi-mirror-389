#!/usr/bin/env python3
"""
Advanced application examples from Section 4.2 of the manuscript.
These examples demonstrate the use of ChemCalc for complex real-world 
chemical mixture calculations.
"""

import ChemCalc_lib as cc

print("="*70)
print("Section 4.2.1: Simulation of a battery formulation")
print("="*70)
print()

# Battery-grade electrolyte: 80wt% of 1.2 mol/kg of LiPF6 in EC/EMC/DMC 25:5:70 w/w/w
# and 20wt% of methyl acetate

# Note: This example uses a recursive mixture structure to demonstrate
# the full capability of ChemCalc. The mixture tree is:
# Battery Electrolyte (80wt% LiPF6 solution + 20wt% methyl acetate)
#   ├─ LiPF6 solution (1.2 mol/kg in EC/EMC/DMC solvent)
#   │   ├─ EC
#   │   ├─ EMC
#   │   ├─ DMC
#   │   └─ LiPF6
#   └─ Methyl acetate

# Define components
components = {
    "EC": {
        "name": "EC",
        "mw": 88.06,  # g/mol
    },
    "EMC": {
        "name": "EMC",
        "mw": 104.11, # g/mol
    },
    "DMC": {
        "name": "DMC",
        "mw": 90.08,  # g/mol
    },
    "LiPF6": {
        "name": "LiPF6",
        "mw": 151.91, # g/mol
        "properties": {
            "entities": [
                {"name": "Li+", "stoichiometry": 1.0},
                {"name": "PF6-", "stoichiometry": 1.0}
            ]
        }
    },
    "MethylAcetate": {
        "name": "MethylAcetate",
        "mw": 74.08,  # g/mol
    }
}

# Create the EC/EMC/DMC mixture (25:5:70 w/w/w)
lipf6_solution = {
    "name": "LiPF6-Solution",
    "parents": [
        {"name": "EC", "amount": 25, "amount_type": "w", "unit": "%"},
        {"name": "EMC", "amount": 5, "amount_type": "w", "unit": "%"},
        {"name": "DMC", "amount": 70, "amount_type": "w", "unit": "%"},
        {"name": "LiPF6", "amount": 1.2, "amount_type": "b", "unit": "mol/kg"}
    ]
}

# Final battery electrolyte (80wt% of LiPF6 solution + 20wt% methyl acetate)
battery_electrolyte = {
    "name": "Battery-Electrolyte",
    "parents": [
        {"name": "LiPF6-Solution", "amount": 80, "amount_type": "w", "unit": "%"},
        {"name": "MethylAcetate", "amount": 20, "amount_type": "w", "unit": "%"}
    ]
}

# Create dictionary of all nodes
all_nodes = {
    "EC": components["EC"],
    "EMC": components["EMC"],
    "DMC": components["DMC"],
    "LiPF6": components["LiPF6"],
    "MethylAcetate": components["MethylAcetate"],
    "LiPF6-Solution": lipf6_solution,
    "Battery-Electrolyte": battery_electrolyte
}

# Calculate properties
results = cc.get_mole_fractions_recursive(all_nodes, include_entities=True)

print("Battery electrolyte composition:")
print("(80wt% of 1.2 mol/kg LiPF6 in EC/EMC/DMC 25:5:70 w/w/w + 20wt% methyl acetate)")
for mixture in results:
    if mixture["name"] == "Battery-Electrolyte":
        print("\nComponent mole fractions:")
        for comp, xval in mixture["mole_fractions"].items():
            print(f"  {comp:20s}: {xval:.4f}")
        print("\nEntity mole fractions:")
        for entity, xval in mixture["entity_mole_fractions"].items():
            print(f"  {entity:20s}: {xval:.4f}")
        
        # Compare with expected values from paper (Table 7/8)
        print("\n  Expected values from paper (Table 7):")
        print("  DMC                 : 0.445")
        print("  EC                  : 0.162")
        print("  EMC                 : 0.027")
        print("  methyl acetate      : 0.228")
        print("  Li+                 : 0.069")
        print("  PF6-                : 0.069")


print()
print("="*70)
print("Section 4.2.2: Simulation of a microemulsion")
print("="*70)
print()

# Microemulsion: 1:1 w/w system of water (with 1 mol/L NaCl) and octane,
# with 3wt% of surfactant mixture (80mol% C10E4 + 20mol% DTAB)

# Define components
components_micro = {
    "Water": {
        "name": "Water",
        "mw": 18.02,
        "vm": 18.0,
    },
    "Octane": {
        "name": "Octane",
        "mw": 114.23,
    },
    "NaCl": {
        "name": "NaCl",
        "mw": 58.44,
        "vm": 27.0,
        "properties": {
            "entities": [
                {"name": "Na+", "stoichiometry": 1.0},
                {"name": "Cl-", "stoichiometry": 1.0}
            ]
        }
    },
    "C10E4": {
        "name": "C10E4",
        "mw": 334.5,
    },
    "DTAB": {
        "name": "DTAB",
        "mw": 308.35,
        "properties": {
            "entities": [
                {"name": "Dodecyltrimethylammonium", "stoichiometry": 1.0},
                {"name": "Br-", "stoichiometry": 1.0}
            ]
        }
    }
}

# Create the saline water (1 mol/L NaCl)
saline_water = {
    "name": "Saline-Water",
    "parents": [
        {"name": "Water", "amount": 1, "amount_type": "V", "unit": "L"},
        {"name": "NaCl", "amount": 1, "amount_type": "c", "unit": "mol/L"}
    ]
}

# Create the surfactant mixture (80mol% C10E4 + 20mol% DTAB)
surfactant_mix = {
    "name": "Surfactant-Mix",
    "parents": [
        {"name": "C10E4", "amount": 80, "amount_type": "x", "unit": "%"},
        {"name": "DTAB", "amount": 20, "amount_type": "x", "unit": "%"}
    ]
}

# Create the water-octane base (1:1 w/w)
water_octane = {
    "name": "Water-Octane-Base",
    "parents": [
        {"name": "Saline-Water", "amount": 50, "amount_type": "w", "unit": "%"},
        {"name": "Octane", "amount": 50, "amount_type": "w", "unit": "%"}
    ]
}

# Final microemulsion (97wt% water-octane + 3wt% surfactant mixture)
microemulsion = {
    "name": "Microemulsion",
    "parents": [
        {"name": "Water-Octane-Base", "amount": 97, "amount_type": "w", "unit": "%"},
        {"name": "Surfactant-Mix", "amount": 3, "amount_type": "w", "unit": "%"}
    ]
}

# Create dictionary of all nodes
all_nodes_micro = {
    "Water": components_micro["Water"],
    "Octane": components_micro["Octane"],
    "NaCl": components_micro["NaCl"],
    "C10E4": components_micro["C10E4"],
    "DTAB": components_micro["DTAB"],
    "Saline-Water": saline_water,
    "Surfactant-Mix": surfactant_mix,
    "Water-Octane-Base": water_octane,
    "Microemulsion": microemulsion
}

# Calculate properties
results_micro = cc.get_mole_fractions_recursive(all_nodes_micro, include_entities=True)

print("Microemulsion composition:")
print("(1:1 w/w water with 1 mol/L NaCl and octane + 3wt% surfactant)")
for mixture in results_micro:
    if mixture["name"] == "Microemulsion":
        print("\nComponent mole fractions:")
        for comp, xval in mixture["mole_fractions"].items():
            print(f"  {comp:20s}: {xval:.6f}")
        print("\nEntity mole fractions:")
        for entity, xval in mixture["entity_mole_fractions"].items():
            print(f"  {entity:20s}: {xval:.6f}")
        
        # Compare with expected values from paper (Table 8)
        print("\n  Expected values from paper (Table 8):")
        print("  Water                    : 0.827")
        print("  Octane                   : 0.138")
        print("  Sodium cation            : 1.53E-02")
        print("  Chloride                 : 1.53E-02")
        print("  C10E4                    : 2.38E-03")
        print("  Bromide                  : 5.94E-04")
        print("  Dodecyltrimethylammonium : 5.94E-04")

print()
print("="*70)
print("Section 4.2.3: Preparation of a chemical reaction")
print("="*70)
print()