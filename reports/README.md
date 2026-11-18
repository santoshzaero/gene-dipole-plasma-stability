# Research report

[Linear Stability of Electron–Hydrogen and Electron–Deuterium Plasmas in Dipole Geometry](isotope_stability_report.pdf) is the original MAE 190 report. Its [LaTeX source](isotope_stability_report.tex) was adapted only to locate the archived figures from the repository root. Build a local copy with

```sh
mkdir -p generated/report
latexmk -pdf -outdir=generated/report reports/isotope_stability_report.tex
```

The current [technical methods](../docs/technical/convergence.md) document the automated fit thresholds and explain the manual classification, and the [research log](../docs/research_log.md) adds the subsequent wavenumber scan.
