#!/usr/bin/env python3
"""
Example script demonstrating how to use the library
"""

''' Example 1: mole fractions, and conversion, of a water/ethanol solution with salt '''

# Import the library
import ChemCalc_lib as cc

# Define the mixture components
names             = ["Water", "Ethanol", "NaCl"        ]
amounts           = [70.0   , 30.0     , 1.0           ]
amount_types      = ["φ"    , "φ"      , "c"           ]
units             = ["%"    , "%"      ,"mol/L"        ]
molar_weights     = [18.02  , 46.07    , 58.44         ]
molar_volumes     = [18.0   , 58.5     , 27.0          ]
entities          = [[]     , []       , ["Na+", "Cl-"]]             
stoichiometries   = [[]     , []       , [1.0  , 1.0  ]]      

# Prepare conversion to natural amounts for a 1L solution
target_types      = ["V"    , "V"      , "m"           ] #water and ethanol are naturally measured in volume, NaCl is naturally measured in mass
total_amount_type = "V"             #we want a volume
total_amount      = 1               #we want a 1L solution

# Prepare for calculation
component_data = cc.create_mixture(
    names, amounts, amount_types, units, Mw = molar_weights, 
    Vm = molar_volumes, entities = entities, stoichiometries = stoichiometries
)

# Get mole fractions
result = cc.get_mole_fractions(component_data, include_entities=True)
print("Example 1: 1 mol/L NaCl in a water/ethanol mixture 7:3 v/v")
print("__________________________________________________________")
print(
    "Mole fractions       :",
    {k: round(v, 3) for k, v in result["mole_fractions"].items()}
)
print(
    "Entity mole fractions:",
    {k: round(v, 3) for k, v in result["entity_mole_fractions"].items()}
)

# Get natural amounts
conversion = cc.convert(component_data, target_types, total_amount, total_amount_type)
print("Amounts to prepare a 1L solution:")
for comp_name, data in conversion["converted_amounts"].items():
    if data["amount_type"] == "V":
        print(comp_name, round(data["amount"], 2), "L")
    elif data["amount_type"] == "m":
        print(comp_name, round(data["amount"], 2), "g")

# Populate a unit cell            
cell = {'a' : 15, 'b' : 15, 'c' : 15, 'alpha' : 90, 'beta' : 90, 'gamma' : 90}
result_cell = cc.populate_unit_cell(
    result["mole_fractions"],
    {"Water" : 18.0, "Ethanol" : 58.5, "NaCl" : 27.0},
    {"Water" : [("Water", 1)], "Ethanol" : [("Ethanol", 1)], "NaCl": [("Na+", 1), ("Cl-", 1)]},
    cell
)

# Format cell volume and total moles to 3 significant figures (scientific notation)
cell_volume = result_cell.get("cell_volume_L")
total_moles_cell = result_cell.get("total_moles")

result_cell_print = dict(result_cell)
if cell_volume is not None:
    result_cell_print["cell_volume_L"] = float(f"{cell_volume:.3e}")
if total_moles_cell is not None:
    result_cell_print["total_moles"] = float(f"{total_moles_cell:.3e}")

print("In a cubic unit cell (edge length 15 Å):\n", result_cell_print)
print("__________________________________________________________")

''' Example 2: molality of a solute '''

# Note: molality is defined for a single solute in a solvent. If several molalities are given, then the calculation will run for each solute separately to the exclusion of other solutes with molalities.

# Define the mixture components
names             = ["Water", "Ethanol", "NaCl"        , "Urea"  , "Hydroxybenzoic acid"]
amounts           = [70.0   , 30.0     , 1.0           , 0.5     , 0.8                  ]
amount_types      = ["φ"    , "φ"      , "c"           , "b"     , "b"                  ]
units             = ["%"    , "%"      ,"mol/L"        , "mol/kg", "mol/kg"             ]
molar_weights     = [18.02  , 46.07    , 58.44         , 60.06   , 138.12               ]
molar_volumes     = [18.0   , 58.5     , 27.0          , 45.5    , 94.60                ]
entities          = [[]     , []       , ["Na+", "Cl-"], []      , []                   ]             
stoichiometries   = [[]     , []       , [1.0  , 1.0  ], []      , []                   ]      

# Prepare conversion to natural amounts for a 1L solution
target_types      = ["V"    , "V"      , "m"           , "m"     , "m"                  ] #water and ethanol are naturally measured in volume, NaCl and the two solutes are naturally measured in mass
total_amount_type = "V"             #we want a volume
total_amount      = 1               #we want a 1L solution


# Prepare for calculation
component_data = cc.create_mixture(
    names, amounts, amount_types, units, Mw = molar_weights, 
    Vm = molar_volumes, entities = entities, stoichiometries = stoichiometries
)

# Get mole fractions
result = cc.get_mole_fractions(component_data, include_entities=True)
print("Example 2: molalities of 0.5mol/kg of urea and 0.8mol/kg of hydroxybenzoic acid in a solvent composed of 1 mol/L NaCl in a water/ethanol mixture 7:3 v/v")
print("__________________________________________________________")

# result is a list if there are multiple 'b' solutes
if isinstance(result, list):
    for r in result:
        print(
            "Mole fractions       :",
            {k: round(v, 3) for k, v in r["mole_fractions"].items()}
        )
        print(
            "Entity mole fractions:",
            {k: round(v, 3) for k, v in r["entity_mole_fractions"].items()}
        )
else:
    print(
        "Mole fractions       :",
        {k: round(v, 3) for k, v in result["mole_fractions"].items()}
    )
    print(
        "Entity mole fractions:",
        {k: round(v, 3) for k, v in result["entity_mole_fractions"].items()}
    )
    
# Get natural amounts
conversion = cc.convert(component_data, target_types, total_amount, total_amount_type)

print("Amounts to prepare a 1L solution:")
if isinstance(conversion, list):
    for conv in conversion:
        for comp_name, data in conv["converted_amounts"].items():
            if data["amount_type"] == "V":
                print(comp_name, round(data["amount"], 2), "L")
            elif data["amount_type"] == "m":
                print(comp_name, round(data["amount"], 2), "g")
else:
    for comp_name, data in conversion["converted_amounts"].items():
        if data["amount_type"] == "V":
            print(comp_name, round(data["amount"], 2), "L")
        elif data["amount_type"] == "m":
            print(comp_name, round(data["amount"], 2), "g")

print("__________________________________________________________")
