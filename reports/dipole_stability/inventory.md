# Figure inventory for the revised paper

The first version is accessible at commit [`3455ba0`](https://github.com/santoshzaero/gene-dipole-plasma-stability/tree/3455ba0/reports/dipole_stability). The following table uses its figure numbers so that the revisions can be traced even when LaTeX renumbers the figures. Earlier figures and results remain available in the project. [Research log](../../docs/research_log.md) · [Follow-up study](../../docs/studies/deuterium_followup.md)

| Original | Revised disposition | Figure or evidence | Basis and interpretation |
| --- | --- | --- | --- |
| 1 | Main text, revised | [Historical pair gradients](figures/01_pair_gradients.pdf) | `pair_grid.csv` and `pair_density.csv` preserve the Phase 1 joint-gradient and fixed-temperature density series. |
| 2 | Main text, clarified | [Pair benchmark](figures/02_pair_benchmark.pdf) | `pair_projection.csv` and `pair_windows.csv` demonstrate exponential growth with stationary temporal phase. |
| 3 | Moved to Appendix C | [Unresolved pair energies](figures/03_pair_unresolved_energy.pdf) | `energy_histories.csv.gz` shows why amplitude renormalization is not a physical change in energy. The complete diagnostics leave all five modal rates unqualified. |
| 4 | Main text, clarified | [Hydrogen versus deuterium](figures/04_isotope_gradient_comparison.pdf) | The 41 paired qualified points from the isotope CSVs establish a modeled isotope response at matched normalization. |
| 5 | Split | [Zero-drive decay](figures/05_zero_gradient_energy.pdf) and [Appendix C fit examples](figures/05_isotope_fit_examples.pdf) | The main plot contains only normalized zero-gradient energies. The appendix shows the qualified and uncertain finite-time fits, with visible dashed fit segments and all 13 outcomes in a table. |
| 6 | Main text, clarified | [Isotope wavenumber comparison](figures/06_isotope_wavenumber.pdf) | `isotope_wavenumber.csv`; five qualified pairs and the distinction between binormal wavelength and field-line position. |
| 7 | Main-text table; full plot moved to Appendix A | [Grid and timestep comparisons](figures/07_resolution_and_timestep.pdf) | `combined_comparison.csv` and the convergence tables supply rates, percentages and runtimes. The 1% screen is exploratory. |
| 8 | Moved to Appendix A | [Timestep and velocity-domain controls](figures/08_velocity_and_domain_controls.pdf) | Curated energies and the `domain_*` and `v_*` tables. The roughly 4.9% domain frequency sensitivity remains in the main limitations. |
| 9 | Replaced in Appendix B | [Fixed-step and parallel-grid controls](figures/16_low_wavenumber_controls.pdf) | Native follow-up fields and energy traces, weighted log-ratio audit, and per-step alias diagnosis in `data/followup_*`. Historical anomalous rates stay outside the qualified scan. |
| 10 | Main text, simpler labels | [Qualified deuterium wavenumbers](figures/10_deuterium_wavenumber.pdf) | `phase2_runs.csv`, `phase2_extension.csv`, and the qualified 32-point half-step result at common gradient 2 and `kymin = 0.3`. Both temperature gradients stay fixed at 2. |
| 11 | Main text, simpler labels | [Common density-gradient series](figures/11_deuterium_density.pdf) | The same dataset viewed at fixed wavenumber. The zero-density point is unresolved. |
| 12 | Split | [Mode amplitude in main text](figures/12_mode_amplitude.pdf) and [Relative spatial phase in Appendix C](figures/12_mode_phase.pdf) | `field_profiles.csv`, `phase2_overlap.csv` and `phase2_extension_overlap.csv`; peak-normalized amplitude is visually distinct from aligned phase. |
| 13 | Main text, retained | [Matched electron response](figures/13_electron_response.pdf) | Native rates, projected fits and field profiles for kinetic and adiabatic electrons at one collisionless point. |
| 14 | Appendix A | [Late phase and shape](figures/14_reference_field_settling.pdf) | The two `field_nz*.csv.gz` archives show late temporal slope and departure from the final mode. |
| New | Main text | [Compensated electron-gradient pilot](figures/15_compensated_electron_gradient.pdf) | Three accepted electron–deuterium–helium equilibria. Helium gradient changes together with electron gradient at fixed deuterium gradient. |

The [raw lineage](data/raw_lineage.csv) applies to the original reconstruction. New source hashes, field and energy histories, fit windows, and final complex profiles are in the `data/followup_*` files. Vector PDFs have corresponding 360 dpi PNGs.
