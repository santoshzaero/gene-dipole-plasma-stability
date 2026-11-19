# Linear Gyrokinetic Stability of Dipole-Confined Plasmas

The full Phase 1 and Phase 2 report combines the foundational numerical and isotope work with the later common-density and wavenumber studies. It includes all 14 figures and the three appendices. The earlier isotope report, meeting figures, and final paired figures remain in the repository as historical presentations.

- [Compiled article](dipole_stability.pdf) and [LaTeX source](dipole_stability.tex)
- [Bibliography](references.bib)
- [Figure and investigation inventory](inventory.md)
- [Unavailable and excluded figures](limitations.md)
- [Vector PDF and 360 dpi PNG figures](figures/) and [data snapshot](data/)

## Rebuild offline

The plot inputs are recorded in `data/`. NumPy and Matplotlib are the only Python dependencies. Run these commands from this directory in the checkout:

```sh
python3 -m pip install -r ../../requirements.txt
python3 verify_data.py
python3 make_figures.py
latexmk -pdf -outdir=build dipole_stability.tex
```

The committed PDF was built with TeX Live 2026 and BibTeX. The named captions and references compile with the figure PDFs. To refresh the data from accessible saved simulations, use `python3 recover_data.py --runs /absolute/path/to/gene-complete/runs --work /absolute/path/to/repository/work`. The optional `--source-repo` takes a matching checkout containing the tracked results. The source tables were read from repository revision `f1ee6ef`. Raw records are read in place, and columns or profiles are checked against the matched curated records where applicable. The simulator is never invoked. For machines without the raw output directories, the complete plotted dataset and fit tables are already present here.

`data/raw_lineage.csv` records which traces and profiles were freshly recovered and identifies checked native files by SHA-256. `data/input_inventory.csv` identifies tracked and local input collections with their relative paths, solver, species, gradients, and hashes where readable. Some local duplicates were offloaded at recovery time and retain blank metadata in that inventory. Their parameter settings survive in the tracked configurations. Filter decisions and the group-to-file mapping are documented in the inventory. The bibliography links refer to published sources. The classmate PDF served only as a layout reference and is outside the report package.
