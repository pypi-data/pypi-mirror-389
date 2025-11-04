# NaivePyDESSEM User Guide

## 1. Introduction

### Purpose and Scope

The **NaivePyDESSEM Project Suite** is a pedagogical framework designed to provide a transparent, modular, and fully reproducible environment for the study and experimentation of **power system operation and expansion planning**. The suite comprises three complementary packages — **NaivePyDESSEM**, **NaivePyDECOMP**, and **MDI** — which collectively simulate, analyze, and optimize short-term dispatch, medium-term operation, and data integration within the energy systems domain.

This User Guide is intended for researchers, graduate students, and professionals seeking to understand the internal logic, structure, and usage of the NaivePyDESSEM ecosystem. The document adopts a formal technical tone consistent with academic and professional documentation standards, offering detailed explanations of modeling principles, solver integration, data preparation, and output interpretation.

### Conceptual Foundations

The NaivePyDESSEM family mirrors the conceptual hierarchy established in the **CEPEL** models — *DESSEM* for short-term operation, *DECOMP* for medium-term optimization, and *NEWAVE* for long-term planning — while maintaining a simplified yet analytically rigorous structure suitable for academic research and classroom experimentation.

Each package is built atop the **Pyomo** optimization framework, leveraging its declarative modeling language to define decision variables, constraints, and objective functions for deterministic and stochastic optimization problems. The design emphasizes clarity of implementation, mathematical transparency, and reproducibility, allowing users to directly inspect, modify, and extend each model component.

### Target Audience

This guide addresses three primary user profiles:

1. **Students and Educators** – who require a didactic framework for demonstrating fundamental principles of energy systems operation and optimization.
2. **Researchers and Developers** – who seek a modular foundation for developing or benchmarking novel optimization methodologies, including stochastic, metaheuristic, or decomposition-based approaches.
3. **Industry Professionals** – who wish to experiment with open, interpretable models before transitioning to large-scale proprietary tools.

### System Requirements

To ensure optimal performance and reproducibility, the following environment is recommended:

* **Operating System:** Linux (preferred), macOS, or Windows 10/11.
* **Python Version:** 3.9 or higher.
* **Required Dependencies:** `pyomo`, `pandas`, `numpy`, `yaml`, `matplotlib`, and `mealpy` (for metaheuristic integration).
* **Optional Solvers:** `GLPK`, `CPLEX`, `Gurobi`, or `IPOPT`.

## 2. Installation Guide

The following instructions describe the complete setup procedure for **NaivePyDESSEM**, including environment initialization, package installation, and solver configuration.

---

### 1. Create and Activate a Virtual Environment

It is strongly recommended to install NaivePyDESSEM inside an isolated Python environment to ensure dependency consistency and avoid version conflicts.

```bash
# Create a virtual environment (Python ≥ 3.9 recommended)
virtalenv venv

# Activate the environment
# On Linux / macOS:
source venv/bin/activate

# On Windows (PowerShell):
venv\Scripts\activate
```

---

### 2. Install NaivePyDESSEM

#### Option A – From PyPI (recommended for most users)

```bash
pip install naivepydessem
```

#### Option B – From Source (HTTPS)

```bash
git clone https://github.com/superflanker/NaivePyDESSEM.git
cd NaivePyDESSEM
pip install -e .
```

#### Option C – From Source (SSH)

```bash
git clone git@github.com:superflanker/NaivePyDESSEM.git
cd NaivePyDESSEM
pip install -e .
```

---

### 3. Build Pyomo Extensions

NaivePyDESSEM automatically installs **Pyomo** as a dependency.  
However, certain solvers require Pyomo’s compiled extensions to be available.  
Execute the following command once after installation:

```bash
pyomo build-extensions
```

---

### 4. Install and Configure Optimization Solvers

NaivePyDESSEM relies on external solvers for mixed-integer linear programming (MILP) and nonlinear optimization.  
The following options are supported:

#### **IBM CPLEX**

