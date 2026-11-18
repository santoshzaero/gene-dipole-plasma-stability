# Historical GENE input files

## Start here

Each `parameters` file records the settings for one simulation, including the particles, magnetic geometry, and quantities varied in that study. To try one example, read the [shared deuterium benchmark](../benchmarks/README.md).

## Technical layout

Every nested `parameters` file is a byte-for-byte copy of the corresponding recorded input. [Run index](../results/run_index.csv) pairs the inputs with their diagnostics and runtime. [Provenance](../results/provenance.csv) records original paths and checksums.

| Folder | Inputs |
| --- | --- |
| [pair_density](pair_density/) | Seven density-gradient pilot cases |
| [pair](pair/) | 49 combinations of density and temperature gradients for electron–positron plasma |
| [pair_extended](pair_extended/) | Five pair cases with a longer step cap |
| [isotope](isotope/) | 49 hydrogen and 49 deuterium gradient pairs |
| [ky](ky/) | Eight wavenumbers per isotope at common gradients of 2 |

Folder labels use `p` in place of a decimal point. For example, `ky_0p7` denotes normalized wavenumber 0.7. The [run instructions](../docs/reproducibility.md#reproduce-one-simulation) explain how to use any archived input in a fresh run directory.
