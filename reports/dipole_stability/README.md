# Linear Gyrokinetic Stability of Dipole-Confined Plasmas

The revised paper focuses on physical findings from the IV pair, isotope, common-gradient and electron-response studies. An electron–deuterium–helium pilot and two targeted low-wavenumber controls extend the original record. Supporting resolution, timestep, energy and spatial-phase diagnostics are in the appendices. The previous article is preserved at commit `3455ba0`. [Follow-up methods and results](../../docs/studies/deuterium_followup.md)

- [Compiled article](dipole_stability.pdf) and [LaTeX source](dipole_stability.tex)
- [Bibliography](references.bib)
- [Figure and investigation inventory](inventory.md)
- [Unavailable and excluded figures](limitations.md)
- [Vector PDF and 360 dpi PNG figures](figures/) and [data snapshot](data/)

## Rebuild offline

The plot inputs are recorded in `data/`. The offline build uses NumPy and Matplotlib. The optional raw follow-up extraction also uses SciPy (`python3 -m pip install -r requirements-followup.txt`). Run these commands from this directory in the checkout:

```sh
python3 -m pip install -r ../../requirements.txt
python3 verify_data.py
python3 make_figures.py
latexmk -pdf -outdir=build dipole_stability.tex
```

The committed PDF was built with TeX Live 2026 and BibTeX. The named captions and references compile with the figure PDFs. To refresh the data from accessible saved simulations, use `python3 recover_data.py --runs /absolute/path/to/gene-complete/runs --work /absolute/path/to/repository/work`. The optional `--source-repo` takes a matching checkout containing the tracked results. The source tables were read from repository revision `f1ee6ef`. Run `python3 analyze_followup.py --runs /absolute/path/to/gene-complete/runs` separately to refresh the follow-up tables from the saved raw outputs in `work/deuterium_followup`. Raw records are read in place. The original tables and the follow-up tables both ship with the report. The build and analysis commands run only on saved data. For machines without the raw output directories, the complete plotted dataset and fit tables are already present here.

`data/raw_lineage.csv` records which traces and profiles were freshly recovered and identifies checked native files by SHA-256. `data/input_inventory.csv` identifies tracked and local input collections with their relative paths, solver, species, gradients, and hashes where readable. Some local duplicates were offloaded at recovery time and retain blank metadata in that inventory. Their parameter settings survive in the tracked configurations. Filter decisions and the group-to-file mapping are documented in the inventory. The bibliography links refer to published sources. The classmate PDF served only as a layout reference and is outside the report package.
