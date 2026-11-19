# Historical GENE input files

## Start here

Each `parameters` file records the settings for one simulation, including the particles, magnetic geometry, and quantities varied in that study. For a current input, start with the [shared electron–positron benchmark](../benchmarks/classmate/README.md) or the [deuterium reference](../benchmarks/README.md).

## Technical layout

Every nested `parameters` file preserves the exact original IV input as a historical research record. Dormant eigenvalue-solver keys in those records are obsolete. Use a cleaned copy for a new IV run and keep the archived file intact. [Run index](../results/run_index.csv) pairs the inputs with their diagnostics and runtime. [Provenance](../results/provenance.csv) records original paths and checksums.

| Folder | Inputs |
| --- | --- |
| [pair_density](pair_density/) | Seven density-gradient pilot cases |
| [pair](pair/) | 49 combinations of density and temperature gradients for electron–positron plasma |
| [pair_extended](pair_extended/) | Five pair cases with a longer step cap |
| [isotope](isotope/) | 49 hydrogen and 49 deuterium gradient pairs |
| [ky](ky/) | Eight wavenumbers per isotope at common gradients of 2 |

Folder labels use `p` in place of a decimal point. For example, `ky_0p7` denotes normalized wavenumber 0.7. The [run instructions](../docs/reproducibility.md#reproduce-one-simulation) explain how to use any archived input in a fresh run directory.