1. Install IBM ILOG CPLEX Optimization Studio from:  
   [https://www.ibm.com/products/ilog-cplex-optimization-studio](https://www.ibm.com/products/ilog-cplex-optimization-studio)

2. Set the environment variable `CPLEX_HOME` (if not automatically configured).

3. Verify installation:
   ```bash
   cplex -version
   ```

---

#### **Gurobi**

1. Install the Gurobi Optimizer from:  
   [https://www.gurobi.com/downloads/](https://www.gurobi.com/downloads/)

2. Obtain an academic or trial license and activate it:
   ```bash
   grbgetkey <license-key>
   ```

3. Confirm installation:
   ```bash
   gurobi_cl --version
   ```

---

#### **SCIP**

1. Install SCIP Optimization Suite (open-source alternative):  
   [https://www.scipopt.org/](https://www.scipopt.org/)

2. Depending on your platform:
   ```bash
   # On Debian/Ubuntu
   sudo apt install scipopt

   # Or via conda (recommended)
   conda install -c conda-forge pyscipopt
   ```

3. Verify installation:
   ```bash
   scip --version
   ```

---

### 5. Validate the Environment

To confirm successful installation, open a Python session and run:

```python
import pyomo.environ as pyo
import naivepydessem

print("Pyomo version:", pyo.version.__version__)
print("NaivePyDESSEM successfully imported.")
```

If no errors occur, the environment is properly configured.

---

### 6. (Optional) Upgrade or Uninstall

To upgrade:
```bash
pip install --upgrade naivepydessem
```

To uninstall:
```bash
pip uninstall naivepydessem
```

---

✅ **Installation Cheatsheet**

| Component | Purpose | Installation |
|------------|----------|---------------|
| **Virtualenv** | Isolated environment | `virtualenv venv` |
| **Virtualenv Activation** | Isolated environment | `source venv/bin/activate` |
| **NaivePyDESSEM** | Core library | `pip install naivepydessem` |
| **Pyomo Extensions** | Solver interfaces | `pyomo build-extensions` |
| **Solvers (CPLEX, Gurobi, SCIP)** | Optimization engines | External installation required |

---

**Note:** Some solvers (e.g., CPLEX, Gurobi) require valid licenses.  
Ensure environment variables (e.g., `PATH`, `CPLEX_HOME`, `GUROBI_HOME`) are correctly configured before executing optimization models.

## 2. Problem Formulation and Mathematical Modeling

This chapter formalizes the mathematical structures that underpin each model, providing a unified notation and formulation style across planning horizons. Each model is expressed as a mixed-integer or linear optimization problem, with explicit definitions of sets, parameters, decision variables, objective functions, and constraints.

Each model represents a specific temporal and operational scope within the decision hierarchy of the **SIN (National Interconnected System)**:

- **DESSEM (Short-Term Hydrothermal Scheduling Model):**  
  Formulates the hourly dispatch problem with detailed operational constraints for hydro, thermal, renewable, and storage units. It employs mixed-integer linear programming (MILP) formulations to capture short-term dynamics, including reservoir balance, ramping, and startup/shutdown logic.

- **DECOMP (Medium-Term Hydrothermal Operation Model):**  
  Represents weekly scheduling decisions using stochastic dual dynamic programming (SDDP) or deterministic decompositions. It approximates the stochastic inflow process and optimizes hydrothermal coordination under energy balance constraints, accounting for the trade-off between hydraulic and thermal generation costs.

- **MDI (Long-Term Expansion Planning Model):**  
  Determines the optimal investment and operation plan for generation and storage over a multi-year horizon. It is formulated as a **Mixed-Integer Linear Programming (MILP)** problem, aiming to minimize total system cost while satisfying capacity adequacy, reliability, and environmental criteria.

In summary, these models together form a consistent multi-horizon optimization chain:

| Model | Horizon | Decision Type | Mathematical Nature | Main Objective |
|:------|:---------|:---------------|:--------------------|:----------------|
| **DESSEM** | Short-term (hours–days) | Operational dispatch | MILP | Minimize operating cost |
| **DECOMP** | Medium-term (weeks–months) | Operation planning | Linear or Stochastic DP | Optimize hydrothermal coordination |
| **MDI** | Long-term (years) | Expansion planning | MILP | Minimize investment + operation cost |

Each formulation in this chapter includes the complete definition of sets, parameters, decision variables, objective function, and constraints.  
The presentation follows a standardized mathematical notation to facilitate comparison and integration across planning horizons.


### Mathematical Modeling of DESSEM

#### Hydropower Plants

##### Sets and Indices
\[
\begin{aligned}
&\mathcal{T} = \{1,\dots,T\} && \text{(hourly periods)} \\
&\mathcal{H} = \{\text{UHE}_1, \dots, \text{UHE}_{n_h}\} && \text{(hydropower plants)} \\
&\mathcal{U}(h) \subseteq \mathcal{H} && \text{(set of upstream hydropower plants of $h$)}
\end{aligned}
\]

##### Parameters (Data)
\[
\begin{aligned}
&a_{h,t} && \text{natural inflow to plant $h$ in period $t$ (m$^3$/s)} \\
&d_t && \text{demand in period $t$ (MWh/h)} \\
&\zeta_{\text{vol}} && \text{volume–flow conversion factor (hm$^3$/h)} \Rightarrow \frac{3600}{10^6} \\
&\zeta && \text{hydraulic constant} \Rightarrow \frac{9.81}{1000} \text{ (MW per m$^3$/sm of head)} \\
&V_{{\min}_h},\,V_{{\max}_h} && \text{volume limits (hm$^3$)} \\
&Q_{{\min}_h},\,Q_{{\max}_h} && \text{turbined flow limits (m$^3$/s)} \\
&V_{{\text{ini}}_h} && \text{initial reservoir volume (hm$^3$)} \\
&V_{{\text{meta}}_h} && \text{target terminal volume (hm$^3$)} \\
&C_{{\text{def}}} && \text{unitary cost of deficit (\$/MWh)} \\
&\alpha_{h,k},\,\beta_{h,k},\,\gamma_{h,k} && \text{polynomial coefficients for $h_{\text{up}}$, $h_{\text{down}}$, $h_{\text{loss}}$} \\
&\rho_{h,k} && \text{polynomial coefficients of the specific productivity $\rho_h$}
\end{aligned}
\]

##### Decision Variables
\[
\begin{aligned}
&Q_{h,t} \ge 0 && \text{turbined flow (m$^3$/s)} \\
&S_{h,t} \ge 0 && \text{spillage (m$^3$/s)} \\
&V_{h,t} \ge 0 && \text{stored volume (hm$^3$)} \\
&G_{h,t} \ge 0 && \text{hydropower generation (MWh/h)} \\
&D_t \ge 0 && \text{energy deficit (MWh/h)}
\end{aligned}
\]

##### Hydraulic Polynomial Functions for Plant $h$
\[
\begin{aligned}
\rho(Q, H_{\text{net}}) 
&= \zeta \,\Big( 
\rho_0 + \rho_1 Q + \rho_2 H_{\text{net}} + \rho_3 Q H_{\text{net}} + \rho_4 Q^2 + \rho_5 H_{\text{net}}^2
\Big), \text{ (CEPEL, 2023)} \\[2mm]
h_{\text{up},h}(V) &= \sum_{k=0}^{K_a} \alpha_{h,k}\, V^k, \\[2mm]
h_{\text{down},h}(q) &= \sum_{k=0}^{K_b} \beta_{h,k}\, q^k, \\[2mm]
h_{\text{loss},h}(Q) &= \sum_{k=0}^{K_\gamma} \gamma_{h,k}\, Q^k.
\end{aligned}
\]

##### Hydropower Production Function (HPF)
\[
\begin{aligned}
H_{{\text{net}}_{h,t}} &= h_{\text{up},h}(V_{h,t})- h_{\text{down},h}(Q_{h,t}+S_{h,t}) - h_{\text{loss},h}(Q_{h,t}), \\[2mm]
G_{h,t} &= \zeta \, Q_{h,t}\, \rho_h(Q_{h,t}, H_{{\text{net}}_{h,t}})\, H_{{\text{net}}_{h,t}} \quad \textbf{(Exact HPF)}, \\[2mm]
G_{h,t} &= \zeta \mathrm{PE} H_{{\mathrm{net}}_{h,t}} Q_{h,t} \quad \textbf{(HPF with constant PE)}, \\[2mm]
G_{h,t} &= \mathrm{P}  Q_{h,t} \quad \textbf{(Linearized HPF)}.
\end{aligned}
\]

##### Total Instantaneous Inflow (Cascade without Delay)
\[
I_{h,t} = a_{h,t} + \sum_{u \in \mathcal{U}(h)} ( Q_{u,t} + S_{u,t} ), 
\quad \forall h\in\mathcal{H},\; \forall t\in\mathcal{T}.
\]

##### Constraints

###### Generation
\[
G_{h,t} = HPF(Q,V,S), \quad \forall h\in\mathcal{H},\, t\in\mathcal{T}.
\]

###### Reservoir Mass Balance
\[
\begin{aligned}
V_{h,1} &= V_{{\text{ini}}_h} + \zeta_{\text{vol}} ( I_{h,1} - Q_{h,1} - S_{h,1}), \\
V_{h,t} &= V_{h,t-1} + \zeta_{\text{vol}} ( I_{h,t} - Q_{h,t} - S_{h,t}),
\quad \forall t=2,\dots,T.
\end{aligned}
\]

###### Targets and Operational Limits
\[
\begin{aligned}
&V_{h,T} \ge V_{{\text{meta}}_h}, \\
&V_{{\min}_h} \le V_{h,t} \le V_{{\max}_h}, \\
&Q_{{\min}_h} \le Q_{h,t} \le Q_{{\max}_h}, \\
&S_{h,t},\, G_{h,t},\, D_t \ge 0.
\end{aligned}
\]

---

#### Thermal Power Plants

##### Sets and Indices
\[
\mathcal{T} = \{1,\dots,T\}, \quad
\mathcal{G} = \{\text{UTE}_1,\dots,\text{UTE}_{n_g}\}.
\]

##### Parameters
\[
\begin{aligned}
&d_t && \text{system demand (MW)} \\
&P_{{\min}_g},\, P_{{\max}_g} && \text{generation limits of plant $g$ (MW)} \text{ (CEPEL, 2023)} \\
&a_g,\, b_g,\, c_g && \text{thermal cost coefficients of plant $g$} \\
&SC_g && \text{startup cost of plant $g$} \\
&R U_g,\, R D_g && \text{ramp-up/ramp-down rates (MW per interval)} \\
&t_{{\uparrow}_g},\, t_{{\downarrow}_g} && \text{minimum up/down times (h)} \\
&C_{\text{def}} && \text{deficit penalty cost (R\$/MWh)} \\
&u_{g,0},\, p_{g,0} && \text{initial on/off status and generation (from initial status data)}
\end{aligned}
\]

##### Decision Variables
\[
p_{g,t}\ge 0,\quad u_{g,t}, y_{g,t}, w_{g,t}\in\{0,1\},\quad D_t\ge 0.
\]
(where $u$ = on, $y$ = startup, $w$ = shutdown.)

##### Constraints

###### Power Balance
\[
\sum_{g\in\mathcal{G}} p_{g,t} + D_t = d_t, \quad \forall t.
\]

###### Conditional Capacity
\[
P_{{\min}_g} u_{g,t} \le p_{g,t} \le P_{{\max}_g} u_{g,t}.
\]

###### Startup/Shutdown Logic
\[
u_{g,t} - u_{g,t-1} = y_{g,t} - w_{g,t}.
\]

###### Ramping Limits
\[
\begin{aligned}
p_{g,t} - p_{g,t-1} &\le RU_g + P_{{\max}_g} y_{g,t},\\
p_{g,t-1} - p_{g,t} &\le RD_g + P_{{\max}_g} w_{g,t}.
\end{aligned}
\]

###### Minimum Up/Down Time
\[
\begin{aligned}
\sum_{\tau=t-t^{\uparrow}_g+1}^{t} y_{g,\tau} &\le u_{g,t},\\
\sum_{\tau=t-t^{\downarrow}_g+1}^{t} w_{g,\tau} &\le 1-u_{g,t}.
\end{aligned}
\]

###### Consistent Initial Conditions
\[
p_{g,0}\in
\begin{cases}
[\,P_{{\min}_g},\,P_{{\max}_g}\,], & \text{if } u_{g,0}=1,\\
\{0\}, & \text{if } u_{g,0}=0.
\end{cases}
\]

---

#### Renewable Energies and Storage

##### Sets and Indices
\[
\mathcal{T} = \{1,\dots,T\},\quad
\mathcal{R} = \{1,\dots,R_{n_r}\},\quad
\mathcal{S} = \{1,\dots,S_{n_s}\}.
\]

##### Parameters
\[
\begin{aligned}
&\overline{g}_{r,t} && \text{exogenous renewable availability profile (MW avg)} \\
&\Delta t && \text{time step (typically 1 h)} \\
&E_{{\min}_s},\,E_{{\max}_s} && \text{energy storage limits (MWh)} \\
&E_{{\mathrm{ini}}_s} && \text{initial energy (MWh)} \\
&\overline{P}_{{\mathrm{ch}}_{s}},\,\overline{P}_{{\mathrm{dis}}_{s}} && \text{max charge/discharge power (MW)} \\
&\eta_{{\mathrm{c}}_{s}},\,\eta_{{\mathrm{d}}_{s}} && \text{charge and discharge efficiencies}
\end{aligned}
\]

##### Decision Variables
\[
\begin{aligned}
&g_{{\mathrm{ren}}_{r,t}} \ge 0 && \text{dispatched renewable generation (MW)} \\
&E_{s,t} \ge 0 && \text{stored energy (MWh)} \\
&P_{{\mathrm{ch}}_{s,t}},\,P_{{\mathrm{dis}}_{s,t}} \ge 0 && \text{charging/discharging power (MW)}
\end{aligned}
\]

##### Constraints

###### Renewable Generation — Availability Limit
\[
0 \le g_{{\mathrm{ren}}_{r,t}} \le \overline{g}_{r,t}, \quad \forall r,t.
\]

###### Storage — Energy Balance (SoC)
\[
\begin{aligned}
E_{s,1} &= E_{{\mathrm{ini}}_s} + \eta_{{\mathrm{c}}_{s}} P_{{\mathrm{ch}}_{s,1}} \Delta t - \frac{1}{\eta_{{\mathrm{d}}_{s}}} P_{{\mathrm{dis}}_{s,1}} \Delta t,\\
E_{s,t} &= E_{s,t-1} + \eta_{{\mathrm{c}}_{s}} P_{{\mathrm{ch}}_{s,t}} \Delta t - \frac{1}{\eta_{{\mathrm{d}}_{s}}} P_{{\mathrm{dis}}_{s,t}} \Delta t, \quad \forall t=2,\dots,T.
\end{aligned}
\]

###### Storage — State of Charge (SoC) Limits
\[
E_{{\min}_s} \le E_{s,t} \le E_{{\max}_s}.
\]

###### Storage — Power Limits
\[
\begin{aligned}
0 \le P_{{\mathrm{ch}}_{s,t}} \le \overline{P}_{{\mathrm{ch}}_{s}},\\
0 \le P_{{\mathrm{dis}}_{s,t}} \le \overline{P}_{{\mathrm{dis}}_{s}}.
\end{aligned}
\]

---

#### Objective Function

The hydrothermal dispatch problem is formulated as a minimization of total generation and deficit costs, including:
- Thermal generation costs;
- Deficit costs (represented by a thermal deficit unit with fixed cost, as per Unsihuay, 2023);
- Penalty for reservoir spillage.

$$
\begin{aligned}
\min Z =\; &\sum_{g\in\mathcal{G}}\sum_{t\in\mathcal{T}} c_g\,p_{g,t} \\
&+ 0.3\sum_{h\in\mathcal{H}}\sum_{t\in\mathcal{T}} S_{h,t} \\
&+ C_{def}\sum_{t\in\mathcal{T}} D_t
\end{aligned}
$$


---

#### Power Balance (Load Supply)

\[
\sum_{h \in \mathcal{H}} G_{h,t} +
\sum_{g \in \mathcal{G}} p_{g,t} +
\sum_{r \in \mathcal{R}} g_{{\mathrm{ren}}_{r,t}} +
\sum_{s \in \mathcal{S}} ( P_{{\mathrm{dis}}_{s,t}} - P_{{\mathrm{ch}}_{s,t}} ) +
D_t = d_t, \quad \forall t \in \mathcal{T}.
\]

### Mathematical Modeling of DECOMP

#### Hydropower Plants

##### Sets and Indices
\[
\begin{aligned}
&\mathcal{T} = \{1,\dots,T\} && \text{(hourly periods)} \\
&\mathcal{H} = \{\text{UHE}_1, \dots, \text{UHE}_{n_h}\} && \text{(hydropower plants)} \\
&\mathcal{U}(h) \subseteq \mathcal{H} && \text{(set of upstream hydropower plants of $h$)}
\end{aligned}
\]

##### Parameters (Data)
\[
\begin{aligned}
&a_{h,t} && \text{natural inflow to plant $h$ in period $t$ (m$^3$/s)} \\
&d_t && \text{demand in period $t$ (MWh/h)} \\
&V_{{\min}_h},\,V_{{\max}_h} && \text{storage limits (hm$^3$)} \\
&Q_{{\min}_h},\,Q_{{\max}_h} && \text{turbined flow limits (hm$^3$)} \\
&V_{{\text{ini}}_h} && \text{initial reservoir volume (hm$^3$)} \\
&V_{{\text{meta}}_h} && \text{target terminal volume (hm$^3$)} \\
&C_{{\text{def}}} && \text{unitary cost of deficit (\$/MWh)} 
\end{aligned}
\]

##### Decision Variables
\[
\begin{aligned}
&Q_{h,t} \ge 0 && \text{turbined flow (hm$^3$)} \\
&S_{h,t} \ge 0 && \text{spillage (m$^3$)} \\
&V_{h,t} \ge 0 && \text{stored volume (hm$^3$)} \\
&G_{h,t} \ge 0 && \text{hydropower generation (MWmed)} \\
&D_t \ge 0 && \text{energy deficit (MWh/h)}
\end{aligned}
\]

##### Hydropower Production Function (HPF)
$$
G_{h,t} = P\, Q_{h,t} \quad \textbf{(Linearized HPF)}
$$

##### Constraints

###### Total Instantaneous Inflow (Cascade without Delay)
$$
I_{h,t} = a_{h,t} + \sum_{u \in \mathcal{U}(h)} ( Q_{u,t} + S_{u,t} ), \quad \forall h \in \mathcal{H}, \; \forall t \in \mathcal{T}
$$

###### Reservoir Mass Balance
$$
V_{h,1} = V_{\text{ini}_h} + ( I_{h,1} - Q_{h,1} - S_{h,1} ), \quad \forall h, \; t = 1
$$
$$
V_{h,t} = V_{h,t-1} + ( I_{h,t} - Q_{h,t} - S_{h,t} ), \quad \forall h, \; t = 2,\dots,T
$$

---

#### Thermal Units

##### Sets and Indices
\[
\begin{aligned}
    &\mathcal{T} = && \{1,\dots,T\}, \quad\\
    &\mathcal{G} = &&\{\text{UTE}_1,\dots,\text{UTE}_{n}\}.
\end{aligned}
\]

##### Parameters
\[
\begin{aligned}
G_{\min_g}, G_{\max_g} \text{ — generation limits of unit } g \text{ (MW)}\\
c_g \text{ — thermal generation cost of unit } g
\end{aligned}
\]

##### Decision Variables
$$
p_{g,t} \ge 0 \text{ (MW)}
$$

##### Constraints

###### Capacity
$$
G_{\min_g} \le p_{g,t} \le G_{\max_g}, \quad \forall g, t
$$

---

#### Renewable Energies and Storage

##### Sets and Indices
\[
\begin{aligned}
&\mathcal{T} = &&\{1,2,\dots,T\} \quad \text{(periods)}\\
&\mathcal{R} = &&\{1,2,\dots,N_R\} \quad \text{set of renewable units (wind/solar)}\\
&\mathcal{S} = &&\{1,2,\dots,N_S\} \quad \text{set of storage units (batteries)}
\end{aligned}
\]

##### Parameters
For each $t \in \mathcal{T}$, $r \in \mathcal{R}$, and $s \in \mathcal{S}$:
\[
\begin{aligned}
& \overline{g}_{r,t} &&\text{ — exogenous renewable availability profile (MWmed)}\\
&\Delta t &&\text{ — time step (T), typically } \Delta t = 1\\
&E_{\min_s}, E_{\max_s} && \text{ — min/max stored energy limits (MWh)}\\
& E_{\text{ini}_s} &&\text{ — initial energy (MWh)}
&\overline{P}_{\text{ch}_s}, \overline{P}_{\text{dis}_s} && \text{ — maximum charge/discharge power (MW)}\\
& \eta_{\text{c}_s}, \eta_{\text{d}_s} \in (0,1] && \text{ — charging and discharging efficiencies}
\end{aligned}
\]

##### Decision Variables
$$
g_{\text{ren}_{r,t}} \ge 0 \text{ — dispatched renewable generation of unit } r \text{ at } t \text{ (MWavg)}
$$
$$
E_{s,t} \ge 0 \text{ — stored energy (SoC) of battery } s \text{ at } t \text{ (MWh)}
$$
$$
P_{\text{ch}_{s,t}}, P_{\text{dis}_{s,t}} \ge 0 \text{ — charge/discharge powers (MW)}
$$

##### Constraints

###### Renewable Sources — Availability Limit
$$
0 \le g_{\text{ren}_{r,t}} \le \overline{g}_{r,t}, \quad \forall r \in \mathcal{R}, \; \forall t \in \mathcal{T}
$$

###### Storage — Energy Balance (SoC)
\[
\begin{aligned}
&E_{s,1} = && E_{\text{ini}_s} + \eta_{\text{c}_s} P_{\text{ch}_{s,1}} \Delta t - \frac{1}{\eta_{\text{d}_s}} P_{\text{dis}_{s,1}} \Delta t, \quad \forall s \in \mathcal{S}\\
&E_{s,t} = && E_{s,t-1} + \eta_{\text{c}_s} P_{\text{ch}_{s,t}} \Delta t - \frac{1}{\eta_{\text{d}_s}} P_{\text{dis}_{s,t}} \Delta t, \quad \forall s \in \mathcal{S}, \; t=2,\dots,T
\end{aligned}
\]
###### Storage — State of Charge (SoC) Limits
\[
E_{\min_s} \le E_{s,t} \le E_{\max_s}, \quad \forall s \in \mathcal{S}, \; \forall t \in \mathcal{T}
\]

###### Storage — Power Limits
\[
\begin{aligned}
&0 \le P_{\text{ch}_{s,t}} \le \overline{P}_{\text{ch}_s}, && \quad \forall s \in \mathcal{S}, \; \forall t \in \mathcal{T}\\
&0 \le P_{\text{dis}_{s,t}} \le \overline{P}_{\text{dis}_s}, &&\quad \forall s \in \mathcal{S}, \; \forall t \in \mathcal{T}
\end{aligned}
\]

---

#### Objective Function

The hydrothermal dispatch problem is formulated as the minimization of total generation and deficit costs, namely:

- Thermal generation costs  
- Deficit cost (represented by a thermal unit with fixed cost, as in Unsihuay, 2023)  
- Spillage penalty (energy waste)  
- For the PDDD case, the future cost term $\alpha$ (FCF) is included  

##### Single LP Objective Function
$$
\min Z = \sum_{g\in\mathcal{G}} \sum_{t\in\mathcal{T}} (c_g p_{g,t}) + 0.3 \sum_{h\in\mathcal{H}} \sum_{t\in\mathcal{T}} S_{h,t} + C_{\text{def}} \sum_{t\in\mathcal{T}} D_t
$$

##### Objective Function for PDDD
$$
\min Z = \sum_{g\in\mathcal{G}} \sum_{t\in\mathcal{T}} (c_g p_{g,t}) + 0.3 \sum_{h\in\mathcal{H}} \sum_{t\in\mathcal{T}} S_{h,t} + C_{\text{def}} \sum_{t\in\mathcal{T}} D_t + \sum_{t\in\mathcal{T}} \alpha_{k_t}
$$

---

#### Power Balance (Load Satisfaction)

The load balance constraint requires that the total generation from all available sources, plus battery discharge and any incurred deficit, exactly meets the system demand:

$$
\sum_{h \in \mathcal{H}} G_{h,t} + \sum_{g \in \mathcal{G}} p_{g,t} + \sum_{r \in \mathcal{R}} g_{\text{ren}_{r,t}} + \sum_{s \in \mathcal{S}} ( P_{\text{dis}_{s,t}} - P_{\text{ch}_{s,t}} ) + D_t = d_t, \quad \forall t \in \mathcal{T}
$$

### Mathematical Modeling of MDI

The objective of this model is to determine the **optimal expansion plan** of the electric generation system, minimizing the total investment and operation cost, considering the availability of multiple technologies (hydroelectric, thermal, solar, wind, and battery storage), the demand satisfaction in two load levels (peak and off-peak), and the distinction between existing and candidate units.

This constitutes a **Mixed-Integer Linear Programming (MILP)** problem, solved by decomposition methods or **Branch and Bound**, as discussed in the theoretical overview.

---

#### Sets

- $\mathcal{G}$ – total set of generating units (hydroelectric, thermal, solar, and wind)  
- $\mathcal{G}_E \subset \mathcal{G}$ – subset of existing plants  
- $\mathcal{G}_C \subset \mathcal{G}$ – subset of candidate plants  
- $\mathcal{B}$ – total set of storage units (batteries)  
- $\mathcal{B}_E \subset \mathcal{B}$ – subset of existing batteries  
- $\mathcal{B}_C \subset \mathcal{B}$ – subset of candidate batteries  
- $\mathcal{T}$ – planning periods ($t = 1,\dots,10$)  
- $\mathcal{P}$ – load levels (peak and off-peak)

---

#### Parameters

- $C_{\text{inv}_g}$ – investment cost of generator $g$ [R\$ /MW]  
- $C_{\text{op}_g}$ – operating cost of generator $g$ [R\$ /MWh]  
- $P_{\text{max}_g}$ – maximum capacity of generator $g$ [MW]  
- $C_{\text{inv}_b}$ – investment cost of battery $b$ [R\$ /MW]  
- $C_{\text{op}_b}$ – operating cost of battery $b$ [R\$ /MWh]  
- $E_{\text{max}_b}$, $E_{\text{min}_b}$ – state-of-charge limits for battery $b$ [MWh]  
- $P_{\text{bat}_{\text{max}_b}}$ – maximum charge/discharge power of battery $b$ [MW]  
- $E_{0_b}$ – initial state of charge of battery $b$ [MWh]  
- $\eta_{c_b}$, $\eta_{d_b}$ – charge/discharge efficiencies (0.95)  
- $D_{p,t}$ – demand in load level $p$ and period $t$ [MW]  
- $h_p$ – duration of load level $p$ [h/year]  
- $x_{g,0}$ – 1 if generator $g$ exists at the beginning of the horizon, 0 otherwise  
- $x_{b,0}$ – 1 if battery $b$ exists at the beginning of the horizon, 0 otherwise  

---

#### Decision Variables

- $y_{g,t} \in \{0,1\}$ – construction (1) or not (0) of candidate generator $g$ in period $t$  
- $y_{b,t} \in \{0,1\}$ – construction (1) or not (0) of candidate battery $b$ in period $t$  
- $x_{g,t} \in \{0,1\}$ – existence of generator $g$ in period $t$ (1 if built up to $t$)  
- $x_{b,t} \in \{0,1\}$ – existence of battery $b$ in period $t$ (1 if built up to $t$)  
- $P_{g,p,t} \ge 0$ – generation of unit $g$ in load level $p$ and period $t$ [MW]  
- $P^{c}_{b,p,t} \ge 0$ – charging power of battery $b$ [MW]  
- $P^{d}_{b,p,t} \ge 0$ – discharging power of battery $b$ [MW]  
- $E_{b,p,t}$ – state of charge (SoC) of battery $b$ [MWh]  

---

---

#### Constraints

##### Demand Satisfaction
$$
\sum_{g \in \mathcal{G}} P_{g,t,p} + \sum_{b \in \mathcal{B}} ( P^{d}_{b,t,p} - P^{c}_{b,t,p} ) = D_{t,p}, \quad \forall t \in \mathcal{T}, \, p \in \mathcal{P}
$$

This ensures power balance at each period and load level: total net generation (generation plus storage balance) equals system demand.

---

#### Capacity Adequacy
$$
\sum_{g \in \mathcal{G}} G^{\max}_g x_{g,t} + \sum_{s \in \mathcal{S}} P^{\text{dis,max}}_{s,p} x_{s,t} \ge D_{t,p}, \quad \forall t,p
$$

Guarantees that total available capacity (generation + discharge) is sufficient to meet demand in all time steps.

---

#### Generation Limits
$$
0 \le P_{g,t,p} \le P^{\max}_g x_{g,t}, \quad \forall g,t,p
$$

Ensures that generation of each unit does not exceed its maximum capacity and is zero when inactive.

---

#### Storage Dynamics
$$
E_{s,t,p} = \begin{cases} 
E_{\text{ini},s} x_{s,t}, & t = 1, p = p_1, \\
E_{s,t-1,p_{|\mathcal{P}|}} + E_{\text{ini},s} y_{s,t} + \eta_c P^{ch}_{s,t,p} \Delta t_p - \dfrac{P^{dis}_{s,t,p}}{\eta_d} \Delta t_p, & t > 1, p  p_1, \\
E_{s,t,p-1} + \eta_c P^{ch}_{s,t,p} \Delta t_p - \dfrac{P^{dis}_{s,t,p}}{\eta_d} \Delta t_p, & p \neq p_1
\end{cases}
$$

Ensures energy continuity across load levels and periods, applying charge/discharge efficiencies and introducing initial energy only when the unit is built.

---

#### State of Charge Limits
$$
E^{\min}_b x_{b,t} \le E_{b,t,p} \le E^{\max}_b x_{b,t}, \quad \forall b,t,p
$$

Keeps the state of charge within the operational range, proportional to the unit’s availability.

---

#### Charge/Discharge Power Limits
$$
0 \le P^{c}_{b,t,p}, P^{d}_{b,t,p} \le P^{\max}_{\text{bat}_b} x_{b,t}, \quad \forall b,t,p
$$

Restricts charging and discharging powers according to the installed battery capacity and availability.

---

#### Initial State
$$
E_{b,1,p} = E_{0_b}, \quad \forall b,p
$$

Defines the initial energy level for each battery, ensuring consistency in the dynamic storage model.

---

#### Expansion Dynamics (Existence Accumulation)
\[
    x_{g,t} = x_{g,t-1} + y_{g,t}, \quad\\
x_{b,t} = x_{b,t-1} + y_{b,t}, \quad \\
\forall g,b,t>1\\
x_{g,0}, x_{b,0} \text{ given (initial existence)}
\]

Guarantees temporal coherence of the expansion plan: units exist only if previously constructed.

---

#### Unique Construction
$$
\sum_{t \in \mathcal{T}} y_{g,t} \le 1, \quad
\sum_{t \in \mathcal{T}} y_{b,t} \le 1, \quad \forall g \in \mathcal{G}_C, b \in \mathcal{B}_C
$$

Prevents multiple constructions of the same unit within the planning horizon.

---

#### Monotonic Growth
$$
x_{g,t} \ge x_{g,t-1}, \quad
x_{b,t} \ge x_{b,t-1}, \quad \forall g,b,t
$$

Ensures that the set of existing units grows monotonically, avoiding deactivation after construction and maintaining temporal consistency in expansion.

#### Objective Function

$$
\min Z = \sum_{t \in \mathcal{T}} \Bigg[\sum_{g \in \mathcal{G}} C^{\text{inv}}_g x_{g,t}+ \sum_{b \in \mathcal{B}} C^{\text{inv}}_b x_{b,t} + \sum_{p \in \mathcal{P}} h_p \Big( \sum_{g \in \mathcal{G}} C^{\text{op}}_g P_{g,t,p} + \sum_{b \in \mathcal{B}} C^{\text{op}}_b (P^{d}_{b,t,p} +  P^{c}_{b,t,p}) \Big) \Bigg]
$$

Where:

- $Z$ — total objective function value (minimum system cost)  
- $C^{\text{inv}}_{g}, C^{\text{inv}}_{b}$ — investment costs for generation and storage units [\$]  
- $C^{\text{op}}_{g}, C^{\text{op}}_{b}$ — operating costs for generation and storage units [\$/MWh]  
- $x_{g,t}, x_{b,t}$ — binary variables for existence of generation/storage units  
- $P_{g,t,p}$ — generated power [MW]  
- $P^{d}_{b,t,p}, P^{c}_{b,t,p}$ — discharging and charging powers [MW]  
- $h_p$ — duration of load level $p$ [h]  

This objective minimizes total system cost across the planning horizon, combining investment and operating costs weighted by the duration of each load level. The formulation captures the trade-off between capacity expansion and operation, ensuring an economically optimal solution under technical and energy constraints.

## **3. Model Architecture**

### **Overview**

The **NaivePyDESSEM** package follows a layered architecture that mirrors the hierarchical structure of the Brazilian energy models (*MDI*, *DECOMP*, and *DESSEM*).  
Its design ensures separation between **data ingestion**, **mathematical formulation**, **solver execution**, and **post-processing**, allowing flexible experimentation, teaching, and research on hydrothermal coordination.

The architecture is implemented in **Python 3.9+**, following object-oriented principles and extensive documentation through docstrings compliant with the *NumPy* style guide.

The **NaivePyDESSEM** package follows a layered architecture that mirrors the hierarchical structure of the Brazilian energy models (*MDI*, *DECOMP*, and *DESSEM*).  
Its design ensures separation between **data ingestion**, **mathematical formulation**, **solver execution**, and **post-processing**, allowing flexible experimentation, teaching, and research on hydrothermal coordination.

The architecture is implemented in **Python 3.11+**, following object-oriented principles and extensive documentation through docstrings compliant with the *NumPy* style guide.

### **Package Hierarchy**

The repository is organized into three primary modules — **NaivePyDESSEM**, **NaivePyDECOMP**, and **MDI** — each corresponding to a specific temporal stage of the Brazilian hydrothermal planning chain.  

The modular design ensures independent testing, scalability, and interoperability through a unified modeling interface based on **Pyomo** and **YAML-driven configuration**.

```text
├── src
│   ├── MDI
│   │   ├── cli
│   │   │   ├── __init__.py
│   │   │   ├── cli.py
│   │   │   └── plot_cli.py
│   │   ├── Generator
│   │   │   ├── __init__.py
│   │   │   ├── GeneratorBuilder.py
│   │   │   ├── GeneratorConstraints.py
│   │   │   ├── GeneratorDataTypes.py
│   │   │   ├── GeneratorEquations.py
│   │   │   ├── GeneratorObjectives.py
│   │   │   └── GeneratorVars.py
│   │   ├── Storage
│   │   │   ├── __init__.py
│   │   │   ├── StorageBuilder.py
│   │   │   ├── StorageConstraints.py
│   │   │   ├── StorageDataTypes.py
│   │   │   ├── StorageEquations.py
│   │   │   ├── StorageObjective.py
│   │   │   └── StorageVars.py
│   │   ├── __init__.py
│   │   ├── Builder.py
│   │   ├── DataFrames.py
│   │   ├── Formatters.py
│   │   ├── ModelCheck.py
│   │   ├── ModelFormatters.py
│   │   ├── PlotSeries.py
│   │   ├── Reporting.py
│   │   ├── Solver.py
│   │   ├── Utils.py
│   │   └── YAMLLoader.py
│   ├── NaivePyDECOMP
│   │   ├── cli
│   │   │   ├── __init__.py
│   │   │   ├── cli.py
│   │   │   ├── pddd_cli.py
│   │   │   └── plot_cli.py
│   │   ├── HydraulicGenerator
│   │   │   ├── __init__.py
│   │   │   ├── HydraulicConstraints.py
│   │   │   ├── HydraulicDataTypes.py
│   │   │   ├── HydraulicEquations.py
│   │   │   ├── HydraulicGeneratorBuilder.py
│   │   │   ├── HydraulicObjectives.py
│   │   │   ├── HydraulicVars.py
│   │   │   └── SimplifiedConstantProductivityFPH.py
│   │   ├── RenewableGenerator
│   │   │   ├── __init__.py
│   │   │   ├── RenewableConstraints.py
│   │   │   ├── RenewableDataTypes.py
│   │   │   ├── RenewableEquations.py
│   │   │   ├── RenewableGeneratorBuilder.py
│   │   │   ├── RenewableObjectives.py
│   │   │   └── RenewableVars.py
│   │   ├── Storage
│   │   │   ├── __init__.py
│   │   │   ├── StorageBuilder.py
│   │   │   ├── StorageConstraints.py
│   │   │   ├── StorageDataTypes.py
│   │   │   ├── StorageEquations.py
│   │   │   ├── StorageObjective.py
│   │   │   └── StorageVars.py
│   │   ├── ThermalGenerator
│   │   │   ├── __init__.py
│   │   │   ├── ThermalConstraints.py
│   │   │   ├── ThermalDataTypes.py
│   │   │   ├── ThermalEquations.py
│   │   │   ├── ThermalGeneratorBuilder.py
│   │   │   ├── ThermalObjectives.py
│   │   │   └── ThermalVars.py
│   │   ├── __init__.py
│   │   ├── Builder.py
│   │   ├── BuilderPDDD.py
│   │   ├── DataFrames.py
│   │   ├── Formatters.py
│   │   ├── ModelCheck.py
│   │   ├── ModelFormatters.py
│   │   ├── PDDDMergeModels.py
│   │   ├── PlotSeries.py
│   │   ├── Reporting.py
│   │   ├── Solver.py
│   │   ├── SolverPDDD.py
│   │   ├── Utils.py
│   │   └── YAMLLoader.py
│   ├── NaivePyDESSEM
│   │   ├── cli
│   │   │   ├── __init__.py
│   │   │   ├── cli.py
│   │   │   └── plot_cli.py
│   │   ├── HydraulicGenerator
│   │   │   ├── __init__.py
│   │   │   ├── ConstantProductivityFPH.py
│   │   │   ├── ExactFPH.py
│   │   │   ├── HydraulicConstraints.py
│   │   │   ├── HydraulicDataTypes.py
│   │   │   ├── HydraulicEquations.py
│   │   │   ├── HydraulicGeneratorBuilder.py
│   │   │   ├── HydraulicObjectives.py
│   │   │   ├── HydraulicVars.py
│   │   │   ├── PEFPH.py
│   │   │   └── SimplifiedConstantProductivityFPH.py
│   │   ├── RenewableGenerator
│   │   │   ├── __init__.py
│   │   │   ├── RenewableConstraints.py
│   │   │   ├── RenewableDataTypes.py
│   │   │   ├── RenewableEquations.py
│   │   │   ├── RenewableGeneratorBuilder.py
│   │   │   ├── RenewableObjectives.py
│   │   │   └── RenewableVars.py
│   │   ├── Storage
│   │   │   ├── __init__.py
│   │   │   ├── StorageBuilder.py
│   │   │   ├── StorageConstraints.py
│   │   │   ├── StorageDataTypes.py
│   │   │   ├── StorageEquations.py
│   │   │   ├── StorageObjective.py
│   │   │   └── StorageVars.py
│   │   ├── ThermalGenerator
│   │   │   ├── __init__.py
│   │   │   ├── ThermalConstraints.py
│   │   │   ├── ThermalDataTypes.py
│   │   │   ├── ThermalEquations.py
│   │   │   ├── ThermalGeneratorBuilder.py
│   │   │   ├── ThermalObjectives.py
│   │   │   ├── ThermalPieceWise.py
│   │   │   └── ThermalVars.py
│   │   ├── __init__.py
│   │   ├── Builder.py
│   │   ├── DataFrames.py
│   │   ├── Formatters.py
│   │   ├── ModelCheck.py
│   │   ├── ModelFormatters.py
│   │   ├── PlotSeries.py
│   │   ├── Reporting.py
│   │   ├── Solver.py
│   │   ├── Utils.py
│   │   └── YAMLLoader.py
│   └── naivepydessem.egg-info
│       ├── dependency_links.txt
│       ├── entry_points.txt
│       ├── PKG-INFO
│       ├── requires.txt
│       ├── SOURCES.txt
│       └── top_level.txt
├── tests
├── LICENSE
├── MANIFEST.in
├── pyproject.toml
├── README.md
├── requirements.txt
└── setup.cfg
```
Each main module contains domain-specific subpackages:

- **cli/** — Command-line interfaces for model execution, plotting, and data export.

- **Generator/, HydraulicGenerator/, ThermalGenerator/, RenewableGenerator/, Storage/** — Contain builder, constraint, variable, and objective definitions for each asset type.

- **Builder.py** — Central class responsible for assembling the Pyomo model using data and configuration inputs.

- **Solver.py** — Wrapper for solver execution (CPLEX, Gurobi, SCIP) and result handling.

- **DataFrames.py, Reporting.py, PlotSeries.py** — Modules for data manipulation, result visualization, and reporting in cli formats.

- **YAMLLoader.py** — Responsible for reading model configurations, parameters, and instance data from YAML files.

- **ModelCheck.py and ModelFormatters.py** — Implement internal consistency checks and formatting utilities for validation and debugging.

### Design Overview

The architecture follows a layered modular pattern:

- **Data Layer** — YAML configuration parsing, type definitions, and validation.

- **Model Layer** — Definition of decision variables, constraints, and objectives for each subsystem.

- **Solver Layer** — Interfaces with external solvers and manages solution logging.

- **Visualization Layer** — Generation of time series plots and .

This hierarchy promotes clarity, reusability, and transparency in both model development and numerical experimentation.



### 🧭 Command-Line Interface (CLI)

Each module provides a lightweight command-line interface (CLI) that allows direct model execution and visualization without requiring manual scripting.  

Each command-line tool encapsulates a complete modeling workflow, including:
- YAML-based configuration parsing;
- Model construction and validation;
- Solver execution and result export;
- Optional visualization and reporting.

The CLI is implemented with the **Click** framework, ensuring cross-platform compatibility, structured argument parsing, and reproducibility through declarative configuration files.

---

#### **1. Solving a Model**

Each model variant can be solved directly via its respective command-line entry point.  
Input data and settings are defined in a YAML file describing system topology, parameters, and solver options.

**DESSEM-like dispatch (short-term)**  
Solves the hourly hydrothermal scheduling problem.

```bash
pydessem-solve path/to/case.yaml --out_dir results/ --out_file dispatch.csv
```

**DESSEM-like dispatch (short-term)**  

Single-LP (Linear Program):

```bash
pydecomp-solve path/to/case.yaml --out_dir results/ --out_file dispatch.csv
```

Using PDDD (Deterministic Dual Dynamic Programming):

```bash
pydecomp-pddsolve path/to/case.yaml --out_dir results/ --out_file dispatch.csv
```

**MDI-like generation expansion planning (long-term)**
Determines the optimal multi-year investment and operation plan.


```bash
mdi-solve path/to/case.yaml --out_dir results/ --out_file dispatch.csv
```

#### 2. Plotting Results

## 4. CLI Arguments

#### 1. Solver CLI

All solver commands share three common command-line arguments:

- **`{yaml_file}`** — the first positional argument, corresponding to the YAML input file defining the case configuration.  
- **`--out_dir`** — the output directory where the resulting case solutions (CSV, Excel, or Parquet) will be saved.  
- **`--out_file`** — the name of the results file to be generated.

All three arguments are **mandatory**.

---

### 2. Plot CLI

The basic plot CLI commands share the following options:

- **`input_file`**  
  Path to the input data file.  
  Supported formats: `.csv`, `.xlsx`, `.parquet`.

- **`--mode`**  
  Defines the export or visualization mode.  
  Options:  
  - `table` → Generates a LaTeX-formatted table.  
  - `plot` → Creates a graphical plot (line or bar).  
  - `ctrl` → Exports a control matrix (U/Y/W).

- **`--category`, `-c`**  
  Specifies one or more variable categories to visualize or export.  
  Example: `--category G ctrl BAT cost`.

- **`--plot-style`**  
  Defines the plot style when `--mode plot` is selected.  
  Options:  
  - `line` → Line plot.  
  - `bar` → Bar plot.

- **`--stacked`**  
  Enables stacked bars (applies only to bar plots).  
  Useful for cumulative or component-based visualizations.

- **`--level`**  
  Specifies the generation level for categories such as `G` or `GT`.  
  Example: `--level Ponta` or `--level Fora`.

- **`--title`**  
  Custom title for the plot or caption for LaTeX table output.

- **`--ylabel`**  
  Y-axis label for plots (e.g., “Energy [MWh]”).

- **`--out-dir`**  
  Output directory for the generated file.

- **`--out-file`**  
  Name of the output file (plot image or `.tex` table).

- **`--label`**  
  LaTeX label identifier for referencing generated tables or figures.

## 4. YAML Configuration

All models in the NaivePyDESSEM suite are configured via YAML files, which define system data, solver settings, and simulation parameters in a human-readable format. 

### 🧩 Step-by-Step: Building a DESSEM Configuration File

This section provides a structured walkthrough for creating a **NaivePyDESSEM** configuration file (`.yaml`), guiding the user through each key section — from meta information to hydropower, thermal, renewable, and storage data.  
All keywords, indentation levels, and formats must follow the conventions shown below.

---

#### 🪶 1. Header and Metadata (`meta`)

Start by defining general model information and global parameters under the `meta:` key.  
This section includes the case name, time horizon, solver options, and system demand.

```yaml
meta:
  name: "CaseName-Study1"      # Descriptive case identifier
  horizon: 24                  # Number of hourly periods (e.g., 24 for one day)
  delta_t: 1.0                 # Duration of each time step [h]
  Cdef: 1000.0                 # Deficit penalty cost [$ / MWh]
  Solver: mindtpy              # Main solver (MILP/MINLP)
  Solver_Options:              # Optional fine-tuning of solver parameters
    mip_solver: cbc
    nlp_solver: cyipopt
    strategy: OA
    time_limit: 300
  demand: [700, 750, 850, 950, 1000, 1100, 1150, 1200,
           1250, 1400, 1500, 1400, 1400, 1300, 1400, 1600,
           1700, 1900, 2000, 1800, 1300, 1100, 900, 800]  # MW per hour
```

📘 **Notes**
- `horizon` defines the number of time intervals (typically 24 for daily cases).
- `Cdef` imposes a high penalty to discourage energy deficits.
- `Solver_Options` can be adjusted according to the installed solvers (e.g., `cbc`, `gurobi`, or `cplex`).

---

#### 🌊 2. Hydropower Data (`hydro`)

Define hydraulic parameters, reservoir characteristics, and inflows for each hydro unit.  
The **`hydro`** block starts with two constants — `zeta` (hydraulic constant) and `zeta_vol` (volume–flow conversion factor) — followed by a `units:` dictionary.

```yaml
hydro:
  zeta: 0.00981                # MW per (m3/s * m)
  zeta_vol: 0.0036             # hm3 per (m3/s * h)
  units:
    UHE_1:
      Qmin: 0.0                # Minimum turbined flow [m3/s]
      Qmax: 600.0              # Maximum turbined flow [m3/s]
      Vmin: 1000.0             # Minimum volume [hm3]
      Vmax: 3000.0             # Maximum volume [hm3]
      Vmeta: 2000.0            # Target final volume [hm3]
      Vini: 2500.0             # Initial reservoir volume [hm3]
      afluencia: [200, 210, 220, ..., 170]  # Natural inflows [m3/s]
      upstreams: []            # Upstream reservoirs (if any)
      a: [4.012e+2, 5.010e-2, -1.573e-5, 3.297e-9, -2.883e-13]  # h_up(V)
      b: [3.719e+2, 1.932e-3, -8.530e-8, 2.376e-12, -2.616e-17]  # h_down(Q+S)
      rho: [6.895e-2, 3.007e-3, 5.559e-3, 5.840e-6, -4.637e-6, -3.636e-5]  # Productivity curve
      losses: [0.0, 0.0, 1.375e-5]  # h_loss(Q)
      pe: 0.92                 # Specific productivity [MW/(m3/s)]
      p: 0.92                  # Global productivity (simplified)
      mode: "exact"            # {"constant","specific","exact","simplified"}
      compute_total_inflow: true
```

📘 **Notes**
- `mode` selects the type of hydraulic head computation.
- When using `"exact"` or `"specific"`, coefficients `a`, `b`, `rho`, and `losses` must be provided.
- If the plant has upstream reservoirs, list them under `upstreams`.

Add subsequent hydropower units (`UHE_2`, `UHE_3`, etc.) following the same structure.

---

#### 🔥 3. Thermal Data (`thermal`)

The **`thermal`** section defines each thermal generation unit, including operational limits and cost coefficients.

```yaml
thermal:
  units:
    UT_1:
      Pmin: 150               # Minimum generation [MW]
      Pmax: 455               # Maximum generation [MW]
      RU: 50                  # Ramp-up limit [MW/h]
      RD: 50                  # Ramp-down limit [MW/h]
      a: 1000                 # Fixed cost [$ / h]
      b: 16.19                # Linear cost [$ / MWh]
      c: 0.00048              # Quadratic cost [$ / (MWh)^2]
      SC: 4500                # Start-up cost [$]
      t_up: 8                 # Minimum up-time [h]
      t_down: 8               # Minimum down-time [h]
      init_status_h: 8        # Initial on-state duration [h]
      u0: 1                   # Initial unit status (1 = on)
      p0: 0.0                 # Initial generation [MW]
      gamma: 0.0              # Reserved for future use
      pw_breaks: null         # (optional) for piecewise cost
      pw_costs: null          # (optional) for piecewise cost
  has_history: true           # Indicates that initial conditions are defined
```

📘 **Notes**
- Each **UT_x** corresponds to a thermal unit (e.g., gas or coal plant).  
- Cost coefficients follow a quadratic cost function:  
  $$ C(p) = a + b\,p + c\,p^2 $$
- Use `has_history: true` to indicate the model should consider previous operational states.

---

#### 🌬️ 4. Renewable Data (`renewable`)

This section defines renewable generation units such as **wind (EOL)** and **solar (SOL)**, with their availability profiles.

```yaml
renewable:
  units:
    EOL_1:
      gbar: [110, 112, 110, 105, 100, 85, 80, 60,
             55, 50, 45, 40, 40, 45, 50, 55,
             60, 80, 85, 100, 105, 110, 112, 110]
    SOL_1:
      gbar: [0, 0, 0, 0, 0, 0, 40, 65,
             90, 120, 140, 160, 170, 170, 160, 130,
             100, 60, 20, 0, 0, 0, 0, 0]
```

📘 **Notes**
- `gbar` represents the **maximum available renewable power** per hour (in MW).  
- Values are typically derived from normalized wind or solar resource profiles.  
- The model will optimize dispatch up to these limits.

---

#### ⚡ 5. Storage Data (`storage`)

The **`storage`** block specifies battery storage characteristics, including energy and power constraints.

```yaml
storage:
  delta_t: 1.0
  units:
    BAT_1:
      Emin: 300.0             # Minimum state of charge [MWh]
      Emax: 1500.0            # Maximum state of charge [MWh]
      Eini: 400.0             # Initial stored energy [MWh]
      Pch_max: 150.0          # Maximum charging power [MW]
      Pdis_max: 150.0         # Maximum discharging power [MW]
      eta_c: 0.95             # Charging efficiency
      eta_d: 0.95             # Discharging efficiency
```

📘 **Notes**
- The **state of charge (SoC)** evolves dynamically via the energy balance equation.  
- Ensure that `delta_t` is consistent with the value defined in `meta.delta_t`.

---

#### ✅ 6. Final Checks

Before running the model:
- Validate YAML indentation (2 spaces per level, no tabs).  
- Ensure lists (`[...]`) have exactly `horizon` entries for time-dependent parameters.  
- Confirm that all units are consistent (MW, MWh, m³/s, hm³).  
- Save the file as, for example:
  ```bash
  DESSEM_CaseX.yaml
  ```

To execute:
```bash
pydessem-solve DESSEM_CaseX.yaml --out_dir results/ --out_file dispatch.csv
```

---

🧭 **Summary**

| Section | Keyword | Description |
|----------|----------|-------------|
| `meta:` | General model setup | Time, solver, and demand |
| `hydro:` | Hydropower configuration | Reservoirs, inflows, polynomials |
| `thermal:` | Thermal generation data | Unit limits, cost curves, dynamics |
| `renewable:` | Renewable generation | Solar and wind profiles |
| `storage:` | Energy storage | SoC, efficiency, charge/discharge power |

This structure ensures full compatibility with **NaivePyDESSEM**, maintaining transparent, reproducible, and standardized model definitions for academic and professional use.

### 🧩 Step-by-Step: Building a DECOMP Configuration File

This section presents a detailed guide for constructing a **NaivePyDECOMP** configuration file (`.yaml`), representing a **medium-term hydrothermal operation model** based on the Brazilian DECOMP structure.  
Each block must respect the same naming conventions, indentation, and parameter formatting as the example below.

---

#### 🪶 1. Header and Metadata (`meta`)

The `meta` section defines the **simulation scope, solver configuration, and demand series**.  
It establishes the number of time periods (typically months), the duration of each period, and the optimization solver.

```yaml
meta:
  name: "CaseName-DECOMP"     # Case identifier
  horizon: 12                 # Number of monthly periods (e.g., 12 months)
  delta_t: 1.0                # Duration of each period [months]
  Cdef: 500.0                 # Deficit penalty cost [$ / MWh]
  Solver: cbc                 # MILP solver
  Solver_Options:             # Optional solver fine-tuning
    mip_solver: glpk
    nlp_solver: cyipopt
    strategy: OA
    time_limit: 3600

  demand: [100, 120, 150, 100, 120, 150, 100, 120, 150, 100, 120, 150]
```

📘 **Notes**
- The demand vector (`demand`) defines total system load per period (in MWmed or MWh/month).
- `Cdef` specifies the cost of non-served energy, typically between 500–2000 R$/MWh.
- Solver configurations can be adapted for Gurobi or CPLEX when available.

---

#### 🌊 2. Hydropower Data (`hydro`)

The **`hydro`** block contains reservoir and flow parameters for all hydroelectric plants.  
Each unit is defined by physical limits, initial conditions, inflows, and upstream relationships.

```yaml
hydro:
  units:
    UHE_1:
      Qmin: 0.0               # Minimum turbined flow [hm3]
      Qmax: 60.0              # Maximum turbined flow [hm3]
      Vmin: 20.0              # Minimum storage [hm3]
      Vmax: 100.0             # Maximum storage [hm3]
      Vini: 100.0             # Initial volume [hm3]
      afluencia: [16, 14, 11, 16, 14, 11, 16, 14, 11, 16, 14, 11]
      upstreams: ['UHE_2']    # Upstream plant(s)
      p: 0.95                 # Specific productivity [MW/(hm3/month)]
      compute_total_inflow: true
    UHE_2:
      Qmin: 0.0
      Qmax: 80.0
      Vmin: 40.0
      Vmax: 200.0
      Vini: 130.0
      afluencia: [15, 12, 10, 15, 12, 10, 15, 12, 10, 15, 12, 10]
      upstreams: []           # No upstream plants
      p: 0.90
      compute_total_inflow: true
```

📘 **Notes**
- All flows and volumes are in **hm³**, consistent with monthly scales.  
- `p` defines the **linear productivity** for each plant in MW per hm³/month.  
- `compute_total_inflow: true` ensures automatic addition of upstream releases and spillage.

---

#### 🔥 3. Thermal Data (`thermal`)

The **`thermal`** block defines dispatchable thermal plants, typically simplified with constant cost and capacity limits.

```yaml
thermal:
  units:
    UT_1:
      Gmin: 0                 # Minimum generation [MW]
      Gmax: 30                # Maximum generation [MW]
      Cost: 10                # Average operating cost [$ / MWh]
    UT_2:
      Gmin: 0
      Gmax: 20
      Cost: 25
```

📘 **Notes**
- Each thermal unit contributes to meeting the demand and adds a fixed cost proportional to energy produced.
- Units can be expanded to include ramping or startup constraints if needed.

---

#### 🌬️ 4. Renewable Data (`renewable`)

Defines variable renewable generation (wind and solar) with exogenous availability profiles.

```yaml
renewable:
  units:
    EOL_1:
      gbar: [30, 25, 40, 30, 25, 40, 30, 25, 40, 25, 25, 40]  # Wind generation [MW]
    SOL_1:
      gbar: [25, 20, 30, 25, 10, 30, 25, 10, 30, 10, 10, 30]  # Solar generation [MW]
```

📘 **Notes**
- The `gbar` list defines the available renewable power per month.  
- Renewable energy is treated as non-dispatchable (upper bound).  
- The model optimizes renewable curtailment implicitly.

---

#### ⚡ 5. Storage Data (`storage`)

The **`storage`** section specifies battery-type energy storage systems with energy and power constraints.

```yaml
storage:
  delta_t: 1.0
  units:
    BAT_1:
      Emin: 50.0              # Minimum state of charge [MWh]
      Emax: 500.0             # Maximum state of charge [MWh]
      Eini: 60.0              # Initial energy [MWh]
      Pch_max: 50.0           # Maximum charging power [MW]
      Pdis_max: 50.0          # Maximum discharging power [MW]
      eta_c: 0.95             # Charge efficiency
      eta_d: 0.95             # Discharge efficiency
```

📘 **Notes**
- Monthly time steps imply slower charge/discharge dynamics compared to DESSEM.  
- Units are compatible with multi-period optimization and dual dynamic programming (PDDD) extensions.

---

#### ✅ 6. Final Checks

Before execution:
- Verify YAML structure (two-space indentation, no tabs).  
- Ensure all lists (`[...]`) match the declared `horizon` (12 elements).  
- Keep consistent units: MW, MWh, and hm³.  
- Save as:
  ```bash
  DECOMP_CaseX.yaml
  ```

Execute the model:
```bash
pydecomp-solve DECOMP_CaseX.yaml --out_dir results/ --out_file dispatch.csv
```

Or, using PDDD:
```bash
pydecomp-pddd-solve DECOMP_CaseX.yaml --out_dir results/ --out_file dispatch.csv
```
---

🧭 **Summary**

| Section | Keyword | Description |
|----------|----------|-------------|
| `meta:` | Simulation setup | Time, solver, and demand definition |
| `hydro:` | Hydropower model | Reservoirs, inflows, productivity |
| `thermal:` | Thermal units | Capacity and cost |
| `renewable:` | Renewable generation | Wind and solar data |
| `storage:` | Energy storage | Capacity, SoC limits, and efficiency |

This template ensures full compliance with **NaivePyDECOMP**, promoting transparent modeling of hydrothermal coordination problems with monthly resolution.

### 🧩 Step-by-Step: Building an MDI Configuration File

This document provides a comprehensive guide for constructing a **NaivePyMDI** configuration file (`.yaml`), used for **generation expansion planning** (long-term).  
Each section defines parameters and structures that control investment, operation, and energy balance between *peak* and *off-peak* demand levels.

---

#### 🪶 1. Header and Metadata (`meta`)

The `meta` section defines simulation parameters, solver configuration, and load segmentation into *Ponta* and *Fora de Ponta* levels.

```yaml
meta:
  name: "CaseName-MDI"          # Case identifier
  horizon: 10                   # Number of planning periods (e.g., 10 years)
  delta_t: 0.5                  # Duration of each period [years]
  parcel_investment: True       # Annualize investment costs (True/False)
  Solver: cbc                   # MILP solver
  Solver_Options:
    mip_solver: glpk
    nlp_solver: cyipopt
    strategy: OA
    time_limit: 3600

  demand:
    Ponta: [200, 350, 350, 400, 500, 600, 650, 750, 850, 1000]
    Fora:  [100, 150, 200, 250, 300, 350, 400, 450, 450, 500]

  level_hours:
    Ponta: 2000
    Fora:  6740

  level_precedence: ["Ponta", "Fora"]
```

📘 **Notes**
- `parcel_investment: True` spreads investment costs evenly across the horizon (annualized model).  
- `demand` defines two load segments — *Ponta* (peak) and *Fora* (off-peak) — each with a vector of MW values.  
- `level_hours` specifies the duration of each level in hours per year.  
- The order of load levels is given by `level_precedence`, ensuring temporal consistency.

---

#### ⚙️ 2. Generator Data (`generator`)

The **`generator`** section defines generation units (existing and candidate) across multiple technologies — hydro, thermal, solar, wind, and deficit (penalty) units.

```yaml
generator:
  units:
    UHE_1:
      state: 1                 # Existing (1)
      p_max: 600               # Installed capacity [MW]
      c_op: 0                  # Operating cost [$ / MWh]
      c_inv: 0                 # Investment + O&M cost [$]
      include_cap: True        # Include in capacity constraint

    UHE_2:
      state: 0                 # Candidate (0)
      p_max: 500
      c_op: 0
      c_inv: 75_000_000
      include_cap: True

    UTE_1:
      state: 1
      p_max: 250
      c_op: 55
      c_inv: 0
      include_cap: True

    UTE_2:
      state: 0
      p_max: 250
      c_op: 40
      c_inv: 15_000_000
      include_cap: True

    SOL_1:
      state: 0
      p_max: 100
      c_op: 0
      c_inv: 15_000_000
      include_cap: True

    EOL_1:
      state: 0
      p_max: 100
      c_op: 0
      c_inv: 10_000_000
      include_cap: True

    Def_1:
      state: 1
      p_max: 10000
      c_op: 5000
      c_inv: 0
      include_cap: True
```

📘 **Notes**
- Each generator has a **binary state**:
  - `1` → existing plant, active from the first period;
  - `0` → candidate plant, may be built during the horizon.
- `c_inv` (investment) applies only to candidate units.  
- The “Def” (deficit) unit provides load balance at very high cost, enforcing the penalty mechanism.  
- `include_cap` ensures participation in the adequacy constraint (capacity margin).

---

#### ⚡ 3. Storage Data (`storage`)

The **`storage`** section defines battery systems with power and energy limits, as well as investment and operation costs.

```yaml
storage:
  delta_t: 0.5
  units:
    BAT_1:
      state: 0                 # Candidate
      c_op: 0                  # Operating cost [$ / MWh]
      c_inv: 5_000             # Investment + O&M cost [$]
      Emin: 50.0               # Minimum state of charge [MWh]
      Emax: 500.0              # Maximum state of charge [MWh]
      Eini: 100.0              # Initial stored energy [MWh]
      Pch_max: 300.0           # Maximum charging power [MW]
      Pdis_max: 300.0          # Maximum discharging power [MW]
      eta_c: 0.95              # Charge efficiency
      eta_d: 0.95              # Discharge efficiency
      include_cap: True        # Include in capacity adequacy constraint
```

📘 **Notes**
- The `state` flag distinguishes **existing** (1) and **candidate** (0) storage units.  
- Efficiency parameters (`eta_c`, `eta_d`) capture energy conversion losses.  
- The model considers investment and operation costs for optimal expansion planning.  
- Storage units can offset peak demand, reducing thermal generation and investment needs.

---

#### ✅ 4. Final Checks

Before running the simulation:
- Validate YAML indentation and syntax (2 spaces per level).  
- Ensure both `Ponta` and `Fora` demand vectors have the same length as the planning horizon.  
- Check that all capacity and cost parameters are positive and consistent in units (MW, MWh, years).  
- Save as:
  ```bash
  MDI_CaseX.yaml
  ```

Execute:
```bash
mdi-solve MDI_CaseX.yaml --out_dir results/ --out_file dispatch.csv
```

---

🧭 **Summary**

| Section | Keyword | Description |
|----------|----------|-------------|
| `meta:` | Simulation setup | Time horizon, solver, and demand segmentation |
| `generator:` | Generation units | Capacity, investment, and operation costs |
| `storage:` | Energy storage | Dynamic SoC, efficiency, and investment data |

This configuration schema fully aligns with **NaivePyMDI**, supporting deterministic or investment-based planning for academic, research, and professional applications.