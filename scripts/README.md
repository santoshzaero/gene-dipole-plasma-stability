# Analysis scripts

- [reproduce.py](reproduce.py) checks artifact hashes and reported results, recomputes the isotope fits, and generates reviewed charts. It uses committed data and runs offline.
- [restore_historical_figures.py](restore_historical_figures.py) stages portable inputs in a temporary directory and runs five original **plotting** scripts from [archive](archive/). It recreates the density pilot charts, pair gradient and unresolved-energy plots, six final isotope heatmaps, and two isotope energy diagnostic panels. The archived pair extension image is preserved as supplied and has no matching standalone plotter in the source work. Its five underlying traces are included. Font and library differences can affect the exact raster rendering.
- The original launch and analysis scripts in [archive](archive/) preserve experimental provenance, including hard-coded project paths and historical plot methods. Use the separate [reproduction commands](../docs/reproducibility.md) for a fresh simulation. Some archived launchers run simulations immediately when executed or imported.

From the repository root, after installing the [dependencies](../requirements.txt), regenerate the historical plots with

```sh
python scripts/restore_historical_figures.py generated/historical
```
