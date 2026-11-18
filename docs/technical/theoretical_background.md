# Linear model and dipole geometry

The $\delta f$ gyrokinetic approximation separates a small distribution perturbation $\delta f_s$ from an equilibrium Maxwellian $F_{0s}$ for species $s$. Gyrokinetics orders the characteristic fluctuation frequency well below the cyclotron frequency, assumes a strongly magnetized equilibrium with slowly varying profiles on the orbit scale, and averages over the gyrophase while retaining finite Larmor radius effects. Phase space then has three gyrocenter spatial coordinates and two velocity coordinates. In a local flux tube the equilibrium and its profile derivatives are prescribed on a reference surface.

A schematic linear form is

$$
\partial_t g_s=\mathcal L_s[g]+\mathcal D_s[\phi_1]+\mathcal C_s[g].
$$

Here $g_s$ is the perturbation variable for species $s$, $g$ collects all species, $\phi_1$ is the perturbed electrostatic potential, and $t$ is time. The linear operators $\mathcal L_s$, $\mathcal D_s$, and $\mathcal C_s$ group streaming, mirror and magnetic drift terms, the gyroaveraged field and equilibrium-gradient response, and collisions, respectively. The charge response determines $\phi_1$ self-consistently. This operator form summarizes the model. GENE evolves its discretized equations with the configured numerical dissipation and velocity-space collision operator. [GENE dipole gyrokinetics](../references.md)

The runs use `beta = 0`, `debye2 = 0`, and `nonlinear = F`. The equilibrium magnetic field is retained, the potential is the single evolved field diagnostic, and the fluctuating magnetic components are omitted. The zero Debye-length limit applies the gyrokinetic quasineutral field equation, including finite-gyroradius polarization. An electromagnetic extension would retain magnetic fluctuations and address a different model. The Landau collision operator is active with `coll = 0.01` and `coll_cons_model = 'xu_rosenbluth'`.

The ring-dipole interface generates field strength, curvature, gradients, and the metric along a closed flux tube. The local source identifies these inputs.

| Setting | Value | Role |
| --- | --- | --- |
| `r0_dipole` | 0.4 | Current-ring radius in metres |
| `Icurr_dipole` | 750 | Ring current in amperes |
| `c_surf_dipole` | 1.2 | Surface-selection factor measured in ring radii |
| `c_dt_dipole` | $10^{-5}$ | Numerical field-line tracing step input, separate from the plasma integration timestep |
| `dpdx_term` | `gradB_eq_curv` | Selected relationship for the pressure-gradient contribution to magnetic drifts |

The base input has `q0 = shat = 0` and `nexc = 0`. Use the dipole metrics for spatial interpretation. The standard tokamak interpretation of the safety factor or a tokamak mapping from toroidal mode number to `kymin` requires separate justification in this geometry. [Ring-dipole implementation and coordinates](../references.md)
