# ChemCalc

ChemCalc is a Python library to convert between different chemical amount types
and to compute mole fractions for complex mixtures, including mixtures of
mixtures.

## Features

- Convert between amount types (mass, volume, moles, concentrations, fractions, etc.)
- Calculate mole fractions from various mixture specifications
- Handle complex mixture compositions including entities (ions, fragments) and stoichiometry
- Support for mixtures of mixtures at any level of nesting (recursive mixture trees)
- Unit cell population calculations for molecular simulation
- Support for molality calculations with multiple solutes
- Utility algebra functions for building custom workflows

## Installation

```bash
pip install chemcalc_lib
```

## Quick Start

### Basic example: water/ethanol/NaCl solution

```python
import ChemCalc_lib as cc

# Define the mixture components
names             = ["Water", "Ethanol", "NaCl"        ]
amounts           = [70.0   , 30.0     , 1.0           ]
amount_types      = ["φ"    , "φ"      , "c"           ]  # volume fractions and molarity
units             = ["%"    , "%"      , "mol/L"       ]
molar_weights     = [18.02  , 46.07    , 58.44         ]  # g/mol
molar_volumes     = [18.0   , 58.5     , 27.0          ]  # mL/mol
entities          = [[]     , []       , ["Na+", "Cl-"]]
stoichiometries   = [[]     , []       , [1.0  , 1.0  ]]

# Prepare the mixture
component_data = cc.create_mixture(
    names, amounts, amount_types, units,
    Mw=molar_weights, Vm=molar_volumes,
    entities=entities, stoichiometries=stoichiometries,
)

# Mole fractions (rounded for readability)
result = cc.get_mole_fractions(component_data, include_entities=True)
print("Mole fractions       :",
      {k: round(v, 3) for k, v in result["mole_fractions"].items()})
print("Entity mole fractions:",
      {k: round(v, 3) for k, v in result["entity_mole_fractions"].items()})

# Convert to practical amounts for preparing 1 L of solution
target_types      = ["V", "V", "m"]   # solvents in volume, salt in mass
total_amount      = 1.0               # 1 L total
total_amount_type = "V"

conversion = cc.convert(component_data, target_types, total_amount, total_amount_type)

print("To prepare 1 L solution:")
for comp_name, data in conversion["converted_amounts"].items():
    if data["amount_type"] == "V":
        print(comp_name, round(data["amount"], 2), "L")
    elif data["amount_type"] == "m":
        print(comp_name, round(data["amount"], 2), "g")
```

### Advanced examples

The `examples/` folder contains several fully worked scripts:

- `basic_examples.py`  
  - Example 1: 1 mol/L NaCl in water/ethanol 7:3 v/v  
  - Example 2: multiple solutes with molalities in a mixed solvent  
  - Includes a unit-cell population example.

- `recursive_example.py`  
  - Toy example of recursive mixtures built from basic components (water, ethanol, glycerol, several salts).  
  - Demonstrates how to define a mixture tree manually and obtain mole fractions and practical preparation amounts for terminal mixtures.

- `paper_examples.py`  
  - Reproduces the two first application examples from Section 4.2 of the manuscript (“Arithmetic of Mixing”):
    - 4.2.1 Battery electrolyte formulation
    - 4.2.2 Microemulsion with surfactant mixture

You can run any of these from the repository root with:

```bash
python examples/basic_examples.py
python examples/recursive_example.py
python examples/paper_examples.py
```

(adjust paths as needed depending on where you place the files.)

## Supported amount types

| Symbol | Type               | Standard unit |
|--------|--------------------|---------------|
| `m`    | Mass               | g             |
| `V`    | Volume             | L             |
| `n`    | Moles              | mol           |
| `w`    | Weight fraction    | – (0–1)       |
| `φ`    | Volume fraction    | – (0–1)       |
| `x`    | Mole fraction      | – (0–1)       |
| `c`    | Molarity           | mol/L         |
| `b`    | Molality           | mol/kg        |
| `ρ`    | Mass concentration | g/L           |
| `v`    | Specific volume    | L/g           |

## Unit handling

The library automatically handles common unit conversions:

- Mass: kg, g, mg, μg  
- Volume: m³, L, mL, μL, cc, cm³  
- Amount: mol, mmol, μmol  
- Concentrations: M, mM, μM, mol/L, etc.  
- Fractions: decimal (0–1) or percentage (%)

## API overview

### Main functions

- `create_mixture()` – build the internal data structure for a mixture.  
- `get_mole_fractions()` – calculate mole fractions (and optionally entity mole fractions).  
- `convert()` – convert a mixture to a set of target amount types for a specified total amount.  
- `get_mole_fractions_recursive()` – handle mixtures of mixtures defined as a mixture tree.  
- `populate_unit_cell()` – calculate the population of entities in a crystallographic unit cell.

### Utilities

- `create_amount_matrix()` – convert mixture specifications into matrix form.  
- `entities_mole_fraction_algebra()` – perform the algebra for entity mole fractions.  
- `amount_conversion_algebra()` – core conversion engine between amount types.

For full details, see the docstrings in the source code and the example scripts.

## Requirements

- Python ≥ 3.8  
- NumPy ≥ 1.19.0  

## License

MIT License

## Contributing

Contributions are welcome. Please open issues or pull requests on the GitHub
repository:

https://github.com/TheophileGaudin/chemcalc-lib

## Citation

If you use ChemCalc in your research, please cite:

```text
Théophile Gaudin, Arithmetic of Mixing, in preparation.
GitHub: https://github.com/TheophileGaudin/chemcalc-lib, doi: 10.5281/zenodo.17525109 

```
