# Four-student GENE benchmark

**Status:** Candidate based on two historical local runs. The four-student comparison and mesh validation are pending.

Use [the exact deuterium parameter file](parameters), copied byte-for-byte from the isotope reference case. All four students should use this same file and GENE 3.1 patch 5, with the source/build details in [the installation record](../docs/research_log.md#1-installation-and-validation). Use one rank and one OpenMP thread for the first comparison when supported. Log alternative builds and environments.

- Electron/deuterium charges −1 and +1, masses 0.00054462 and 2 in proton-mass units, and both densities and temperatures 1 in code units.
- Both `omn` and `omt` equal 2 for both species, with `kymin = 0.7` and grid `nx0,nky0,nz0,nv0,nw0 = 1,1,32,48,32`.
- Ring radius 0.4 m, current 750 A, surface factor 1.2, and tracing step input $10^{-5}$. [Reference scales](../docs/technical/normalization.md)
- Historical normalized $\gamma = 4.172$, $\omega = 0.946$, solver-converged. The exact parameter input and repeated local values are evidence for the starting reference. They leave cross-platform accuracy open.

Follow the [single-run instructions](../docs/reproducibility.md#reproduce-one-simulation). Log the input SHA-256, build, actual result and run time in [the comparison template](comparison.csv). Confirm solver status and phase consistency before comparing significant digits. The archived omega diagnostic writes three decimal places. That permits comparison of the displayed $\omega=0.946$ to three significant digits only. Appending a trailing zero would imply precision the file does not supply. To compare four significant digits, agree on a higher-precision diagnostic or a common late-time complex-potential analysis and verify its equivalence to the solver output. Agree on reference values and rounding/tolerance using that method. If the grid study selects a revised benchmark, version its input and establish a new reference before assigned-composition experiments.
