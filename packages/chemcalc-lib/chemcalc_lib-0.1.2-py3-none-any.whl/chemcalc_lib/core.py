import json
import itertools, math
import numpy as np
from copy         import deepcopy
from numpy        import array, zeros, asarray, isnan, isinf, zeros_like, dot
from numpy        import any as np_any, all as np_all
from numpy.linalg import solve, matrix_rank, LinAlgError

#dictionary to retrieve standard unit for amount type
amount_type_to_std_unit = {
"m": "g",
"V": "L",
"n": "mol",
"w": "-",
"φ": "-",
"x": "-",
"c": "mol/L",
"b*": "mol/g",
"ρ": "g/L",
"v": "L/g",
"b": "mol/g"
}

'''basic utilities'''

def create_mixture(names,
    amounts,
    amount_types,
    units,
    Mw=None,
    Vm=None,
    entities=None,
    stoichiometries=None):
    """
    Create component data for mixture calculations, allowing Mw or Vm to be optional.
    """
    num_components = len(names)
    if Mw is None: Mw = [None] * num_components
    if Vm is None: Vm = [None] * num_components
    if entities is None: entities = [[]] * num_components
    if stoichiometries is None: stoichiometries = [[]] * num_components

    if not all(len(lst) == num_components for lst in [amounts, amount_types, units, Mw, Vm, entities, stoichiometries]):
        raise ValueError("All input lists must have the same length")

    component_data = []
    for i in range(num_components):
        component = {
            'name': names[i],
            'amount': amounts[i],
            'amount_type': amount_types[i],
            'unit': units[i],
        }
        if Mw[i] is not None:
            component['mw'] = Mw[i]
        if Vm[i] is not None:
            component['vm'] = Vm[i]
        if entities[i]:
            if len(entities[i]) != len(stoichiometries[i]):
                raise ValueError(f"Entities and stoichiometries lists for {names[i]} must match")
            component['entities'] = [
                {'name': e, 'stoichiometry': s} for e, s in zip(entities[i], stoichiometries[i])
            ]
        component_data.append(component)
    return component_data
def create_amount_matrix(components_data):
    """
    Create amount matrix, tolerating missing Mw or Vm (replaced with 1.0 only if needed).
    """
    n = len(components_data)
    matrix = np.zeros((n, 10))
    names, Mw, Vm = [], np.zeros(n), np.zeros(n)

    for i, comp in enumerate(components_data):
        names.append(comp['name'])
        Mw[i] = comp.get('mw', 1.0) if comp.get('mw') not in [None, 0] else 1.0
        Vm[i] = convert_molar_volume(comp.get('vm', 1.0), comp.get('vm_unit', 'mL/mol')) \
            if comp.get('vm') not in [None, 0] else 1.0

        amt = convert_to_standard_unit(comp['amount'], comp['amount_type'], comp['unit'])
        idx = get_column_index(comp['amount_type'])
        matrix[i, idx] = amt
    return matrix, names, Mw, Vm
def convert_to_standard_unit(amount, amount_type, unit):
    """
    Convert an amount to the standard unit used in the matrix.
    
    Standard units:
    - Mass (m): g
    - Volume (V): L
    - Moles (n): mol
    - Weight fraction (w): unitless (0-1)
    - Volume fraction (φ): unitless (0-1)
    - Mole fraction (x): unitless (0-1)
    - Molarity (c): mol/L
    - Molality (b): mol/kg (converted to mol/g)
    - Mass concentration (ρ): g/L
    - Specific volume (v): L/g
    
    Parameters:
        amount (float): Amount value
        amount_type (str): Type of amount
        unit (str): Unit of measurement
        
    Returns:
        float: Converted amount in standard unit
    """
    # Mass conversions
    if amount_type == 'm':
        if unit == 'kg':
            return amount * 1000
        elif unit == 'mg':
            return amount / 1000
        elif unit == 'μg' or unit == 'ug':
            return amount / 1000000
        # g is standard
        return amount
    
    # Volume conversions
    elif amount_type == 'V':
        if unit == 'mL':
            return amount / 1000
        elif unit == 'μL' or unit == 'uL':
            return amount / 1000000
        elif unit == 'cm³' or unit == 'cc':
            return amount / 1000
        elif unit == 'm³':
            return amount * 1000
        # L is standard
        return amount
    
    # Mole conversions
    elif amount_type == 'n':
        if unit == 'mmol':
            return amount / 1000
        elif unit == 'μmol' or unit == 'umol':
            return amount / 1000000
        # mol is standard
        return amount
    
    # Fraction conversions (unitless)
    elif amount_type in ['w', 'φ', 'x']:
        if unit == '%':
            return amount / 100
        # Unitless is standard
        return amount
    
    # Molarity conversions
    elif amount_type == 'c':
        if unit == 'mmol/L' or unit == 'mM':
            return amount / 1000
        elif unit == 'μmol/L' or unit == 'μM' or unit == 'umol/L' or unit == 'uM':
            return amount / 1000000
        # mol/L is standard
        return amount
    
    # Molality conversions
    elif amount_type == 'b':
        if unit == 'mol/kg':
            return amount / 1000  # Convert to mol/g for calculations
        elif unit == 'mmol/kg':
            return amount / 1000000
        # mol/g is standard internally
        return amount
    
    # Mass concentration conversions
    elif amount_type == 'ρ' or amount_type == 'rho':
        if unit == 'mg/L':
            return amount / 1000
        elif unit == 'g/mL':
            return amount * 1000
        elif unit == 'mg/mL':
            return amount
        # g/L is standard
        return amount
    
    # Specific volume conversions
    elif amount_type == 'v':
        if unit == 'mL/g':
            return amount / 1000
        # L/g is standard
        return amount
    
    # Return original if no conversion needed
    return amount
def get_column_index(amount_type):
    """
    Map amount type to the corresponding column index in the matrix.
    
    Parameters:
        amount_type (str): Type of amount
        
    Returns:
        int: Column index
    """
    # Matrix columns: m, V, n, w, φ, x, c, b, ρ, v
    amount_type_mapping = {
        'm': 0,   # mass
        'V': 1,   # volume
        'n': 2,   # moles
        'w': 3,   # weight fraction
        'φ': 4,   # volume fraction (phi)
        'phi': 4, # alternative for phi
        'x': 5,   # mole fraction
        'c': 6,   # molarity
        'b': 7,   # molality (internally b*)
        'ρ': 8,   # mass concentration (rho)
        'rho': 8, # alternative for rho
        'v': 9    # specific volume (internally v*)
    }
    
    return amount_type_mapping.get(amount_type, 0)
