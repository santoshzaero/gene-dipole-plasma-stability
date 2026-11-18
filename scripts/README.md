# Analysis scripts

## Start here

The scripts can check the saved results and redraw figures from those data. For a first pass, run `python scripts/reproduce.py` from the repository root after installing the [dependencies](../requirements.txt). It reads archived results without starting a simulation. Add `--out generated/figures` to write the reviewed plots.

## Technical reference

- [compare_parallel_followup.py](compare_parallel_followup.py) checks timestep sensitivity and the 24-point trial using completed runs or redraws the figure from published plot data. [Follow-up study](../docs/studies/deuterium_timestep_nz24.md)
- [compare_parallel_resolution.py](compare_parallel_resolution.py) redraws the deuterium grid-comparison figure from archived data. With both completed run directories, it recomputes the field and energy diagnostics without launching GENE. [Study instructions](../docs/studies/deuterium_parallel_grid.md)
- [reproduce.py](reproduce.py) checks artifact hashes and reported results, recomputes the isotope fits, and generates reviewed charts. It uses committed data and runs offline.
- [restore_historical_figures.py](restore_historical_figures.py) stages portable inputs in a temporary directory and runs five original **plotting** scripts from [archive](archive/). It recreates the density pilot charts, pair gradient and unresolved-energy plots, six final isotope heatmaps, and two isotope energy diagnostic panels. The archived pair extension image is preserved as supplied and has no matching standalone plotter in the source work. Its five underlying traces are included. Font and library differences can affect the exact raster rendering.
- The original launch and analysis scripts in [archive](archive/) preserve experimental provenance, including hard-coded project paths and historical plot methods. Use the separate [reproduction commands](../docs/reproducibility.md) for a fresh simulation. Some archived launchers run simulations immediately when executed or imported.

From the repository root, after installing the [dependencies](../requirements.txt), regenerate the historical plots with

```sh
python scripts/restore_historical_figures.py generated/historical
```
