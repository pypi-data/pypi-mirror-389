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
#   │   ├─ EC/EMC/DMC (25:5:70 w/w/w)
#   │   │   ├─ EC
#   │   │   ├─ EMC
#   │   │   └─ DMC
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
        print("  Water               : 0.827")
        print("  Octane              : 0.138")
        print("  Sodium cation       : 1.53E-02")
        print("  Chloride            : 1.53E-02")
        print("  C10E4               : 2.38E-03")
        print("  Bromide             : 5.94E-04")
        print("  Dodecyltrimethyl... : 5.94E-04")

print()
print("="*70)
print("Section 4.2.3: Preparation of a chemical reaction")
print("="*70)
print()

# Reaction mixture: Starting from 20g of L-leucine, prepare a reaction with:
# - 3.5 equivalents of NaBr
# - 1.3 mL/mmol of a 2.5M solution of H2SO4
# - 1.25 equivalents of NaNO2

# Define reaction components
names_rxn = ["L-Leucine", "NaBr", "H2SO4", "NaNO2"]
molar_weights_rxn = [131.17, 102.894, 98.08, 68.9953]  # g/mol
molar_volumes_rxn = [110.0, 40.0, 53.0, 37.0]  # mL/mol (approximate)

# Starting amount: 20g of L-leucine
mass_leucine = 20.0  # g
moles_leucine = mass_leucine / molar_weights_rxn[0]

print(f"Starting with {mass_leucine} g of L-leucine")
print(f"This corresponds to {moles_leucine:.4f} mol of L-leucine")
print()

# Calculate required amounts based on equivalents and ratios

# NaBr: 3.5 equivalents
equiv_nabr = 3.5
mass_nabr = moles_leucine * equiv_nabr * molar_weights_rxn[1]
print(f"NaBr required: {equiv_nabr} equivalents = {mass_nabr:.2f} g")

# H2SO4: 1.3 mL/mmol of 2.5M solution
ml_per_mmol = 1.3  # mL/mmol
molarity_h2so4 = 2.5  # mol/L
volume_h2so4 = moles_leucine * 1000 * ml_per_mmol / 1000  # Convert to L
mass_h2so4 = volume_h2so4 * molarity_h2so4 * molar_weights_rxn[2]
print(f"H2SO4 solution required: {ml_per_mmol} mL/mmol = {volume_h2so4*1000:.2f} mL of {molarity_h2so4}M solution")
print(f"  (corresponding to {mass_h2so4:.2f} g of pure H2SO4)")

# NaNO2: 1.25 equivalents
equiv_nano2 = 1.25
mass_nano2 = moles_leucine * equiv_nano2 * molar_weights_rxn[3]
print(f"NaNO2 required: {equiv_nano2} equivalents = {mass_nano2:.2f} g")
print()

# Create the complete reaction mixture for mole fraction calculation
# We'll model this as absolute amounts

# For the H2SO4 solution, we need to account for water
# A 2.5M H2SO4 solution contains approximately 220 g H2SO4 per liter
# Density ~ 1.18 g/mL, so 1L weighs ~1180g, meaning ~960g water per liter
density_h2so4_solution = 1180  # g/L for 2.5M H2SO4
mass_h2so4_per_liter = 245  # g/L for 2.5M solution
mass_water_per_liter = density_h2so4_solution - mass_h2so4_per_liter

mass_water_in_solution = (mass_water_per_liter / 1000) * volume_h2so4 * 1000

names_complete = ["L-Leucine", "NaBr", "H2SO4", "Water", "NaNO2"]
amounts_complete = [mass_leucine, mass_nabr, mass_h2so4, mass_water_in_solution, mass_nano2]
amount_types_complete = ["m", "m", "m", "m", "m"]
units_complete = ["g", "g", "g", "g", "g"]
molar_weights_complete = [131.17, 102.894, 98.08, 18.015, 68.9953]
molar_volumes_complete = [110.0, 40.0, 53.0, 18.0, 37.0]
entities_complete = [[], [], [], [], []]
stoichiometries_complete = [[], [], [], [], []]

rxn_data = cc.create_mixture(
    names_complete, amounts_complete, amount_types_complete, units_complete,
    Mw=molar_weights_complete, Vm=molar_volumes_complete,
    entities=entities_complete, stoichiometries=stoichiometries_complete
)

# Get mole fractions
rxn_result = cc.get_mole_fractions(rxn_data, include_entities=False)

print("Reaction mixture composition:")
print("Component mole fractions:")
for comp, xval in rxn_result["mole_fractions"].items():
    print(f"  {comp:15s}: {xval:.6f}")

print()
print("="*70)
print("Summary")
print("="*70)
print()
print("These examples demonstrate ChemCalc's capability to handle:")
print("1. Complex nested mixtures (battery electrolytes)")
print("2. Multi-component formulations with ionic species (microemulsions)")
print("3. Stoichiometric calculations for chemical reactions")
print()
print("The mixture tree approach simplifies calculations that would be")
print("tedious and error-prone when performed by hand.")
print()