def get_mole_fractions(components_data, include_entities=False):
    """
    Calculate mole fractions from component data.
    
    Behaviour:
    - If no component has amount_type 'b' (molality), return a single result dict.
    - If exactly one component has amount_type 'b', return a single result dict for
      that solute.
    - If more than one component has amount_type 'b', return a list of result dicts,
      one per solute, each mixed with the same solvent.
      
    The function is permissive w.r.t. mw / vm:
    - If 'mw' or 'vm' is missing or None, it is auto-filled with 1.0.
      (This only matters numerically if that property is actually used
       in the algebra for the given amount types.)
    """
    from copy import deepcopy
    import numpy as np

    # Work on a copy so we don't mutate the caller's data
    components_data = deepcopy(components_data)

    # Auto-fill missing mw and vm with dummy values
    for component in components_data:
        if component.get("mw") is None:
            component["mw"] = 1.0
        if component.get("vm") is None:
            component["vm"] = 1.0

    # --- Triaging molality ("b") solutes vs "normal" components ---

    molality_n          = 0
    pristine_components = deepcopy(components_data)
    molality_solute_idx = []
    molality_solute_name = []
    molality_solute_Mw   = []
    molality_solute_b    = []

    for i, comp in enumerate(pristine_components):
        if comp["amount_type"] == "b":
            molality_solute_name.append(comp["name"])
            molality_solute_Mw.append(comp["mw"])
            molality_solute_b.append(comp["amount"])
            molality_solute_idx.append(i)

            # Remove solute from the "pristine" solvent mixture
            comp["amount"]      = 0.0
            comp["amount_type"] = "x"
            comp["unit"]        = "-"
            molality_n += 1

    # --- Case 1: no traditional molality 'b' present -> single mixture ---

    if molality_n == 0:
        # Build amount matrix (Table 1) and property arrays
        matrix, names, Mw, Vm = create_amount_matrix(components_data)

        # Solve for mole fractions and mixture properties
        x, Mw_avg, Vm_avg, n_tot, no_abs = mole_fraction_algebra(matrix, Mw, Vm)

        # Put components back in mole-fraction form
        results_components = deepcopy(components_data)
        for i, comp in enumerate(results_components):
            comp["amount"]      = x[i]
            comp["amount_type"] = "x"
            comp["unit"]        = "-"

        # Base result dict
        results = {
            "mole_fractions": {names[i]: x[i] for i in range(len(names))},
            "average_molar_weight": Mw_avg,
            "average_molar_volume_L_mol": Vm_avg,
            "average_molar_volume_mL_mol": Vm_avg * 1000.0,
            "total_moles": n_tot if not no_abs else None,
            "component list": results_components,
        }

        # Optional entity mole fractions
        if include_entities:
            entities_info = extract_entities_information(components_data)
            entity_x = entities_mole_fraction_algebra(
                entities_info, results["mole_fractions"]
            )
            results["entity_mole_fractions"] = entity_x

        return results

    # --- Case 2: at least one 'b' solute -> one mixture per solute ---

    # First compute solvent composition (without any 'b' solutes)
    matrix, names, Mw, Vm = create_amount_matrix(pristine_components)
    x_solvent, Mw_avg, Vm_avg, n_tot, no_abs = mole_fraction_algebra(matrix, Mw, Vm)

    results_list = []

    for k in range(molality_n):
        # Compute mole fractions including this solute with given molality
        x = calculate_mole_fractions_with_molality(
            x_solvent,
            names,
            Mw_avg,
            molality_solute_b[k],
            molality_solute_Mw[k],
            molality_solute_name[k],
        )

        # Store component data in mole-fraction form
        results_components = deepcopy(components_data)
        for i, comp in enumerate(results_components):
            comp["amount"]      = x[i]
            comp["amount_type"] = "x"
            comp["unit"]        = "-"

        # For each solute, recompute averages for that specific mixture
        Mw_mix = np.dot(x, Mw)
        Vm_mix = np.dot(x, Vm)

        res = {
            "mole_fractions": {
                names[i]: x[i] for i in range(len(names)) if x[i] > 0.0
            },
            "average_molar_weight": Mw_mix,
            "average_molar_volume_L_mol": Vm_mix,
            "average_molar_volume_mL_mol": Vm_mix * 1000.0,
            "total_moles": n_tot if not no_abs else None,
            "component list": results_components,
        }

        if include_entities:
            entities_info = extract_entities_information(components_data)
            entity_x = entities_mole_fraction_algebra(
                entities_info, res["mole_fractions"]
            )
            res["entity_mole_fractions"] = entity_x

        results_list.append(res)

    # Single solute -> single dict; multiple solutes -> list of dicts
    if molality_n == 1:
        return results_list[0]
    else:
        return results_list
def solve_partitioned_system(A, b, knowns):
    """
    Solves a system of linear equations A x = b, taking into account that
    some variables are either known as numeric values or defined to be equal 
    to another variable (e.g., "=i" means that variable is equal to x_i).
    
    Parameters:
        A (numpy.ndarray): Coefficient matrix of shape (m, n).
        b (numpy.ndarray): Right-hand side vector of shape (m,).
        knowns (array-like): 2D array (or list of lists) where each row is 
                             [variable_index, value]. The value can be a 
                             number or a string like "=i" indicating that the 
                             variable equals variable i.
                             
    Returns:
        numpy.ndarray: Full solution vector x of length n, with the known 
                       variables inserted and the remaining unknowns computed.
                       
    Raises:
        ValueError: If no suitable set of independent equations is found for a 
                    unique solution.
    """
    m, n = A.shape

    # Step 1. Process the "knowns": separate numeric knowns and dependency mappings.
    known_numeric = {}    # Mapping: variable index -> numeric value.
    dependencies = {}     # Mapping: variable index -> representative index.
    for entry in knowns:
        var = int(entry[0])
        val = entry[1]
        if isinstance(val, str) and val.startswith("="):
            # The variable is defined to be equal to another variable.
            rep = int(val[1:])
            dependencies[var] = rep
        else:
            # The variable is directly known.
            known_numeric[var] = float(val)
    
    # Step 2. Resolve dependency chains.
    def find_rep(i):
        # Follow the dependency chain until a variable is not in dependencies.
        while i in dependencies:
            i = dependencies[i]
        return i
    
    for var in list(dependencies.keys()):
        rep = find_rep(dependencies[var])
        dependencies[var] = rep

    # Step 3. Modify the matrix A to account for dependencies.
    # We will merge columns: if x[j] = x[i] then add A[:, j] to A[:, i] and mark j for removal.
    remove_cols = set()
    for var, rep in dependencies.items():
        if rep in known_numeric:
            # If the representative is known numerically, then var becomes known as well.
            known_numeric[var] = known_numeric[rep]
            remove_cols.add(var)
        else:
            if var != rep:
                A[:, rep] = A[:, rep] + A[:, var]
                remove_cols.add(var)
    
    # Also, any variable that is directly known (numeric) will be removed from the unknown set.
    for var in known_numeric.keys():
        remove_cols.add(var)
    
    # Determine indices of variables that remain unknown (i.e. independent).
    unknown_indices = [i for i in range(n) if i not in remove_cols]
    
    # Step 4. Adjust the right-hand side b by subtracting the contributions of known variables.
    b_prime = b.copy()
    for var, value in known_numeric.items():
        b_prime = b_prime - A[:, var] * value

    # The reduced system is A_u * x_u = b_prime, where A_u consists of the columns for unknown indices.
    A_u = A[:, unknown_indices]
    n_unknown = len(unknown_indices)
    
    

    # Step 5. Since the reduced system may be overdetermined, look for a subset of rows
    # (of size n_unknown) that forms an invertible square system.
    for rows in itertools.combinations(range(m), n_unknown):
        sub_A_u = A_u[list(rows), :]
        if matrix_rank(sub_A_u) == n_unknown:
            sub_b_prime = b_prime[list(rows)]
            try:
                x_unknown = solve(sub_A_u, sub_b_prime)
            except LinAlgError:
                continue  # If singular, try another combination.
            # Build the full solution vector.
            # print("reduced matrix:")
            # for i in range(len(sub_A_u)):
                # print(sub_A_u[i])
            # print("reduced result vector")
            # print(sub_b_prime)
            
            x_full = zeros(n)
            for i, idx in enumerate(unknown_indices):
                x_full[idx] = x_unknown[i]
            for var, value in known_numeric.items():
                x_full[var] = value
                
            #reattribute known variables equal to previously unknown ones
            for i in range(len(knowns)):
                if isinstance(knowns[i][1],str):
                    index_to_get = int(knowns[i][1][1:])
                    
                    x_full[knowns[i][0]] = x_full[index_to_get]
                
            return x_full
    
    
    raise ValueError("No suitable set of independent equations found for a unique solution.")
def check_physically_valid(values):
    """
    Check if values are physically valid (not negative, not infinite, not NaN).
    
    Args:
        values: Can be a single number, list, or numpy array
        
    Returns:
        bool: True if all values are physically valid, False otherwise
    """
    # Handle single values
    if isinstance(values, (int, float)):
        return not (values < 0 or isnan(values) or isinf(values))
    
    # Handle lists or numpy arrays
    for val in asarray(values).flatten():
        if val < 0 or isnan(val) or isinf(val):
            return False
    
    return True
