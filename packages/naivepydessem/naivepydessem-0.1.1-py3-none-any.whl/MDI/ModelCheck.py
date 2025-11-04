
"""
ModelCheck Module
=================
EELT7030 — Operation and Expansion Planning of Electric Power Systems  
Federal University of Paraná (UFPR)

Author
------
Augusto Mathias Adams <augusto.adams@ufpr.br>

Summary
-------
The **ModelCheck** module provides lightweight structural verification
utilities for **Pyomo ConcreteModel** instances within the
**MDI (Modular Decision Infrastructure)** framework.

Its purpose is to confirm the presence of essential attributes,
sets, and variables that characterize generator and storage subsystems
before performing downstream operations such as dispatch extraction
or cost evaluation.

Description
-----------
Model verification plays a crucial role in ensuring robustness
and error prevention within modular optimization frameworks.
These functions perform *non-invasive integrity checks* by verifying
the existence of predefined attributes in the model object
without altering its state.

They are used extensively throughout post-processing routines
(e.g., :mod:`Dataframes`) to guarantee that operations are executed
only if the corresponding subsystem is present and properly defined.

Functions
---------
has_generator_model(model)
    Verifies whether the provided model instance contains all
    mandatory components of a generator subsystem, including sets
    and decision variables for generation, commitment, and investment.

has_storage_model(model)
    Checks whether the model instance includes all necessary
    structures to represent an energy storage subsystem,
    including energy balance, charge/discharge, and state-of-charge
    variables.

Usage Example
-------------
>>> from MDI.ModelCheck import has_generator_model, has_storage_model
>>> from pyomo.environ import ConcreteModel
>>> m = ConcreteModel()
>>> has_generator_model(m)
False
>>> # After adding generator sets and variables
>>> has_generator_model(m)
True

Notes
-----
- Designed for structural validation only (no numerical evaluation).  
- Returns boolean values indicating model completeness.  
- Compatible with **Pyomo ≥ 6.6.0**.  
- Used internally by data extraction, reporting, and consistency
  modules across the MDI framework.

References
----------
[1] CEPEL, DESSEM. Manual de Metodologia, 2023  
[2] Unsihuay Vila, C. Introdução aos Sistemas de Energia Elétrica, Lecture Notes, EELT7030/UFPR, 2023.
"""

from pyomo.environ import ConcreteModel


def has_generator_model(model: ConcreteModel) -> bool:
    """
    Check whether the given Pyomo model contains all components of a geerator subsystem.

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

    """

    required = [
        'GU', 'T', 'P',
        'gen_P', 'gen_c_op', 'gen_c_inv',
        'gen_y', 'gen_x'
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
    """

    required = [
        'T', 'SU', 'storage_dis', 'storage_ch', 'storage_E'
    ]
    if all(hasattr(model, attr) for attr in required):
        return True
    return False
