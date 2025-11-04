"""
Builder Module
==============
EELT7030 — Operation and Expansion Planning of Electric Power Systems  
Federal University of Paraná (UFPR)

Author
------
Augusto Mathias Adams <augusto.adams@ufpr.br>

Summary
-------
The **Builder** module provides the high-level orchestration routines for constructing
a complete **MDI (Modular Decision Infrastructure)** system model. It integrates
the Generator and Storage subsystems, validates YAML input data, and assembles
the optimization problem by defining constraints, objectives, and auxiliary
expressions using **Pyomo**.

Description
-----------
This module serves as the *entry point* for model instantiation from a YAML specification,
including validation of meta parameters, generation and storage data, and global
power balance. It encapsulates all system-level expressions such as:

- **Adequacy Constraint** — ensures total available capacity meets mean demand.  
- **Power Balance** — enforces node-level balance between demand and generation.  
- **Objective Function** — minimizes total system costs including generation, storage, and deficit penalties.

It also handles automatic conversion of YAML datasets into `GeneratorData` and
`StorageData` dataclasses, ensuring consistency of units, bounds, and efficiency parameters.

Functions
---------
_validate_meta(meta)
    Performs structural and numerical checks on the metadata section.
_validate_demand(d, T)
    Validates demand profiles (currently placeholder).
_validate_storage(storage)
    Ensures energy capacity and efficiency values are within valid physical limits.
_validate_generator(generators)
    Validates generator attributes and required fields.

_mk_generator_data(root)
    Factory for creating a `GeneratorData` instance from YAML input.
_mk_storage_data(root)
    Factory for creating a `StorageData` instance from YAML input.

compute_mean_demand(m, yaml_data)
    Computes weighted mean demand over all load levels and attaches it to the model.
add_system_adequacy_expression(m)
    Adds a system adequacy constraint based on installed capacity.

build_balance_and_objective_from_yaml(model, yaml_data)
    Constructs balance constraints and total cost objective function.

build_model_from_file(path)
    High-level entry point: loads YAML, validates, builds subsystems,
    and returns a complete `ConcreteModel`.

Notes
-----
- Requires **Pyomo ≥ 6.6.0**.  
- YAML input structure must contain sections: `meta`, `generator`, `storage`.  
- All time indices (`t`) are assumed to start at 1 (Pyomo convention).  
- The Builder supports both investment and operational formulations.

References
----------
[1] CEPEL, DESSEM. Manual de Metodologia, 2023  
[2] Unsihuay Vila, C. Introdução aos Sistemas de Energia Elétrica, Lecture Notes, EELT7030/UFPR, 2023.  
"""

from __future__ import annotations

import json
import numpy as np
from typing import Any, Dict, List, Tuple
from pyomo.environ import ConcreteModel, Objective, Constraint, minimize

from MDI.Generator.GeneratorDataTypes import GeneratorData, GeneratorUnit
from MDI.Generator.GeneratorBuilder import add_generator_problem
from MDI.Generator.GeneratorEquations import (
    add_generator_cost_expression,
    add_generator_balance_expression,
    add_generator_capacity_expression
)

from MDI.Storage.StorageDataTypes import StorageData, StorageUnit
from MDI.Storage.StorageBuilder import add_storage_problem
from MDI.Storage.StorageEquations import (
    add_storage_cost_expression,
    add_storage_balance_expression,
    add_storage_capacity_expression
)

from .YAMLLoader import yaml_loader

# ============================================================================
# Validators (lightweight sanity checks)
# ============================================================================


def _validate_meta(meta: Dict[str, Any]) -> None:
   
    horizon = meta.get("horizon")
    if not isinstance(horizon, int) or horizon <= 0:
        raise ValueError("meta.horizon must be a positive integer.")


def _validate_demand(d: Dict[Any, Any], T: int) -> None:
   
    pass



def _validate_storage(storage: Dict[str, Any]) -> None:
   
    units = storage.get("units", {})
    for name, u in units.items():
        if not (u["Emin"] <= u["Eini"] <= u["Emax"]):
            raise ValueError(
                f"storage.units[{name}] must satisfy Emin <= Eini <= Emax.")
        for k in ("eta_c", "eta_d"):
            if not (0.0 < u[k] <= 1.0):
                raise ValueError(
                    f"storage.units[{name}].{k} must be in (0, 1].")


            
def _validate_generator(generators: Dict[str, Any]) -> None:

    required = [
        'GU', 'T', 'P',
        'gen_P', 'gen_c_op', 'gen_c_inv',
        'gen_y', 'gen_x'
    ]

    units = generators.get("units", {})
    for name, u in units.items():
        if all(hasattr(u, attr) for attr in required):
            raise ValueError(
                    f"generator.units[{name}] is invalid.")