def collect_entities_information(data, is_recursive=False):
    """
    Collects information about all entities from component data.
    For recursive case, extracts entities only from leaf nodes.
    Handles duplicate entities from the same component.
    
    Args:
        data: Either the component list (non-recursive) or the mixture tree (recursive)
        is_recursive (bool): Flag indicating whether the data is in recursive format
        
    Returns:
        list: A list of lists where each inner list has format [Entity, Parent component, Stoichiometry]
    """
    # Dictionary to track unique entity-parent pairs
    # Key is a tuple (entity_name, parent_component_name)
    # Value is the index in entities_information list
    unique_pairs = {}
    entities_information = []
    
    if is_recursive:
        # Extract all leaf components from the mixture tree
        leaf_components = []
        
        def extract_leaf_nodes(node):
            """Recursively extract leaf nodes from the mixture tree"""
            if "parents" not in node or not node["parents"]:
                # This is a leaf node, add it to our list
                leaf_components.append(node)
            else:
                # This is an intermediate node, process its parents
                for parent in node["parents"]:
                    extract_leaf_nodes(parent)
        
        # Start extraction from the root node
        extract_leaf_nodes(data)
        
        # Process each leaf component
        for component in leaf_components:
            component_name = component["name"]
            
            # Check if component has entity information
            if "properties" in component and "entities" in component["properties"] and component["properties"]["entities"]:
                for entity in component["properties"]["entities"]:
                    if "name" in entity and "stoichiometry" in entity:
                        entity_name = entity["name"]
                        stoichiometry = entity["stoichiometry"]
                        
                        # Create a unique key for this entity-parent pair
                        key = (entity_name, component_name)
                        
                        # Check if we've already seen this pair
                        if key in unique_pairs:
                            # We've already added this entity from this parent
                            # Skip it to avoid duplicates
                            continue
                            
                        # Add new entity information
                        entities_information.append([entity_name, component_name, stoichiometry])
                        # Record the index
                        unique_pairs[key] = len(entities_information) - 1
            
            # If no entities defined, use the component itself
            elif component_name:
                # Create a unique key for this entity-parent pair (component as its own entity)
                key = (component_name, component_name)
                
                # Check if we've already seen this pair
                if key not in unique_pairs:
                    entities_information.append([component_name, component_name, 1.0])
                    unique_pairs[key] = len(entities_information) - 1
    else:
        # Non-recursive case: process the list of components
        for component in data:
            component_name = component["name"]
            
            # Check if component has entity information
            if "entities" in component and component["entities"]:
                for entity in component["entities"]:
                    if "name" in entity and "stoichiometry" in entity:
                        entity_name = entity["name"]
                        stoichiometry = entity["stoichiometry"]
                        
                        # Create a unique key for this entity-parent pair
                        key = (entity_name, component_name)
                        
                        # Check if we've already seen this pair
                        if key in unique_pairs:
                            # We've already added this entity from this parent
                            # Skip it to avoid duplicates
                            continue
                            
                        # Add new entity information
                        entities_information.append([entity_name, component_name, stoichiometry])
                        # Record the index
                        unique_pairs[key] = len(entities_information) - 1
            
            # If no entities defined, use the component itself
            elif component_name:
                # Create a unique key for this entity-parent pair (component as its own entity)
                key = (component_name, component_name)
                
                # Check if we've already seen this pair
                if key not in unique_pairs:
                    entities_information.append([component_name, component_name, 1.0])
                    unique_pairs[key] = len(entities_information) - 1
    
    return entities_information
def calculate_mole_fractions_with_molality(solvent_mole_fractions, solvent_names, solvent_mw_avg, solute_molality, solute_mw, solute_name):
    """
    Calculate mole fractions for all components including a solute with known molality.
    
    Args:
        solvent_mole_fractions (dict): Dictionary of mole fractions for solvent components only
        solvent_mw_avg (float): Average molar weight of the solvent components (g/mol)
        solute_molality (float): Molality of the solute (mol/kg, will be converted to mol/g)
        solute_name (str): Name of the solute component
        
    Returns:
        dict: Updated dictionary with mole fractions for all components including the solute
    """
    # Convert molality from mol/kg to mol/g if needed
    b_solute = solute_molality / 1000  # Convert to mol/g
    M_solvent = solvent_mw_avg  # Average molar mass of solvent (g/mol)
    
    # Calculate solute mole fraction using the formula:
    # x_solute = (b_solute * M_solvent) / (b_solute * M_solvent + 1)
    x_solute = (b_solute * M_solvent) / (b_solute * M_solvent + 1)
    
    # Calculate solvent scale factor:
    # Solvent components need to be scaled by (1 - x_solute) / sum(solvent_mole_fractions)
    # This is mathematically equivalent to: 1 / (b_solute * M_solvent + 1)
    scaling_factor = 1 / (b_solute * M_solvent + 1)
    
    
    # Build mole fractions vector
    complete_mole_fractions = deepcopy(solvent_mole_fractions)    
    for i in range(len(solvent_names)):
        if solvent_names[i] == solute_name:
            complete_mole_fractions[i] = x_solute
        else:
            scaled_fraction = solvent_mole_fractions[i] * scaling_factor
            complete_mole_fractions[i] = scaled_fraction
    return complete_mole_fractions
def convert_molar_volume(value, unit):
    """
    Convert molar volume to L/mol (standard unit for calculations).
    
    Parameters:
        value (float): Molar volume value
        unit (str): Current unit of molar volume
        
    Returns:
        float: Molar volume in L/mol
    """
    if unit == 'mL/mol':
        return value / 1000  # Convert mL/mol to L/mol
    elif unit == 'cm³/mol' or unit == 'cc/mol':
        return value / 1000  # Convert cm³/mol to L/mol
    elif unit == 'dm³/mol':
        return value / 1     # Convert dm³/mol to L/mol (they are the same)
    elif unit == 'm³/mol':
        return value * 1000  # Convert m³/mol to L/mol
    
    # L/mol is already standard
    return value
def convert(components_data, target_types=None, total_amount=1.0, total_amount_type="n", include_entities=False):
    """
    Calculate mole fractions and convert to specific target amount types.
    
    Parameters:
        components_data (list): List of component dictionaries
        target_types (list, optional): List of target amount types for each component
                                     If None, uses their original amount types
        total_amount (float): The total amount of the mixture (in standardized units)
        total_amount_type (str): The type of total amount ('n', 'm', or 'V')
        include_entities (bool): Whether to calculate entity mole fractions
        
    Returns:
        dict: Results including mole fractions, converted amounts, and mixture properties
    """
    
    # Triage molality cases from normal cases
    molality_n = 0
    pristine_components_data = deepcopy(components_data)
    molality_solute_idx     = list()
    molality_solute_name    = list()
    molality_solute_Mw      = list()
    molality_solute_b       = list()
    
    for i, component in enumerate(pristine_components_data):
        if component["amount_type"] == "b": #remove the component from the pristine mixture
            molality_solute_name.append(component["name"])
            molality_solute_Mw.append(component["mw"])
            molality_solute_b.append(component["amount"])
            molality_solute_idx.append(i)
            component["amount"]      = 0
            component["amount_type"] = "x"
            component["unit"]        = "-"
            molality_n += 1
            
    
    # Normal case returns just one results object
    if molality_n == 0:
    
        # Create matrix and extract component properties
        matrix, names, Mw, Vm = create_amount_matrix(components_data)
        
        # Calculate mole fractions using the library function
        x, Mw_avg, Vm_avg, n_tot, no_abs = mole_fraction_algebra(matrix, Mw, Vm)
        
        
        # Store component data in mole fractions format
        results_components_data = deepcopy(components_data)
        for i, component in enumerate(results_components_data):
            component["amount"]      = x[i]
            component["amount_type"] = "x"
            component["unit"]        = "-"
            
        
        # Set default target types if not specified
        if target_types is None:
            target_types = [comp['amount_type'] for comp in components_data]
        
        # Convert mole fractions to target amount types
        result_matrix, Mw_back, Vm_back = amount_conversion_algebra(
            x, Mw, Vm, target_types, total_amount, total_amount_type
        )
        
        # Create results dictionary
        results = {
            'mole_fractions': {names[i]: x[i] for i in range(len(names))},
            'converted_amounts': {
                names[i]: {
                    'amount': result_matrix[i, 0],
                    'amount_type': target_types[i]
                } for i in range(len(names))
            },
            'average_molar_weight': Mw_avg,
            'average_molar_volume_L_mol': Vm_avg,
            'average_molar_volume_mL_mol': Vm_avg * 1000,  # Convert back to mL/mol for reporting
            'total_moles': n_tot if not no_abs else None
        }
        
        # If requested, calculate entity mole fractions
        if include_entities:
            # Extract entity information from components
            entities_information = extract_entities_information(components_data)
            
            # Calculate entity mole fractions
            entity_mole_fractions = entities_mole_fraction_algebra(
                entities_information, 
                results['mole_fractions']
            )
            
            # Add entity mole fractions to results
            results['entity_mole_fractions'] = entity_mole_fractions
        
        return results
    else: # Here we return one case per provided molality
        # First we compute the properties for the pristine mixture without molality solutes
        matrix, names, Mw, Vm              = create_amount_matrix(pristine_components_data)
        x_0, Mw_avg, Vm_avg, n_tot, no_abs = mole_fraction_algebra(matrix, Mw, Vm)
        
        results_list = list()
        for i in range(molality_n):
            # Include solute in calculation of mole fractions
            x                                = calculate_mole_fractions_with_molality(x_0, names, Mw_avg, molality_solute_b[i], molality_solute_Mw[i], molality_solute_name[i])
            
            # Store component data in mole fractions format
            results_components_data = deepcopy(components_data)
            for i, component in enumerate(results_components_data):
                component["amount"]      = x[i]
                component["amount_type"] = "x"
                component["unit"]        = "-"   
            
            
            # Set default target types if not specified
            if target_types is None:
                target_types = [comp['amount_type'] for comp in components_data]
            
            # Convert mole fractions to target amount types
            result_matrix, Mw_back, Vm_back = amount_conversion_algebra(
                x, Mw, Vm, target_types, total_amount, total_amount_type
            )
            
            # Create results dictionary
            results = {
                'mole_fractions':  {names[i]: x[i] for i in range(len(names)) if x[i] > 0},
                'converted_amounts': {
                    names[i]: {
                        'amount': result_matrix[i, 0],
                        'amount_type': target_types[i]
                    } for i in range(len(names)) if x[i] > 0
                },
                'average_molar_weight'       : np.dot(x, Mw),         # Recalculate average properties
                'average_molar_volume_L_mol' : np.dot(x, Vm),         # Recalculate average properties
                'average_molar_volume_mL_mol': np.dot(x, Vm) * 1000,  # Convert back to mL/mol for reporting
                'total_moles': n_tot if not no_abs else None
            }
            
            # If requested, calculate entity mole fractions
            if include_entities:
                # Extract entity information from components
                entities_information = extract_entities_information(components_data)
                
                # Calculate entity mole fractions
                entity_mole_fractions = entities_mole_fraction_algebra(
                    entities_information, 
                    results['mole_fractions']
                )
                
                # Add entity mole fractions to results
                results['entity_mole_fractions'] = entity_mole_fractions
            results_list.append(results)
                
        if molality_n == 1: #if a single solute no need to return a list of results
            return results
        else:
            return results_list
    
    
    
    return results
