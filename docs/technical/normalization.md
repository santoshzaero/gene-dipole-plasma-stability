# Normalization and species

In the GENE 3.1 manual, the reference velocity is $c_{\rm ref}=\sqrt{T_{\rm ref}/m_{\rm ref}}$ with temperature expressed in energy units and $m_{\rm ref}$ the reference mass. In SI, the reference cyclotron angular frequency is $\Omega_{\rm ref}=e B_{\rm ref}/m_{\rm ref}$, where $e$ is the positive elementary charge and $B_{\rm ref}$ is the reference field strength. The reference gyroradius is $\rho_{\rm ref}=c_{\rm ref}/\Omega_{\rm ref}$. With reference length $L_{\rm ref}$, code time is $t_{\rm phys} c_{\rm ref}/L_{\rm ref}$ and the rates recorded in `omega.dat` are the physical growth and real angular frequency divided by $c_{\rm ref}/L_{\rm ref}$. [GENE manual and normalization reference](../references.md)

The normalized gradient parameters for species $s$ are

$$
\texttt{omn}_s=-L_{\rm ref}\,\partial_x\ln n_s,\qquad
\texttt{omt}_s=-L_{\rm ref}\,\partial_x\ln T_s,
$$

where $x$ is the GENE radial profile coordinate before its length normalization, $n_s$ the equilibrium density and $T_s$ the equilibrium temperature. These are local logarithmic profile derivatives. The physical binormal wavenumber is $k_y$ and the dimensionless code input is $k_y\rho_{\rm ref}$. Here `ky0_ind = 1` and `nky0 = 1`, so `kymin` is the one nonzero simulated binormal wavenumber in reference units. The coordinate wavelength is $2\pi/k_y$ in length units. Physical $k_\perp$ depends on the metric along the tube and on the radial wavenumber.

| Study/species | Code mass | Charge in $e$ | Density | Temperature |
| --- | ---: | ---: | ---: | ---: |
| Pair scan, positron (input label `ions`) | 1 | +1 | 1 | 1 |
| Pair scan, electron | 1 | −1 | 1 | 1 |
| Isotope scans, hydrogen | 1 | +1 | 1 | 1 |
| Isotope scans, deuterium | 2 | +1 | 1 | 1 |
| Isotope scans, electron | 0.00054462 | −1 | 1 | 1 |

The isotope inputs share `mref = 1.0` in proton-mass units. The pair inputs set equal masses and leave `mref` unspecified. The manual expresses species masses and temperatures as ratios to their references, and densities relative to the electron density. The isotope parameter output supplies `mref`; the saved dipole metadata lists zero for `Lref` and `Bref` and the input omits `Tref` and `nref`. These records do not establish a complete SI mapping. In particular, the physical ring inputs alone are insufficient to infer the frequency conversion factor used by these runs.

The isotope ordering compares simulations at a shared code normalization and matched nominal gradients and binormal wavenumbers. Fixing $k_y\rho_{\rm ref}$ can still change $k_y\rho_i$ when the ion thermal gyroradius $\rho_i$ changes with ion mass. Fixing `coll` fixes a code input and leaves room for mass-dependent scattering rates in the operator. Before comparisons in physical units, establish common dimensional reference values, confirm the geometry mapping and collision normalization, and state whether the comparison matches the reference or species gyroradius scale.
