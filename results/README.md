# Data dictionary

[Run index](run_index.csv) records 175 archived inputs across the documented series. The index is derived from original run logs and `omega.dat`. Columns are study and case ID, exact input path, presence of the GENE convergence and underflow messages, reported solver wallclock in seconds, number of steps, and the three raw omega diagnostic columns. The latter are normalized wavenumber, growth, and real frequency. A raw zero can be a diagnostic placeholder. Empty fields indicate unavailable or unreported values. Each case key maps to the corresponding archived input.

| File or directory | Contents |
| --- | --- |
| [Pair density pilot](pair/density_scan.csv) | Seven density settings at fixed temperature gradient 2. Original `OK` rows agree with the convergence messages. |
| [Pair gradient scan](pair/gradient_scan.csv) | 49 initial cases with both gradients, growth, frequency, and status. The five `CHECK` rows contain raw zero placeholders. The `pair_extended` index entries track the five longer follow-ups. |
| [Hydrogen](isotope/hydrogen.csv) and [deuterium](isotope/deuterium.csv) | 49 cases per isotope with raw return codes and solver status. Growth and frequency cells are empty in the unresolved isotope rows. |
| [Original energy fits](isotope/energy_fit_original.csv) | Three rates, three $R^2$ values, and the original automatic `CONSISTENT` or `UNCERTAIN` screen. |
| [Final historical classification](isotope/growth_rates_with_quality_original.csv) | Final rates and `gene`, `qualified`, and `uncertain` labels, including the documented manual override. The legacy “GENE eigenvalue” label refers to the initial-value diagnostic in this project. |
| [Wavenumber scan](ky/original.csv) | Sixteen runs and original status, rates, and return codes. Deuterium at 0.3 is anomalous and unvalidated even though the solver convergence flag was set. |
| [Regression summary](installation/regression_summary.csv) | Test identifiers, names, counts of matching upstream comparisons, and initial-value solver times printed in the original test log. |
| [Provenance](provenance.csv) | Curated file paths, original paths relative to the separate GENE checkout, transformation where applicable, and SHA-256 of each staged artifact. |

The energy histories are gzip-compressed TSVs with normalized time and the total-energy column exactly as printed by GENE. [Isotope fits](isotope/energy_histories/) include all 13 unresolved cases. [Pair histories](pair/energy_histories/) include the five original and five extended cases. [Wavenumber histories](ky/energy_histories/) include all 16 cases, with isotope and `kymin` in the paths. The original multi-column diagnostics and binary field files are held in the separate simulation workspace.