def extract_entities_information(components_data):
    """
    Extract entity information from component dictionaries.
    If no entities are defined for a component, the component itself
    is used as an entity with stoichiometry 1.0.
    
    Parameters:
        components_data (list): A list of component dictionaries
        
    Returns:
        list: A list of lists where each inner list has format [Entity, Parent component, Stoichiometry]
    """
    entities_information = []
    
    for component in components_data:
        component_name = component['name']
        
        # Check if component has entity information
        if 'entities' in component and component['entities']:
            for entity in component['entities']:
                if 'name' in entity and 'stoichiometry' in entity:
                    entity_name = entity['name']
                    stoichiometry = entity['stoichiometry']
                    entities_information.append([entity_name, component_name, stoichiometry])
        else:
            # If no entities defined, use the component itself as an entity with stoichiometry 1.0
            entities_information.append([component_name, component_name, 1.0])
    
    return entities_information

''' recursive utilities '''

def distribute_mixture_component(amount_type, standardized_amount, M_mo, V_mo, x_i, M_i, V_m_i):
    """
    Distribute a standardized amount of a component from a parent mixture to a daughter mixture
    based on physical equations for mixture composition.

    Args:
        amount_type (str): The type of amount ('m', 'V', 'n', 'w', 'φ', 'x', 'c', 'b', 'ρ', 'v')
        standardized_amount (float): The standardized amount value
        x_i (float): Mole fraction of component i in the parent mixture
        M_i (float): Molar weight of component i (g/mol)
        V_m_i (float): Molar volume of component i (L/mol)
        M_mo (float): Average molar weight of parent mixture (g/mol)
        V_mo (float): Average molar volume of parent mixture (L/mol)

    Returns:
        tuple: (distributed_amount, output_amount_type)
    """

    # Guard only for the quantities actually needed in each case

    # Types that do NOT use mixture Mw or Vm
    if amount_type in ['n', 'x', 'c', 'b']:
        # no extra checks; formulas only use x_i and the standardized amount
        pass

    # Types that need mixture M_mo only
    elif amount_type in ['m', 'w', 'ρ']:
        if abs(M_mo) < 1e-10:
            raise ValueError(
                f"Cannot distribute '{amount_type}' from parent: "
                f"mixture molar mass M_mo is zero or missing."
            )

    # Types that need mixture V_mo only
    elif amount_type in ['V', 'φ']:
        if abs(V_mo) < 1e-10:
            raise ValueError(
                f"Cannot distribute '{amount_type}' from parent: "
                f"mixture molar volume V_mo is zero or missing."
            )

    # Type that needs both M_mo and component V_m_i
    elif amount_type == 'v':
        if abs(M_mo) < 1e-10 or abs(V_m_i) < 1e-10:
            raise ValueError(
                "Cannot distribute 'v' from parent: M_mo or component V_m_i "
                "is zero or missing."
            )

    # Now implement equations C1–C14

    if amount_type == 'n':
        # C1: n_i^mo = x_mo^i * n_mo
        distributed_amount = standardized_amount * x_i
        return distributed_amount, 'n'

    elif amount_type == 'm':
        # C2: m_i^mo = x_mo^i * M_i * n_mo
        # n_mo = m_mo / M_mo
        n_mo = standardized_amount / M_mo
        distributed_amount = x_i * n_mo * M_i
        return distributed_amount, 'm'

    elif amount_type == 'V':
        # C3: V_i^mo = x_mo^i * V_m,i * n_mo
        # n_mo = V_mo / V_m,mo
        n_mo = standardized_amount / V_mo
        distributed_amount = x_i * n_mo * V_m_i
        return distributed_amount, 'V'

    elif amount_type == 'x':
        # C4: x_i^mo = x_mo * x_mo^i
        distributed_amount = standardized_amount * x_i
        return distributed_amount, 'x'

    elif amount_type == 'w':
        # C5: w_i^mo = (w_mo * M_i / M_mo) * x_mo^i
        distributed_amount = standardized_amount * (M_i / M_mo) * x_i
        return distributed_amount, 'w'

    elif amount_type == 'φ':
        # C6: φ_i^mo = (φ_mo * V_m,i / V_mo) * x_mo^i
        distributed_amount = standardized_amount * (V_m_i / V_mo) * x_i
        return distributed_amount, 'φ'

    elif amount_type == 'c':
        # C7/C11: c_i^mo = x_mo^i * c_mo
        distributed_amount = standardized_amount * x_i
        return distributed_amount, 'c'

    elif amount_type == 'ρ':
        # C8/C12: ρ_i^mo = (M_i / M_mo) * ρ_mo * x_mo^i
        distributed_amount = standardized_amount * (M_i / M_mo) * x_i
        return distributed_amount, 'ρ'

    elif amount_type == 'b':
        # C9/C13: b_i^mo = x_mo^i * b_mo
        distributed_amount = standardized_amount * x_i
        return distributed_amount, 'b'

    elif amount_type == 'v':
        # C10/C14: v_i^mo = (V_m,i / M_mo) * v_mo * x_mo^i
        distributed_amount = standardized_amount * (V_m_i / M_mo) * x_i
        return distributed_amount, 'v'

    else:
        print(f"Warning: Unknown amount type '{amount_type}'")
        return 0.0, amount_type

