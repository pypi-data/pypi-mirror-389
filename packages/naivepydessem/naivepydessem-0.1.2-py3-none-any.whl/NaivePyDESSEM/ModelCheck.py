"""
EELT 7030 — Operation and Expansion Planning of Electric Power Systems  
Federal University of Paraná (UFPR)

Module: Model Component Validators

Author
------
Augusto Mathias Adams <augusto.adams@ufpr.br>

Description
-----------
This module provides a set of utility functions to verify whether a given Pyomo
`ConcreteModel` contains the essential variables, parameters, and sets required
for each subsystem in an energy dispatch problem.

The validation is modular and lightweight, designed to support the dynamic
assembly of hybrid dispatch models comprising:
- Hydropower units
- Thermal generation units
- Renewable generation sources
- Energy storage systems

These functions are typically used to determine the feasibility of operations
such as cost extraction, result formatting, or diagnostics on a per-subsystem basis.

Functions
---------
- has_hydro_model(model): Checks presence of hydropower-related variables.
- has_thermal_model(model): Checks presence of thermal generation variables.
- has_renewable_model(model): Checks presence of renewable generation variables.
- has_storage_model(model): Checks presence of storage system variables.

Usage Example
-------------
>>> if has_thermal_model(m):
>>>     print("Thermal model components detected.")

References
----------
[1] CEPEL, DESSEM. Manual de Metodologia, 2023  
[2] Unsihuay Vila, C. Introdução aos Sistemas de Energia Elétrica, Lecture Notes, EELT7030/UFPR, 2023.
"""

from pyomo.environ import ConcreteModel


def has_hydro_model(model: ConcreteModel) -> bool:
    """
    Check whether the given Pyomo model contains all components of a hydro subsystem.

    This function verifies the presence of essential attributes associated with
    hydropower modeling, including sets and variables related to generation,
    volume, flow, and spillage.

    Parameters
    ----------
    model : ConcreteModel
        The Pyomo model instance to be validated.

    Returns
    -------
    bool
        True if all required hydro components are present, False otherwise.

    Notes
    -----
    The required attributes are:
    - T         : Time periods.
    - HG        : Set of hydro units.
    - hydro_G   : Hydropower generation variable.
    - hydro_V   : Reservoir volume variable.
    - hydro_Q   : Turbined flow variable.
    - hydro_S   : Spillage flow variable.
    """

    required = [
        'T', 'HG', 'hydro_G', 'hydro_V', 'hydro_Q', 'hydro_S'
    ]
    if all(hasattr(model, attr) for attr in required):
        return True
    return False


def has_thermal_model(model: ConcreteModel) -> bool:
    """
    Check whether the given Pyomo model contains all components of a thermal subsystem.

    This function validates the existence of typical thermal dispatch variables,
    including generation, commitment status, and startup/shutdown indicators.

    Parameters
    ----------
    model : ConcreteModel
        The Pyomo model instance to be validated.

    Returns
    -------
    bool
        True if all required thermal components are present, False otherwise.

    Notes
    -----
    The required attributes are:
    - T             : Time periods.
    - TG            : Set of thermal units.
    - thermal_p     : Power generation variable.
    - thermal_u     : Commitment status variable (binary).
    - thermal_w     : Shutdown indicator variable (binary).
    - thermal_y     : Startup indicator variable (binary).
    - thermal_SC    : Start-up cost parameter.
    """

    required = [
        'T', 'TG', 'thermal_p', 'thermal_u', 'thermal_w',
        'thermal_y', 'thermal_SC'
    ]
    if all(hasattr(model, attr) for attr in required):
        return True
    return False


def has_renewable_model(model: ConcreteModel) -> bool:
    """
    Check whether the given Pyomo model contains all components of a renewable subsystem.

    This function verifies whether the model has the necessary sets and variables
    to support renewable generation units.

    Parameters
    ----------
    model : ConcreteModel
        The Pyomo model instance to be validated.

    Returns
    -------
    bool
        True if all required renewable components are present, False otherwise.

    Notes
    -----
    The required attributes are:
    - T               : Time periods.
    - RU              : Set of renewable units.
    - renewable_gen   : Renewable generation variable.
    """

    required = [
        'T', 'RU', 'renewable_gen'
    ]
    if all(hasattr(model, attr) for attr in required):
        return True
    return False


def has_storage_model(model: ConcreteModel) -> bool:
    """
    Check whether the given Pyomo model contains all components of a storage subsystem.

    This function ensures that charging, discharging, and state-of-charge variables
    are defined for energy storage modeling.

    Parameters
    ----------
    model : ConcreteModel
        The Pyomo model instance to be validated.

    Returns
    -------
    bool
        True if all required storage components are present, False otherwise.

    Notes
    -----
    The required attributes are:
    - T              : Time periods.
    - SU             : Set of storage units.
    - storage_dis    : Discharging power variable.
    - storage_ch     : Charging power variable.
    - storage_E      : Energy (state-of-charge) variable.
    """

    required = [
        'T', 'SU', 'storage_dis', 'storage_ch', 'storage_E'
    ]
    if all(hasattr(model, attr) for attr in required):
        return True
    return False
