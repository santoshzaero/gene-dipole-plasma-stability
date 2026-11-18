# Adiabatic-electron theory benchmark

The proposed comparison uses one Maxwellian kinetic deuterium species, a Boltzmann electron response with equal reference temperatures, electrostatic local geometry, negligible Debye length, and a collisionless limit for the theory comparison. Choose a nonzonal perturbation with nonzero binormal wavenumber. Use the same equilibrium gradients, field-line boundary conditions, geometry metrics, and frequency convention in both models. Include full ion finite-Larmor-radius and streaming effects unless the benchmark explicitly takes a controlled asymptotic limit.

Plunk et al. equations (2)–(5) give a candidate kinetic-ion and Boltzmann-electron eigenproblem in the convention $e^{-i\Omega t}$. For singly charged ions write it as

$$
[i v_\parallel\partial_\ell + \Omega - \omega_{di}]g_i
= \varphi J_0(a)(\Omega-\omega_{*i}^T)F_{0i},
\qquad
\int d^3v\,J_0(a)g_i=n_i(1+T_i/T_e)\varphi.
$$

Here $\Omega$ is the complex angular frequency, $g_i$ the nonadiabatic ion response, $\ell$ the distance along the magnetic field, $v_\parallel$ the velocity parallel to the field, and $F_{0i}$ the ion equilibrium Maxwellian of density $n_i$ and temperature $T_i$. The potential is $\varphi=e\phi_1/T_i$, where $e$ is the elementary charge and $\phi_1$ the electrostatic perturbation. $T_e$ is electron temperature. $J_0$ is the Bessel function of order zero, with $a=k_\perp v_\perp/\Omega_{ci}$, using local perpendicular wavenumber $k_\perp$, perpendicular speed $v_\perp$, and ion cyclotron angular frequency $\Omega_{ci}=eB/m_i$ at local magnetic field strength $B$ for ion mass $m_i$. The magnetic drift frequency $\omega_{di}$ is the local dot product of drift velocity and perpendicular wavevector. $\omega_{*i}^T$ is the velocity-dependent diamagnetic drive determined by density and temperature gradients. The velocity integral is over ion velocity space. Use guiding-center orbit coordinates and include the variation of parallel velocity along the field and bounce matching for trapped particles. [Plunk et al., formulation and conventions](../references.md)

Eliminating $g_i$ using periodic and bounce-matched streaming gives a frequency-dependent integral operator on $\varphi$. The dispersion condition is existence of a nonzero $\varphi$ satisfying the quasineutrality equation after substitution. This is an analytical eigenproblem rather than a universal scalar polynomial. Confirm the exact drift and gyroaveraging factors and the applicability of the field-line boundary condition in the ring dipole before solving it. If no closed-form root is available, independently discretize and solve the integral equation with refinement. For an algebraic check, select a separately justified limiting geometry or ordering and document how GENE approaches that limit.

For the GENE candidate use `n_spec = 1` with only the deuterium species block, retain `beta = debye2 = 0`, `tau = 1`, and use the collisionless setting for the theory comparison. The source detects adiabatic electrons when an active electron species is absent, requires `tau = 1` in this path, and sets beta to zero. Confirm the startup model, effective electron response, absence of hybrid/no-response settings, and the nonzonal field equation before interpreting output. Record the effect of numerical hyperdiffusion and test its sensitivity together with grid and timestep refinement. Convert the signed frequency into the same convention before comparing roots and envelopes.

First establish one matched operating point. Then vary density gradient at fixed temperature gradient and track the same branch in theory and simulation. Both the presence of growth and the shape of the real-frequency response depend on the branch and assumptions. Zero growth or linear scaling with density gradient remains to be established for the chosen case.