def get_mole_fractions_recursive(all_nodes, include_entities=True):
    nodes_by_level, node_types = classify_node_levels(all_nodes)
   
    
    # For each level we determine the composition. We start with assumption of x = 1 for each component
    for node_name in nodes_by_level[0]:
        node = all_nodes.get(node_name)
        
        # Level 0: Base components
        # Add component to itself with mole fraction of 1
        node['components'] = {
            node_name: {
                "name": node_name,
                "mw": node.get("mw", 0),
                "vm": node.get("vm", 0),
                "x": 1.0,  # Mole fraction = 1 for pure component
                "properties": node.get("properties", {})
            }
        }
        # For base components, Mw_mix and Vm_mix are just their own values
        node['Mw_mix'] = node.get("mw", 0)
        node['Vm_mix'] = node.get("vm", 0) / 1000
        
    for i in range(len(nodes_by_level)-1):
        for node_name in nodes_by_level[i+1]:
            # Get nodes
            node = all_nodes.get(node_name)
            
            # Initialize component list for the "solvent" (non-molality components)
            component_list = list()
            
            # Separate molality parents from non-molality parents
            # Molality components are solutes that will be added after calculating the solvent composition
            molality_parents = []
            non_molality_parents = []
            
            for parent in node["parents"]:
                if parent["amount_type"] == "b":
                    molality_parents.append(parent)
                else:
                    non_molality_parents.append(parent)
            
            # Process non-molality parents to build the "solvent" composition
            for parent in non_molality_parents:
                parent_node = all_nodes.get(parent["name"])
                
                amount_type         = parent["amount_type"]
                standardized_amount = convert_to_standard_unit(parent["amount"], parent["amount_type"], parent["unit"])
                
                # Collect mixture properties
                M_mo                = parent_node["Mw_mix"]  
                V_mo                = parent_node["Vm_mix"] 
                
                # Assign individual components of parent mixture to the current mixture
                for component in parent_node['components']:
                    comp_node = parent_node['components'].get(component)
                    
                    # Get mole fraction of component in parent mixture
                    x_i   = comp_node["x"] 
                    
                    # Get component properties
                    M_i   = comp_node["mw"]
                    V_m_i = comp_node["vm"] / 1000  # L/mol
                    
                    # Get amounts of components from parent mixture
                    comp_node["amount"], comp_node["amount_type"] = distribute_mixture_component(amount_type, standardized_amount, M_mo, V_mo, x_i, M_i, V_m_i)
                    comp_node["unit"] = amount_type_to_std_unit[comp_node["amount_type"]]
                    component_list.append(comp_node)
            
            # Calculate the "solvent" composition (mixture without molality solutes)
            if component_list:  # Only if there are non-molality components
                matrix, names, Mw, Vm = create_amount_matrix(component_list)
                x, Mw_av, Vm_av, n_tot, no_abs = mole_fraction_algebra(matrix, Mw, Vm)
            else:
                # Edge case: only molality components (shouldn't happen in practice)
                names = []
                Mw = array([])
                Vm = array([])
                x = array([])
                Mw_av = 0
                Vm_av = 0
                n_tot = 0
                no_abs = True
            
            # Apply molality constraints if any exist
            # Each molality component is a solute in the solvent mixture calculated above
            if molality_parents:
                # For each molality parent, we need to add it to the mixture
                # using the molality constraint equation
                
                for parent in molality_parents:
                    parent_name = parent['name']
                    parent_node = all_nodes.get(parent_name)
                    
                    # Convert molality to standard units (mol/g)
                    molality_value = convert_to_standard_unit(parent['amount'], parent['amount_type'], parent['unit'])
                    
                    # Check if this parent is a mixture or a simple component
                    if 'components' in parent_node and len(parent_node['components']) > 1:
                        # Parent is a mixture - this means molality is specified for an entire mixture
                        # We need to treat each component of this mixture as having proportional molality
                        
                        # For a mixture parent with molality, distribute the molality proportionally
                        # to each component based on their mole fraction in that mixture
                        mixture_components = []
                        for comp_name, comp_data in parent_node['components'].items():
                            comp_fraction = comp_data['x']
                            comp_mw = comp_data['mw']
                            comp_vm = comp_data['vm']
                            
                            # This component gets a fraction of the molality
                            comp_molality = molality_value * comp_fraction
                            
                            mixture_components.append({
                                'name': comp_name,
                                'mw': comp_mw,
                                'vm': comp_vm / 1000,  # Convert to L/mol
                                'molality': comp_molality,
                                'properties': comp_data.get('properties', {})
                            })
                        
                        # Now add all these components using their distributed molality
                        for solute_comp in mixture_components:
                            solute_name = solute_comp['name']
                            solute_molality = solute_comp['molality']
                            solute_mw = solute_comp['mw']
                            solute_vm = solute_comp['vm']
                            
                            # Calculate solute mole fraction using molality equation
                            # x_solute = (b * M_solvent) / (1 + b * M_solvent)
                            # where M_solvent is the average molar weight of the current solvent mixture
                            x_solute = (solute_molality * Mw_av) / (1 + solute_molality * Mw_av)
                            
                            # Add this component to the mixture
                            # Rescale existing components by (1 - x_solute)
                            x = x * (1 - x_solute)
                            
                            # Append the new component
                            names = list(names) + [solute_name]
                            Mw = np.append(Mw, solute_mw)
                            Vm = np.append(Vm, solute_vm)
                            x = np.append(x, x_solute)
                            
                            # Update component_list for later processing
                            component_list.append({
                                'name': solute_name,
                                'mw': solute_mw,
                                'vm': solute_vm * 1000,  # Back to mL/mol for consistency
                                'x': x_solute,
                                'amount': x_solute,
                                'amount_type': 'x',
                                'unit': '-',
                                'properties': solute_comp.get('properties', {})
                            })
                            
                            # Recalculate average properties
                            Mw_av = np.dot(x, Mw)
                            Vm_av = np.dot(x, Vm)
                    else:
                        # Parent is a simple component (solute)
                        solute_name = parent_name
                        solute_mw = parent_node.get('mw', 0)
                        solute_vm = parent_node.get('vm', 0) / 1000  # Convert to L/mol
                        
                        # Calculate solute mole fraction using molality equation
                        # x_solute = (b * M_solvent) / (1 + b * M_solvent)
                        x_solute = (molality_value * Mw_av) / (1 + molality_value * Mw_av)
                        
                        # Rescale existing (solvent) components by (1 - x_solute)
                        x = x * (1 - x_solute)
                        
                        # Append the solute component
                        names = list(names) + [solute_name]
                        Mw = np.append(Mw, solute_mw)
                        Vm = np.append(Vm, solute_vm)
                        x = np.append(x, x_solute)
                        
                        # Update component_list for later processing
                        component_list.append({
                            'name': solute_name,
                            'mw': solute_mw,
                            'vm': solute_vm * 1000,  # Back to mL/mol
                            'x': x_solute,
                            'amount': x_solute,
                            'amount_type': 'x',
                            'unit': '-',
                            'properties': parent_node.get('properties', {})
                        })
                        
                        # Recalculate average properties
                        Mw_av = np.dot(x, Mw)
                        Vm_av = np.dot(x, Vm)
            
            # Add mixture properties to the node
            node['Mw_mix'] = Mw_av
            node['Vm_mix'] = Vm_av
            node['n_tot']  = n_tot if not no_abs else None
            
            # Assign computed mole fractions to each component of the node
            for j in range(len(component_list)):
                comp_name = component_list[j]['name']
                # Find this component in the names list
                if comp_name in names:
                    idx = names.index(comp_name) if isinstance(names, list) else list(names).index(comp_name)
                    component_list[j]["x"] = x[idx]
             
            # Manage duplicates             
            combined = {}
            
            for comp in component_list:
                comp_name = comp['name']
                if comp_name in combined:
                    # Add mole fractions for duplicates
                    combined[comp_name]['x'] += comp.get('x', 0)
                else:
                    # First occurrence of this component
                    combined[comp_name] = comp.copy()
            
            components_list = list(combined.values())
            
            components_dict = {}
            for comp in components_list:
                comp_name = comp['name']
                components_dict[comp_name] = comp
            
            # Append components and their mole fractions to the node
            node['components'] = components_dict
            
               
            if node_types[node_name] == "terminal":
                # Extract component mole fractions
                node["component_mole_fractions"] = {
                    comp_name: comp['x'] 
                    for comp_name, comp in node['components'].items()
                }
                
                # Extract entities information
                entities_information = []
                for comp_name, comp in node['components'].items():
                    # Check if component has defined entities
                    if 'properties' in comp and 'entities' in comp['properties'] and comp['properties']['entities']:
                        # Use defined entities
                        for entity in comp['properties']['entities']:
                            entities_information.append([
                                entity['name'],
                                comp_name,
                                entity['stoichiometry']
                            ])
                    else:
                        # Default: use component name as entity with stoichiometry 1
                        entities_information.append([
                            comp_name,
                            comp_name,
                            1.0
                        ])
                 
                entity_mole_fractions = entities_mole_fraction_algebra(entities_information, node["component_mole_fractions"])    
                
                # Store entity mole fractions in the node
                node['entity_mole_fractions'] = entity_mole_fractions
                
                # For terminal mixtures, update components with standardized mole fraction amount
                for comp_name, comp in node['components'].items():
                    # Set the amount as the mole fraction
                    comp['amount'] = comp['x']
                    comp['amount_type'] = 'x'
                    comp['unit'] = '-'
                    
                # Extract component information for conversion
                component_list = []
                for comp_name, comp_node in node["components"].items():
                    
                    # Find original component data in all_nodes
                    for node_C in all_nodes.values():
                        if 'components' in node_C and comp_name in node_C['components']:
                            component = node_C['components'][comp_name].copy()
                            component["x"] = comp_node["x"]
                            component["amount"] = comp_node["x"]
                            component["amount_type"] = "x"
                            component["unit"] = "-"
                            component_list.append(component)
                            break
                node["component_list"] = component_list
                
               
                    
                
                
    # Collect terminal mixture results at the end
    terminal_results = list()
    
    for node_name, node_type in node_types.items():
        if node_type == "terminal":
            node = all_nodes.get(node_name)
            
            # Create a clean result structure for this terminal mixture
            terminal_results.append( {
                'name'                        : node_name,
                'mole_fractions'              : node["component_mole_fractions"],
                'average_molar_weight'        : node["Mw_mix"],
                'average_molar_volume_L_mol'  : node["Vm_mix"],
                'average_molar_volume_mL_mol' : node["Vm_mix"] * 1000,
                'component list'              : node["component_list"],
                'total_moles'                 : node['n_tot']         
            })
            
            # Add entity mole fractions if calculated
            if 'entity_mole_fractions' in node:
                terminal_results[-1]["entity_mole_fractions"] = node["entity_mole_fractions"]
    
    return terminal_results