# ============================================================================
# Dataclass factories
# ============================================================================

def _mk_generator_data(root: Dict[str, Any]) -> GeneratorData:
   
    meta = root["meta"]
    generators = root["generator"]
    # demanda “global” veio em root["demand"]
    H = meta["horizon"]
    level_hours = meta["level_hours"]
    demand = meta["demand"]
    units = {}
    for name, u in generators["units"].items():
        units[name] = GeneratorUnit(
            name=name,
            state=int(u["state"]),
            c_op=float(u["c_op"]),
            c_inv=float(u["c_inv"]),
            p_max=float(u["p_max"]),
            include_cap=bool(u["include_cap"])
        )
    return GeneratorData(
        horizon=H,
        demand=demand,
        units=units,
        level_hours=level_hours
    )


def _mk_storage_data(root: Dict[str, Any]) -> StorageData:
    
    storage = root["storage"]
    meta = root["meta"]
    H = meta["horizon"]
    level_hours = meta["level_hours"]
    delta_t = float(storage.get("delta_t", meta.get("delta_t", 1.0)))
    demand = meta["demand"]
    units = {}
    for name, u in storage["units"].items():
        units[name] = StorageUnit(
            name=name,            
            state=int(u["state"]),
            c_op=float(u["c_op"]),
            c_inv=float(u["c_inv"]),
            Emin=float(u["Emin"]),
            Emax=float(u["Emax"]),
            Eini=float(u["Eini"]),
            Pch_max=float(u["Pch_max"]),
            Pdis_max=float(u["Pdis_max"]),
            eta_c=float(u["eta_c"]),
            eta_d=float(u["eta_d"]),
        )
    return StorageData(
        horizon=H,
        demand=demand,
        units=units,
        delta_t=delta_t,
        level_hours=level_hours
    )

# ============================================================================
# Master entry point
# ============================================================================
def build_balance_and_objective_from_yaml(model: ConcreteModel, yaml_data: Dict[str, Any]) -> ConcreteModel:
    
    # --------------------------
    # ADEQUACY CONSTRAINT
    # --------------------------
    def capacity_balance_rule(m, t, p):
        capacity_terms: List[Any] = []
        
        
        if 'generator' in yaml_data:
            add_generator_capacity_expression(m, t, p, capacity_terms)
        if 'storage' in yaml_data:
            add_storage_capacity_expression(m, t, p, capacity_terms)

        idx = t-1
        return sum(capacity_terms) >= model.d[p][idx]

    model.Adequacy = Constraint(model.T, model.P, rule=capacity_balance_rule)
    
    # --------------------------
    # BALANCE CONSTRAINT
    # --------------------------
    def power_balance_rule(m, t, p):
        balance_terms: List[Any] = []
        if 'generator' in yaml_data:
            add_generator_balance_expression(m, t, p, balance_terms)
        if 'storage' in yaml_data:
            add_storage_balance_expression(m, t, p, balance_terms)

        # Final balance expression
        return sum(balance_terms) == m.d[p][t-1]

    model.Balance = Constraint(model.T, model.P, rule=power_balance_rule)

    # --------------------------
    # OBJECTIVE FUNCTION
    # --------------------------
    cost_terms: List[Any] = []

    if 'generator' in yaml_data:
        add_generator_cost_expression(model, cost_terms)
    if 'storage' in yaml_data:
        add_storage_cost_expression(model, cost_terms)
    
    model.OBJ = Objective(expr=sum(cost_terms), sense=minimize)

    return model


def build_model_from_file(path: str) -> Tuple[ConcreteModel, Dict]:
   
    root = yaml_loader(path)
    level_precedence = root["meta"]["level_precedence"]
    parcel_investment = bool(root["meta"]["parcel_investment"])

    if "meta" not in root:
        raise ValueError("File must contain 'meta' sections.")

    m = ConcreteModel()

    m.level_precedence = level_precedence
    m.parcel_investment = parcel_investment

    # Basic validations
    _validate_meta(root["meta"])
    T = int(root["meta"]["horizon"])
    _validate_demand(root["meta"]["demand"], T)
    has_valid_units = False
    if "generator" in root and root["generator"] is not None:
        _validate_generator(root["generator"])
        generator_data = _mk_generator_data(root)
        m = add_generator_problem(m=m,
                              data=generator_data,
                              include_objective=False)
        has_valid_units = True

    if "storage" in root and root["storage"] is not None:
        _validate_storage(root["storage"])
        storage_data = _mk_storage_data(root)
        m = add_storage_problem(m=m,
                                data=storage_data,
                                include_objective=False)
        has_valid_units = True
    if not has_valid_units:
        raise ValueError("No buildable sections found. Provide at least one of "
                         "{generators, storage}.")
    m = build_balance_and_objective_from_yaml(m, root)

    return m, root
