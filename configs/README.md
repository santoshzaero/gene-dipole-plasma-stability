# Historical GENE input files

Every nested `parameters` file is a byte-for-byte copy of the corresponding recorded input. [Run index](../results/run_index.csv) pairs the inputs with their diagnostics and runtime. [Provenance](../results/provenance.csv) records original paths and checksums.

| Folder | Inputs |
| --- | --- |
| [pair_density](pair_density/) | Seven density-gradient pilot cases |
| [pair](pair/) | 49 electron–positron gradient pairs |
| [pair_extended](pair_extended/) | Five pair cases with a longer step cap |
| [isotope](isotope/) | 49 hydrogen and 49 deuterium gradient pairs |
| [ky](ky/) | Eight wavenumbers per isotope at common gradients of 2 |

Folder labels use `p` in place of a decimal point. Start with the [shared reference case](../benchmarks/README.md) to reproduce one simulation.
