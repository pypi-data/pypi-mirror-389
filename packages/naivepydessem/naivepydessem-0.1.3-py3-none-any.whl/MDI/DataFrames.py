"""
Dataframes Module
=================
EELT7030 — Operation and Expansion Planning of Electric Power Systems  
Federal University of Paraná (UFPR)

Author
------
Augusto Mathias Adams <augusto.adams@ufpr.br>

Summary
-------
The **Dataframes** module provides structured routines for converting
optimization results from **Pyomo** models into analytical **pandas DataFrames**.
It enables direct visualization and statistical evaluation of dispatch,
cost, and marginal values from the **MDI (Modular Decision Infrastructure)** framework.

Description
-----------
This module acts as a post-processing interface between the optimization
model and external data analysis tools. It extracts primal and dual
values from the **Pyomo ConcreteModel**, computes derived indicators
(e.g., marginal operation cost), and organizes the results into tabular
form suitable for export to spreadsheets, CSV, or visualization software.

Each function contributes a layer of semantic enrichment to the resulting
dataset, corresponding to a subsystem (generation, storage, cost structure).

Functions
---------
add_generator_dispatch_to_dataframe(df, model)
    Extracts generator dispatch, commitment, and investment variables
    from the model and appends them to the provided DataFrame.

add_storage_dispatch_to_dataframe(df, model)
    Extracts storage charge/discharge behavior, state of charge, and
    investment decisions from the model and appends them to the DataFrame.

add_cost_to_dataframe(df, model)
    Computes total operating and investment costs, as well as marginal
    prices such as CMO (Custo Marginal de Operação) and CME (Custo Marginal
    de Expansão). Adds these metrics as new columns to the DataFrame.

build_dispatch_dataframe(model)
    High-level routine that sequentially aggregates generator, storage,
    and cost data into a single unified DataFrame.

Notes
-----
- Requires **pandas ≥ 2.0.0** and **Pyomo ≥ 6.6.0**.  
- All numerical values are retrieved through `pyomo.environ.value()`.  
- Dual values must be available (i.e., model must have been solved
  with a solver that supports dual variable extraction).  
- The notation `CMO` and `CME` corresponds respectively to:
  - *Custo Marginal de Operação* — derived from balance constraints.
  - *Custo Marginal de Expansão* — derived from adequacy constraints.  
- Column naming conventions are consistent with the MDI’s export structure
  for integration with visualization dashboards and academic reports.

References
----------
[1] CEPEL, DESSEM. Manual de Metodologia, 2023  
[2] Unsihuay Vila, C. Introdução aos Sistemas de Energia Elétrica, Lecture Notes, EELT7030/UFPR, 2023.
"""

import pandas as pd
from pyomo.environ import ConcreteModel, value
from .ModelCheck import *

from copy import deepcopy
from pyomo.environ import ConcreteModel, SolverFactory, value

def add_generator_dispatch_to_dataframe(df: pd.DataFrame,
                                        model: ConcreteModel) -> pd.DataFrame:
    """
    Append generator dispatch results to a pandas DataFrame.

    This function extracts the turbined flow, storage volume, hydropower
    generation, and spillage from a Pyomo model and appends them to the
    given DataFrame, one column per unit and variable.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to which the results will be appended. It may be empty.
    model : ConcreteModel
        A Pyomo model instance containing hydropower variables.

    Returns
    -------
    pd.DataFrame
        The updated DataFrame including hydropower dispatch results.
    """

    if has_generator_model(model):
        T = list(model.T)
        G = list(model.GU)
        P = list(model.P)

        for g in G:
            for p in P:
                ps = r'{' + p + r'}'
                df[f'G_{{{{g_{g}}}{{p_{ps}}}}}'] = [
                    value(model.gen_P[g, t, p]) for t in T]
            df[f'Y_{{g_{g}}}'] = [value(model.gen_y[g, t]) for t in T]
            df[f'X_{{g_{g}}}'] = [value(model.gen_x[g, t]) for t in T]

    return df


def add_storage_dispatch_to_dataframe(df: pd.DataFrame,
                                      model: ConcreteModel) -> pd.DataFrame:
    """
    Append storage dispatch results to a pandas DataFrame.

    This function extracts charging, discharging, net output,
    and state of charge (SoC) values from the Pyomo model and
    adds them as columns to the DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to which the results will be appended.
    model : ConcreteModel
        A Pyomo model instance containing storage unit variables.

    Returns
    -------
    pd.DataFrame
        The updated DataFrame including storage dispatch results.
    """

    if has_storage_model(model):
        T = list(model.T)
        S = list(model.SU)
        P = list(model.P)
        for s in S:
            for p in P:
                ps = r'{' + p + r'}'
                df[f'D_{{{{s_{s}}}{{p_{ps}}}}}'] = [
                    value(model.storage_dis[s, t, p] * model.level_hours[p]) for t in T]
                df[f'C_{{{{s_{s}}}{{p_{ps}}}}}'] = [
                    -value(model.storage_ch[s, t, p] * model.level_hours[p]) for t in T]
                df[f'G_{{{{s_{s}}}{{p_{ps}}}}}'] = [
                    value(model.storage_dis[s, t, p] - model.storage_ch[s, t, p]) for t in T]
                df[f'E_{{{{s_{s}}}{{p_{ps}}}}}'] = [
                    value(model.storage_E[s, t, p]) for t in T]
            df[f'Y_{{b_{s}}}'] = [value(model.storage_y[s, t]) for t in T]
            df[f'X_{{b_{s}}}'] = [value(model.storage_x[s, t]) for t in T]

    return df