def classify_node_levels(all_nodes):
    """
    Classifies nodes into levels and flags them as intermediate or terminal.
    - Level 0: Nodes with no parents (base components)
    - Level 1: Nodes made directly from level 0 components
    - Level 2: Nodes with at least one Level 1 node as parent
    - Level 3: Nodes with at least one Level 2 node as parent
    And so on.
    
    Also flags nodes as:
    - "intermediate": Used as parent by at least one other node
    - "terminal": Not used as a parent by any other node
    
    Args:
        all_nodes: Dictionary containing all nodes
        
    Returns:
        Tuple: (nodes_by_level, node_types)
        - nodes_by_level: List of lists where each sublist contains nodes of the same level
        - node_types: Dictionary mapping node names to "intermediate" or "terminal"
    """
    # Initialize a dictionary to store the level of each node
    levels = {}
    
    def get_node_level(node_name):
        # If we've already calculated the level, return it
        if node_name in levels:
            return levels[node_name]
        
        # Get the node
        node = all_nodes.get(node_name)
        
        # If node doesn't exist or has no parents, it's a level 0 node
        if not node or 'parents' not in node or not node['parents']:
            levels[node_name] = 0
            return 0
        
        # Calculate the level as 1 + max(parent levels)
        parent_levels = [get_node_level(parent['name']) for parent in node['parents']]
        level = 1 + max(parent_levels)
        
        # Store and return the level
        levels[node_name] = level
        return level
    
    # Calculate the level for each node
    for node_name in all_nodes:
        get_node_level(node_name)
    
    # Identify which nodes are used as parents (intermediate nodes)
    used_as_parent = set()
    for node_name, node in all_nodes.items():
        if 'parents' in node and node['parents']:
            for parent in node['parents']:
                used_as_parent.add(parent['name'])
    
    # Flag nodes as intermediate or terminal
    node_types = {}
    for node_name in all_nodes:
        if node_name in used_as_parent:
            node_types[node_name] = "intermediate"
        else:
            node_types[node_name] = "terminal"
    
    # Convert the levels dictionary to a list of lists
    max_level = max(levels.values()) if levels else 0
    nodes_by_level = [[] for _ in range(max_level + 1)]
    
    for node_name, level in levels.items():
        nodes_by_level[level].append(node_name)
    
    return nodes_by_level, node_types

''' calculation functions '''

def mole_fraction_algebra(matrix, Mw, Vm): 

    '''beginning of mathematical transformations'''
    #extract quantity vectors
    n_components = len(Mw)
    m_m          = matrix[:,0]    
    V_V          = matrix[:,1]    
    n_n          = matrix[:,2]    
    w_w_0        = matrix[:,3]    
    phi_phi_0    = matrix[:,4]    
    x_x_0        = matrix[:,5]    
    c_c          = matrix[:,6]    
    bstar_b      = matrix[:,7]    
    rho_rho      = matrix[:,8]    
    vstar_v      = matrix[:,9]    


    #define known composition variables
    no_abs     = np_all(matrix[:, :3] < 10**-10)
    Mw_abs     = 0.
    Vm_abs     = 0.
    m_abs      = 0.
    V_abs      = 0.
    n_abs      = 0.
    x_x_0t     = 0.
    Mw_x_0     = 0.
    Vm_x_0     = 0.
    bstar_w_0  = 0.
    w_w_0t     = 0.
    vstar_w_0  = 0.
    c_phi_0    = 0.
    rho_phi_0  = 0.
    phi_phi_0t = 0.
    bstar_bv   = 0.
    vstar_bv   = 0.
    w_bv       = 0.
    c_crho     = 0.
    rho_crho   = 0.
    phi_crho   = 0.
    
    #compute known composition variables
    for I in range(n_components):
        # Absolute mass, volume, number of moles
        if not no_abs: #only if the number of moles in absolute quantity is non zero
            m_abs  += n_n[I] * Mw[I] + m_m[I]                 + V_V[I] * Mw[I] / Vm[I]
            V_abs  += n_n[I] * Vm[I] + m_m[I] * Vm[I] / Mw[I] + V_V[I] 
            n_abs  += n_n[I]         + m_m[I]         / Mw[I] + V_V[I]         / Vm[I]  
        # Contributions of relative amounts to total mole fraction, average molar weight and volume of mixture
        x_x_0t     += x_x_0[I]
        Mw_x_0     += x_x_0[I] * Mw[I]
        Vm_x_0     += x_x_0[I] * Vm[I]       
        # overall molality due to mass fraction, overall mass fraction, specific volume due to mass fraction
        bstar_w_0  += w_w_0[I]         / Mw[I]
        w_w_0t     += w_w_0[I] 
        vstar_w_0  += w_w_0[I] * Vm[I] / Mw[I]
        # molarity due to volume fraction, mass concentration due to volume fraction, overall volume fraction
        c_phi_0    += phi_phi_0[I]         / Vm[I]
        rho_phi_0  += phi_phi_0[I] * Mw[I] / Vm[I] 
        phi_phi_0t += phi_phi_0[I]
        # overall molality, partial specific volume, weight fraction due to (b+v)
        bstar_bv   +=          bstar_b[I]         + vstar_v[I]     / Vm[I]
        vstar_bv   +=          bstar_b[I] * Vm[I] + vstar_v[I]
        w_bv       += Mw[I] * (bstar_b[I] +         vstar_v[I]     / Vm[I])
        # molarity, density, volume fraction due to (c+rho)
        c_crho     +=          c_c[I]         + rho_rho[I] / Mw[I]
        rho_crho   +=          c_c[I] * Mw[I] + rho_rho[I]
        phi_crho   += Vm[I] * (c_c[I]         + rho_rho[I] / Mw[I])
    #absolute molar weight and volume
    if not no_abs:
        Mw_abs = m_abs / n_abs
        Vm_abs = V_abs / n_abs
    
    
    # identification of the algebraic problem
    only_relative_amounts = False
    only_absolute_amounts = False
    no_solutes            = False
    no_absolute_amounts   = False
    no_relative_amounts   = False
    general_case          = False
    if (not np_any(bstar_b)) and (not np_any(c_c)) and (not np_any(rho_rho)) and (not np_any(vstar_v)):
        if (not np_any(m_m)) and (not np_any(V_V)) and (not np_any(n_n)):
            #case of relative amounts only
            only_relative_amounts = True
        else:
             if (not np_any(w_w_0)) and (not np_any(phi_phi_0)) and (not np_any(x_x_0)): 
                 #case of absolute amounts only
                 only_absolute_amounts = True
             else:
                 #case of no solutes
                 no_solutes = True
    else:
         if (not np_any(m_m)) and (not np_any(V_V)) and (not np_any(n_n)):
             #case of no absolute amounts
             no_absolute_amounts = True
         else:
             if (not np_any(w_w_0)) and (not np_any(phi_phi_0)) and (not np_any(x_x_0)): 
                 #no relative amounts
                 no_relative_amounts = True
             else:
                 #general case
                 general_case = True
    
    # construction and inversion of the UAC conversion matrix
    C = zeros((6, 6))
    r = zeros((6))
    
    """START MATRIX C"""
    C[0][0] =   1
    C[0][1] = bstar_w_0
    C[0][2] = c_phi_0
    C[1][3] = 1
    C[1][4] = - bstar_bv
    C[1][5] = - c_crho
    C[2][0] = Mw_abs
    C[2][1] = w_w_0t    - 1
    C[2][2] = rho_phi_0
    C[3][1] = 1
    C[3][4] = w_bv - 1
    C[3][5] = rho_crho
    C[4][0] = Vm_abs
    C[4][1] = vstar_w_0
    C[4][2] = phi_phi_0t - 1
    C[5][2] = 1
    C[5][4] = vstar_bv
    C[5][5] = phi_crho - 1
    """END MATRIX C"""
    
    """START VECTOR r"""
    r[0]    =   1 - x_x_0t
    r[1]    =   1
    r[2]    = - Mw_x_0
    r[4]    = - Vm_x_0
    """END VECTOR r"""
    
    #allocating known variables if any
    if general_case:
        knowns = []
    if no_absolute_amounts:
        knowns = [[0, 0]]
    if no_relative_amounts:
        knowns = [[0,1]]
        
    if no_solutes:
        knowns = [[3,1],
                  [4,"=1"],
                  [5,"=2"]]
    if only_relative_amounts:
        knowns = [[0, 0],
                  [3,1],
                  [4,"=1"],
                  [5,"=2"]]
    if only_absolute_amounts:
        knowns = [[0, 1],
                  [3,1],
                  [4,"=1"],
                  [5,"=2"]]
    #resolving the system
    t = solve_partitioned_system(C, r, knowns)
    
    # extraction of relevant variables from target vector
    x_abs_0 = t[0]
    Mw_0    = t[1]
    Vm_0    = t[2]
    x_0     = 1 / t[3]
    Mw_av   = t[4] * x_0
    Vm_av   = t[5] * x_0    
    
    # print(only_relative_amounts,
    # only_absolute_amounts,
    # no_solutes,
    # no_absolute_amounts,
    # no_relative_amounts,
    # general_case)
    
    # print(t)
    # print(x_abs_0, x_0)
    
    #computation of mole fractions (eq. 1 in the paper)
    x = zeros((n_components))
    for I in range(n_components):
        if n_abs > 10**-10:
            x[I] = x_0 * ( (n_n[I] + m_m[I] / Mw[I] + V_V[I] / Vm[I]) / n_abs * x_abs_0 + x_x_0[I] + w_w_0[I] / Mw[I] * Mw_0 + phi_phi_0[I] / Vm[I] * Vm_0 ) + bstar_b[I] * Mw_av + c_c[I] * Vm_av + vstar_v[I] * Mw_av / Vm_av + rho_rho[I] * Vm_av / Mw_av
            
        else:
            x[I] = x_0 * ( x_x_0[I] + w_w_0[I] / Mw[I] * Mw_0 + phi_phi_0[I] / Vm[I] * Vm_0 )  + bstar_b[I] * Mw_av + c_c[I] * Vm_av + vstar_v[I] * Mw_av / Vm_av + rho_rho[I] * Vm_av / Mw_av
    
    #computation of total number of moles if relevant
    if n_abs > 10**-10:
        n_tot = n_abs / (x_abs_0 * x_0)
    else:
        n_tot = 0
    return x, Mw_av, Vm_av, n_tot, no_abs
