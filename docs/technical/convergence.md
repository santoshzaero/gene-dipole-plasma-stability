# Convergence and energy-derived estimates

## GENE initial-value diagnostic

In the checked 3.1 patch 5 source, the single-mode diagnostic computes the complex log of the ratio of consecutive sampled potentials, divided by `dt * istep_omega`. It averages the local rate estimates with weights proportional to the previous potential amplitude and checks their weighted spread using the source's variance-like expression with factor 6.7 against $(0.1\,\texttt{omega_prec})^2$. The configured default `omega_prec` is $10^{-3}$ and the sample spacing is ten steps. A nonzero accepted complex estimate triggers the convergence exit. Read both the convergence line in `run.log` and the corresponding `omega.dat` record. The columns are normalized wavenumber, growth rate, and signed real frequency. An exit code or a zero-valued `omega.dat` record alone gives insufficient evidence. [Implementation verification points](../references.md)

A temporal diagnostic addresses consistency of the evolved mode on one discretization. Grid refinement, velocity-domain tests, timestep checks, and mode identification address numerical accuracy. Physical validity further requires that the modeled equilibrium and approximation apply to the question.

## Free-energy fitting

A single mode with amplitude proportional to $e^{\gamma t}$ has a positive quadratic perturbation energy $W(t)\propto e^{2\gamma t}$. Thus $\gamma_{\rm eff}=(1/2)\,d\ln W/dt$, with $t$ the recorded normalized time. The project used column 2 (total energy) in `energy.dat`, filtered finite time and strictly positive finite energy, required at least 100 samples, and fit a straight line to $\ln W$ versus $t$ on the final 50%, 30%, and 15% of the retained **sample count**. The 15% slope divided by two was the reported estimate.

The automated rule required both $R^2_{15}$ and $R^2_{30}$ above 0.99 and $\max(|\gamma_{50}-\gamma_{15}|,|\gamma_{30}-\gamma_{15}|)<\max(0.05,0.1|\gamma_{15}|)$. Here $R^2$ is the linear fit coefficient of determination and the subscripts are window percentages. Five cases passed. Deuterium at `omn = omt = 0` was manually qualified in the final analysis based on consistent negative slopes and near-threshold 30% $R^2$ (0.989404). Its 15% estimate was about −0.0750. The original fit table preserves `UNCERTAIN` for this case and the final figure script records the override. Both decisions remain auditable. [Original fits](../../results/isotope/energy_fit_original.csv) · [Original classification logic](../../scripts/archive/create_final_isotope_heatmaps.py)

The final totals are 85 GENE-converged, six qualified energy estimates (including the override), and seven uncertain. A high $R^2$ supports log-linearity over the selected window. It does not establish that transients are absent or that the fit isolates one eigenmode. Energy alone supplies no phase information or real frequency. [Energy diagnostics](../../figures/energy/all_13_energy_fits.png)
