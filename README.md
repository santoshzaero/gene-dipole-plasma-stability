# Linear plasma stability in a magnetic dipole

## Start here

Plasma is a gas of charged particles. This project asks how quickly small disturbances grow when a ring-shaped magnet is used to confine a plasma. We used the GENE simulation code to compare ordinary hydrogen with deuterium, a heavier form of hydrogen, while changing how sharply density and temperature vary across the plasma.

In all 41 like-for-like tests where GENE could identify a consistent growing disturbance in both plasmas, the disturbance grew faster in hydrogen. The comparison measures early growth at the settings tested. How long the plasma stays confined would require a different study.

![Difference in hydrogen and deuterium growth rates across the sampled grid, restricted to the 41 pairs with both GENE convergence flags](figures/regenerated/isotope_gene_only.png)

Each square compares hydrogen and deuterium at the same density and temperature gradients. The number shows how much faster hydrogen grew in GENE's normalized units. A blank square means that GENE did not identify a comparable result for both plasmas.

## Technical overview

This MAE 190 study uses GENE 3.1 patch 5 for linear electrostatic initial-value simulations in a ring dipole. The isotope gradient comparison fixes the normalized binormal wavenumber at $k_y\rho_{\mathrm{ref}}=0.7$. When the normalized density and temperature gradients are both 2, the recorded growth rates are 6.096 for hydrogen and 4.172 for deuterium. The central heatmap uses only the 41 pairs with solver convergence flags. Grid independence and cross-platform agreement remain to be established. The [research log](docs/research_log.md) covers the separate wavenumber scan and its anomalous low-wavenumber case.

| Start here | What it covers |
| --- | --- |
| [Beginner guide](docs/beginner_guide/README.md) | Plasma, dipoles, instabilities, GENE, and reading the figures |
| [Technical guide](docs/technical/README.md) | Gyrokinetic model, numerical settings, normalization, diagnostics, and mode structure |
| [Completed studies](docs/research_log.md) | Installation, pair plasma, isotopes, energy fits, and the wavenumber scan |
| [Findings](docs/findings.md) and [limitations](docs/limitations.md) | Data quality, claims supported by the records, and open questions |
| [Reproduction instructions](docs/reproducibility.md) and [class benchmark](benchmarks/README.md) | Regenerate figures from saved data or reproduce a simulation with independently obtained GENE |
| [Parallel grid](docs/studies/deuterium_parallel_grid.md) and [timestep follow-up](docs/studies/deuterium_timestep_nz24.md) | Deuterium reference at 24, 32, and 64 field-line points, with rates, timings, and mode diagnostics |
| [Combined-grid validation](docs/studies/deuterium_combined_validation.md) | Exploratory grid, first velocity-boundary test, and class benchmark choice |
| [Research roadmap](docs/research_roadmap.md) | Convergence study, class replication, controlled scans, and theory validation |
| [Scope and provenance](docs/provenance.md) and [session workflow](docs/research_workflow.md) | What was curated, how to review new results, and the publication plan |
| [Archived report](reports/README.md) | Original isotope report and rebuild instructions |

## Audit and regenerate figures

From the repository root, use a Python environment with the packages in [requirements.txt](requirements.txt).

```sh
python -m pip install -r requirements.txt
python scripts/reproduce.py --out generated/figures
```

The command works entirely from the archived data. It checks the inputs and run index, reproduces the thirteen free-energy fits, audits the reported counts and the low-wavenumber anomaly, and renders four comparison figures. See the [data dictionary](results/README.md) for the original tables and status labels.

## Software and research references

GENE stands for Gyrokinetic Electromagnetic Numerical Experiment. The simulation code is maintained by the GENE Development Team and is obtained separately. This archive contains the project's configurations, results, analysis, figures, and report. When citing this work, include the repository revision and the relevant GENE references. [Research references](docs/references.md) [GENE project](https://genecode.org/main.html) · [GENE access](https://www.genecode.org/license.html)
