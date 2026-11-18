# Limitations

- **Linear initial-value response.** The calculations address infinitesimal perturbations. They provide no direct measure of turbulent saturation, net transport, confinement time, engineering performance, or experimental stability.
- **Finite parameter coverage.** The isotope gradient grid fixes one wavenumber and varies gradients jointly between species. The wavelength grid fixes both gradients at 2. Growth between samples, off the selected surface, or in other magnetic equilibria is open.
- **Numerical accuracy.** The archived runs used one grid and one integration configuration. GENE's temporal diagnostic cannot establish resolution independence, branch identity, or benchmark precision. The low-wavenumber anomaly illustrates why numerical checks matter.
- **Output precision.** The kinetic reference outputs store three decimal places. The D frequency 0.946 has three significant digits, and its fourth digit is unavailable in that output.
- **Physical normalization.** Shared code inputs support a normalized comparison. The records do not specify a complete SI scale, and isotope mass changes species gyroradii and can change effective collision rates even at fixed nominal input.
- **Mode interpretation.** Phase, parity, spatial localization, and gradient-response studies are needed before firmly assigning a mode family. A growth-rate trend alone supports only a hypothesis about its mechanism.
- **Data gaps.** An unresolved or underflowing run does not prove stability. Diagnostic placeholders and secondary energy fits require distinct labels. The historical figures retain their original names and qualifiers.