def entities_mole_fraction_algebra(entities_information, component_mole_fractions):
    """
    Calculate mole fractions for all entities based on their parent components.
    
    Args:
        entities_information (list): A list of lists where each inner list has the format 
                                    [Entity, Parent component, Stoichiometry]
        component_mole_fractions (dict): Dictionary mapping component names to their mole fractions
        
    Returns:
        dict: Dictionary mapping entity names to their mole fractions
    """
    # Initialize dictionaries for calculations
    entity_contributions = {}  # To track each entity's contribution
    
    # First pass: calculate raw entity contributions from each component
    total_contribution = 0.0
    
    for entity, parent, stoichiometry in entities_information:
        # Skip if parent component is not in the component mole fractions
        if parent not in component_mole_fractions:
            continue
            
        # Get parent component's mole fraction
        parent_mole_fraction = component_mole_fractions[parent]
        
        # Calculate entity contribution from this parent (weighted by stoichiometry)
        contribution = parent_mole_fraction * stoichiometry
        
        # Add to the entity's total contribution
        if entity in entity_contributions:
            entity_contributions[entity] += contribution
        else:
            entity_contributions[entity] = contribution
            
        # Update total contribution for normalization
        total_contribution += contribution
        
        # print(entity, parent, component_mole_fractions[parent], stoichiometry, contribution, total_contribution)
    
    # Second pass: normalize to ensure sum equals 1.0
    entity_mole_fractions = {}
    if total_contribution > 0:
        for entity, contribution in entity_contributions.items():
            entity_mole_fractions[entity] = contribution / total_contribution
    
    return entity_mole_fractions
