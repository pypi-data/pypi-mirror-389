"""
EELT 7030 — Operation and Expansion Planning of Electric Power Systems  
Federal University of Paraná (UFPR)

Utility: Post-Solve Dispatch Summary and Cost Reports

Author
------
Augusto Mathias Adams <augusto.adams@ufpr.br>

Description
-----------
This module contains functions to summarize dispatch results after solving
a Pyomo-based optimization problem. It prints total generation, cost breakdowns,
and unit-level summaries for hydropower, thermal, renewable, and storage technologies.

Features:
- Total cost, demand, deficit and thermal cost components.
- Per-unit dispatch summaries with color-enhanced output (via `colorama`).
- Compatible with modular NaivePyDESSEM subsystem architecture.

References
----------
[1] CEPEL, DESSEM. Manual de Metodologia, 2023  
[2] Unsihuay Vila, C. Introdução aos Sistemas de Energia Elétrica, Lecture Notes, EELT7030/UFPR, 2023.
"""

from pyomo.environ import ConcreteModel, value
from typing import Any, Tuple, Dict
from colorama import Fore, Style
from .Formatters import format_brl
from .ModelCheck import *


def __compute_total_generation(model: ConcreteModel) -> float:
    """
    Compute total system generation across all technologies.

    Parameters
    ----------
    model : ConcreteModel
        Solved Pyomo model instance.

    Returns
    -------
    float
        Total generated energy [MWh] across hydro, thermal, renewable, and storage.
    """
    total_generation = 0.0

    if has_generator_model(model):
        total_generation += sum(
            value(model.level_hours[p] * model.gen_P[g, t, p])
            for g in model.GU for t in model.T for p in model.P
        )

    if has_storage_model(model):
        total_generation += sum(value(
            model.level_hours[p] * (
                model.storage_dis[s, t, p] - model.storage_ch[s, t, p]
            ))
            for s in model.SU for t in model.T for p in model.P
        )

    return total_generation


def __compute_investment_cost(model: ConcreteModel) -> float:
    """
    Compute total investment cost.

    Parameters
    ----------
    model : ConcreteModel
        Solved Pyomo model.

    Returns
    -------
    float
        Total investment[$] for building units (geerators and storages).
    """
    total_investment = 0.0
    if has_generator_model(model):
        if model.parcel_investment:
            total_investment += sum(value(model.gen_c_inv[g] * model.gen_x[g, t])
                                    for g in model.GU for t in model.T)
        else:
            total_investment += sum(value(model.gen_c_inv[g] * model.gen_y[g, t])
                                    for g in model.GU for t in model.T)
    if has_storage_model(model):
        if model.parcel_investment:
            total_investment += sum(value(
                model.storage_c_inv[s] * model.storage_x[s, t]) for s in model.SU for t in model.T)
        else:
            total_investment += sum(value(
                model.storage_c_inv[s] * model.storage_y[s, t]) for s in model.SU for t in model.T)
    return total_investment


def __compute_operational_cost(model: ConcreteModel) -> float:
    """
    Compute total operational cost.

    Parameters
    ----------
    model : ConcreteModel
        Solved Pyomo model.

    Returns
    -------
    float
        Total cost[$] for operating units (geerators and storages).
    """
    total_op_cost = 0.0
    if has_generator_model(model):
        total_op_cost += sum(
            value(model.level_hours[p] *
                  model.gen_c_op[g] * model.gen_P[g, t, p])
            for g in model.GU for t in model.T for p in model.P
        )
    if has_storage_model(model):
        total_op_cost += sum(
            value(model.level_hours[p] * model.storage_c_op[s] * (
                model.storage_ch[s, t, p] + model.storage_dis[s, t, p]
            ))
            for s in model.SU for t in model.T for p in model.P
        )
    return total_op_cost


def dispatch_summary(model: ConcreteModel) -> None:
    """
    Print a complete dispatch and cost summary including:
    - Total generation and demand.
    - Deficit and its monetary cost.
    - Thermal cost breakdown (start-up, generation).
    - Overall total cost from the model objective.

    Parameters
    ----------
    model : ConcreteModel
        Solved Pyomo model instance.
    """
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}==================== EXPANSION SUMMARY ===================={Style.RESET_ALL}")
    total_generation = __compute_total_generation(model)
    print(f"  {Fore.CYAN}Total Generation{Style.RESET_ALL}: {Fore.RED}{total_generation:.2f} MWh")
    demand = sum(value(model.level_hours[p] * model.d[p][t-1])
                 for t in model.T for p in model.P)
    # print(f"  {Fore.CYAN}Total Generation{Style.RESET_ALL}: {Fore.RED}{demand:.2f} MWh")
    print(
        f"  {Fore.CYAN}Total Demand{Style.RESET_ALL}: {Fore.RED}{demand:.2f} MWh")

    print(
        f"  {Fore.CYAN}Total Investment Cost{Style.RESET_ALL}: {Fore.RED} $ {format_brl(__compute_investment_cost(model))}")

    print(
        f"  {Fore.CYAN}Total Operational Cost{Style.RESET_ALL}: {Fore.RED} $ {format_brl(__compute_operational_cost(model))}")


def generator_dispatch_summary(model: ConcreteModel) -> None:
    """
    Print unit-level generator units generation summary in MWh.

    Parameters
    ----------
    model : ConcreteModel
        Solved Pyomo model with generator subsystem.
    """
    if has_generator_model(model):
        print(f"{Fore.YELLOW}Generator Units Generation:{Style.RESET_ALL}")
        for g in model.GU:
            dispatch = sum(value(
                model.level_hours[p] * model.gen_P[g, t, p]) for t in model.T for p in model.P)
            print(
                f"  {Fore.BLUE}{g}{Style.RESET_ALL}: {Fore.RED}{dispatch:.2f} MWh")


def storage_dispatch_summary(model: ConcreteModel) -> None:
    """
    Print unit-level storage discharge summary in MWh.

    Parameters
    ----------
    model : ConcreteModel
        Solved Pyomo model with storage subsystem.
    """
    if has_storage_model(model):
        print(f"\n{Fore.YELLOW}Storage Discharge:{Style.RESET_ALL}")
        for s in model.SU:
            dispatch = sum(value(
                model.storage_dis[s, t, p] * model.level_hours[p]) for t in model.T for p in model.P)
            print(
                f"  {Fore.MAGENTA}{s}{Style.RESET_ALL}: {Fore.RED}{dispatch:.2f} MWh")
        print(f"\n{Fore.YELLOW}Storage Charge:{Style.RESET_ALL}")
        for s in model.SU:
            dispatch = sum(value(
                model.storage_ch[s, t, p] * model.level_hours[p]) for t in model.T for p in model.P)
            print(
                f"  {Fore.MAGENTA}{s}{Style.RESET_ALL}: {Fore.RED}{dispatch:.2f} MWh")
        print(f"\n{Fore.YELLOW}Storage Delta:{Style.RESET_ALL}")
        for s in model.SU:
            dispatch = sum(
                value((model.storage_dis[s, t, p] - model.storage_ch[s, t, p]) * model.level_hours[p]) for t in model.T for p in model.P)
            print(
                f"  {Fore.MAGENTA}{s}{Style.RESET_ALL}: {Fore.RED}{dispatch:.2f} MWh")