def add_cost_to_dataframe(df: pd.DataFrame,
                          model: ConcreteModel) -> pd.DataFrame:
    """
    Append cost components and total demand/deficit to the DataFrame.

    This function computes and appends the variable generation cost,
    startup cost, deficit cost, and total cost per time period.
    It also includes total generation, demand, and deficit series.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to which cost components will be appended.
    model : ConcreteModel
        A Pyomo model instance with thermal and system-wide cost variables.

    Returns
    -------
    pd.DataFrame
        The updated DataFrame including cost components and energy balance data.
    """
    def compute_average_CMO(model):
        """Retorna um dicionário com o CMO médio ponderado por patamar."""
        avg_CMO = {}
        total_hours = sum(model.level_hours[p] for p in model.P)

        for t in model.T:
            weighted_sum = sum(value(model.dual[model.Balance[t, p]] * model.level_hours[p]) for p in model.P)
            avg_CMO[t] = weighted_sum / total_hours

        return avg_CMO
    
    def compute_average_CME(model):
        avg_CME = {}
        avg_CMO = compute_average_CMO(model)
        total_hours = sum(model.level_hours[p] for p in model.P)

        for t in model.T:
            weighted_sum = sum(value(model.dual[model.Adequacy[t, p]]) for p in model.P)
            avg_CME[t] = avg_CMO[t] + weighted_sum / total_hours

        return avg_CME
    
    T = list(model.T)

    P = list(model.P)

    generator_generation = {p: [0.0] * len(T) for p in P}

    storage_generation = {p: [0.0] * len(T) for p in P}

    if has_generator_model(model):
        for p in P:
            generator_generation[p] = [sum(value(model.gen_P[g, t, p])
                                           for g in model.GU) for t in model.T]

    if has_storage_model(model):
        for p in P:
            storage_generation[p] = [sum(value(model.storage_dis[s, t, p]
                                               - model.storage_ch[s, t, p])
                                         for s in model.SU) for t in model.T]
    # Totais por período e patamar

    for p in P:

        ps = r'{' + p + r'}'
        df[f'Ge_{{{{Total}}_{ps}}}'] = [x + y for x, y in zip(generator_generation[p],
                                                         storage_generation[p])]

        df[f'Demand_{ps}'] = [value(model.d[p][t-1]) for t in T]

    cost_var, cost_inv = [], []
    # Custos por período (se possível)
    G = list(model.GU)
    for t in T:
        cost_var_t = 0
        cost_inv_t = 0
        if has_storage_model(model):
            cost_var_t += value(sum(
                # Custo de operação (por energia movimentada)
                model.level_hours[p] * model.storage_c_op[s] * (
                    model.storage_ch[s, t, p] + model.storage_dis[s, t, p]
                )
                for s in model.SU for p in model.P)
            )
            if model.parcel_investment:
                cost_inv_t += value(sum(model.storage_c_inv[s]
                                    * model.storage_x[s, t] for s in model.SU))
            else:
                cost_inv_t += value(sum(model.storage_c_inv[s]
                                    * model.storage_y[s, t] for s in model.SU))
        if has_generator_model(model):
            cost_var_t += value(sum(
                model.level_hours[p] * model.gen_c_op[g] * model.gen_P[g, t, p]
                for g in model.GU for p in model.P))

            if model.parcel_investment:
                cost_inv_t += value(sum(model.gen_c_inv[g] * model.gen_x[g, t] for g in model.GU))
            else:
                cost_inv_t += value(sum(model.gen_c_inv[g] * model.gen_y[g, t] for g in model.GU))
        cost_var.append(cost_var_t)
        cost_inv.append(cost_inv_t)
    df['Cost_{var}'] = cost_var
    df['Cost_{inv}'] = cost_inv
    df['CMO'] = compute_average_CMO(model=model)
    df['CME'] = compute_average_CME(model=model)

    return df


def build_dispatch_dataframe(model: ConcreteModel) -> pd.DataFrame:
    """
    Build a full dispatch DataFrame with generation, cost, and balance data.

    This function aggregates the dispatch results from all subsystems
    (hydropower, thermal, renewable, storage) along with cost components
    into a single structured pandas DataFrame.

    Parameters
    ----------
    model : ConcreteModel
        A Pyomo model instance containing subsystem variables and time horizon.

    Returns
    -------
    pd.DataFrame
        A DataFrame with all relevant dispatch results and economic metrics.
    """

    df = pd.DataFrame()
    df = add_storage_dispatch_to_dataframe(df, model)
    df = add_generator_dispatch_to_dataframe(df, model)
    df = add_cost_to_dataframe(df, model)
    return df
