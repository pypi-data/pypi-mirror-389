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