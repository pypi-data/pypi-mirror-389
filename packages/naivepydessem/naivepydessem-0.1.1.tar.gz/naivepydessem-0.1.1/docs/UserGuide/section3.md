## **3. Model Architecture**

### **3.1 Overview**

The **NaivePyDESSEM** package follows a layered architecture that mirrors the hierarchical structure of the Brazilian energy models (*MDI*, *DECOMP*, and *DESSEM*).  
Its design ensures separation between **data ingestion**, **mathematical formulation**, **solver execution**, and **post-processing**, allowing flexible experimentation, teaching, and research on hydrothermal coordination.

The architecture is implemented in **Python 3.11+**, following object-oriented principles and extensive documentation through docstrings compliant with the *NumPy* style guide.

---

### **3.2 Package Hierarchy**

The repository is organized into five principal namespaces:

```
NaivePyDESSEM/
│
├── cli/              # Command-line interface and execution routines
├── core/             # Mathematical models, optimization logic, and solvers
├── data/             # Input parsers, YAML/CSV readers, and preprocessing
├── utils/            # Auxiliary functions (logging, error handling, plotting)
└── tests/            # Unit tests and validation scripts
```

Each module is designed for **independent testing** and **incremental execution**, with configuration handled via YAML files and direct class instantiation.

---

### **3.3 Core Components**

#### **3.3.1 The Solver Core**

At the heart of the package lies the `Solver` class (in `core.solver.py`), responsible for building and executing the optimization problem.  
It interfaces with *Pyomo* to translate model components into a standard MILP form.

**Main attributes:**

| Attribute | Description |
|------------|--------------|
| `model` | Pyomo model instance |
| `parameters` | Dictionary of runtime configuration values |
| `results` | Pyomo results object after solving |
| `solver_name` | Selected MILP solver (e.g., GLPK, CBC, or Gurobi) |

**Execution flow:**

1. Parse configuration (`YAMLLoader`);  
2. Instantiate Pyomo model and variables;  
3. Add operational, hydraulic, and network constraints;  
4. Solve using external MILP solver;  
5. Export solution and derived quantities (flows, generation, CMO).

---

#### **3.3.2 YAML Input System**

All execution parameters, such as system topology, demand series, initial reservoir levels, and solver preferences, are defined in a YAML configuration file parsed by the `YAMLLoader` class.

```yaml
system:
  name: "SE_CO_Brazil"
  horizon: 168   # hours
  timestep: 1h

solver:
  name: "gurobi"
  mipgap: 0.01

reservoirs:
  - name: "ITAIPU"
    v0: 0.85
    vmax: 1.0
```

This declarative structure allows users to quickly reproduce experiments without modifying the code base.

---

#### **3.3.3 Data Structures**

The `data` module converts YAML and CSV inputs into *pandas* `DataFrame` objects for direct use by the solver.  
Key loaders include:

- **`load_hydro_data()`** – parses reservoir characteristics and inflows;  
- **`load_thermal_data()`** – reads thermal generation data and fuel costs;  
- **`load_demand_series()`** – constructs chronological demand curves;  
- **`build_network_topology()`** – defines transmission nodes and limits.

All datasets are automatically validated to ensure temporal consistency and completeness before model construction.

---

#### **3.3.4 Optimization Model**

The optimization model is constructed dynamically using *Pyomo*.  
Its structure follows the canonical DESSEM formulation, expressed as:

\[
\min \; \sum_{t} \left( C_T g_t + C_S s_t + C_D \text{def}_t \right)
\]

subject to:

\[
\begin{aligned}
& \text{Energy balance:} && g_t + h_t + d_t = D_t, \\
& \text{Hydraulic continuity:} && v_t = v_{t-1} + q_t - (turb_t + vert_t), \\
& \text{Network flow:} && f_{ij,t} = B_{ij} (\theta_i - \theta_j), \\
& \text{Generation limits:} && 0 \leq g_t \leq G^{\max}.
\end{aligned}
\]

Pyomo’s modularity allows direct replacement of model components, making NaivePyDESSEM suitable for academic exploration of alternative formulations.

---

### **3.4 Command-Line Interface**

The **CLI module** provides a single entry point for all simulations, enabling configuration loading, solver execution, and report generation through a structured set of subcommands.

**Example usage:**

```bash
naivepydessem run --config input/dessem_case.yaml --solver gurobi
```

**Available commands:**

| Command | Description |
|----------|--------------|
| `run` | Execute the full DESSEM optimization cycle |
| `plot` | Generate time-series plots (generation, reservoir volume, CMO) |
| `summary` | Export aggregated statistics to CSV |
| `validate` | Run unit tests and configuration checks |

---

### **3.5 Visualization and Reporting**

The `PlotSeries` class (in `utils/plot_series.py`) generates analytical visualizations of simulation results:

- Hydro and thermal generation by time step;  
- Reservoir trajectories;  
- Marginal operation costs (CMO) by submarket;  
- Power flow in key interconnections.

All plots are generated with *Matplotlib* and may be exported in PNG, SVG, or PDF formats for publication.

```python
from naivepydessem.utils import PlotSeries

PlotSeries.plot_generation(results)
PlotSeries.plot_reservoirs(results)
```

---

### **3.6 Testing Framework**

Unit testing is implemented in the `tests/` directory using *pytest*.  
The suite covers input parsing, model construction, solver stability, and consistency between analytical and numerical outputs.

**Example test:**

```python
def test_hydro_balance():
    results = run_case("itaipu_case.yaml")
    assert abs(results.reservoirs["ITAIPU"].v_t[-1] - expected_value) < 1e-3
```

Continuous integration support (e.g., GitHub Actions) can be added by invoking:

```bash
pytest --maxfail=1 --disable-warnings -q
```

---

### **3.7 Integration Flow**

The high-level execution flow of NaivePyDESSEM can be summarized as follows:

```
   +----------------------+
   |   YAML Configuration |
   +----------+-----------+
              |
              v
   +----------------------+
   |   Data Preprocessing |
   +----------+-----------+
              |
              v
   +----------------------+
   |   Pyomo Model Build  |
   +----------+-----------+
              |
              v
   +----------------------+
   |   MILP Solver Call   |
   +----------+-----------+
              |
              v
   +----------------------+
   |  Postprocessing &    |
   |  Visualization       |
   +----------------------+
```

This sequential pipeline ensures transparency, reproducibility, and traceability across all modeling stages.

---

### **3.8 Summary**

In essence, **NaivePyDESSEM** encapsulates the complete workflow of a short-term hydrothermal dispatch model, balancing academic clarity with computational rigor.  
Its modular design facilitates integration with upstream models (*MDI*, *DECOMP*) and downstream visualization or market analysis tools, making it a valuable platform for research, teaching, and prototype development in energy systems optimization.