def amount_conversion_algebra(mole_fractions, Mw, Vm, target_types, total_amount=1.0, total_amount_type="n"):
    """
    Converts mole fractions to different amount types according to the
    equations in Table 5 of the reference document, automatically
    identifying solutes based on target types.
    
    Parameters:
    mole_fractions (ndarray): Array of mole fractions for each component
    Mw (ndarray): Array of molar weights for each component (g/mol)
    Vm (ndarray): Array of molar volumes for each component (L/mol)
    target_types (list): List of target amount types for conversion
    total_amount (float): The total amount of the mixture (in standardized units)
    total_amount_type (str): The type of total amount ('n', 'm', or 'V')
    
    Returns:
    ndarray: Matrix of converted amounts
    float: Average molar weight
    float: Average molar volume
    """
    # Convert inputs to numpy arrays for safety
    mole_fractions = array(mole_fractions)
    Mw = array(Mw)
    Vm = array(Vm)
    
    # Calculate average molar weight and volume of the entire mixture
    Mw_av = sum(mole_fractions * Mw)
    Vm_av = sum(mole_fractions * Vm)
    
    # Calculate total moles (n_tot) based on the provided total amount
    if total_amount_type == "n":  # If total amount is already in moles
        n_tot = total_amount
    elif total_amount_type == "m":  # If total amount is in mass
        # n_tot = m_tot / Mw_av
        n_tot = total_amount / Mw_av
    elif total_amount_type == "V":  # If total amount is in volume
        # n_tot = V_tot / Vm_av
        n_tot = total_amount / Vm_av
    else:
        # Default to 1.0 mol if type is not recognized
        n_tot = 1.0
    
    # Create result matrix with dimensions [n_components × 1]
    n_components = len(mole_fractions)
    result_matrix = zeros((n_components, 1))
    
    # Identify which components are solutes based on their target types
    # The concentration target types (c, b, ρ, v) identify solutes
    concentration_types = ["c", "b*", "ρ", "v*"]  # c, b, ρ, v
    is_solute = [target_types[i] in concentration_types for i in range(n_components)]
    
    # Calculate x_0 - the total mole fraction of solvents (non-solutes)
    x_0 = sum([mole_fractions[i] for i in range(n_components) if not is_solute[i]])
    if x_0 <= 0:
        # If all components were identified as solutes, use the total as fallback
        x_0 = 1.0
    
    # Calculate average molar weight and volume of just the solvent portion
    # First, create normalized mole fractions for solvents
    if x_0 > 0:
        solvent_mole_fractions = array([mole_fractions[i] / x_0 if not is_solute[i] else 0 
                                      for i in range(n_components)])
    else:
        solvent_mole_fractions = mole_fractions  # Fallback
    
    # Calculate solvent-only averages
    Mw_solvent_av = sum(solvent_mole_fractions * Mw)
    Vm_solvent_av = sum(solvent_mole_fractions * Vm)
    
    # Convert mole fractions to target types
    for i, target_type in enumerate(target_types):
        # Get the mole fraction, molar weight, and molar volume for this component
        x_i = mole_fractions[i]
        M_i = Mw[i]
        V_m_i = Vm[i]
        
        # Convert based on target type, using equations from Table 5
        # For each case, multiply by n_tot to scale according to total amount
        if target_type == "n":  # Number of moles
            # n_i = x_i * n_tot
            result_matrix[i, 0] = x_i * n_tot  # mol
            
        elif target_type == "m":  # Mass
            # m_i = x_i * n_tot * M_i
            result_matrix[i, 0] = x_i * n_tot * M_i  # g
            
        elif target_type == "V":  # Volume
            # V_i = x_i * n_tot * V_m,i
            result_matrix[i, 0] = x_i * n_tot * V_m_i  # L
            
        elif target_type == "x":  # Mole fraction
            # Relative mole fraction x_i^0 = x_i / x_0
            # Note: Mole fractions are ratios, so they're not affected by total amount
            result_matrix[i, 0] = x_i / x_0  # Unitless fraction
            
        elif target_type == "w":  # Weight fraction
            # Relative mass fraction w_i^0 = (x_i * M_i) / (x_0 * M̄)
            # Where M̄ is the average molar weight of the solvent portion
            # Note: Weight fractions are ratios, so they're not affected by total amount
            result_matrix[i, 0] = (x_i * M_i) / (x_0 * Mw_solvent_av)  # Unitless fraction
            
        elif target_type == "φ":  # Volume fraction (phi)
            # Relative volume fraction φ_i^0 = (x_i * V_m,i) / (x_0 * V̄)
            # Where V̄ is the average molar volume of the solvent portion
            # Note: Volume fractions are ratios, so they're not affected by total amount
            result_matrix[i, 0] = (x_i * V_m_i) / (x_0 * Vm_solvent_av)  # Unitless fraction
            
        elif target_type == "b*":  # Overall molality
            # b_i = (x_i * n_tot) / (x_0 * n_tot * Mw_av) = x_i / (x_0 * Mw_av)
            result_matrix[i, 0] = x_i / (x_0 * Mw_av)  # mol/g (will be converted to mol/kg in UI)
            
        elif target_type == "c":  # Molarity
            # c_i = x_i * n_tot / V_total
            # V_total = n_tot * Vm_av
            # Therefore: c_i = x_i / Vm_av
            result_matrix[i, 0] = x_i / Vm_av  # mol/L
            
        elif target_type == "ρ":  # Mass concentration (rho)
            # ρ_i = x_i * M_i * n_tot / V_total
            # V_total = n_tot * Vm_av
            # Therefore: ρ_i = (x_i * M_i) / Vm_av
            result_matrix[i, 0] = (x_i * M_i) / Vm_av  # g/L
            
        elif target_type == "v*":  # Partial specific volume
            # v_i = V_i / m_total = (x_i * n_tot * V_m,i) / (n_tot * Mw_av)
            # Therefore: v_i = (x_i * V_m,i) / Mw_av
            result_matrix[i, 0] = (x_i * V_m_i) / Mw_av  # L/g
            
        elif target_type == "b":  # Traditional molality - NEW CASE
            # Calculate according to the equation: b_solute = (x_solute/M_solvent) * (1-x_solute)
            # Where M_solvent is the average molar weight of all components except this one
            
            # Skip if this component has mole fraction of 1 (no solvent)
            if x_i >= 0.999:
                result_matrix[i, 0] = 0  # Cannot have molality without solvent
                continue
                
            # Calculate solvent mole fraction (everything except this component)
            x_solvent = 1.0 - x_i
            
            # Calculate solvent average molar weight
            # Create normalized weights for all components except this one
            solvent_weights = zeros(n_components)
            for j in range(n_components):
                if j != i:  # Skip the current component (our solute)
                    # Normalize by total solvent mole fraction
                    solvent_weights[j] = mole_fractions[j] / x_solvent
            
            # Calculate average molar weight of the solvent
            M_solvent = sum(solvent_weights * Mw)
            
            # Calculate molality according to the equation
            # b^solute_solvent = (x_solute/M_solvent) * (1-x_solute)
            result_matrix[i, 0] = (x_i / M_solvent) * x_solvent  # mol/g (will be converted to mol/kg in UI)
    
    return result_matrix, Mw_av, Vm_av
def populate_unit_cell(component_mole_fractions, component_molar_volumes, component_entities, cell_params, round_counts=True):
    """
    Given component mole fractions, component molar volumes, and the mapping of components to their entities (with stoichiometry),
    compute the number of each entity that populate the unit cell.
    
    Parameters:
        component_mole_fractions (dict): Mapping of component names to their mole fractions.
                                           The mole fractions should sum to 1.
        component_molar_volumes (dict): Mapping of component names to their molar volumes (in L/mol).
        component_entities (dict): Mapping of component names to a list of (entity_name, stoichiometry) pairs.
                                   If a component is not present in this dictionary, it is assumed that the component 
                                   is its own entity with stoichiometry 1.
        cell_params (dict): Dictionary with unit cell parameters:
            - 'a', 'b', 'c': Edge lengths (in angstroms)
            - 'alpha', 'beta', 'gamma': Interaxial angles (in degrees)
            The function computes the cell volume in Å³ and then converts it to liters.
        round_counts (bool): If True, round the calculated counts to the nearest integer.
        
    Returns:
        dict: A dictionary containing:
            - 'cell_volume_L': The unit cell volume in liters.
            - 'total_moles': Total number of moles that would fill the cell.
            - 'component_counts': A dictionary mapping each component name to its count in the cell.
            - 'entity_counts': A dictionary mapping each entity name to its count in the cell.
    """
    # Unpack cell parameters (assumed to be in angstroms and degrees)
    a = cell_params.get('a')
    b = cell_params.get('b')
    c = cell_params.get('c')
    alpha_deg = cell_params.get('alpha')
    beta_deg  = cell_params.get('beta')
    gamma_deg = cell_params.get('gamma')
    
    # Convert angles from degrees to radians
    alpha = math.radians(alpha_deg)
    beta  = math.radians(beta_deg)
    gamma = math.radians(gamma_deg)
    
    # Calculate cell volume in Å³ using the general formula
    volume_A3 = a * b * c * math.sqrt(
        1 - math.cos(alpha)**2 - math.cos(beta)**2 - math.cos(gamma)**2 +
        2 * math.cos(alpha) * math.cos(beta) * math.cos(gamma)
    )
    
    # Convert volume from Å³ to liters (1 Å³ = 1e-24 L)
    cell_volume_L = volume_A3 * 1e-24
    
    # Compute the average molar volume of the mixture (L/mol) weighted by component mole fractions.
    V_avg = 0.0
    for comp, x in component_mole_fractions.items():
        v_comp = component_molar_volumes.get(comp)
        if v_comp is None:
            raise ValueError(f"Molar volume for component '{comp}' is not provided.")
        V_avg += x * v_comp
    
    if V_avg <= 0:
        raise ValueError("The computed average molar volume must be positive.")
    
    # Total number of moles that fill the unit cell (mol)
    total_moles = cell_volume_L / V_avg
    
    # Avogadro's number (entities per mol)
    NA = 6.02214076e23
    
    # Calculate component counts
    component_counts = {}
    for comp, x in component_mole_fractions.items():
        moles_comp = x * total_moles  # moles of the component
        count_comp = moles_comp * NA   # number of molecules (entities) for the component
        if round_counts:
            count_comp = int(round(count_comp))
        component_counts[comp] = count_comp
    
    # Distribute counts to entities using stoichiometry.
    # If a component is not in component_entities, assume it is its own entity with stoichiometry 1.
    entity_counts = {}
    for comp, comp_count in component_counts.items():
        entities = component_entities.get(comp, [(comp, 1)])
        for entity, stoich in entities:
            # Multiply the component count by the stoichiometric coefficient.
            count_entity = comp_count * stoich
            if round_counts:
                count_entity = int(round(count_entity))
            # Sum counts if the entity appears from more than one component.
            if entity in entity_counts:
                entity_counts[entity] += count_entity
            else:
                entity_counts[entity] = count_entity
    
    return {
        'cell_volume_L': cell_volume_L,
        'total_moles': total_moles,
        'component_counts': component_counts,
        'entity_counts': entity_counts
    }